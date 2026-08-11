import json
import os
import selectors
import socket
import threading
import typing as ta
import uuid

from ... import dataclasses as dc
from ..runtime import ActivityRejectedError
from ..runtime import ServiceRuntime
from ..services import RuntimeService


##


def _receive_json(sock: socket.socket) -> ta.Mapping[str, ta.Any] | None:
    buf = bytearray()
    while not buf.endswith(b'\n'):
        chunk = sock.recv(4096)
        if not chunk:
            return None
        buf.extend(chunk)

    obj = json.loads(buf.decode('utf-8'))
    if not isinstance(obj, dict):
        raise TypeError(obj)
    return obj


def _send_json(sock: socket.socket, obj: ta.Mapping[str, ta.Any]) -> None:
    sock.sendall(json.dumps(obj).encode('utf-8') + b'\n')


##


class LazySocketService(RuntimeService['LazySocketService.Config']):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        socket_path: str = ''
        launch_log: str = ''

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _record_launch(self, instance: uuid.UUID) -> None:
        data = json.dumps({
            'instance': str(instance),
            'pid': os.getpid(),
        }).encode('utf-8') + b'\n'

        fd = os.open(
            self.config.launch_log,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            while data:
                data = data[os.write(fd, data):]
        finally:
            os.close(fd)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        instance = uuid.uuid7()

        try:
            os.unlink(self.config.socket_path)
        except FileNotFoundError:
            pass

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(self.config.socket_path)
            listener.listen()
            self._record_launch(instance)

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
                    name='LazySocketServiceShutdown',
                    daemon=True,
                )
                shutdown_thread.start()

                try:
                    with selectors.DefaultSelector() as selector:
                        selector.register(listener, selectors.EVENT_READ, 'listener')
                        selector.register(shutdown_read_sock, selectors.EVENT_READ, 'shutdown')

                        while not runtime.shutdown.requested:
                            for key, _ in selector.select():
                                if key.data == 'shutdown':
                                    shutdown_read_sock.recv(4096)
                                    continue

                                conn, _ = listener.accept()
                                with conn:
                                    try:
                                        activity = runtime.activity.acquire()
                                    except ActivityRejectedError:
                                        continue

                                    with activity:
                                        request = _receive_json(conn)
                                        if request is None:
                                            continue

                                        command = request['command']
                                        if command == 'SHUTDOWN':
                                            runtime.shutdown.request(message='test-request')
                                        elif command != 'PING':
                                            raise ValueError(command)

                                        _send_json(conn, {
                                            'command': command,
                                            'instance': str(instance),
                                            'pid': os.getpid(),
                                            'value': request.get('value'),
                                        })

                finally:
                    if not runtime.shutdown.requested:
                        runtime.shutdown.request(message='service-exiting')
                    shutdown_thread.join()

        try:
            os.unlink(self.config.socket_path)
        except FileNotFoundError:
            pass
