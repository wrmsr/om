# ruff: noqa: N803 N806 N812
from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import FeedForward


##


class MLP(FeedForward):
    def __init__(self, p: dict[str, Weight]) -> None:
        super().__init__()

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
