import os.path

import pytest

from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionDecider
from ....permissions.types import PermissionDeniedError
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ...local import LocalFsOps
from ...permissions import FsPermissionTarget
from ..glob import GlobTool


##


class _UnderDecider(PermissionDecider):
    """Allows what is at or under `allowed`, denying everything else - and records what it was asked about."""

    def __init__(self, allowed):
        super().__init__()

        self._allowed = allowed
        self.asked = []

    async def decide(self, request):
        target = request.target
        assert isinstance(target, FsPermissionTarget)
        assert target.mode == 'r'
        self.asked.append(target.path)

        if target.path == self._allowed or target.path.startswith(self._allowed + os.sep):
            return PermissionState.ALLOW
        return PermissionState.DENY


async def _glob(tool, pattern):
    return await tool.execute_context(ToolContext(args={'pattern': pattern}))


def _listed(result):
    lines = result.content.text.splitlines()
    assert lines[0] == '<glob>'
    assert lines[-1] == '</glob>'
    return set(lines[1:-1])


@pytest.mark.asyncs('asyncio')
async def test_glob_tool():
    tool = GlobTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        fs=LocalFsOps(),
    )

    target_dir = os.path.dirname(os.path.dirname(__file__))

    for good in [
        '/**/*.py',
        '/*/*.py',
        '/tests/test_glob.py',
    ]:
        result = await _glob(tool, target_dir + good)
        assert result.error is None, result.content.text
        assert __file__ in _listed(result)

    result = await _glob(tool, 'tests/*.py')
    assert isinstance(result.error, ValueError)


@pytest.mark.asyncs('asyncio')
async def test_glob_tool_asks_about_the_root_and_then_each_match_as_resolved(tmp_path):
    root = os.path.realpath(tmp_path)
    inside = os.path.join(root, 'inside')
    outside = os.path.join(root, 'outside')
    for d in (inside, outside, os.path.join(inside, 'sub')):
        os.mkdir(d)
    for d in (inside, outside):
        with open(os.path.join(d, 'f.txt'), 'w') as f:  # noqa
            f.write('x')

    # A link from inside to a file outside is listed by its own path but asked about as what it resolves to, and a
    # dangling one is asked about as where it points.
    os.symlink(os.path.join(outside, 'f.txt'), os.path.join(inside, 'link.txt'))
    os.symlink(os.path.join(inside, 'missing.txt'), os.path.join(inside, 'dangling.txt'))

    perms = _UnderDecider(inside)
    tool = GlobTool(permissions=perms, fs=LocalFsOps())

    result = await _glob(tool, os.path.join(inside, '*'))
    assert result.error is None, result.content.text
    assert _listed(result) == {
        os.path.join(inside, 'f.txt'),
        os.path.join(inside, 'sub') + '/',
        os.path.join(inside, 'dangling.txt'),
    }
    assert result.details.num_matches == 3
    assert not result.details.has_more

    # The root first, then every match by its resolved path - the one outside refused and silently left out.
    assert perms.asked[0] == inside
    assert sorted(perms.asked[1:]) == sorted([
        os.path.join(inside, 'f.txt'),
        os.path.join(inside, 'sub'),
        os.path.join(outside, 'f.txt'),
        os.path.join(inside, 'missing.txt'),
    ])

    # Allowed where it leads, the link is listed as itself.
    result = await _glob(GlobTool(permissions=_UnderDecider(root), fs=LocalFsOps()), os.path.join(inside, '*'))
    assert result.error is None, result.content.text
    assert os.path.join(inside, 'link.txt') in _listed(result)

    # A refused root fails the glob outright, before anything is globbed.
    perms = _UnderDecider(inside)
    result = await _glob(GlobTool(permissions=perms, fs=LocalFsOps()), os.path.join(outside, '*'))
    assert isinstance(result.error, PermissionDeniedError)
    assert perms.asked == [outside]

    # As does a root which is not there.
    tool = GlobTool(permissions=_UnderDecider(inside), fs=LocalFsOps())
    result = await _glob(tool, os.path.join(inside, 'nope', '*'))
    assert isinstance(result.error, ValueError)
