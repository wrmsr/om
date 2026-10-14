import pytest

from .... import agent as agn
from ....core import ui
from ..base import CommandContext
from ..permissions import PermissionsCommand


##


class _Capture:
    def __init__(self):
        self.lines: list[str] = []

    async def __call__(self, *texts):
        self.lines.append(ui.Text.str_of(list(texts)))


@pytest.mark.asyncs('asyncio')
async def test_add_shows_the_rule_added_and_list_shows_them_all():
    cmd = PermissionsCommand(agn.StandardPermissionsManager())
    cap = _Capture()
    ctx = CommandContext(print=cap)

    await cmd.run(ctx, ['add', 'allow', 'exec', '{}'])
    await cmd.run(ctx, ['add', 'ask', 'tool', '{"tool":"ripgrep","child":{"exec": {}}}'])

    # Each add shows the one rule it added - a single line, on its own, with its index, digest, and state.
    assert len(cap.lines) == 2
    first, second = cap.lines
    assert '\n' not in first and first.startswith('#0 ') and ' allow ' in first and 'exec' in first
    assert '\n' not in second and second.startswith('#1 ') and ' ask ' in second and 'ripgrep' in second

    await cmd.run(ctx, ['list'])
    assert cap.lines[-1] == '\n'.join([first, second])
