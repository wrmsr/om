from .errors import (  # noqa
    KnownError,
    KnownErrors,

    CUSTOM_ERROR_BASE,
    CUSTOM_ERROR_MIN,
    SERVER_BUSY_ERROR_CODE,
    SERVER_SHUTTING_DOWN_ERROR_CODE,
    REQUEST_TIMED_OUT_ERROR_CODE,
    RESPONSE_TOO_LARGE_ERROR_CODE,

    JsonrpcError,
    JsonrpcProtocolError,
    JsonrpcInvalidMessageError,
    JsonrpcConnectionClosedError,
    JsonrpcTimeoutError,
    JsonrpcMessageTooLargeError,
    JsonrpcTooManyRequestsError,

    JsonrpcErrorResponseError,
    JsonrpcRemoteError,
    JsonrpcMethodError,
)

from .types import (  # noqa
    NUMBER_TYPES,
    Number,
    Object,
    Params,
    ID_TYPES,
    Id,

    VERSION,

    NotSpecified,
    is_not_specified,
    check_not_not_specified,

    Request,
    request,
    notification,

    Response,
    result,

    Error,
    error,

    Message,
    detect_message_type,

    InvalidMessage,
    Batch,
    Payload,
)


##


from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .conns import (  # noqa
        JsonrpcConnection as Connection,
        AsyncJsonrpcConnection as AsyncConnection,
    )

    from .dispatch import (  # noqa
        JsonrpcDispatchContext as DispatchContext,
        JsonrpcDispatcher as Dispatcher,
        AsyncJsonrpcDispatcher as AsyncDispatcher,

        JsonrpcMethod as Method,
        JsonrpcMethodLike as MethodLike,
        jsonrpc_method_of as method_of,

        DictJsonrpcDispatcher as DictDispatcher,
        AsyncDictJsonrpcDispatcher as AsyncDictDispatcher,

        jsonrpc_error_for_exception as error_for_exception,
    )

    from .ids import (  # noqa
        JsonrpcIdCreator as IdCreator,
        IntJsonrpcIdCreator as IntIdCreator,
        UuidJsonrpcIdCreator as UuidIdCreator,
        FnJsonrpcIdCreator as FnIdCreator,
        JsonrpcIdCreatorLike as IdCreatorLike,
        jsonrpc_id_creator_of as id_creator_of,
    )

    from .parsing import (  # noqa
        ParseOptions,

        parse_message,
        parse_item,
        parse_payload,
        loads_payload,

        dump_error,
        dump_message,
        dump_payload,
        dumps_payload,

        Payloads,
    )


##


from ... import marshal as _msh


_msh.register_global_module_import('._marshal', __package__)
