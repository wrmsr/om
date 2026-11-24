# ruff: noqa: N803
"""The Qwen families' operations on the MLX backend: the DeltaNet step as one Metal kernel (mlxmetal.py)."""
from omcore import check

from ....backends.mlx import MlxOps
from ....ops.base import Ops
from . import mlxmetal
from .base import QwenOps


##


class MlxQwenOps(QwenOps):
    def __init__(self, ops: Ops) -> None:
        super().__init__(ops)

        self._mlx = check.isinstance(ops, MlxOps)

        self.gdn_variant = 'simd'  # 'simd' (registers + shuffles) | 'tg' (threadgroup-memory tile, the fallback)
        self.gdn_tgv = 16
        self.gdn_ks = 8

    @classmethod
    def serves(cls, ops: Ops) -> bool:
        return isinstance(ops, MlxOps)

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
        if self._mlx.metal:
            return mlxmetal.gdn_step_metal(
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
                self.gdn_tgv,
                self.gdn_variant,
                self.gdn_ks,
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
