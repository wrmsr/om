import sys

from ..types.options import Sandbox
from .bwrap import BwrapSandbox
from .policy import SandboxPolicy


##


def platform_sandbox(policy: SandboxPolicy) -> Sandbox:
    """The default sandbox for the current platform: sandbox-exec on macOS, bubblewrap elsewhere."""

    if sys.platform == 'darwin':
        from .sandboxexec import SandboxExecSandbox  # noqa
        return SandboxExecSandbox(policy=policy)
    return BwrapSandbox(policy=policy)
