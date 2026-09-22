# ruff: noqa: N806 N812
"""
torch backend for `Ops`.

Overrides: rms_norm (F.rms_norm), sdpa (flash/SDPA), conv1d_causal (F.conv1d), on-device quantize. `gated_delta` and
`rope` use the composed reference implementations (a Triton kernel / CUDA graphs are the next steps and slot in here
without touching model.py).
"""
import dataclasses as dc

import numpy as np
import torch
import torch.nn.functional as F

from ..ops import Ops
from ..quant import QWeight
from .torch_triton import HAVE_TRITON
from .torch_triton import gdn_step
from .torch_triton import load_tuned
from .torch_triton import qlinear


##


DTYPES = {'f32': torch.float32, 'f16': torch.float16, 'bf16': torch.bfloat16, 'i32': torch.int32}


@dc.dataclass()
class TorchQWeight:
    q: torch.Tensor  # uint8, packed as in quant.QWeight
    scale: torch.Tensor  # compute dtype
    bias: torch.Tensor
    bits: int
    group: int
    shape: tuple[int, int]

    def nbytes(self) -> int:
        return self.q.numel() + self.scale.numel() * self.scale.element_size() * 2

    def dequant(self, dtype: torch.dtype, rows: slice | torch.Tensor | None = None) -> torch.Tensor:
        q = self.q if rows is None else self.q[rows]
        s = self.scale if rows is None else self.scale[rows]
        b = self.bias if rows is None else self.bias[rows]
        if self.bits == 4:
            q = torch.stack([q & 0xF, q >> 4], dim=-1).reshape(q.shape[0], -1)
        n = q.shape[0]
        x = q.reshape(n, -1, self.group).to(dtype)
        x = x * s[..., None].to(dtype) + b[..., None].to(dtype)
        return x.reshape(n, self.shape[1])

    def linear(self, x: torch.Tensor, chunk_rows: int = 16384) -> torch.Tensor:
        out = self.shape[0]
        if out <= chunk_rows:
            return F.linear(x, self.dequant(x.dtype))
        return torch.cat(
            [F.linear(x, self.dequant(x.dtype, slice(i, i + chunk_rows))) for i in range(0, out, chunk_rows)],
            dim=-1,
        )


class CudaGraphStep:
    """
    CUDA-graph capture of a flat-tuple step function.

    The first call runs the function twice on a side stream (cuBLAS/cuDNN lazy init must not happen inside a
    capture), then captures it against the argument tensors it was given. Those tensors become the graph's
    static inputs: later calls `copy_` new arguments into them (skipping arguments that already *are* the static
    tensors, which is what `kv_write`'s in-place return gives us for the KV buffers), replay, and hand back the
    graph's output tensors. Outputs are overwritten by the next replay, so a caller that keeps state must feed the
    outputs straight back in -- the copy into the static inputs is what carries it forward.
    """

    def __init__(self, fn, use_graph: bool = True) -> None:
        self.fn = fn
        self.use_graph = use_graph  # False: same static-input protocol, no graph (testable on CPU)
        self.graph: torch.cuda.CUDAGraph | None = None
        self.static_in: list[torch.Tensor] = []
        self.static_out: tuple[torch.Tensor, ...] = ()

    def __call__(self, *args):
        if not self.static_in:
            self.static_in = list(args)
            if not self.use_graph:
                return tuple(self.fn(*self.static_in))
            s = torch.cuda.Stream()
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                for _ in range(2):
                    self.fn(*self.static_in)
            torch.cuda.current_stream().wait_stream(s)
            self.graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(self.graph):
                self.static_out = tuple(self.fn(*self.static_in))
            self.graph.replay()  # capture only records; run it once so this call's outputs are real
            return self.static_out
        for dst, src in zip(self.static_in, args):
            if src is not dst:
                dst.copy_(src)
        if not self.use_graph:
            return tuple(self.fn(*self.static_in))
        self.graph.replay()
        return self.static_out


class TorchOps(Ops):
    name = 'torch'

    def __init__(
            self,
            device: str | torch.device = 'cpu',
            capture_mode: str = 'auto',
            triton: bool | None = None,
            triton_max_m: int = 32,
            triton_block_n: int | None = None,
            triton_tuned: str | None = None,
            compile: bool = False,  # noqa
    ) -> None:
        super().__init__()

        self.device = torch.device(device)
        self.name = f'torch:{self.device}'
        self.capture_mode = capture_mode  # 'auto' (graph on cuda, plain elsewhere) | 'graph' | 'static' | 'plain'
        # run the step through torch.compile (inductor fuses the elementwise / norm / cast glue between the big
        # kernels into a few generated ones) before it is graph-captured; slow first call, cached on disk after
        self.compile = compile
        # fused int4/int8 GEMV for quantized weights when the token count is small (decode / verify); prefill
        # stays on dequant + cuBLAS. None: on when cuda and triton import. True on CPU needs TRITON_INTERPRET=1.
        self.triton = (self.device.type == 'cuda' and HAVE_TRITON) if triton is None else (triton and HAVE_TRITON)
        self.triton_max_m = triton_max_m
        self.triton_block_n = triton_block_n
        if triton_tuned and HAVE_TRITON:
            load_tuned(triton_tuned)  # per-shape GEMV configs written by entrypoints/tune
        self.gdn_block_dv = 32  # fused DeltaNet step: value-dim slice per program (state tile [dk, block_dv] f32)
        self.gdn_num_warps = 8

    def dtype(self, name):
        return DTYPES[name]

    def array(self, a, dtype=None):
        a = np.ascontiguousarray(a)
        if not a.flags.writeable:  # memmap-backed (gguf / safetensors) arrays: torch wants ownership
            a = a.copy()
        t = torch.from_numpy(a)
        if dtype is not None:
            t = t.to(dtype)
        return t.to(self.device)

    def numpy(self, x):
        return x.detach().float().cpu().numpy() if x.is_floating_point() else x.detach().cpu().numpy()

    def cast(self, x, dtype):
        return x.to(dtype)

    def copy(self, x):
        return x.clone()

    def zeros(self, shape, dtype):
        return torch.zeros(shape, dtype=dtype, device=self.device)

    def eval(self, *xs):
        if self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)
        elif self.device.type == 'mps':
            torch.mps.synchronize()

    def nbytes(self, w):
        if isinstance(w, TorchQWeight):
            return w.nbytes()
        return w.numel() * w.element_size()

    def reshape(self, x, shape):
        return x.reshape(shape)

    def transpose(self, x, axes):
        return x.permute(axes)

    def concat(self, xs, axis):
        return torch.cat(list(xs), dim=axis)

    def stack(self, xs, axis):
        return torch.stack(list(xs), dim=axis)

    def split(self, x, sizes, axis):
        return list(torch.split(x, list(sizes), dim=axis))

    def repeat(self, x, n, axis):
        return x.repeat_interleave(n, dim=axis)

    def arange(self, n):
        return torch.arange(n, dtype=torch.int32, device=self.device)

    def scalar(self, v):
        return torch.tensor(v, dtype=torch.int32, device=self.device)

    def kv_write(self, buf, pos, x):
        # in place, so a captured graph keeps writing into the same storage
        buf.index_copy_(2, pos.reshape(1).to(torch.int64), x.to(buf.dtype))
        return buf

    def cumsum(self, x, axis):
        return torch.cumsum(x, dim=axis)

    def exp(self, x):
        return torch.exp(x)

    def rsqrt(self, x):
        return torch.rsqrt(x)

    def sum(self, x, axis, keepdims=False):
        return x.sum(dim=axis, keepdim=keepdims)

    def mean(self, x, axis, keepdims=False):
        return x.mean(dim=axis, keepdim=keepdims)

    def sigmoid(self, x):
        return torch.sigmoid(x)

    def softplus(self, x):
        return F.softplus(x)

    def silu(self, x):
        return F.silu(x)

    def softmax(self, x, axis):
        return torch.softmax(x, dim=axis)

    def log(self, x):
        return torch.log(x)

    def argmax(self, x, axis):
        return torch.argmax(x, dim=axis).to(torch.int32)

    def amax(self, x, axis, keepdims=False):
        return torch.amax(x, dim=axis, keepdim=keepdims)

    def topk(self, x, k):
        v, i = torch.topk(x, k, dim=-1, sorted=True)
        return v, i.to(torch.int32)

    def seed(self, seed):
        self._gen = torch.Generator(device=self.device).manual_seed(seed)

    def random_uniform(self, shape):
        if not hasattr(self, '_gen'):
            self.seed(0)
        return torch.rand(shape, dtype=torch.float32, device=self.device, generator=self._gen)

    def index_add(self, x, idx, vals):
        return x.index_add(0, idx.to(torch.int64), vals.to(x.dtype))

    # weights

    def weight(self, w, dtype):
        return self.array(w, dtype)

    def qweight(self, qw: QWeight, dtype):
        return TorchQWeight(
            self.array(qw.q),
            self.array(qw.scale, dtype),
            self.array(qw.bias, dtype),
            qw.bits,
            qw.group,
            qw.shape,
        )

    def quantize(
            self,
            w,
            bits,
            group,
            dtype,
    ):
        """On-device version of quant.quantize (same layout, same numerics up to rounding)."""

        out, inn = w.shape
        if inn % group:
            raise ValueError(f'in_features {inn} not a multiple of group {group}')
        qmax = (1 << bits) - 1
        g = self.array(w, torch.float32).reshape(out, inn // group, group)
        lo = g.amin(-1)
        hi = g.amax(-1)
        scale = (hi - lo) / qmax
        scale = torch.where(scale == 0, torch.ones_like(scale), scale)
        q = torch.round((g - lo[..., None]) / scale[..., None]).clamp_(0, qmax).to(torch.uint8).reshape(out, inn)
        if bits == 4:
            q = q[:, 0::2] | (q[:, 1::2] << 4)
        return TorchQWeight(q.contiguous(), scale.to(dtype), lo.to(dtype), bits, group, (out, inn))

    def export_qweight(self, w):
        if not isinstance(w, TorchQWeight):
            raise NotImplementedError
        return QWeight(
            w.q.cpu().numpy(),
            w.scale.float().cpu().numpy(),
            w.bias.float().cpu().numpy(),
            w.bits,
            w.group,
            w.shape,
        )

    def gdn_step(self, q, k, v, a, b, A, dt_bias, state, all_states, eps=1e-6):
        if self.triton:
            return gdn_step(q, k, v, a, b, A, dt_bias, state, all_states, eps, self.gdn_block_dv, self.gdn_num_warps)
        return super().gdn_step(q, k, v, a, b, A, dt_bias, state, all_states, eps)

    def linear(self, x, w):
        if isinstance(w, TorchQWeight):
            if self.triton and x.numel() // x.shape[-1] <= self.triton_max_m:
                return qlinear(x, w.q, w.scale, w.bias, w.bits, w.group, w.shape, block_n=self.triton_block_n)
            return w.linear(x)
        return F.linear(x, w)

    def embedding(self, ids, w, dtype):
        if isinstance(w, TorchQWeight):
            return w.dequant(dtype, ids.reshape(-1)).reshape(*ids.shape, w.shape[1])
        return F.embedding(ids, w).to(dtype)

    # fused overrides

    def rms_norm(
            self,
            x,
            w,
            eps,
    ):
        xf = x.float()
        return F.rms_norm(xf, (xf.shape[-1],), weight=w.float(), eps=eps).to(x.dtype)

    def sdpa(
            self,
            q,
            k,
            v,
            scale,
            past,
    ):
        B, H, T, D = q.shape
        KV, L = k.shape[1], k.shape[2]
        if KV != H:
            k = k.repeat_interleave(H // KV, dim=1)
            v = v.repeat_interleave(H // KV, dim=1)
        if T == 1:
            return F.scaled_dot_product_attention(q, k, v, scale=scale)
        mask = torch.ones(T, L, dtype=torch.bool, device=q.device).tril(diagonal=past)
        return F.scaled_dot_product_attention(q, k, v, attn_mask=mask, scale=scale)

    def conv1d_causal(self, x, w):
        return F.conv1d(x, w[:, None, :], groups=w.shape[0])

    def capture(self, fn):
        mode = self.capture_mode
        if mode == 'auto':
            mode = 'graph' if self.device.type == 'cuda' else 'plain'
        if self.compile:
            fn = torch.compile(fn, dynamic=False)
        if mode == 'plain':
            return fn
        return CudaGraphStep(fn, use_graph=(mode == 'graph'))

    def rope(
            self,
            x,
            offset,
            dims,
            theta,
    ):
        # composed reference, with the tables cached per (offset, T) since decode hits the same shapes repeatedly
        key = (offset, x.shape[2], dims, theta, x.dtype)
        tabs = self.__dict__.setdefault('_rope_cache', {})
        if key not in tabs:
            if len(tabs) > 256:
                tabs.clear()
            cos_np, sin_np = self.rope_tables(offset, x.shape[2], dims, theta)
            tabs[key] = (self.array(cos_np, x.dtype), self.array(sin_np, x.dtype))
        cos, sin = tabs[key]
        xr, xp = x[..., :dims], x[..., dims:]
        half = dims // 2
        rot = torch.cat([-xr[..., half:], xr[..., :half]], dim=-1)
        return torch.cat([xr * cos[None, None] + rot * sin[None, None], xp], dim=-1)
