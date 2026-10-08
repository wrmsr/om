import pytest

from omcore import lang

from .... import llm
from ....core import ui
from ...fs.permissions import FsPermissionTarget
from ...fs.permissions import GlobFsPermissionMatcher
from ...types.tools import Tool
from ...types.tools import ToolContext
from ..deciders import StandardPermissionDecider
from ..managers import StandardPermissionsManager
from ..tools import ToolPermissionMatcher
from ..types import PermissionAsker
from ..types import PermissionDeniedError
from ..types import PermissionRequest
from ..types import PermissionRequestor
from ..types import PermissionRule
from ..types import PermissionState


##


class _RecordingAsker(PermissionAsker):
    def __init__(self, answer):
        super().__init__()

        self._answer = answer
        self.asked = []

    async def ask(self, request, rule):
        self.asked.append((request, rule))
        return self._answer


async def _unused_executor(ctx):
    raise AssertionError


def _requestor(tool_name):
    return PermissionRequestor(tool_context=ToolContext(
        tool=Tool(llm_tool=llm.Tool(name=tool_name), executor=_unused_executor),
        args={},
    ))


def _decider(asker, *rules):
    return StandardPermissionDecider(
        manager=StandardPermissionsManager(list(rules)),
        asker=asker,
    )


def test_rules_match_the_request_and_the_asker_gets_it_whole():
    rule = PermissionRule(
        ToolPermissionMatcher('edit', GlobFsPermissionMatcher('/w/**', ['w'])),
        PermissionState.ASK,
    )
    asker = _RecordingAsker(PermissionState.ALLOW)
    decider = _decider(asker, rule)

    request = PermissionRequest(
        _requestor('edit'),
        FsPermissionTarget('/w/f.py', 'w'),
        preview=ui.DiffText(old='a\n', new='b\n', path='/w/f.py'),
    )
    assert lang.sync_await(decider.decide(request)) is PermissionState.ALLOW

    # The preview rides through to whoever is asked, untouched.
    [(asked, asked_rule)] = asker.asked
    assert asked is request
    assert asked_rule is rule

    # Matching is on the requestor and target alone: a different tool, or path, matches nothing and is denied unasked.
    for unmatched in [
        PermissionRequest(_requestor('write'), FsPermissionTarget('/w/f.py', 'w')),
        PermissionRequest(_requestor('edit'), FsPermissionTarget('/elsewhere/f.py', 'w')),
    ]:
        assert lang.sync_await(decider.decide(unmatched)) is PermissionState.DENY
    assert len(asker.asked) == 1


def test_check_allowed_raises_denial_with_the_target():
    asker = _RecordingAsker(PermissionState.DENY)
    decider = _decider(asker, PermissionRule(GlobFsPermissionMatcher('/w/**'), PermissionState.ASK))

    target = FsPermissionTarget('/w/f.py', 'w')
    with pytest.raises(PermissionDeniedError) as ei:
        lang.sync_await(decider.check_allowed(PermissionRequest(_requestor('edit'), target)))
    assert ei.value.target == target
