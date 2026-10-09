# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
import collections
import typing as ta
import unittest

from ..streams import MultiplexInputData
from ..streams import MultiplexInputEnd
from ..streams import MultiplexInputMessage
from ..streams import MultiplexOutputFence
from ..streams import MultiplexOutputMessage
from ..streams import MultiplexStream
from ..streams import MultiplexStreamTable
from ..types import DuplicateStreamMultiplexError
from ..types import MultiplexStreamState
from ..types import StreamLimitMultiplexError
from ..types import StreamStateMultiplexError
from ..types import UnknownStreamMultiplexError


##
# An independent reference model of the lifecycle: (local, remote, terminal).


_ModelState = ta.Tuple[str, str, ta.Optional[str]]

_OPS: ta.Sequence[str] = (
    'confirm',
    'refuse',
    'end_local',
    'finish_local',
    'end_remote',
    'close',
    'reset_local',
    'reset_remote',
)


def _model_apply(st: _ModelState, op: str) -> ta.Optional[_ModelState]:
    """Returns the next model state, or None if the op is illegal."""

    local, remote, terminal = st
    if terminal is not None:
        return None

    if op == 'confirm':
        return ('open', remote, None) if local == 'opening' else None
    if op == 'refuse':
        return (local, remote, 'refused') if local == 'opening' else None
    if op == 'end_local':
        return ('ended', remote, None) if local == 'open' else None
    if op == 'finish_local':
        return ('finished', remote, None) if local in ('open', 'ended') else None
    if op == 'end_remote':
        return (local, 'ended', None) if local != 'opening' and remote == 'open' else None
    if op == 'close':
        return (local, remote, 'closed')
    if op in ('reset_local', 'reset_remote'):
        return (local, remote, 'reset')
    raise ValueError(op)


def _model_reported(st: _ModelState) -> MultiplexStreamState:
    local, remote, terminal = st
    if terminal == 'closed':
        return MultiplexStreamState.CLOSED
    if terminal == 'reset':
        return MultiplexStreamState.RESET
    if terminal == 'refused':
        return MultiplexStreamState.REFUSED
    if local == 'opening':
        return MultiplexStreamState.OPENING
    ld = local in ('ended', 'finished')
    rd = remote == 'ended'
    if ld and rd:
        return MultiplexStreamState.ENDED
    if ld:
        return MultiplexStreamState.HALF_CLOSED_LOCAL
    if rd:
        return MultiplexStreamState.HALF_CLOSED_REMOTE
    return MultiplexStreamState.OPEN


def _apply(stream: MultiplexStream, op: str) -> None:
    if op == 'reset_local':
        stream.reset('r', by='local')
    elif op == 'reset_remote':
        stream.reset('r', by='remote')
    elif op in ('refuse', 'close'):
        getattr(stream, op)('r')
    else:
        getattr(stream, op)()


def _replay(path: ta.Sequence[str], *, opening: bool) -> MultiplexStream:
    stream = MultiplexStream('k', 'local', opening=opening)
    for op in path:
        _apply(stream, op)
    return stream


class TestMultiplexStreamStateMachine(unittest.TestCase):
    def test_every_transition_from_every_reachable_state(self) -> None:
        checked = 0
        for opening in (False, True):
            initial: _ModelState = ('opening' if opening else 'open', 'open', None)
            seen: ta.Dict[_ModelState, ta.Sequence[str]] = {initial: ()}
            q: ta.Deque[_ModelState] = collections.deque([initial])
            while q:
                st = q.popleft()
                path = seen[st]

                stream = _replay(path, opening=opening)
                self.assertIs(stream.state, _model_reported(st), (opening, path))

                for op in _OPS:
                    expected = _model_apply(st, op)
                    stream = _replay(path, opening=opening)
                    before = stream.state

                    if expected is None:
                        with self.assertRaises(StreamStateMultiplexError, msg=(opening, path, op)):
                            _apply(stream, op)
                        self.assertIs(stream.state, before, (opening, path, op))
                    else:
                        _apply(stream, op)
                        self.assertIs(stream.state, _model_reported(expected), (opening, path, op))
                        if expected not in seen:
                            seen[expected] = (*path, op)
                            q.append(expected)
                    checked += 1

            # Every lifecycle state is reachable from a locally opened stream.
            if opening:
                self.assertEqual({_model_reported(s) for s in seen}, set(MultiplexStreamState))

        self.assertGreater(checked, 100)

    def test_remote_streams_cannot_be_opening(self) -> None:
        with self.assertRaises(Exception):  # noqa
            MultiplexStream('k', 'remote', opening=True)

    def test_capabilities_by_state(self) -> None:
        s = MultiplexStream('k', 'local', opening=True)
        self.assertFalse(s.can_send_data)
        self.assertFalse(s.can_receive_data)
        self.assertFalse(s.can_receive_message)
        self.assertTrue(s.is_opening)

        s.confirm()
        self.assertTrue(s.can_send_data)
        self.assertTrue(s.can_receive_data)
        self.assertTrue(s.can_receive_message)

        s.end_remote()
        self.assertTrue(s.can_send_data)
        self.assertFalse(s.can_receive_data)
        self.assertTrue(s.can_receive_message)  # e.g. SSH requests after EOF

        s.end_local()
        self.assertFalse(s.can_send_data)
        self.assertIs(s.state, MultiplexStreamState.ENDED)

        s.finish_local()
        self.assertTrue(s.local_finished)
        self.assertIs(s.state, MultiplexStreamState.ENDED)

        s.close('done')
        self.assertTrue(s.is_terminal)
        self.assertFalse(s.can_receive_message)
        self.assertEqual(s.terminal_reason, 'done')

    def test_reset_records_reason_and_initiator(self) -> None:
        s = MultiplexStream('k', 'remote')
        s.reset('cancel', by='remote')
        self.assertIs(s.state, MultiplexStreamState.RESET)
        self.assertEqual(s.terminal_reason, 'cancel')
        self.assertEqual(s.reset_by, 'remote')


class TestMultiplexStreamQueues(unittest.TestCase):
    def test_outbound_order_and_data_gathering(self) -> None:
        s = MultiplexStream('k', 'local')
        fence = object()
        s.push_out_data(b'abc')
        s.push_out_data(memoryview(b'defg'))
        s.push_out_message('req')
        s.push_out_data(b'hi')
        s.push_out_fence('flush', fence)
        s.push_out_data(b'')  # empty segments are dropped

        self.assertEqual(s.out_bytes, 9)
        self.assertEqual(s.out_items, 5)
        self.assertEqual(s.out_head_data_bytes(), 7)

        self.assertEqual(b''.join(s.pop_out_data(2)), b'ab')
        self.assertEqual(s.out_bytes, 7)
        self.assertEqual(b''.join(s.pop_out_data(100)), b'cdefg')  # gathers across segments, stops at the message
        self.assertEqual(s.out_head_data_bytes(), 0)

        self.assertEqual(s.pop_out_data(1), [])  # the head is the message now

        self.assertEqual(s.pop_out_item(), MultiplexOutputMessage('req'))
        with self.assertRaises(TypeError):
            s.pop_out_item()
        self.assertEqual(b''.join(s.pop_out_data(10)), b'hi')
        self.assertEqual(s.pop_out_item(), MultiplexOutputFence('flush', fence))
        self.assertIsNone(s.out_head())
        self.assertEqual(s.out_bytes, 0)

    def test_clear_out_returns_items_for_failing(self) -> None:
        s = MultiplexStream('k', 'local')
        s.push_out_data(b'abc')
        s.push_out_fence('final', 'f')
        s.push_out_message('m')
        items = s.clear_out()
        self.assertEqual(items, [MultiplexOutputFence('final', 'f'), MultiplexOutputMessage('m')])
        self.assertEqual(s.out_bytes, 0)
        self.assertIsNone(s.out_head())

    def test_inbound_order_and_accounting(self) -> None:
        s = MultiplexStream('k', 'remote')
        s.push_in_data(b'abc', 5)
        s.push_in_message('m')
        s.push_in_data(b'de', 2)
        s.push_in_end()

        self.assertEqual((s.in_cost, s.in_bytes, s.in_messages, s.in_items), (7, 5, 1, 4))
        with self.assertRaises(Exception):  # noqa
            s.push_in_data(b'x', 1)
        with self.assertRaises(Exception):  # noqa
            s.push_in_end()

        self.assertEqual(s.pop_in(), MultiplexInputData(b'abc', 5))
        self.assertEqual(s.pop_in(), MultiplexInputMessage('m'))
        self.assertEqual((s.in_cost, s.in_bytes, s.in_messages), (2, 2, 0))
        self.assertEqual(s.pop_in(), MultiplexInputData(b'de', 2))
        self.assertIsInstance(s.pop_in(), MultiplexInputEnd)
        self.assertIsNone(s.in_head())
        self.assertTrue(s.in_end_queued)


class TestMultiplexStreamTable(unittest.TestCase):
    def test_limits_per_origin_and_runtime_changes(self) -> None:
        t = MultiplexStreamTable(max_local=1, max_remote=2)
        t.add(MultiplexStream(1, 'local'))
        self.assertFalse(t.can_open('local'))
        with self.assertRaises(StreamLimitMultiplexError):
            t.add(MultiplexStream(2, 'local'))

        t.add(MultiplexStream(3, 'remote'))
        t.add(MultiplexStream(4, 'remote'))
        with self.assertRaises(StreamLimitMultiplexError):
            t.add(MultiplexStream(5, 'remote'))

        t.set_limits(max_remote=None)
        t.add(MultiplexStream(5, 'remote'))
        t.set_limits(max_local=3)
        t.add(MultiplexStream(2, 'local'))

        # Lowering a limit leaves existing streams but blocks new ones.
        t.set_limits(max_local=0)
        self.assertEqual(t.count('local'), 2)
        self.assertFalse(t.can_open('local'))
        self.assertEqual(t.max_local, 0)
        self.assertIsNone(t.max_remote)

    def test_duplicates_unknown_and_removal_counters(self) -> None:
        t = MultiplexStreamTable()
        a = MultiplexStream('a', 'local', opening=True)
        b = MultiplexStream('b', 'remote')
        c = MultiplexStream('c', 'remote')
        d = MultiplexStream('d', 'local')
        for s in (a, b, c, d):
            t.add(s)
        with self.assertRaises(DuplicateStreamMultiplexError):
            t.add(MultiplexStream('a', 'remote'))
        with self.assertRaises(UnknownStreamMultiplexError):
            t['zzz']  # noqa
        self.assertIsNone(t.get('zzz'))

        with self.assertRaises(Exception):  # noqa
            t.remove('a')  # not terminal

        a.refuse('nope')
        b.reset('cancel', by='remote')
        c.close()
        d.reset('err', by='local')
        for k in 'abcd':
            t.remove(k)
        t.count_refused('remote')

        st = t.stats
        self.assertEqual((st.opened_local, st.opened_remote), (2, 2))
        self.assertEqual((st.refused_local, st.refused_remote), (1, 1))
        self.assertEqual((st.reset_local, st.reset_remote), (1, 1))
        self.assertEqual(st.closed, 1)
        self.assertEqual((st.active_local, st.active_remote), (0, 0))
        self.assertEqual(len(t), 0)
