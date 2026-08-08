import json
import os
import socket
import typing as ta

from ... import dataclasses as dc
from ..rpc import RpcRequest


##


@dc.dataclass(frozen=True, kw_only=True)
class ControlledRpcHandler:
    execution_log: str
    control_path: str | None = None

    def _record(self, request: RpcRequest) -> None:
        data = json.dumps({
            'client_id': request.client_id,
            'method': request.method,
            'pid': os.getpid(),
            'request_id': request.request_id,
        }).encode('utf-8') + b'\n'

        fd = os.open(
            self.execution_log,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            while data:
                data = data[os.write(fd, data):]
        finally:
            os.close(fd)

    def __call__(self, request: RpcRequest) -> ta.Any:
        self._record(request)

        if request.method == 'echo':
            return {
                'params': request.params,
                'pid': os.getpid(),
            }

        if request.method == 'fail':
            raise RuntimeError(f'controlled failure: {request.params}')

        if request.method == 'block':
            if self.control_path is None:
                raise RuntimeError('No control path configured')

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(self.control_path)
                sock.sendall(json.dumps({
                    'pid': os.getpid(),
                    'request_id': request.request_id,
                }).encode('utf-8') + b'\n')
                if sock.recv(1) != b'X':
                    raise RuntimeError('Block control connection closed before release')

            return {
                'params': request.params,
                'pid': os.getpid(),
            }

        raise ValueError(request.method)
