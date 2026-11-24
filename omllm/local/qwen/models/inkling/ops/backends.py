"""Which implementation of Inkling 2's operations a backend gets."""
from ....ops.base import Ops
from .base import Inkling2Ops
from .torch import TorchInkling2Ops


##


def inkling2_ops(ops: Ops) -> Inkling2Ops:
    """Inkling 2's operations for the backend `ops`: its kernels where it has them, else the composed definitions."""

    return ops.extension(Inkling2Ops, (TorchInkling2Ops,))
