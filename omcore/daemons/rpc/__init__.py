from ... import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .asyncio import (  # noqa
        AsyncioRpcClient,
        AsyncioRpcClientConnection,
        AsyncioRpcServer,
        AsyncioRpcServerConfig,
        AsyncRpcHandler,
        ThreadedAsyncRpcHandler,
    )

    from .client import (  # noqa
        RpcClient,
        RpcClientConnection,
    )

    # Endpoints and transports live in omcore.sockets; they are re-exported here under their historical names.
    from ...sockets.endpoints import (  # noqa
        SocketEndpoint as RpcEndpoint,
        UnixSocketEndpoint as UnixRpcEndpoint,
        TcpSocketEndpoint as TcpRpcEndpoint,
        resolve_socket_endpoint as resolve_rpc_endpoint,
    )

    from .fdio import (  # noqa
        FdioRpcServer,
    )

    # Daemon integration adapters. The core protocol, client, server, and object facade modules above do not depend on
    # the daemon lifecycle.
    from .lazy import (  # noqa
        LazyRpcClient,
    )

    from .objects import (  # noqa
        RpcCaller,
        RpcObjectHandler,
        RpcObjectMethod,
        RpcObjectProxy,
        rpc_method,
    )

    from .protocol import (  # noqa
        RPC_DEFAULT_MAX_FRAME_BYTES,
        RPC_PROTOCOL_NAME,
        RPC_PROTOCOL_VERSION,

        RpcCallIndeterminateError,
        RpcError,
        RpcHandler,
        RpcProtocolError,
        RpcRemoteError,
        RpcRequest,
        RpcUnavailableError,
    )

    from .server import (  # noqa
        RpcServer,
        RpcServerConfig,
        RpcServerDrainTimeoutError,
        RpcServerRuntime,
        SimpleRpcServerRuntime,
    )

    from .services import (  # noqa
        RpcService,
    )

    from ...sockets.transports import (  # noqa
        SyncSocketListener as SyncRpcListener,
        SyncSocketTransport as SyncRpcTransport,
        OwnedSocketListener as SocketRpcListener,
        DefaultSyncSocketTransport as DefaultSyncRpcTransport,
        DEFAULT_SYNC_SOCKET_TRANSPORT as DEFAULT_SYNC_RPC_TRANSPORT,

        AsyncioSocketListener as AsyncioRpcListener,
        AsyncioSocketTransport as AsyncioRpcTransport,
        AsyncioServerSocketListener as AsyncioServerRpcListener,
        DefaultAsyncioSocketTransport as DefaultAsyncioRpcTransport,
        DEFAULT_ASYNCIO_SOCKET_TRANSPORT as DEFAULT_ASYNCIO_RPC_TRANSPORT,
    )

    from .waiting import (  # noqa
        RpcWait,
        RpcWaiter,
    )
