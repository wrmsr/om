import pytest

from ..bus import Bus
from ..errors import IdentityLockError
from ..loop import BusLoop
from ..memory import DictBusSessionFactory
from ..outbox import Outbox
from ..types import Message
from ..types import new_worker_id
from ..waker import Waker
from .handlers import CollectingHandler
from .handlers import FlakyHandler
from .harness import CONFIG
from .harness import TIMEOUT
from .harness import running


def test_send_and_receive():
    sf = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()
    bh = CollectingHandler(1)
    a = Bus(worker_id=a_id, session_factory=sf, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=sf, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        a.send(b_id, {'hi': 1})
        assert bh.done.wait(TIMEOUT)

    [m] = bh.received
    assert (m.src_id, m.dst_id, m.seq, m.payload) == (a_id, b_id, 1, {'hi': 1})
    assert m.created_at is not None
    assert sf.storage.select_messages(b_id, limit=10) == []
    assert sf.storage.load_seqs(a_id) == {b_id: 1}


def test_ordering_holds_across_batches():
    sf = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()
    n = 250
    bh = CollectingHandler(n)
    a = Bus(worker_id=a_id, session_factory=sf, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=sf, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        for i in range(n):
            a.send(b_id, i)
        assert bh.done.wait(TIMEOUT)

    assert [m.seq for m in bh.received] == list(range(1, n + 1))
    assert [m.payload for m in bh.received] == list(range(n))
    assert sf.storage.load_seqs(a_id) == {b_id: n}


def test_message_queued_before_receiver_starts_is_polled_on_startup():
    sf = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()
    sf.storage.insert_message(Message(b_id, a_id, 1, 'early'))
    bh = CollectingHandler(1)
    b = Bus(worker_id=b_id, session_factory=sf, handler=bh, name='b', config=CONFIG)

    with running(b):
        assert bh.done.wait(TIMEOUT)

    assert [m.payload for m in bh.received] == ['early']


def test_workers_are_registered():
    sf = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()
    bh = CollectingHandler(1)
    a = Bus(worker_id=a_id, session_factory=sf, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=sf, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        a.send(b_id, 'x')
        assert bh.done.wait(TIMEOUT)
        assert {w.worker_id: w.name for w in sf.storage.list_workers()} == {a_id: 'a', b_id: 'b'}


def test_identity_conflict_is_fatal():
    sf = DictBusSessionFactory()
    wid = new_worker_id()
    assert sf.storage.try_acquire(wid)  # someone else is already live as this identity

    waker = Waker()
    try:
        loop = BusLoop(
            worker_id=wid,
            name='dup',
            session_factory=sf,
            handler=CollectingHandler(1),
            outbox=Outbox(wid),
            waker=waker,
            config=CONFIG,
        )
        with pytest.raises(IdentityLockError) as ei:
            loop.run()
    finally:
        waker.close()

    assert ei.value.worker_id == wid
    assert not sf.storage.try_acquire(wid)  # and the loser's teardown didn't evict the holder


def test_failed_handler_redelivers():
    sf = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()
    bh = FlakyHandler(1, failures=1)
    a = Bus(worker_id=a_id, session_factory=sf, handler=CollectingHandler(1), name='a', config=CONFIG)
    b = Bus(worker_id=b_id, session_factory=sf, handler=bh, name='b', config=CONFIG)

    with running(a, b):
        a.send(b_id, 'x')
        assert bh.done.wait(TIMEOUT)

    assert bh.attempts == 2
    assert [m.payload for m in bh.received] == ['x']
    assert sf.storage.select_messages(b_id, limit=10) == []
