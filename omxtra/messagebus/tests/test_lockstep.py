import threading

from ..bus import Bus
from ..memory import DictBusSessionFactory
from ..types import new_worker_id
from .faults import ObservedBusSession
from .faults import WrappingBusSessionFactory
from .gates import Gate
from .gates import GatedBusSession
from .handlers import CollectingHandler
from .harness import CONFIG
from .harness import TIMEOUT
from .harness import running


def test_notify_landing_between_poll_and_wait_is_not_lost():
    inner = DictBusSessionFactory()
    a_id, b_id = new_worker_id(), new_worker_id()

    committed = threading.Event()
    a = Bus(
        worker_id=a_id,
        session_factory=WrappingBusSessionFactory(inner, lambda s: ObservedBusSession(s, committed)),
        handler=CollectingHandler(1),
        name='a',
        config=CONFIG,
    )

    gate = Gate(timeout=TIMEOUT)
    bh = CollectingHandler(1)
    b = Bus(
        worker_id=b_id,
        session_factory=WrappingBusSessionFactory(inner, lambda s: GatedBusSession(s, gate)),
        handler=bh,
        name='b',
        config=CONFIG,
    )

    try:
        with running(b):
            assert gate.arrived.wait(TIMEOUT)  # b has polled and found nothing, and is about to wait

            with running(a):
                a.send(b_id, 'x')
                assert committed.wait(TIMEOUT)  # the notify has fired while b is still short of its wait

                gate.open()
                assert bh.done.wait(TIMEOUT)  # so this can only pass if listen() subscribed before the first poll
    finally:
        gate.open()

    assert [m.payload for m in bh.received] == ['x']
