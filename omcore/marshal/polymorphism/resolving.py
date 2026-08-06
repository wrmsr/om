"""
The one place polymorphism impl collection happens: resolves a PolymorphismSpec's declared sources into the classic
`Polymorphism`, with merged runtime tag derivation, cross-source dedupe, and real conflict errors.

Source semantics:
 - ExplicitImplSource entries carry final tags and pass through untouched.
 - SubclassesImplSource deep-scans the root's subclass tree at resolve time (abstract intermediates become ImplBases).
 - ConfigImplSource reads `PolymorphismImpl` configs under the root's key through the (footprinting) factory context.
 - ManifestImplSource matches globally-loaded `ImplForManifest` entries by resolved base path and imports their
   modules. Tag derivation uses the manifest's attr string - the impl class name - so a future lazier resolution
   needn't import anything to know the tag map.

Tag derivation is a spec-level decision applied uniformly across the merged entry set: explicit tags (from Impl,
PolymorphismImpl, or ImplForManifest overrides) always win; the rest get the spec's strip_suffix (AUTO evaluated over
the merged derived-name set) and naming translation, exactly mirroring `polymorphism_from_impls`.
"""
import typing as ta

from ... import check
from ... import lang
from ..api.contexts import BaseFactoryContext
from ..api.naming import translate_name
from .api import AUTO_STRIP_SUFFIX
from .api import Impl
from .api import ImplBase
from .api import ImplBases
from .api import Impls
from .api import Polymorphism
from .api import PolymorphismImpl
from .api import PolymorphismImplError
from .manifests import ImplForManifest
from .specs import ConfigImplSource
from .specs import ExplicitImplSource
from .specs import ImplSource
from .specs import ManifestImplSource
from .specs import PolymorphismSpec
from .specs import SubclassesImplSource


if ta.TYPE_CHECKING:
    from ...manifests import globals as manifest_globals
else:
    manifest_globals = lang.proxy_import('...manifests.globals', __package__)


##


class _RawImpl(ta.NamedTuple):
    ty: type | None       # None until the manifest entry is resolved
    name: str             # the derivation input - the impl class name
    tag: str | None       # explicit tag - skips derivation
    alts: tuple[str, ...]

    resolve: ta.Callable[[], type] | None = None


##


def _cls_path(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


@lang.cached_function
def _impl_for_manifests_by_base_path() -> ta.Mapping[str, ta.Sequence[ImplForManifest]]:
    dct: dict[str, list[ImplForManifest]] = {}
    for v in manifest_globals.GlobalManifestLoader.load_values_of(ImplForManifest):
        dct.setdefault(v.resolve_base_path(), []).append(v)
    return dct


def match_impl_for_manifests(
        root: type,
        values: ta.Iterable[ImplForManifest],
) -> list[ImplForManifest]:
    rp = _cls_path(root)
    return [v for v in values if v.resolve_base_path() == rp]


def _manifest_raw_impl(v: ImplForManifest) -> _RawImpl:
    return _RawImpl(
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

    def _collect_source(self, source: ImplSource) -> tuple[list[_RawImpl], list[type]]:
        raws: list[_RawImpl] = []
        bases: list[type] = []

        if isinstance(source, ExplicitImplSource):
            for i in source.impls:
                raws.append(_RawImpl(i.ty, i.ty.__name__, i.tag, tuple(i.alts)))

        elif isinstance(source, SubclassesImplSource):
            tree: ta.Mapping[type, ta.AbstractSet[type]] = lang.deep_subclass_tree(
                self._spec.root,
                total=True,
                concrete_only=True,
            )
            for sub_ty in tree:
                if sub_ty is self._spec.root:
                    # The tree includes the root itself - a (possibly concrete) root is never its own impl.
                    continue
                if lang.is_abstract(sub_ty):
                    bases.append(sub_ty)
                else:
                    raws.append(_RawImpl(sub_ty, sub_ty.__name__, None, ()))

        elif isinstance(source, ConfigImplSource):
            for pi in self._ctx.get_configs(self._spec.root).get(PolymorphismImpl) or ():
                raws.append(_RawImpl(pi.impl_ty, pi.impl_ty.__name__, pi.tag, tuple(pi.alts or ())))

        elif isinstance(source, ManifestImplSource):
            for v in _impl_for_manifests_by_base_path().get(_cls_path(self._spec.root), ()):
                raws.append(_manifest_raw_impl(v))

        else:
            raise TypeError(source)

        return raws, bases

    #

    def _merge_raws(self, raws: ta.Iterable[_RawImpl]) -> list[_RawImpl]:
        # Eagerly resolve manifest entries (importing their modules), then dedupe by ty - the same class may arrive
        # from several sources (a manifest-declared impl is also found by the subclass scan once imported).
        by_ty: dict[type, _RawImpl] = {}

        for r in raws:
            if (ty := r.ty) is None:
                ty = check.isinstance(check.not_none(r.resolve)(), type)
                r = r._replace(ty=ty, resolve=None)

            if (x := by_ty.get(ty)) is None:
                by_ty[ty] = r
                continue

            if x.tag is not None and r.tag is not None and x.tag != r.tag:
                raise PolymorphismImplError(
                    f'Conflicting explicit tags for impl {ty!r} of {self._spec.root!r}: {x.tag!r}, {r.tag!r}',
                )

            by_ty[ty] = x._replace(
                tag=x.tag if x.tag is not None else r.tag,
                alts=(*x.alts, *(a for a in r.alts if a not in x.alts)),
            )

        return list(by_ty.values())

    def _derive_tags(self, raws: ta.Sequence[_RawImpl]) -> list[Impl]:
        spec = self._spec

        derived = [r for r in raws if r.tag is None]

        ssx: str | None
        strip_suffix: ta.Any = spec.strip_suffix
        if strip_suffix is AUTO_STRIP_SUFFIX:
            strip_suffix = all(r.name.endswith(spec.root.__name__) for r in derived)
        if isinstance(strip_suffix, bool):
            ssx = spec.root.__name__ if strip_suffix else None
        elif isinstance(strip_suffix, str):
            ssx = strip_suffix
        else:
            raise TypeError(strip_suffix)

        out: list[Impl] = []
        for r in raws:
            if (tag := r.tag) is None:
                tag = r.name
                if ssx is not None:
                    tag = lang.must_remove_suffix(tag, ssx)
                if spec.naming is not None:
                    tag = translate_name(tag, spec.naming)

            out.append(Impl(
                check.not_none(r.ty),
                tag,
                frozenset(r.alts),
            ))

        return out

    def _check_impls(self, impls: ta.Sequence[Impl]) -> None:
        by_tag: dict[str, Impl] = {}
        for i in impls:
            for t in (i.tag, *i.alts):
                if (x := by_tag.get(t)) is not None:
                    raise PolymorphismImplError(
                        f'Conflicting tag {t!r} for {self._spec.root!r}: {x.ty!r}, {i.ty!r}',
                    )
                by_tag[t] = i

    #

    def _build_bases(self, base_tys: ta.Iterable[type], impls: ta.Sequence[Impl]) -> ImplBases | None:
        lst: list[ImplBase] = []
        for b in base_tys:
            if (b_impls := frozenset(i.ty for i in impls if issubclass(i.ty, b))):
                lst.append(ImplBase(b, b_impls))

        if not lst:
            return None
        return ImplBases(lst)

    #

    def _restrict(self, poly: Polymorphism) -> Polymorphism:
        if (only := self._spec.only) is None:
            return poly

        if any(m is self._spec.root for m in only):
            return poly

        m_tys: set[type] = set()
        for m in only:
            if m in poly.impls.by_ty:
                m_tys.add(m)
            elif poly.bases is not None and (ib := poly.bases.by_ty.get(m)) is not None:
                m_tys.update(ib.impl_tys)
            else:
                raise PolymorphismImplError(
                    f'Union member {m!r} is not a resolved impl (or impl base) of {self._spec.root!r}',
                )

        return Polymorphism(
            self._spec.root,
            Impls([poly.impls.by_ty[t] for t in m_tys]),
            bases=poly.bases,
        )

    #

    def resolve(self) -> Polymorphism:
        raws: list[_RawImpl] = []
        base_tys: list[type] = []
        for source in self._spec.sources:
            s_raws, s_bases = self._collect_source(source)
            raws.extend(s_raws)
            base_tys.extend(s_bases)

        merged = self._merge_raws(raws)
        if not merged:
            raise PolymorphismImplError(f'No impls resolved for {self._spec.root!r} from {self._spec.sources!r}')

        impls = self._derive_tags(merged)
        self._check_impls(impls)

        poly = Polymorphism(
            self._spec.root,
            impls,
            bases=self._build_bases(base_tys, impls),
        )

        return self._restrict(poly)


def resolve_polymorphism(ctx: BaseFactoryContext, spec: PolymorphismSpec) -> Polymorphism:
    return _PolymorphismResolver(ctx, spec).resolve()
