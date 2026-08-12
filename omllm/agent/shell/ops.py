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
class ShellExecuteParams:
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
class ShellExecuteResult:
    rc: int

    stdout: bytes | None = None
    stderr: bytes | None = None


class ShellOps(lang.Abstract):
    @abc.abstractmethod
    def shell_execute(self, params: ShellExecuteParams) -> ta.Awaitable[ShellExecuteResult]:
        raise NotImplementedError


##


class LocalShellOps(ShellOps):
    async def shell_execute(self, params: ShellExecuteParams) -> ShellExecuteResult:
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

        return ShellExecuteResult(
            rc=check.isinstance(proc.returncode, int),

            stdout=check.not_none(stdout),
            stderr=check.not_none(stderr),
        )
