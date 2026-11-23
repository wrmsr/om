# ruff: noqa: N802 N803 N806 N812
"""
torch backend for `Ops`.

Overrides: rms_norm (F.rms_norm), sdpa (flash/SDPA), conv1d_causal (F.conv1d), on-device quantize. `gated_delta` and
`rope` use the composed reference implementations (a Triton kernel / CUDA graphs are the next steps and slot in here
without touching model.py).
"""
import pathlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.logs import all as logs

from ..ops.base import Ops
from ..ops.microscaled import MicroscaledWeight
from ..ops.microscaled import e2m1_pair_values
from ..ops.microscaled import e2m1_values
from ..ops.microscaled import e4m3_values
from ..ops.microscaled import pow2_scale_values
from ..ops.quant import SEARCH_SHRINKS
from ..ops.quant import QWeight
from ..ops.quant import quantize as quantize_np
from .torch_fused import DENSE_ROWS_MAX_K
from .torch_fused import DEPTH_MIX_MAX_SOURCES
from .torch_fused import bottleneck_blend
from .torch_fused import capped_gate
from .torch_fused import dense_gemv
from .torch_fused import dense_rows
from .torch_fused import dense_rows_pays
from .torch_fused import depth_mix
from .torch_fused import ensure_fused_kernels
from .torch_fused import is_pow2
from .torch_fused import kv_append
from .torch_fused import l2_clip
from .torch_fused import rms_norm_to
from .torch_fused import sdpa_window_rel
from .torch_fused import short_conv
from .torch_fused import sigmoid_gated
from .torch_fused import sigmoid_route
from .torch_fused import sum_to
from .torch_fused import weighted_rows
from .torch_triton import HAVE_TRITON
from .torch_triton import GemvTable
from .torch_triton import attn_decode
from .torch_triton import attn_decode_partials
from .torch_triton import attn_prefill
from .torch_triton import dequantize
from .torch_triton import ensure_kernels
from .torch_triton import gdn_step
from .torch_triton import mdequantize
from .torch_triton import mgemv_experts
from .torch_triton import qgemv_experts
from .torch_triton import qlinear
from .torch_triton import resolve_launch


if ta.TYPE_CHECKING:
    import numpy as np  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import torch.nn.functional as F  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    np = lang.proxy_import('numpy')
    torch = lang.proxy_import('torch')
    F = lang.proxy_import('torch.nn.functional')


##


log = logs.get_module_logger(globals())


def dtypes() -> dict[str, ta.Any]:
    """Compute dtype names -> torch dtypes (a function: torch is imported lazily)."""

    return {
        'f32': torch.float32,
        'f16': torch.float16,
        'bf16': torch.bfloat16,
        'i32': torch.int32,
        'i64': torch.int64,
    }


@dc.dataclass()
class TorchQWeight:
    q: torch.Tensor  # uint8, packed as in quant.QWeight
    scale: torch.Tensor  # compute dtype
    bias: torch.Tensor
    bits: int
    group: int
    shape: tuple[int, int]

    # the GEMV launch resolved for this weight on its first (eager) call: see torch_triton.resolve_launch
    launch: ta.Any = None

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


@dc.dataclass()
class TorchQExperts:
    """
    Quantized weights of E experts stacked (Ops.expert_weights): codes [E, N, K / per byte], scale / bias [E, N, K /
    group], each expert an N x K TorchQWeight's layout. `expert_linear` runs it through the expert GEMV kernel.
    """

    q: torch.Tensor
    scale: torch.Tensor
    bias: torch.Tensor
    bits: int
    group: int
    shape: tuple[int, int]  # one expert's (N, K)

    def nbytes(self) -> int:
        return self.q.numel() + self.scale.numel() * self.scale.element_size() * 2

    def dequant(self, dtype: torch.dtype, experts: torch.Tensor) -> torch.Tensor:
        """The given experts' weights, [R, N, K] in `dtype`."""

        q = self.q[experts]
        if self.bits == 4:
            q = torch.stack([q & 0xF, q >> 4], dim=-1).reshape(*q.shape[:-1], -1)
        r, n, _ = q.shape
        x = q.reshape(r, n, -1, self.group).to(dtype)
        x = x * self.scale[experts][..., None].to(dtype) + self.bias[experts][..., None].to(dtype)
        return x.reshape(r, n, -1)


@dc.dataclass()
class TorchMicroscaledExperts:
    """
    E experts stored in a microscaled float format (ops/microscaled.py), as the checkpoint has them: `codes` uint8
    [E, N, K / 2] (nvfp4: two 4-bit codes a byte) or [E, N, K] (mxfp8), `scales` uint8 [E, N, K / block], `outer`
    float32 [E] (nvfp4). The tables turn a byte into its value(s), float32: `code_values` [256, 2] or [256, 1] and
    `scale_values` [256, 1] for the composed decode (an embedding lookup per byte); `code_table` [16] per 4-bit code
    (nvfp4) or [256], and `scale_table` [256], flat, for the kernels. `expert_linear` decodes the experts a step
    reads.
    """

    fmt: str
    codes: torch.Tensor
    scales: torch.Tensor
    outer: torch.Tensor | None
    code_values: torch.Tensor
    scale_values: torch.Tensor
    code_table: torch.Tensor
    scale_table: torch.Tensor
    block: int
    shape: tuple[int, int]  # one expert's (N, K)

    def nbytes(self) -> int:
        return self.codes.numel() + self.scales.numel() + (self.outer.numel() * 4 if self.outer is not None else 0)

    def dequant(self, dtype: torch.dtype, experts: torch.Tensor) -> torch.Tensor:
        """The given experts' weights, [R, N, K] in `dtype`: decoded in float32 (the products exact), then rounded."""

        n, k = self.shape
        experts = experts.to(torch.int64)
        r = experts.shape[0]

        x = F.embedding(self.codes[experts].to(torch.int32), self.code_values)  # [R, N, K / per byte, per byte]
        s = F.embedding(self.scales[experts].to(torch.int32), self.scale_values)  # [R, N, K / block, 1]
        if self.outer is not None:
            s = s * self.outer[experts][:, None, None, None]

        return (x.reshape(r, n, k // self.block, self.block) * s).reshape(r, n, k).to(dtype)


class CudaGraphStep:
    """
    CUDA-graph capture of a flat-tuple step function.

    The first call runs the function twice on a side stream (cuBLAS/cuDNN lazy init must not happen inside a capture),
    then captures it against the argument tensors it was given. Those tensors become the graph's static inputs: later
    calls `copy_` new arguments into them (skipping arguments that already *are* the static tensors, which is what
    `kv_write`'s in-place return gives us for the KV buffers), replay, and hand back the graph's output tensors. Outputs
    are overwritten by the next replay, so a caller that keeps state must feed the outputs straight back in -- the copy
    into the static inputs is what carries it forward.

    With `carry = (outputs_from, inputs_from)` -- the outputs from the one index on are the next call's arguments from
    the other on -- that copy is part of the graph: it ends by writing those outputs into the static inputs they
    belong to, and hands *those* back, which the next call then finds are already its inputs. A plain decode step on
    the 27B has 96 such arrays (the DeltaNet layers' states, 150 MiB): copied in by the host at the next launch they
    were 0.6 ms of launches a token, with nothing for the GPU to do meanwhile.
    """

    def __init__(self, fn, use_graph: bool = True, carry: tuple[int, int] | None = None) -> None:
        super().__init__()

        self.fn = fn
        self.use_graph = use_graph  # False: same static-input protocol, no graph (testable on CPU)
        self.carry = carry
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
                out = tuple(self.fn(*self.static_in))
                if self.carry is not None:
                    outputs_from, inputs_from = self.carry
                    state = self.static_in[inputs_from:]
                    if len(out) - outputs_from != len(state):
                        raise ValueError('carried outputs and inputs differ in number')
                    for dst, src in zip(state, out[outputs_from:]):
                        if src is not dst:
                            dst.copy_(src)
                    out = (*out[:outputs_from], *state)
                self.static_out = out
            self.graph.replay()  # capture only records; run it once so this call's outputs are real
            return self.static_out
        for dst, src in zip(self.static_in, args):
            if src is not dst:
                dst.copy_(src)
        if not self.use_graph:
            return tuple(self.fn(*self.static_in))
        self.graph.replay()  # type: ignore[union-attr]
        return self.static_out


def load_compile_cache(path: str) -> bool:
    """Load torch.compiler cache artifacts saved by `save_compile_cache` (torch >= 2.6). Best effort."""

    p = pathlib.Path(path).expanduser()
    if not p.exists() or not hasattr(torch.compiler, 'load_cache_artifacts'):
        return False
    try:
        torch.compiler.load_cache_artifacts(p.read_bytes())
        return True
    except Exception as e:  # noqa
        log.warning('could not load compile cache %s: %s', p, e)
        return False


def save_compile_cache(path: str) -> bool:
    """Persist the current process's torch.compiler artifacts (call after the steps have compiled)."""

    if not hasattr(torch.compiler, 'save_cache_artifacts'):
        return False
    try:
        got = torch.compiler.save_cache_artifacts()
    except Exception as e:  # noqa
        log.warning('could not save compile cache: %s', e)
        return False
    if not got:
        return False
    blob, _info = got
    p = pathlib.Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(blob)
    return True


def _refit_torch(g, q, s0, b0):
    """Least-squares (scale, bias) per group for fixed codes q (torch twin of quant._refit)."""

    n = q.shape[-1]
    sq = q.sum(-1)
    sqq = (q * q).sum(-1)
    sx = g.sum(-1)
    sqx = (q * g).sum(-1)
    den = n * sqq - sq * sq
    ok = den > 1e-6
    s = torch.where(ok, (n * sqx - sq * sx) / torch.where(ok, den, torch.ones_like(den)), s0)
    b = torch.where(ok, (sx - s * sq) / n, b0)
    err = ((g - (q * s[..., None] + b[..., None])) ** 2).sum(-1)
    return s, b, err


class _DeferredCompile:
    """
    `torch.compile(fn)` that runs `fn` once eagerly first. The eager run is where the Triton wrappers resolve their
    launch configurations (the shared-memory ladders in torch_triton, try/except and all) and populate their caches; by
    the time dynamo traces, every wrapper takes its straight-line path and each `kernel[grid]` launch is a plain
    user-defined Triton kernel to it -- no graph breaks, no per-shape retracing of Triton's launcher. CudaGraphStep's
    warm-up runs make the first (eager) and second (compiling) calls before capture.
    """

    def __init__(self, fn):
        super().__init__()

        self.fn = fn
        self.compiled = None

    def __call__(self, *args):
        if self.compiled is None:
            out = self.fn(*args)
            self.compiled = torch.compile(self.fn, dynamic=False)
            return out
        return self.compiled(*args)


class TorchOps(Ops):
    name = 'torch'

    def __init__(
            self,
            device: str | torch.device = 'cpu',
            capture_mode: str = 'auto',
            triton: bool | None = None,
            triton_max_m: int = 32,
            triton_block_n: int | None = None,
            gemv_tuned: GemvTable | None = None,
            compile: bool = False,  # noqa
            compile_cache: str | None = None,
            kv_dtype: str = 'bf16',
            fused: bool | None = None,
    ) -> None:
        super().__init__()

        self.device = torch.device(device)
        self.name = f'torch:{self.device}'
        self.capture_mode = capture_mode  # 'auto' (graph on cuda, plain elsewhere) | 'graph' | 'static' | 'plain'
        # run the step through torch.compile (inductor fuses the elementwise / norm / cast glue between the big kernels
        # into a few generated ones) before it is graph-captured; slow first call, cached on disk after
        self.compile = compile
        # torch.compiler cache artifacts (dynamo + inductor) persisted between processes, so a warm start is seconds
        # rather than the full re-trace; see save_compile_cache
        self.compile_cache = compile_cache
        self._cache_loaded = False
        # fused int4/int8 GEMV for quantized weights when the token count is small (decode / verify); prefill stays on
        # dequant + cuBLAS. None: on when cuda and triton import. True on CPU needs TRITON_INTERPRET=1.
        self.triton = (self.device.type == 'cuda' and HAVE_TRITON) if triton is None else (triton and HAVE_TRITON)
        # with the Triton kernels the decode attention reads `pos` itself (one graph for the whole capacity, cost
        # proportional to the sequence); without them the Decoder buckets the buffer by powers of two
        self.attn_bucketed = not self.triton
        self.attn_splits = 32
        # KV cache format: 'bf16' (the compute dtype, two arrays per attention layer) or 'fp8' (e4m3 codes with a
        # float32 scale per position and kv head, four arrays: half the bytes, the same for prefix snapshots)
        if kv_dtype not in ('bf16', 'fp8'):
            raise ValueError(kv_dtype)
        self.kv_dtype = kv_dtype
        # the fused small pieces (torch_fused.py) in place of their composed forms. None: on with the Triton kernels.
        # Off, a step is the composed operations: what the fused ones are measured against, in time as in value.
        self.fused = self.triton if fused is None else (fused and self.triton)
        if self.triton:
            ensure_kernels()  # jit now (imports triton): the wrappers must find real JITFunctions when traced
            ensure_fused_kernels()
        self.triton_max_m = triton_max_m
        # a plain weight's product with one row through the Triton GEMV (torch_fused.py) up to this many output rows:
        # past them (an output head) cuBLAS is at the memory's bandwidth already
        self.dense_gemv_max_rows = 8192
        self.triton_block_n = triton_block_n
        self.gemv_tuned: GemvTable = dict(gemv_tuned or {})  # per-shape GEMV configs (entrypoints/tune, load_tuned)
        self.gdn_block_dv = 16  # fused DeltaNet step: value-dim slice per program (state tile [dk, block_dv] f32)
        self.quant_native = False  # on-device quantizer search (faster, not byte-identical across machines)
        self.gdn_num_warps = 1
        # the Triton kernel runs the recurrence for any number of tokens, so the model's fused path (Ops.gdn_step)
        # serves prefill chunks too; without it, only the few tokens of a decode / verify step (the composed step)
        self.gdn_fused_max_t = (1 << 30) if self.triton else 8

    def dtype(self, name):
        return dtypes()[name]

    # Host arrays up to this size go to a CUDA device through pinned memory, without waiting. A plain `.to(device)`
    # is a blocking copy: it waits for everything queued on the GPU first, and the small arrays made mid-generation
    # -- a prompt-lookup round's drafts, a grammar's mask rows, a token id -- are made while the draft head's refresh
    # is queued and the next launch is waiting on the host. (Weights are larger, loaded once, and not worth pinning.)
    ASYNC_ARRAY_BYTES: ta.ClassVar[int] = 1 << 20

    def array(self, a, dtype=None):
        a = np.ascontiguousarray(a)
        if not a.flags.writeable:  # memmap-backed (gguf / safetensors) arrays: torch wants ownership
            a = a.copy()
        t = torch.from_numpy(a)
        if dtype is not None:
            t = t.to(dtype)
        if self.device.type == 'cuda' and 0 < t.numel() * t.element_size() <= self.ASYNC_ARRAY_BYTES:
            return t.pin_memory().to(self.device, non_blocking=True)
        return t.to(self.device)

    def numpy(self, x):
        return x.detach().float().cpu().numpy() if x.is_floating_point() else x.detach().cpu().numpy()

    def numpy_later(self, x):
        if x.device.type != 'cuda':
            return super().numpy_later(x)
        # a copy into pinned memory is queued like a kernel, and the event after it marks where to wait up to
        x = x.detach().float() if x.is_floating_point() else x.detach()
        host = torch.empty(x.shape, dtype=x.dtype, pin_memory=True)
        host.copy_(x, non_blocking=True)
        event = torch.cuda.Event()
        event.record()

        def get():
            event.synchronize()
            return host.numpy().copy()

        return get

    def cast(self, x, dtype):
        return x.to(dtype)

    def copy(self, x):
        # canonical strides, not clone()'s preserved ones: a [1, 1, H] slice of a [1, T, H] tensor counts as contiguous
        # (size-1 dims) and keeps its stride T * H, and a compiled step is guarded on its inputs' strides
        return x.clone(memory_format=torch.contiguous_format)

    def to_host(self, x):
        h = torch.empty(x.shape, dtype=x.dtype, device='cpu', pin_memory=(self.device.type == 'cuda'))
        h.copy_(x)
        return h

    def from_host(self, h):
        return h.to(self.device, non_blocking=True)

    def zeros(self, shape, dtype):
        return torch.zeros(shape, dtype=dtype, device=self.device)

    def eval(self, *xs):
        if self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)
        elif self.device.type == 'mps':
            torch.mps.synchronize()

    def nbytes(self, w):
        if isinstance(w, (TorchQWeight, TorchQExperts, TorchMicroscaledExperts)):
            return w.nbytes()
        return w.numel() * w.element_size()

    def reshape(self, x, shape):
        return x.reshape(shape)

    def transpose(self, x, axes):
        return x.permute(axes)

    def concat(self, xs, axis):
        return torch.cat(list(xs), dim=axis)

    def rows_buffer(self, like, total):
        return torch.empty((like.shape[0], total, *like.shape[2:]), dtype=like.dtype, device=like.device)

    def rows_write(self, buf, start, x):
        buf[:, start:start + x.shape[1]].copy_(x)
        return buf

    def stack(self, xs, axis):
        return torch.stack(list(xs), dim=axis)

    def split(self, x, sizes, axis):
        return list(torch.split(x, list(sizes), dim=axis))

    def repeat(self, x, n, axis):
        return x.repeat_interleave(n, dim=axis)

    def arange(self, n):
        return torch.arange(n, dtype=torch.int32, device=self.device)

    def scalar(self, v):
        # filled on the device. Not `torch.tensor(v, device=...)`: that is a host tensor and a blocking copy of it,
        # which waits for everything queued on the GPU -- and a step's position is made between launches (the draft
        # head's k steps a round, each then waiting out the one before it, with the GPU idle while the host caught up)
        return torch.full((), v, dtype=torch.int32, device=self.device)

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

    def tanh(self, x):
        return torch.tanh(x)

    # the fused small pieces (torch_fused.py): one launch each where the composed forms are a dozen or more

    def bottleneck_blend(self, x, m, down, forget, gain, *, eps, dtype):
        if not (self.fused and x.is_cuda and isinstance(down, torch.Tensor) and is_pow2(down.shape[0])):
            return super().bottleneck_blend(x, m, down, forget, gain, eps=eps, dtype=dtype)
        return bottleneck_blend(x, m, down, forget, gain, eps)

    def short_conv(self, x, hist, weight, *, scale, all_states=False):
        if not (self.fused and x.is_cuda and x.shape[0] == 1):
            return super().short_conv(x, hist, weight, scale=scale, all_states=all_states)
        return short_conv(x, hist, weight, scale, all_states)

    def short_conv_dynamic(self, x, hist, weight, dyn, *, scale, all_states=False):
        if not (self.fused and x.is_cuda and x.shape[0] == 1 and dyn.is_contiguous()):
            return super().short_conv_dynamic(x, hist, weight, dyn, scale=scale, all_states=all_states)
        return short_conv(x, hist, weight, scale, all_states, dyn=dyn)

    def unit_rms(self, x, eps):
        xf = x.float()
        return F.rms_norm(xf, (xf.shape[-1],), eps=eps)

    def rms_norm_to(self, x, w, eps, dtype):
        if not (self.fused and x.is_cuda and w.dim() == 1 and x.shape[0] == 1 and x.dim() == 3):
            return super().rms_norm_to(x, w, eps, dtype)
        return rms_norm_to(x, w, eps, dtype)

    def l2_clip(self, x, threshold, *, scale=None, after=None):
        if not (
                self.fused and
                x.is_cuda and
                x.dim() == 4 and
                x.shape[0] == 1 and
                is_pow2(x.shape[-1]) and
                x.is_contiguous() and
                (scale is None or (scale.dtype == x.dtype and tuple(scale.shape) == tuple(x.shape[2:])))
        ):
            return super().l2_clip(x, threshold, scale=scale, after=after)
        return l2_clip(x, threshold, scale, after)

    def sdpa_window_rel_at(self, q, state, base, slots, pos, *, scale, rel, rel_proj, sink, window):
        if not (
                self.fused and
                q.is_cuda and
                q.shape[0] == 1 and
                len(state) == 2 and
                isinstance(rel_proj, torch.Tensor) and
                is_pow2(q.shape[-1]) and
                is_pow2(rel_proj.shape[-1])
        ):
            return super().sdpa_window_rel_at(
                q,
                state,
                base,
                slots,
                pos,
                scale=scale,
                rel=rel,
                rel_proj=rel_proj,
                sink=sink,
                window=window,
            )
        return sdpa_window_rel(
            q,
            state[0],
            state[1],
            pos,
            scale,
            rel.contiguous(),
            rel_proj,
            sink,
            window,
            base=base.to(torch.int32),
            slots=slots,
        )

    # The queries the window kernel takes at a time. A step's few go whole. A prefill's go this many at a time, each
    # run against the keys it can see: the kernel scores every tile of the keys it is handed for every query, so a
    # long run of queries, whose windows cover different keys, would have most of its tiles see nothing.
    window_rel_rows: int = 256

    def sdpa_window_rel(self, q, k, v, pos, *, scale, rel, rel_proj, sink, window, more=()):
        if not (
                self.fused and
                q.is_cuda and
                q.shape[0] == 1 and
                isinstance(rel_proj, torch.Tensor) and
                is_pow2(q.shape[-1]) and
                is_pow2(rel_proj.shape[-1])
        ):
            return super().sdpa_window_rel(
                q,
                k,
                v,
                pos,
                scale=scale,
                rel=rel,
                rel_proj=rel_proj,
                sink=sink,
                window=window,
                more=more,
            )

        T = q.shape[2]
        N = k.shape[2]
        rel = rel.contiguous()
        if T <= self.window_rel_rows:
            return sdpa_window_rel(q, k.contiguous(), v.contiguous(), pos, scale, rel, rel_proj, sink, window, more)

        outs = []
        for a in range(0, T, self.window_rel_rows):
            b = min(a + self.window_rel_rows, T)
            lo = max(0, N - T + a - (window - 1))  # the first slot the run's first query sees
            hi = N - T + b
            outs.append(sdpa_window_rel(
                q[:, :, a:b],
                k[:, :, lo:hi].contiguous(),
                v[:, :, lo:hi].contiguous(),
                pos + a,
                scale,
                rel[a:b],
                rel_proj,
                sink[:, :, a:b],
                window,
                [(m[:, :, a:b], ls[:, :, a:b], o[:, :, a:b]) for m, ls, o in more],
            ))
        return torch.cat(outs, 2)

    def sigmoid_gated(self, x, g, dtype):
        if not (self.fused and x.is_cuda and x.shape == g.shape and x.is_contiguous() and g.is_contiguous()):
            return super().sigmoid_gated(x, g, dtype)
        return sigmoid_gated(x, g, dtype)

    def sum_to(self, a, b, dtype):
        if not (self.fused and a.is_cuda and a.shape == b.shape and a.is_contiguous() and b.is_contiguous()):
            return super().sum_to(a, b, dtype)
        return sum_to(a, b, dtype)

    def sigmoid_route(self, logits, bias, k, *, total):
        if not (self.fused and logits.is_cuda and logits.dim() == 2 and logits.is_contiguous()):
            return super().sigmoid_route(logits, bias, k, total=total)
        return sigmoid_route(logits, bias, k, total)

    def capped_gate(self, h, *, gate_cap, up_cap):
        if not (self.fused and h.is_cuda and h.dim() == 2 and h.is_contiguous()):
            return super().capped_gate(h, gate_cap=gate_cap, up_cap=up_cap)
        return capped_gate(h, gate_cap, up_cap)

    def weighted_rows(self, y, w, dtype):
        if not (self.fused and y.is_cuda and y.is_contiguous()):
            return super().weighted_rows(y, w, dtype)
        return weighted_rows(y, w, dtype)

    def depth_mix(self, queries, sources, *, raw=0, eps=0.):
        if not (
                self.fused and
                queries.is_cuda and
                len(sources) <= DEPTH_MIX_MAX_SOURCES and
                all(s.shape[0] == 1 and s.is_contiguous() for s in sources)
        ):
            return super().depth_mix(queries, sources, raw=raw, eps=eps)
        return depth_mix(queries, sources, raw, eps)

    def sqrt(self, x):
        return torch.sqrt(x)

    def maximum(self, x, v):
        return torch.clamp(x, min=v)

    def minimum(self, x, v):
        return torch.clamp(x, max=v)

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

    def weight(self, w, dtype, name=None):
        return self.array(w, dtype)

    def qweight(self, qw: QWeight, dtype, name=None):
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
            search=True,
            name=None,
    ):
        """
        Quantize + adopt. The error-minimising search runs in the canonical numpy implementation (bit-identical on every
        machine and backend, so a parameter cache built here matches one built on a Mac) unless `quant_native` is set,
        which uses this on-device version instead: the same algorithm, a few seconds per 27B tensor faster, but
        reductions in GPU order, so not byte-for-byte the same codes. Plain min/max always runs on the device. Rows are
        processed in blocks of ~256 MB of float32 so a 5 GB output head does not need itself plus the search's
        temporaries resident at once.
        """

        if search and not self.quant_native:
            return self.qweight(quantize_np(w, bits, group, True), dtype)
        out, inn = w.shape
        if inn % group:
            raise ValueError(f'in_features {inn} not a multiple of group {group}')
        rows = max(64, (256 << 20) // (inn * 4))
        if out > rows:
            parts = [
                self.quantize(
                    w[r:r + rows],
                    bits,
                    group,
                    dtype,
                    search,
                )
                for r in range(0, out, rows)
            ]
            return TorchQWeight(
                torch.cat([p.q for p in parts], 0),
                torch.cat([p.scale for p in parts], 0),
                torch.cat([p.bias for p in parts], 0),
                bits,
                group,
                (out, inn),
            )
        qmax = (1 << bits) - 1
        g = self.array(np.ascontiguousarray(w), torch.float32).reshape(out, inn // group, group)
        lo = g.amin(-1)
        hi = g.amax(-1)
        scale = (hi - lo) / qmax
        scale = torch.where(scale == 0, torch.ones_like(scale), scale)
        bias = lo
        if search:
            mid = (hi + lo) * 0.5
            half = (hi - lo) * 0.5
            best_err = None
            best_q = None
            best_s = scale
            best_b = bias
            for shrink in SEARCH_SHRINKS:
                s = torch.clamp(2 * half * shrink / qmax, min=1e-12)
                b = mid - half * shrink
                q = torch.round((g - b[..., None]) / s[..., None]).clamp_(0, qmax)
                s2, b2, err = _refit_torch(g, q, s, b)
                if best_err is None:
                    best_err = err
                    best_q = q
                    best_s = s2
                    best_b = b2
                else:
                    better = err < best_err
                    best_err = torch.where(better, err, best_err)
                    best_q = torch.where(better[..., None], q, check.not_none(best_q))
                    best_s = torch.where(better, s2, best_s)
                    best_b = torch.where(better, b2, best_b)
            q = torch.round((g - best_b[..., None]) / best_s[..., None]).clamp_(0, qmax)
            s2, b2, err = _refit_torch(g, q, best_s, best_b)
            better = err < best_err
            qf = torch.where(better[..., None], q, check.not_none(best_q))
            scale = torch.where(better, s2, best_s)
            bias = torch.where(better, b2, best_b)
        else:
            qf = torch.round((g - bias[..., None]) / scale[..., None]).clamp_(0, qmax)
        q = qf.to(torch.uint8).reshape(out, inn)
        if bits == 4:
            q = q[:, 0::2] | (q[:, 1::2] << 4)
        return TorchQWeight(
            q.contiguous(),
            scale.to(dtype),
            bias.to(dtype),
            bits,
            group,
            (out, inn),
        )

    def head_rows(self, w, n):
        if isinstance(w, TorchQWeight):
            return TorchQWeight(
                w.q[:n],
                w.scale[:n],
                w.bias[:n],
                w.bits,
                w.group,
                (n, w.shape[1]),
            )

        return w[:n]

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

    def gdn_step(
            self,
            q,
            k,
            v,
            a,
            b,
            A,
            dt_bias,
            state,
            all_states,
            eps=1e-6,
    ):
        if self.triton:
            return gdn_step(
                q,
                k,
                v,
                a,
                b,
                A,
                dt_bias,
                state,
                all_states,
                eps,
                self.gdn_block_dv,
                self.gdn_num_warps,
            )

        return super().gdn_step(
            q,
            k,
            v,
            a,
            b,
            A,
            dt_bias,
            state,
            all_states,
            eps,
        )

    def linear(self, x, w):
        if isinstance(w, TorchQWeight):
            if self.triton and x.numel() // x.shape[-1] <= self.triton_max_m:
                launch = w.launch
                if launch is None:  # the first, eager call (compiled steps run once eagerly first: _DeferredCompile)
                    launch = w.launch = resolve_launch(
                        x,
                        w.q,
                        w.scale,
                        w.bias,
                        w.bits,
                        w.group,
                        w.shape,
                        block_n=self.triton_block_n,
                        tuned=self.gemv_tuned,
                    )
                return qlinear(
                    x,
                    w.q,
                    w.scale,
                    w.bias,
                    w.bits,
                    w.group,
                    w.shape,
                    launch=launch,
                )
            return self._linear_dense(x, w)
        if (
                self.fused and
                x.is_cuda and
                x.numel() == x.shape[-1] and
                w.dim() == 2 and
                w.shape[0] <= self.dense_gemv_max_rows and
                w.dtype == x.dtype and
                w.is_contiguous()
        ):
            return dense_gemv(x, w)  # (a step's one token)
        if (
                self.fused and
                x.is_cuda and
                w.dim() == 2 and
                w.dtype == x.dtype and
                w.is_contiguous() and
                w.shape[1] <= DENSE_ROWS_MAX_K
        ):
            rows = x.numel() // x.shape[-1]
            if dense_rows_pays(rows, w.shape[0]):
                # (a speculative round's rows)
                return dense_rows(x.reshape(rows, x.shape[-1]), w).reshape(*x.shape[:-1], w.shape[0])
        return F.linear(x, w)

    def _linear_dense(self, x, w, chunk_rows=16384):
        """
        A quantized weight against many rows (a prefill chunk): dequantized, 16384 output rows at a time (the 27B's
        output head whole would be 2.5 GB), and matmul'd by cuBLAS. With Triton the dequantization is one fused pass
        (torch_triton.dequantize: a fifth of the composed tensor ops' time, and computed in float32 like the GEMV
        kernels' use of the same weight, where the composition rounds to the compute dtype three times); without,
        TorchQWeight.dequant's composition.
        """

        if not (self.triton and x.is_cuda):
            return w.linear(x, chunk_rows)

        n, k = w.shape
        outs = []
        for i in range(0, n, chunk_rows):
            j = min(i + chunk_rows, n)
            dense = dequantize(w.q[i:j], w.scale[i:j], w.bias[i:j], w.bits, w.group, (j - i, k), x.dtype)
            outs.append(F.linear(x, dense))
        return outs[0] if len(outs) == 1 else torch.cat(outs, dim=-1)

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
        if w.dim() > 1:  # a weight per group (see Ops.rms_norm): F.rms_norm takes one for the normalized dim only
            return super().rms_norm(x, w, eps)
        xf = x.float()
        return F.rms_norm(xf, (xf.shape[-1],), weight=w.float(), eps=eps).to(x.dtype)

    def sdpa_static(self, q, kbuf, vbuf, pos, ar, scale):
        if self.triton:
            return attn_decode(
                q,
                kbuf,
                vbuf,
                pos,
                scale,
                self.attn_splits,
            )
        return super().sdpa_static(
            q,
            kbuf,
            vbuf,
            pos,
            ar,
            scale,
        )

    # KV state format (see Ops.kv_arity): fp8 e4m3 codes + per-position scales when kv_dtype == 'fp8'

    FP8_MAX = 448.0  # e4m3's largest finite value

    @property
    def FP8(self):  # (a property: torch is imported lazily, so no class attribute may touch it)
        return torch.float8_e4m3fn

    @property
    def kv_arity(self):  # type: ignore[override]
        return 4 if self.kv_dtype == 'fp8' else 2

    def _fp8_quant(self, x):
        """[B, KV, T, D] -> (e4m3 codes, float32 scales [B, KV, T]) with one scale per position and kv head."""

        xf = x.float()
        amax = xf.abs().amax(-1)
        scale = (amax / self.FP8_MAX).clamp_min(1e-12)
        q = (xf / scale[..., None]).to(self.FP8)
        return q, scale

    def _fp8_dequant(self, q, scale, dtype):
        return (q.to(torch.float32) * scale[..., None]).to(dtype)

    def kv_new(self, k, v):
        if self.kv_dtype != 'fp8':
            return (k, v)
        kq, ks = self._fp8_quant(k)
        vq, vs = self._fp8_quant(v)
        return (kq, ks, vq, vs)

    def kv_adapt(self, state, dtype=None):
        """A state in this backend's format: (k, v) -> fp8 codes + scales, or fp8 -> (k, v) in `dtype`."""

        if len(state) == self.kv_arity:
            return state
        if self.kv_dtype == 'fp8' and len(state) == 2:
            return self.kv_new(state[0], state[1])
        if self.kv_dtype == 'bf16' and len(state) == 4:
            dt = dtype if dtype is not None else (torch.bfloat16 if self.device.type != 'cpu' else torch.float32)
            return (self._fp8_dequant(state[0], state[1], dt), self._fp8_dequant(state[2], state[3], dt))
        raise ValueError(f'cannot adapt a {len(state)}-array KV state to kv_dtype={self.kv_dtype}')

    def expert_weights(self, parts):
        flat = [w for p in parts for w in p]
        if not all(isinstance(w, TorchQWeight) for w in flat):
            dense = [[w.dequant(self.dtype('f32')) if isinstance(w, TorchQWeight) else w for w in p] for p in parts]
            return super().expert_weights(dense)
        bits, group = flat[0].bits, flat[0].group
        if any(w.bits != bits or w.group != group for w in flat):
            raise ValueError('experts quantized at different widths or groups cannot be stacked')
        experts = [
            (torch.cat([w.q for w in p], 0), torch.cat([w.scale for w in p], 0), torch.cat([w.bias for w in p], 0))
            for p in parts
        ]
        return TorchQExperts(
            q=torch.stack([e[0] for e in experts], 0),
            scale=torch.stack([e[1] for e in experts], 0),
            bias=torch.stack([e[2] for e in experts], 0),
            bits=bits,
            group=group,
            shape=(sum(w.shape[0] for w in parts[0]), parts[0][0].shape[1]),
        )

    def microscaled(self, mw: MicroscaledWeight, dtype, name=None):
        f32 = torch.float32
        nvfp4 = mw.fmt == 'nvfp4'
        scale_values = e4m3_values() if nvfp4 else pow2_scale_values()
        return TorchMicroscaledExperts(
            fmt=mw.fmt,
            codes=self.array(mw.codes),
            scales=self.array(mw.scales),
            outer=self.array(mw.outer, f32) if mw.outer is not None else None,
            code_values=self.array(e2m1_pair_values() if nvfp4 else e4m3_values()[:, None], f32),
            scale_values=self.array(scale_values[:, None], f32),
            code_table=self.array(e2m1_values() if nvfp4 else e4m3_values(), f32),
            scale_table=self.array(scale_values, f32),
            block=mw.block,
            shape=(mw.shape[1], mw.shape[2]),
        )

    def expert_dense(self, w, e, dtype):
        if isinstance(w, TorchMicroscaledExperts) and self.triton and w.codes.is_cuda:
            return mdequantize(
                w.codes[e],
                w.scales[e],
                w.outer[e:e + 1] if w.outer is not None else None,
                w.code_table,
                w.scale_table,
                w.block,
                w.shape,
                dtype,
            )
        if isinstance(w, (TorchQExperts, TorchMicroscaledExperts)):
            return w.dequant(dtype, torch.full((1,), e, dtype=torch.int64, device=self.device))[0]
        return super().expert_dense(w, e, dtype)

    # The experts a prefill decodes to dense at a time (`expert_linear_grouped`): one launch writes that many, and
    # what they take while their rows are multiplied is what a long prefill's peak grows by -- 0.34 GiB for 32 of
    # Inkling 2 Mini's larger matrix at bfloat16.
    microscaled_dense_stack: int = 32

    def expert_linear_grouped(self, rows, w, eids):
        """
        For packed experts with the Triton kernels: the rows sorted by expert on the device, the experts decoded a
        run at a time in one launch each, and each expert present multiplied into its rows where they lie. (The
        composed form's decode and matmul per expert, with its slices and its concatenation, was a second of every
        prefill chunk on Inkling 2 Mini -- 12,288 experts a chunk over its 48 visits, bound by their launches.)
        """

        if not (isinstance(w, TorchMicroscaledExperts) and self.triton and rows.is_cuda):
            return super().expert_linear_grouped(rows, w, eids)

        E = w.codes.shape[0]
        n = w.shape[0]
        ids = eids.to(torch.int64)
        order = torch.argsort(ids, stable=True)
        counts = torch.bincount(ids, minlength=E).tolist()  # (read on the host: this is a prefill's)
        sorted_rows = rows[order]
        out = torch.empty((rows.shape[0], n), dtype=rows.dtype, device=rows.device)

        at = 0
        for e0 in range(0, E, self.microscaled_dense_stack):
            e1 = min(e0 + self.microscaled_dense_stack, E)
            if not any(counts[e0:e1]):
                continue
            dense = mdequantize(
                w.codes[e0:e1],
                w.scales[e0:e1],
                w.outer[e0:e1] if w.outer is not None else None,
                w.code_table,
                w.scale_table,
                w.block,
                w.shape,
                rows.dtype,
            )
            for e in range(e0, e1):
                c = counts[e]
                if c:
                    torch.mm(sorted_rows[at:at + c], dense[e - e0].T, out=out[at:at + c])
                    at += c

        return torch.empty_like(out).index_copy_(0, order, out)

    # With the Triton kernel a row costs the expert's own work and nothing else, so a prefill's rows go through it
    # too until they are so many that decoding each expert present once (`expert_linear_grouped`) is less: that
    # many rows an expert of the stack. Measured on Inkling 2 Mini's 128 experts (the 5090, seconds of a prefill):
    #
    #     tokens        16    64    128   256   384   512   768   1024
    #     by the row    0.11  0.11  0.17  0.36  0.54  0.72  1.09  1.48
    #     grouped       0.29  0.36  0.40  0.42  0.44  0.48  0.51  0.54
    #
    # They cross near 310 tokens, 19 rows an expert. (48 when the grouped path decoded and multiplied an expert at
    # a time and cost a second whatever the rows; and at 8, first set by guess, a 129-token prefill took 1.1 s
    # where a 128-token one took 0.2.)
    microscaled_gemv_rows_per_expert: int = 20

    def expert_linear(self, x, w, eids, x_div=1):
        if not isinstance(w, (TorchQExperts, TorchMicroscaledExperts)):
            return super().expert_linear(x, w, eids, x_div)
        if isinstance(w, TorchQExperts) and self.triton and x.is_cuda:
            return qgemv_experts(
                x,
                eids.to(torch.int32),
                w.q,
                w.scale.to(x.dtype),
                w.bias.to(x.dtype),
                w.bits,
                w.group,
                w.shape,
                x_div=x_div,
            )
        if isinstance(w, TorchMicroscaledExperts) and self.triton and x.is_cuda:
            if eids.shape[0] <= self.microscaled_gemv_rows_per_expert * w.codes.shape[0]:
                return mgemv_experts(
                    x,
                    eids.to(torch.int32),
                    w.codes,
                    w.scales,
                    w.outer,
                    w.code_table,
                    w.scale_table,
                    w.block,
                    w.shape,
                    x_div=x_div,
                )
            rows = x.repeat_interleave(x_div, 0) if x_div > 1 else x
            return self.expert_linear_grouped(rows, w, eids)
        rows = x.repeat_interleave(x_div, 0) if x_div > 1 else x
        if rows.shape[0] > self.expert_gather_max_rows:
            return self.expert_linear_grouped(rows, w, eids)  # (a prefill's rows: expert by expert)
        return (w.dequant(x.dtype, eids) @ rows[:, :, None])[..., 0]

    def kv_gather(self, state, positions, dtype):
        if len(state) == 2:
            return state[0][0][:, positions], state[1][0][:, positions]
        kq, ks, vq, vs = (a[0][:, positions] for a in state)
        return self._fp8_dequant(kq, ks, dtype), self._fp8_dequant(vq, vs, dtype)

    def kv_dense(self, state, dtype):
        if len(state) == 2:
            return state[0], state[1]
        return self._fp8_dequant(state[0], state[1], dtype), self._fp8_dequant(state[2], state[3], dtype)

    def kv_concat(self, state, k, v):
        if self.kv_dtype != 'fp8':
            return super().kv_concat(state, k, v)
        if len(state) != 4:
            state = self.kv_adapt(state)
        kq, ks = self._fp8_quant(k)
        vq, vs = self._fp8_quant(v)
        return (
            torch.cat([state[0], kq], 2),
            torch.cat([state[1], ks], 2),
            torch.cat([state[2], vq], 2),
            torch.cat([state[3], vs], 2),
        )

    def kv_pad(self, state, capacity):
        out = []
        for a in state:
            n = a.shape[2]
            if n < capacity:
                shape = list(a.shape)
                shape[2] = capacity - n
                if a.dtype == self.FP8:
                    pad = torch.zeros(shape, dtype=torch.uint8, device=a.device).view(self.FP8)
                else:
                    pad = torch.zeros(shape, dtype=a.dtype, device=a.device)
                a = torch.cat([a, pad], 2)
            elif n > capacity:
                raise ValueError(f'KV longer ({n}) than capacity ({capacity})')
            out.append(a)
        return tuple(out)

    kv_in_place = True
    capture_sampling = True

    def kv_reserve(self, state, capacity, into=None):
        # index writes are in place here, so a prefill fills capacity buffers (the decoder's own, in the end)
        n = self.kv_len(state)
        if n >= capacity:
            return state
        if (
                into is not None and
                len(into) == len(state) and
                all(
                    d.shape[2] == capacity and d.dtype == s.dtype and d.device == s.device and
                    d.shape[:2] == s.shape[:2] and d.shape[3:] == s.shape[3:]
                    for d, s in zip(into, state)
                )
        ):
            # an earlier decoder's buffers: no allocation and no zero fill, just the state's own positions
            if n:
                for d, s in zip(into, state):
                    d[:, :, :n].copy_(s)
            return tuple(into)
        return self.kv_pad(state, capacity)

    def kv_write_state(self, state, pos, k, v):
        return self.kv_write_tokens(state, pos, k, v)

    def assign(self, dst, src):
        dst.copy_(src)
        return dst

    def kv_move(self, state, src, dst, n):
        for a in state:
            a[:, :, dst:dst + n] = a[:, :, src:src + n].clone()  # (a copy first: the two stretches may overlap)
        return state

    def kv_write_tokens(self, state, pos, k, v):
        # every position of the step in one indexed write per buffer (and one fp8 quantization): a T-token step made
        # T of each, per attention layer -- ~200 small kernels a speculative round on the 27B, and T-long chains of
        # in-place writes that torch.compile took minutes over past a dozen tokens
        if (
                self.kv_dtype != 'fp8' and
                self.fused and
                k.is_cuda and
                k.shape[0] == 1 and
                is_pow2(k.shape[-1]) and
                k.stride(3) == 1 and
                v.stride(3) == 1 and
                state[0].is_contiguous() and
                state[1].is_contiguous()
        ):
            kv_append(state[0], state[1], pos, k, v)
            return (state[0], state[1])

        idx = pos.reshape(1).to(torch.int64) + torch.arange(k.shape[2], device=k.device)
        if self.kv_dtype != 'fp8':
            kbuf, vbuf = state
            kbuf.index_copy_(2, idx, k.to(kbuf.dtype))
            vbuf.index_copy_(2, idx, v.to(vbuf.dtype))
            return (kbuf, vbuf)
        kq, ks = self._fp8_quant(k)
        vq, vs = self._fp8_quant(v)
        kbuf, ksb, vbuf, vsb = state
        # In place, same objects out. Item assignment with an index array is an index_put_ on the fp8 buffer itself,
        # which is the one indexed write that works here: index_copy_ has no float8 kernel (cpu or cuda), and writing
        # through a uint8 view of the buffer breaks torch.compile - inductor stores the view's bytes through the
        # buffer's own fp8-typed pointer, and Triton has no int -> fp8 value cast ('cannot cast uint8[..] to
        # fp8e4nv').
        kbuf[:, :, idx] = kq
        vbuf[:, :, idx] = vq
        ksb.index_copy_(2, idx, ks)
        vsb.index_copy_(2, idx, vs)
        return (kbuf, ksb, vbuf, vsb)

    def sdpa_state(self, q, state, scale, past):
        if len(state) == 2:
            return self.sdpa(
                q,
                state[0],
                state[1],
                scale,
                past,
            )
        kq, ks, vq, vs = state
        if self.triton and q.shape[2] > 1:
            return attn_prefill(
                q,
                kq,
                vq,
                scale,
                past,
                ks=ks,
                vs=vs,
            )
        return self.sdpa(
            q,
            self._fp8_dequant(kq, ks, q.dtype),
            self._fp8_dequant(vq, vs, q.dtype),
            scale,
            past,
        )

    def sdpa_static_state(self, q, state, pos, ar, scale):
        if len(state) == 2:
            return self.sdpa_static(q, state[0], state[1], pos, ar, scale)
        kq, ks, vq, vs = state
        if self.triton:
            return attn_decode(q, kq, vq, pos, scale, self.attn_splits, ks=ks, vs=vs)
        kd = self._fp8_dequant(kq, ks, q.dtype)
        vd = self._fp8_dequant(vq, vs, q.dtype)
        return super().sdpa_static(q, kd, vd, pos, ar, scale)

    def sdpa_causal_partials(self, q, k, v, last, scale):
        if not (self.triton and q.is_cuda):
            return super().sdpa_causal_partials(q, k, v, last, scale)

        # The decode attention kernel, which reads each query row's own keys and keeps no [T, L] of scores: a
        # prefill's rows at once. One split of the keys -- the splits are for a step's few rows to fill the device
        # with, and each costs a partial per row.
        T = q.shape[2]
        m, l, o = attn_decode_partials(
            q,
            k,
            v,
            torch.tensor(max(last, -T), dtype=torch.int32, device=q.device),
            scale,
            self.attn_splits if T <= 16 else 1,
        )
        return torch.clamp(m, min=-1e30), l, o  # (a row with no key: -inf from the kernel)

    def sdpa_static_rel(self, q, state, pos, ar, scale, rel, rel_proj, sink):
        if not (self.triton and q.is_cuda and isinstance(rel_proj, torch.Tensor)):
            return super().sdpa_static_rel(q, state, pos, ar, scale, rel, rel_proj, sink)
        return self.sdpa_static_rel_split(q, state, pos, scale, rel, rel_proj, sink)

    def sdpa_static_rel_split(self, q, state, pos, scale, rel, rel_proj, sink):
        """
        `sdpa_static_rel`, length-aware, in two parts whose softmax partials are merged with the sink. The keys at
        least E back carry no relative term: they go through the decode attention kernel at a position E earlier (row
        t then sees the keys up to pos - E + t, which are exactly those), reading the positions in use and no others.
        The E - 1 + T nearest are gathered and scored with the term, as a window E long: the window kernel's
        partials (torch_fused.py), a tile of them a set.
        """

        B, H, T, D = q.shape
        E = rel_proj.shape[0]

        if len(state) == 2:
            kbuf, vbuf = state
            ks = vs = None
        else:
            kbuf, ks, vbuf, vs = state
        far_pos = torch.clamp(pos - E, min=-T)
        m_far, l_far, o_far = attn_decode_partials(q, kbuf, vbuf, far_pos, scale, self.attn_splits, ks=ks, vs=vs)

        n = E - 1 + T
        far = [(m_far, l_far, o_far)]

        # (slot j of the near keys stands for position pos - (E - 1) + j: none where that is negative, and the
        # kernel leaves those, like the ones E or more back from a query, out -- and never reads them)
        if ks is None and self.fused and is_pow2(D) and is_pow2(rel_proj.shape[-1]) and kbuf.is_contiguous():
            # plain buffers: read where they lie
            base = (pos - (E - 1)).to(torch.int32)
            return sdpa_window_rel(q, kbuf, vbuf, pos, scale, rel, rel_proj, sink, E, far, base=base, slots=n)

        kpos = (pos.reshape(1) - (E - 1)) + torch.arange(n, device=q.device, dtype=torch.int32)
        kg, vg = self.kv_gather(state, torch.clamp(kpos, min=0), q.dtype)  # [KV, n, D]
        return sdpa_window_rel(q, kg[None], vg[None], pos, scale, rel, rel_proj, sink, E, far)

    def sdpa(
            self,
            q,
            k,
            v,
            scale,
            past,
    ):
        B, H, T, D = q.shape
        KV = k.shape[1]
        L = k.shape[2]
        if self.triton and T > 1:
            # flash-attention with the KV offset: no [T, L] mask, no key blocks above the diagonal, GQA by index
            return attn_prefill(q, k, v, scale, past)
        if KV != H:
            k = k.repeat_interleave(H // KV, dim=1)
            v = v.repeat_interleave(H // KV, dim=1)
        if T == 1:
            return F.scaled_dot_product_attention(q, k, v, scale=scale)
        if past == 0:
            return F.scaled_dot_product_attention(q, k, v, is_causal=True, scale=scale)
        mask = torch.ones(T, L, dtype=torch.bool, device=q.device).tril(diagonal=past)
        return F.scaled_dot_product_attention(q, k, v, attn_mask=mask, scale=scale)

    def conv1d_causal(self, x, w):
        return F.conv1d(x, w[:, None, :], groups=w.shape[0])

    def compile_fn(self, fn):
        if not self.compile:
            return fn
        if self.compile_cache and not self._cache_loaded:
            self._cache_loaded = True
            load_compile_cache(self.compile_cache)
        return _DeferredCompile(fn)

    def _capture(self, fn, carry=None):
        mode = self.capture_mode
        if mode == 'auto':
            mode = 'graph' if self.device.type == 'cuda' else 'plain'
        if mode == 'plain':
            return fn
        return CudaGraphStep(fn, use_graph=(mode == 'graph'), carry=carry)

    def capture(self, fn):
        return self._capture(fn)

    def capture_carrying(self, fn, outputs_from, inputs_from):
        return self._capture(fn, (outputs_from, inputs_from))

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
        xr = x[..., :dims]
        xp = x[..., dims:]
        half = dims // 2
        rot = torch.cat([-xr[..., half:], xr[..., :half]], dim=-1)
        return torch.cat([xr * cos[None, None] + rot * sin[None, None], xp], dim=-1)
