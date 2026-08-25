"""Serialization of frontend protocol messages. Pure: no IO, no connection state beyond the client encoding."""
import typing as ta

from . import codes
from . import messages as msgs
from .packing import INT32
from .packing import INT32_PAIR
from .packing import UINT16


##


def frame_message(code: bytes, payload: bytes | bytearray = b'') -> bytes:
    return code + INT32.pack(len(payload) + 4) + payload


class FrontendMessageEncoder:
    def __init__(self, *, encoding: str = 'utf8') -> None:
        super().__init__()

        self._encoding = encoding

    def set_encoding(self, encoding: str) -> None:
        self._encoding = encoding

    #

    def _str(self, s: str) -> bytes:
        return s.encode(self._encoding)

    def _cstr(self, s: str) -> bytes:
        return s.encode(self._encoding) + codes.NULL_BYTE

    #

    def _encode_ssl_request(self, msg: msgs.SslRequest) -> bytes:
        return INT32_PAIR.pack(8, codes.SSL_REQUEST_CODE)

    def _encode_startup_message(self, msg: msgs.StartupMessage) -> bytes:
        body = bytearray(INT32.pack(codes.PROTOCOL_VERSION))
        for k, v in msg.params.items():
            body.extend(k.encode('ascii') + codes.NULL_BYTE + v + codes.NULL_BYTE)
        body.extend(codes.NULL_BYTE)
        return INT32.pack(len(body) + 4) + bytes(body)

    def _encode_password_message(self, msg: msgs.PasswordMessage) -> bytes:
        return frame_message(codes.PASSWORD, msg.password + codes.NULL_BYTE)

    def _encode_sasl_initial_response(self, msg: msgs.SaslInitialResponse) -> bytes:
        return frame_message(
            codes.PASSWORD,
            msg.mechanism.encode('ascii') + codes.NULL_BYTE + INT32.pack(len(msg.data)) + msg.data,
        )

    def _encode_sasl_response(self, msg: msgs.SaslResponse) -> bytes:
        return frame_message(codes.PASSWORD, msg.data)

    def _encode_query(self, msg: msgs.Query) -> bytes:
        return frame_message(codes.QUERY, self._cstr(msg.sql))

    def _encode_parse(self, msg: msgs.Parse) -> bytes:
        body = bytearray(self._cstr(msg.name))
        body.extend(self._cstr(msg.sql))
        body.extend(UINT16.pack(len(msg.type_oids)))
        for oid in msg.type_oids:
            # An oid of -1 is the client-side marker for 'unspecified', which the server spells as zero.
            body.extend(INT32.pack(0 if oid == -1 else oid))
        return frame_message(codes.PARSE, body)

    def _encode_bind(self, msg: msgs.Bind) -> bytes:
        body = bytearray(self._cstr(msg.portal))
        body.extend(self._cstr(msg.statement))
        body.extend(UINT16.pack(0))  # parameter format codes: all text
        body.extend(UINT16.pack(len(msg.params)))
        for param in msg.params:
            if param is None:
                body.extend(INT32.pack(-1))
            else:
                val = self._str(param)
                body.extend(INT32.pack(len(val)))
                body.extend(val)
        body.extend(UINT16.pack(0))  # result format codes: all text
        return frame_message(codes.BIND, body)

    def _encode_describe(self, msg: msgs.Describe) -> bytes:
        return frame_message(codes.DESCRIBE, msg.kind.value + self._cstr(msg.name))

    def _encode_execute(self, msg: msgs.Execute) -> bytes:
        return frame_message(codes.EXECUTE, self._cstr(msg.portal) + INT32.pack(msg.max_rows))

    def _encode_close(self, msg: msgs.Close) -> bytes:
        return frame_message(codes.CLOSE, msg.kind.value + self._cstr(msg.name))

    def _encode_flush(self, msg: msgs.Flush) -> bytes:
        return frame_message(codes.FLUSH)

    def _encode_sync(self, msg: msgs.Sync) -> bytes:
        return frame_message(codes.SYNC)

    def _encode_terminate(self, msg: msgs.Terminate) -> bytes:
        return frame_message(codes.TERMINATE)

    def _encode_copy_data(self, msg: msgs.CopyData) -> bytes:
        return frame_message(codes.COPY_DATA, msg.data)

    def _encode_copy_done(self, msg: msgs.CopyDone) -> bytes:
        return frame_message(codes.COPY_DONE)

    def _encode_copy_fail(self, msg: msgs.CopyFail) -> bytes:
        return frame_message(codes.COPY_FAIL, self._cstr(msg.message))

    _ENCODERS: ta.ClassVar[ta.Mapping[type[msgs.FrontendMessage], ta.Callable[[ta.Any, ta.Any], bytes]]] = {
        msgs.SslRequest: _encode_ssl_request,
        msgs.StartupMessage: _encode_startup_message,
        msgs.PasswordMessage: _encode_password_message,
        msgs.SaslInitialResponse: _encode_sasl_initial_response,
        msgs.SaslResponse: _encode_sasl_response,
        msgs.Query: _encode_query,
        msgs.Parse: _encode_parse,
        msgs.Bind: _encode_bind,
        msgs.Describe: _encode_describe,
        msgs.Execute: _encode_execute,
        msgs.Close: _encode_close,
        msgs.Flush: _encode_flush,
        msgs.Sync: _encode_sync,
        msgs.Terminate: _encode_terminate,
        msgs.CopyData: _encode_copy_data,
        msgs.CopyDone: _encode_copy_done,
        msgs.CopyFail: _encode_copy_fail,
    }

    def encode(self, msg: msgs.FrontendMessage) -> bytes:
        try:
            fn = self._ENCODERS[type(msg)]
        except KeyError:
            raise TypeError(f'Unsupported frontend message: {msg!r}') from None
        return fn(self, msg)
