import tempfile

import pytest

from ......core import procs
from .....permissions.deciders import StaticPermissionDecider
from .....permissions.types import PermissionState
from .....types.tools import ToolContext
from .....types.tools import ToolEnvironment
from ....ops import ExecOps
from ....ops import ExecResult
from ..ripgrep import RipgrepTool
from ..ripgrep import RipgrepToolParams


class _CaptureExecOps(ExecOps):
    def __init__(self):
        super().__init__()

        self.captured = None

    async def exec(self, scope, params):
        self.captured = params
        return ExecResult(rc=0, stdout=b'', stderr=b'')


@pytest.mark.asyncs('asyncio')
async def test_ripgrep_passes_sandbox_option_when_enabled():
    cap = _CaptureExecOps()
    rg = RipgrepTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        exec=cap,
        sandbox=True,
    )
    with tempfile.TemporaryDirectory() as td:
        async with procs.AsyncioProcessManager() as m:
            ctx = ToolContext(args={}, env=ToolEnvironment(cwd=td, procs=m.root))
            await rg.execute(ctx, RipgrepToolParams(args=['foo']))

    assert cap.captured is not None
    assert any(isinstance(o, procs.Sandbox) for o in cap.captured.options)


@pytest.mark.asyncs('asyncio')
async def test_ripgrep_no_sandbox_by_default():
    cap = _CaptureExecOps()
    rg = RipgrepTool(permissions=StaticPermissionDecider(PermissionState.ALLOW), exec=cap)
    with tempfile.TemporaryDirectory() as td:
        async with procs.AsyncioProcessManager() as m:
            ctx = ToolContext(args={}, env=ToolEnvironment(cwd=td, procs=m.root))
            await rg.execute(ctx, RipgrepToolParams(args=['foo']))

    assert cap.captured is not None
    assert cap.captured.options == ()
