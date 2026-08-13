from ... import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

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

    from .client import (  # noqa
        RpcClient,
        RpcClientConnection,
    )

    from .asyncio import (  # noqa
        AsyncioRpcClient,
        AsyncioRpcClientConnection,
        AsyncioRpcServer,
        AsyncioRpcServerConfig,
        AsyncRpcHandler,
        ThreadedAsyncRpcHandler,
    )

    from .server import (  # noqa
        RpcServer,
        RpcServerConfig,
        RpcServerDrainTimeoutError,
        RpcServerRuntime,
        SimpleRpcServerRuntime,
    )

    from .fdio import (  # noqa
        FdioRpcServer,
    )

    from .objects import (  # noqa
        RpcCaller,
        RpcObjectHandler,
        RpcObjectMethod,
        RpcObjectProxy,
        rpc_method,
    )

    # Daemon integration adapters. The core protocol, client, server, and object
    # facade modules above do not depend on the daemon lifecycle.
    from .lazy import (  # noqa
        LazyRpcClient,
    )

    from .waiting import (  # noqa
        RpcWait,
        RpcWaiter,
    )

    from .services import (  # noqa
        RpcService,
    )
