import pytest

from ..bus import Bus
from ..memory import DictBusSessionFactory
from ..types import new_worker_id
from .faults import FaultPoint
from .faults import FaultyBusSessionFactory
from .handlers import CollectingHandler
from .harness import CONFIG
from .harness import TIMEOUT
from .harness import running


def test_reconnects_after_failed_opens():
    inner = DictBusSessionFactory()
    faulty = FaultyBusSessionFactory(inner, failed_opens=2)
    a_id, b_id = new_worker_id(), new_worker_id()
    bh = CollectingHandler(1)
    a = Bus(worker_id=a_id, session_factory=faulty, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=inner, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        a.send(b_id, 'x')
        assert bh.done.wait(TIMEOUT)

    assert faulty.opens == 3
    assert [m.payload for m in bh.received] == ['x']


@pytest.mark.parametrize('point', [FaultPoint.BEFORE_COMMIT, FaultPoint.AFTER_COMMIT])
def test_torn_batch_is_delivered_exactly_once(point):
    inner = DictBusSessionFactory()
    faulty = FaultyBusSessionFactory(inner, point=point, faults=1)
    a_id, b_id = new_worker_id(), new_worker_id()
    bh = CollectingHandler(3)
    a = Bus(worker_id=a_id, session_factory=faulty, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=inner, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        for p in ('x', 'y', 'z'):
            a.send(b_id, p)
        assert bh.done.wait(TIMEOUT)
        assert faulty.wait_for_opens(2, timeout=TIMEOUT)  # after commit, delivery can outrun the reconnect

    # No duplicate and no gap on the receiving side...
    assert [(m.seq, m.payload) for m in bh.received] == [(1, 'x'), (2, 'y'), (3, 'z')]
    assert inner.storage.select_messages(b_id, limit=10) == []

    # ...and exactly one reconnect on the sending side: a wrongly retried batch would have tripped the pk and cost
    # another session, a wrongly dropped one would have left a gap.
    assert faulty.opens == 2
    assert inner.storage.load_seqs(a_id) == {b_id: 3}
