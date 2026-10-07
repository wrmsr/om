# ruff: noqa: UP006 UP007 UP045
import base64
import typing as ta
import unittest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from .. import protocol as proto


class TestRemoteProcessProtocol(unittest.TestCase):
    def _roundtrip(self, obj: ta.Any) -> None:
        self.assertEqual(unmarshal_obj(marshal_obj(obj), type(obj)), obj)

    def test_roundtrips(self) -> None:
        self._roundtrip(proto.RemoteProcessSpawnParams(
            argv=['sh', '-c', 'x'],
            cwd='/r',
            env={'A': 'b'},
            stdio=proto.RemoteProcessStdioSpec(kind='pipes', stdin='pipe', stdout='pipe', stderr='stdout'),
            name=None,
        ))
        self._roundtrip(proto.RemoteProcessSpawnParams(
            argv=['x'],
            cwd=None,
            env=None,
            stdio=proto.RemoteProcessStdioSpec(kind='pty', rows=20, cols=70, term='xterm'),
            name='n',
        ))
        self._roundtrip(proto.RemoteProcessSpawnResult(id='p1', pid=42, created_at=1.5, name=None))
        self._roundtrip(proto.RemoteProcessSignalParams(id='p1', signal=15, process_group=True))
        self._roundtrip(proto.RemoteProcessCloseParams(id='p1', policy=proto.RemoteProcessClosePolicySpec(
            signal=15, grace_s=5., kill_s=5., close_stdin=True, process_group=True, drain_s=1.,
        )))
        self._roundtrip(proto.RemoteProcessCloseResult(returncode=-9, state='reaped'))
        self._roundtrip(proto.RemoteProcessWriteParams(id='p1', data=b'abc'))
        self._roundtrip(proto.RemoteProcessRefParams(id='p1'))
        self._roundtrip(proto.RemoteProcessResizeParams(id='p1', rows=30, cols=100))
        self._roundtrip(proto.RemoteProcessOutputEvent(id='p1', fd=1, data=b'out'))
        self._roundtrip(proto.RemoteProcessOutputEndEvent(id='p1'))
        self._roundtrip(proto.RemoteProcessExitedEvent(id='p1', returncode=0))

    def test_bytes_are_standard_base64_on_the_wire(self) -> None:
        raw = b'\x00\xff\x10hello world'
        wire = base64.b64encode(raw).decode('ascii')
        self.assertEqual(marshal_obj(proto.RemoteProcessWriteParams(id='p', data=raw))['data'], wire)
        self.assertEqual(unmarshal_obj({'id': 'p', 'data': wire}, proto.RemoteProcessWriteParams).data, raw)

    def test_unknown_and_missing_fields_are_rejected(self) -> None:
        with self.assertRaises(KeyError):
            unmarshal_obj({'id': 'p1', 'extra': 1}, proto.RemoteProcessRefParams)
        with self.assertRaises(TypeError):
            unmarshal_obj({}, proto.RemoteProcessRefParams)

    def test_event_methods(self) -> None:
        self.assertEqual(proto.REMOTE_PROCESS_EVENT_METHODS, {
            proto.REMOTE_PROCESS_OUTPUT_METHOD,
            proto.REMOTE_PROCESS_OUTPUT_END_METHOD,
            proto.REMOTE_PROCESS_EXITED_METHOD,
        })

    def test_invariants(self) -> None:
        with self.assertRaises(Exception):  # noqa
            proto.RemoteProcessSignalParams(id='p1', signal=0, process_group=False)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteProcessResizeParams(id='p1', rows=0, cols=1)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteProcessSpawnParams(
                argv=[],
                cwd=None,
                env=None,
                stdio=proto.RemoteProcessStdioSpec(kind='pipes', stdin='pipe', stdout='pipe', stderr='pipe'),
                name=None,
            )
        with self.assertRaises(ValueError):
            proto.RemoteProcessStdioSpec(kind='nope')
        with self.assertRaises(Exception):  # noqa
            proto.RemoteProcessSpawnResult(id='', pid=1, created_at=0., name=None)
