import os.path
import tempfile

import pytest

from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ....types.tools import ToolEnvironment
from ...ops import LocalFsOps
from ..details import EditToolResultDetails
from ..details import ReadToolResultDetails
from ..details import WriteToolResultDetails
from ..edit import EditTool
from ..read import ReadTool
from ..write import WriteTool


##


async def _call(tool, cwd, args):
    result = await tool.execute_context(
        ToolContext(args=args, env=ToolEnvironment(cwd=cwd)),
    )
    assert result.error is None, result.content.text
    return result


@pytest.mark.asyncs('asyncio')
async def test_write_edit_and_read_report_details():
    perms = StaticPermissionDecider(PermissionState.ALLOW)
    fs = LocalFsOps()

    with tempfile.TemporaryDirectory() as td:
        td = os.path.realpath(td)
        path = os.path.join(td, 'f.txt')

        w = await _call(WriteTool(permissions=perms, fs=fs), td, {'file_path': path, 'contents': 'a\nb\n'})
        assert isinstance(w.details, WriteToolResultDetails)
        assert w.details.path == path
        assert w.details.created
        assert w.details.num_bytes == 4

        w2 = await _call(
            WriteTool(permissions=perms, fs=fs),
            td,
            {'file_path': path, 'contents': 'a\nb\n', 'overwrite': True},
        )
        assert isinstance(w2.details, WriteToolResultDetails)
        assert not w2.details.created

        e = await _call(
            EditTool(permissions=perms, fs=fs),
            td,
            {'file_path': path, 'old_string': 'b\n', 'new_string': 'c\n'},
        )
        assert isinstance(e.details, EditToolResultDetails)
        assert e.details.path == path
        assert '-b' in e.details.diff and '+c' in e.details.diff

        r = await _call(ReadTool(permissions=perms, fs=fs), td, {'file_path': path, 'num_lines': 1})
        assert isinstance(r.details, ReadToolResultDetails)
        assert r.details.path == path
        assert r.details.line_offset == 0
        assert r.details.num_lines == 1
        assert r.details.has_more

        r2 = await _call(ReadTool(permissions=perms, fs=fs), td, {'file_path': path})
        assert isinstance(r2.details, ReadToolResultDetails)
        assert r2.details.num_lines == 2
        assert not r2.details.has_more
