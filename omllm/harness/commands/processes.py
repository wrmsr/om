import signal
import time
import typing as ta

from omcore import check
from omcore import lang
from omcore.argparse import all as ap

from ...core import processes
from ...core import ui
from .base import CommandContext
from .classes import ParserCommandClass


##


class ProcessesCommand(ParserCommandClass):
    """
    Inspects and manages the processes owned by the process manager (the same ones the agent's process_* tools
    see).
    """

    def __init__(self, processes: processes.ProcessManager) -> None:
        super().__init__()

        self._processes = processes

    #

    _STATE_COLORS: ta.ClassVar[ta.Mapping[processes.ProcessState, ui.TextColor]] = {
        processes.ProcessState.SPAWNING: 'blue',
        processes.ProcessState.RUNNING: 'green',
        processes.ProcessState.EXITED: 'yellow',
        processes.ProcessState.REAPED: 'yellow',
        processes.ProcessState.ABANDONED: 'red',
        processes.ProcessState.POISONED: 'red',
    }

    _STATE_NAME_LEN: ta.ClassVar[int] = max(len(s.name) for s in processes.ProcessState)

    _JSON_STYLE: ta.ClassVar = ui.JsonTextStyle(
        mode='compact',
        five=True,
        unquote_idents=True,
    )

    def _process_body(self, p: processes.Process) -> ta.Mapping[str, ta.Any]:
        body: dict[str, ta.Any] = {
            'pid': p.pid,
            'argv': list(p.spec.argv),
        }
        if p.name is not None:
            body['name'] = p.name
        if p.returncode is not None:
            body['returncode'] = p.returncode
        body['elapsed_s'] = round(time.time() - p.created_at, 1)
        body['scope'] = '/'.join(p.scope.path)
        return body

    def _render_process(self, p: processes.Process) -> ui.CanText:
        return list(lang.interleave(' ' * 2, [
            ui.Text.style(p.id, bold=True),
            ui.Text.style(
                p.state.name.lower().ljust(self._STATE_NAME_LEN),
                bold=True,
                color=self._STATE_COLORS[p.state],
            ),
            ui.JsonText(self._process_body(p), self._JSON_STYLE),
        ]))

    #

    @ap.cmd(
        name='list',
        default=True,
    )
    async def _run_list(self, ctx: CommandContext, args: ap.Namespace) -> None:
        procs_ = sorted(self._processes.processes.values(), key=lambda p: p.created_at)
        if not procs_:
            await ctx.print('No processes')
            return

        await ctx.print(ui.Text.join('\n', [self._render_process(p) for p in procs_]), '\n')

    #

    @ap.cmd(
        ap.arg('id'),
        ap.arg('-f', '--force', action='store_true'),
        name='kill',
    )
    async def _run_kill(self, ctx: CommandContext, args: ap.Namespace) -> None:
        try:
            proc = self._processes.processes[processes.ProcessId(check.non_empty_str(args.id))]
        except KeyError:
            await ctx.print(f'No such process: {args.id}')
            return

        if args.force:
            await proc.aclose(processes.TerminationPolicy(signal=signal.SIGKILL, grace_s=0.0))
        else:
            await proc.aclose()

        await ctx.print(list(lang.interleave(' ' * 2, [
            ui.Text.style(proc.id, bold=True),
            ui.Text.style('killed', bold=True, color='red'),
            ui.JsonText({'returncode': proc.returncode}, self._JSON_STYLE),
        ])), '\n')
