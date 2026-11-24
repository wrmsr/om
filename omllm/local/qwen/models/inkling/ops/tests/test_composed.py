# ruff: noqa: N803 N806
"""
Inkling 2's operations (base.py) on every backend that imports (test_parity.backends) against the numpy float64
reference: a backend runs each operation's composed definition, or a form of its own, over arrays of its own.
"""
import typing as ta

import numpy as np

from .....ops.base import Ops
from .....tests.test_composed import _arr
from .....tests.test_composed import _each
from ..backends import inkling2_ops


##


def test_norms_and_clips():
    rng = np.random.default_rng(1)
    x = rng.standard_normal((1, 3, 4, 16)) * 3
    w = rng.standard_normal(16)
    scale = rng.standard_normal((4, 16))
    after = rng.uniform(1, 2, 3)

    _each('unit_rms', lambda ops: inkling2_ops(ops).unit_rms(_arr(ops, x), 1e-6))
    _each('rms_norm_to', lambda ops: inkling2_ops(ops).rms_norm_to(_arr(ops, x), _arr(ops, w), 1e-6, ops.dtype('f32')))
    _each('l2_clip', lambda ops: inkling2_ops(ops).l2_clip(_arr(ops, x), 2.5))
    _each(
        'l2_clip scaled',
        lambda ops: inkling2_ops(ops).l2_clip(_arr(ops, x), 9., scale=_arr(ops, scale), after=_arr(ops, after)),
    )


def test_stream_reads():
    rng = np.random.default_rng(2)
    T, H, Q, R = 3, 24, 2, 4
    queries = rng.standard_normal((Q, H))
    sources = [rng.standard_normal((1, T, H)) * s for s in (1., 1., 4.)]
    x = rng.standard_normal((1, T, H)) * 3
    m = rng.standard_normal((1, T, H))
    down = rng.standard_normal((R, 2 * H)) / np.sqrt(H)
    forget = rng.standard_normal((H, R)) / np.sqrt(R)
    gain = rng.standard_normal((H, R)) / np.sqrt(R)

    for raw in (0, 1):
        def mix(ops: Ops, raw: int = raw) -> ta.Any:
            return inkling2_ops(ops).depth_mix(_arr(ops, queries), [_arr(ops, s) for s in sources], raw=raw, eps=1e-6)

        _each(f'depth_mix raw={raw}', mix)

    _each(
        'bottleneck_blend',
        lambda ops: inkling2_ops(ops).bottleneck_blend(
            _arr(ops, x),
            _arr(ops, m),
            _arr(ops, down),
            _arr(ops, forget),
            _arr(ops, gain),
            eps=1e-6,
            dtype=ops.dtype('f32'),
        ),
    )


def test_experts_small_work():
    rng = np.random.default_rng(3)
    N, E, K, I, H = 5, 12, 3, 8, 16
    logits = rng.standard_normal((N, E)) * 2
    bias = rng.standard_normal(E) * 0.5
    h = rng.standard_normal((N * K, 2 * I)) * 6
    y = rng.standard_normal((N, K, H))
    w = rng.uniform(0, 1, (N, K))

    _each(
        'sigmoid_route',
        lambda ops: inkling2_ops(ops).sigmoid_route(_arr(ops, logits), _arr(ops, bias), K, total=float(K)),
    )
    _each('capped_gate', lambda ops: inkling2_ops(ops).capped_gate(_arr(ops, h), gate_cap=4., up_cap=25.))
    _each('weighted_rows', lambda ops: inkling2_ops(ops).weighted_rows(_arr(ops, y), _arr(ops, w), ops.dtype('f32')))
