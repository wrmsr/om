# ruff: noqa: N803 N806
"""
Flash-Next's gated residual (transformers' Qwen4ExpTextGatedResidual; FLASHNEXT.md §0). The stream is `hc` branches of
`hidden` side by side, [B, T, hc * hidden], entered as the embedding repeated into each. A sublayer reads

    n = rmsnorm per branch (R)                    one norm, a weight per branch element
    g = sigmoid(W_up . silu(W_down . n / hc))     rank `hc_lowrank`
    x = mean over branches (g * n)                the sublayer's input: there is no other pre-norm

and writes `R + w_b * y` into every branch b, with `w = 2 sigmoid(W_inject . n / hc)` from the same `n`. The model's
exit is a read with no write (no final norm either).
"""
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import Connection
from .mixing import ResidualStream


##


class GatedResidualConnection(Connection):
    def __init__(
            self,
            *,
            hc: int,
            hidden: int,
            norm: Array,
            down: Weight,
            up: Weight,
            inject: Weight | None,
            eps: float,
    ) -> None:
        super().__init__()

        self.hc = hc
        self.hidden = hidden
        self.norm = norm  # [hc, hidden], the +1 applied
        self.down = down
        self.up = up
        self.inject = inject
        self.eps = eps

    def normed(self, ops: Ops, r: Array) -> Array:
        """Each branch of r [B, T, hc * hidden] rms-normed with its own weights."""

        B, T, _ = r.shape
        n = ops.rms_norm(ops.reshape(r, (B, T, self.hc, self.hidden)), self.norm, self.eps)
        return ops.reshape(n, (B, T, self.hc * self.hidden))

    def mix(self, ops: Ops, n: Array) -> Array:
        """The gated mean of the normed branches: [B, T, hidden]."""

        B, T, _ = n.shape
        g = ops.sigmoid(ops.linear(ops.silu(ops.linear(n, self.down) / self.hc), self.up))
        return ops.mean(ops.reshape(g * n, (B, T, self.hc, self.hidden)), -2)

    def read(self, ops: Ops, r: Array) -> tuple[Array, ta.Any]:
        if self.inject is None:
            raise TypeError('a gated residual connection without write weights only reads (the model exit)')
        n = self.normed(ops, r)
        w = ops.sigmoid(ops.linear(n, self.inject) / self.hc) * 2  # [B, T, hc]
        return self.mix(ops, n), w

    def write(self, ops: Ops, r: Array, y: Array, carry: ta.Any) -> Array:
        B, T, _ = r.shape
        add = y[:, :, None, :] * carry[..., None]  # [B, T, hc, hidden]
        return r + ops.reshape(add, (B, T, self.hc * self.hidden))


class GatedResidualStream(ResidualStream):
    def __init__(self, mixer: GatedResidualConnection) -> None:
        super().__init__()

        self.mixer = mixer  # the exit's read (no write weights)

    def enter(self, ops: Ops, x: Array) -> Array:
        return ops.concat([x] * self.mixer.hc, -1)

    def exit(self, ops: Ops, r: Array) -> Array:
        return self.mixer.mix(ops, self.mixer.normed(ops, r))
