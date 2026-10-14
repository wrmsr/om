import tempfile

import pytest

from ....core import processes
from ....core import ui
from ..base import CommandContext
from ..processes import ProcessesCommand


class _Capture:
    def __init__(self):
        self.lines: list[str] = []

    async def __call__(self, *texts):
        self.lines.append(ui.Text.str_of(list(texts)))

    @property
    def last(self) -> str:
        return self.lines[-1]


@pytest.mark.asyncs('asyncio')
async def test_processes_command_list_and_kill():
    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            p1 = await m.root.spawn(processes.ProcessSpec(['sleep', '30'], cwd=td, name='sleeper'))
            p2 = await m.root.spawn(processes.ProcessSpec(['sh', '-c', 'exit 0'], cwd=td))
            await p2.wait(2.0)  # exits, stays a held (unreaped) zombie in the registry

            cmd = ProcessesCommand(m)
            assert cmd.name == 'processes'

            cap = _Capture()
            ctx = CommandContext(print=cap)

            # default (no subcommand) == list
            await cmd.run(ctx, [])
            listed = cap.last
            assert p1.id in listed and p2.id in listed
            assert 'running' in listed and 'exited' in listed
            assert 'name:"sleeper"' in listed          # json5: unquoted key, quoted value
            assert '"sleep"' in listed and '"30"' in listed
            assert 'returncode:0' in listed            # exited proc shows its rc

            # explicit 'list' is the same view as the default (elapsed_s aside)
            await cmd.run(ctx, ['list'])
            assert p1.id in cap.last and p2.id in cap.last

            # kill p1
            await cmd.run(ctx, ['kill', p1.id])
            assert p1.id in cap.last and 'killed' in cap.last
            assert 'returncode:-15' in cap.last        # SIGTERM
            assert p1.id not in m.processes            # reaped, gone from the registry

            # p1 no longer listed
            await cmd.run(ctx, [])
            assert p1.id not in cap.last and p2.id in cap.last

            # unknown id
            await cmd.run(ctx, ['kill', 'p999'])
            assert cap.last == 'No such process: p999'

            # force kill the leftover exited zombie
            await cmd.run(ctx, ['kill', '-f', p2.id])
            assert p2.id in cap.last and 'killed' in cap.last
            assert not m.processes

            # empty
            await cmd.run(ctx, [])
            assert cap.last == 'No processes'
