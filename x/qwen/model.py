"""
Qwen3.5 / 3.6 / 3.8 (dense) text decoder in plain PyTorch.

Every op is written out; there is no `transformers` and no fused kernel. Layer math is cross-checked against llama.cpp's
`src/models/qwen35.cpp` and HF's `modeling_qwen3_5.py`:

  block:    x = x + mixer(rmsnorm(x));  x = x + swiglu(rmsnorm(x))
  mixer is either
    full:   gated GQA attention -- q_proj emits [q | gate] per head, per-head q/k RMSNorm,
            partial NeoX RoPE on the first `rope_dim` dims, softmax attention, * sigmoid(gate), o_proj
    linear: Gated DeltaNet -- in_proj_qkv -> causal depthwise conv1d(k=4)+silu -> l2norm(q,k)
            -> gated delta rule recurrence (fixed-size state) -> rmsnorm * silu(z) -> out_proj

The recurrence is the per-token form for both prefill and decode (correct, O(T) sequential; a chunked parallel prefill
is the obvious next optimisation).
"""
import dataclasses as dc
import math

import numpy as np
import torch
import torch.nn.functional as F

from .quant import QUANT_BITS
from .quant import QWeight
from .quant import embedding
from .quant import from_native
from .quant import linear
from .quant import param_nbytes
from .quant import quantize
from .weights import Qwen35Config
from .weights import TensorSource


##
# Cache


@dc.dataclass()
class FullAttnCache:
    k: torch.Tensor | None = None  # [B, n_kv, T, hd]
    v: torch.Tensor | None = None


@dc.dataclass()
class LinearCache:
    conv: torch.Tensor | None = None  # [B, conv_dim, kernel-1]  last inputs to the conv
    state: torch.Tensor | None = None  # [B, n_v, dk, dv] float32


class Cache:
    """
    One entry per layer. Attention layers grow a KV cache; linear layers keep a fixed-size (conv window, recurrent
    state) pair -- so 'prefix caching' for 3/4 of the stack is just snapshotting a tensor.
    """

    def __init__(self, cfg: Qwen35Config):
        self.layers: list = [
            FullAttnCache() if t == 'full' else LinearCache() for t in cfg.layer_types
        ]
        self.seq_len = 0

    def snapshot(self) -> "Cache":
        c = Cache.__new__(Cache)
        c.seq_len = self.seq_len
        c.layers = []
        for l in self.layers:
            if isinstance(l, FullAttnCache):
                c.layers.append(
                    FullAttnCache(
                        l.k.clone() if l.k is not None else None,
                        l.v.clone() if l.v is not None else None,
                    ),
                )
            else:
                c.layers.append(
                    LinearCache(
                        l.conv.clone() if l.conv is not None else None,
                        l.state.clone() if l.state is not None else None,
                    ),
                )
        return c


##
# Primitives


def rms_norm(x: torch.Tensor, w: torch.Tensor, eps: float) -> torch.Tensor:
    xf = x.float()
    y = xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + eps)
    return (y * w.float()).to(x.dtype)


def l2_norm(x: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    # FLA-style: x / sqrt(sum(x^2) + eps)   (llama.cpp: rms_norm(x, eps/n) / sqrt(n) -- identical)
    return x * torch.rsqrt(x.pow(2).sum(-1, keepdim=True) + eps)


def rope_cos_sin(
    positions: torch.Tensor, rope_dim: int, theta: float, device, dtype=torch.float32,
):
    inv = 1.0 / (
        theta
        ** (torch.arange(0, rope_dim, 2, device=device, dtype=torch.float32) / rope_dim)
    )
    freqs = positions.to(torch.float32)[:, None] * inv[None, :]  # [T, rope_dim/2]
    emb = torch.cat([freqs, freqs], dim=-1)  # [T, rope_dim]
    return emb.cos().to(dtype), emb.sin().to(dtype)


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """NeoX rotate-half on the first rope_dim dims of x: [B, H, T, hd]; cos/sin: [T, rope_dim]."""

    rd = cos.shape[-1]
    xr, xp = x[..., :rd], x[..., rd:]
    half = rd // 2
    x1, x2 = xr[..., :half], xr[..., half:]
    rot = torch.cat([-x2, x1], dim=-1)
    xr = xr * cos[None, None] + rot * sin[None, None]
    return torch.cat([xr, xp], dim=-1)


def gated_delta_rule_recurrent(q, k, v, g, beta, state):
    """
    Per-token gated delta rule.

    q, k: [B, H, T, dk] (already l2-normed; q already scaled by 1/sqrt(dk))
    v:    [B, H, T, dv]
    g:    [B, H, T]  log decay (<= 0);   beta: [B, H, T] in (0, 1)
    state:[B, H, dk, dv]
    returns out [B, H, T, dv], new state
    """

    B, H, T, dk = q.shape
    out = torch.empty(B, H, T, v.shape[-1], dtype=torch.float32, device=q.device)
    S = state
    for t in range(T):
        q_t, k_t, v_t = q[:, :, t], k[:, :, t], v[:, :, t]  # [B,H,dk] / [B,H,dv]
        S = S * g[:, :, t].exp()[..., None, None]  # decay
        mem = (S * k_t[..., None]).sum(-2)  # k^T S -> [B,H,dv]
        delta = (v_t - mem) * beta[:, :, t][..., None]
        S = S + k_t[..., None] * delta[..., None, :]  # rank-1 update
        out[:, :, t] = (S * q_t[..., None]).sum(-2)  # q^T S
    return out, S


##
# Layers


class Attention:
    def __init__(self, cfg: Qwen35Config, p: dict):
        self.cfg = cfg
        self.wq, self.wk, self.wv, self.wo = (
            p['q_proj'],
            p['k_proj'],
            p['v_proj'],
            p['o_proj'],
        )
        self.q_norm, self.k_norm = p['q_norm'], p['k_norm']
        self.scale = 1.0 / math.sqrt(cfg.head_dim)

    def __call__(
        self, x: torch.Tensor, cos, sin, cache: FullAttnCache | None,
    ) -> torch.Tensor:
        c = self.cfg
        B, T, _ = x.shape
        H, KV, D = c.num_heads, c.num_kv_heads, c.head_dim
        qg = linear(x, self.wq).view(B, T, H, 2 * D)
        q, gate = qg[..., :D], qg[..., D:]  # per-head [q | gate]
        k = linear(x, self.wk).view(B, T, KV, D)
        v = linear(x, self.wv).view(B, T, KV, D)
        q = rms_norm(q, self.q_norm, c.rms_eps).transpose(1, 2)  # [B,H,T,D]
        k = rms_norm(k, self.k_norm, c.rms_eps).transpose(1, 2)  # [B,KV,T,D]
        v = v.transpose(1, 2)
        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)
        past = 0
        if cache is not None:
            if cache.k is not None:
                past = cache.k.shape[2]
                k = torch.cat([cache.k, k], dim=2)
                v = torch.cat([cache.v, v], dim=2)
            cache.k, cache.v = k, v
        if KV != H:
            k = k.repeat_interleave(H // KV, dim=1)
            v = v.repeat_interleave(H // KV, dim=1)
        if T == 1:
            o = F.scaled_dot_product_attention(q, k, v, scale=self.scale)
        else:
            L = past + T
            mask = torch.ones(T, L, dtype=torch.bool, device=x.device).tril(
                diagonal=past,
            )
            o = F.scaled_dot_product_attention(
                q, k, v, attn_mask=mask, scale=self.scale,
            )
        o = o.transpose(1, 2).reshape(B, T, H * D)
        o = o * torch.sigmoid(gate.reshape(B, T, H * D).float()).to(o.dtype)
        return linear(o, self.wo)


class GatedDeltaNet:
    def __init__(self, cfg: Qwen35Config, p: dict):
        self.cfg = cfg
        self.w_qkv, self.w_z, self.w_a, self.w_b = (
            p['in_proj_qkv'],
            p['in_proj_z'],
            p['in_proj_a'],
            p['in_proj_b'],
        )
        self.conv_w = p['conv1d']  # [conv_dim, K] float32
        self.A = p['A']  # [n_v] == -exp(A_log), float32
        self.dt_bias = p['dt_bias']  # [n_v] float32
        self.norm_w, self.w_out = p['norm'], p['out_proj']

    def __call__(self, x: torch.Tensor, cache: LinearCache | None) -> torch.Tensor:
        c = self.cfg
        B, T, _ = x.shape
        Hk, Hv, dk, dv, K = (
            c.num_k_heads,
            c.num_v_heads,
            c.head_k_dim,
            c.head_v_dim,
            c.conv_kernel,
        )
        qkv = linear(x, self.w_qkv).float().transpose(1, 2)  # [B, conv_dim, T]
        z = linear(x, self.w_z).float()  # [B, T, value_dim]
        a = linear(x, self.w_a).float()  # [B, T, n_v]
        b = linear(x, self.w_b).float()

        # causal depthwise conv1d (+ state)
        if cache is not None and cache.conv is not None:
            inp = torch.cat([cache.conv, qkv], dim=-1)
        else:
            inp = F.pad(qkv, (K - 1, 0))
        if cache is not None:
            cache.conv = inp[..., -(K - 1) :].clone()
        conv = F.conv1d(
            inp, self.conv_w[:, None, :], groups=c.conv_dim,
        )  # [B, conv_dim, T]
        conv = F.silu(conv).transpose(1, 2)  # [B, T, conv_dim]
        q, k, v = torch.split(conv, [c.key_dim, c.key_dim, c.value_dim], dim=-1)
        q = l2_norm(q.view(B, T, Hk, dk)).transpose(1, 2) * (dk**-0.5)  # [B,Hk,T,dk]
        k = l2_norm(k.view(B, T, Hk, dk)).transpose(1, 2)
        v = v.view(B, T, Hv, dv).transpose(1, 2)  # [B,Hv,T,dv]
        if (
            Hv != Hk
        ):  # canonical grouped V order -> repeat_interleave (llama.cpp's tiled order would use repeat)
            q = q.repeat_interleave(Hv // Hk, dim=1)
            k = k.repeat_interleave(Hv // Hk, dim=1)

        beta = torch.sigmoid(b).transpose(1, 2)  # [B,Hv,T]
        g = (self.A[None, None, :] * F.softplus(a + self.dt_bias)).transpose(
            1, 2,
        )  # [B,Hv,T], <= 0

        state = (
            cache.state
            if (cache is not None and cache.state is not None)
            else torch.zeros(B, Hv, dk, dv, dtype=torch.float32, device=x.device)
        )
        out, state = gated_delta_rule_recurrent(q, k, v, g, beta, state)
        if cache is not None:
            cache.state = state

        out = out.transpose(1, 2).reshape(B, T, Hv, dv)  # [B,T,Hv,dv]
        z = z.view(B, T, Hv, dv)
        out = rms_norm(out, self.norm_w, c.rms_eps) * F.silu(z)  # gated RMSNorm
        return linear(out.reshape(B, T, c.value_dim).to(x.dtype), self.w_out)


class MLP:
    def __init__(self, p: dict):
        self.wg, self.wu, self.wd = p['gate_proj'], p['up_proj'], p['down_proj']

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        return linear(F.silu(linear(x, self.wg)) * linear(x, self.wu), self.wd)


class Block:
    def __init__(self, cfg: Qwen35Config, kind: str, p: dict):
        self.kind = kind
        self.ln1, self.ln2 = p['input_layernorm'], p['post_attention_layernorm']
        self.eps = cfg.rms_eps
        self.mixer = Attention(cfg, p) if kind == 'full' else GatedDeltaNet(cfg, p)
        self.mlp = MLP(p)

    def __call__(self, x, cos, sin, cache):
        h = rms_norm(x, self.ln1, self.eps)
        x = x + (
            self.mixer(h, cos, sin, cache)
            if self.kind == 'full'
            else self.mixer(h, cache)
        )
        return x + self.mlp(rms_norm(x, self.ln2, self.eps))


##
# Model
##
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
                for n in ('q_proj', 'k_proj', 'v_proj', 'o_proj', 'q_norm', 'k_norm')
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
KEEP_F32 = ('norm', 'linear_attn.A', 'dt_bias', 'conv1d')

# 2-D weights that are never quantized: the low-rank DeltaNet projections are quantization-sensitive (Ollama's own
# converter also keeps them at source precision)
NO_QUANT = ('in_proj_a', 'in_proj_b')


def is_quantizable(name: str, t: torch.Tensor, group: int) -> bool:
    if t.ndim != 2 or t.shape[1] % group:
        return False
    return not any(s in name for s in KEEP_F32 + NO_QUANT)


Param = torch.Tensor | QWeight


class Qwen35:
    def __init__(self, cfg: Qwen35Config, params: dict[str, Param], device, dtype: torch.dtype = torch.bfloat16):
        self.cfg = cfg
        self.device = device
        self.dtype = dtype
        self.nbytes = sum(param_nbytes(p) for p in params.values())
        self.embed = params['embed_tokens.weight']
        self.norm_w = params['norm.weight']
        self.lm_head = params.get('lm_head.weight', self.embed)
        self.blocks: list[Block] = []
        for i, kind in enumerate(cfg.layer_types):
            pre = f'layers.{i}.'
            p = {}
            for k, v in params.items():
                if k.startswith(pre):
                    leaf = k[len(pre) :]
                    # collapse "self_attn.q_proj.weight" -> "q_proj", "linear_attn.A" -> "A", "mlp.gate_proj.weight" -> "gate_proj"
                    parts = leaf.split('.')
                    if parts[-1] == 'weight':
                        parts = parts[:-1]
                    p[parts[-1]] = v
            self.blocks.append(Block(cfg, kind, p))

    # loading

    @classmethod
    def from_source(
        cls,
        src: TensorSource,
        device='cpu',
        dtype=torch.bfloat16,
        verbose=True,
        quant: str | None = None,
        group: int = 64,
    ) -> "Qwen35":
        """
        quant: None (weights in `dtype`), 'int8' or 'int4' (weight-only affine, see quant.py). If the source already
        holds MLX-quantized tensors at the requested width they are re-packed as-is; otherwise weights are quantized
        on `device` after loading.
        """

        cfg = src.config
        if quant is not None and quant not in QUANT_BITS:
            raise ValueError(f'quant must be one of {list(QUANT_BITS)}, got {quant!r}')
        bits = QUANT_BITS[quant] if quant else None
        if cfg.rope_scaling:
            print(
                f'[model] WARNING: rope_scaling={cfg.rope_scaling} present; only plain RoPE is implemented '
                f'(fine for prompts within the original context length)',
            )
        params: dict[str, torch.Tensor] = {}
        available = set(src.names())
        names = required_param_names(cfg)
        missing = [n for n in names if n not in available]
        if missing:
            raise KeyError(
                f'source is missing {len(missing)} tensors, e.g. {missing[:5]}',
            )
        if 'lm_head.weight' in available and not cfg.tied_embeddings:
            names.append('lm_head.weight')
        n_native = n_quant = 0
        for n_i, name in enumerate(names):
            p: Param | None = None
            if bits is not None and not any(s in name for s in KEEP_F32 + NO_QUANT):
                nq = src.get_quant(name)
                if nq is not None and nq.bits == bits:
                    p = from_native(
                        torch.from_numpy(np.array(nq.values, copy=True)).to(device),
                        torch.from_numpy(np.array(nq.scale, dtype=np.float32, copy=True)).to(device),
                        torch.from_numpy(np.array(nq.bias, dtype=np.float32, copy=True)).to(device),
                        nq.bits,
                        nq.group,
                        dtype,
                    )
                    n_native += 1
            if p is None:
                t = torch.from_numpy(np.array(src.get(name), dtype=np.float32, copy=True)).to(device)
                if any(s in name for s in KEEP_F32):
                    p = t
                elif bits is not None and is_quantizable(name, t, group):
                    p = quantize(t, bits, group, dtype)
                    n_quant += 1
                else:
                    p = t.to(dtype)
            params[name] = p
            if verbose and (n_i % 50 == 0 or n_i == len(names) - 1):
                print(
                    f'\r[model] loading tensors {n_i + 1}/{len(names)}',
                    end='',
                    flush=True,
                )
        model = cls(cfg, params, device, dtype)
        if verbose:
            q_note = f', {n_native} re-packed + {n_quant} quantized to {quant}' if bits else ''
            print(f'\n[model] {model.nbytes / 2**30:.2f} GiB of weights on {device}{q_note}')
        return model

    # forward

    @torch.no_grad()
    def forward(
        self,
        tokens: torch.Tensor,
        cache: Cache | None = None,
        start_pos: int | None = None,
        last_only: bool = False,
    ) -> torch.Tensor:
        """tokens: [B, T] int64. Returns logits [B, T, V] (or [B, 1, V] with last_only) in float32."""

        c = self.cfg
        B, T = tokens.shape
        if start_pos is None:
            start_pos = cache.seq_len if cache is not None else 0
        pos = torch.arange(start_pos, start_pos + T, device=self.device)
        cos, sin = rope_cos_sin(pos, c.rope_dim, c.rope_theta, self.device, dtype=self.dtype)
        x = embedding(tokens, self.embed, self.dtype)
        for i, blk in enumerate(self.blocks):
            x = blk(x, cos, sin, cache.layers[i] if cache is not None else None)
        if cache is not None:
            cache.seq_len = start_pos + T
        if last_only:
            x = x[:, -1:]
        x = rms_norm(x, self.norm_w, c.rms_eps)
        return linear(x, self.lm_head).float()

    @torch.no_grad()
    def generate(
        self,
        prompt_ids: list[int],
        max_new_tokens: int = 64,
        eos_ids: set[int] | None = None,
        on_token=None,
    ) -> list[int]:
        """Greedy decoding with the cache. Yields token ids through on_token as they are produced."""

        cache = Cache(self.cfg)
        ids = torch.tensor([prompt_ids], dtype=torch.long, device=self.device)
        logits = self.forward(ids, cache, last_only=True)
        out: list[int] = []
        for _ in range(max_new_tokens):
            nxt = int(logits[0, -1].argmax())
            out.append(nxt)
            if on_token:
                on_token(nxt)
            if eos_ids and nxt in eos_ids:
                break
            logits = self.forward(
                torch.tensor([[nxt]], device=self.device), cache, last_only=True,
            )
        return out
