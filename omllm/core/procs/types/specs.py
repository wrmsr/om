"""
The launch-shape of a process: what to run, where, with which environment and stdio wiring. Deliberately *only* that -
policies (termination, spooling, credentials, ...) are `ProcOption`s in `options.py`, so that this stays a small,
stable, marshalable value and each policy can be layered and injected independently.
"""
import os
import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang


##


# `'pipe'`: a manager-owned pipe - readable output lands in the process spool, stdin becomes writable.
# `'devnull'`: /dev/null. `'inherit'`: the manager's own fd. An int: an already-open fd of the caller, passed as-is.
# `'stdout'` (stderr only): OS-level merge into stdout - faithful interleaving, but fd identity is lost in the spool.

type StdinChannel = ta.Literal['pipe', 'devnull', 'inherit'] | int
type StdoutChannel = ta.Literal['pipe', 'devnull', 'inherit'] | int
type StderrChannel = ta.Literal['pipe', 'devnull', 'inherit', 'stdout'] | int


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True)
class ProcessStdio:
    stdin: StdinChannel = 'devnull'
    stdout: StdoutChannel = 'pipe'
    stderr: StderrChannel = 'pipe'

    def __post_init__(self) -> None:
        for n, v, allowed in [
            ('stdin', self.stdin, ('pipe', 'devnull', 'inherit')),
            ('stdout', self.stdout, ('pipe', 'devnull', 'inherit')),
            ('stderr', self.stderr, ('pipe', 'devnull', 'inherit', 'stdout')),
        ]:
            if isinstance(v, int):
                if v < 0:
                    raise ValueError(f'{n}: negative fd {v!r}')
            elif v not in allowed:
                raise ValueError(f'{n}: invalid channel {v!r}')

    @property
    def any_pipes(self) -> bool:
        return 'pipe' in (self.stdin, self.stdout, self.stderr)


DEFAULT_PROCESS_STDIO: ta.Final = ProcessStdio()


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True)
class PtyStdio:
    """
    Run the child under a pseudo-terminal: its stdin/stdout/stderr are the pty slave (a real controlling tty), and the
    handle exposes the merged master as output plus a writable stdin. Output is a single interleaved stream (fd 1 in the
    spool) - a tty has no separate stderr. Requires session-leader semantics (SessionMode 'session'), which the manager
    enforces.
    """

    rows: int = 24
    cols: int = 80

    # Value for the child's TERM env var. Authoritative for the pty (overrides any inherited host TERM); only an
    # explicit TERM in the spec's env wins over it. None leaves TERM untouched.
    term: str | None = 'xterm-256color'

    def __post_init__(self) -> None:
        check.arg(self.rows > 0)
        check.arg(self.cols > 0)


type Stdio = ProcessStdio | PtyStdio


##


def _check_argv(argv: ta.Sequence[str]) -> tuple[str, ...]:
    check.not_isinstance(argv, str)
    tup = tuple(argv)
    if not tup:
        raise ValueError('Empty argv')
    for a in tup:
        if not isinstance(a, str):
            raise TypeError(a)
        if '\0' in a:
            raise ValueError(f'NUL in argv item: {a!r}')
    return tup


def _check_env(env: ta.Mapping[str, str] | None) -> ta.Mapping[str, str] | None:
    if env is None:
        return None
    for k, v in env.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError((k, v))
        if not k or '=' in k or '\0' in k or '\0' in v:
            raise ValueError(f'Invalid env entry: {k!r}')
    return col.frozendict(env)


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, default_repr_fn=lang.opt_repr)
class ProcessSpec:
    argv: lang.SequenceNotStr[str] = dc.xfield(coerce=_check_argv)

    _: dc.KW_ONLY

    # Working directory. None means the manager's own cwd at spawn time.
    cwd: str | None = None

    # The exact environment of the target. None means the manager's own `os.environ` at spawn time; an empty mapping
    # means a clean environment. Note that argv[0] is resolved against the PATH of *this* env (or `os.defpath`).
    env: ta.Mapping[str, str] | None = dc.xfield(default=None, coerce=_check_env)

    stdio: Stdio = DEFAULT_PROCESS_STDIO

    # A human / llm facing label. Not unique.
    name: str | None = None

    #

    def resolve_env(self) -> ta.Mapping[str, str]:
        if (env := self.env) is not None:
            return env
        return dict(os.environ)

    def resolve_cwd(self) -> str:
        if (cwd := self.cwd) is not None:
            return cwd
        return os.getcwd()

    def with_env(self, **kwargs: str) -> ProcessSpec:
        return dc.replace(self, env={**self.resolve_env(), **kwargs})
