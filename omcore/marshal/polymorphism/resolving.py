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

from ... import check
from ... import lang
from ..api.contexts import BaseFactoryContext
from ..api.naming import translate_name
from .api import ConfigsSubtypeSource
from .api import ExplicitSubtypeSource
from .api import ManifestsSubtypeSource
from .api import Polymorphism
from .api import PolymorphismSubtypeError
from .api import SubclassesSubtypeSource
from .api import SubtypeConfig
from .api import SubtypeInfo
from .api import SubtypeInfos
from .api import _suffix_stripper
from .manifests import SubtypeManifest
from .specs import PolymorphismSpec
from .specs import SubtypeSource


if ta.TYPE_CHECKING:
    from ...manifests import globals as manifest_globals
else:
    manifest_globals = lang.proxy_import('...manifests.globals', __package__)


##


class _RawSubtype(ta.NamedTuple):
    ty: type | None       # None until the manifest entry is resolved
    name: str             # the derivation input - the subtype class name
    tag: str | None       # explicit tag - skips derivation
    alts: tuple[str, ...]

    resolve: ta.Callable[[], type] | None = None


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
        None,
        v.attr,
        v.tag,
        tuple(v.alts or ()),
        resolve=v.resolve,
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
                raws.append(_RawSubtype(i.ty, i.ty.__name__, i.tag, tuple(i.alts)))

        elif isinstance(source, SubclassesSubtypeSource):
            sub_ty: type
            for sub_ty in lang.deep_subclasses(self._spec.root, concrete_only=True):
                raws.append(_RawSubtype(sub_ty, sub_ty.__name__, None, ()))

        elif isinstance(source, ConfigsSubtypeSource):
            for sc in self._ctx.get_configs(self._spec.root).get(SubtypeConfig) or ():
                raws.append(_RawSubtype(sc.ty, sc.ty.__name__, sc.tag, tuple(sc.alts or ())))

        elif isinstance(source, ManifestsSubtypeSource):
            for v in _subtype_manifests_by_base_path().get(_cls_path(self._spec.root), ()):
                raws.append(_manifest_raw_subtype(v))

        else:
            raise TypeError(source)

        return raws

    #

    def _merge_raws(self, raws: ta.Iterable[_RawSubtype]) -> list[_RawSubtype]:
        # Eagerly resolve manifest entries (importing their modules), then dedupe by ty - the same class may arrive
        # from several sources (a manifest-declared subtype is also found by the subclass scan once imported).
        by_ty: dict[type, _RawSubtype] = {}

        for r in raws:
            if (ty := r.ty) is None:
                ty = check.isinstance(check.not_none(r.resolve)(), type)
                r = r._replace(ty=ty, resolve=None)

            if (x := by_ty.get(ty)) is None:
                by_ty[ty] = r
                continue

            if x.tag is not None and r.tag is not None and x.tag != r.tag:
                raise PolymorphismSubtypeError(
                    f'Conflicting explicit tags for subtype {ty!r} of {self._spec.root!r}: {x.tag!r}, {r.tag!r}',
                )

            by_ty[ty] = x._replace(
                tag=x.tag if x.tag is not None else r.tag,
                alts=(*x.alts, *(a for a in r.alts if a not in x.alts)),
            )

        return list(by_ty.values())

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
                check.not_none(r.ty),
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

        out: dict[type, SubtypeInfo] = {}
        for m in only:
            if (i := poly.subtypes.by_ty.get(m)) is not None:
                out[m] = i
            elif (
                    lang.is_abstract(m) and
                    issubclass(m, self._spec.root) and
                    (covered := [c for c in poly.subtypes if issubclass(c.ty, m)])
            ):
                out.update({c.ty: c for c in covered})
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
