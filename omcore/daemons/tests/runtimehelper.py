import json
import os
import selectors
import socket
import threading
import typing as ta

from ... import dataclasses as dc
from ..runtime import Activity
from ..runtime import ActivityRejectedError
from ..runtime import ServiceRuntime
from ..runtime import ShutdownReason
from ..services import RuntimeService


##


def _send_json(sock: socket.socket, obj: ta.Mapping[str, ta.Any]) -> None:
    sock.sendall(json.dumps(obj).encode('utf-8') + b'\n')


def _receive_json(sock: socket.socket, buf: bytearray) -> ta.Mapping[str, ta.Any] | None:
    while b'\n' not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            return None
        buf.extend(chunk)

    line, _, remaining = buf.partition(b'\n')
    buf[:] = remaining
    obj = json.loads(line.decode('utf-8'))
    if not isinstance(obj, dict):
        raise TypeError(obj)
    return obj


##


class RuntimeControlledService(RuntimeService['RuntimeControlledService.Config']):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        control_path: str = ''
        label: str = 'runtime-service'

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        activities: list[Activity] = []

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as control_sock:
            control_sock.connect(self.config.control_path)
            _send_json(control_sock, {
                'label': self.config.label,
                'pid': os.getpid(),
                'ppid': os.getppid(),
                'sid': os.getsid(0),
            })

            shutdown_read_sock, shutdown_write_sock = socket.socketpair()
            with shutdown_read_sock, shutdown_write_sock:
                def wake_for_shutdown() -> None:
                    runtime.shutdown.wait()
                    try:
                        shutdown_write_sock.sendall(b'X')
                    except OSError:
                        pass

                shutdown_thread = threading.Thread(
                    target=wake_for_shutdown,
                    name='RuntimeControlledServiceShutdown',
                    daemon=True,
                )
                shutdown_thread.start()

                return_with_activity = False
                shutdown_reported = False
                control_buf = bytearray()

                with selectors.DefaultSelector() as selector:
                    selector.register(control_sock, selectors.EVENT_READ, 'control')
                    selector.register(shutdown_read_sock, selectors.EVENT_READ, 'shutdown')

                    try:
                        while True:
                            request = runtime.shutdown.request_
                            if request is not None and not shutdown_reported:
                                _send_json(control_sock, {
                                    'event': 'SHUTDOWN',
                                    'reason': request.reason.name,
                                    'signal': request.signal,
                                })
                                shutdown_reported = True

                            if request is not None and not runtime.activity.active_count:
                                _send_json(control_sock, {'event': 'EXITING'})
                                break

                            for key, _ in selector.select():
                                if key.data == 'shutdown':
                                    shutdown_read_sock.recv(4096)
                                    continue

                                command = _receive_json(control_sock, control_buf)
                                if command is None:
                                    runtime.shutdown.request(message='control-closed')
                                    continue

                                match command['command']:
                                    case 'START':
                                        try:
                                            activities.append(runtime.activity.acquire())
                                        except ActivityRejectedError as exc:
                                            _send_json(control_sock, {
                                                'event': 'REJECTED',
                                                'reason': exc.request.reason.name,
                                            })
                                        else:
                                            _send_json(control_sock, {
                                                'event': 'ACTIVE',
                                                'count': runtime.activity.active_count,
                                            })

                                    case 'FINISH':
                                        activities.pop().close()
                                        _send_json(control_sock, {
                                            'event': 'ACTIVE',
                                            'count': runtime.activity.active_count,
                                        })

                                    case 'WAIT_IDLE_WINDOW':
                                        idle_timeout_s = runtime.activity.idle_timeout_s
                                        if idle_timeout_s is None:
                                            raise RuntimeError('No idle timeout configured')
                                        wait_result = runtime.shutdown.wait(idle_timeout_s * 1.5)
                                        _send_json(control_sock, {
                                            'event': 'IDLE_WINDOW',
                                            'shutdown': wait_result is not None,
                                        })

                                    case 'STOP':
                                        runtime.shutdown.request(
                                            ShutdownReason.REQUESTED,
                                            message='control',
                                        )
                                        _send_json(control_sock, {'event': 'STOPPED'})

                                    case 'RETURN_ACTIVE':
                                        activities.append(runtime.activity.acquire())
                                        runtime.shutdown.request(
                                            ShutdownReason.REQUESTED,
                                            message='return-active',
                                        )
                                        _send_json(control_sock, {'event': 'RETURNING'})
                                        return_with_activity = True
                                        break

                                    case command_name:
                                        raise ValueError(command_name)

                                if return_with_activity:
                                    break

                            if return_with_activity:
                                break

                    finally:
                        if not runtime.shutdown.requested:
                            runtime.shutdown.request(message='service-exiting')
                        shutdown_thread.join()
