"""
The direction-agnostic 'what' of a polymorphism: a root type plus the declared *sources* its impls are collected from,
plus the tagging/naming behaviors - divorced from how the polymorphism was requested (metadata decorator, union
annotation, hand construction). The PolymorphismSpecMarshalerFactory / PolymorphismSpecUnmarshalerFactory pair
consumes these by resolving the sources (see `resolving.py`) into the classic `Polymorphism` and handing off to the
trivial handlers.

Per the InternalSpec contract these are values - hashable and compared by value, serving as their own handler cache
keys. Note that unlike ObjectSpecs, PolymorphismSpec *consumption* is deliberately not config-free: late-binding
sources (config-registered impls, subclass scans, manifests) resolve at handler construction, with registry reads
landing in the entry's config footprint.
"""
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..api.naming import Naming
from ..api.specs import InternalSpec
from .api import AUTO_STRIP_SUFFIX
from .api import Impl
from .api import TypeTagging
from .api import WrapperTypeTagging


##


class ImplSource(lang.Abstract):
    """Sources are values: immutable, hashable, compared by value."""


@ta.final
@dc.dataclass(frozen=True)
class ExplicitImplSource(ImplSource, lang.Final):
    impls: ta.Sequence[Impl] = dc.xfield(coerce=tuple)


@ta.final
@dc.dataclass(frozen=True)
class SubclassesImplSource(ImplSource, lang.Final):
    """
    Deep-scans the root's subclasses at resolve time (including intermediate abstract bases). Note the sharp edge:
    subclasses imported after handler construction are invisible until something invalidates the handler (a config
    change observed in its footprint, or a Runtime.flush()).
    """


@ta.final
@dc.dataclass(frozen=True)
class ConfigImplSource(ImplSource, lang.Final):
    """
    Reads `PolymorphismImpl` configs registered under the root's key. The read lands in the handler's config
    footprint, so late registrations invalidate and rebuild affected handlers.
    """


@ta.final
@dc.dataclass(frozen=True)
class ManifestImplSource(ImplSource, lang.Final):
    """
    Collects `ImplForManifest` entries whose (resolved) base path names the root - letting impls scattered across
    lazily-imported modules be discovered without importing them. Matched entries' modules are imported eagerly at
    handler construction; tags are derived from the manifests' attr (class name) strings per the spec's naming
    configuration unless explicitly overridden on the manifest.
    """


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class PolymorphismSpec(InternalSpec, lang.Final):
    root: type

    sources: ta.Sequence[ImplSource] = dc.xfield(coerce=tuple)

    tagging: TypeTagging = WrapperTypeTagging()

    naming: Naming | None = None
    strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False

    # Restricts the resolved impl set to these member types (expanding intermediate abstract bases) - the union case.
    # A member equal to the root lifts the restriction entirely.
    only: ta.Sequence[type] | None = dc.xfield(default=None, coerce=lang.opt_fn(tuple))

    def __post_init__(self) -> None:
        check.not_empty(self.sources)
