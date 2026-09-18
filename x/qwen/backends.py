"""Backend selection for the CLIs."""
import platform

from .ops import NumpyOps
from .ops import Ops


##


BACKENDS = (
    'torch',
    'mlx',
    'numpy',
)


def default_backend() -> str:
    if platform.system() == 'Darwin':
        try:
            import mlx.core  # noqa

            return 'mlx'

        except ImportError:
            pass

    return 'torch'


def make_ops(backend: str | None = None, device: str | None = None) -> Ops:
    backend = backend or default_backend()

    if backend == 'torch':
        import torch

        from .torch_ops import TorchOps

        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
            elif getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'
        return TorchOps(device)

    if backend == 'mlx':
        from .mlx_ops import MlxOps

        return MlxOps()

    if backend == 'numpy':
        return NumpyOps()

    raise ValueError(f'unknown backend {backend!r} (want one of {BACKENDS})')


def default_dtype(ops: Ops) -> str:
    """bf16 on accelerators, f32 on cpu (bf16 matmuls on CPU are slow in every backend)."""

    name = ops.name
    if name.startswith(('torch:cpu', 'numpy', 'mlx:Device(cpu')):
        return 'f32'
    return 'bf16'
