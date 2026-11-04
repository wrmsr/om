# @om-recommended-import-alias "rpc"
from .. import lang as _lang


with _lang.auto_proxy_init(
        globals(),
        update_exports=True,
):
    ##

    from .asyncios import (  # noqa
        AsyncioRpcRuntime as AsyncioRuntime,
        AsyncioSerializingRpcHandler as AsyncioSerializingHandler,
        AsyncioRpcConnections as AsyncioConnections,
    )

    from .closing import (  # noqa
        RpcCloseAfterRequestsIoPipelineHandler as CloseAfterRequestsHandler,
    )

    from .codecs import (  # noqa
        RpcValueCodec as ValueCodec,
        JsonRpcValueCodec as JsonValueCodec,

        RpcEnvelopeCodec as EnvelopeCodec,
        RpcValueEnvelopeCodec as ValueEnvelopeCodec,

        RpcEnvelopeCodecIoPipelineHandler as EnvelopeCodecHandler,
    )

    from .configs import (  # noqa
        RpcConfig as Config,
    )

    from .connection import (  # noqa
        RpcConnectionCloseCallback as ConnectionCloseCallback,
        RpcNotificationErrorHandler as NotificationErrorHandler,
        RpcTimeoutArg as TimeoutArg,

        BaseRpcConnection as BaseConnection,
        RpcConnection as Connection,

        BaseSyncRpcConnection as BaseSyncConnection,
        SyncRpcConnection as SyncConnection,
    )

    from .dispatch import (  # noqa
        RpcMethodFn as MethodFn,
        RpcInlineNotificationFn as InlineNotificationFn,

        RpcHandler as Handler,

        rpc_merge_method_tables as merge_method_tables,
        rpc_async_method as async_method,

        RpcMethodTableHandler as MethodTableHandler,
    )

    from .errors import (  # noqa
        RpcError as Error,
        RpcProtocolError as ProtocolError,
        RpcConnectionClosedError as ConnectionClosedError,
        RpcTimeoutError as TimeoutError,  # noqa
        RpcMessageTooLargeError as MessageTooLargeError,
        RpcTooManyRequestsError as TooManyRequestsError,
        RpcCancelledError as CancelledError,
        RpcMethodNotFoundError as MethodNotFoundError,
        RpcUnexpectedMessageError as UnexpectedMessageError,
        RpcHandlerError as HandlerError,

        RpcErrorCodes as ErrorCodes,

        RpcRemoteErrorData as RemoteErrorData,
        RpcRemoteError as RemoteError,
        RpcRemoteCancelledError as RemoteCancelledError,
        RpcRemoteMethodNotFoundError as RemoteMethodNotFoundError,
        RpcRemoteShuttingDownError as RemoteShuttingDownError,

        rpc_exception_type_name as exception_type_name,
        rpc_remote_error_for_data as remote_error_for_data,
    )

    from .fdios import (  # noqa
        RpcFdioPromise as FdioPromise,
        FdioRpcRuntime as FdioRuntime,
        RpcSocketFdioHandler as SocketFdioHandler,
    )

    from .framing import (  # noqa
        RpcFrame as Frame,

        RpcLengthPrefixedFramingIoPipelineHandler as LengthPrefixedFramingHandler,
    )

    from .handshake import (  # noqa
        RpcHelloValidator as HelloValidator,
        RpcHandshakeCompletedEvent as HandshakeCompletedEvent,
        RpcHandshakeIoPipelineHandler as HandshakeHandler,
    )

    from .ids import (  # noqa
        RpcIdCreatorLike as IdCreatorLike,

        RpcIdCreator as IdCreator,
        IntRpcIdCreator as IntIdCreator,
        UuidRpcIdCreator as UuidIdCreator,
        FnRpcIdCreator as FnIdCreator,

        rpc_id_creator_of as id_creator_of,
    )

    from .keepalive import (  # noqa
        RpcKeepaliveIoPipelineHandler as KeepaliveHandler,
    )

    from .marshal import (  # noqa
        MarshalRpcSerde as MarshalSerde,
    )

    from .messages import (  # noqa
        RpcUnspecified as Unspecified,

        RpcEnvelope as Envelope,
        RpcRequestMessage as RequestMessage,
        RpcResultMessage as ResultMessage,
        RpcErrorMessage as ErrorMessage,
        RpcCancelMessage as CancelMessage,
        RpcNotificationMessage as NotificationMessage,
        RpcPingMessage as PingMessage,
        RpcPongMessage as PongMessage,
        RpcHelloMessage as HelloMessage,
        RpcInfoEvent as InfoEvent,

        RpcResponseMessage as ResponseMessage,

        RpcSessionMessages as SessionMessages,
    )

    from .pure import (  # noqa
        PureRpcLinkDeadlockError as PureLinkDeadlockError,

        PureRpcRuntime as PureRuntime,
        PureRpcLink as PureLink,

        PureRpcConnectionPair as PureConnectionPair,
        pure_rpc_connection_pair as pure_connection_pair,
    )

    from .runtime import (  # noqa
        RpcRuntimeSink as RuntimeSink,
        RpcRuntime as Runtime,
    )

    from .serde import (  # noqa
        RpcErrorTranslator as ErrorTranslator,

        RpcSerde as Serde,
        IdentityRpcSerde as IdentitySerde,
        LiteMarshalRpcSerde as LiteMarshalSerde,

        rpc_typed_method as typed_method,

        RpcTypedCaller as TypedCaller,
    )

    from .session import (  # noqa
        RpcSessionState as SessionState,

        RpcSessionIoPipelineHandler as SessionHandler,
    )

    from .specs import (  # noqa
        rpc_build_pipeline_spec as build_pipeline_spec,
    )

    from .syncs import (  # noqa
        RpcSyncPromise as SyncPromise,

        BaseSyncRpcRuntime as BaseSyncRuntime,
        SyncRpcRuntime as SyncRuntime,

        SyncRpcConnections as SyncConnections,
    )

    from .translate import (  # noqa
        RPC_TRANSLATED_BUILTIN_EXCEPTIONS as TRANSLATED_BUILTIN_EXCEPTIONS,

        translate_rpc_remote_builtin_error as translate_remote_builtin_error,
    )
