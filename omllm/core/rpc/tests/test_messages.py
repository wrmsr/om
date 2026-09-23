# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta
import unittest

from ..errors import RpcProtocolError
from ..errors import RpcRemoteErrorData
from ..messages import JsonRpcMessageCodec
from ..messages import RpcCancelMessage
from ..messages import RpcErrorMessage
from ..messages import RpcMessage
from ..messages import RpcNotificationMessage
from ..messages import RpcPingMessage
from ..messages import RpcPongMessage
from ..messages import RpcRequestMessage
from ..messages import RpcResultMessage


##


class TestJsonRpcMessageCodec(unittest.TestCase):
    def test_roundtrips(self) -> None:
        codec = JsonRpcMessageCodec()
        messages: ta.List[RpcMessage] = [
            RpcRequestMessage(1, 'add', {'a': 1}),
            RpcResultMessage(2, [1, None, True]),
            RpcErrorMessage(3, RpcRemoteErrorData('remote', 'ValueError', 'bad', 'trace')),
            RpcCancelMessage(4),
            RpcNotificationMessage('log', 'hello'),
            RpcPingMessage(5),
            RpcPongMessage(6),
        ]

        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(codec.decode(codec.encode(message)), message)

    def test_rejects_invalid_messages(self) -> None:
        codec = JsonRpcMessageCodec()

        for data in [
            b'[]',                                     # not an object
            b'{"type":"wat"}',                         # unknown tag
            b'{"type":"ping"}',                        # missing required field
            b'{"type":"ping","id":0}',                 # invariant: id must be positive
            b'{"type":"request","id":1,"method":""}',  # invariant: non-empty method
            b'{"type":"ping","id":1,"extra":2}',       # unknown field
            b'{"type":"result","id":1,"result":NaN}',  # non-finite
            b'not json',
        ]:
            with self.subTest(data=data):
                with self.assertRaises(RpcProtocolError):
                    codec.decode(data)

    def test_rejects_non_json_payload(self) -> None:
        codec = JsonRpcMessageCodec()

        with self.assertRaises(RpcProtocolError):
            codec.encode(RpcResultMessage(1, dc.MISSING))

    def test_invariants_are_enforced_at_construction(self) -> None:
        # Value invariants live in __post_init__ now, so an invalid message cannot even be built.
        with self.assertRaises(RpcProtocolError):
            RpcPingMessage(0)
        with self.assertRaises(RpcProtocolError):
            RpcRequestMessage(1, '')

    def test_bool_id_is_coerced_not_rejected(self) -> None:
        # Documented consequence of marshaling: the lite marshaler coerces primitives, so a bool id becomes an int
        # rather than being rejected. Harmless under same-code-both-ends (a bool id is never sent).
        codec = JsonRpcMessageCodec()
        self.assertEqual(codec.decode(b'{"type":"ping","id":true}'), RpcPingMessage(1))
