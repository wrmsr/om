# ruff: noqa: N803 N806 N812
"""Backend selection for the CLIs."""
import platform

from omcore import lang

from ..ops import NumpyOps
from ..ops import Ops


##


BACKENDS = (
    'torch',
    'mlx',
    'tinygrad',
    'numpy',
)


def available_backends() -> list[str]:
    """The backends whose library is installed (found, not imported: every backend module imports lazily)."""

    out = []
    for name, lib in (('torch', 'torch'), ('mlx', 'mlx'), ('tinygrad', 'tinygrad')):
        if lang.can_import(lib):
            out.append(name)
    out.append('numpy')
    return out


def default_backend() -> str:
    if platform.system() == 'Darwin' and lang.can_import('mlx'):
        return 'mlx'
    return 'torch'


def make_ops(backend: str | None = None, device: str | None = None) -> Ops:
    backend = backend or default_backend()

    if backend == 'torch':
        import torch

        from .torch import TorchOps

        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
            elif getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'
        return TorchOps(device)

    if backend == 'mlx':
        from .mlx import MlxOps

        return MlxOps()

    if backend == 'tinygrad':
        from .tinygrad import TinygradOps

        return TinygradOps(device)

    if backend == 'numpy':
        return NumpyOps()

    raise ValueError(f'unknown backend {backend!r} (want one of {BACKENDS})')


def default_dtype(ops: Ops) -> str:
    """bf16 on accelerators, f32 on cpu (bf16 matmuls on CPU are slow in every backend)."""

    name = ops.name

    if (
        name.startswith((
            'torch:cpu',
            'numpy',
            'mlx:Device(cpu',
        )) or
        name in (
            'tinygrad:CPU',
            'tinygrad:LLVM',
            'tinygrad:PYTHON',
        )
    ):
        return 'f32'

    return 'bf16'
