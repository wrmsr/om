from ... import check
from ... import dataclasses as dc
from ... import lang


##


class RpcEndpoint(lang.Abstract):
    """A transport-neutral RPC byte-stream endpoint description."""


@dc.dataclass(frozen=True, kw_only=True)
class UnixRpcEndpoint(RpcEndpoint):
    path: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.path)


@dc.dataclass(frozen=True, kw_only=True)
class TcpRpcEndpoint(RpcEndpoint):
    host: str
    port: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.host)
        check.arg(0 <= self.port <= 65_535)


def resolve_rpc_endpoint(
        *,
        endpoint: RpcEndpoint | None,
        socket_path: str,
) -> RpcEndpoint:
    check.isinstance(socket_path, str)
    if endpoint is None:
        return UnixRpcEndpoint(path=check.non_empty_str(socket_path))

    check.arg(not socket_path, 'Specify either endpoint or socket_path, not both')
    return check.isinstance(endpoint, RpcEndpoint)
