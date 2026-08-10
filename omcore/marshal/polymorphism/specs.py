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
from .api import PolymorphismSubtypeError
from .api import PolymorphismTaggingError
from .api import SubtypeSource
from .api import SuffixStripping
from .api import TypeTagging
from .api import WrapperTypeTagging


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True)
class PolymorphismSpec(InternalSpec, lang.Final):
    root: type

    sources: ta.Sequence[SubtypeSource] = dc.xfield(coerce=tuple)

    tagging: TypeTagging = WrapperTypeTagging()

    naming: Naming | None = None
    suffix_stripping: SuffixStripping | None = None

    # Restricts the resolved subtype set to these member types (expanding abstract intermediates) - the union case. A
    # member equal to the root lifts the restriction entirely.
    only: ta.Sequence[type] | None = dc.xfield(default=None, coerce=lang.opt_fn(tuple))

    def __post_init__(self) -> None:
        check.not_empty(self.sources)


##


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class DisjointPolymorphismSpec(InternalSpec, lang.Final):
    """
    The multi-root union case - `llm.Message | AgentMessage` - as a merger of ordinary per-root specs. There is
    deliberately no merger-level naming or restriction: each constituent resolves entirely under its own root's
    configuration (so subtypes keep their exact single-root wire tags), and union restrictions distribute into the
    constituents' `only`s. All constituents must agree on tagging - wrapper and field tagging cannot mix.
    """

    specs: ta.Sequence[PolymorphismSpec] = dc.xfield(coerce=tuple)

    def __post_init__(self) -> None:
        check.arg(len(self.specs) > 1)
        for s in self.specs:
            check.isinstance(s, PolymorphismSpec)

        if len({id(s.root) for s in self.specs}) != len(self.specs):
            raise PolymorphismSubtypeError(f'Duplicate roots: {[s.root for s in self.specs]!r}')

        if len({s.tagging for s in self.specs}) != 1:
            raise PolymorphismTaggingError(
                f'Constituent specs must agree on tagging: {[s.tagging for s in self.specs]!r}',
            )

    @property
    def tagging(self) -> TypeTagging:
        return self.specs[0].tagging
