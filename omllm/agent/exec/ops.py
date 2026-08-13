"""
TODO:
 - streaming
 - background
 - cancel / kill
"""
import abc
import asyncio
import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang


##


@ta.final
@dc.dataclass(frozen=True)
class ExecParams:
    cmd: lang.SequenceNotStr[str] = dc.xfield(coerce=tuple)

    _: dc.KW_ONLY

    cwd: str
    env: ta.Mapping[str, str] = dc.xfield(coerce=col.frozendict)

    timeout_s: float | None = None

    def __post_init__(self) -> None:
        check.not_isinstance(self.cmd, str)
        if not all(isinstance(p, str) and p for p in self.cmd):
            raise ValueError(self.cmd)

        check.not_empty(self.env)
        if not all(isinstance(k, str) and isinstance(v, str) and k and v for k, v in self.env.items()):
            raise ValueError(list(self.env))


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ExecResult:
    rc: int

    stdout: bytes | None = None
    stderr: bytes | None = None


class ExecOps(lang.Abstract):
    @abc.abstractmethod
    def exec(self, params: ExecParams) -> ta.Awaitable[ExecResult]:
        raise NotImplementedError


##


class LocalExecOps(ExecOps):
    async def exec(self, params: ExecParams) -> ExecResult:
        proc = await asyncio.create_subprocess_exec(
            *params.cmd,

            cwd=params.cwd,
            env=params.env,

            stdin=asyncio.subprocess.DEVNULL,

            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,

            start_new_session=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(  # noqa
                proc.communicate(),
                timeout=params.timeout_s,
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise

        return ExecResult(
            rc=check.isinstance(proc.returncode, int),

            stdout=check.not_none(stdout),
            stderr=check.not_none(stderr),
        )
