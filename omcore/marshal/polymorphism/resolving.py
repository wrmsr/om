"""
The one place polymorphism subtype collection happens: resolves a PolymorphismSpec's declared sources into the classic
`Polymorphism`, with merged runtime tag derivation, cross-source dedupe, and real conflict errors.

Source semantics:
 - ExplicitSubtypeSource entries carry final tags and pass through untouched.
 - SubclassesSubtypeSource deep-scans the root's subclass tree at resolve time.
 - ConfigSubtypeSource reads `SubtypeConfig` configs under the root's key through the (footprinting) factory context.
 - ManifestSubtypeSource matches globally-loaded `SubtypeManifest` entries by resolved base path and imports their
   modules. Tag derivation uses the manifest's attr string - the subtype class name - so a future lazier resolution
   needn't import anything to know the tag map.

Tag derivation is a spec-level decision applied uniformly across the merged entry set: explicit tags (from
SubtypeInfo, SubtypeConfig, or SubtypeManifest overrides) always win; the rest get the spec's suffix_stripping (auto
evaluated over the merged derived-name set) and naming translation, exactly mirroring `polymorphism_from_subtypes`.
"""
import typing as ta

from ... import lang
from ..api.contexts import BaseFactoryContext
from ..api.naming import translate_name
from .api import ConfigsSubtypeSource
from .api import ExplicitSubtypeSource
from .api import LazySubtype
from .api import ManifestsSubtypeSource
from .api import Polymorphism
from .api import PolymorphismSubtypeError
from .api import SubclassesSubtypeSource
from .api import SubtypeConfig
from .api import SubtypeInfo
from .api import SubtypeInfos
from .api import _suffix_stripper
from .api import opt_cls_fqcn
from .manifests import SubtypeManifest
from .specs import PolymorphismSpec
from .specs import SubtypeSource


if ta.TYPE_CHECKING:
    from ...manifests import globals as manifest_globals
else:
    manifest_globals = lang.proxy_import('...manifests.globals', __package__)


##


class _RawSubtype(ta.NamedTuple):
    ty: type | LazySubtype  # Never resolved during resolution - laziness survives all the way into the handlers.
    name: str               # the derivation input - the subtype class name
    tag: str | None         # explicit tag - skips derivation
    alts: tuple[str, ...]


##


def _cls_path(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


@lang.cached_function
def _subtype_manifests_by_base_path() -> ta.Mapping[str, ta.Sequence[SubtypeManifest]]:
    dct: dict[str, list[SubtypeManifest]] = {}
    for v in manifest_globals.GlobalManifestLoader.load_values_of(SubtypeManifest):
        dct.setdefault(v.resolve_base_path(), []).append(v)
    return dct


def match_subtype_manifests(
        root: type,
        values: ta.Iterable[SubtypeManifest],
) -> list[SubtypeManifest]:
    rp = _cls_path(root)
    return [v for v in values if v.resolve_base_path() == rp]


def _manifest_raw_subtype(v: SubtypeManifest) -> _RawSubtype:
    return _RawSubtype(
        ty=LazySubtype(f'{v.module}.{v.attr}', v.resolve),
        name=v.attr,
        tag=v.tag,
        alts=tuple(v.alts or ()),
    )


##


class _PolymorphismResolver:
    def __init__(self, ctx: BaseFactoryContext, spec: PolymorphismSpec) -> None:
        super().__init__()

        self._ctx = ctx
        self._spec = spec

    #

    def _collect_source(self, source: SubtypeSource) -> list[_RawSubtype]:
        raws: list[_RawSubtype] = []

        if isinstance(source, ExplicitSubtypeSource):
            for i in source.subtypes:
                raws.append(_RawSubtype(
                    ty=i.ty,
                    name=i.ty.fqcn.rsplit('.', 1)[-1] if isinstance(i.ty, LazySubtype) else i.ty.__name__,
                    tag=i.tag,
                    alts=tuple(i.alts),
                ))

        elif isinstance(source, SubclassesSubtypeSource):
            sub_ty: type
            for sub_ty in lang.deep_subclasses(self._spec.root, concrete_only=True):
                raws.append(_RawSubtype(
                    ty=sub_ty,
                    name=sub_ty.__name__,
                    tag=None,
                    alts=(),
                ))

        elif isinstance(source, ConfigsSubtypeSource):
            for sc in self._ctx.get_configs(self._spec.root).get(SubtypeConfig) or ():
                raws.append(_RawSubtype(
                    ty=sc.ty,
                    name=sc.ty.__name__,
                    tag=sc.tag,
                    alts=tuple(sc.alts or ()),
                ))

        elif isinstance(source, ManifestsSubtypeSource):
            for v in _subtype_manifests_by_base_path().get(_cls_path(self._spec.root), ()):
                raws.append(_manifest_raw_subtype(v))

        else:
            raise TypeError(source)

        return raws

    #

    def _merge_raws(self, raws: ta.Iterable[_RawSubtype]) -> list[_RawSubtype]:
        # Dedupe best-effort by fqcn when one is available (a manifest-declared subtype unifies with its class as
        # found by the subclass scan once imported - preferring the concrete side and *never* resolving) and by type
        # identity otherwise. Two distinct concrete classes sharing an fqcn are a real ambiguity.
        merged: dict[str | lang.Identity, _RawSubtype] = {}

        for r in raws:
            if isinstance(r.ty, LazySubtype):
                k: str | lang.Identity = r.ty.fqcn
            else:
                k = opt_cls_fqcn(r.ty) or lang.Identity(r.ty)

            if (x := merged.get(k)) is None:
                merged[k] = r
                continue

            if (
                    isinstance(x.ty, type) and
                    isinstance(r.ty, type) and
                    x.ty is not r.ty
            ):
                raise PolymorphismSubtypeError(
                    f'Distinct subtype classes sharing fqcn {k!r} for {self._spec.root!r}: {x.ty!r}, {r.ty!r}',
                )

            if x.tag is not None and r.tag is not None and x.tag != r.tag:
                raise PolymorphismSubtypeError(
                    f'Conflicting explicit tags for subtype {k!r} of {self._spec.root!r}: {x.tag!r}, {r.tag!r}',
                )

            merged[k] = x._replace(
                ty=x.ty if isinstance(x.ty, type) else r.ty,
                tag=x.tag if x.tag is not None else r.tag,
                alts=(*x.alts, *(a for a in r.alts if a not in x.alts)),
            )

        return list(merged.values())

    def _derive_tags(self, raws: ta.Sequence[_RawSubtype]) -> list[SubtypeInfo]:
        spec = self._spec

        derived = [r for r in raws if r.tag is None]

        strip_suffix = _suffix_stripper(
            spec.suffix_stripping,
            spec.root.__name__,
            {r.name for r in derived},
        )

        out: list[SubtypeInfo] = []
        for r in raws:
            if (tag := r.tag) is None:
                tag = strip_suffix(r.name)
                if spec.naming is not None:
                    tag = translate_name(tag, spec.naming)

            out.append(SubtypeInfo(
                r.ty,
                tag,
                frozenset(r.alts),
            ))

        return out

    def _check_subtypes(self, subtypes: ta.Sequence[SubtypeInfo]) -> None:
        by_tag: dict[str, SubtypeInfo] = {}
        for i in subtypes:
            for t in (i.tag, *i.alts):
                if (x := by_tag.get(t)) is not None:
                    raise PolymorphismSubtypeError(
                        f'Conflicting tag {t!r} for {self._spec.root!r}: {x.ty!r}, {i.ty!r}',
                    )
                by_tag[t] = i

    #

    def _restrict(self, poly: Polymorphism) -> Polymorphism:
        if (only := self._spec.only) is None:
            return poly

        if any(m is self._spec.root for m in only):
            return poly

        out: dict[str | lang.Identity, SubtypeInfo] = {}
        for m in only:
            if (i := poly.subtypes.by_ty.get(m)) is not None:
                out[i.fqcn or lang.Identity(i.ty)] = i
            elif (
                    (mf := opt_cls_fqcn(m)) is not None and
                    (i := poly.subtypes.lazy_by_fqcn.get(mf)) is not None
            ):
                # The member class is loaded (it appeared in an annotation) but was resolved as a lazy declaration.
                out[mf] = i
            elif (
                    lang.is_abstract(m) and
                    issubclass(m, self._spec.root) and
                    # Abstract-intermediate expansion covers concrete entries only - lazy entries cannot be
                    # subclass-tested without importing.
                    (covered := [c for c in poly.subtypes if c.cls is not None and issubclass(c.cls, m)])
            ):
                out.update({(c.fqcn or lang.Identity(c.ty)): c for c in covered})
            else:
                raise PolymorphismSubtypeError(
                    f'Union member {m!r} is not a resolved subtype (or covering base) of {self._spec.root!r}',
                )

        return Polymorphism(
            self._spec.root,
            SubtypeInfos(list(out.values())),
        )

    #

    def resolve(self) -> Polymorphism:
        raws: list[_RawSubtype] = []
        for source in self._spec.sources:
            raws.extend(self._collect_source(source))

        merged = self._merge_raws(raws)
        if not merged:
            raise PolymorphismSubtypeError(
                f'No subtypes resolved for {self._spec.root!r} from {self._spec.sources!r}',
            )

        subtypes = self._derive_tags(merged)
        self._check_subtypes(subtypes)

        poly = Polymorphism(
            self._spec.root,
            SubtypeInfos(subtypes),
        )

        return self._restrict(poly)


def resolve_polymorphism(ctx: BaseFactoryContext, spec: PolymorphismSpec) -> Polymorphism:
    return _PolymorphismResolver(ctx, spec).resolve()
