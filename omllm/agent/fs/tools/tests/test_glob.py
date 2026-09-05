import os.path

import pytest

from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ....types.tools import ToolEnvironment
from ...ops import LocalFsOps
from ..glob import GlobTool


@pytest.mark.asyncs('asyncio')
async def test_glob_tool():
    tool = GlobTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        fs=LocalFsOps(),
    )

    target_dir = os.path.dirname(os.path.dirname(__file__))

    env = ToolEnvironment(
        cwd=target_dir,
    )

    for good in [
        '/**/*.py',
        '/*/*.py',
        '/tests/test_glob.py',
    ]:
        result = await tool.execute_context(
            ToolContext(
                args={
                    'pattern': target_dir + good,
                },
                env=env,
            ),
        )

        assert __file__ in result.content.text.splitlines()
        assert result.error is None

    for bad in [
        '/../**/*.py',
    ]:
        result = await tool.execute_context(
            ToolContext(
                args={
                    'pattern': target_dir + bad,
                },
                env=env,
            ),
        )

        assert __file__ not in result.content.text.splitlines()
        assert result.error is not None
