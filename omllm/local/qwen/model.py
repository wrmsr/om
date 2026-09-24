# ruff: noqa: N803 N806 N812
"""
Qwen3.5 / 3.6 / 3.8 (dense) text decoder, written once against `Ops` (see ops.py) and run on any backend.

Every op is written out; there is no `transformers` and no backend-specific code here. Layer math is cross-checked
against llama.cpp's `src/models/qwen35.cpp` and HF's `modeling_qwen3_5.py`:

  block:    x = x + mixer(rmsnorm(x));  x = x + swiglu(rmsnorm(x))
  mixer is either
    full:   gated GQA attention -- q_proj emits [q | gate] per head, per-head q/k RMSNorm, partial NeoX RoPE on the
            first `rope_dim` dims, softmax attention, * sigmoid(gate), o_proj
    linear: Gated DeltaNet -- in_proj_qkv -> causal depthwise conv1d(k=4)+silu -> l2norm(q,k) -> gated delta rule
            recurrence (fixed-size state) -> rmsnorm * silu(z) -> out_proj

State is functional: each mixer takes its state (or None) and returns the new one. The gated delta rule lives behind
`Ops.gated_delta`, which dispatches to the per-token form for decode (T == 1) and the chunked WY form for prefill; both
are composed from the primitives, and backends override whichever they have a kernel for.
"""
import math
import pathlib
import typing as ta

import numpy as np

from omcore import check

from .ops import Array
from .ops import Ops
from .ops import Weight
from .paramcache import ParamCache
from .prefixcache import PrefixCache
from .prefixcache import Snapshot
from .quant import QUANT_BITS
from .quant import QWeight
from .quant import from_native
from .quant import quantize as quantize_np
from .weights import Qwen35Config
from .weights import TensorSource


##
# Cache


FullState = tuple[Array, Array]  # k, v: [B, n_kv, T, hd]
LinearState = tuple[Array, Array]  # conv: [B, conv_dim, kernel-1] last inputs to the conv; state: [B, n_v, dk, dv]


class Cancelled(Exception):  # noqa
    """Raised out of `generate` (by its callbacks) to abandon a generation between rounds or prefill chunks."""


class Cache:
    """
    One entry per layer. Attention layers grow a KV cache; linear layers keep a fixed-size (conv window, recurrent
    state) pair -- so 'prefix caching' for 3/4 of the stack is just snapshotting a tensor.
    """

    def __init__(self, cfg: Qwen35Config) -> None:
        self.layers: list[FullState | LinearState | None] = [None] * cfg.num_layers
        self.seq_len = 0

    def snapshot(self, ops: Ops) -> Cache:
        c = Cache.__new__(Cache)
        c.seq_len = self.seq_len
        c.layers = [None if st is None else tuple(ops.copy(a) for a in st) for st in self.layers]
        return c


##
# Layers


class Attention:
    def __init__(self, cfg: Qwen35Config, p: dict[str, Weight]) -> None:
        self.cfg = cfg
        self.wqkv = p.get('qkv_proj')  # fused [q | k | v] when the loader provides it
        self.wq = p.get('q_proj')
        self.wk = p.get('k_proj')
        self.wv = p.get('v_proj')
        self.wo = p['o_proj']
        self.q_norm = p['q_norm']
        self.k_norm = p['k_norm']
        self.scale = 1.0 / math.sqrt(cfg.head_dim)

    def project(self, ops: Ops, x: Array) -> tuple[Array, Array, Array]:
        """[q | gate] [B, T, H*2D], k [B, T, KV*D], v [B, T, KV*D] -- one GEMV when fused."""

        c = self.cfg
        if self.wqkv is not None:
            nq = c.num_heads * c.head_dim * 2
            nkv = c.num_kv_heads * c.head_dim
            qg, k, v = ops.split(ops.linear(x, self.wqkv), [nq, nkv, nkv], -1)
            return qg, k, v
        return ops.linear(x, self.wq), ops.linear(x, self.wk), ops.linear(x, self.wv)

    def __call__(self, ops: Ops, x: Array, pos: int, state: FullState | None) -> tuple[Array, FullState]:
        c = self.cfg
        B, T, _ = x.shape
        H = c.num_heads
        KV = c.num_kv_heads
        D = c.head_dim
        qg, k, v = self.project(ops, x)
        qg = ops.reshape(qg, (B, T, H, 2 * D))
        # per-head [q | gate]
        q = qg[..., :D]
        gate = qg[..., D:]
        k = ops.reshape(k, (B, T, KV, D))
        v = ops.reshape(v, (B, T, KV, D))
        q = ops.transpose(ops.rms_norm(q, self.q_norm, c.rms_eps), (0, 2, 1, 3))  # [B,H,T,D]
        k = ops.transpose(ops.rms_norm(k, self.k_norm, c.rms_eps), (0, 2, 1, 3))  # [B,KV,T,D]
        v = ops.transpose(v, (0, 2, 1, 3))
        q = ops.rope(q, pos, c.rope_dim, c.rope_theta)
        k = ops.rope(k, pos, c.rope_dim, c.rope_theta)
        past = 0
        if state is not None:
            past = state[0].shape[2]
            k = ops.concat([state[0], k], 2)
            v = ops.concat([state[1], v], 2)
        o = ops.sdpa(q, k, v, self.scale, past)  # [B,H,T,D]
        o = ops.reshape(ops.transpose(o, (0, 2, 1, 3)), (B, T, H * D))
        o = o * ops.cast(ops.sigmoid(ops.f32(ops.reshape(gate, (B, T, H * D)))), o.dtype)
        return ops.linear(o, self.wo), (k, v)

    def decode(
            self,
            ops: Ops,
            x: Array,
            pos: Array,
            ar: Array,
            cos: Array,
            sin: Array,
            state: FullState,
    ) -> tuple[Array, FullState]:
        """
        T tokens against fixed-capacity KV buffers. x: [B, T, hidden] at positions pos..pos+T-1; pos: 0-d int
        array; ar: arange(L); cos, sin: [T, rope_dim] rows for those positions; state: (kbuf, vbuf)
        [B, KV, L, D]. Every shape is static in `pos`; T == 1 is decode, T == k + 1 speculative verify.
        """

        c = self.cfg
        B, T, _ = x.shape
        H = c.num_heads
        KV = c.num_kv_heads
        D = c.head_dim
        qg, k, v = self.project(ops, x)
        qg = ops.reshape(qg, (B, T, H, 2 * D))
        q = qg[..., :D]
        gate = qg[..., D:]
        k = ops.reshape(k, (B, T, KV, D))
        v = ops.reshape(v, (B, T, KV, D))
        q = ops.transpose(ops.rms_norm(q, self.q_norm, c.rms_eps), (0, 2, 1, 3))  # [B,H,T,D]
        k = ops.transpose(ops.rms_norm(k, self.k_norm, c.rms_eps), (0, 2, 1, 3))  # [B,KV,T,D]
        v = ops.transpose(v, (0, 2, 1, 3))
        q = ops.rope_with(q, cos, sin)
        k = ops.rope_with(k, cos, sin)
        kbuf, vbuf = state
        for i in range(T):
            kbuf = ops.kv_write(kbuf, pos + i, k[:, :, i:i + 1])
            vbuf = ops.kv_write(vbuf, pos + i, v[:, :, i:i + 1])
        o = ops.sdpa_static(q, kbuf, vbuf, pos, ar, self.scale)  # [B,H,T,D]
        o = ops.reshape(ops.transpose(o, (0, 2, 1, 3)), (B, T, H * D))
        o = o * ops.cast(ops.sigmoid(ops.f32(ops.reshape(gate, (B, T, H * D)))), o.dtype)
        return ops.linear(o, self.wo), (kbuf, vbuf)


class GatedDeltaNet:
    def __init__(self, cfg: Qwen35Config, p: dict[str, Weight]) -> None:
        self.cfg = cfg
        self.w_qkvz = p.get('in_proj_qkvz')  # fused [qkv | z] when the loader provides it
        self.w_qkv = p.get('in_proj_qkv')
        self.w_z = p.get('in_proj_z')
        # the two low-rank [n_v, hidden] projections are fused into one [2 n_v, hidden] matmul when the loader provides
        # it (see from_source); separate weights are still accepted
        self.w_ab = p.get('in_proj_ab')
        self.w_a = p.get('in_proj_a')
        self.w_b = p.get('in_proj_b')
        self.conv_w = p['conv1d']  # [conv_dim, K] float32
        self.A = p['A']  # [n_v] == -exp(A_log), float32
        self.dt_bias = p['dt_bias']  # [n_v] float32
        self.norm_w = p['norm']
        self.w_out = p['out_proj']

    def __call__(
            self,
            ops: Ops,
            x: Array,
            state: LinearState | None,
            all_states: bool = False,
    ) -> tuple[Array, LinearState]:
        """
        With all_states the returned pair is stacked per token -- conv [T, B, C, K-1], S [T, B, H, dk, dv] -- so a
        speculative verify can keep the state after exactly the accepted prefix (the KV side needs no rollback: stale
        positions are masked by `pos`).
        """

        c = self.cfg
        B, T, _ = x.shape
        Hk = c.num_k_heads
        Hv = c.num_v_heads
        dk = c.head_k_dim
        dv = c.head_v_dim
        K = c.conv_kernel
        f32 = ops.dtype('f32')
        if self.w_qkvz is not None:
            qkv, z = ops.split(ops.f32(ops.linear(x, self.w_qkvz)), [c.conv_dim, c.value_dim], -1)
        else:
            qkv = ops.f32(ops.linear(x, self.w_qkv))
            z = ops.f32(ops.linear(x, self.w_z))  # [B, T, value_dim]
        qkv = ops.transpose(qkv, (0, 2, 1))  # [B, conv_dim, T]
        if self.w_ab is not None:
            a, b = ops.split(ops.f32(ops.linear(x, self.w_ab)), [Hv, Hv], -1)  # [B, T, n_v] each
        else:
            a = ops.f32(ops.linear(x, self.w_a))  # [B, T, n_v]
            b = ops.f32(ops.linear(x, self.w_b))

        # causal depthwise conv1d over [history | new]
        hist = state[0] if state is not None else ops.zeros((B, c.conv_dim, K - 1), f32)
        inp = ops.concat([hist, qkv], -1)
        conv_state = inp[..., -(K - 1):]
        conv = ops.transpose(ops.silu(ops.conv1d_causal(inp, self.conv_w)), (0, 2, 1))  # [B, T, conv_dim]
        q, k, v = ops.split(conv, [c.key_dim, c.key_dim, c.value_dim], -1)
        S = state[1] if state is not None else ops.zeros((B, Hv, dk, dv), f32)
        if all_states:
            conv_state = ops.stack([inp[..., t + 1:t + K] for t in range(T)], 0)  # [T, B, C, K-1]
        if T <= ops.gdn_fused_max_t:
            # decode / verify: one op from the raw projections (fusable into a single kernel per layer)
            out, S = ops.gdn_step(
                ops.reshape(q, (B, T, Hk, dk)),
                ops.reshape(k, (B, T, Hk, dk)),
                ops.reshape(v, (B, T, Hv, dv)),
                a,
                b,
                self.A,
                self.dt_bias,
                S,
                all_states,
                c.rms_eps,
            )  # out: [B,T,Hv,dv]; S: [B,Hv,dk,dv] or [T,B,Hv,dk,dv]
        else:
            # prefill: normalise, broadcast heads, chunked recurrence
            q = ops.transpose(ops.l2_norm(ops.reshape(q, (B, T, Hk, dk)), c.rms_eps), (0, 2, 1, 3)) * (dk**-0.5)
            k = ops.transpose(ops.l2_norm(ops.reshape(k, (B, T, Hk, dk)), c.rms_eps), (0, 2, 1, 3))  # [B,Hk,T,dk]
            v = ops.transpose(ops.reshape(v, (B, T, Hv, dv)), (0, 2, 1, 3))  # [B,Hv,T,dv]
            if Hv != Hk:  # canonical grouped V order -> repeat_interleave (llama.cpp's tiled order would tile)
                q = ops.repeat(q, Hv // Hk, 1)
                k = ops.repeat(k, Hv // Hk, 1)
            beta = ops.transpose(ops.sigmoid(b), (0, 2, 1))  # [B,Hv,T]
            g = ops.transpose(self.A[None, None, :] * ops.softplus(a + self.dt_bias), (0, 2, 1))  # <= 0
            if all_states:
                out, S = ops.gated_delta_states(q, k, v, g, beta, S)
            else:
                out, S = ops.gated_delta(q, k, v, g, beta, S)
            out = ops.transpose(out, (0, 2, 1, 3))  # [B,T,Hv,dv]

        z = ops.reshape(z, (B, T, Hv, dv))
        out = ops.rms_norm(out, self.norm_w, c.rms_eps) * ops.silu(z)  # gated RMSNorm
        y = ops.linear(ops.cast(ops.reshape(out, (B, T, c.value_dim)), x.dtype), self.w_out)
        return y, (conv_state, S)


class MLP:
    def __init__(self, p: dict[str, Weight]) -> None:
        self.wgu = p.get('gate_up_proj')  # fused [2 ff, hidden] when the loader provides it
        self.wg = p.get('gate_proj')
        self.wu = p.get('up_proj')
        self.wd = p['down_proj']

    def __call__(self, ops: Ops, x: Array) -> Array:
        if self.wgu is not None:
            gu = ops.linear(x, self.wgu)
            g, u = ops.split(gu, [gu.shape[-1] // 2, gu.shape[-1] // 2], -1)
        else:
            g, u = ops.linear(x, self.wg), ops.linear(x, self.wu)
        return ops.linear(ops.silu(g) * u, self.wd)


class Block:
    def __init__(self, cfg: Qwen35Config, index: int, kind: str, p: dict[str, Weight]) -> None:
        self.index = index
        self.kind = kind
        self.ln1 = p['input_layernorm']
        self.ln2 = p['post_attention_layernorm']
        self.eps = cfg.rms_eps
        self.mixer: Attention | GatedDeltaNet = Attention(cfg, p) if kind == 'full' else GatedDeltaNet(cfg, p)
        self.mlp = MLP(p)

    def __call__(self, ops: Ops, x: Array, pos: int, state: ta.Any) -> tuple[Array, ta.Any]:
        h = ops.rms_norm(x, self.ln1, self.eps)
        if self.kind == 'full':
            m, state = ta.cast(Attention, self.mixer)(ops, h, pos, state)
        else:
            m, state = ta.cast(GatedDeltaNet, self.mixer)(ops, h, state)
        ops.tap(f'layers.{self.index}.mixer', m)
        x = x + m
        x = x + self.mlp(ops, ops.rms_norm(x, self.ln2, self.eps))
        ops.tap(f'layers.{self.index}.out', x)
        return x, state

    def decode(
            self,
            ops: Ops,
            x: Array,
            pos: Array,
            ar: Array,
            cos: Array,
            sin: Array,
            state: ta.Any,
            all_states: bool = False,
    ) -> tuple[Array, ta.Any]:
        """Static-shape step for T tokens (no taps: a captured step cannot leave the device)."""

        h = ops.rms_norm(x, self.ln1, self.eps)
        if self.kind == 'full':
            m, state = ta.cast(Attention, self.mixer).decode(ops, h, pos, ar, cos, sin, state)
        else:
            m, state = ta.cast(GatedDeltaNet, self.mixer)(ops, h, state, all_states)  # T tokens: fixed-shape
        x = x + m
        x = x + self.mlp(ops, ops.rms_norm(x, self.ln2, self.eps))
        return x, state


##
# Model


def required_param_names(cfg: Qwen35Config) -> list[str]:
    names = ['embed_tokens.weight', 'norm.weight']
    for i, kind in enumerate(cfg.layer_types):
        q = f'layers.{i}.'
        names += [
            q + 'input_layernorm.weight',
            q + 'post_attention_layernorm.weight',
            q + 'mlp.gate_proj.weight',
            q + 'mlp.up_proj.weight',
            q + 'mlp.down_proj.weight',
        ]
        if kind == 'full':
            names += [
                q + f'self_attn.{n}.weight'
                for n in (
                    'q_proj',
                    'k_proj',
                    'v_proj',
                    'o_proj',
                    'q_norm',
                    'k_norm',
                )
            ]
        else:
            names += [
                q + f'linear_attn.{n}.weight'
                for n in (
                    'in_proj_qkv',
                    'in_proj_z',
                    'in_proj_a',
                    'in_proj_b',
                    'conv1d',
                    'norm',
                    'out_proj',
                )
            ]
            names += [q + 'linear_attn.A', q + 'linear_attn.dt_bias']
    return names


def mtp_param_names() -> list[str]:
    """The one-layer draft head: stem, a full-attention block (text geometry, private weights), final norm."""

    q = 'mtp.layers.0.'
    names = [
        'mtp.fc.weight',
        'mtp.pre_fc_norm_embedding.weight',
        'mtp.pre_fc_norm_hidden.weight',
        'mtp.norm.weight',
        q + 'input_layernorm.weight',
        q + 'post_attention_layernorm.weight',
        q + 'mlp.gate_proj.weight',
        q + 'mlp.up_proj.weight',
        q + 'mlp.down_proj.weight',
    ]
    names += [
        q + f'self_attn.{n}.weight'
        for n in (
            'q_proj',
            'k_proj',
            'v_proj',
            'o_proj',
            'q_norm',
            'k_norm',
        )
    ]
    return names


# tensors that stay in float32 whatever the compute dtype
KEEP_F32 = (
    'norm',
    'linear_attn.A',
    'dt_bias',
    'conv1d',
)

# 2-D weights that are never quantized: the low-rank DeltaNet projections are quantization-sensitive (Ollama's own
# converter also keeps them at source precision)
NO_QUANT = (
    'in_proj_a',
    'in_proj_b',
)


# Projections that share an input are loaded as one weight stacked along the output dim: one GEMV launch instead of two
# or three, and a wider N streams better. (fused suffix, part suffixes, bits override). The a/b pair is kept separate
# from qkv/z because it is stored at int8 whatever the model's width.
FUSIONS: tuple[tuple[str, tuple[str, ...], int | None], ...] = (
    (
        'mlp.gate_up_proj.weight',
        ('mlp.gate_proj.weight', 'mlp.up_proj.weight'),
        None,
    ),
    (
        'self_attn.qkv_proj.weight',
        ('self_attn.q_proj.weight', 'self_attn.k_proj.weight', 'self_attn.v_proj.weight'),
        None,
    ),
    (
        'linear_attn.in_proj_qkvz.weight',
        ('linear_attn.in_proj_qkv.weight', 'linear_attn.in_proj_z.weight'),
        None,
    ),
    (
        'linear_attn.in_proj_ab.weight',
        ('linear_attn.in_proj_a.weight', 'linear_attn.in_proj_b.weight'),
        8,
    ),
)


def fusion_of(name: str) -> tuple[str, list[str], int | None] | None:
    """For a canonical part name, the (fused name, all part names, bits override) it belongs to."""

    for fused, parts, fbits in FUSIONS:
        for part in parts:
            if name.endswith(part):
                prefix = name[: -len(part)]
                return prefix + fused, [prefix + p for p in parts], fbits
    return None


def is_quantizable(name: str, shape: tuple[int, ...], group: int) -> bool:
    if len(shape) != 2 or shape[1] % group:
        return False
    return not any(s in name for s in KEEP_F32 + NO_QUANT)


class Qwen35:
    def __init__(
            self,
            cfg: Qwen35Config,
            params: dict[str, Weight],
            ops: Ops,
            dtype: ta.Any,
    ) -> None:
        self.cfg = cfg
        self.ops = ops
        self.dtype = dtype
        self.nbytes = sum(ops.nbytes(p) for p in params.values())
        self.last_spec: SpecDecoder | None = None  # the most recent generate(spec=k)'s decoder, for its stats
        self.last_prefix: tuple[int, int] = (0, 0)  # (prompt tokens reused from the prefix cache, prompt length)
        self._steps: dict[tuple[int, bool, bool], ta.Callable[..., tuple[Array, ...]]] = {}  # see step_fn
        self.embed = params['embed_tokens.weight']
        self.norm_w = params['norm.weight']
        self.lm_head = params.get('lm_head.weight', self.embed)
        self.blocks: list[Block] = [
            Block(cfg, i, kind, block_params(params, f'layers.{i}.'))
            for i, kind in enumerate(cfg.layer_types)
        ]
        self.mtp: MtpHead | None = MtpHead(self, params) if 'mtp.fc.weight' in params else None

    # loading

    @classmethod
    def from_source(
        cls,
        src: TensorSource,
        ops: Ops,
        dtype: str = 'bf16',
        quant: str | None = None,
        group: int = 64,
        verbose: bool = True,
        mtp: bool = False,
        cache_dir: str | pathlib.Path | None = None,
    ) -> Qwen35:
        """
        dtype: 'bf16' | 'f16' | 'f32' (compute dtype; norms, A, dt_bias, conv stay f32).
        quant: None, 'int8' or 'int4' (weight-only affine, see quant.py). If the source already holds MLX-quantized
               tensors at the requested width they are re-packed as-is; otherwise weights are quantized.
        mtp:   also load the multi-token-prediction draft head (needs `num_mtp_layers >= 1` in the source).
        cache_dir: keep the finished parameters on disk there (see paramcache.py); the first load fills it, later ones
                   memory-map it and skip the GGUF dequantization entirely.
        """

        cfg = src.config
        if cfg.rope_scaling:
            print(
                f'[model] WARNING: rope_scaling={cfg.rope_scaling} present; only plain RoPE is implemented '
                f'(fine for prompts within the original context length)',
            )
        if quant is not None and quant not in QUANT_BITS:
            raise ValueError(f'quant must be one of {list(QUANT_BITS)}, got {quant!r}')
        bits = QUANT_BITS[quant] if quant else None
        dt = ops.dtype(dtype)
        f32 = ops.dtype('f32')
        params: dict[str, Weight] = {}
        available = set(src.names())
        names = required_param_names(cfg)
        if mtp:
            if not cfg.num_mtp_layers:
                raise ValueError('this source has no MTP head')
            names += mtp_param_names()
        missing = [n for n in names if n not in available]
        if missing:
            raise KeyError(f'source is missing {len(missing)} tensors, e.g. {missing[:5]}')
        if 'lm_head.weight' in available and not cfg.tied_embeddings:
            names.append('lm_head.weight')
        cache = ParamCache.open(cache_dir, src, quant, group) if cache_dir is not None else None
        n_native = n_quant = 0
        for n_i, name in enumerate(names):
            p: Weight | None = None
            keep_f32 = any(s in name for s in KEEP_F32)
            fusion = fusion_of(name)
            if fusion is not None:
                fused_name, parts, fbits = fusion
                if fused_name in params:
                    continue
                if all(pn in available for pn in parts):
                    fb = None if bits is None else (fbits or bits)
                    params[fused_name] = cls._load_fused(src, ops, cache, fused_name, parts, fb, group, dt)
                    if fb is not None:
                        n_quant += 1
                    continue
                # a part without its siblings (unusual source): fall through and load it on its own
            cached = cache.get(name) if cache is not None else None
            if isinstance(cached, QWeight):
                p = ops.qweight(cached, dt)
            elif cached is not None:
                p = ops.weight(cached, f32 if keep_f32 else dt)
            if p is None and bits is not None and not keep_f32 and not any(s in name for s in NO_QUANT):
                nq = src.get_quant(name)
                if nq is not None and nq.bits == bits:
                    qw = from_native(nq.values, nq.scale, nq.bias, nq.bits, nq.group)
                    if cache is not None:
                        cache.put(name, qw)
                    p = ops.qweight(qw, dt)
                    n_native += 1
            if p is None:
                arr = np.array(src.get(name), dtype=np.float32, copy=True)
                if keep_f32:
                    if cache is not None:
                        cache.put(name, arr)
                    p = ops.weight(arr, f32)
                elif bits is not None and is_quantizable(name, arr.shape, group):
                    if cache is not None:
                        try:  # quantize on the device (fast) and export; fall back to the numpy quantizer
                            p = ops.quantize(arr, bits, group, dt)
                            qw = ops.export_qweight(p)
                        except NotImplementedError:
                            qw = quantize_np(arr, bits, group)
                            p = ops.qweight(qw, dt)
                        cache.put(name, qw)
                    else:
                        p = ops.quantize(arr, bits, group, dt)
                    n_quant += 1
                else:
                    if cache is not None:
                        cache.put(name, arr)
                    p = ops.weight(arr, dt)
            params[name] = p
            if verbose and (n_i % 50 == 0 or n_i == len(names) - 1):
                print(f'\r[model] loading tensors {n_i + 1}/{len(names)}', end='', flush=True)
        model = cls(cfg, params, ops, dt)
        if verbose:
            q_note = f', {n_native} re-packed + {n_quant} quantized to {quant}' if bits else ''
            c_note = f'; cache {cache.root}: {cache.hits} hit / {cache.misses} miss' if cache is not None else ''
            print(f'\n[model] {model.nbytes / 2**30:.2f} GiB of weights on {ops.name}{q_note}{c_note}')
        return model

    @staticmethod
    def _load_fused(src, ops, cache, fused_name, parts, fbits, group, dt) -> Weight:
        """
        Load `parts`, stack them along the output dim, quantize (fbits) or adopt dense; cached under the fused name.
        Sources that hold the parts already quantized at the same width are re-packed row-wise without requantization.
        """

        cached = cache.get(fused_name) if cache is not None else None
        if isinstance(cached, QWeight):
            return ops.qweight(cached, dt)
        if cached is not None:
            return ops.weight(cached, dt)
        if fbits is not None:
            natives = [src.get_quant(pn) for pn in parts]
            if all(nq is not None and nq.bits == fbits and nq.group == group for nq in natives):
                qw = from_native(
                    np.concatenate([nq.values for nq in natives], 0),
                    np.concatenate([nq.scale for nq in natives], 0),
                    np.concatenate([nq.bias for nq in natives], 0),
                    fbits,
                    group,
                )
                if cache is not None:
                    cache.put(fused_name, qw)
                return ops.qweight(qw, dt)
        arr = np.concatenate([np.asarray(src.get(pn), dtype=np.float32) for pn in parts], 0)
        if fbits is not None and arr.ndim == 2 and arr.shape[1] % group == 0:  # (NO_QUANT is about int4; fbits decides)
            if cache is not None:
                try:
                    p = ops.quantize(arr, fbits, group, dt)
                    qw = ops.export_qweight(p)
                except NotImplementedError:
                    qw = quantize_np(arr, fbits, group)
                    p = ops.qweight(qw, dt)
                cache.put(fused_name, qw)
                return p
            return ops.quantize(arr, fbits, group, dt)
        if cache is not None:
            cache.put(fused_name, arr)
        return ops.weight(arr, dt)

    # forward

    def prefill(
            self,
            tokens: ta.Sequence[int],
            cache: Cache,
            chunk: int = 4096,
            should_stop: ta.Callable[[], bool] | None = None,
    ) -> tuple[Array, Array]:
        """
        `forward` over a prompt in chunks of `chunk` tokens through the growing cache, so activation memory (the
        [T, intermediate] tensors, ~35 KB per token for the 27B) stays bounded whatever the prompt length, and a
        cancellation (`should_stop`) has somewhere to land. Returns the last position's logits [B, 1, V] and the
        final-normed hidden states of every position [B, T, hidden].
        """

        ops = self.ops
        toks = np.asarray(tokens, dtype=np.int32).reshape(1, -1)
        T = toks.shape[1]
        hiddens: list[Array] = []
        logits = None
        for start in range(0, T, max(1, chunk)):
            if should_stop is not None and should_stop():
                raise Cancelled
            logits, h = self.forward(toks[:, start:start + chunk], cache, return_hidden=True)
            hiddens.append(h)
        return (
            check.not_none(logits)[:, -1:],
            (hiddens[0] if len(hiddens) == 1 else ops.concat(hiddens, 1)),
        )

    def forward(
        self,
        tokens: np.ndarray,
        cache: Cache | None = None,
        start_pos: int | None = None,
        last_only: bool = False,
        return_hidden: bool = False,
    ) -> ta.Any:
        """
        tokens: [B, T] ints. Returns logits [B, T, V] (or [B, 1, V] with last_only) in float32; with
        return_hidden also the final-normed hidden states [B, T, hidden] (what the MTP head conditions on).
        """

        ops = self.ops
        c = self.cfg
        tokens = np.asarray(tokens, dtype=np.int32)
        B, T = tokens.shape
        if start_pos is None:
            start_pos = cache.seq_len if cache is not None else 0
        x = ops.embedding(ops.array(tokens), self.embed, self.dtype)
        ops.tap('embed', x)
        for i, blk in enumerate(self.blocks):
            x, st = blk(ops, x, start_pos, cache.layers[i] if cache is not None else None)
            if cache is not None:
                cache.layers[i] = st
        if cache is not None:
            cache.seq_len = start_pos + T
        if last_only:
            x = x[:, -1:]
        x = ops.rms_norm(x, self.norm_w, c.rms_eps)
        ops.tap('final_norm', x)
        logits = ops.f32(ops.linear(x, self.lm_head))
        ops.tap('logits', logits)
        if return_hidden:
            return logits, x
        return logits

    def step_fn(
            self,
            T: int,
            all_states: bool = False,
            return_hidden: bool = False,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        The static T-token step: `fn(toks, pos, ar, cos_tab, sin_tab, *flat_state) -> (logits, [hidden,] *flat_state)`.

        toks: [B, T] int at positions pos..pos+T-1; pos: 0-d int; ar: arange(capacity); cos_tab, sin_tab: [capacity,
        rope_dim]; flat_state: two arrays per layer (kbuf, vbuf) or (conv, S). Everything is an argument (no closed-over
        tensors) so one compiled function serves every Decoder with the same shapes; nothing in the step may allocate
        from the host. Returns logits [B, T, V] float32 (and, with return_hidden, the final-normed hidden [B, T, hidden]
        the draft head conditions on); with all_states the DeltaNet entries come back stacked per token. Pure apart from
        `kv_write`, so a backend may capture it. T == 1 is decode; T == k + 1 with all_states is speculative verify.
        Built (and `Ops.compile_fn`ed) once per (T, all_states, return_hidden) and cached on the model.
        """

        key = (T, all_states, return_hidden)
        fn = self._steps.get(key)
        if fn is None:
            fn = self._steps[key] = self.ops.compile_fn(self._build_step(T, all_states, return_hidden))
        return fn

    def _build_step(self, T: int, all_states: bool, return_hidden: bool) -> ta.Callable[..., tuple[Array, ...]]:
        ops, c = self.ops, self.cfg

        def fn(toks, pos, ar, cos_tab, sin_tab, *flat):
            # index with a 1-element array, not the 0-d one: torch turns a 0-d tensor index into `.item()`, a
            # device->host sync that is illegal inside a CUDA graph capture; a 1-d index is a plain gather
            rows = ops.reshape(pos, (1,)) + ar[:T]
            cos = cos_tab[rows]  # [T, rope_dim]
            sin = sin_tab[rows]
            x = ops.embedding(toks, self.embed, self.dtype)
            out: list[Array] = []
            for i, blk in enumerate(self.blocks):
                x, st = blk.decode(ops, x, pos, ar, cos, sin, (flat[2 * i], flat[2 * i + 1]), all_states)
                out.extend(st)
            x = ops.rms_norm(x, self.norm_w, c.rms_eps)
            logits = ops.f32(ops.linear(x, self.lm_head))
            if return_hidden:
                return (logits, x, *out)
            return (logits, *out)

        return fn

    def decode_fn(self) -> ta.Callable[..., tuple[Array, ...]]:
        """
        The single-token step: `fn(tok, pos, ar, cos_tab, sin_tab, *flat_state) -> (logits [B, 1, V], *flat_state)`.
        """

        return self.step_fn(1)

    def generate(
        self,
        prompt_ids: list[int],
        max_new_tokens: int = 64,
        eos_ids: set[int] | None = None,
        on_token: ta.Callable[[int], None] | None = None,
        static: bool = True,
        sampler: Sampler | None = None,
        spec: int = 0,
        capacity: int | None = None,
        draft_vocab: int = 0,
        prefix_cache: PrefixCache | None = None,
        prefill_chunk: int = 4096,
        should_stop: ta.Callable[[], bool] | None = None,
    ) -> list[int]:
        """
        Generation. Prefill goes through `forward` (chunked); decode then runs the captured static step (`static=True`,
        the fast path) or keeps growing the functional cache (`static=False`, the reference). `sampler` defaults to
        greedy. `spec=k` (needs the MTP head loaded) drafts k tokens per round with the draft head and verifies them in
        one target step. `capacity` pins the decode buffers' length (rounded up to a power of two); the captured /
        compiled steps are specific to it, so callers that want to reuse them across generations -- a warm-up, a server
        -- should pass the same value every time. Default: just enough for this call. With a `prefix_cache`, the longest
        cached snapshot whose tokens are a prefix of the prompt is resumed and only the rest is prefilled, and the state
        after the prompt and after the generation are stored for later requests (see prefixcache.py); `self.last_prefix`
        reports (matched, prompt length). The prompt is prefilled `prefill_chunk` tokens at a time. `should_stop`,
        polled between prefill chunks and decode rounds, raises `Cancelled` when it returns True; `on_token` may raise
        it too. Yields token ids through on_token as they are produced.
        """

        capacity = max(capacity or 0, len(prompt_ids) + max_new_tokens + spec + 2)

        ops = self.ops
        sampler = sampler or Sampler()
        sampler.bind(ops, self.cfg.vocab_size)
        n = len(prompt_ids)
        snap = prefix_cache.lookup(prompt_ids) if prefix_cache is not None else None
        mtp_kv: FullState | None = None
        if snap is not None:
            # resume: the snapshot's cache is a private copy; prefill only the tokens past it
            cache = snap.cache
            n0 = snap.n
            self.last_prefix = (n0, n)
            if n0 < n:
                logits, hidden_new = self.prefill(prompt_ids[n0:], cache, prefill_chunk, should_stop)
                hidden = ops.concat([snap.hidden, hidden_new], 1)  # positions n0-1 .. n-1
            else:
                logits = ops.reshape(snap.logits, (1, 1, -1))
                hidden = snap.hidden  # position n-1
            start = n0 - 1  # position of hidden's first row
            mtp_kv = snap.mtp_kv  # entries 0..n0-2, or None
        else:
            self.last_prefix = (0, n)
            cache = Cache(self.cfg)
            logits, hidden = self.prefill(prompt_ids, cache, prefill_chunk, should_stop)
            start = 0
        if prefix_cache is not None or spec:
            if self.mtp is not None and n - 1 > start:
                # bring the draft head's KV up to entry n-2 (entry p: hidden at p, token at p+1)
                _, _, mtp_kv = self.mtp.prefill(
                    np.asarray([prompt_ids[start + 1:n]], dtype=np.int32),
                    hidden[:, :n - 1 - start],
                    start,
                    draft_vocab,
                    mtp_kv,
                )
        if prefix_cache is not None:
            prefix_cache.put(Snapshot(
                tuple(int(t) for t in prompt_ids),
                cache.snapshot(ops),
                ops.copy(logits[:, -1]),
                ops.copy(hidden[:, -1:]),
                None if mtp_kv is None else (ops.copy(mtp_kv[0]), ops.copy(mtp_kv[1])),
            ))
        out: list[int] = []

        def emit(tok: int) -> bool:
            out.append(tok)
            if on_token:
                on_token(tok)
            return bool(eos_ids and tok in eos_ids)

        if spec:
            if self.mtp is None:
                raise ValueError('spec decoding needs the MTP head (from_source(..., mtp=True))')
            spec_dec = SpecDecoder(
                self,
                cache,
                prompt_ids,
                logits,
                hidden[:, -1:],
                k=spec,
                sampler=sampler,
                capacity=capacity,
                draft_vocab=draft_vocab,
                mtp_kv=mtp_kv,
            )
            self.last_spec = spec_dec
            processed: list[int] = []  # every committed token, including any past an EOS / the budget
            while len(out) < max_new_tokens:
                if should_stop is not None and should_stop():
                    raise Cancelled
                committed = spec_dec.round()
                processed.extend(committed)
                stop = False
                for tok in committed:
                    if emit(tok) or len(out) >= max_new_tokens:
                        stop = True
                        break
                if stop:
                    break
            if prefix_cache is not None:
                prefix_cache.put(spec_dec.snapshot(list(prompt_ids) + processed))
            return out

        dec = Decoder(self, cache, capacity=capacity) if static else None

        def draw(row: Array) -> int:  # row: [1, V] on the device -> one token id; only that id leaves the device
            t = sampler.sample(row)
            sampler.observe(t)
            return int(ops.numpy(t)[0])

        nxt = draw(logits[:, -1])
        for _ in range(max_new_tokens):
            if emit(nxt):
                break
            if should_stop is not None and should_stop():
                raise Cancelled
            if dec is not None:
                nxt = draw(dec.step(nxt))
            else:
                nxt = draw(self.forward(np.array([[nxt]]), cache, last_only=True)[:, -1])
        if prefix_cache is not None and dec is not None and dec.seq_len > n:
            prefix_cache.put(dec.snapshot_after(list(prompt_ids) + out))
        return out


##
# Draft head


class MtpHead:
    """
    Qwen3.5's multi-token-prediction head (the `nextn` block of the GGUF, `mtp.*` in HF): given the target's
    final-normed hidden state at position p and the token at p+1, it predicts the token at p+2 --

        e = rmsnorm(embed(x_{p+1}), pre_fc_norm_embedding)
        h = rmsnorm(h_p, pre_fc_norm_hidden)
        u = fc(concat(e, h))                       # embedding first, hidden second
        u = one gated-attention block (text geometry, private weights, private KV)
        d = rmsnorm(u, norm);  logits = lm_head(d)  # the target's output head

    and can recurse, feeding its own normed output `d` back in as the next hidden. All norm weights are stored with the
    +1 already applied, like the text model's. The block runs through `Block.decode` on its own KV buffers (positions
    are the hidden's position).
    """

    def __init__(self, model: Qwen35, params: dict[str, Weight]) -> None:
        self.model = model
        self.cfg = model.cfg
        self.fc = params['mtp.fc.weight']
        self.enorm = params['mtp.pre_fc_norm_embedding.weight']
        self.hnorm = params['mtp.pre_fc_norm_hidden.weight']
        self.norm_w = params['mtp.norm.weight']
        self.block = Block(self.cfg, self.cfg.num_layers, 'full', block_params(params, 'mtp.layers.0.'))
        self._steps: dict[tuple[int, int], ta.Callable[..., tuple[Array, ...]]] = {}
        self._heads: dict[int, Weight] = {}

    def stem(self, ops: Ops, toks: Array, hidden: Array) -> Array:
        c = self.cfg
        m = self.model
        e = ops.rms_norm(ops.embedding(toks, m.embed, m.dtype), self.enorm, c.rms_eps)
        h = ops.rms_norm(ops.cast(hidden, m.dtype), self.hnorm, c.rms_eps)
        return ops.linear(ops.concat([e, h], -1), self.fc)

    def head(self, ops: Ops, u: Array, draft_vocab: int = 0) -> tuple[Array, Array]:
        """
        Final norm + output head. draft_vocab > 0 restricts the head to the first that many vocabulary ids: Qwen's BPE
        ids are roughly in merge-frequency order, so the first 32-64k cover almost every token the target will pick
        while costing a fraction of the 248k-row matmul (ninfer's `--lm-head-draft`).
        """

        c = self.cfg
        m = self.model
        d = ops.rms_norm(u, self.norm_w, c.rms_eps)
        head = m.lm_head
        if draft_vocab:
            key = draft_vocab
            head = self._heads.get(key)
            if head is None:
                head = self._heads[key] = ops.head_rows(m.lm_head, draft_vocab)
        return ops.f32(ops.linear(d, head)), d

    def prefill(
            self,
            toks: np.ndarray,
            hidden: Array,
            pos: int = 0,
            draft_vocab: int = 0,
            state: FullState | None = None,
    ) -> tuple[Array, Array, FullState]:
        """
        Functional (growing-cache) pass over T entries: toks [B, T] are the tokens at positions pos+1..pos+T, hidden [B,
        T, H] the target's hidden states at pos..pos+T-1, `state` the head's KV for entries 0..pos-1 (None to start
        empty). Returns logits, d, (k, v) covering entries 0..pos+T-1.
        """

        ops = self.model.ops
        u = self.stem(ops, ops.array(np.asarray(toks, dtype=np.int32)), hidden)
        u, state = self.block(ops, u, pos, state)
        logits, d = self.head(ops, u, draft_vocab)
        return logits, d, state

    def step_fn(self, T: int, draft_vocab: int = 0) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Static T-entry step: `fn(toks [B,T], hidden [B,T,H], pos, ar, cos_tab, sin_tab, kbuf, vbuf) -> (logits, d, kbuf,
        vbuf)`; built and compiled once per (T, draft_vocab), cached on the head. With draft_vocab the logits cover only
        the first that many ids (see `head`).
        """

        key = (T, draft_vocab)
        fn = self._steps.get(key)
        if fn is None:
            ops = self.model.ops

            def raw(toks, hidden, pos, ar, cos_tab, sin_tab, kbuf, vbuf):
                rows = ops.reshape(pos, (1,)) + ar[:T]
                u = self.stem(ops, toks, hidden)
                u, (kbuf, vbuf) = self.block.decode(ops, u, pos, ar, cos_tab[rows], sin_tab[rows], (kbuf, vbuf))
                logits, d = self.head(ops, u, draft_vocab)
                return logits, d, kbuf, vbuf

            fn = self._steps[key] = ops.compile_fn(raw)
        return fn


def block_params(params: dict[str, Weight], prefix: str) -> dict[str, Weight]:
    """Collapse "prefix.self_attn.q_proj.weight" -> "q_proj", "prefix.linear_attn.A" -> "A", ..."""

    p = {}
    for k, v in params.items():
        if k.startswith(prefix):
            parts = k[len(prefix):].split('.')
            if parts[-1] == 'weight':
                parts = parts[:-1]
            p[parts[-1]] = v
    return p


##
# Sampling


class Sampler:
    """
    Sampling on the device: temperature -> presence/frequency penalties -> top-k -> top-p -> min-p -> Gumbel-max draw,
    all as `Ops` calls on a [T, V] float32 logits array, so what leaves the device is T token ids. temperature <= 0 is
    greedy (an argmax) and ignores the rest. Qwen's published presets: thinking t=1.0 top-p=0.95 top-k=20; non-thinking
    t=0.7 top-p=0.8 top-k=20 presence=1.5.

    top-p and min-p are applied among the top-k candidates (top-k must be > 0 for them; with top-k=0 they sort the whole
    vocabulary). The penalties read a device histogram of the tokens `observe`d so far; rows sampled in one call share
    that state, which for speculative verify means a round's k+1 draws see the histogram as of the round's start. `seed`
    seeds the backend's generator, so the stream differs between backends.
    """

    def __init__(
            self,
            temperature: float = 0.0,
            top_k: int = 0,
            top_p: float = 1.0,
            min_p: float = 0.0,
            presence_penalty: float = 0.0,
            frequency_penalty: float = 0.0,
            seed: int = 0,
    ) -> None:
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.min_p = min_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.seed = seed
        self.ops: Ops | None = None
        self.counts: Array | None = None  # [V] float32 histogram of observed tokens

    @property
    def greedy(self) -> bool:
        return self.temperature <= 0

    @property
    def penalized(self) -> bool:
        return bool(self.presence_penalty or self.frequency_penalty)

    def bind(self, ops: Ops, vocab: int) -> None:
        if self.ops is not ops:
            self.ops = ops
            ops.seed(self.seed)
            self.counts = ops.zeros((vocab,), ops.dtype('f32'))

    def observe(self, toks: Array) -> None:
        """Record generated tokens (a 1-d int array on the device) for the penalties."""

        if self.penalized and self.ops is not None and self.counts is not None:
            self.counts = self.ops.index_add(self.counts, toks, self.ops.zeros(toks.shape, self.counts.dtype) + 1)

    def sample(self, logits: Array) -> Array:
        """logits [T, V] float32 on the device -> [T] int32 token ids on the device."""

        ops = self.ops
        if ops is None:
            raise RuntimeError('bind() first')
        T, V = logits.shape
        if self.greedy:
            return ops.argmax(logits, -1)
        l = logits
        if self.penalized and self.counts is not None:
            pen = self.presence_penalty * ops.cast(self.counts > 0, l.dtype) + self.frequency_penalty * self.counts
            l = l - pen[None, :]
        k = self.top_k if 0 < self.top_k < V else V
        vals, idx = ops.topk(l, k)  # [T, k] descending
        z = vals / self.temperature
        p = ops.softmax(z, -1)
        keep = ops.cast(ops.cumsum(p, -1) - p < self.top_p, z.dtype) if self.top_p < 1.0 else None
        if self.min_p > 0:
            km = ops.cast(p >= self.min_p * ops.amax(p, -1, keepdims=True), z.dtype)
            keep = km if keep is None else keep * km
        if keep is not None:
            z = z + (1 - keep) * -1e30
        # Gumbel-max: argmax(z + g), g = -log(-log(u)), is a draw from softmax(z)
        u = ops.random_uniform((T, k))
        g = -ops.log(-ops.log(u * (1 - 2e-7) + 1e-7))
        choice = ops.argmax(z + g, -1)  # [T] index into the k candidates
        oh = ops.cast(ops.arange(k)[None, :] == choice[:, None], ops.dtype('f32'))
        return ops.cast(ops.sum(ops.cast(idx, ops.dtype('f32')) * oh, -1) + 0.5, ops.dtype('i32'))

    def probs(self, logits: Array) -> Array:
        """
        The distribution `sample` draws from, materialised over the whole vocabulary: [T, V] float32 rows that sum to 1,
        zero outside the kept set. Every truncation (top-k, top-p, min-p) is a per-row threshold on the tempered logits,
        so this is a topk on the candidates to find the threshold, then one masked softmax. Greedy is a one-hot row.
        Speculative verify compares the target's and the draft head's versions of this.
        """

        ops = self.ops
        if ops is None:
            raise RuntimeError('bind() first')
        T, V = logits.shape
        f32 = ops.dtype('f32')
        if self.greedy:
            mx = ops.amax(logits, -1, keepdims=True)
            return ops.softmax(logits + ops.cast(logits < mx, f32) * -1e30, -1)
        l = logits
        if self.penalized and self.counts is not None:
            pen = self.presence_penalty * ops.cast(self.counts > 0, l.dtype) + self.frequency_penalty * self.counts
            l = l - pen[None, :]
        l = l / self.temperature
        k = self.top_k if 0 < self.top_k < V else V
        vals, _ = ops.topk(l, k)  # [T, k] descending
        thr = vals[:, k - 1:k]  # the k-th largest: everything below it is out
        if self.top_p < 1.0:
            p = ops.softmax(vals, -1)
            keep = ops.cast(ops.cumsum(p, -1) - p < self.top_p, f32)
            thr_p = -ops.amax(-(vals + (1 - keep) * 1e30), -1, keepdims=True)  # smallest kept value
            thr = ops.amax(ops.stack([thr, thr_p], 0), 0)
        if self.min_p > 0:
            # p >= min_p * p_max <=> z >= z_max + ln min_p
            thr_m = ops.amax(vals, -1, keepdims=True) + math.log(self.min_p)
            thr = ops.amax(ops.stack([thr, thr_m], 0), 0)
        return ops.softmax(l + ops.cast(l < thr, f32) * -1e30, -1)

    def draw(self, probs: Array) -> Array:
        """One token per row of a [T, V] probability matrix (Gumbel-max over log p; zeros never win)."""

        ops = self.ops
        if ops is None:
            raise RuntimeError('bind() first')
        T, V = probs.shape
        u = ops.random_uniform((T, V))
        g = -ops.log(-ops.log(u * (1 - 2e-7) + 1e-7))
        return ops.argmax(ops.log(probs) + g, -1)

    @staticmethod
    def gather(ops: Ops, probs: Array, toks: Array) -> Array:
        """probs[i, toks[i]] for each row -> [T]."""

        V = probs.shape[1]
        oh = ops.cast(ops.arange(V)[None, :] == toks[:, None], probs.dtype)
        return ops.sum(probs * oh, -1)


def speculative_accept(
        ops: Ops,
        sampler: Sampler,
        p_rows: Array,
        q_rows: Array,
        drafts: Array,
        q_d: Array,
) -> tuple[Array, Array]:
    """
    The rejection-sampling step of speculative decoding (Leviathan et al. / Chen et al.). p_rows: [k+1, V], the target's
    warped distribution at each verified position; q_rows: [k, V], the draft head's at the k drafted positions; drafts:
    [k] tokens that were sampled from q_rows; q_d: [k] their draft probabilities. Draft i is accepted with probability
    min(1, p_i(d_i) / q_i(d_i)). Returns (accept flags [k] int32, corrections [k+1] int32): the token to emit at
    position i if draft i is the first rejected one -- a draw from the residual max(0, p_i - q_i) renormalised -- and,
    at index k, a plain draw from p_k for the case where every draft was accepted. The caller takes the first rejection
    on the host; everything here is one small batch of vocabulary-wide ops, so the round still has a single device->host
    sync. With every distribution one-hot (greedy) this reduces to "accept iff argmax matches", so greedy and sampled
    decoding share the path.
    """

    k = q_rows.shape[0]
    f32 = ops.dtype('f32')
    p_d = Sampler.gather(ops, p_rows[:k], drafts)
    ratio = p_d / (q_d + 1e-30)
    ratio = ratio * (1 - ops.cast(ratio > 1, f32)) + ops.cast(ratio > 1, f32)  # min(1, ratio)
    u = ops.random_uniform((k,))
    accept = ops.cast(u < ratio, ops.dtype('i32'))
    resid = p_rows[:k] - q_rows
    resid = resid * ops.cast(resid > 0, f32) + 1e-12 * p_rows[:k]  # max(0, p - q); the tiny term guards p == q
    resid = resid / ops.sum(resid, -1, keepdims=True)
    corrections = sampler.draw(ops.concat([resid, p_rows[k:k + 1]], 0))  # [k+1]
    return accept, corrections


##
# Static decode


def _pow2_at_least(n: int, floor: int = 8) -> int:
    c = floor
    while c < n:
        c *= 2
    return c


class Decoder:
    """
    Fixed-capacity decode state plus the captured step.

    Built from a `Cache` after prefill: the KV of every attention layer is copied into a zero-padded buffer of
    `capacity` positions, the DeltaNet (conv, S) pairs are carried as-is, and the position becomes a 0-d device array.
    `step(tok)` runs the captured `decode_fn`; the only host<->device traffic per token is the token id in and the
    logits out. When the sequence reaches capacity the buffers are doubled and the step re-captured.
    """

    def __init__(self, model: Qwen35, cache: Cache, capacity: int | None = None) -> None:
        if model.ops.taps is not None:
            raise RuntimeError('taps must be off for the static decoder')
        self.model = model
        self.ops = model.ops
        self.seq_len = cache.seq_len
        self.capacity = _pow2_at_least(capacity or (cache.seq_len + 1))
        if self.capacity <= self.seq_len:
            self.capacity = _pow2_at_least(self.seq_len + 1)
        self.flat: list[Array] = []
        for st in cache.layers:
            if st is None:
                raise ValueError('cache has no state; run a prefill first')
            self.flat.extend(st)
        self._alloc(self.capacity, first=True)

    def _pad_to(self, capacity: int) -> None:
        """Zero-pad every KV buffer to `capacity` positions (no-op for buffers already that long)."""

        ops = self.ops
        c = self.model.cfg
        flat: list[Array] = []
        for i, kind in enumerate(c.layer_types):
            a, b = self.flat[2 * i], self.flat[2 * i + 1]
            if kind == 'full':
                B, KV, T, D = a.shape
                if T < capacity:
                    pad = ops.zeros((B, KV, capacity - T, D), a.dtype)
                    a = ops.concat([a, pad], 2)
                    b = ops.concat([b, pad], 2)
                elif T > capacity:
                    raise ValueError(f'KV longer ({T}) than capacity ({capacity})')
            flat.extend([a, b])
        self.flat = flat

    def _alloc(self, capacity: int, first: bool = False) -> None:
        ops = self.ops
        c = self.model.cfg
        self.capacity = capacity
        self._pad_to(capacity)
        self.ar = ops.arange(capacity)
        cos_np, sin_np = ops.rope_tables(0, capacity, c.rope_dim, c.rope_theta)
        self.cos_tab = ops.array(cos_np, self.model.dtype)
        self.sin_tab = ops.array(sin_np, self.model.dtype)
        self.fns: dict[tuple[int, bool, bool], ta.Callable[..., tuple[Array, ...]]] = {}
        self.fn = self._fn(1, False, True)

    def _fn(self, T: int, all_states: bool, return_hidden: bool) -> ta.Callable[..., tuple[Array, ...]]:
        """The captured step for a given shape, built on first use (each is one graph on CUDA)."""

        key = (T, all_states, return_hidden)
        if key not in self.fns:
            self.fns[key] = self.ops.capture(self.model.step_fn(T, all_states, return_hidden))
        return self.fns[key]

    def tables(self) -> tuple[Array, Array, Array]:
        return self.ar, self.cos_tab, self.sin_tab

    def ensure_capacity(self, n: int) -> None:
        if n > self.capacity:
            self._alloc(_pow2_at_least(n))

    def step(self, tok: int | list[int]) -> Array:
        """Process the token at position `seq_len`; returns logits [B, V] float32 for the next position."""

        ops = self.ops
        self.ensure_capacity(self.seq_len + 1)
        ids = np.asarray([tok] if isinstance(tok, int) else tok, dtype=np.int32).reshape(-1, 1)
        out = self.fn(ops.array(ids), ops.scalar(self.seq_len), *self.tables(), *self.flat)
        self.flat = list(out[2:])
        self.logits_last = out[0][:, 0]  # [B, V]
        self.hidden_last = out[1][:, -1:]  # [B, 1, H]
        self.seq_len += 1
        return out[0][:, 0]

    def export_cache(self) -> Cache:
        """The functional `Cache` equivalent of the static state: exact-length KV, copied."""

        ops = self.ops
        c = Cache(self.model.cfg)
        c.seq_len = self.seq_len
        for i, kind in enumerate(self.model.cfg.layer_types):
            a = self.flat[2 * i]
            b = self.flat[2 * i + 1]
            if kind == 'full':
                c.layers[i] = (ops.copy(a[:, :, :self.seq_len]), ops.copy(b[:, :, :self.seq_len]))
            else:
                c.layers[i] = (ops.copy(a), ops.copy(b))
        return c

    def snapshot_after(self, tokens: ta.Sequence[int]) -> Snapshot:
        """Prefix-cache snapshot of the state after the first `seq_len` of `tokens` (no draft-head KV)."""

        return Snapshot(
            tuple(int(t) for t in tokens[:self.seq_len]),
            self.export_cache(),
            self.ops.copy(self.logits_last),
            self.ops.copy(self.hidden_last),
            None,
        )

    def verify(self, toks: list[int] | Array) -> tuple[Array, Array, list[Array]]:
        """
        Speculative verify: run T tokens (a list of ids, or a [1, T] int array already on the device) at
        positions seq_len.. in one captured step. Returns logits [B, T, V], the final-normed hidden
        [B, T, hidden], and the per-layer state with the DeltaNet entries stacked per token. Nothing is
        committed until `commit`.
        """

        ops = self.ops
        if isinstance(toks, list):
            toks = ops.array(np.asarray(toks, dtype=np.int32).reshape(1, len(toks)))
        T = toks.shape[1]
        self.ensure_capacity(self.seq_len + T)
        out = self._fn(T, True, True)(toks, ops.scalar(self.seq_len), *self.tables(), *self.flat)
        return out[0], out[1], list(out[2:])

    def commit(self, flat_all: list[Array], n_accept: int) -> None:
        """
        Keep the state after the first `n_accept` verified tokens (the KV buffers need no rollback: positions
        past the commit are masked by `pos` and overwritten by the next step).
        """

        flat: list[Array] = []
        for i, kind in enumerate(self.model.cfg.layer_types):
            a, b = flat_all[2 * i], flat_all[2 * i + 1]
            if kind == 'full':
                flat.extend([a, b])
            else:
                flat.extend([a[n_accept - 1], b[n_accept - 1]])
        self.flat = flat
        self.seq_len += n_accept

    def snapshot(self) -> tuple[int, list[Array]]:
        """(seq_len, copies of the state) -- the prefix-cache primitive for the static path."""

        return self.seq_len, [self.ops.copy(a) for a in self.flat]

    def restore(self, snap: tuple[int, list[Array]]) -> None:
        self.seq_len, flat = snap
        self.flat = [self.ops.copy(a) for a in flat]
        snap_cap = max(a.shape[2] for a, kind in zip(self.flat[::2], self.model.cfg.layer_types) if kind == 'full')
        if snap_cap > self.capacity:
            self._alloc(snap_cap)  # snapshot taken after a growth; the step must be re-captured for its shapes
        else:
            self._pad_to(self.capacity)


##
# Speculative decoding


class SpecDecoder:
    """
    MTP speculative decoding, batch 1: each round drafts `k` tokens with the draft head (the first from the head's last
    refreshed entry, the rest by recursion on its own hidden), verifies all of them plus the already-sampled next token
    in one T = k + 1 target step, commits the accepted prefix, and refreshes the draft head's KV with the target's true
    hidden states for the committed positions. Acceptance is "the target's sample equals the draft": exact for greedy
    and for sampling (each committed token is a sample from the target's own distribution given its prefix), just less
    efficient than rejection sampling would be.

    Rollback on the target side is free: the KV buffers are masked by position and the DeltaNet state after the accepted
    prefix is selected from the per-token stack the verify step returns. On the draft side the entries written past the
    commit are rewritten by the next refresh before anything can attend to them.
    """

    def __init__(
            self,
            model: Qwen35,
            cache: Cache,
            prompt_ids: list[int],
            logits: Array,
            hidden: Array,
            k: int,
            sampler: Sampler,
            capacity: int | None = None,
            draft_vocab: int = 0,
            mtp_kv: FullState | None = None,
    ) -> None:
        """
        `cache` holds the target's state after the n prompt tokens; `logits` its logits at the last position; `hidden`
        [1, T, H] the target's final-normed hidden states for positions n-T..n-1 -- all n of them when starting
        from scratch, or just the tail when `mtp_kv` already holds the draft head's KV for entries 0..n-T-1 (a prefix
        snapshot resuming). The draft head is then prefilled over entries n-T..n-1 only.
        """

        if model.mtp is None:
            raise ValueError('no MTP head loaded')
        if draft_vocab < 0 or draft_vocab > model.cfg.vocab_size:
            raise ValueError(f'draft_vocab must be 0..{model.cfg.vocab_size}')
        self.draft_vocab = draft_vocab
        if not 1 <= k <= 8:
            raise ValueError(f'draft tokens must be 1..8, got {k}')
        self.model = model
        self.ops = ops = model.ops
        self.mtp = model.mtp
        self.k = k
        self.sampler = sampler
        self.dec = Decoder(model, cache, capacity)
        n = self.dec.seq_len
        sampler.bind(ops, model.cfg.vocab_size)
        self.i32 = ops.dtype('i32')
        self.next_arr = sampler.sample(logits[:, -1])  # [1] on the device
        sampler.observe(self.next_arr)
        self.next_tok = int(ops.numpy(self.next_arr)[0])
        # draft-head prefill: entry p uses the target hidden at p and the token at p+1, for p = start..n-1 (start = 0
        # from scratch; the position of the first supplied hidden row when resuming on top of `mtp_kv`)
        start = n - hidden.shape[1]
        mtoks = np.asarray([*prompt_ids[start + 1:n], self.next_tok], dtype=np.int32)[None]
        mlogits, d, (mk, mv) = self.mtp.prefill(mtoks, hidden, start, draft_vocab, mtp_kv)
        self.mflat: list[Array] = [mk, mv]
        self.logits_last = logits[:, -1]  # [1, V]: the target's logits for position n (what next_tok was drawn from)
        self.hidden_last = hidden[:, -1:]  # [1, 1, H]: the target's hidden at position n-1
        self.mcap = 0
        self.mfns: dict[int, ta.Callable[..., tuple[Array, ...]]] = {}
        self.d_last = d[:, -1:]  # [B, 1, H]
        self.mlogits_last = mlogits[:, -1]  # [1, V] on the device
        self.mseq = n  # draft-head entries with true hidden states
        self.rounds = 0
        self.accepted = 0
        # test hook: (seq_len, next_tok, k) -> k draft tokens, replacing the draft head's proposals
        self.draft_fn: ta.Callable[[int, int, int], list[int]] | None = None

    def _sync_capacity(self) -> None:
        """Pad the draft head's KV to the target's capacity (re-capturing its steps) whenever the latter grew."""

        ops = self.ops
        cap = self.dec.capacity
        if cap == self.mcap:
            return
        mk, mv = self.mflat
        B, KV, T, D = mk.shape
        if T < cap:
            pad = ops.zeros((B, KV, cap - T, D), mk.dtype)
            mk = ops.concat([mk, pad], 2)
            mv = ops.concat([mv, pad], 2)
        self.mflat = [mk, mv]
        self.mcap = cap
        self.mfns = {}

    def _mfn(self, T: int) -> ta.Callable[..., tuple[Array, ...]]:
        if T not in self.mfns:
            self.mfns[T] = self.ops.capture(self.mtp.step_fn(T, self.draft_vocab))
        return self.mfns[T]

    def round(self) -> list[int]:
        """One draft / verify / commit cycle; returns the committed tokens (1..k+1 of them)."""

        ops = self.ops
        k = self.k
        sampler = self.sampler
        self.dec.ensure_capacity(self.dec.seq_len + k + 2)
        self._sync_capacity()
        n = self.dec.seq_len
        i32 = self.i32
        f32 = ops.dtype('f32')
        V = self.model.cfg.vocab_size

        # draft on the device: d_1 from the last refreshed entry, d_2..d_k by recursion at positions n, n+1, ...
        # Each draft is *sampled* from the head's warped distribution q (greedy: its argmax), and q and q(d) are kept
        # for the acceptance test. Nothing comes to the host until that test.
        darr: list[Array] = []
        qrows: list[Array] = []
        qds: list[Array] = []
        ml = self.mlogits_last  # [1, V or draft_vocab]
        hid = self.d_last
        for j in range(k):
            q = sampler.probs(ml)
            d = ops.cast(sampler.draw(q), i32)  # [1]
            darr.append(d)
            qds.append(Sampler.gather(ops, q, d))
            if q.shape[1] < V:  # drafting over a vocabulary prefix: zero mass elsewhere
                q = ops.concat([q, ops.zeros((1, V - q.shape[1]), f32)], -1)
            qrows.append(q)
            if j < k - 1:
                ml, hid, mk, mv = self._mfn(1)(
                    ops.reshape(d, (1, 1)), hid, ops.scalar(n + j), *self.dec.tables(), *self.mflat,
                )
                self.mflat = [mk, mv]
                ml = ml[:, -1]
        if self.draft_fn is not None:  # test hook: given drafts count as certain (q = one-hot at the draft)
            darr = [ops.array(np.asarray([t], dtype=np.int32)) for t in self.draft_fn(n, self.next_tok, k)]
            qrows = [ops.cast(ops.arange(V)[None, :] == d[:, None], f32) for d in darr]
            qds = [ops.zeros((1,), f32) + 1 for _ in darr]
        drafts_arr = ops.concat(darr, 0)  # [k]

        # verify: [next_tok, d_1..d_k] at positions n..n+k in one target step; rejection-sample on the device; the only
        # host round-trip of the round is the k accept flags, the k+1 corrections and the k drafts
        toks = ops.reshape(ops.concat([ops.cast(self.next_arr, i32), drafts_arr], 0), (1, k + 1))
        logits, hidden, flat_all = self.dec.verify(toks)
        p_rows = sampler.probs(logits[0])  # [k+1, V]; row i is the target's distribution for position n+i+1
        accept, corr = speculative_accept(ops, sampler, p_rows, ops.concat(qrows, 0), drafts_arr, ops.concat(qds, 0))
        got = ops.numpy(ops.concat([drafts_arr, accept, ops.cast(corr, i32)], 0)).tolist()
        drafts, flags, corrections = got[:k], got[k:2 * k], got[2 * k:]
        m = 0
        while m < k and flags[m]:
            m += 1
        committed = [self.next_tok, *drafts[:m]]
        self.dec.commit(flat_all, m + 1)
        new_arr = corr[m:m + 1]
        sampler.observe(ops.concat([drafts_arr[:m], ops.cast(new_arr, i32)], 0))  # committed drafts + the next token
        self.next_arr = new_arr
        self.next_tok = corrections[m]

        # refresh the draft head over positions n..n+k with true hidden states; entry m is the one that matters (hidden
        # at n+m, token at n+m+1 = the new next token); entries past it are junk that the next refresh overwrites before
        # anything attends to them
        rtoks = ops.reshape(ops.concat([drafts_arr[:m], ops.cast(new_arr, i32), drafts_arr[m:]], 0)[:k + 1], (1, k + 1))
        ml, d, mk, mv = self._mfn(k + 1)(rtoks, hidden, ops.scalar(n), *self.dec.tables(), *self.mflat)
        self.mflat = [mk, mv]
        self.mlogits_last = ml[:, m]
        self.d_last = d[:, m:m + 1]
        self.logits_last = logits[:, m]
        self.hidden_last = hidden[:, m:m + 1]
        self.mseq = n + m + 1
        self.rounds += 1
        self.accepted += m
        return committed

    def snapshot(self, tokens: ta.Sequence[int]) -> Snapshot:
        """
        The state after the `dec.seq_len` processed tokens, for the prefix cache: `tokens` must be the whole sequence
        so far (prompt + emitted), of which the first seq_len are the processed ones. Copies everything.
        """

        ops = self.ops
        n = self.dec.seq_len
        mk, mv = self.mflat
        return Snapshot(
            tuple(int(t) for t in tokens[:n]),
            self.dec.export_cache(),
            ops.copy(self.logits_last),
            ops.copy(self.hidden_last),
            (ops.copy(mk[:, :, :n - 1]), ops.copy(mv[:, :, :n - 1])),
        )
