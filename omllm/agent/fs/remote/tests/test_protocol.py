# ruff: noqa: UP006 UP007 UP045
import typing as ta
import unittest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from .. import protocol as proto


class TestRemoteFsProtocol(unittest.TestCase):
    def _roundtrip(self, obj: ta.Any) -> None:
        self.assertEqual(unmarshal_obj(marshal_obj(obj), type(obj)), obj)

    def test_roundtrips(self) -> None:
        self._roundtrip(proto.RemoteFsPathParams('/a/b'))
        self._roundtrip(proto.RemoteFsStatResult(path='/a', size=3, is_dir=False, is_file=True, is_symlink=False))
        self._roundtrip(proto.RemoteFsReadFileResult(data=b'\x00\xffhi', digest='d'))
        self._roundtrip(proto.RemoteFsWriteFileParams(path='/a', content=b'x', overwrite=True, expected_digest=None))
        self._roundtrip(proto.RemoteFsWriteFileResult(created=True))
        self._roundtrip(proto.RemoteFsGlobParams(pattern='*.py', root='/r', max_results=None))
        self._roundtrip(proto.RemoteFsGlobResult(
            entries=[proto.RemoteFsEntry('a', '/a', True, False, False)],
            has_more=True,
        ))

    def test_unknown_and_missing_fields_are_rejected(self) -> None:
        with self.assertRaises(KeyError):
            unmarshal_obj({'path': '/a', 'extra': 1}, proto.RemoteFsPathParams)
        with self.assertRaises(TypeError):
            unmarshal_obj({}, proto.RemoteFsPathParams)

    def test_invariants(self) -> None:
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsStatResult(path='/a', size=-1, is_dir=False, is_file=True, is_symlink=False)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadFileResult(data=b'', digest='')
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsGlobParams(pattern='*', root='/r', max_results=-1)
