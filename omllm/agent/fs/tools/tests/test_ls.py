import os.path

import pytest

from ....permissions.types import PermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ...local import LocalFsOps
from ...permissions import FsPermissionTarget
from ..ls import LsTool


##


class _RecordingDecider(PermissionDecider):
    def __init__(self):
        super().__init__()

        self.targets = []

    async def decide(self, request):
        self.targets.append(request.target)
        return PermissionState.ALLOW


@pytest.mark.asyncs('asyncio')
async def test_ls_tool_lists_directories_with_a_trailing_slash(tmp_path):
    root = os.path.realpath(tmp_path)
    os.mkdir(os.path.join(root, 'sub'))
    with open(os.path.join(root, 'f.txt'), 'w') as f:  # noqa
        f.write('x')
    os.symlink(os.path.join(root, 'sub'), os.path.join(root, 'linked'))
    os.symlink(os.path.join(root, 'missing'), os.path.join(root, 'dangling'))

    perms = _RecordingDecider()
    tool = LsTool(permissions=perms, fs=LocalFsOps())

    result = await tool.execute_context(ToolContext(args={'dir_path': root}))
    assert result.error is None, result.content.text
    assert result.content.text == '<dir>\ndangling\nf.txt\nlinked/\nsub/\n</dir>\n'

    # The directory is asked about as itself, spelled bare.
    assert perms.targets == [FsPermissionTarget(root, 'r')]
    assert perms.targets[0].path == root

    result = await tool.execute_context(ToolContext(args={'dir_path': os.path.join(root, 'f.txt')}))
    assert isinstance(result.error, ValueError)
