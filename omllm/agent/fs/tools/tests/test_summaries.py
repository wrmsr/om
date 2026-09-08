import pytest

from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ...ops import LocalFsOps
from ..edit import EditTool
from ..glob import GlobTool
from ..ls import LsTool
from ..read import ReadTool
from ..write import WriteTool


##


@pytest.mark.parametrize(
    ('tool_cls', 'args', 'expected'),
    [
        (GlobTool, {'pattern': '/workspace/**/*.py'}, '/workspace/**/*.py'),
        (ReadTool, {'file_path': '/workspace/read.py'}, '/workspace/read.py'),
        (LsTool, {'dir_path': '/workspace'}, '/workspace'),
        (
            EditTool,
            {'file_path': '/workspace/edit.py', 'old_string': 'old', 'new_string': 'new'},
            '/workspace/edit.py',
        ),
        (WriteTool, {'file_path': '/workspace/write.py', 'contents': 'text'}, '/workspace/write.py'),
    ],
)
def test_fs_tool_call_summaries(tool_cls, args, expected):
    tool = tool_cls(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        fs=LocalFsOps(),
    ).tool()
    context = ToolContext(tool=tool, args=args)

    assert tool.summarizer is not None
    assert tool.summarizer(context) == expected
