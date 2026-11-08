import typing as ta

from omcore import lang

from ..manager import SystemPromptManager
from ..types import SystemPromptContributor
from ..types import SystemPromptContributors
from ..types import SystemPromptPart
from ..types import SystemPromptPriority


class _Sync(SystemPromptContributor):
    def __init__(self, *parts: SystemPromptPart) -> None:
        super().__init__()

        self._parts = parts

    def get_system_prompt_parts(self) -> ta.Sequence[SystemPromptPart] | None:
        return self._parts or None


class _Async(SystemPromptContributor):
    def __init__(self, *parts: SystemPromptPart) -> None:
        super().__init__()

        self._parts = parts

    async def get_system_prompt_parts(self) -> ta.Sequence[SystemPromptPart] | None:
        return self._parts or None


def _build(*contributors: SystemPromptContributor) -> str:
    return lang.sync_await(SystemPromptManager(SystemPromptContributors(list(contributors))).build_system_prompt())


def test_empty():
    assert _build() == ''
    assert _build(_Sync(), _Async()) == ''
    assert lang.sync_await(SystemPromptManager().build_system_prompt()) == ''


def test_sync_and_async_contributors_are_ordered_by_priority_then_text():
    out = _build(
        _Async(
            SystemPromptPart(SystemPromptPriority.ENVIRONMENT, 'env'),
            SystemPromptPart(SystemPromptPriority.MISSION, 'mission'),
        ),
        _Sync(
            SystemPromptPart(SystemPromptPriority.USER, 'user b'),
            SystemPromptPart(SystemPromptPriority.LAST, '  '),
        ),
        _Async(SystemPromptPart(SystemPromptPriority.USER, 'user a')),
        _Sync(SystemPromptPart(SystemPromptPriority.FIRST, ' first \n')),
    )

    assert out == '\n\n'.join(['first', 'mission', 'user a', 'user b', 'env'])


def test_duplicate_text_is_said_once():
    part = SystemPromptPart(SystemPromptPriority.TOOLS, 'prefer the fs tools')

    assert _build(_Sync(part), _Async(part)) == 'prefer the fs tools'
