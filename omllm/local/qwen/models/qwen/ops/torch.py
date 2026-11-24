# ruff: noqa: N803
"""The Qwen families' operations on the torch backend: the DeltaNet step as one Triton kernel (torchkernels.py)."""
from omcore import check

from ....backends.torch import TorchOps
from ....ops.base import Ops
from . import torchkernels
from .base import QwenOps


##


class TorchQwenOps(QwenOps):
    def __init__(self, ops: Ops) -> None:
        super().__init__(ops)

        self._torch = check.isinstance(ops, TorchOps)

        self.gdn_block_dv = 16  # the fused step's value-dim slice per program (a state tile [dk, block_dv] float32)
        self.gdn_num_warps = 1

        # the Triton kernel runs the recurrence for any number of tokens, so the model's fused path (`gdn_step`)
        # serves prefill chunks too; without it, only the few tokens of a decode / verify step (the composed step)
        if self._torch.triton:
            self.gdn_fused_max_t = 1 << 30
            torchkernels.ensure_qwen_kernels()  # jit now: the wrapper must find a real JITFunction when traced

    @classmethod
    def serves(cls, ops: Ops) -> bool:
        return isinstance(ops, TorchOps)

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
        if self._torch.triton:
            return torchkernels.gdn_step(
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
                self.gdn_block_dv,
                self.gdn_num_warps,
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
