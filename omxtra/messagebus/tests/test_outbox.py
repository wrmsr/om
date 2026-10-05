import pytest

from ..outbox import Outbox
from ..types import OutgoingMessage
from ..types import new_worker_id


def test_seqs_are_per_dst():
    src, a, b = new_worker_id(), new_worker_id(), new_worker_id()
    ob = Outbox(src)
    ob.enqueue(OutgoingMessage(a, 'x'))
    ob.enqueue(OutgoingMessage(b, 'y'))
    ob.enqueue(OutgoingMessage(a, 'z'))
    assert ob.has_pending()

    batch = ob.take_batch(10)
    assert [(m.dst_id, m.seq, m.payload) for m in batch.messages] == [(a, 1, 'x'), (b, 1, 'y'), (a, 2, 'z')]
    assert all(m.src_id == src for m in batch.messages)
    assert batch.seqs_after == {a: 2, b: 1}
    assert batch.dst_ids == {a, b}
    assert not ob.has_pending()


def test_batches_respect_max_size_and_continue_after_commit():
    src, a = new_worker_id(), new_worker_id()
    ob = Outbox(src)
    for i in range(5):
        ob.enqueue(OutgoingMessage(a, i))

    b1 = ob.take_batch(2)
    assert [m.seq for m in b1.messages] == [1, 2]
    assert ob.has_pending()
    ob.commit(b1)

    b2 = ob.take_batch(10)
    assert [(m.seq, m.payload) for m in b2.messages] == [(3, 2), (4, 3), (5, 4)]
    assert b2.seqs_after == {a: 5}


def test_only_one_batch_in_flight():
    src, a = new_worker_id(), new_worker_id()
    ob = Outbox(src)
    ob.enqueue(OutgoingMessage(a, 'x'))
    ob.take_batch(10)
    with pytest.raises(Exception):  # noqa
        ob.take_batch(10)


def test_reconcile_drops_a_batch_that_committed():
    src, a = new_worker_id(), new_worker_id()
    ob = Outbox(src)
    ob.enqueue(OutgoingMessage(a, 'x'))
    ob.enqueue(OutgoingMessage(a, 'y'))
    b = ob.take_batch(10)

    # The connection died after commit: the reloaded row already reflects the batch.
    ob.reconcile(b.seqs_after)
    assert not ob.has_pending()

    ob.enqueue(OutgoingMessage(a, 'z'))
    assert [m.seq for m in ob.take_batch(10).messages] == [3]


def test_reconcile_requeues_a_batch_that_did_not_commit_ahead_of_newer_messages():
    src, a, b = new_worker_id(), new_worker_id(), new_worker_id()
    ob = Outbox(src)
    ob.enqueue(OutgoingMessage(a, 'x'))
    ob.enqueue(OutgoingMessage(b, 'y'))
    ob.take_batch(10)
    ob.enqueue(OutgoingMessage(a, 'z'))  # arrived while the batch was in flight

    # The connection died before commit: the reloaded row knows nothing of the batch.
    ob.reconcile({})
    assert ob.has_pending()

    retry = ob.take_batch(10)
    assert [(m.dst_id, m.seq, m.payload) for m in retry.messages] == [(a, 1, 'x'), (b, 1, 'y'), (a, 2, 'z')]


def test_reconcile_resumes_from_loaded_seqs():
    src, a = new_worker_id(), new_worker_id()
    ob = Outbox(src)
    ob.reconcile({a: 41})
    ob.enqueue(OutgoingMessage(a, 'x'))
    assert [m.seq for m in ob.take_batch(10).messages] == [42]
