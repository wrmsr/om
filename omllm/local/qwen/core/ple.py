# ruff: noqa: N803 N806
"""
Flash-Next's n-gram layer, "PLE" (transformers' Qwen4ExpTextNGramEmbedding and Qwen4ExpTextPLELayer; FLASHNEXT.md §0,
§4.4, and §4.4.1, which this implements). On its layers, before the gated residual's read, the block adds

    e = the table's rows at the token's n-gram ids, one per hash head, side by side
    key = rmsnorm per branch (W_key . e)      value = W_value . e      q = rmsnorm per branch (R)
    s_b = signed sqrt((key_b . q_b) / sqrt(hidden))                    v_b = sigmoid(s_b) * value
    addend = v + silu(conv(rmsnorm per branch (v)))      a causal depthwise conv, dilation n

into every branch of the stream R. The ids hash each token with up to n - 1 predecessors within its EOS-delimited
segment: `(n - 1) x heads_per_ngram` heads (the bigram heads, then the trigram heads, ...), each the n-gram's
`XOR_j token_j * m_j` mod its own prime, offset into one table. Everything is integer arithmetic below 2^63, so the ids
are exact in int64 -- computed by one formulation, on the host (NumpyOps) for the functional form and on the device for
the static step, with the same bits.

The state is the last n - 1 tokens (the hash's context) and the conv's last (K - 1) n inputs. The table is a device
weight gathered by `Ops.embedding`; a host-resident table feeding the step its rows is FLASHNEXT.md phase 5.
"""
import math
import typing as ta

import numpy as np

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from ..ops.reference import NumpyOps
from .config import Qwen4ExpConfig
from .mixing import LayerEmbedding
from .mixing import StateLayout
from .mixing import StepContext


##


SPLITMIX64_GAMMA = 0x9E3779B97F4A7C15
SPLITMIX64_MASK = (1 << 64) - 1


def splitmix64(x: int) -> int:
    """SplitMix64's output function (Steele, Lea and Flood 2014) of a 64-bit input: the increment, then the mix."""

    x = (x + SPLITMIX64_GAMMA) & SPLITMIX64_MASK
    z = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & SPLITMIX64_MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & SPLITMIX64_MASK
    return z ^ (z >> 31)


def ngram_multipliers(*, n: int, vocab_size: int, seed: int, ple_index: int) -> list[int]:
    """
    The hash's n odd multipliers for the PLE layer `ple_index`, each below (2^63 - 1) / vocab_size, so that a token id
    times one fits in int64.
    """

    bound = max(1, ((2**63 - 1) // max(vocab_size, 1)) // 2)
    base = seed + 10007 * ple_index
    return [
        2 * (splitmix64((base + SPLITMIX64_GAMMA * (j + 1)) & SPLITMIX64_MASK) % bound) + 1
        for j in range(n)
    ]


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, math.isqrt(n) + 1, 2))


def ngram_primes(base: int, count: int) -> list[int]:
    """The `count` smallest primes that are at least `base`."""

    out: list[int] = []
    c = base
    while len(out) < count:
        if _is_prime(c):
            out.append(c)
        c += 1
    return out


class NGramStateLayout(StateLayout):
    """
    The n-gram layer's state: the last n - 1 tokens, int32 [B, n - 1] (initially n - 1 EOS), and the conv's history,
    its last (K - 1) n inputs, float32 [B, hc * hidden, (K - 1) n] (initially zeros). Fixed-size, so nothing to pad; a
    T-token step that returns the state after every token commits by selecting one.
    """

    def __init__(self, *, context: int, channels: int, history: int, eos: int) -> None:
        super().__init__()

        self._context = context
        self._channels = channels
        self._history = history
        self._eos = eos

    def arity(self, ops: Ops) -> int:
        return 2

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        return (
            ops.array(np.full((1, self._context), self._eos, dtype=np.int32), ops.dtype('i32')),
            ops.zeros((1, self._channels, self._history), ops.dtype('f32')),
        )

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return state

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        # dense copies whatever came in: a compiled step is guarded on its inputs' strides (see RecurrentStateLayout)
        return tuple(ops.copy(a) for a in state)

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return tuple(ops.copy(a) for a in state)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        if not stacked:
            return state
        return tuple(ops.copy(ops.select(a, n - 1)) for a in state)

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return None


class NGramLayerEmbedding(LayerEmbedding):
    """
    The n-gram layer of the PLE layer `ple_index` (its index among `cfg.ple_layers`, which numbers its hash heads and
    seeds its multipliers). `p`: the table `ngram_embedding` [rows, ple_embed_dim / heads], `key_proj` [hc * hidden,
    ple_embed_dim], `value_proj` [hidden, ple_embed_dim], the norms `norm_key`, `norm_query`, `norm_conv` ([hc, hidden],
    the +1 applied) and `conv1d` [hc * hidden, K] (float32).
    """

    def __init__(self, cfg: Qwen4ExpConfig, ple_index: int, p: ta.Mapping[str, Weight]) -> None:
        super().__init__()

        if cfg.ngram_size < 2:
            raise ValueError(f'an n-gram layer needs ngram_size >= 2, not {cfg.ngram_size}')

        self.cfg = cfg
        self.n = cfg.ngram_size
        self.eos = cfg.eos_id
        self.hc = cfg.hc_count
        self.hidden = cfg.hidden_size
        self.kernel = cfg.ple_conv_kernel

        # the hash: one multiplier per shift, and per head (bigrams first) a prime vocabulary and its offset
        heads = (self.n - 1) * cfg.heads_per_ngram
        self.multipliers = ngram_multipliers(
            n=self.n,
            vocab_size=cfg.vocab_size,
            seed=cfg.ngram_seed,
            ple_index=ple_index,
        )
        self.sizes = ngram_primes(cfg.ngram_vocab_size_base, (ple_index + 1) * heads)[ple_index * heads:]
        self.offsets = [sum(self.sizes[:h]) for h in range(heads)]

        self.table = p['ngram_embedding']
        self.w_key = p['key_proj']
        self.w_value = p['value_proj']
        self.norm_key = p['norm_key']
        self.norm_query = p['norm_query']
        self.norm_conv = p['norm_conv']
        self.conv_w = p['conv1d']

        self._state = NGramStateLayout(
            context=self.n - 1,
            channels=self.hc * self.hidden,
            history=(self.kernel - 1) * self.n,
            eos=self.eos,
        )
        self._host = NumpyOps()  # the functional form hashes on the host, through the step's own formulation

    @property
    def state(self) -> StateLayout:
        return self._state

    def _ids(self, ops: Ops, hist: Array) -> Array:
        """
        The n-gram ids [B, T, heads] (int64) of the last T tokens of `hist` [B, n - 1 + T] (the context, then the new
        tokens). Shifted tokens are slices of the history, each EOS instead when an EOS lies at or after it before the
        current token; fixed shapes and integer arithmetic only, so it runs inside a captured step as on the host.
        """

        n = self.n
        E = self.eos
        hpn = self.cfg.heads_per_ngram
        i64 = ops.dtype('i64')
        T = hist.shape[1] - (n - 1)

        h = ops.cast(hist, i64)
        x = h[:, n - 1:] * self.multipliers[0]
        live = None
        ids = []
        for s in range(1, n):
            prev = h[:, n - 1 - s:n - 1 - s + T]  # each token's s-th predecessor
            ok = ops.cast(prev != E, i64)
            live = ok if live is None else live * ok  # no EOS among the s tokens before the current one
            x = x ^ ((E + (prev - E) * live) * self.multipliers[s])  # the order s + 1 n-gram's hash
            for g in range((s - 1) * hpn, s * hpn):
                ids.append(x % self.sizes[g] + self.offsets[g])
        return ops.stack(ids, -1)

    def _addend(
            self,
            ops: Ops,
            r: Array,
            ids: Array,
            conv: Array,
            all_states: bool,
    ) -> tuple[Array, Array]:
        """The addend [B, T, hc * hidden] in r's dtype, and the conv's history after the T tokens (or after each)."""

        c = self.cfg
        B, T, _ = r.shape
        hc = self.hc
        H = self.hidden
        n = self.n
        K = self.kernel
        f32 = ops.dtype('f32')

        e = ops.embedding(ids, self.table, r.dtype)  # [B, T, heads, ple_embed_dim / heads]
        e = ops.reshape(e, (B, T, e.shape[-2] * e.shape[-1]))

        key = ops.rms_norm(ops.reshape(ops.linear(e, self.w_key), (B, T, hc, H)), self.norm_key, c.rms_eps)
        value = ops.linear(e, self.w_value)  # [B, T, H]: one for every branch
        q = ops.rms_norm(ops.reshape(r, (B, T, hc, H)), self.norm_query, c.rms_eps)

        # each branch's gate: sigmoid of the signed square root of its scaled key . query, |s| floored at 1e-6 (the
        # floor is exact either way: a product with 1 or 0 and a sum with 0)
        s = ops.sum(ops.f32(key) * ops.f32(q), -1) / math.sqrt(H)  # [B, T, hc]
        sign = ops.cast(s > 0, f32) - ops.cast(s < 0, f32)
        mag = s * sign
        tiny = ops.cast(mag < 1e-6, f32)
        mag = mag * (1 - tiny) + tiny * 1e-6
        gate = ops.sigmoid(sign * (mag * ops.rsqrt(mag)))
        v = ops.cast(gate, value.dtype)[..., None] * value[:, :, None, :]  # [B, T, hc, H]

        # the causal depthwise conv, dilation n, over the normed v with its history before it: output t is
        # sum_j w[:, j] u(t - (K - 1 - j) n), and u(t - (K - 1 - j) n) sits at j n + t of [history | u]
        u = ops.f32(ops.reshape(ops.rms_norm(v, self.norm_conv, c.rms_eps), (B, T, hc * H)))
        inp = ops.concat([conv, ops.transpose(u, (0, 2, 1))], -1)  # [B, hc H, (K - 1) n + T]
        y = None
        for j in range(K):
            term = inp[:, :, j * n:j * n + T] * self.conv_w[:, j][None, :, None]
            y = term if y is None else y + term

        add = ops.f32(ops.reshape(v, (B, T, hc * H))) + ops.silu(ops.transpose(y, (0, 2, 1)))

        W = (K - 1) * n
        if all_states:
            conv_out = ops.stack([inp[:, :, t + 1:t + 1 + W] for t in range(T)], 0)  # [T, B, hc H, W]
        else:
            conv_out = ops.copy(inp[:, :, T:])  # dense: a slice's strides would depend on T (NGramStateLayout.pad)

        return ops.cast(add, r.dtype), conv_out

    def __call__(
            self,
            ops: Ops,
            r: Array,
            ids: ta.Any,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        """The functional form: the ids hashed on the host, the context read back from the state."""

        if ids is None:
            raise ValueError('the n-gram layer needs the token ids')

        B, T, _ = r.shape
        n = self.n

        toks = np.asarray(ids, dtype=np.int64).reshape(B, T)
        if state is None:
            ctx = np.full((B, n - 1), self.eos, dtype=np.int64)
            conv = ops.zeros((B, self.hc * self.hidden, (self.kernel - 1) * n), ops.dtype('f32'))
        else:
            ctx = np.asarray(ops.numpy(state[0]), dtype=np.int64)
            conv = state[1]
        hist = np.concatenate([ctx, toks], 1)  # [B, n - 1 + T]

        add, conv_out = self._addend(ops, r, ops.array(self._ids(self._host, hist)), conv, False)
        ctx_out = ops.array(np.ascontiguousarray(hist[:, T:], dtype=np.int32), ops.dtype('i32'))
        return add, (ctx_out, conv_out)

    def step(
            self,
            ops: Ops,
            r: Array,
            ctx: StepContext,
            state: tuple[Array, ...],
    ) -> tuple[Array, tuple[Array, ...]]:
        """The static form: the ids hashed on the device from the context and ctx.ids, the same bits as the host's."""

        if ctx.ids is None:
            raise ValueError('the n-gram layer in a static step needs the token ids in its StepContext')

        T = r.shape[1]
        n = self.n

        hist = ops.concat([state[0], ops.cast(ctx.ids, state[0].dtype)], 1)  # [B, n - 1 + T] int32
        add, conv = self._addend(ops, r, self._ids(ops, hist), state[1], ctx.all_states)

        if ctx.all_states:
            ctx_out = ops.stack([hist[:, t + 1:t + n] for t in range(T)], 0)  # [T, B, n - 1]
        else:
            ctx_out = ops.copy(hist[:, T:])
        return add, (ctx_out, conv)
