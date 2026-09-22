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
            b'[]',
            b'{"type":"wat"}',
            b'{"type":"ping","id":true}',
            b'{"type":"ping","id":1,"extra":2}',
            b'{"type":"result","id":1,"result":NaN}',
            b'not json',
        ]:
            with self.subTest(data=data):
                with self.assertRaises(RpcProtocolError):
                    codec.decode(data)

    def test_rejects_non_json_payload(self) -> None:
        codec = JsonRpcMessageCodec()

        with self.assertRaises(RpcProtocolError):
            codec.encode(RpcResultMessage(1, dc.MISSING))

    def test_rejects_invalid_outbound_envelope(self) -> None:
        codec = JsonRpcMessageCodec()

        with self.assertRaises(RpcProtocolError):
            codec.encode(RpcPingMessage(0))
