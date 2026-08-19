import sys

from ..types.options import Sandbox
from .bwrap import BwrapSandbox
from .policy import SandboxPolicy


##


def platform_sandbox(policy: SandboxPolicy) -> Sandbox:
    """The default sandbox for the current platform: sandbox-exec on macOS, bubblewrap elsewhere."""

    if getattr(sys, 'platform') == 'darwin':
        from .seatbelt import SeatbeltSandbox  # noqa
        return SeatbeltSandbox(policy=policy)

    return BwrapSandbox(policy=policy)
