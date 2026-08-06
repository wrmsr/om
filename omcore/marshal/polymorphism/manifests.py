# ruff: noqa: UP006 UP007 UP045
"""
Deliberately dumb, static manifest data: an `ImplForManifest` names its polymorphic base (as a dotted path string,
optionally `$.`-prefixed as package-root-relative) and rides the stock ModAttrManifest machinery for its own
module/attr. It knows nothing about naming or tagging - tags are derived at runtime from the base's current
configuration using the manifest's `attr` (the impl class name); the optional `tag`/`alts` overrides are the
exception, not the rule.

Usage - a hot comment above the impl class def:

    # @om-manifest omcore.marshal.ImplForManifest(base='$.agent.events.Event')
    class MessageSentEvent(Event):
        ...

This module must remain dependency-light and lite-unmarshalable: manifest values are instantiated by the lite marshal
system, potentially in contexts where nothing else of the marshal package is loaded.
"""
import dataclasses as dc
import typing as ta

from ...manifests.base import ModAttrManifest


##


@dc.dataclass(frozen=True)
class ImplForManifest(ModAttrManifest):
    base: str

    tag: ta.Optional[str] = None
    alts: ta.Optional[ta.Sequence[str]] = None

    def resolve_base_path(self) -> str:
        """The base's absolute dotted path, with a `$.` prefix expanded against this manifest's own package root."""

        if self.base.startswith('$.'):
            return f'{self.module.split(".")[0]}{self.base[1:]}'
        return self.base
