import contextlib
import socket
import typing as ta

import pytest


T = ta.TypeVar('T')


SqlBackend: ta.TypeAlias = ta.Literal[
    'mysql',
    'postgres',
]


##


def mark_sql_backend(backend: SqlBackend) -> ta.Callable[[T], T]:
    def inner(obj):
        pytest.mark.xdist_group(backend)(obj)
        return obj

    return inner


@contextlib.contextmanager
def stalled_tcp_listener() -> ta.Iterator[tuple[str, int]]:
    """Fill a local listener's accept queue so a further TCP connect must wait."""

    with socket.create_server(('127.0.0.1', 0), backlog=1) as listener:
        address = listener.getsockname()
        with contextlib.ExitStack() as connections:
            for _ in range(256):
                try:
                    connections.enter_context(socket.create_connection(address, timeout=.1))
                except TimeoutError:
                    break
            else:
                raise RuntimeError('could not fill the local TCP listen queue')
            yield address
