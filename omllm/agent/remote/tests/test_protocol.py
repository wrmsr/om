# ruff: noqa: UP006 UP007 UP045
import base64
import typing as ta
import unittest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from .. import protocol as proto


class TestRemoteProtocol(unittest.TestCase):
    def _roundtrip(self, obj: ta.Any) -> None:
        self.assertEqual(unmarshal_obj(marshal_obj(obj), type(obj)), obj)

    def test_roundtrips(self) -> None:
        self._roundtrip(proto.PathParams('/a/b'))
        self._roundtrip(proto.StatResult(path='/a', size=3, is_dir=False, is_file=True, is_symlink=False))
        self._roundtrip(proto.ReadFileResult(data=b'\x00\xffhi', digest='d'))
        self._roundtrip(proto.WriteFileParams(path='/a', content=b'x', overwrite=True, expected_digest=None))
        self._roundtrip(proto.WriteFileResult(created=True))
        self._roundtrip(proto.GlobParams(pattern='*.py', root='/r', max_results=None))
        self._roundtrip(proto.GlobResult(entries=[proto.FsEntry('a', '/a', True, False, False)], has_more=True))
        self._roundtrip(proto.SpawnParams(
            argv=['sh', '-c', 'x'],
            cwd='/r',
            env={'A': 'b'},
            stdio=proto.StdioSpec(kind='pipes', stdin='pipe', stdout='pipe', stderr='stdout'),
            name=None,
        ))
        self._roundtrip(proto.SpawnParams(
            argv=['x'],
            cwd=None,
            env=None,
            stdio=proto.StdioSpec(kind='pty', rows=20, cols=70, term='xterm'),
            name='n',
        ))
        self._roundtrip(proto.SpawnResult(id='p1', pid=42, created_at=1.5, name=None))
        self._roundtrip(proto.SignalParams(id='p1', signal=15, process_group=True))
        self._roundtrip(proto.CloseParams(id='p1', policy=proto.ClosePolicySpec(
            signal=15, grace_s=5., kill_s=5., close_stdin=True, process_group=True, drain_s=1.,
        )))
        self._roundtrip(proto.CloseResult(returncode=-9, state='reaped'))
        self._roundtrip(proto.WriteParams(id='p1', data=b'abc'))
        self._roundtrip(proto.ProcessRefParams(id='p1'))
        self._roundtrip(proto.ResizeParams(id='p1', rows=30, cols=100))
        self._roundtrip(proto.OutputEvent(id='p1', fd=1, data=b'out'))
        self._roundtrip(proto.OutputEndEvent(id='p1'))
        self._roundtrip(proto.ExitedEvent(id='p1', returncode=0))

    def test_bytes_are_standard_base64_on_the_wire(self) -> None:
        raw = b'\x00\xff\x10hello world'
        wire = base64.b64encode(raw).decode('ascii')
        self.assertEqual(marshal_obj(proto.WriteParams(id='p', data=raw))['data'], wire)
        self.assertEqual(unmarshal_obj({'id': 'p', 'data': wire}, proto.WriteParams).data, raw)

    def test_unknown_and_missing_fields_are_rejected(self) -> None:
        with self.assertRaises(KeyError):
            unmarshal_obj({'path': '/a', 'extra': 1}, proto.PathParams)
        with self.assertRaises(TypeError):
            unmarshal_obj({}, proto.PathParams)

    def test_invariants(self) -> None:
        with self.assertRaises(Exception):  # noqa
            proto.SignalParams(id='p1', signal=0, process_group=False)
        with self.assertRaises(Exception):  # noqa
            proto.ResizeParams(id='p1', rows=0, cols=1)
        with self.assertRaises(Exception):  # noqa
            proto.SpawnParams(
                argv=[],
                cwd=None,
                env=None,
                stdio=proto.StdioSpec(kind='pipes', stdin='pipe', stdout='pipe', stderr='pipe'),
                name=None,
            )
        with self.assertRaises(ValueError):
            proto.StdioSpec(kind='nope')
        with self.assertRaises(Exception):  # noqa
            proto.SpawnResult(id='', pid=1, created_at=0., name=None)
