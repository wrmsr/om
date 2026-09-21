import itertools

import pytest

from ..workers import TailPacing


def test_tail_pacing():
    p = TailPacing()

    # a tenth of the quiet so far, between a half second and ten
    assert [p.interval_s(s) for s in (0., 1., 5., 10., 50., 100., 1000.)] == [.5, .5, .5, 1., 5., 10., 10.]

    # which, each wait adding itself to the quiet, is each wait a tenth longer than the last
    t, waits = 0., []
    while t < 200.:
        waits.append(p.interval_s(t))
        t += waits[-1]
    growing = [w for w in waits if .5 < w < 10.]
    assert all(b == pytest.approx(a * 1.1) for a, b in itertools.pairwise(growing))
    assert waits[0] == .5 and waits[-1] == 10.

    for kw in [dict(min_interval_s=0.), dict(min_interval_s=2., max_interval_s=1.), dict(idle_ratio=0.)]:
        with pytest.raises(RuntimeError):  # noqa
            TailPacing(**kw)
