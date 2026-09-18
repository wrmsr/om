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
import typing as ta

import numpy as np

from .ops import Array
from .ops import Ops
from .ops import Weight
from .quant import QUANT_BITS
from .quant import from_native
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
        H, KV, D = c.num_heads, c.num_kv_heads, c.head_dim
        qg = ops.reshape(ops.linear(x, self.wq), (B, T, H, 2 * D))
        q, gate = qg[..., :D], qg[..., D:]  # per-head [q | gate]
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

    def __call__(self, ops: Ops, x: Array, state: LinearState | None) -> tuple[Array, LinearState]:
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
        self.embed = params['embed_tokens.weight']
        self.norm_w = params['norm.weight']
        self.lm_head = params.get('lm_head.weight', self.embed)
        self.blocks: list[Block] = []
        for i, kind in enumerate(cfg.layer_types):
            pre = f'layers.{i}.'
            p = {}
            for k, v in params.items():
                if k.startswith(pre):
                    leaf = k[len(pre):]
                    # collapse "self_attn.q_proj.weight" -> "q_proj", "linear_attn.A" -> "A", "mlp.gate_proj.weight" ->
                    # "gate_proj"
                    parts = leaf.split('.')
                    if parts[-1] == 'weight':
                        parts = parts[:-1]
                    p[parts[-1]] = v
            self.blocks.append(Block(cfg, i, kind, p))

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
    ) -> Qwen35:
        """
        dtype: 'bf16' | 'f16' | 'f32' (compute dtype; norms, A, dt_bias, conv stay f32).
        quant: None, 'int8' or 'int4' (weight-only affine, see quant.py). If the source already holds
        MLX-quantized tensors at the requested width they are re-packed as-is; otherwise weights are quantized.
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
        missing = [n for n in names if n not in available]
        if missing:
            raise KeyError(f'source is missing {len(missing)} tensors, e.g. {missing[:5]}')
        if 'lm_head.weight' in available and not cfg.tied_embeddings:
            names.append('lm_head.weight')
        n_native = n_quant = 0
        for n_i, name in enumerate(names):
            p: Weight | None = None
            if bits is not None and not any(s in name for s in KEEP_F32 + NO_QUANT):
                nq = src.get_quant(name)
                if nq is not None and nq.bits == bits:
                    p = ops.qweight(from_native(nq.values, nq.scale, nq.bias, nq.bits, nq.group), dt)
                    n_native += 1
            if p is None:
                arr = np.array(src.get(name), dtype=np.float32, copy=True)
                if any(s in name for s in KEEP_F32):
                    p = ops.weight(arr, f32)
                elif bits is not None and is_quantizable(name, arr.shape, group):
                    p = ops.quantize(arr, bits, group, dt)
                    n_quant += 1
                else:
                    p = ops.weight(arr, dt)
            params[name] = p
            if verbose and (n_i % 50 == 0 or n_i == len(names) - 1):
                print(f'\r[model] loading tensors {n_i + 1}/{len(names)}', end='', flush=True)
        model = cls(cfg, params, ops, dt)
        if verbose:
            q_note = f', {n_native} re-packed + {n_quant} quantized to {quant}' if bits else ''
            print(f'\n[model] {model.nbytes / 2**30:.2f} GiB of weights on {ops.name}{q_note}')
        return model

    # forward

    def forward(
        self,
        tokens: np.ndarray,
        cache: Cache | None = None,
        start_pos: int | None = None,
        last_only: bool = False,
    ) -> Array:
        """tokens: [B, T] ints. Returns logits [B, T, V] (or [B, 1, V] with last_only) in float32."""

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
        return logits

    def generate(
        self,
        prompt_ids: list[int],
        max_new_tokens: int = 64,
        eos_ids: set[int] | None = None,
        on_token: ta.Callable[[int], None] | None = None,
    ) -> list[int]:
        """Greedy decoding with the cache. Yields token ids through on_token as they are produced."""

        ops = self.ops
        cache = Cache(self.cfg)
        logits = self.forward(np.array([prompt_ids]), cache, last_only=True)
        out: list[int] = []
        for _ in range(max_new_tokens):
            nxt = int(np.argmax(ops.numpy(logits[0, -1])))
            out.append(nxt)
            if on_token:
                on_token(nxt)
            if eos_ids and nxt in eos_ids:
                break
            logits = self.forward(np.array([[nxt]]), cache, last_only=True)
        return out
