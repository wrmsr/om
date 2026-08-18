import contextlib
import functools
import typing as ta

from .. import check
from .. import lang
from ..logs import all as logs
from ..os.pidfiles.manager import open_inheritable_pidfile
from ..os.pidfiles.pidfile import Pidfile
from .pidfiles import daemon_pidfile_info_context
from .pidfiles import dumps_daemon_pidfile_info
from .pidfiles import make_daemon_pidfile_info
from .reparent import reparent_process
from .spawning import InProcessSpawner
from .spawning import Spawn
from .spawning import Spawned
from .spawning import Spawner
from .spawning import Spawning
from .spawning import spawner_for
from .startup import LaunchError
from .startup import launch_monitor
from .targets import Target
from .targets import target_runner_for


log = logs.get_module_logger(globals())


##


class Launcher:
    def __init__(
            self,
            *,
            target: Target,
            spawning: Spawning,

            pid_file: str | None = None,
            reparent_process: bool = False,  # noqa
            launched_timeout_s: float = 5.,
    ) -> None:
        super().__init__()

        self._target = target
        self._spawning = spawning

        self._pid_file = pid_file
        self._reparent_process = reparent_process
        self._launched_timeout_s = launched_timeout_s

    def _inner_launch(
            self,
            *,
            pidfile_manager: ta.ContextManager | None,
            launched: ta.Callable[[], None],
    ) -> None:
        if self._reparent_process:
            log.info('Reparenting')
            reparent_process()

        with contextlib.ExitStack() as es:
            pidfile: Pidfile | None = None  # noqa
            if pidfile_manager is not None:
                pidfile = check.isinstance(es.enter_context(pidfile_manager), Pidfile)
                pidfile_info = make_daemon_pidfile_info()
                pidfile.write(suffix=dumps_daemon_pidfile_info(pidfile_info))
                es.enter_context(daemon_pidfile_info_context(pidfile_info))

            runner = target_runner_for(self._target)

            launched()
            runner.run()

    def launch(self) -> bool:
        with contextlib.ExitStack() as es:
            spawner: Spawner = es.enter_context(spawner_for(self._spawning))

            #

            inherit_fds: set[int] = set()
            pidfile: Pidfile | None = None  # noqa
            pidfile_manager: ta.ContextManager | None = None

            if (pid_file := self._pid_file) is not None:
                if not isinstance(spawner, InProcessSpawner):
                    pidfile = es.enter_context(open_inheritable_pidfile(pid_file))
                    pidfile_manager = lang.ValueContextManager(pidfile)

                else:
                    check.state(not self._reparent_process)
                    pidfile = es.enter_context(Pidfile(pid_file))
                    pidfile_manager = pidfile.dup()

                if not pidfile.try_acquire_lock():
                    return False

                inherit_fds.add(check.isinstance(pidfile.fileno(), int))

            #

            monitor = launch_monitor(in_process=isinstance(spawner, InProcessSpawner))
            es.callback(monitor.close)
            inherit_fds.update(monitor.inherit_fds)

            spawned: Spawned = spawner.spawn(Spawn(
                functools.partial(
                    self._inner_launch,
                    pidfile_manager=pidfile_manager,
                    launched=monitor.reporter.started,
                ),
                target=self._target,
                inherit_fds=inherit_fds,
                on_error=monitor.reporter.failed,
            ))
            monitor.after_spawn()

            report = monitor.wait(self._launched_timeout_s)
            if report.error is not None:
                spawned.join(self._launched_timeout_s)
                raise LaunchError(report.error)

            return True
