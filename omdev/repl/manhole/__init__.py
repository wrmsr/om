# fmt: off
# ruff: noqa: I001
from omcore import lang as _lang


with _lang.auto_proxy_init(
        globals(),
):
    from .base import (  # noqa
        UnixAddress,
        TcpAddress,
        Address,
        parse_address,

        Connection,
        ConnectionHandler,

        ManholeServer,
    )

    from .client import (  # noqa
        connect,
        run_client,
    )

    from .protocol import (  # noqa
        strip_telnet_commands,
        decode_line,
        ManholeProtocol,
    )

    from .server import (  # noqa
        STANDARD_SEED,
        MANHOLE_MODULE_NAME,
        InterpreterFactory,
        default_banner,
        Manhole,
    )

    ##
    # hostings

    from .asyncio import (  # noqa
        AsyncioConnection,
        AsyncioManholeServer,
        AsyncioLoopThread,
        AsyncioThreadManhole,
        start_manhole,
    )

    from .sync import (  # noqa
        SyncSocketConnection,
        serve_inline,
        SyncThreadManhole,
    )
