# ruff: noqa: N803 N806 N812
import abc
import typing as ta

from omcore import check
from omcore import lang

from ..core.cache import Cache
from ..core.errors import Cancelled
from ..core.mixing import StateLayout
from ..ops.base import Array
from .rounds import Verified


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


if ta.TYPE_CHECKING:
    from ..core.model import Qwen35


##


def _pow2_at_least(n: int, floor: int = 8) -> int:
    c = floor
    while c < n:
        c *= 2
    return c


class TargetDecoder(lang.Abstract):
    """
    The target model's decode state past the prompt: steps over T tokens at the current position without committing
    (`verify`), then keeps the state after a prefix of them (`commit`). `Decoder` is the fast one (captured static
    steps over fixed-capacity buffers); `FunctionalDecoder` is the reference it is checked against.
    """

    seq_len: int

    @abc.abstractmethod
    def verify(self, toks: Array, *, all_states: bool = True) -> Verified:
        """
        T tokens ([1, T] int32 on the device) at positions seq_len..seq_len+T-1. With all_states the result can be
        committed at any prefix; without, only whole (which is all a one-token step needs).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def commit(self, verified: Verified, n: int) -> None:
        """Keep the state after the first n tokens of `verified` (0 keeps nothing)."""

        raise NotImplementedError

    @abc.abstractmethod
    def ensure_capacity(self, n: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def export_cache(self) -> Cache:
        """The state as a functional `Cache`: exact-length KV, copied."""

        raise NotImplementedError


class Decoder(TargetDecoder):
    """
    Fixed-capacity decode state plus the captured step.

    Built from a `Cache` after prefill: the KV of every attention layer is carried in buffers of `capacity` positions
    (copied into zero-padded ones -- unless the prefill already filled buffers of that size, `Model.prefill`'s
    `reserve`, which are then adopted as they are), the DeltaNet (conv, S) pairs are carried as-is, and the position
    becomes a 0-d device array.
    `step(tok)` runs the captured `decode_fn`; the only host<->device traffic per token is the token id in and the
    logits out. When the sequence reaches capacity the buffers are doubled and the step re-captured.

    Attention over the buffers is length-bucketed: on backends whose `sdpa_static` reads the whole buffer it is
    given (`ops.attn_bucketed`), the step is captured per power-of-two window covering the positions in use, from
    `MIN_BUCKET` up to the capacity, so a decode step's attention cost follows the sequence rather than the
    capacity; a new window is a new (cheap) capture as the sequence crosses each power of two. Backends whose
    attention kernel reads `pos` itself run one step for the whole capacity.
    """

    MIN_BUCKET = 1024

    @staticmethod
    def capacity_for(capacity: int | None, seq_len: int) -> int:
        """The buffer positions a decoder asked for `capacity` allocates when it starts from `seq_len` tokens."""

        c = _pow2_at_least(capacity or (seq_len + 1))
        if c <= seq_len:
            c = _pow2_at_least(seq_len + 1)
        return c

    def __init__(
            self,
            model: Qwen35,
            cache: Cache,
            capacity: int | None = None,
            *,
            consume: bool = False,
    ) -> None:
        """
        From a functional cache's state (a prefill's, a snapshot's), laid out in buffers of `capacity` positions.
        `consume`: the cache is the caller's to give away -- each layer's state is released as soon as it is in its
        buffer, so the exact-length KV and the buffers are never both held whole. At the full 262k window that is
        8.6 GB of fp8 KV (17 at bf16) not held twice, which a 32 GB card cannot afford next to the 27B's weights.
        """

        super().__init__()

        if model.ops.taps is not None:
            raise RuntimeError('taps must be off for the static decoder')
        self.model = model
        self.ops = model.ops
        self.seq_len = cache.seq_len
        self.capacity = self.capacity_for(capacity, self.seq_len)
        self._layouts = model.state_layouts()  # each layer's mixer says how its state is carried
        self.flat: list[Array] = []
        for i, (st, layout) in enumerate(zip(cache.layers, self._layouts)):
            if st is None:
                if cache.seq_len:
                    raise ValueError('cache has no state; run a prefill first')
                st = layout.empty(self.ops, model.dtype)  # a decoder starting from nothing (see `prefill`)
            elif consume:
                cache.layers[i] = None
            # padded layer by layer, so with `consume` only one layer's state is ever held in both forms
            st = layout.pad(self.ops, layout.adapt(self.ops, st, model.dtype), self.capacity)
            self.flat.extend(st)
            del st
        self._alloc(self.capacity, first=True)

    def _layers(self, flat: ta.Sequence[Array]) -> ta.Iterator[tuple[StateLayout, tuple[Array, ...]]]:
        for (o, n), layout in zip(self.model.state_offsets(), self._layouts):
            yield layout, tuple(flat[o:o + n])

    # the static prefill's step length: every chunk of a prompt runs as one `PREFILL_T`-token verify step (the last
    # one padded, its pad positions rewritten by the next step before anything reads them), so one captured step
    # serves every prompt. Small enough to capture quickly (its DeltaNet recurrence is sequential per token).
    PREFILL_T: ta.ClassVar[int] = 16

    def prefill(
            self,
            tokens: ta.Sequence[int],
            should_stop: ta.Callable[[], bool] | None = None,
    ) -> tuple[Array, Array]:
        """
        The prompt through the captured step, `PREFILL_T` tokens at a time, committing each chunk (for a backend
        whose `forward` would be scheduled eagerly: `Ops.static_prefill`). Returns what `Qwen35.prefill` returns:
        the last position's logits [B, 1, V] and the final-normed hidden states of every position [B, T, hidden].
        """

        ops = self.ops
        T = self.PREFILL_T

        toks = [int(t) for t in tokens]
        if not toks:
            raise ValueError('nothing to prefill')

        hiddens: list[Array] = []
        last: Array | None = None
        for start in range(0, len(toks), T):
            if should_stop is not None and should_stop():
                raise Cancelled

            chunk = toks[start:start + T]
            n = len(chunk)
            ids = np.asarray(chunk + [chunk[-1]] * (T - n), dtype=np.int32).reshape(1, T)
            verified = self.verify(ops.array(ids))

            self.commit(verified, n)

            hiddens.append(verified.hidden[:, :n] if n < T else verified.hidden)
            last = verified.logits[:, n - 1:n]

        return check.not_none(last), (hiddens[0] if len(hiddens) == 1 else ops.concat(hiddens, 1))

    def _pad_to(self, capacity: int) -> None:
        """Every layer's state in buffers of `capacity` positions (a no-op for fixed-size states and full buffers)."""

        flat: list[Array] = []
        for layout, st in self._layers(self.flat):
            flat.extend(layout.pad(self.ops, st, capacity))
        self.flat = flat

    def _alloc(self, capacity: int, first: bool = False) -> None:
        self.capacity = capacity
        if not first:  # (the constructor has laid each layer's state out already, as it took it)
            self._pad_to(capacity)
        self.ar, self.cos_tab, self.sin_tab = self.model.decode_tables(capacity)

        self.fns: dict[tuple[int, bool, bool, int], ta.Callable[..., tuple[Array, ...]]] = {}

    def bucket(self, n: int) -> int:
        """The attention window for a step whose last position is n - 1: 0 (whole buffer) unless the backend buckets."""

        if not self.ops.attn_bucketed:
            return 0
        b = self.MIN_BUCKET
        while b < n:
            b *= 2
        return min(b, self.capacity)

    def _fn(self, T: int, all_states: bool, return_hidden: bool) -> ta.Callable[..., tuple[Array, ...]]:
        """The captured step for a given shape and the current attention window, built on first use."""

        key = (T, all_states, return_hidden, self.bucket(self.seq_len + T))
        if key not in self.fns:
            self.fns[key] = self.ops.capture(self.model.step_fn(T, all_states, return_hidden, key[3]))
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
        out = self._fn(1, False, True)(ops.array(ids), ops.scalar(self.seq_len), *self.tables(), *self.flat)

        self.flat = list(out[2:])
        self.logits_last = out[0][:, 0]  # [B, V]
        self.hidden_last = out[1][:, -1:]  # [B, 1, H]

        self.seq_len += 1
        return out[0][:, 0]

    def export_cache(self) -> Cache:
        """The functional `Cache` equivalent of the static state: exact-length KV, copied."""

        c = Cache(self.model.cfg)
        c.seq_len = self.seq_len
        for i, (layout, st) in enumerate(self._layers(self.flat)):
            c.layers[i] = layout.export(self.ops, st, self.seq_len)
        return c

    def verify(self, toks: Array, *, all_states: bool = True) -> Verified:
        """
        Run T tokens ([1, T] int32 on the device) at positions seq_len.. in one captured step. With all_states the
        DeltaNet entries of the returned state are stacked per token (speculative verify, the static prefill), so a
        commit can keep any prefix. Nothing is committed until `commit`.
        """

        ops = self.ops
        T = toks.shape[1]

        self.ensure_capacity(self.seq_len + T)

        out = self._fn(T, all_states, True)(toks, ops.scalar(self.seq_len), *self.tables(), *self.flat)

        return Verified(out[0], out[1], list(out[2:]), all_states)

    def commit(self, verified: Verified, n: int) -> None:
        """
        Keep the state after the first n verified tokens (the KV buffers need no rollback: positions past the commit are
        masked by `pos` and overwritten by the next step).
        """

        if n <= 0:
            return

        if not verified.stacked and n != verified.logits.shape[1]:
            raise ValueError('a step without per-token states commits whole')

        flat: list[Array] = []
        for layout, st in self._layers(verified.states):
            flat.extend(layout.commit(self.ops, st, n, verified.stacked))

        self.flat = flat
        self.seq_len += n

    def snapshot(self) -> tuple[int, list[Array]]:
        """(seq_len, copies of the state) -- the prefix-cache primitive for the static path."""

        return self.seq_len, [self.ops.copy(a) for a in self.flat]

    def restore(self, snap: tuple[int, list[Array]]) -> None:
        self.seq_len, flat = snap
        self.flat = [self.ops.copy(a) for a in flat]

        snap_cap = max(
            (cap for layout, st in self._layers(self.flat) if (cap := layout.capacity(self.ops, st)) is not None),
            default=0,
        )

        if snap_cap > self.capacity:
            self._alloc(snap_cap)  # snapshot taken after a growth; the step must be re-captured for its shapes
        else:
            self._pad_to(self.capacity)


class FunctionalDecoder(TargetDecoder):
    """
    The reference decoder: one `Qwen35.forward` per token on the growing functional cache, keeping a copy of the cache
    after every token so a commit can choose any of them. Slow, obviously right, and backend-agnostic -- what the static
    `Decoder` is checked against (`generate(..., static=False)`, `entrypoints/generate --functional`).
    """

    def __init__(self, model: Qwen35, cache: Cache) -> None:
        super().__init__()

        self.model = model
        self.ops = model.ops
        self.cache = cache
        self.seq_len = cache.seq_len

    def verify(self, toks: Array, *, all_states: bool = True) -> Verified:
        ops = self.ops
        ids = [int(t) for t in ops.numpy(toks).reshape(-1)]

        logits: list[Array] = []
        hidden: list[Array] = []
        caches: list[Cache] = []

        cache = self.cache
        for t in ids:
            cache = cache.snapshot(ops)
            lg, h = self.model.forward(np.asarray([[t]], dtype=np.int32), cache, return_hidden=True)
            logits.append(lg)
            hidden.append(h)
            caches.append(cache)

        return Verified(
            ops.concat(logits, 1),
            ops.concat(hidden, 1),
            caches,
            True,
        )

    def commit(self, verified: Verified, n: int) -> None:
        if n > 0:
            self.cache = verified.states[n - 1]
            self.seq_len = self.cache.seq_len

    def ensure_capacity(self, n: int) -> None:
        pass

    def export_cache(self) -> Cache:
        return self.cache.snapshot(self.ops)
