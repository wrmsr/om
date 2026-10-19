from ...permissions.types import PermissionMatchContext
from ..permissions import FsPermissionTarget
from ..permissions import GlobFsPermissionMatcher


def _matches(glob, path, mode='r', **kwargs):
    return GlobFsPermissionMatcher(glob, **kwargs).match(PermissionMatchContext(FsPermissionTarget(path, mode)))


def test_trailing_separators_are_dropped_on_construction():
    assert FsPermissionTarget('/a/b/', 'r').path == '/a/b'
    assert FsPermissionTarget('/a/b/', 'r') == FsPermissionTarget('/a/b', 'r')
    assert FsPermissionTarget('/', 'r').path == '/'
    assert FsPermissionTarget('//', 'r').path == '/'

    assert GlobFsPermissionMatcher('/a/**/').glob == '/a/**'
    assert GlobFsPermissionMatcher('/a/**/') == GlobFsPermissionMatcher('/a/**')
    assert GlobFsPermissionMatcher('/').glob == '/'


def test_a_directory_is_the_same_target_however_it_is_spelled():
    for path in ('/cwd/sub', '/cwd/sub/'):
        assert _matches('/cwd/*', path)
        assert _matches('/cwd/**', path)
        assert _matches('/cwd/sub', path)
        assert _matches('/cwd/sub/', path)

        assert not _matches('/cwd/sub/*', path)
        assert not _matches('/cwd/sub/**', path, modes=['w'])
        assert not _matches('/other/**', path)

    # A tree grant covers its own root, a single level one does not.
    assert _matches('/cwd/**', '/cwd')
    assert _matches('/cwd/**', '/cwd/')
    assert not _matches('/cwd/*', '/cwd')

    assert _matches('/cwd/**', '/cwd/sub/f.py', 'w')
    assert not _matches('/cwd/**', '/cwd/sub/f.py', 'w', modes=['r'])
