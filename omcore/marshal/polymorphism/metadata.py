"""
The metadata-driven spec derivers: classes decorated `set_polymorphic_from_subclasses` (and unions of their
subtypes) resolve to PolymorphismSpecs and re-enter construction. The spec's sources unify the collection flavors -
subclass scanning, config-registered subtypes, and manifest-declared subtypes all contribute, deduped by the resolver.

There is no cache here: spec resolution happens at (runtime-cached, footprint-invalidated) handler construction, so -
unlike the old permanently-baked global PolymorphismMetadataCache - a Runtime.flush() genuinely resets
subclass-derived polymorphisms, and late config-registered impls invalidate precisely.
"""
import typing as ta

from ... import metadata as md
from ... import reflect as rfl
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import DuplexFactory
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from .api import _PolymorphismMetadata
from .specs import ConfigSubtypeSource
from .specs import ManifestSubtypeSource
from .specs import PolymorphismSpec
from .specs import SubclassesSubtypeSource
from .specs import SubtypeSource


##


_DEFAULT_METADATA_SUBTYPE_SOURCES: tuple[SubtypeSource, ...] = (
    SubclassesSubtypeSource(),
    ConfigSubtypeSource(),
    ManifestSubtypeSource(),
)


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
    if pmd.mode != 'subclasses':
        raise RuntimeError(f'Unsupported polymorphism mode: {pmd.mode}')

    return PolymorphismSpec(
        root=cls,
        sources=_DEFAULT_METADATA_SUBTYPE_SOURCES,
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
    Derives PolymorphismSpecs from unions whose members all share a single nearest metadata-decorated ancestor,
    resolving to that root's PolymorphismSpec restricted to the members. A member equal to the root lifts the
    restriction (the union degenerates to the full polymorphism).
    """

    def _find_metadata_root(self, cls: type) -> type | None:
        for mro_cls in cls.__mro__[:-1]:
            if _get_polymorphism_metadata(mro_cls) is not None:
                return mro_cls
        return None

    def _derive_spec(self, spec: Spec) -> PolymorphismSpec | None:
        if not isinstance(spec, rfl.UnionType):
            return None

        tys = [rfl.get_runtime_type_or_none(it) for it in spec.items]
        if any(t is None for t in tys):
            return None
        members = ta.cast('list[type]', tys)

        roots = {self._find_metadata_root(m) for m in members}
        if len(roots) != 1 or (root := roots.pop()) is None:
            return None

        pmd = _get_polymorphism_metadata(root)
        if pmd is None:
            return None

        return _make_metadata_spec(
            root,
            pmd,
            only=None if root in members else members,
        )

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_marshaler(psp)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if (psp := self._derive_spec(spec)) is None:
            return None

        return lambda: ctx.make_unmarshaler(psp)
