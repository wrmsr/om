from .. import check
from .. import dataclasses as dc
from .. import lang


##


class SocketEndpoint(lang.Abstract):
    """A transport-neutral byte-stream socket endpoint description."""


@dc.dataclass(frozen=True, kw_only=True)
class UnixSocketEndpoint(SocketEndpoint):
    path: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.path)


@dc.dataclass(frozen=True, kw_only=True)
class TcpSocketEndpoint(SocketEndpoint):
    host: str
    port: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.host)
        check.arg(0 <= self.port <= 65_535)


def resolve_socket_endpoint(
        *,
        endpoint: SocketEndpoint | None,
        socket_path: str,
) -> SocketEndpoint:
    """Accepts either an explicit endpoint or the compatibility spelling of a unix socket path, not both."""

    check.isinstance(socket_path, str)
    if endpoint is None:
        return UnixSocketEndpoint(path=check.non_empty_str(socket_path))

    check.arg(not socket_path, 'Specify either endpoint or socket_path, not both')
    return check.isinstance(endpoint, SocketEndpoint)
