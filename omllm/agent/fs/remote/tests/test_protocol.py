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
        self._roundtrip(proto.RemoteFsGlobParams(pattern='*.py', root='/r', max_results=None))
        self._roundtrip(proto.RemoteFsGlobResult(
            entries=[proto.RemoteFsEntry('a', '/a', True, False, False)],
            has_more=True,
        ))

        self._roundtrip(proto.RemoteFsHandleParams('r1'))
        self._roundtrip(proto.RemoteFsHandleResult('w1'))

        self._roundtrip(proto.RemoteFsReadFileParams(path='/a', max_bytes=10))
        self._roundtrip(proto.RemoteFsReadFileResult(data=b'\x00\xffhi', digest='d', handle=None))
        self._roundtrip(proto.RemoteFsReadFileResult(data=b'\x00\xffhi', digest=None, handle='r1'))
        self._roundtrip(proto.RemoteFsReadChunkParams(handle='r1', max_bytes=10))
        self._roundtrip(proto.RemoteFsReadChunkResult(data=b'x', digest=None))
        self._roundtrip(proto.RemoteFsReadChunkResult(data=b'', digest='d'))

        self._roundtrip(proto.RemoteFsWriteFileParams(path='/a', content=b'x', overwrite=True, expected_digest=None))
        self._roundtrip(proto.RemoteFsWriteFileResult(created=True))
        self._roundtrip(proto.RemoteFsWriteChunkParams(handle='w1', data=b'x'))
        self._roundtrip(proto.RemoteFsWriteCommitParams(handle='w1', overwrite=False, expected_digest='d'))

    def test_unknown_and_missing_fields_are_rejected(self) -> None:
        with self.assertRaises(KeyError):
            unmarshal_obj({'path': '/a', 'extra': 1}, proto.RemoteFsPathParams)
        with self.assertRaises(TypeError):
            unmarshal_obj({}, proto.RemoteFsPathParams)

    def test_invariants(self) -> None:
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsStatResult(path='/a', size=-1, is_dir=False, is_file=True, is_symlink=False)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsGlobParams(pattern='*', root='/r', max_results=-1)

        # A first read is either complete, with its digest, or continued through a handle - never both or neither.
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadFileResult(data=b'', digest='d', handle='r1')
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadFileResult(data=b'', digest=None, handle=None)

        # Nothing on the wire exceeds the chunk bound.
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadFileParams(path='/a', max_bytes=0)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadFileParams(path='/a', max_bytes=proto.REMOTE_FS_MAX_CHUNK_BYTES + 1)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsReadChunkParams(handle='r1', max_bytes=proto.REMOTE_FS_MAX_CHUNK_BYTES + 1)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsWriteChunkParams(handle='w1', data=b'\x00' * (proto.REMOTE_FS_MAX_CHUNK_BYTES + 1))
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsWriteFileParams(
                path='/a',
                content=b'\x00' * (proto.REMOTE_FS_MAX_CHUNK_BYTES + 1),
                overwrite=False,
                expected_digest=None,
            )
