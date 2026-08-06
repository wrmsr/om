import abc
import enum
import functools
import os
import threading
import time
import typing as ta

from .. import check
from .. import dataclasses as dc
from .. import lang
from ..diag import pydevd
from .targets import Target


if ta.TYPE_CHECKING:
    import multiprocessing as mp
    import multiprocessing.context
    import multiprocessing.process  # noqa

    from ..multiprocessing import spawn as omp_spawn

else:
    mp = lang.proxy_import('multiprocessing', extras=['context', 'process'])
    subprocess = lang.proxy_import('subprocess')

    omp_spawn = lang.proxy_import('..multiprocessing.spawn', __package__)


##


class Spawning(dc.Case):
    pass


class Spawn(dc.Frozen, final=True):
    fn: ta.Callable[[], None]

    _: dc.KW_ONLY

    target: Target | None = None

    inherit_fds: ta.Collection[int] | None = None

    on_error: ta.Callable[[BaseException], bool] | None = None


class Spawned(lang.Abstract):
    @property
    @abc.abstractmethod
    def pid(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def join(self, timeout_s: float | None = None) -> bool:
        raise NotImplementedError


class Spawner(lang.SelfContextManaged, lang.Abstract):
    @abc.abstractmethod
    def spawn(self, spawn: Spawn) -> Spawned:
        raise NotImplementedError


class InProcessSpawner(Spawner, lang.Abstract):
    pass


@functools.singledispatch
def spawner_for(spawning: Spawning) -> Spawner:
    raise TypeError(spawning)


def _notify_spawn_error(spawn: Spawn, exc: BaseException) -> bool:
    if isinstance(exc, SystemExit) and exc.code in (None, 0):
        return False

    if (on_error := spawn.on_error) is not None:
        try:
            return on_error(exc)
        except BaseException:  # noqa
            pass

    return False


def _run_spawn(spawn: Spawn) -> None:
    try:
        spawn.fn()
    except BaseException as exc:
        if not _notify_spawn_error(spawn, exc):
            raise


##


class MultiprocessingSpawning(Spawning, kw_only=True):
    class StartMethod(enum.Enum):
        SPAWN = enum.auto()
        FORK = enum.auto()
        # TODO: FORK_SERVER

    # Defaults to 'fork' if under pydevd, else 'spawn'
    start_method: StartMethod | None = None

    #

    # Note: Per multiprocessing docs, `no_linger=True` processes (corresponding to `Process(daemon=True)`) cannot spawn
    # subprocesses, and thus will fail if `Daemon.Config.reparent_process` is set.
    no_linger: bool = False

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class EntrypointArgs:
        spawning: MultiprocessingSpawning
        spawn: Spawn
        start_method: MultiprocessingSpawning.StartMethod

    entrypoint: ta.Callable[[EntrypointArgs], None] | None = None


class MultiprocessingSpawner(Spawner):
    def __init__(self, spawning: MultiprocessingSpawning) -> None:
        super().__init__()

        self._spawning = spawning
        self._process: ta.Optional['mp.process.BaseProcess'] = None  # noqa

    @lang.cached_function
    def _determine_start_method(self) -> MultiprocessingSpawning.StartMethod:
        if (start_method := self._spawning.start_method) is not None:
            return start_method

        # Unfortunately, pydevd forces the use of the 'fork' start_method, which cannot be mixed with 'spawn':
        #   https://github.com/python/cpython/blob/a7427f2db937adb4c787754deb4c337f1894fe86/Lib/multiprocessing/spawn.py#L102  # noqa
        if pydevd.is_running():
            return MultiprocessingSpawning.StartMethod.FORK

        return MultiprocessingSpawning.StartMethod.SPAWN

    def _process_cls(self, spawn: Spawn) -> type[mp.process.BaseProcess]:
        start_method = self._determine_start_method()

        ctx: 'mp.context.BaseContext'  # noqa
        if start_method == MultiprocessingSpawning.StartMethod.FORK:
            ctx = mp.get_context(check.non_empty_str('fork'))

        elif start_method == MultiprocessingSpawning.StartMethod.SPAWN:
            ctx = omp_spawn.ExtrasSpawnContext(omp_spawn.SpawnExtras(
                pass_fds=frozenset(spawn.inherit_fds) if spawn.inherit_fds is not None else None,
            ))

        else:
            raise ValueError(start_method)

        return ctx.Process  # type: ignore

    @staticmethod
    def _run(
            spawning: MultiprocessingSpawning,
            spawn: Spawn,
            start_method: MultiprocessingSpawning.StartMethod,
    ) -> None:
        try:
            if (entrypoint := spawning.entrypoint) is not None:
                entrypoint(MultiprocessingSpawning.EntrypointArgs(
                    spawning=spawning,
                    spawn=spawn,
                    start_method=start_method,
                ))
            else:
                spawn.fn()
        except BaseException as exc:
            _notify_spawn_error(spawn, exc)
            raise

    def spawn(self, spawn: Spawn) -> Spawned:
        check.none(self._process)

        start_method = self._determine_start_method()

        self._process = self._process_cls(spawn)(
            target=functools.partial(
                self._run,
                self._spawning,
                spawn,
                start_method,
            ),
            daemon=self._spawning.no_linger,
        )
        self._process.start()

        return MultiprocessingSpawned(self._process)


class MultiprocessingSpawned(Spawned):
    def __init__(self, process: mp.process.BaseProcess) -> None:
        super().__init__()

        self._process = process

    @property
    def pid(self) -> int:
        return check.isinstance(self._process.pid, int)

    def join(self, timeout_s: float | None = None) -> bool:
        self._process.join(timeout_s)
        return not self._process.is_alive()


@spawner_for.register
def _(spawning: MultiprocessingSpawning) -> MultiprocessingSpawner:
    return MultiprocessingSpawner(spawning)


##


class ForkSpawning(Spawning, kw_only=True):
    @dc.dataclass(frozen=True, kw_only=True)
    class PostForkArgs:
        spawning: ForkSpawning
        spawn: Spawn

    post_fork: ta.Callable[[PostForkArgs], None] | None = None


class ForkSpawned(Spawned):
    def __init__(self, pid: int) -> None:
        super().__init__()

        self._pid = pid
        self._reaped = False

    @property
    def pid(self) -> int:
        return self._pid

    def join(self, timeout_s: float | None = None) -> bool:
        if self._reaped:
            return True

        if timeout_s is None:
            try:
                os.waitpid(self._pid, 0)
            except ChildProcessError:
                pass
            self._reaped = True
            return True

        deadline = time.monotonic() + timeout_s
        while True:
            try:
                pid, _ = os.waitpid(self._pid, os.WNOHANG)
            except ChildProcessError:
                self._reaped = True
                return True
            if pid:
                self._reaped = True
                return True

            remaining_s = deadline - time.monotonic()
            if remaining_s <= 0.:
                return False
            time.sleep(min(remaining_s, .01))


class ForkSpawner(Spawner, dc.Frozen):
    spawning: ForkSpawning

    def spawn(self, spawn: Spawn) -> Spawned:
        if (pid := os.fork()):  # noqa
            return ForkSpawned(pid)

        try:
            if (post_fork := self.spawning.post_fork) is not None:
                post_fork(ForkSpawning.PostForkArgs(
                    spawning=self.spawning,
                    spawn=spawn,
                ))

            spawn.fn()
        except BaseException as exc:  # noqa
            _notify_spawn_error(spawn, exc)
            raise SystemExit(1) from None
        else:
            raise SystemExit(0)

        raise RuntimeError('Unreachable')  # noqa


@spawner_for.register
def _(spawning: ForkSpawning) -> ForkSpawner:
    return ForkSpawner(spawning)


##


class ThreadSpawning(Spawning, kw_only=True):
    linger: bool = False


class ThreadSpawned(Spawned, dc.Frozen):
    thread: threading.Thread

    @property
    def pid(self) -> int:
        return os.getpid()

    def join(self, timeout_s: float | None = None) -> bool:
        self.thread.join(timeout_s)
        return not self.thread.is_alive()


class ThreadSpawner(InProcessSpawner):
    def __init__(self, spawning: ThreadSpawning) -> None:
        super().__init__()

        self._spawning = spawning
        self._thread: threading.Thread | None = None

    def spawn(self, spawn: Spawn) -> Spawned:
        check.none(self._thread)
        self._thread = threading.Thread(
            target=functools.partial(_run_spawn, spawn),
            daemon=not self._spawning.linger,
        )
        self._thread.start()

        return ThreadSpawned(self._thread)


@spawner_for.register
def _(spawning: ThreadSpawning) -> ThreadSpawner:
    return ThreadSpawner(spawning)
