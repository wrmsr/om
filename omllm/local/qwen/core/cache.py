# ruff: noqa: N803 N806 N812
from ..ops.base import Array
from ..ops.base import Ops
from .config import Qwen35Config


FullState = tuple[Array, ...]  # the backend's KV state: (k, v) [B, n_kv, T, hd] by default; see Ops.kv_arity
LinearState = tuple[Array, Array]  # conv: [B, conv_dim, kernel-1] last inputs to the conv; state: [B, n_v, dk, dv]


##


class Cache:
    """
    One entry per layer. Attention layers grow a KV cache; linear layers keep a fixed-size (conv window, recurrent
    state) pair -- so 'prefix caching' for 3/4 of the stack is just snapshotting a tensor.
    """

    def __init__(self, cfg: Qwen35Config) -> None:
        super().__init__()

        self.layers: list[FullState | LinearState | None] = [None] * cfg.num_layers
        self.seq_len = 0

    def snapshot(self, ops: Ops) -> Cache:
        c = Cache.__new__(Cache)
        c.seq_len = self.seq_len
        c.layers = [None if st is None else tuple(ops.copy(a) for a in st) for st in self.layers]
        return c
