"""
The direction-agnostic 'what' of a polymorphism: a root type plus the declared *sources* its subtypes are collected
from, plus the tagging/naming behaviors - divorced from how the polymorphism was requested (metadata decorator, union
annotation, hand construction). The PolymorphismSpecMarshalerFactory / PolymorphismSpecUnmarshalerFactory pair
consumes these by resolving the sources (see `resolving.py`) into the classic `Polymorphism` and handing off to the
trivial handlers.

Per the InternalSpec contract these are values - hashable and compared by value, serving as their own handler cache
keys. Note that unlike ObjectSpecs, PolymorphismSpec *consumption* is deliberately not config-free: late-binding
sources (config-registered subtypes, subclass scans, manifests) resolve at handler construction, with registry reads
landing in the entry's config footprint.
"""
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..api.naming import Naming
from ..api.specs import InternalSpec
from .api import AUTO_STRIP_SUFFIX
from .api import SubtypeInfos
from .api import TypeTagging
from .api import WrapperTypeTagging


##


class SubtypeSource(lang.Abstract):
    """Sources are values: immutable, hashable, compared by value."""


@ta.final
@dc.dataclass(frozen=True)
class ExplicitSubtypeSource(SubtypeSource, lang.Final):
    """Carries final, already-tagged subtype infos - passes through tag derivation untouched."""

    subtypes: SubtypeInfos


@ta.final
@dc.dataclass(frozen=True)
class SubclassesSubtypeSource(SubtypeSource, lang.Final):
    """
    Deep-scans the root's subclasses at resolve time. Note the sharp edge: subclasses imported after handler
    construction are invisible until something invalidates the handler (a config change observed in its footprint, or
    a Runtime.flush()).
    """


@ta.final
@dc.dataclass(frozen=True)
class ConfigSubtypeSource(SubtypeSource, lang.Final):
    """
    Reads `SubtypeConfig` configs registered under the root's key. The read lands in the handler's config footprint,
    so late registrations invalidate and rebuild affected handlers.
    """


@ta.final
@dc.dataclass(frozen=True)
class ManifestSubtypeSource(SubtypeSource, lang.Final):
    """
    Collects `SubtypeManifest` entries whose (resolved) base path names the root - letting subtypes scattered across
    lazily-imported modules be discovered without importing them. Matched entries' modules are imported eagerly at
    handler construction; tags are derived from the manifests' attr (class name) strings per the spec's naming
    configuration unless explicitly overridden on the manifest.
    """


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True)
class PolymorphismSpec(InternalSpec, lang.Final):
    root: type

    sources: ta.Sequence[SubtypeSource] = dc.xfield(coerce=tuple)

    tagging: TypeTagging = WrapperTypeTagging()

    naming: Naming | None = None
    strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False

    # Restricts the resolved subtype set to these member types (expanding abstract intermediates) - the union case. A
    # member equal to the root lifts the restriction entirely.
    only: ta.Sequence[type] | None = dc.xfield(default=None, coerce=lang.opt_fn(tuple))

    def __post_init__(self) -> None:
        check.not_empty(self.sources)
