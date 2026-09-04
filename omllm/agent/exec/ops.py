"""
Command execution for tools, backed by the process manager (`omllm.core.processes`). An `ExecOps` runs a single
foreground command in a caller-supplied `ProcessScope` - spawn, wait (with an optional timeout), tear down, and
collect the captured output - and returns a structured `ExecResult`. `format_exec_output` renders that into
model-facing text (combined streams, exit / timeout notes, head+tail truncation for very large output).

Long-lived / background / streaming processes are spawned directly against a scope, not through here.

FIXME:
 - pointless ProcessesExecOps abstraction with 'processes.ProcessScope' and whatnot baked right into the interface lol
  - or? retain as a 'simplified' (if leaky) interface?
"""
import abc
import time
import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang

from ...core import processes


##


@ta.final
@dc.dataclass(frozen=True)
class ExecParams:
    cmd: lang.SequenceNotStr[str] = dc.xfield(coerce=tuple)

    _: dc.KW_ONLY

    cwd: str
    env: ta.Mapping[str, str] = dc.xfield(coerce=col.frozendict)

    timeout_s: float | None = None

    # Extra process options (Sandbox, Target, ...) applied to the spawn.
    options: ta.Sequence[processes.ProcessOption] = dc.xfield(default=(), coerce=tuple)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ExecResult:
    rc: int

    stdout: bytes | None = None
    stderr: bytes | None = None

    # The command exceeded its timeout and was terminated.
    timed_out: bool = False

    # Some captured output was dropped before it could be returned (output cap with spilling disabled).
    truncated: bool = False


class ExecOutputSink(lang.Abstract):
    """Receives a command's output as it arrives, for a caller which wants to show it before the command is done."""

    @abc.abstractmethod
    def write(self, fd: int, data: bytes) -> ta.Awaitable[None]:
        raise NotImplementedError


class ExecOps(lang.Abstract):
    @abc.abstractmethod
    def exec(
            self,
            scope: processes.ProcessScope,
            params: ExecParams,
            *,
            output: ExecOutputSink | None = None,
    ) -> ta.Awaitable[ExecResult]:
        raise NotImplementedError


##


class ProcessesExecOps(ExecOps):
    async def _wait_streaming(
            self,
            proc: processes.Process,
            timeout_s: float | None,
            output: ExecOutputSink,
    ) -> None:
        """
        Follows the output to its end within the time budget, then waits for the exit within what is left of it. The
        spool keeps everything, so the caller still reads the whole result afterwards.
        """

        if timeout_s is None:
            async for read in proc.spool.subscribe(0):
                for r in read.records:
                    await output.write(r.fd, r.data)

            await proc.wait(None)
            return

        deadline = time.monotonic() + timeout_s

        cursor = 0
        while (remaining := deadline - time.monotonic()) > 0:
            # A long-poll: back with the first output to arrive, the end of output, or the rest of the budget spent.
            # It must be given a positive timeout - to the spool, none at all means "do not wait".
            read = await proc.spool.poll(cursor, timeout=remaining)

            for r in read.records:
                await output.write(r.fd, r.data)
            cursor = read.end

            if read.ended:
                break

        # Output ending is not the process exiting: that is observed separately, and a spent budget raises here.
        await proc.wait(max(deadline - time.monotonic(), 0.))

    async def exec(
            self,
            scope: processes.ProcessScope,
            params: ExecParams,
            *,
            output: ExecOutputSink | None = None,
    ) -> ExecResult:
        spec = processes.ProcessSpec(
            tuple(params.cmd),
            cwd=params.cwd,
            env=dict(params.env),
        )

        proc = await scope.spawn(spec, *params.options)

        timed_out = False
        try:
            try:
                if output is None:
                    await proc.wait(params.timeout_s)
                else:
                    await self._wait_streaming(proc, params.timeout_s, output)
            except processes.ProcessTimeoutError:
                timed_out = True
        finally:
            # Reaps the process (and, on timeout, kills it and its group first).
            await proc.aclose()

        try:
            read = proc.spool.read_available(0)
        finally:
            # Output collected: release the spool (memory + spill file).
            proc.spool.close()

        return ExecResult(
            rc=proc.returncode if proc.returncode is not None else -1,
            stdout=read.data(1),
            stderr=read.data(2),
            timed_out=timed_out,
            truncated=read.dropped_before > 0,
        )


##


DEFAULT_MAX_EXEC_OUTPUT_CHARS: ta.Final[int] = 30_000


def format_exec_output(
        result: ExecResult,
        *,
        timeout_s: float | None = None,
        max_chars: int | None = DEFAULT_MAX_EXEC_OUTPUT_CHARS,
) -> str:
    """
    Renders an `ExecResult` as model-facing text: combined stdout then stderr, with out-of-band notes for a nonzero
    exit, a timeout, or truncation - phrased so a model can tell them apart from the command's own output.
    """

    out = (result.stdout or b'').decode('utf-8', 'replace')
    err = (result.stderr or b'').decode('utf-8', 'replace')

    body = out
    if err:
        if body and not body.endswith('\n'):
            body += '\n'
        body += err

    if max_chars is not None and len(body) > max_chars:
        half = max_chars // 2
        head = body[:half]
        tail = body[-half:]
        omitted = len(body) - len(head) - len(tail)
        body = f'{head}\n\n[... {omitted} characters of output truncated ...]\n\n{tail}'

    notes: list[str] = []
    if result.timed_out:
        notes.append(f'command timed out{f" after {timeout_s}s" if timeout_s is not None else ""} and was terminated')
    if result.rc:
        notes.append(f'exit code {result.rc}')
    if result.truncated:
        notes.append('some output was dropped')

    if notes:
        if body and not body.endswith('\n'):
            body += '\n'
        body += '\n[' + '; '.join(notes) + ']'

    return body or '(no output)'
