"""
The metadata-driven spec derivers: classes decorated `set_polymorphic_from_subclasses` (and unions of their
subtypes) resolve to PolymorphismSpecs and re-enter construction. The spec's sources unify the collection flavors -
subclass scanning, config-registered subtypes, and manifest-declared subtypes all contribute, deduped by the resolver.

There is no cache here: spec resolution happens at (runtime-cached, footprint-invalidated) handler construction, so -
unlike the old permanently-baked global PolymorphismMetadataCache - a Runtime.flush() genuinely resets
subclass-derived polymorphisms, and late config-registered impls invalidate precisely.
"""
import typing as ta

from ... import check
from ... import metadata as md
from ... import reflect as rfl
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import DuplexFactory
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from .api import ConfigsSubtypeSource
from .api import ManifestsSubtypeSource
from .api import SubclassesSubtypeSource
from .api import SubtypeSource
from .api import _PolymorphismMetadata
from .specs import DisjointPolymorphismSpec
from .specs import PolymorphismSpec


##


_DEFAULT_METADATA_SUBTYPE_SOURCES: ta.Mapping[str, SubtypeSource] = {
    'subclasses': SubclassesSubtypeSource(),
    'configs': ConfigsSubtypeSource(),
    'manifests': ManifestsSubtypeSource(),
}


def _get_polymorphism_metadata(cls: type) -> _PolymorphismMetadata | None:
    if not md.has_object_metadata(cls):
        return None

    return md.get_single_object_metadata(cls, type=_PolymorphismMetadata)


def _make_metadata_spec(
        cls: type,
        pmd: _PolymorphismMetadata,
        *,
        only: ta.Sequence[type] | None = None,
) -> PolymorphismSpec:
    return PolymorphismSpec(
        root=cls,
        sources=pmd.sources,
        tagging=pmd.type_tagging,
        naming=pmd.naming,
        suffix_stripping=pmd.suffix_stripping,
        only=only,
    )


##


class PolymorphismMetadataFactory(DuplexFactory):
    """Derives PolymorphismSpecs from classes bearing polymorphism metadata."""

    def _derive_spec(self, spec: Spec) -> PolymorphismSpec | None:
        if not isinstance(spec, rfl.Type):
            return None

        if (cls := rfl.get_runtime_type_or_none(spec)) is None:
            return None

        if (pmd := _get_polymorphism_metadata(cls)) is None:
            return None

        return _make_metadata_spec(cls, pmd)

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_marshaler(psp)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_unmarshaler(psp)


##


class PolymorphismMetadataUnionFactory(DuplexFactory):
    """
    Derives specs from unions whose members each have a nearest metadata-decorated ancestor: a single shared root
    resolves to that root's PolymorphismSpec restricted to the members, while members spanning multiple roots
    resolve to a DisjointPolymorphismSpec of per-root specs (each with its own member restriction, each resolving
    entirely under its own root's configuration - constituents must agree on tagging). A member equal to its root
    lifts that root's restriction.
    """

    def _find_metadata_root(self, cls: type) -> type | None:
        for mro_cls in cls.__mro__[:-1]:
            if _get_polymorphism_metadata(mro_cls) is not None:
                return mro_cls
        return None

    def _derive_spec(self, spec: Spec) -> PolymorphismSpec | DisjointPolymorphismSpec | None:
        if not isinstance(spec, rfl.UnionType):
            return None

        tys = [rfl.get_runtime_type_or_none(it) for it in spec.items]
        if any(t is None for t in tys):
            return None
        members = ta.cast('list[type]', tys)

        by_root: dict[type, list[type]] = {}
        for m in members:
            if (root := self._find_metadata_root(m)) is None:
                return None
            by_root.setdefault(root, []).append(m)

        # Canonically ordered so differently-ordered union annotations (distinct reflected types) converge on the
        # same value-keyed spec and share one handler.
        specs = [
            _make_metadata_spec(
                root,
                check.not_none(_get_polymorphism_metadata(root)),
                only=None if root in ms else ms,
            )
            for root, ms in sorted(by_root.items(), key=lambda kv: (kv[0].__module__, kv[0].__qualname__))
        ]

        if len(specs) == 1:
            return specs[0]

        return DisjointPolymorphismSpec(specs)

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_marshaler(psp)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_unmarshaler(psp)
