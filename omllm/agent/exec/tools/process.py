"""
Tools for managing long-lived background processes: spawn one that outlives the tool call, then poll its output
(cursor + wait window), write to its stdin, list them, and terminate them. Foreground one-shot commands go through
the `bash` tool instead.

All of these operate on the process scope carried by `ToolEnvironment.processes` - a backgrounded process lives there
until it is terminated or the scope (session) is torn down.
"""
import os
import shutil
import signal
import time
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ....core import processes
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..permissions import ExecPermissionTarget


##


def _scope(ctx: ToolContext) -> processes.ProcessScope:
    if ctx.env is None or (scope := ctx.env.processes) is None:
        raise ValueError('No process scope configured')
    return scope


def _lookup(ctx: ToolContext, process_id: str) -> processes.Process:
    scope = _scope(ctx)
    try:
        return scope.processes[processes.ProcessId(check.non_empty_str(process_id))]
    except KeyError:
        raise ValueError(f'No such process: {process_id!r} (use process_list)') from None


def _status_note(proc: processes.Process, read: processes.SpoolRead) -> str:
    parts: list[str] = [proc.id]
    # Whether the process has *exited* is a distinct event from whether its *output* has ended (a process can close
    # its stdio and keep running, and - the source of a past flake - output EOF can be observed before the exit is,
    # since the exit code arrives from a separate waitid). Report the exit only once it is actually observed.
    if proc.exited:
        rc = proc.returncode
        parts.append(f'exited (rc={rc})' if rc is not None else 'exited')
    elif read.ended:
        parts.append('running; output closed')
    elif read.more:
        parts.append('running; more output available')
    else:
        parts.append('running')
    if read.dropped_before:
        parts.append(f'dropped {read.dropped_before} bytes')
    parts.append(f'next_cursor={read.end}')
    return '[' + '; '.join(parts) + ']'


##


@dc.dataclass(frozen=True)
class ProcessSpawnToolParams:
    command: str

    _: dc.KW_ONLY

    name: str | None = None


class ProcessSpawnTool(ToolClass[ProcessSpawnToolParams]):
    name: ta.Final = 'process_spawn'

    params_cls: ta.Final = ProcessSpawnToolParams

    description: ta.Final = ToolDescription(
        """
            Starts a long-running bash command in the background and returns immediately with a process id. The
            process keeps running after this tool returns; use process_read to read its output, process_write to send
            it input, process_list to see running processes, and process_kill to stop it.

            Use this instead of bash for servers, watchers, REPLs, or any command you want to interact with or that
            does not finish quickly.
        """,
        dict(
            command='The bash command to run in the background.',
            name='An optional short label for the process.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
    ) -> None:
        super().__init__()

        self._permissions = permissions

    async def execute(self, ctx: ToolContext, params: ProcessSpawnToolParams) -> str:
        scope = _scope(ctx)
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')

        cmd = [
            check.not_none(shutil.which('bash')),
            '-c',
            params.command,
        ]

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            ExecPermissionTarget(cmd),
        )

        proc = await scope.spawn(processes.ProcessSpec(
            cmd,
            cwd=cwd,
            env=dict(os.environ),
            stdio=processes.ProcessStdio(stdin='pipe', stdout='pipe', stderr='pipe'),
            name=params.name,
        ))

        return (
            f'Started background process {proc.id} (pid {proc.pid}). '
            f'Read its output with process_read id={proc.id!r}.'
        )


##


@dc.dataclass(frozen=True)
class ProcessReadToolParams:
    id: str  # noqa

    _: dc.KW_ONLY

    cursor: int = 0
    wait_s: float = 0.0
    max_bytes: int | None = None


class ProcessReadTool(ToolClass[ProcessReadToolParams]):
    # How long a read that has hit end-of-output will wait for the (imminent) exit to be observed, so the status can
    # report the exit code. A process that merely closed its stdio and kept running is reported as running after this.
    _EXIT_GRACE_S: ta.ClassVar[float] = 5.0

    name: ta.Final = 'process_read'

    params_cls: ta.Final = ProcessReadToolParams

    description: ta.Final = ToolDescription(
        """
            Reads output from a background process (see process_spawn). Returns the output since 'cursor' followed by
            a status line ending in 'next_cursor=N' - pass that N as 'cursor' on the next call to continue where you
            left off (start at 0). With 'wait_s' > 0 the tool waits up to that many seconds for new output (or until
            the process exits), which is the efficient way to follow a running process without busy-polling.
        """,
        dict(
            id='The process id returned by process_spawn.',
            cursor='Opaque cursor from the previous read (start at 0).',
            wait_s='Seconds to wait for new output before returning (0 = return whatever is available now).',
            max_bytes='Maximum number of output bytes to return in this call.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: ProcessReadToolParams) -> str:
        proc = _lookup(ctx, params.id)

        read = await proc.spool.poll(
            params.cursor,
            timeout=params.wait_s if params.wait_s > 0 else None,
            max_bytes=params.max_bytes,
        )

        # Output is fully closed but the exit has not been observed yet: for a normal command the process just
        # exited and its exit code is imminent, so wait briefly (bounded) rather than racing it into the status.
        if read.ended and not proc.exited:
            try:
                await proc.wait(self._EXIT_GRACE_S)
            except processes.ProcessTimeoutError:
                pass

        text = processes.ArrivalMergedRenderer().render(read.records)
        note = _status_note(proc, read)
        if text and not text.endswith('\n'):
            text += '\n'
        return f'{text}{note}' if text else note


##


@dc.dataclass(frozen=True)
class ProcessWriteToolParams:
    id: str  # noqa
    data: str

    _: dc.KW_ONLY

    eof: bool = False


class ProcessWriteTool(ToolClass[ProcessWriteToolParams]):
    name: ta.Final = 'process_write'

    params_cls: ta.Final = ProcessWriteToolParams

    description: ta.Final = ToolDescription(
        """
            Writes to the stdin of a background process. Include any trailing newline you want in 'data'. Set 'eof' to
            close the process's stdin after writing (signals end-of-input to programs that read until EOF).
        """,
        dict(
            id='The process id returned by process_spawn.',
            data='The text to write to the process stdin.',
            eof="Whether to close the process's stdin after writing.",
        ),
    )

    async def execute(self, ctx: ToolContext, params: ProcessWriteToolParams) -> str:
        proc = _lookup(ctx, params.id)

        if params.data:
            await proc.write(params.data.encode('utf-8'))
        if params.eof:
            await proc.write_eof()

        return (
            f'Wrote {len(params.data.encode("utf-8"))} bytes to {proc.id}'
            + ('; closed stdin.' if params.eof else '.')
        )


##


@dc.dataclass(frozen=True)
class ProcessKillToolParams:
    id: str  # noqa

    _: dc.KW_ONLY

    force: bool = False


class ProcessKillTool(ToolClass[ProcessKillToolParams]):
    name: ta.Final = 'process_kill'

    params_cls: ta.Final = ProcessKillToolParams

    description: ta.Final = ToolDescription(
        """
            Terminates a background process (and its child process group) and returns its exit status. By default it
            asks the process to stop gracefully (SIGTERM) before forcing it; set 'force' to send SIGKILL immediately.
            Also use this to clean up a process that has already exited.
        """,
        dict(
            id='The process id returned by process_spawn.',
            force='Send SIGKILL immediately instead of a graceful SIGTERM first.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: ProcessKillToolParams) -> str:
        proc = _lookup(ctx, params.id)

        if params.force:
            await proc.aclose(processes.TerminationPolicy(signal=signal.SIGKILL, grace_s=0.0))
        else:
            await proc.aclose()

        # Reaped and unregistered - no further process_read can reach it, so release its output now.
        proc.spool.close()

        return f'Terminated process {proc.id} (rc {proc.returncode}).'


##


@dc.dataclass(frozen=True)
class ProcessListToolParams:
    pass


class ProcessListTool(ToolClass[ProcessListToolParams]):
    name: ta.Final = 'process_list'

    params_cls: ta.Final = ProcessListToolParams

    description: ta.Final = ToolDescription(
        'Lists the background processes started with process_spawn, with their id, pid, state, and command.',
    )

    async def execute(self, ctx: ToolContext, params: ProcessListToolParams) -> str:
        scope = _scope(ctx)
        procs_ = sorted(scope.processes.values(), key=lambda p: p.created_at)
        if not procs_:
            return 'No background processes.'

        now = time.time()
        lines: list[str] = []
        for p in procs_:
            state = p.state.name.lower()
            rc = f' rc={p.returncode}' if p.returncode is not None else ''
            label = f' ({p.name})' if p.name else ''
            elapsed = f'{now - p.created_at:.0f}s'
            lines.append(f'{p.id}  pid={p.pid}  {state}{rc}  {elapsed}  {" ".join(p.spec.argv)}{label}')
        return '\n'.join(lines)
