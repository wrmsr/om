import pytest

from ...tests.tools import bare_tool
from ...types.states import State
from ...types.tools import ToolSet
from ...types.turns import TurnConfig
from ..errors import UnknownSubagentToolsError
from ..profiles import DEFAULT_SUBAGENT_MAX_TURNS
from ..profiles import GENERAL_SUBAGENT_PROFILE
from ..profiles import SubagentProfile
from ..profiles import SubagentProfiles
from ..profiles import apply_subagent_profile
from ..profiles import explore_subagent_profile


##


async def _unused(ctx):
    raise AssertionError


def _pool(*names):
    return ToolSet([bare_tool(n, _unused) for n in names])


def test_profile_without_tool_names_takes_the_whole_pool():
    pool = _pool('a', 'b')
    assert GENERAL_SUBAGENT_PROFILE.select_tools(pool) is pool


def test_profile_selects_named_tools_in_pool_order():
    profile = SubagentProfile(name='p', description='d', tool_names=['c', 'a'])
    assert isinstance(profile.tool_names, frozenset)

    selected = profile.select_tools(_pool('a', 'b', 'c'))
    assert [t.name for t in selected] == ['a', 'c']


def test_profile_naming_a_missing_tool_is_an_error_not_an_omission():
    profile = SubagentProfile(name='p', description='d', tool_names=['a', 'z', 'y'])

    with pytest.raises(UnknownSubagentToolsError) as ei:
        profile.select_tools(_pool('a', 'b'))

    assert ei.value.profile == 'p'
    assert list(ei.value.tool_names) == ['y', 'z']


def test_profiles_are_looked_up_by_name_and_the_first_is_the_default():
    explore = explore_subagent_profile(['a'])
    profiles = SubagentProfiles([GENERAL_SUBAGENT_PROFILE, explore])

    assert profiles.default is GENERAL_SUBAGENT_PROFILE
    assert profiles['explore'] is explore
    assert profiles[1] is explore
    assert [p.name for p in profiles] == ['general', 'explore']
    assert len(profiles) == 2

    with pytest.raises(KeyError):
        profiles['nope']  # noqa


def test_profiles_reject_duplicates_and_emptiness():
    with pytest.raises(Exception):  # noqa
        SubagentProfiles([GENERAL_SUBAGENT_PROFILE, GENERAL_SUBAGENT_PROFILE])

    with pytest.raises(Exception):  # noqa
        SubagentProfiles([])


def test_profiles_validate_every_profile_against_the_pool():
    profiles = SubagentProfiles([GENERAL_SUBAGENT_PROFILE, explore_subagent_profile(['a', 'z'])])

    profiles.validate_tools(_pool('a', 'z'))

    with pytest.raises(UnknownSubagentToolsError):
        profiles.validate_tools(_pool('a'))


def test_apply_profile_sets_the_turn_limit_and_keeps_the_rest():
    assert apply_subagent_profile(State(), GENERAL_SUBAGENT_PROFILE).turn_config == TurnConfig(
        max_turns=DEFAULT_SUBAGENT_MAX_TURNS,
    )

    state = State(turn_config=TurnConfig(max_turns=3, max_concurrent_tool_calls=2))
    profile = SubagentProfile(name='p', description='d', max_turns=None)
    assert apply_subagent_profile(state, profile).turn_config == TurnConfig(max_concurrent_tool_calls=2)
