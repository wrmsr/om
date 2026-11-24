"""
Inkling 2's operations on the torch backend: `Inkling2Ops` with a Triton kernel (torchkernels.py) wherever the backend
has its fused kernels on and an operation's arguments are of the shape its kernel takes, and the composed definition
otherwise.
"""
import typing as ta

from omcore import check
from omcore import lang

from ....backends.torch import TorchOps
from ....backends.torch_fused import is_pow2
from ....ops.base import Ops
from . import torchkernels
from .base import Inkling2Ops


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')


##


class TorchInkling2Ops(Inkling2Ops):
    def __init__(self, ops: Ops) -> None:
        super().__init__(ops)

        self._torch = check.isinstance(ops, TorchOps)

        if self._torch.fused:
            torchkernels.ensure_inkling2_kernels()  # jit now: the wrappers must find real JITFunctions when traced

    @classmethod
    def serves(cls, ops: Ops) -> bool:
        return isinstance(ops, TorchOps)

    def unit_rms(self, x, eps):
        xf = x.float()
        return torch.nn.functional.rms_norm(xf, (xf.shape[-1],), eps=eps)

    def rms_norm_to(self, x, w, eps, dtype):
        if not (self._torch.fused and x.is_cuda and w.dim() == 1 and x.shape[0] == 1 and x.dim() == 3):
            return super().rms_norm_to(x, w, eps, dtype)
        return torchkernels.rms_norm_to(x, w, eps, dtype)

    def sum_to(self, a, b, dtype):
        if not (self._torch.fused and a.is_cuda and a.shape == b.shape and a.is_contiguous() and b.is_contiguous()):
            return super().sum_to(a, b, dtype)
        return torchkernels.sum_to(a, b, dtype)

    def sigmoid_gated(self, x, g, dtype):
        if not (self._torch.fused and x.is_cuda and x.shape == g.shape and x.is_contiguous() and g.is_contiguous()):
            return super().sigmoid_gated(x, g, dtype)
        return torchkernels.sigmoid_gated(x, g, dtype)

    def l2_clip(self, x, threshold, *, scale=None, after=None):
        if not (
                self._torch.fused and
                x.is_cuda and
                x.dim() == 4 and
                x.shape[0] == 1 and
                is_pow2(x.shape[-1]) and
                x.is_contiguous() and
                (scale is None or (scale.dtype == x.dtype and tuple(scale.shape) == tuple(x.shape[2:])))
        ):
            return super().l2_clip(x, threshold, scale=scale, after=after)
        return torchkernels.l2_clip(x, threshold, scale, after)

    def depth_mix(self, queries, sources, *, raw=0, eps=0.):
        if not (
                self._torch.fused and
                queries.is_cuda and
                len(sources) <= torchkernels.DEPTH_MIX_MAX_SOURCES and
                all(s.shape[0] == 1 and s.is_contiguous() for s in sources)
        ):
            return super().depth_mix(queries, sources, raw=raw, eps=eps)
        return torchkernels.depth_mix(queries, sources, raw, eps)

    def bottleneck_blend(self, x, m, down, forget, gain, *, eps, dtype):
        if not (self._torch.fused and x.is_cuda and isinstance(down, torch.Tensor) and is_pow2(down.shape[0])):
            return super().bottleneck_blend(x, m, down, forget, gain, eps=eps, dtype=dtype)
        return torchkernels.bottleneck_blend(x, m, down, forget, gain, eps)

    def sigmoid_route(self, logits, bias, k, *, total):
        if not (self._torch.fused and logits.is_cuda and logits.dim() == 2 and logits.is_contiguous()):
            return super().sigmoid_route(logits, bias, k, total=total)
        return torchkernels.sigmoid_route(logits, bias, k, total)

    def capped_gate(self, h, *, gate_cap, up_cap):
        if not (self._torch.fused and h.is_cuda and h.dim() == 2 and h.is_contiguous()):
            return super().capped_gate(h, gate_cap=gate_cap, up_cap=up_cap)
        return torchkernels.capped_gate(h, gate_cap, up_cap)

    def weighted_rows(self, y, w, dtype):
        if not (self._torch.fused and y.is_cuda and y.is_contiguous()):
            return super().weighted_rows(y, w, dtype)
        return torchkernels.weighted_rows(y, w, dtype)
