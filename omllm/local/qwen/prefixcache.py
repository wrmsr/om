# ruff: noqa: N803 N806 N812
"""
Prefix snapshots: exact-prefix reuse of decode state across requests, with a device tier and a host tier.

An agent loop's next request is almost always the previous one plus the model's answer plus a tool result, so after
every prefill and every generation the state is snapshotted under its token ids, and a new request resumes from the
longest cached snapshot whose tokens are a prefix of its own -- prefilling only what is new. For this hybrid model that
is the only kind of reuse possible: the DeltaNet layers' state is a fixed-size recurrence that cannot be rewound to an
arbitrary earlier position, so snapshots are taken at request boundaries (prompt end, generation end) and matched whole,
never split.

What a snapshot holds (all on the device while resident): the functional `Cache` (exact-length KV for the attention
layers, the (conv, S) pairs for the DeltaNet ones), the target's logits for the next position and its final-normed
hidden state at the last position (so a request that matches completely, or the draft head, need nothing recomputed),
and the draft head's KV for the entries before the last position when the MTP head is loaded. A 27B snapshot is ~150 MB
of DeltaNet state plus 32 KB per token of KV.

Tiers: a device LRU with a byte budget; entries evicted from it move to a host LRU (pinned memory on torch/CUDA, so a 1
GB snapshot crosses PCIe in well under a second; the array itself on unified-memory or CPU backends) with its own
budget, or are dropped. A hit on a host entry promotes it back. Matching is on token ids exactly, so a harness should
keep the ids it was given rather than re-tokenise text (BPE is not idempotent across a boundary), and anything that
rewrites earlier turns -- stripping reasoning blocks, editing history -- breaks the prefix.
"""
import typing as ta

from omcore import dataclasses as dc

from .ops import Array
from .ops import Ops


##


@dc.dataclass()
class Snapshot:
    tokens: tuple[int, ...]  # the n tokens the state has processed
    cache: ta.Any  # model.Cache with seq_len == n
    logits: Array  # [1, V] float32: the target's logits for position n
    hidden: Array  # [1, 1, hidden]: the target's final-normed hidden state at position n-1
    mtp_kv: tuple[Array, Array] | None  # draft-head KV for entries 0..n-2, when the head is loaded

    @property
    def n(self) -> int:
        return len(self.tokens)

    def arrays(self) -> list[Array]:
        out: list[Array] = [self.logits, self.hidden]
        for st in self.cache.layers:
            if st is not None:
                out.extend(st)
        if self.mtp_kv is not None:
            out.extend(self.mtp_kv)
        return out

    def map(self, fn: ta.Callable[[Array], Array]) -> Snapshot:
        """A new Snapshot with `fn` applied to every array (copy, to_host, from_host)."""

        cache = type(self.cache).__new__(type(self.cache))  # type: ignore[call-overload]
        cache.seq_len = self.cache.seq_len
        cache.layers = [None if st is None else tuple(fn(a) for a in st) for st in self.cache.layers]
        return Snapshot(
            self.tokens,
            cache,
            fn(self.logits),
            fn(self.hidden),
            None if self.mtp_kv is None else (fn(self.mtp_kv[0]), fn(self.mtp_kv[1])),
        )

    def nbytes(self, ops: Ops) -> int:
        return sum(ops.nbytes(a) for a in self.arrays())


@dc.dataclass()
class _Entry:
    snap: Snapshot
    tier: str  # 'device' | 'host'
    nbytes: int
    tick: int  # last use; larger is more recent


class PrefixCache:
    def __init__(
            self,
            ops: Ops,
            device_bytes: int,
            host_bytes: int = 0,
    ) -> None:
        self.ops = ops
        self.device_bytes = device_bytes
        self.host_bytes = host_bytes
        self.entries: dict[tuple[int, ...], _Entry] = {}
        self.tick = 0
        self.hits = 0
        self.misses = 0
        self.matched_tokens = 0

    # accounting

    def used(self, tier: str) -> int:
        return sum(e.nbytes for e in self.entries.values() if e.tier == tier)

    def _touch(self, e: _Entry) -> None:
        self.tick += 1
        e.tick = self.tick

    def _lru(self, tier: str) -> _Entry | None:
        cands = [e for e in self.entries.values() if e.tier == tier]
        return min(cands, key=lambda e: e.tick) if cands else None

    def _drop(self, e: _Entry) -> None:
        del self.entries[e.snap.tokens]

    def _demote(self, e: _Entry) -> None:
        """Device -> host, or drop when the host tier has no room even after evicting its own LRU entries."""

        if self.host_bytes <= 0 or e.nbytes > self.host_bytes:
            self._drop(e)
            return
        while self.used('host') + e.nbytes > self.host_bytes:
            victim = self._lru('host')
            if victim is None:
                break
            self._drop(victim)
        e.snap = e.snap.map(self.ops.to_host)
        e.tier = 'host'

    def _make_room(self, nbytes: int, keep: _Entry | None = None) -> bool:
        """Free device budget for `nbytes` by demoting device LRU entries (never `keep`)."""

        if nbytes > self.device_bytes:
            return False
        while self.used('device') + nbytes > self.device_bytes:
            cands = [e for e in self.entries.values() if e.tier == 'device' and e is not keep]
            if not cands:
                return False
            self._demote(min(cands, key=lambda e: e.tick))
        return True

    # api

    def put(self, snap: Snapshot) -> None:
        """
        Store a snapshot, taking ownership of its arrays (pass copies if the state stays live elsewhere). Replaces an
        entry with the same tokens; demotes device LRU entries to make room; drops the snapshot if it cannot fit.
        """

        old = self.entries.pop(snap.tokens, None)
        if old is not None:
            del old
        nbytes = snap.nbytes(self.ops)
        if not self._make_room(nbytes):
            return
        e = _Entry(snap, 'device', nbytes, 0)
        self.entries[snap.tokens] = e
        self._touch(e)

    def lookup(self, tokens: ta.Sequence[int]) -> Snapshot | None:
        """
        The longest snapshot whose tokens are a prefix of `tokens`, as a private copy on the device (the entry itself
        stays cached), promoted from the host tier if that is where it lived. None when nothing matches.
        """

        toks = tuple(tokens)
        best: _Entry | None = None
        for e in self.entries.values():
            n = len(e.snap.tokens)
            if n <= len(toks) and (best is None or n > len(best.snap.tokens)) and toks[:n] == e.snap.tokens:
                best = e
        if best is None:
            self.misses += 1
            return None
        self.hits += 1
        self.matched_tokens += len(best.snap.tokens)
        self._touch(best)
        if best.tier == 'host':
            if not self._make_room(best.nbytes, keep=best):
                # no device room even after demotions: hand back a device copy without keeping one resident
                return best.snap.map(self.ops.from_host)
            best.snap = best.snap.map(self.ops.from_host)
            best.tier = 'device'
        return best.snap.map(self.ops.copy)

    def stats(self) -> str:
        n_dev = sum(e.tier == 'device' for e in self.entries.values())
        n_host = len(self.entries) - n_dev
        return (
            f'{self.hits} hits / {self.misses} misses, {self.matched_tokens} tokens reused; '
            f'device {n_dev} entries {self.used("device") / 2**20:.0f} MiB, '
            f'host {n_host} entries {self.used("host") / 2**20:.0f} MiB'
        )
