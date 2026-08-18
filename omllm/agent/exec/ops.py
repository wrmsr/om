"""
Command execution for tools, backed by the process manager (`omllm.core.processes`). An `ExecOps` runs a single
foreground command in a caller-supplied `ProcessScope` - spawn, wait (with an optional timeout), tear down, and
collect the captured output - and returns a structured `ExecResult`. `format_exec_output` renders that into
model-facing text (combined streams, exit / timeout notes, head+tail truncation for very large output).

Long-lived / background / streaming processes are spawned directly against a scope, not through here.

FIXME:
 - pointless ProcessesExecOps abstraction with 'processes.ProcessScope' and whatnot baked right into the interface lol
"""
import abc
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


class ExecOps(lang.Abstract):
    @abc.abstractmethod
    def exec(self, scope: processes.ProcessScope, params: ExecParams) -> ta.Awaitable[ExecResult]:
        raise NotImplementedError


##


class ProcessesExecOps(ExecOps):
    async def exec(self, scope: processes.ProcessScope, params: ExecParams) -> ExecResult:
        spec = processes.ProcessSpec(
            tuple(params.cmd),
            cwd=params.cwd,
            env=dict(params.env),
        )

        proc = await scope.spawn(spec, *params.options)

        timed_out = False
        try:
            try:
                await proc.wait(params.timeout_s)
            except processes.ProcessTimeoutError:
                timed_out = True
        finally:
            # Reaps the process (and, on timeout, kills it and its group first).
            await proc.aclose()

        read = proc.spool.read_available(0)

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
