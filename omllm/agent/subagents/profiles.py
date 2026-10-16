"""
A profile is what a subagent is spawned *as*: its instructions, which of the tools around it it gets, and how long it
may run. The set of profiles a subagent tool offers is fixed when the tool is built, and the model picks one by name.

Tools are selected by name here. That is a weak linkage - a profile and the tool pool it is applied to are assembled
separately, and agree only by convention - so a profile naming a tool the pool does not have is an error wherever it is
applied, never a silent omission. See DESIGN.md for where this is meant to go.
"""
import typing as ta

from omcore import cached
from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang

from ..types.states import State
from ..types.tools import ToolSet
from ..types.turns import TurnConfig
from .errors import UnknownSubagentToolsError


##


# How many LLM calls a subagent may make before it is cut short, unless its profile says otherwise. A subagent has
# nobody watching it, so an unbounded run is not the right default.
DEFAULT_SUBAGENT_MAX_TURNS: int = 30


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SubagentProfile:
    name: str = dc.xfield(validate=lambda v: bool(v))

    # Shown to the model in the subagent tool's description, so it can pick.
    description: str

    system_prompt: str | None = None

    # The names of the tools the subagent gets, out of the pool it is spawned from. None is the whole pool.
    tool_names: ta.Iterable[str] | None = dc.xfield(
        None,
        coerce=lambda v: frozenset(v) if v is not None else None,
    )

    # None is unbounded.
    max_turns: int | None = DEFAULT_SUBAGENT_MAX_TURNS

    def select_tools(self, tools: ToolSet) -> ToolSet:
        """The profile's tools out of the given pool, in the pool's order. Raises if the pool lacks any of them."""

        if (names := self.tool_names) is None:
            return tools

        names = check.isinstance(names, frozenset)
        if (missing := sorted(names - tools.by_name.keys())):
            raise UnknownSubagentToolsError(self.name, missing)

        return ToolSet([t for t in tools if t.name in names])


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class SubagentProfiles(ta.Sequence[SubagentProfile]):
    """The profiles a subagent tool offers. The first is the default - what the model gets when it names none."""

    profiles: ta.Sequence[SubagentProfile]

    def __post_init__(self) -> None:
        check.not_empty(self.profiles)

    @cached.property
    @dc.init
    def by_name(self) -> ta.Mapping[str, SubagentProfile]:
        return col.make_map(((p.name, p) for p in self.profiles), strict=True)

    @property
    def default(self) -> SubagentProfile:
        return self.profiles[0]

    def validate_tools(self, tools: ToolSet) -> None:
        """Raises UnknownSubagentToolsError for the first profile naming a tool the pool does not have."""

        for p in self.profiles:
            p.select_tools(tools)

    #

    def __iter__(self) -> ta.Iterator[SubagentProfile]:
        return iter(self.profiles)

    def __len__(self) -> int:
        return len(self.profiles)

    @ta.overload
    def __getitem__(self, index: int | str, /) -> SubagentProfile:
        ...

    @ta.overload
    def __getitem__(self, index: slice, /) -> ta.Sequence[SubagentProfile]:  # noqa
        ...

    def __getitem__(self, index):
        if isinstance(index, str):
            return self.by_name[index]
        else:
            return self.profiles[index]


##


def apply_subagent_profile(state: State, profile: SubagentProfile) -> State:
    """
    The profile's turn configuration, onto a state otherwise set up for the subagent: its tools and system prompt are
    the business of whoever builds that state, since where they come from differs by host.
    """

    turn_config = state.turn_config if state.turn_config is not None else TurnConfig()

    return dc.replace(
        state,
        turn_config=dc.replace(
            turn_config,
            max_turns=profile.max_turns,
        ),
    )


##


GENERAL_SUBAGENT_PROFILE_NAME: str = 'general'

GENERAL_SUBAGENT_PROFILE: SubagentProfile = SubagentProfile(
    name=GENERAL_SUBAGENT_PROFILE_NAME,
    description=(
        'A general-purpose subagent with the same tools as you, for a self-contained multi-step task: an '
        'investigation, a change to make, a thing to build and verify.'
    ),
    system_prompt=(
        'Carry out the task you were given completely and autonomously, using your tools as needed, and then report '
        'the outcome: what you did, what you found, and anything the requester must know.'
    ),
)


EXPLORE_SUBAGENT_PROFILE_NAME: str = 'explore'


def explore_subagent_profile(tool_names: ta.Iterable[str]) -> SubagentProfile:
    """
    A read-only investigator. Which tools are read-only is for whoever assembles the tool pool to say, which is why the
    names are given rather than fixed here.
    """

    return SubagentProfile(
        name=EXPLORE_SUBAGENT_PROFILE_NAME,
        description=(
            'A read-only subagent for exploration: searching and reading code, files, and the web, and reporting what '
            'it finds. It cannot modify anything. Prefer it for research and lookups whose details you do not need in '
            'your own context.'
        ),
        system_prompt=(
            'You are an explorer: investigate the question you were given using your read-only tools and report your '
            'findings precisely - with file paths, line numbers, names, and short quotations where they matter. Do not '
            'attempt to modify anything, and do not speculate beyond what you found.'
        ),
        tool_names=tool_names,
    )
