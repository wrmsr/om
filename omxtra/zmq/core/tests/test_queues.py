import pytest

from ..errors import PeerViolationError
from ..fairqueues import FairQueue
from ..queues import MessageQueue
from ..subscriptions import SubscriptionCounts


def test_message_queue_bounds():
    q = MessageQueue(max_messages=3, max_bytes=10)
    assert q.has_room()
    q.push((b'',))
    q.push((b'', b''))
    assert q.has_room() and q.bytes == 0
    q.push((b'x' * 100,))  # one message may overshoot the byte bound
    assert not q.has_room() and q.bytes == 100
    assert q.pop() == (b'',)
    assert not q.has_room()  # still over bytes
    q.pop()
    q.pop()
    assert q.has_room() and q.bytes == 0 and not q


def test_message_queue_counts_empty_frames():
    q = MessageQueue(max_messages=2, max_bytes=1000)
    q.push((b'',) * 100)
    q.push((b'',))
    assert not q.has_room()


def test_fair_queue():
    fq: FairQueue[str] = FairQueue()
    for m in 'abca':
        fq.add(m)
    assert len(fq) == 3
    assert fq.pop() == 'a'
    fq.add('a')
    assert [fq.pop() for _ in range(3)] == ['b', 'c', 'a']
    assert fq.pop() is None

    for m in 'abcd':
        fq.add(m)
    assert fq.find(lambda m: m in 'cd') == 'c'
    assert fq.find(lambda m: m in 'cd') == 'd'
    assert fq.find(lambda m: m in 'cd') == 'c'
    assert fq.find(lambda m: False) is None
    fq.remove('c')
    fq.remove('zz')
    assert 'c' not in fq and len(fq) == 3


def test_subscription_counts():
    s = SubscriptionCounts(max_prefixes=2)
    assert s.add(b'a')
    assert not s.add(b'a')
    assert s.add(b'')
    with pytest.raises(PeerViolationError):
        s.add(b'b')
    assert s.matches(b'anything')
    assert not s.remove(b'zzz')
    assert s.remove(b'')
    assert not s.matches(b'b') and s.matches(b'abc')
    assert not s.remove(b'a')
    assert s.remove(b'a')
    assert not s.matches(b'a') and len(s) == 0
