# ruff: noqa: N806 N812
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

from .ops import Array
from .ops import Ops
from .ops import Weight
from .paramcache import ParamCache
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
        self.wq = p['q_proj']
        self.wk = p['k_proj']
        self.wv = p['v_proj']
        self.wo = p['o_proj']
        self.q_norm = p['q_norm']
        self.k_norm = p['k_norm']
        self.scale = 1.0 / math.sqrt(cfg.head_dim)

    def __call__(self, ops: Ops, x: Array, pos: int, state: FullState | None) -> tuple[Array, FullState]:
        c = self.cfg
        B, T, _ = x.shape
        H = c.num_heads
        KV = c.num_kv_heads
        D = c.head_dim
        qg = ops.reshape(ops.linear(x, self.wq), (B, T, H, 2 * D))
        # per-head [q | gate]
        q = qg[..., :D]
        gate = qg[..., D:]
        k = ops.reshape(ops.linear(x, self.wk), (B, T, KV, D))
        v = ops.reshape(ops.linear(x, self.wv), (B, T, KV, D))
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
        """T tokens against fixed-capacity KV buffers. x: [B, T, hidden] at positions pos..pos+T-1; pos: 0-d int
        array; ar: arange(L); cos, sin: [T, rope_dim] rows for those positions; state: (kbuf, vbuf)
        [B, KV, L, D]. Every shape is static in `pos`; T == 1 is decode, T == k + 1 speculative verify."""

        c = self.cfg
        B, T, _ = x.shape
        H = c.num_heads
        KV = c.num_kv_heads
        D = c.head_dim
        qg = ops.reshape(ops.linear(x, self.wq), (B, T, H, 2 * D))
        q = qg[..., :D]
        gate = qg[..., D:]
        k = ops.reshape(ops.linear(x, self.wk), (B, T, KV, D))
        v = ops.reshape(ops.linear(x, self.wv), (B, T, KV, D))
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
        self.w_qkv = p['in_proj_qkv']
        self.w_z = p['in_proj_z']
        self.w_a = p['in_proj_a']
        self.w_b = p['in_proj_b']
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
        """With all_states the returned pair is stacked per token -- conv [T, B, C, K-1], S [T, B, H, dk, dv] --
        so a speculative verify can keep the state after exactly the accepted prefix (the KV side needs no
        rollback: stale positions are masked by `pos`)."""

        c = self.cfg
        B, T, _ = x.shape
        Hk = c.num_k_heads
        Hv = c.num_v_heads
        dk = c.head_k_dim
        dv = c.head_v_dim
        K = c.conv_kernel
        f32 = ops.dtype('f32')
        qkv = ops.transpose(ops.f32(ops.linear(x, self.w_qkv)), (0, 2, 1))  # [B, conv_dim, T]
        z = ops.f32(ops.linear(x, self.w_z))  # [B, T, value_dim]
        a = ops.f32(ops.linear(x, self.w_a))  # [B, T, n_v]
        b = ops.f32(ops.linear(x, self.w_b))

        # causal depthwise conv1d over [history | new]
        hist = state[0] if state is not None else ops.zeros((B, c.conv_dim, K - 1), f32)
        inp = ops.concat([hist, qkv], -1)
        conv_state = inp[..., -(K - 1):]
        conv = ops.transpose(ops.silu(ops.conv1d_causal(inp, self.conv_w)), (0, 2, 1))  # [B, T, conv_dim]
        q, k, v = ops.split(conv, [c.key_dim, c.key_dim, c.value_dim], -1)
        q = ops.transpose(ops.l2_norm(ops.reshape(q, (B, T, Hk, dk))), (0, 2, 1, 3)) * (dk**-0.5)  # [B,Hk,T,dk]
        k = ops.transpose(ops.l2_norm(ops.reshape(k, (B, T, Hk, dk))), (0, 2, 1, 3))
        v = ops.transpose(ops.reshape(v, (B, T, Hv, dv)), (0, 2, 1, 3))  # [B,Hv,T,dv]
        if Hv != Hk:  # canonical grouped V order -> repeat_interleave (llama.cpp's tiled order would use tiling)
            q = ops.repeat(q, Hv // Hk, 1)
            k = ops.repeat(k, Hv // Hk, 1)

        beta = ops.transpose(ops.sigmoid(b), (0, 2, 1))  # [B,Hv,T]
        g = ops.transpose(self.A[None, None, :] * ops.softplus(a + self.dt_bias), (0, 2, 1))  # [B,Hv,T], <= 0

        S = state[1] if state is not None else ops.zeros((B, Hv, dk, dv), f32)
        if all_states:
            out, S = ops.gated_delta_states(q, k, v, g, beta, S)  # S: [T, B, Hv, dk, dv]
            conv_state = ops.stack([inp[..., t + 1:t + K] for t in range(T)], 0)  # [T, B, C, K-1]
        else:
            out, S = ops.gated_delta(q, k, v, g, beta, S)

        out = ops.reshape(ops.transpose(out, (0, 2, 1, 3)), (B, T, Hv, dv))  # [B,T,Hv,dv]
        z = ops.reshape(z, (B, T, Hv, dv))
        out = ops.rms_norm(out, self.norm_w, c.rms_eps) * ops.silu(z)  # gated RMSNorm
        y = ops.linear(ops.cast(ops.reshape(out, (B, T, c.value_dim)), x.dtype), self.w_out)
        return y, (conv_state, S)


class MLP:
    def __init__(self, p: dict[str, Weight]) -> None:
        self.wg = p['gate_proj']
        self.wu = p['up_proj']
        self.wd = p['down_proj']

    def __call__(self, ops: Ops, x: Array) -> Array:
        return ops.linear(ops.silu(ops.linear(x, self.wg)) * ops.linear(x, self.wu), self.wd)


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
        cache_dir: keep the finished parameters on disk there (see paramcache.py); the first load fills it, later
               ones memory-map it and skip the GGUF dequantization entirely.
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

    # forward

    def forward(
        self,
        tokens: np.ndarray,
        cache: Cache | None = None,
        start_pos: int | None = None,
        last_only: bool = False,
        return_hidden: bool = False,
    ) -> ta.Any:
        """tokens: [B, T] ints. Returns logits [B, T, V] (or [B, 1, V] with last_only) in float32; with
        return_hidden also the final-normed hidden states [B, T, hidden] (what the MTP head conditions on)."""

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
            ar: Array,
            cos_tab: Array,
            sin_tab: Array,
            all_states: bool = False,
            return_hidden: bool = False,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Build the static T-token step: `fn(toks, pos, *flat_state) -> (logits, [hidden,] *flat_state)`.

        toks: [B, T] int at positions pos..pos+T-1; pos: 0-d int; flat_state: two arrays per layer (kbuf, vbuf) or
        (conv, S). `ar` and the rope tables are constants closed over (they must already live on the device:
        nothing in the step may allocate from the host). Returns logits [B, T, V] float32 (and, with
        return_hidden, the final-normed hidden [B, T, hidden] the draft head conditions on); with all_states the
        DeltaNet entries come back stacked per token. Pure apart from `kv_write`, so a backend may capture it.
        T == 1 is decode; T == k + 1 with all_states is speculative verify.
        """

        ops, c = self.ops, self.cfg

        def fn(toks, pos, *flat):
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

    def decode_fn(
            self,
            ar: Array,
            cos_tab: Array,
            sin_tab: Array,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """The single-token step: `fn(tok, pos, *flat_state) -> (logits [B, 1, V], *flat_state)`."""

        return self.step_fn(1, ar, cos_tab, sin_tab)

    def generate(
        self,
        prompt_ids: list[int],
        max_new_tokens: int = 64,
        eos_ids: set[int] | None = None,
        on_token: ta.Callable[[int], None] | None = None,
        static: bool = True,
        sampler: Sampler | None = None,
        spec: int = 0,
    ) -> list[int]:
        """
        Generation. Prefill goes through `forward` (chunked); decode then runs the captured static step
        (`static=True`, the fast path) or keeps growing the functional cache (`static=False`, the reference).
        `sampler` defaults to greedy. `spec=k` (needs the MTP head loaded) drafts k tokens per round with the
        draft head and verifies them in one target step. Yields token ids through on_token as they are produced.
        """

        ops = self.ops
        sampler = sampler or Sampler()
        cache = Cache(self.cfg)
        logits, hidden = self.forward(np.array([prompt_ids]), cache, return_hidden=True)
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
                hidden,
                k=spec,
                sampler=sampler,
                capacity=len(prompt_ids) + max_new_tokens + spec + 2,
            )
            self.last_spec = spec_dec
            while len(out) < max_new_tokens:
                for tok in spec_dec.round():
                    if emit(tok) or len(out) >= max_new_tokens:
                        break
                else:
                    continue
                break
            return out

        dec = Decoder(self, cache, capacity=len(prompt_ids) + max_new_tokens + 1) if static else None
        nxt = sampler.sample(ops.numpy(logits[0, -1]))
        for _ in range(max_new_tokens):
            if emit(nxt):
                break
            if dec is not None:
                row = ops.numpy(dec.step(nxt))[0]
            else:
                row = ops.numpy(self.forward(np.array([[nxt]]), cache, last_only=True))[0, -1]
            nxt = sampler.sample(row)
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

    and can recurse, feeding its own normed output `d` back in as the next hidden. All norm weights are stored
    with the +1 already applied, like the text model's. The block runs through `Block.decode` on its own KV
    buffers (positions are the hidden's position).
    """

    def __init__(self, model: Qwen35, params: dict[str, Weight]) -> None:
        self.model = model
        self.cfg = model.cfg
        self.fc = params['mtp.fc.weight']
        self.enorm = params['mtp.pre_fc_norm_embedding.weight']
        self.hnorm = params['mtp.pre_fc_norm_hidden.weight']
        self.norm_w = params['mtp.norm.weight']
        self.block = Block(self.cfg, self.cfg.num_layers, 'full', block_params(params, 'mtp.layers.0.'))

    def stem(self, ops: Ops, toks: Array, hidden: Array) -> Array:
        c, m = self.cfg, self.model
        e = ops.rms_norm(ops.embedding(toks, m.embed, m.dtype), self.enorm, c.rms_eps)
        h = ops.rms_norm(ops.cast(hidden, m.dtype), self.hnorm, c.rms_eps)
        return ops.linear(ops.concat([e, h], -1), self.fc)

    def head(self, ops: Ops, u: Array) -> tuple[Array, Array]:
        c, m = self.cfg, self.model
        d = ops.rms_norm(u, self.norm_w, c.rms_eps)
        return ops.f32(ops.linear(d, m.lm_head)), d

    def prefill(self, toks: np.ndarray, hidden: Array, pos: int = 0) -> tuple[Array, Array, FullState]:
        """Functional (growing-cache) pass over T entries: toks [B, T] are the tokens at positions pos+1..pos+T,
        hidden [B, T, H] the target's hidden states at pos..pos+T-1. Returns logits, d, (k, v)."""

        ops = self.model.ops
        u = self.stem(ops, ops.array(np.asarray(toks, dtype=np.int32)), hidden)
        u, state = self.block(ops, u, pos, None)
        logits, d = self.head(ops, u)
        return logits, d, state

    def step_fn(self, T: int, ar: Array, cos_tab: Array, sin_tab: Array) -> ta.Callable[..., tuple[Array, ...]]:
        """Static T-entry step: `fn(toks [B,T], hidden [B,T,H], pos, kbuf, vbuf) -> (logits, d, kbuf, vbuf)`."""

        ops = self.model.ops

        def fn(toks, hidden, pos, kbuf, vbuf):
            rows = ops.reshape(pos, (1,)) + ar[:T]
            u = self.stem(ops, toks, hidden)
            u, (kbuf, vbuf) = self.block.decode(ops, u, pos, ar, cos_tab[rows], sin_tab[rows], (kbuf, vbuf))
            logits, d = self.head(ops, u)
            return logits, d, kbuf, vbuf

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
    Host-side sampling over a float32 logits row: temperature -> presence/frequency penalties -> top-k ->
    top-p -> min-p -> multinomial. temperature <= 0 is greedy (argmax) and ignores the rest. Qwen's published
    presets: thinking t=1.0 top-p=0.95 top-k=20; non-thinking t=0.7 top-p=0.8 top-k=20 presence=1.5.
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
        self.rng = np.random.default_rng(seed)
        self.counts: dict[int, int] = {}  # generated-token histogram for the penalties

    @property
    def greedy(self) -> bool:
        return self.temperature <= 0

    def observe(self, tok: int) -> None:
        self.counts[tok] = self.counts.get(tok, 0) + 1

    def sample(self, logits: np.ndarray) -> int:
        """One token from a [V] float32 row; records it for the penalties."""

        tok = self.sample_many(logits[None])[0]
        return tok

    def sample_many(self, logits: np.ndarray) -> list[int]:
        """One token per row of [T, V]; rows are independent (each is conditioned on its own prefix by the caller,
        as in speculative verify). Records every sampled token."""

        out = []
        for row in logits:
            out.append(self._one(np.asarray(row, dtype=np.float64)))
        for t in out:
            self.observe(t)
        return out

    def _one(self, l: np.ndarray) -> int:
        if self.greedy:
            return int(np.argmax(l))
        if self.counts and (self.presence_penalty or self.frequency_penalty):
            idx = np.fromiter(self.counts.keys(), dtype=np.int64)
            cnt = np.fromiter(self.counts.values(), dtype=np.float64)
            l = l.copy()
            l[idx] -= self.presence_penalty + self.frequency_penalty * cnt
        # narrow to the top-k candidates first (a partial partition, O(V)); everything after works on k values, so
        # top-p never sorts the 248k-wide vocabulary
        if self.top_k > 0 and self.top_k < l.shape[0]:
            cand = np.argpartition(l, -self.top_k)[-self.top_k:]
        else:
            cand = np.arange(l.shape[0])
        z = l[cand] / self.temperature
        p = np.exp(z - z.max())
        p /= p.sum()
        if self.min_p > 0:
            p = np.where(p < self.min_p * p.max(), 0.0, p)
        if self.top_p < 1.0:
            order = np.argsort(-p)
            cum = np.cumsum(p[order])
            cut = int(np.searchsorted(cum, self.top_p)) + 1
            keep = np.zeros_like(p)
            keep[order[:cut]] = p[order[:cut]]
            p = keep
        p /= p.sum()
        return int(cand[self.rng.choice(p.shape[0], p=p)])


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
    `capacity` positions, the DeltaNet (conv, S) pairs are carried as-is, and the position becomes a 0-d device
    array. `step(tok)` runs the captured `decode_fn`; the only host<->device traffic per token is the token id in
    and the logits out. When the sequence reaches capacity the buffers are doubled and the step re-captured.
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

        ops, c = self.ops, self.model.cfg
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
        ops, c = self.ops, self.model.cfg
        self.capacity = capacity
        self._pad_to(capacity)
        self.ar = ops.arange(capacity)
        cos_np, sin_np = ops.rope_tables(0, capacity, c.rope_dim, c.rope_theta)
        self.cos_tab = ops.array(cos_np, self.model.dtype)
        self.sin_tab = ops.array(sin_np, self.model.dtype)
        self.fns: dict[tuple[int, bool, bool], ta.Callable[..., tuple[Array, ...]]] = {}
        self.fn = self._fn(1, False, False)

    def _fn(self, T: int, all_states: bool, return_hidden: bool) -> ta.Callable[..., tuple[Array, ...]]:
        """The captured step for a given shape, built on first use (each is one graph on CUDA)."""

        key = (T, all_states, return_hidden)
        if key not in self.fns:
            self.fns[key] = self.ops.capture(
                self.model.step_fn(T, self.ar, self.cos_tab, self.sin_tab, all_states, return_hidden),
            )
        return self.fns[key]

    def ensure_capacity(self, n: int) -> None:
        if n > self.capacity:
            self._alloc(_pow2_at_least(n))

    def step(self, tok: int | list[int]) -> Array:
        """Process the token at position `seq_len`; returns logits [B, V] float32 for the next position."""

        ops = self.ops
        self.ensure_capacity(self.seq_len + 1)
        ids = np.asarray([tok] if isinstance(tok, int) else tok, dtype=np.int32).reshape(-1, 1)
        out = self.fn(ops.array(ids), ops.scalar(self.seq_len), *self.flat)
        self.flat = list(out[1:])
        self.seq_len += 1
        return out[0][:, 0]

    def verify(self, toks: list[int]) -> tuple[Array, Array, list[Array]]:
        """
        Speculative verify: run T = len(toks) tokens at positions seq_len.. in one captured step. Returns logits
        [B, T, V], the final-normed hidden [B, T, hidden], and the per-layer state with the DeltaNet entries
        stacked per token. Nothing is committed until `commit`.
        """

        ops = self.ops
        T = len(toks)
        self.ensure_capacity(self.seq_len + T)
        ids = np.asarray(toks, dtype=np.int32).reshape(1, T)
        out = self._fn(T, True, True)(ops.array(ids), ops.scalar(self.seq_len), *self.flat)
        return out[0], out[1], list(out[2:])

    def commit(self, flat_all: list[Array], n_accept: int) -> None:
        """Keep the state after the first `n_accept` verified tokens (the KV buffers need no rollback: positions
        past the commit are masked by `pos` and overwritten by the next step)."""

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
    MTP speculative decoding, batch 1: each round drafts `k` tokens with the draft head (the first from the
    head's last refreshed entry, the rest by recursion on its own hidden), verifies all of them plus the
    already-sampled next token in one T = k + 1 target step, commits the accepted prefix, and refreshes the draft
    head's KV with the target's true hidden states for the committed positions. Acceptance is "the target's
    sample equals the draft": exact for greedy and for sampling (each committed token is a sample from the
    target's own distribution given its prefix), just less efficient than rejection sampling would be.

    Rollback on the target side is free: the KV buffers are masked by position and the DeltaNet state after the
    accepted prefix is selected from the per-token stack the verify step returns. On the draft side the entries
    written past the commit are rewritten by the next refresh before anything can attend to them.
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
    ) -> None:
        if model.mtp is None:
            raise ValueError('no MTP head loaded')
        if not 1 <= k <= 8:
            raise ValueError(f'draft tokens must be 1..8, got {k}')
        self.model = model
        self.ops = ops = model.ops
        self.mtp = model.mtp
        self.k = k
        self.sampler = sampler
        self.dec = Decoder(model, cache, capacity)
        n = self.dec.seq_len
        self.next_tok = sampler.sample(ops.numpy(logits[0, -1]))
        # draft-head prefill: entry p uses the target hidden at p and the token at p+1, for p = 0..n-1
        mtoks = np.asarray(list(prompt_ids[1:]) + [self.next_tok], dtype=np.int32)[None]
        mlogits, d, (mk, mv) = self.mtp.prefill(mtoks, hidden[:, :n], 0)
        self.mflat: list[Array] = [mk, mv]
        self.mcap = 0
        self.mfns: dict[int, ta.Callable[..., tuple[Array, ...]]] = {}
        self.d_last = d[:, -1:]  # [B, 1, H]
        self.mlogits_last = ops.numpy(mlogits[0, -1])
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
            self.mfns[T] = self.ops.capture(self.mtp.step_fn(T, self.dec.ar, self.dec.cos_tab, self.dec.sin_tab))
        return self.mfns[T]

    def round(self) -> list[int]:
        """One draft / verify / commit cycle; returns the committed tokens (1..k+1 of them)."""

        ops, k = self.ops, self.k
        self.dec.ensure_capacity(self.dec.seq_len + k + 2)
        self._sync_capacity()
        n = self.dec.seq_len

        # draft: d_1 from the last refreshed entry, d_2..d_k by recursion at positions n, n+1, ...
        drafts = [int(np.argmax(self.mlogits_last))]
        hid = self.d_last
        for j in range(1, k):
            toks = ops.array(np.asarray([[drafts[-1]]], dtype=np.int32))
            ml, hid, mk, mv = self._mfn(1)(toks, hid, ops.scalar(n - 1 + j), *self.mflat)
            self.mflat = [mk, mv]
            drafts.append(int(np.argmax(ops.numpy(ml[0, -1]))))
        if self.draft_fn is not None:
            drafts = list(self.draft_fn(n, self.next_tok, k))

        # verify: [next_tok, d_1..d_k] at positions n..n+k in one target step
        logits, hidden, flat_all = self.dec.verify([self.next_tok] + drafts)
        rows = ops.numpy(logits[0])  # [k+1, V]; row i is the target's distribution for position n+i+1
        targets: list[int] = []
        m = 0
        for i in range(k + 1):
            t = self.sampler.sample(rows[i])
            targets.append(t)
            if i < k and drafts[i] == t:
                m += 1
            else:
                break
        committed = [self.next_tok] + drafts[:m]
        self.dec.commit(flat_all, m + 1)
        self.next_tok = targets[m]

        # refresh the draft head over positions n..n+k with true hidden states; entry m is the one that matters
        # (hidden at n+m, token at n+m+1 = the new next token); entries past it are junk that the next refresh
        # overwrites before anything attends to them
        rtoks = np.asarray((drafts[:m] + [targets[m]] + drafts[m:])[:k + 1], dtype=np.int32)[None]
        ml, d, mk, mv = self._mfn(k + 1)(ops.array(rtoks), hidden, ops.scalar(n), *self.mflat)
        self.mflat = [mk, mv]
        self.mlogits_last = ops.numpy(ml[0, m])
        self.d_last = d[:, m:m + 1]
        self.mseq = n + m + 1
        self.rounds += 1
        self.accepted += m
        return committed
