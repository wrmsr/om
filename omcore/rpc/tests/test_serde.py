# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from ...lite.asyncs import as_async
from ..dispatch import RpcMethodTableHandler
from ..errors import RpcRemoteError
from ..pure import pure_rpc_connection_pair
from ..serde import IdentityRpcSerde
from ..serde import LiteMarshalRpcSerde
from ..serde import RpcTypedCaller
from ..serde import rpc_typed_method
from ..translate import translate_rpc_remote_builtin_error


##


@dc.dataclass(frozen=True)
class _RpcSerdeTestPoint:
    x: int
    y: int
    label: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class _RpcSerdeTestBox:
    points: ta.Sequence[_RpcSerdeTestPoint]


class TestSerde(unittest.TestCase):
    def test_lite_marshal_typed_roundtrip(self):
        serde = LiteMarshalRpcSerde()
        notes: ta.List[ta.Any] = []

        async def bounds(box: _RpcSerdeTestBox) -> _RpcSerdeTestPoint:
            return _RpcSerdeTestPoint(max(p.x for p in box.points), max(p.y for p in box.points), 'max')

        def nothing() -> None:
            return None

        async def note(p: _RpcSerdeTestPoint) -> None:
            notes.append(p)

        h = RpcMethodTableHandler(
            {
                'bounds': rpc_typed_method(bounds, _RpcSerdeTestBox, _RpcSerdeTestPoint, serde=serde),
                'nothing': rpc_typed_method(as_async(nothing), serde=serde),
            },
            notifications={
                'note': rpc_typed_method(note, _RpcSerdeTestPoint, serde=serde),
            },
        )
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=h))
        caller = RpcTypedCaller(pair.a.connection, serde)

        box = _RpcSerdeTestBox([_RpcSerdeTestPoint(1, 5), _RpcSerdeTestPoint(3, 2)])
        self.assertEqual(
            pair.a.run(caller.call('bounds', box, _RpcSerdeTestPoint)),
            _RpcSerdeTestPoint(3, 5, 'max'),
        )

        # Without a result type the wire value comes back as-is.
        self.assertEqual(pair.a.run(caller.call('bounds', box)), {'x': 3, 'y': 5, 'label': 'max'})

        self.assertIsNone(pair.a.run(caller.call('nothing', result_type=_RpcSerdeTestPoint)))

        pair.a.run(caller.notify('note', _RpcSerdeTestPoint(7, 8)))
        pair.a.ping()
        self.assertEqual(notes, [_RpcSerdeTestPoint(7, 8)])

    def test_identity(self):
        serde = IdentityRpcSerde()
        h = RpcMethodTableHandler({'len': rpc_typed_method(as_async(len), list, int, serde=serde)})
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=h))
        self.assertEqual(pair.a.run(RpcTypedCaller(pair.a.connection, serde).call('len', [1, 2, 3], int)), 3)

    def test_error_translation(self):
        def missing(p: ta.Any) -> ta.Any:
            raise FileNotFoundError('/nope')

        def other(p: ta.Any) -> ta.Any:
            raise ValueError('x')

        serde = IdentityRpcSerde()
        h = RpcMethodTableHandler({
            'missing': rpc_typed_method(as_async(missing), object, serde=serde),
            'other': rpc_typed_method(as_async(other), object, serde=serde),
        })
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=h))

        caller = RpcTypedCaller(pair.a.connection, serde, translate_error=translate_rpc_remote_builtin_error)
        with self.assertRaises(FileNotFoundError) as cm:
            pair.a.run(caller.call('missing', 1))
        self.assertIsInstance(cm.exception.__cause__, RpcRemoteError)
        with self.assertRaises(RpcRemoteError):
            pair.a.run(caller.call('other', 1))

        plain = RpcTypedCaller(pair.a.connection, serde)
        with self.assertRaises(RpcRemoteError):
            pair.a.run(plain.call('missing', 1))
