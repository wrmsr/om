# ruff: noqa: UP006 UP007 UP045
import typing as ta
import unittest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from .. import protocol as proto


def _entry(**kwargs: ta.Any) -> proto.RemoteFsEntry:
    base: ta.Dict[str, ta.Any] = dict(
        path='/a',
        resolved_path='/a',
        is_dir=False,
        is_file=True,
        is_symlink=False,
        mode=0o100644,
        ino=1,
        dev=2,
        nlink=1,
        uid=3,
        gid=4,
        size=3,
        atime_ns=5,
        mtime_ns=6,
        ctime_ns=7,
        blksize=4096,
        blocks=8,
        rdev=0,
        flags=None,
        gen=None,
        birthtime_ns=None,
    )
    base.update(kwargs)
    return proto.RemoteFsEntry(**base)


class TestRemoteFsProtocol(unittest.TestCase):
    def _roundtrip(self, obj: ta.Any) -> None:
        self.assertEqual(unmarshal_obj(marshal_obj(obj), type(obj)), obj)

    def test_roundtrips(self) -> None:
        self._roundtrip(proto.RemoteFsPathParams('/a/b'))
        self._roundtrip(_entry())
        self._roundtrip(_entry(flags=1, gen=2, birthtime_ns=3))
        self._roundtrip(proto.RemoteFsGlobParams(pattern='*.py', max_results=None))
        self._roundtrip(proto.RemoteFsGlobResult(
            entries=[_entry(path='/a/b', resolved_path='/c/b', is_dir=True, is_file=False)],
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
            _entry(size=-1)
        with self.assertRaises(Exception):  # noqa
            proto.RemoteFsGlobParams(pattern='*', max_results=-1)

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
