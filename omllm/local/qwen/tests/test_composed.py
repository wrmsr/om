# ruff: noqa: N803 N806
"""
The composed operations Inkling 2 and its draft model are built from (ops/base.py), on every backend that imports
(test_parity.backends) against the numpy float64 reference. A backend runs each operation's composed definition, or
a form of its own, over arrays of its own, so what this holds it to is its primitives and the indexing the
definitions lean on: an index held on the device, a comparison taken as a float, a gather by an int array.
"""
import typing as ta

import numpy as np

from ..ops.base import Ops
from ..ops.reference import NumpyOps
from .test_microscaled import random_microscaled
from .test_parity import backends


##


def _arr(ops: Ops, a: ta.Any) -> ta.Any:
    """A numpy array on a backend: floats as its float32, ints as int32 (the reference keeps its float64)."""

    a = np.asarray(a)
    if isinstance(ops, NumpyOps):
        return a.astype(np.int32) if a.dtype.kind in 'iu' else a
    if a.dtype.kind == 'f':
        return ops.array(a.astype(np.float32), ops.dtype('f32'))
    return ops.array(a.astype(np.int32), ops.dtype('i32'))


def _same(ops: Ops, got: ta.Any, want: ta.Any, tol: float, what: str) -> None:
    if isinstance(want, (tuple, list)):
        assert len(got) == len(want), (ops.name, what)
        for i, (g, w) in enumerate(zip(got, want)):
            _same(ops, g, w, tol, f'{what}[{i}]')
        return

    g = got if isinstance(got, np.ndarray) else np.asarray(ops.numpy(got))  # (or read on the host already)
    w = np.asarray(want)
    assert g.shape == w.shape, (ops.name, what, g.shape, w.shape)
    if w.dtype.kind in 'iu':
        assert g.dtype.kind in 'iu' and np.array_equal(g, w), (ops.name, what)
        return

    err = float(np.abs(g.astype(np.float64) - w).max() / max(1e-6, float(np.abs(w).max()))) if w.size else 0.
    assert err < tol, (ops.name, what, err)


def _each(what: str, fn: ta.Callable[[Ops], ta.Any], tol: float = 2e-5) -> None:
    """`fn` on the reference and on each backend: the same values, ints exactly."""

    want = fn(NumpyOps())
    for ops in backends():
        _same(ops, fn(ops), want, tol, what)


def test_elementwise():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((2, 5, 16)) * 3
    y = rng.standard_normal((2, 5, 16)) * 3
    i = rng.integers(-9, 9, (5, 7))

    _each('tanh', lambda ops: ops.tanh(_arr(ops, x)))
    _each('sqrt', lambda ops: ops.sqrt(_arr(ops, np.abs(x) * (np.abs(x) > 1))))  # (zeros among them)
    _each('maximum', lambda ops: ops.maximum(_arr(ops, x), 0.5))
    _each('minimum', lambda ops: ops.minimum(_arr(ops, x), 0.5))
    _each('maximum_of', lambda ops: ops.maximum_of(_arr(ops, x), _arr(ops, y)))

    # ints stay ints: a clamped distance is a row index (Ops.rel_bias)
    _each('int clamp', lambda ops: ops.minimum(ops.maximum(_arr(ops, i), 0), 4))


def test_short_convolutions():
    rng = np.random.default_rng(4)
    C, K, G = 12, 4, 3

    for T in (1, 3):
        x = rng.standard_normal((1, T, C))
        hist = rng.standard_normal((1, C, K - 1))
        weight = rng.standard_normal((C, K)) * 0.3
        lagged = rng.standard_normal((K, C)) * 0.3
        dyn = rng.standard_normal((1, T, G, K)) * 0.3

        for all_states in (False, True):
            for given in (None, hist):
                def static(ops: Ops, x=x, weight=weight, given=given, all_states=all_states) -> ta.Any:
                    return ops.short_conv(
                        _arr(ops, x),
                        None if given is None else _arr(ops, given),
                        _arr(ops, weight),
                        scale=0.5,
                        all_states=all_states,
                    )

                def dynamic(ops: Ops, x=x, lagged=lagged, dyn=dyn, given=given, all_states=all_states) -> ta.Any:
                    return ops.short_conv_dynamic(
                        _arr(ops, x),
                        None if given is None else _arr(ops, given),
                        _arr(ops, lagged),
                        _arr(ops, dyn),
                        scale=1. / 3,
                        all_states=all_states,
                    )

                _each(f'short_conv T={T}', static)
                _each(f'short_conv_dynamic T={T}', dynamic)


def test_picks_by_a_device_index():
    """
    What a commit picks a state with (decode/decoder.py): a per-token state by a count held on the device, a window
    of keys and values starting at one; and a gather of positions in any order.
    """

    rng = np.random.default_rng(5)
    T, KV, D, kept = 4, 2, 8, 5
    stacked = rng.standard_normal((T, 1, 6, 3))
    k = rng.standard_normal((1, KV, kept + T, D))
    v = rng.standard_normal((1, KV, kept + T, D))
    positions = np.asarray([7, 0, 3, 3, 8])

    for n in range(1, T + 1):
        def state(ops: Ops, n: int = n) -> ta.Any:
            return ops.select_at(_arr(ops, stacked), ops.scalar(n) - 1)

        def window(ops: Ops, n: int = n) -> ta.Any:
            taken = ops.kv_take(
                ops.kv_new(_arr(ops, k), _arr(ops, v)),
                ops.reshape(ops.scalar(n), (1,)) + ops.arange(kept),
            )
            return ops.kv_dense(taken, ops.dtype('f32'))

        _each('select_at', state)
        _each('kv_take', window)

    # ... and an index that is a value computed on the device, which nothing can know while the pick is built
    pick = np.asarray([0.1, 0.7, 2.5, 0.3])
    _each('select_at computed', lambda ops: ops.select_at(_arr(ops, stacked), ops.argmax(_arr(ops, pick), -1)))

    _each(
        'kv_take any order',
        lambda ops: ops.kv_dense(
            ops.kv_take(ops.kv_new(_arr(ops, k), _arr(ops, v)), _arr(ops, positions)),
            ops.dtype('f32'),
        ),
    )
    _each(
        'kv_gather',
        lambda ops: ops.kv_gather(ops.kv_new(_arr(ops, k), _arr(ops, v)), _arr(ops, positions), ops.dtype('f32')),
    )
    _each(
        'kv_range, kv_join',
        lambda ops: ops.kv_dense(
            ops.kv_join(
                ops.kv_range(ops.kv_new(_arr(ops, k), _arr(ops, v)), 2, 5),
                ops.kv_new(_arr(ops, k[:, :, :2]), _arr(ops, v[:, :, :2])),
            ),
            ops.dtype('f32'),
        ),
    )


def test_a_commit_is_one_captured_call():
    """
    The static decoder's commit of a verify step (decode/decoder.py): a function of a count on the device, the
    step's states and the state as it stands -- which it does not read -- through `Ops.capture_carrying`, called
    with one count after another, its outputs the next call's last arguments. Some of what it returns it was handed
    (a KV buffer); and a capture that took its first call's count for the function's own would go on returning that
    call's picks.
    """

    rng = np.random.default_rng(9)
    T, KV, D, kept, L = 4, 2, 8, 5, 16
    stacked = rng.standard_normal((T, 1, 6, 3))
    k = rng.standard_normal((1, KV, kept + T, D))
    v = rng.standard_normal((1, KV, kept + T, D))
    buf = rng.standard_normal((1, KV, L, D))
    counts = (2, 4, 1, 4, 3)

    def commits(ops: Ops) -> ta.Any:
        if getattr(ops, 'capture_mode', None) == 'auto':
            ops.capture_mode = 'static'  # type: ignore[attr-defined]  # (torch: the captured protocol, without a graph)

        def fn(n, stacked_, k_, v_, buf_, *standing):
            window = ops.kv_take(ops.kv_new(k_, v_), ops.reshape(n, (1,)) + ops.arange(kept))
            return (ops.select_at(stacked_, n - 1), *window, buf_)

        captured = ops.capture_carrying(fn, 0, 5)
        step = [_arr(ops, a) for a in (stacked, k, v, buf)]
        state = [_arr(ops, np.zeros(s)) for s in ((1, 6, 3), (1, KV, kept, D), (1, KV, kept, D), (1, KV, L, D))]

        out = []
        for n in counts:
            state = list(captured(ops.scalar(n), *step, *state))
            pick, *window, held = state
            kd, vd = ops.kv_dense(tuple(window), ops.dtype('f32'))
            out.append([np.array(ops.numpy(a)) for a in (pick, kd, vd, held)])  # (copied: good until the next call)
        return out

    want = commits(NumpyOps())
    for n, (pick, kd, vd, held) in zip(counts, want):
        assert np.array_equal(pick, stacked[n - 1]) and np.array_equal(kd, k[:, :, n:n + kept])
        assert np.array_equal(vd, v[:, :, n:n + kept]) and np.array_equal(held, buf)

    _each('commit', commits)


def test_relative_attention():
    rng = np.random.default_rng(6)
    H, KV, D, R, E, L = 4, 2, 8, 3, 5, 16
    k = rng.standard_normal((1, KV, L, D))
    v = rng.standard_normal((1, KV, L, D))
    rel_proj = rng.standard_normal((E, R))

    for T, pos in ((1, 0), (1, 7), (3, 4), (2, L - 2)):
        q = rng.standard_normal((1, H, T, D))
        rel = rng.standard_normal((T, H, R))
        sink = rng.standard_normal((1, H, T))
        table = rng.standard_normal((T, H, E))

        def term(ops: Ops, T=T, pos=pos, table=table) -> ta.Any:
            return ops.rel_bias(_arr(ops, table), ops.reshape(ops.scalar(pos), (1,)) + ops.arange(T), ops.arange(L))

        def static(ops: Ops, q=q, rel=rel, sink=sink, pos=pos) -> ta.Any:
            return ops.sdpa_static_rel(
                _arr(ops, q),
                ops.kv_new(_arr(ops, k), _arr(ops, v)),
                ops.scalar(pos),
                ops.arange(L),
                0.3,
                _arr(ops, rel),
                _arr(ops, rel_proj),
                _arr(ops, sink),
            )

        # a window's slots end at the step's last position: before the sequence's start some stand for no position
        def window(ops: Ops, q=q, rel=rel, sink=sink, pos=pos, T=T) -> ta.Any:
            N = 6 + T
            return ops.sdpa_window_rel(
                _arr(ops, q),
                _arr(ops, k[:, :, :N]),
                _arr(ops, v[:, :, :N]),
                ops.scalar(pos),
                scale=0.3,
                rel=_arr(ops, rel),
                rel_proj=_arr(ops, rel_proj),
                sink=_arr(ops, sink),
                window=7,
            )

        _each(f'rel_bias T={T} pos={pos}', term)
        _each(f'sdpa_static_rel T={T} pos={pos}', static)
        _each(f'sdpa_window_rel T={T} pos={pos}', window)

    # one query over one key, their positions arrays of one element made on the host: a forward's first token
    for qpos, kpos in ((0, 0), (3, 1), (9, 2)):
        def lone(ops: Ops, qpos=qpos, kpos=kpos, table=rng.standard_normal((1, H, E))) -> ta.Any:
            return ops.rel_bias(
                _arr(ops, table),
                ops.array(np.asarray([qpos], dtype=np.int32)),
                ops.array(np.asarray([kpos], dtype=np.int32)),
            )

        _each(f'rel_bias one query at {qpos}, one key at {kpos}', lone)


def test_attention_in_parts():
    rng = np.random.default_rng(7)
    H, KV, D, T, L = 6, 2, 8, 4, 12
    q = rng.standard_normal((1, H, T, D))
    k = rng.standard_normal((1, KV, L, D))
    v = rng.standard_normal((1, KV, L, D))
    bias = rng.standard_normal((1, H, T, 5))
    sink = rng.standard_normal((1, H, T))

    def merged(ops: Ops, parts: ta.Sequence[ta.Any], with_sink: bool) -> ta.Any:
        return ops.sdpa_merge(parts, _arr(ops, sink) if with_sink else None, ops.dtype('f32'))

    def plain(ops: Ops) -> ta.Any:
        near = ops.sdpa_partials(_arr(ops, q), _arr(ops, k[:, :, 7:]), _arr(ops, v[:, :, 7:]), 0.3, _arr(ops, bias))
        far = ops.sdpa_partials(_arr(ops, q), _arr(ops, k[:, :, :7]), _arr(ops, v[:, :, :7]), 0.3)
        return [*near, merged(ops, [far, near], True), merged(ops, [far, near], False)]

    _each('sdpa_partials, sdpa_merge', plain)

    # queries in order, each seeing one key more: from before any key (m = -1e30, which no finite score yields to)
    for last in (-2, 0, 5):
        def causal(ops: Ops, last=last) -> ta.Any:
            far = ops.sdpa_causal_partials(_arr(ops, q), _arr(ops, k), _arr(ops, v), last, 0.3)
            near = ops.sdpa_partials(_arr(ops, q), _arr(ops, k[:, :, 7:]), _arr(ops, v[:, :, 7:]), 0.3)
            return [far[0], merged(ops, [near, far], True)]

        _each(f'sdpa_causal_partials last={last}', causal)

    # a stretch of a buffer by two indices on the device: whole, partial, empty
    for lo, hi in ((0, L), (3, 9), (5, 5)):
        def span(ops: Ops, lo=lo, hi=hi) -> ta.Any:
            far = ops.sdpa_span_partials(
                _arr(ops, q),
                _arr(ops, k),
                _arr(ops, v),
                ops.scalar(lo),
                ops.scalar(hi),
                ops.arange(L),
                0.3,
            )
            near = ops.sdpa_partials(_arr(ops, q), _arr(ops, k[:, :, :3]), _arr(ops, v[:, :, :3]), 0.3)
            return [far[0], merged(ops, [far, near], False)]

        _each(f'sdpa_span_partials {lo}..{hi}', span)


def test_expert_products():
    """Every row against its own expert: of a dense stack, and of a stack in each microscaled format."""

    rng = np.random.default_rng(8)
    E, N, K, slots = 6, 8, 64, 2
    x = rng.standard_normal((3, K))
    eids = rng.integers(0, E, 3 * slots)
    dense = rng.standard_normal((E, N, K))

    def products(ops: Ops, w: ta.Any) -> ta.Any:
        f32 = ops.dtype('f32')
        rows = ops.repeat(_arr(ops, x), slots, 0)
        return [
            ops.expert_linear(_arr(ops, x), w, _arr(ops, eids), slots),
            ops.expert_linear_grouped(rows, w, _arr(ops, eids)),
            ops.expert_dense(w, 4, f32),
        ]

    _each('expert_linear', lambda ops: products(ops, ops.expert_weights([[_arr(ops, w)] for w in dense])))

    for fmt in ('nvfp4', 'mxfp8'):
        def packed(ops: Ops, mw=random_microscaled(rng, fmt, E, N, K), fmt=fmt) -> ta.Any:
            return products(ops, ops.microscaled(mw, ops.dtype('f32'), name=f'layers.0.{fmt}'))

        _each(f'expert_linear {fmt}', packed)
