"""Which implementation of the Qwen families' operations a backend gets."""
from ....ops.base import Ops
from .base import QwenOps
from .mlx import MlxQwenOps
from .torch import TorchQwenOps


##


QWEN_OPS_IMPLS: tuple[type[QwenOps], ...] = (TorchQwenOps, MlxQwenOps)


def qwen_ops(ops: Ops) -> QwenOps:
    """The Qwen families' operations for the backend `ops`: its kernel where it has one, else the composed ones."""

    return ops.extension(QwenOps, QWEN_OPS_IMPLS)
