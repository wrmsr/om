import enum
import math
import os
import signal
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...collections.frozen import FrozenDict


##


class ChildProcessInput(enum.Enum):
    INHERIT = enum.auto()
    DEVNULL = enum.auto()


class ChildProcessOutputMode(enum.Enum):
    INHERIT = enum.auto()
    DEVNULL = enum.auto()
    FILE = enum.auto()
    STDOUT = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class ChildProcessOutput:
    mode: ChildProcessOutputMode = ChildProcessOutputMode.INHERIT
    path: str | None = None
    append: bool = True

    @classmethod
    def file(cls, path: str, *, append: bool = True) -> ta.Self:
        return cls(
            mode=ChildProcessOutputMode.FILE,
            path=path,
            append=append,
        )

    def __post_init__(self) -> None:
        if self.mode is ChildProcessOutputMode.FILE:
            check.non_empty_str(self.path)
        else:
            check.none(self.path)


##


@dc.dataclass(frozen=True, kw_only=True)
class ChildProcessConfig:
    cmd: ta.Sequence[str] = dc.xfield(coerce=lambda value: tuple(check.not_isinstance(value, str)))

    cwd: str | None = None

    inherit_env: bool = True
    env: ta.Mapping[str, str | None] | None = dc.xfield(
        default=None,
        coerce=lambda value: None if value is None else FrozenDict(value),
        repr_fn=lambda env: (
            repr({key: lang.LiteralRepr('...') if value is not None else None for key, value in env.items()})
            if env is not None else None
        ),
    )

    stdin: ChildProcessInput = ChildProcessInput.DEVNULL
    stdout: ChildProcessOutput = ChildProcessOutput()
    stderr: ChildProcessOutput = ChildProcessOutput()

    pass_fds: ta.Sequence[int] = dc.xfield(default=(), coerce=tuple)
    start_new_session: bool = False

    def __post_init__(self) -> None:
        check.arg(bool(self.cmd))
        for arg in self.cmd:
            check.isinstance(arg, str)
            check.arg('\x00' not in arg)

        if self.cwd is not None:
            check.non_empty_str(self.cwd)

        if self.env is not None:
            for key, value in self.env.items():
                check.non_empty_str(key)
                check.arg('=' not in key)
                check.arg('\x00' not in key)
                if value is not None:
                    check.isinstance(value, str)
                    check.arg('\x00' not in value)

        check.arg(self.stdout.mode is not ChildProcessOutputMode.STDOUT)
        if (
                self.stdout.mode is ChildProcessOutputMode.FILE and
                self.stderr.mode is ChildProcessOutputMode.FILE and
                os.path.abspath(os.path.expanduser(check.not_none(self.stdout.path))) ==
                os.path.abspath(os.path.expanduser(check.not_none(self.stderr.path)))
        ):
            check.equal(self.stdout.append, self.stderr.append)

        for fd in self.pass_fds:
            check.isinstance(fd, int)
            check.arg(fd >= 0)
        check.equal(len(set(self.pass_fds)), len(self.pass_fds))

    def resolved_cwd(self) -> str | None:
        if self.cwd is None:
            return None
        return os.path.expanduser(self.cwd)

    def resolved_env(self) -> dict[str, str] | None:
        if self.inherit_env:
            env: dict[str, str | None] = dict(os.environ)
        elif self.env is None:
            return {}
        else:
            env = {}

        if self.env is not None:
            env.update(self.env)

        return {key: value for key, value in env.items() if value is not None}


@dc.dataclass(frozen=True, kw_only=True)
class ChildTerminationConfig:
    signal: int | None = signal.SIGTERM
    forward_runtime_signal: bool = True

    grace_timeout_s: float | None = 10.
    kill_timeout_s: float | None = 10.

    signal_process_group: bool = False

    def __post_init__(self) -> None:
        if self.signal is not None:
            check.arg(self.signal > 0)

        if self.grace_timeout_s is not None:
            check.arg(math.isfinite(self.grace_timeout_s))
            check.arg(self.grace_timeout_s >= 0.)

        if self.kill_timeout_s is not None:
            check.arg(math.isfinite(self.kill_timeout_s))
            check.arg(self.kill_timeout_s > 0.)
