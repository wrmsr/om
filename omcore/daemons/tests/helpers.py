import argparse
import json
import logging
import os
import socket

from ... import check
from ... import dataclasses as dc
from ...logs import all as logs
from ..launching import Launcher
from ..pidfiles import current_daemon_pidfile_info
from ..services import Service
from ..spawning import ForkSpawning
from ..spawning import MultiprocessingSpawning
from ..targets import Target
from ..targets import TargetRunner
from ..targets import target_runner_for


log = logs.get_module_logger(globals())


##


class ControlledTarget(Target):
    control_path: str

    label: str = 'worker'
    fail: bool = False

    bootstrap_file: str | None = None
    probe_fd: int | None = None


class UnregisteredTarget(Target):
    pass


class ControlledTargetRunner(TargetRunner, dc.Frozen):
    target: ControlledTarget

    def run(self) -> None:
        run_controlled_worker(
            self.target.control_path,
            label=self.target.label,
            fail=self.target.fail,
            probe_fd=self.target.probe_fd,
        )


@target_runner_for.register
def _(target: ControlledTarget) -> ControlledTargetRunner:
    return ControlledTargetRunner(target)


##


class ControlledService(Service['ControlledService.Config']):
    @dc.dataclass(frozen=True)
    class Config(Service.Config):
        control_path: str = ''
        label: str = 'service'

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _run(self) -> None:
        run_controlled_worker(
            self.config.control_path,
            label=self.config.label,
        )


##


def _is_fd_open(fd: int) -> bool:
    try:
        os.fstat(fd)
    except OSError:
        return False
    else:
        return True


def run_controlled_worker(
        control_path: str,
        *,
        label: str = 'worker',
        fail: bool = False,
        probe_fd: int | None = None,
) -> None:
    probe_fd_open = _is_fd_open(probe_fd) if probe_fd is not None else None
    pidfile_info = current_daemon_pidfile_info()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(control_path)
        sock.sendall(json.dumps({
            'cwd': os.getcwd(),
            'label': label,
            'pid': os.getpid(),
            'ppid': os.getppid(),
            'probe_fd_open': probe_fd_open,
            'sid': os.getsid(0),
            'instance_id': pidfile_info.instance_id if pidfile_info is not None else None,
        }).encode('utf-8') + b'\n')

        if sock.recv(1) != b'X':
            raise RuntimeError('Worker control connection closed before release')

    if fail:
        raise RuntimeError('Controlled worker failure')


def controlled_multiprocessing_entrypoint(args: MultiprocessingSpawning.EntrypointArgs) -> None:
    target = check.isinstance(args.spawn.target, ControlledTarget)

    if (bootstrap_file := target.bootstrap_file) is not None:
        logs.configure_standard_logging(
            'INFO',
            force=True,
            handler_factory=lambda: logging.FileHandler(bootstrap_file),
        )
        log.info('Controlled worker bootstrap: %s', args.start_method.name)

    args.spawn.fn()


def failing_multiprocessing_entrypoint(args: MultiprocessingSpawning.EntrypointArgs) -> None:
    raise RuntimeError(f'Entrypoint failed before target: {args.start_method.name}')


def close_controlled_target_probe_fd(args: ForkSpawning.PostForkArgs) -> None:
    target = check.isinstance(args.spawn.target, ControlledTarget)
    os.close(check.isinstance(target.probe_fd, int))


##


def _run_contender(
        contender: str,
        barrier_path: str,
        control_path: str,
        pid_file: str,
) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as barrier_sock:
        barrier_sock.connect(barrier_path)
        barrier_sock.sendall(json.dumps({'contender': contender}).encode('utf-8') + b'\n')
        if barrier_sock.recv(1) != b'X':
            raise RuntimeError('Contender barrier closed before release')

    launched = Launcher(
        target=ControlledTarget(control_path, label='detached'),
        spawning=MultiprocessingSpawning(
            start_method=MultiprocessingSpawning.StartMethod.SPAWN,
        ),
        pid_file=pid_file,
        reparent_process=True,
    ).launch()

    print(json.dumps({
        'contender': contender,
        'launched': launched,
    }), flush=True)


def _main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)

    worker_parser = subparsers.add_parser('worker')
    worker_parser.add_argument('control_path')
    worker_parser.add_argument('--label', default='exec')
    worker_parser.add_argument('--fail', action='store_true')

    contender_parser = subparsers.add_parser('contend')
    contender_parser.add_argument('contender')
    contender_parser.add_argument('barrier_path')
    contender_parser.add_argument('control_path')
    contender_parser.add_argument('pid_file')

    args = parser.parse_args()

    match args:
        case argparse.Namespace(command='worker'):  # noqa
            run_controlled_worker(
                args.control_path,
                label=args.label,
                fail=args.fail,
            )

        case argparse.Namespace(command='contend'):  # noqa
            _run_contender(
                args.contender,
                args.barrier_path,
                args.control_path,
                args.pid_file,
            )

        case _:
            raise TypeError(args)


if __name__ == '__main__':
    _main()
