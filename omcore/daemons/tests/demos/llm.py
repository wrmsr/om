import argparse
import logging
import os
import tempfile
import time
import typing as ta

from .... import check
from .... import dataclasses as dc
from ....logs import all as logs
from ...daemon import Daemon
from ...lazy import LazyDaemon
from ...rpc import LazyRpcClient
from ...rpc import RpcClient
from ...rpc import RpcHandler
from ...rpc import RpcRequest
from ...rpc import RpcService
from ...rpc import RpcWait
from ...runtime import ServiceRuntime
from ...services import ServiceDaemon
from ...services import ServiceTarget
from ...spawning import MultiprocessingSpawning


log = logs.get_module_logger(globals())


##


@dc.dataclass(frozen=True)
class DummyLlmHandler:
    def __call__(self, request: RpcRequest) -> ta.Any:
        if request.method != 'chat':
            raise ValueError(f'Unknown LLM method: {request.method!r}')

        user_message = check.isinstance(request.params, str)
        log.info('Answering mock LLM request: %r', user_message)
        time.sleep(1.)
        return f'Fascintating! Tell me more about {user_message}'


class LlmService(RpcService):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RpcService.Config):
        handler: RpcHandler = dc.field(default_factory=DummyLlmHandler)
        log_file: str

    def __init__(self, config: Config) -> None:
        super().__init__(config)


def _llm_service_entrypoint(args: MultiprocessingSpawning.EntrypointArgs) -> None:
    target = check.isinstance(args.spawn.target, ServiceTarget)
    service = check.isinstance(target.svc, LlmService)
    config = check.isinstance(service.config, LlmService.Config)

    logs.configure_standard_logging(
        'INFO',
        force=True,
        handler_factory=lambda: logging.FileHandler(config.log_file),
    )
    log.info('Starting mock LLM service')
    args.spawn.fn()


def build_lazy_llm_client(
        state_dir: str,
        *,
        linger_s: float,
        timeout_s: float,
) -> LazyRpcClient:
    state_dir = os.path.abspath(os.path.expanduser(state_dir))
    os.makedirs(state_dir, mode=0o700, exist_ok=True)

    socket_path = os.path.join(state_dir, 'llm.sock')
    pid_file = os.path.join(state_dir, 'llm.pid')
    log_file = os.path.join(state_dir, 'llm.log')

    client_config = RpcClient.Config(
        socket_path=socket_path,
        connect_timeout_s=timeout_s,
        io_timeout_s=timeout_s,
    )
    service_daemon: ServiceDaemon[LlmService, LlmService.Config] = ServiceDaemon(
        LlmService.Config(
            runtime=ServiceRuntime.Config(
                idle_timeout_s=linger_s,
                drain_timeout_s=timeout_s,
            ),
            socket_path=socket_path,
            connection_timeout_s=timeout_s,
            log_file=log_file,
        ),
        Daemon.Config(
            spawning=MultiprocessingSpawning(
                start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                entrypoint=_llm_service_entrypoint,
            ),
            pid_file=pid_file,
            reparent_process=True,
            wait=RpcWait(client_config),
            wait_timeout=timeout_s,
            wait_sleep_s=.05,
        ),
    )

    return LazyRpcClient(
        LazyDaemon(service_daemon.daemon_()),
        RpcClient(client_config),
    )


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.:
        raise argparse.ArgumentTypeError('must be greater than zero')
    return parsed


def _default_state_dir() -> str:
    return os.path.join(tempfile.gettempdir(), f'omcore-daemons-llm-{os.getuid()}')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Talk to a lazily spawned mock LLM background service.',
    )
    parser.add_argument(
        '--state-dir',
        default=_default_state_dir(),
        help='directory for the Unix socket, pidfile, and worker log',
    )
    parser.add_argument(
        '--linger',
        type=_positive_float,
        default=10.,
        metavar='SECONDS',
        help='worker idle lifetime after its last request (default: %(default)s)',
    )
    parser.add_argument(
        '--timeout',
        type=_positive_float,
        default=15.,
        metavar='SECONDS',
        help='startup, connection, and call timeout (default: %(default)s)',
    )
    parser.add_argument(
        '-m',
        '--message',
        action='append',
        help='send one message non-interactively; may be repeated',
    )
    return parser


def _chat(client: LazyRpcClient, user_message: str, *, timeout_s: float) -> str:
    return check.isinstance(client.call('chat', user_message, timeout=timeout_s), str)


def _run_repl(client: LazyRpcClient, *, timeout_s: float) -> None:
    print('Mock LLM REPL. Enter /quit to exit.')
    while True:
        try:
            user_message = input('you> ')
        except EOFError:
            print()
            return

        if user_message in {'/exit', '/quit'}:
            return
        if not user_message:
            continue

        print(f'llm> {_chat(client, user_message, timeout_s=timeout_s)}')


def main(argv: ta.Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    client = build_lazy_llm_client(
        args.state_dir,
        linger_s=args.linger,
        timeout_s=args.timeout,
    )

    if args.message:
        for user_message in args.message:
            print(_chat(client, user_message, timeout_s=args.timeout))
    else:
        _run_repl(client, timeout_s=args.timeout)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
