"""
The residual stream is a seam (core/mixing.py): every path through the model -- the functional forward, the static
step, the draft head -- must read and write the stream only through its connections and ends, or a second strategy
(Flash-Next's gated residual) silently computes something else. A two-branch stream that is mathematically the plain
one pins that: the model built with it must produce exactly the plain model's tokens.
"""
import typing as ta

import numpy as np

from ...api import generate
from ...backends.torch import TorchOps
from ...core.mixing import Connection
from ...core.mixing import PlainConnection
from ...core.mixing import ResidualStream
from ...load.policies import QWEN35_LAYOUT
from ...load.recipe import LoadRecipe
from ...tests.test_parity import synthetic_source
from ..qwen35 import Qwen35Architecture


##


class TwoBranchResidual(ResidualStream):
    """The stream as two halves stacked on a branch axis; the final norm reads their sum. Equal to plain."""

    def __init__(self, norm, eps):
        super().__init__()

        self._final = PlainConnection(norm, eps)

    def enter(self, ops, x):
        return ops.stack([x * 0.5, x * 0.5], -2)

    def exit(self, ops, r):
        return self._final.read(ops, ops.sum(r, -2))[0]


class TwoBranchConnection(Connection):
    """Reads the norm of the branches' sum, writes into the first branch. Equal to plain."""

    def __init__(self, norm, eps):
        super().__init__()

        self._plain = PlainConnection(norm, eps)

    def read(self, ops, r) -> tuple[ta.Any, ta.Any]:
        return self._plain.read(ops, ops.sum(r, -2))

    def write(self, ops, r, y, carry):
        b0, b1 = ops.split(r, [1, 1], -2)
        return ops.concat([b0 + y[..., None, :], b1], -2)


class TwoBranchArchitecture(Qwen35Architecture):
    def _residual(self, cfg, norm):
        return TwoBranchResidual(norm, cfg.rms_eps)

    def _connection(self, cfg, norm):
        return TwoBranchConnection(norm, cfg.rms_eps)


def test_every_path_goes_through_the_residual_stream():
    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(3).integers(0, cfg.vocab_size, 9).tolist()
    ops = TorchOps('cpu', capture_mode='static')
    recipe = LoadRecipe(quant=None, group=64, search=True, policy='uniform')

    plain, _ = Qwen35Architecture().load(src, ops, recipe=recipe, dtype='f32', mtp=True)
    branched, _ = TwoBranchArchitecture().load(src, ops, recipe=recipe, dtype='f32', mtp=True)
    assert isinstance(branched.residual, TwoBranchResidual)
    assert isinstance(branched.blocks[0].mixer_conn, TwoBranchConnection)
    assert branched.mtp is not None and isinstance(branched.mtp.residual, TwoBranchResidual)
    assert Qwen35Architecture().layout is QWEN35_LAYOUT

    ids = np.asarray([prompt])
    a = ops.numpy(plain.forward(ids))
    b = ops.numpy(branched.forward(ids))
    assert np.abs(a - b).max() < 1e-4, np.abs(a - b).max()

    for spec in (0, 3):
        ta = generate(plain, prompt, max_new_tokens=8, spec=spec).tokens
        tb = generate(branched, prompt, max_new_tokens=8, spec=spec).tokens
        assert ta == tb, (spec, ta, tb)
