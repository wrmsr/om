# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta


##


class RpcError(Exception):
    pass


class RpcProtocolError(RpcError):
    pass


class RpcConnectionClosedError(RpcError):
    pass


class RpcMethodNotFoundError(RpcError):
    def __init__(self, method: str) -> None:
        super().__init__(f'RPC method not found: {method!r}')

        self.method = method


@dc.dataclass(frozen=True)
class RpcRemoteErrorData:
    code: str
    remote_type: str
    message: str
    traceback: ta.Optional[str] = None


class RpcRemoteError(RpcError):
    def __init__(self, data: RpcRemoteErrorData) -> None:
        super().__init__(f'{data.remote_type}: {data.message}')

        self.data = data

    @property
    def code(self) -> str:
        return self.data.code

    @property
    def remote_type(self) -> str:
        return self.data.remote_type

    @property
    def remote_message(self) -> str:
        return self.data.message

    @property
    def remote_traceback(self) -> ta.Optional[str]:
        return self.data.traceback


class RpcRemoteCancelledError(RpcRemoteError):
    pass
