import pytest

from ..memory import DictBusStorage
from ..types import Message
from ..types import new_worker_id
from ..waker import Waker


def test_identity_lock_is_exclusive():
    st = DictBusStorage()
    a = new_worker_id()
    assert st.try_acquire(a)
    assert not st.try_acquire(a)
    st.release(a)
    assert st.try_acquire(a)


def test_register_preserves_seqs_and_updates_name():
    st = DictBusStorage()
    a, b = new_worker_id(), new_worker_id()
    st.register_worker(a, 'first')
    st.update_seqs(a, {b: 3})
    st.register_worker(a, 'second')
    assert st.load_seqs(a) == {b: 3}
    [w] = st.list_workers()
    assert (w.worker_id, w.name) == (a, 'second')


def test_duplicate_message_key_is_rejected():
    st = DictBusStorage()
    a, b = new_worker_id(), new_worker_id()
    st.insert_message(Message(b, a, 1, 'x'))
    with pytest.raises(Exception):  # noqa
        st.insert_message(Message(b, a, 1, 'y'))


def test_select_keeps_per_src_order_and_delete_removes():
    st = DictBusStorage()
    a, b, c = new_worker_id(), new_worker_id(), new_worker_id()
    for seq in (1, 2, 3):
        st.insert_message(Message(c, a, seq, f'a{seq}'))
        st.insert_message(Message(c, b, seq, f'b{seq}'))
    st.insert_message(Message(a, b, 1, 'elsewhere'))

    got = st.select_messages(c, limit=10)
    assert len(got) == 6
    assert all(m.created_at is not None for m in got)
    assert [m.seq for m in got if m.src_id == a] == [1, 2, 3]
    assert [m.seq for m in got if m.src_id == b] == [1, 2, 3]
    assert len(st.select_messages(c, limit=4)) == 4

    for m in got:
        st.delete_message(m)
    assert st.select_messages(c, limit=10) == []
    assert len(st.select_messages(a, limit=10)) == 1


def test_wake_reaches_only_a_registered_waker():
    st = DictBusStorage()
    b = new_worker_id()
    w = Waker()
    try:
        st.wake([b])
        assert not w.wait(0.)

        st.set_waker(b, w)
        st.wake([b])
        assert w.wait(0.)

        st.clear_waker(b, w)
        st.wake([b])
        assert not w.wait(0.)
    finally:
        w.close()
