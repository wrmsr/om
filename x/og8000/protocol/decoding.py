"""Deserialization of backend protocol messages. Pure: no IO, no connection state beyond the client encoding."""
import struct
import typing as ta

from ..exceptions import ProtocolError
from . import codes
from . import messages as msgs
from .codes import AuthenticationCode
from .codes import TransactionStatus
from .packing import COPY_RESPONSE_HEADER
from .packing import FIELD_DESCRIPTION_TAIL
from .packing import INT32
from .packing import INT32_PAIR
from .packing import UINT16


##


class BackendMessageDecoder:
    def __init__(self, *, encoding: str = 'utf8') -> None:
        super().__init__()

        self._encoding = encoding

    def set_encoding(self, encoding: str) -> None:
        self._encoding = encoding

    #

    def _str(self, b: bytes | memoryview) -> str:
        return bytes(b).decode(self._encoding)

    def _fields(self, payload: bytes) -> dict[str, str]:
        # The encoding of error and notice text is 'best effort', as these can arrive before (or about) the client
        # encoding being negotiated.
        return {
            s[:1].decode('ascii'): s[1:].decode(self._encoding, errors='replace')
            for s in payload.split(codes.NULL_BYTE)
            if s
        }

    #

    def _decode_authentication(self, payload: bytes) -> msgs.Authentication:
        code = INT32.unpack_from(payload)[0]
        rest = payload[4:]

        if code == AuthenticationCode.OK:
            return msgs.AuthenticationOk()
        elif code == AuthenticationCode.CLEARTEXT_PASSWORD:
            return msgs.AuthenticationCleartextPassword()
        elif code == AuthenticationCode.MD5_PASSWORD:
            return msgs.AuthenticationMd5Password(rest[:4])
        elif code == AuthenticationCode.SASL:
            return msgs.AuthenticationSasl([m.decode('ascii') for m in rest.split(codes.NULL_BYTE) if m])
        elif code == AuthenticationCode.SASL_CONTINUE:
            return msgs.AuthenticationSaslContinue(rest)
        elif code == AuthenticationCode.SASL_FINAL:
            return msgs.AuthenticationSaslFinal(rest)
        else:
            return msgs.AuthenticationOther(code, rest)

    def _decode_backend_key_data(self, payload: bytes) -> msgs.BackendKeyData:
        process_id, secret_key = INT32_PAIR.unpack_from(payload)
        return msgs.BackendKeyData(process_id, secret_key)

    def _decode_parameter_status(self, payload: bytes) -> msgs.ParameterStatus:
        pos = payload.find(codes.NULL_BYTE)
        return msgs.ParameterStatus(
            payload[:pos].decode('ascii'),
            payload[pos + 1:-1].decode(self._encoding),
        )

    def _decode_ready_for_query(self, payload: bytes) -> msgs.ReadyForQuery:
        try:
            status = TransactionStatus(payload[:1])
        except ValueError:
            raise ProtocolError(f'Unknown transaction status: {payload[:1]!r}') from None
        return msgs.ReadyForQuery(status)

    def _decode_row_description(self, payload: bytes) -> msgs.RowDescription:
        count = UINT16.unpack_from(payload)[0]
        idx = 2
        fields: list[msgs.FieldDescription] = []
        for _ in range(count):
            end = payload.find(codes.NULL_BYTE, idx)
            name = payload[idx:end].decode(self._encoding)
            idx = end + 1
            fields.append(msgs.FieldDescription(name, *FIELD_DESCRIPTION_TAIL.unpack_from(payload, idx)))
            idx += FIELD_DESCRIPTION_TAIL.size
        return msgs.RowDescription(fields)

    def _decode_data_row(self, payload: bytes) -> msgs.DataRow:
        count = UINT16.unpack_from(payload)[0]
        idx = 2
        values: list[bytes | None] = []
        for _ in range(count):
            length = INT32.unpack_from(payload, idx)[0]
            idx += 4
            if length == -1:
                values.append(None)
            else:
                values.append(payload[idx:idx + length])
                idx += length
        return msgs.DataRow(values)

    def _decode_command_complete(self, payload: bytes) -> msgs.CommandComplete:
        return msgs.CommandComplete(payload[:-1].decode(self._encoding))

    def _decode_error_response(self, payload: bytes) -> msgs.ErrorResponse:
        return msgs.ErrorResponse(self._fields(payload))

    def _decode_notice_response(self, payload: bytes) -> msgs.NoticeResponse:
        return msgs.NoticeResponse(self._fields(payload))

    def _decode_notification_response(self, payload: bytes) -> msgs.NotificationResponse:
        process_id = INT32.unpack_from(payload)[0]
        idx = 4
        end = payload.find(codes.NULL_BYTE, idx)
        channel = payload[idx:end].decode(self._encoding)
        idx = end + 1
        end = payload.find(codes.NULL_BYTE, idx)
        notification = payload[idx:end].decode(self._encoding)
        return msgs.NotificationResponse(process_id, channel, notification)

    def _decode_parameter_description(self, payload: bytes) -> msgs.ParameterDescription:
        count = UINT16.unpack_from(payload)[0]
        return msgs.ParameterDescription(struct.unpack_from(f'!{count}i', payload, 2))

    def _decode_copy_response(self, payload: bytes) -> tuple[bool, tuple[int, ...]]:
        fmt, count = COPY_RESPONSE_HEADER.unpack_from(payload)
        return bool(fmt), struct.unpack_from(f'!{count}h', payload, COPY_RESPONSE_HEADER.size)

    def _decode_copy_in_response(self, payload: bytes) -> msgs.CopyInResponse:
        return msgs.CopyInResponse(*self._decode_copy_response(payload))

    def _decode_copy_out_response(self, payload: bytes) -> msgs.CopyOutResponse:
        return msgs.CopyOutResponse(*self._decode_copy_response(payload))

    def _decode_copy_data(self, payload: bytes) -> msgs.CopyData:
        return msgs.CopyData(payload)

    _DECODERS: ta.ClassVar[ta.Mapping[bytes, ta.Callable[[ta.Any, bytes], msgs.BackendMessage]]] = {
        codes.AUTHENTICATION: _decode_authentication,
        codes.BACKEND_KEY_DATA: _decode_backend_key_data,
        codes.PARAMETER_STATUS: _decode_parameter_status,
        codes.READY_FOR_QUERY: _decode_ready_for_query,
        codes.ROW_DESCRIPTION: _decode_row_description,
        codes.DATA_ROW: _decode_data_row,
        codes.COMMAND_COMPLETE: _decode_command_complete,
        codes.ERROR_RESPONSE: _decode_error_response,
        codes.NOTICE_RESPONSE: _decode_notice_response,
        codes.NOTIFICATION_RESPONSE: _decode_notification_response,
        codes.PARAMETER_DESCRIPTION: _decode_parameter_description,
        codes.COPY_IN_RESPONSE: _decode_copy_in_response,
        codes.COPY_OUT_RESPONSE: _decode_copy_out_response,
        codes.COPY_DATA: _decode_copy_data,
        codes.COPY_DONE: lambda self, payload: msgs.CopyDone(),
        codes.PARSE_COMPLETE: lambda self, payload: msgs.ParseComplete(),
        codes.BIND_COMPLETE: lambda self, payload: msgs.BindComplete(),
        codes.CLOSE_COMPLETE: lambda self, payload: msgs.CloseComplete(),
        codes.PORTAL_SUSPENDED: lambda self, payload: msgs.PortalSuspended(),
        codes.NO_DATA: lambda self, payload: msgs.NoData(),
        codes.EMPTY_QUERY_RESPONSE: lambda self, payload: msgs.EmptyQueryResponse(),
    }

    def decode(self, code: bytes, payload: bytes) -> msgs.BackendMessage:
        try:
            fn = self._DECODERS[code]
        except KeyError:
            raise ProtocolError(f'Unknown backend message type: {code!r}') from None
        return fn(self, payload)
