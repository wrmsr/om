import pytest

from .....io.pipelines import all as ipl
from ...errors import REQUEST_TIMED_OUT_ERROR_CODE
from ...errors import RESPONSE_TOO_LARGE_ERROR_CODE
from ...errors import SERVER_BUSY_ERROR_CODE
from ...errors import SERVER_SHUTTING_DOWN_ERROR_CODE
from ...errors import JsonrpcConnectionClosedError
from ...errors import JsonrpcMessageTooLargeError
from ...errors import JsonrpcProtocolError
from ...errors import JsonrpcTimeoutError
from ...errors import JsonrpcTooManyRequestsError
from ...errors import KnownErrors
from ...types import Batch
from ...types import Error
from ...types import error
from ...types import notification
from ...types import request
from ...types import result
from ..configs import JsonrpcPipelineConfig
from ..messages import JsonrpcPipelineMessages as Jpm
from .harness import Harness
from .harness import one
from .harness import only


def _cfg(**kwargs) -> JsonrpcPipelineConfig:
    return JsonrpcPipelineConfig(**kwargs)


##
# outbound requests


def test_request_response_roundtrip():
    h = Harness()
    assert h.send(Jpm.SendRequest(request(1, 'add', [1, 2]))) == []
    assert h.out() == [{'jsonrpc': '2.0', 'method': 'add', 'params': [1, 2], 'id': 1}]
    assert h.session.pending_outbound_ids == {1}

    evs = h.recv({'jsonrpc': '2.0', 'result': 3, 'id': 1})
    ev = one(evs, Jpm.ResponseReceived)
    assert ev.request == request(1, 'add', [1, 2])
    assert ev.response == result(1, 3)
    assert not h.session.pending_outbound_ids


def test_error_response():
    h = Harness()
    h.send(Jpm.SendRequest(request('a', 'x')))
    evs = h.recv({'jsonrpc': '2.0', 'error': {'code': 5, 'message': 'no', 'data': [1]}, 'id': 'a'})
    ev = one(evs, Jpm.ResponseReceived)
    assert ev.response == error('a', Error(5, 'no', [1]))


def test_concurrent_requests_any_order():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')), Jpm.SendRequest(request(2, 'b')), Jpm.SendRequest(request(3, 'c')))
    assert [o['id'] for o in h.out()] == [1, 2, 3]
    evs = h.recv({'jsonrpc': '2.0', 'result': 'c', 'id': 3}, {'jsonrpc': '2.0', 'result': 'a', 'id': 1})
    assert [(e.request.id, e.response.result) for e in only(evs, Jpm.ResponseReceived)] == [(3, 'c'), (1, 'a')]
    assert h.session.pending_outbound_ids == {2}


def test_notification_send():
    h = Harness()
    assert h.send(Jpm.SendNotification(notification('n', {'k': 1}))) == []
    assert h.out() == [{'jsonrpc': '2.0', 'method': 'n', 'params': {'k': 1}}]
    assert not h.session.pending_outbound_ids


def test_request_timeout():
    h = Harness(_cfg(default_request_timeout_s=5.))
    h.send(Jpm.SendRequest(request(1, 'slow')))
    assert h.tick(4.) == []
    evs = h.tick(1.)
    ev = one(evs, Jpm.RequestFailed)
    assert ev.request.id == 1
    assert isinstance(ev.exc, JsonrpcTimeoutError)
    assert not h.closed
    # A late response is dropped.
    assert h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 1}) == []
    assert not h.closed


def test_per_request_timeout_override():
    h = Harness(_cfg(default_request_timeout_s=5.))
    h.send(Jpm.SendRequest(request(1, 'a'), timeout_s=1.), Jpm.SendRequest(request(2, 'b'), timeout_s=None))
    evs = h.tick(1.)
    assert [e.request.id for e in only(evs, Jpm.RequestFailed)] == [1]
    assert h.tick(100.) == []
    assert h.session.pending_outbound_ids == {2}


def test_no_default_timeout():
    h = Harness(_cfg(default_request_timeout_s=None))
    h.send(Jpm.SendRequest(request(1, 'a')))
    assert h.tick(1e6) == []
    assert h.session.pending_outbound_ids == {1}


def test_cancel_request():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')))
    assert h.send(Jpm.CancelRequest(1)) == []
    assert not h.session.pending_outbound_ids
    assert h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 1}) == []
    assert h.tick(1000.) == []


def test_max_pending_outbound():
    h = Harness(_cfg(max_pending_outbound=2))
    evs = h.send(Jpm.SendRequest(request(1, 'a')), Jpm.SendRequest(request(2, 'b')), Jpm.SendRequest(request(3, 'c')))
    ev = one(evs, Jpm.RequestFailed)
    assert ev.request.id == 3
    assert isinstance(ev.exc, JsonrpcTooManyRequestsError)
    assert [o['id'] for o in h.out()] == [1, 2]

    h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 1})
    assert h.send(Jpm.SendRequest(request(3, 'c'))) == []
    assert h.session.pending_outbound_ids == {2, 3}


def test_duplicate_outbound_id():
    h = Harness()
    evs = h.send(Jpm.SendRequest(request(1, 'a')), Jpm.SendRequest(request(1, 'b')))
    ev = one(evs, Jpm.RequestFailed)
    assert ev.request.method == 'b'
    assert isinstance(ev.exc, ValueError)
    assert h.session.pending_outbound_ids == {1}


def test_unmatched_response_ignored():
    h = Harness()
    assert h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 99}) == []
    assert not h.closed


def test_unmatched_response_closes():
    h = Harness(_cfg(on_unmatched_response='close'))
    evs = h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 99})
    ev = one(evs, Jpm.Closed)
    assert isinstance(ev.exc, JsonrpcProtocolError)
    assert h.closed


##
# inbound requests


def test_inbound_request_response():
    h = Harness()
    evs = h.recv({'jsonrpc': '2.0', 'method': 'add', 'params': {'a': 1}, 'id': 'q'})
    ev = one(evs, Jpm.RequestReceived)
    assert ev.request == request('q', 'add', {'a': 1})
    assert h.session.inflight_inbound_ids == {'q'}
    assert h.out() == []

    assert h.send(Jpm.SendResponse(result('q', 2))) == []
    assert h.out() == [{'jsonrpc': '2.0', 'result': 2, 'id': 'q'}]
    assert not h.session.inflight_inbound_ids


def test_inbound_notification():
    h = Harness()
    evs = h.recv({'jsonrpc': '2.0', 'method': 'note', 'params': [1]})
    ev = one(evs, Jpm.NotificationReceived)
    assert ev.notification == notification('note', [1])
    assert not h.session.inflight_inbound_ids
    assert h.out() == []


def test_inbound_null_id_request():
    h = Harness()
    evs = h.recv({'jsonrpc': '2.0', 'method': 'x', 'id': None})
    ev = one(evs, Jpm.RequestReceived)
    assert ev.request.id is None
    assert not ev.request.is_notification
    h.send(Jpm.SendResponse(result(None, 1)))
    assert h.out() == [{'jsonrpc': '2.0', 'result': 1, 'id': None}]


def test_response_to_unknown_inbound_dropped():
    h = Harness()
    assert h.send(Jpm.SendResponse(result('nope', 1))) == []
    assert h.out() == []


def test_duplicate_inbound_id():
    h = Harness()
    h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1})
    evs = h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 1})
    assert not only(evs, Jpm.RequestReceived)
    [o] = h.out()
    assert o['id'] == 1
    assert o['error']['code'] == KnownErrors.INVALID_REQUEST.code
    assert h.session.inflight_inbound_ids == {1}


def test_inbound_handling_timeout():
    h = Harness(_cfg(inbound_handling_timeout_s=2.))
    h.recv({'jsonrpc': '2.0', 'method': 'slow', 'id': 1})
    assert h.tick(1.) == []
    evs = h.tick(1.)
    ev = one(evs, Jpm.RequestHandlingAborted)
    assert ev.request.id == 1
    assert isinstance(ev.exc, JsonrpcTimeoutError)
    [o] = h.out()
    assert o['error']['code'] == REQUEST_TIMED_OUT_ERROR_CODE
    assert not h.session.inflight_inbound_ids
    assert not h.closed

    # A late response from the host is dropped.
    h.send(Jpm.SendResponse(result(1, 'late')))
    assert h.out() == []


def test_inbound_handling_timeout_no_response():
    h = Harness(_cfg(inbound_handling_timeout_s=2., respond_to_aborted_inbound=False))
    h.recv({'jsonrpc': '2.0', 'method': 'slow', 'id': 1})
    evs = h.tick(2.)
    one(evs, Jpm.RequestHandlingAborted)
    assert h.out() == []


def test_max_inflight_reject():
    h = Harness(_cfg(max_inflight_inbound=1))
    evs = h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1}, {'jsonrpc': '2.0', 'method': 'b', 'id': 2})
    assert [e.request.id for e in only(evs, Jpm.RequestReceived)] == [1]
    [o] = h.out()
    assert o['id'] == 2
    assert o['error']['code'] == SERVER_BUSY_ERROR_CODE

    h.send(Jpm.SendResponse(result(1, 'ok')))
    evs = h.recv({'jsonrpc': '2.0', 'method': 'c', 'id': 3})
    assert [e.request.id for e in only(evs, Jpm.RequestReceived)] == [3]


def _wants_input(h: Harness) -> bool:
    return h.drv.wants_input


def test_max_inflight_pause():
    h = Harness(_cfg(max_inflight_inbound=1, inflight_limit_policy='pause'))
    assert h.events() == []
    assert _wants_input(h)
    evs = h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1})
    assert [e.request.id for e in only(evs, Jpm.RequestReceived)] == [1]
    assert h.out() == []

    # At the limit: the driver has not been told to read again, so further input waits.
    assert not _wants_input(h)
    assert h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 2}) == []
    assert not _wants_input(h)

    # Answering frees a slot and reading resumes.
    evs = h.send(Jpm.SendResponse(result(1, 'ok')))
    assert [e.request.id for e in only(evs, Jpm.RequestReceived)] == [2]
    assert h.out() == [{'jsonrpc': '2.0', 'result': 'ok', 'id': 1}]


##
# invalid messages


def test_parse_error_response():
    h = Harness()
    assert h.recv_bytes(b'{not json\n') == []
    [o] = h.out()
    assert o == {'jsonrpc': '2.0', 'error': {'code': -32700, 'message': 'Parse error'}, 'id': None}
    assert not h.closed


def test_invalid_request_response_keeps_id():
    h = Harness()
    assert h.recv({'jsonrpc': '2.0', 'method': 5, 'id': 7}) == []
    [o] = h.out()
    assert o['error']['code'] == KnownErrors.INVALID_REQUEST.code
    assert o['id'] == 7


def test_invalid_response_like_not_answered():
    h = Harness()
    assert h.recv({'jsonrpc': '2.0', 'result': 1, 'error': {'code': 1, 'message': 'm'}, 'id': 1}) == []
    assert h.out() == []
    assert not h.closed


def test_invalid_message_close_policy():
    h = Harness(_cfg(on_invalid_message='close'))
    evs = h.recv_bytes(b'garbage\n')
    ev = one(evs, Jpm.Closed)
    assert isinstance(ev.exc, JsonrpcProtocolError)
    assert h.out() == []
    assert h.closed


def test_consecutive_invalid_closes():
    h = Harness(_cfg(max_consecutive_invalid=3))
    assert h.recv_bytes(b'x\ny\n') == []
    assert len(h.out()) == 2
    assert not h.closed
    # A valid message resets the count.
    h.recv({'jsonrpc': '2.0', 'method': 'n'})
    assert h.recv_bytes(b'x\ny\n') == []
    assert not h.closed
    evs = h.recv_bytes(b'z\n')
    one(evs, Jpm.Closed)
    assert len(h.out()) == 3  # the third was still answered before closing
    assert h.closed


def test_oversize_inbound_line_is_fatal():
    h = Harness(_cfg(max_frame_bytes=32))
    evs = h.recv_bytes(b'{"jsonrpc":"2.0","method":"' + b'x' * 100 + b'"}\n')
    ev = one(evs, Jpm.Closed)
    assert isinstance(ev.exc, JsonrpcMessageTooLargeError)
    assert h.closed


##
# batches


def test_inbound_batch_spec_example():
    h = Harness()
    evs = h.recv([
        {'jsonrpc': '2.0', 'method': 'sum', 'params': [1, 2, 4], 'id': '1'},
        {'jsonrpc': '2.0', 'method': 'notify_hello', 'params': [7]},
        {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': '2'},
        {'foo': 'boo'},
        {'jsonrpc': '2.0', 'method': 'foo.get', 'params': {'name': 'myself'}, 'id': '5'},
        {'jsonrpc': '2.0', 'method': 'get_data', 'id': '9'},
    ])
    assert [e.request.id for e in only(evs, Jpm.RequestReceived)] == ['1', '2', '5', '9']
    assert [e.notification.method for e in only(evs, Jpm.NotificationReceived)] == ['notify_hello']
    # Nothing is sent until every member is answered.
    assert h.out() == []

    h.send(Jpm.SendResponse(result('1', 7)))
    h.send(Jpm.SendResponse(result('2', 19)))
    h.send(Jpm.SendResponse(error('5', Error(-32601, 'Method not found'))))
    assert h.out() == []
    h.send(Jpm.SendResponse(result('9', ['hello', 5])))
    [b] = h.out()
    # The spec permits any order; responses are kept in request order.
    assert b == [
        {'jsonrpc': '2.0', 'result': 7, 'id': '1'},
        {'jsonrpc': '2.0', 'result': 19, 'id': '2'},
        {'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'Invalid Request'}, 'id': None},
        {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found'}, 'id': '5'},
        {'jsonrpc': '2.0', 'result': ['hello', 5], 'id': '9'},
    ]


def test_inbound_batch_all_notifications():
    h = Harness()
    evs = h.recv([
        {'jsonrpc': '2.0', 'method': 'a'},
        {'jsonrpc': '2.0', 'method': 'b'},
    ])
    assert [e.notification.method for e in only(evs, Jpm.NotificationReceived)] == ['a', 'b']
    assert h.out() == []


def test_inbound_batch_all_invalid():
    h = Harness()
    assert h.recv([1, 2, 3]) == []
    [b] = h.out()
    assert len(b) == 3
    assert all(o['error']['code'] == -32600 for o in b)


def test_inbound_empty_batch():
    h = Harness()
    assert h.recv([]) == []
    [o] = h.out()
    assert o['error']['code'] == -32600
    assert o['id'] is None


def test_inbound_batch_of_responses():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')), Jpm.SendRequest(request(2, 'b')))
    h.out()
    evs = h.recv([{'jsonrpc': '2.0', 'result': 'a', 'id': 1}, {'jsonrpc': '2.0', 'result': 'b', 'id': 2}])
    assert [e.response.result for e in only(evs, Jpm.ResponseReceived)] == ['a', 'b']


def test_batches_rejected():
    h = Harness(_cfg(accept_batches=False))
    assert h.recv([{'jsonrpc': '2.0', 'method': 'a', 'id': 1}]) == []
    [o] = h.out()
    assert o['error']['code'] == -32600
    assert o['id'] is None


def test_batch_too_large():
    h = Harness(_cfg(max_batch_size=2))
    assert h.recv([{'jsonrpc': '2.0', 'method': 'a'}] * 3) == []
    [o] = h.out()
    assert o['error']['code'] == -32600


def test_batch_member_handling_timeout_still_completes_batch():
    h = Harness(_cfg(inbound_handling_timeout_s=1.))
    h.recv([{'jsonrpc': '2.0', 'method': 'a', 'id': 1}, {'jsonrpc': '2.0', 'method': 'b', 'id': 2}])
    h.send(Jpm.SendResponse(result(1, 'a')))
    assert h.out() == []
    evs = h.tick(1.)
    one(evs, Jpm.RequestHandlingAborted)
    [b] = h.out()
    assert [o['id'] for o in b] == [1, 2]
    assert b[1]['error']['code'] == REQUEST_TIMED_OUT_ERROR_CODE


def test_outbound_batch():
    h = Harness()
    assert h.send(Jpm.SendBatch(Batch([request(1, 'a'), notification('n'), request(2, 'b')]))) == []
    [b] = h.out()
    assert [o.get('id') for o in b] == [1, None, 2]
    assert h.session.pending_outbound_ids == {1, 2}
    evs = h.recv([{'jsonrpc': '2.0', 'result': 'b', 'id': 2}])
    assert [e.request.id for e in only(evs, Jpm.ResponseReceived)] == [2]
    evs = h.recv({'jsonrpc': '2.0', 'result': 'a', 'id': 1})
    assert [e.request.id for e in only(evs, Jpm.ResponseReceived)] == [1]


def test_outbound_batch_timeout():
    h = Harness(_cfg(default_request_timeout_s=3.))
    h.send(Jpm.SendBatch(Batch([request(1, 'a'), request(2, 'b')])))
    evs = h.tick(3.)
    assert sorted(e.request.id for e in only(evs, Jpm.RequestFailed)) == [1, 2]


def test_outbound_batch_with_response_rejected():
    h = Harness()
    evs = h.send(Jpm.SendBatch(Batch([request(1, 'a'), result(2, 'x')])))
    ev = one(evs, Jpm.RequestFailed)
    assert ev.request.id == 1
    assert h.out() == []
    assert not h.session.pending_outbound_ids


##
# oversize outbound


def test_oversize_outbound_request_fails_only_that_request():
    h = Harness(_cfg(max_frame_bytes=64))
    evs = h.send(
        Jpm.SendRequest(request(1, 'a')),
        Jpm.SendRequest(request(2, 'big', {'x': 'y' * 100})),
        Jpm.SendRequest(request(3, 'c')),
    )
    ev = one(evs, Jpm.RequestFailed)
    assert ev.request.id == 2
    assert isinstance(ev.exc, JsonrpcMessageTooLargeError)
    assert [o['id'] for o in h.out()] == [1, 3]
    assert h.session.pending_outbound_ids == {1, 3}
    assert not h.closed


def test_oversize_outbound_response_substituted():
    h = Harness(_cfg(max_frame_bytes=128))
    h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1})
    assert h.send(Jpm.SendResponse(result(1, 'z' * 200))) == []
    [o] = h.out()
    assert o['id'] == 1
    assert o['error']['code'] == RESPONSE_TOO_LARGE_ERROR_CODE
    assert not h.closed


def test_oversize_outbound_response_substitute_too_large_is_dropped():
    h = Harness(_cfg(max_frame_bytes=40))
    h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1})
    assert h.send(Jpm.SendResponse(result(1, 'z' * 200))) == []
    assert h.out() == []
    assert not h.closed


def test_unencodable_outbound_response_substituted():
    h = Harness()
    h.recv({'jsonrpc': '2.0', 'method': 'a', 'id': 1})
    assert h.send(Jpm.SendResponse(result(1, float('nan')))) == []
    [o] = h.out()
    assert o['error']['code'] == KnownErrors.INTERNAL_ERROR.code


def test_unencodable_outbound_request_fails():
    h = Harness()
    evs = h.send(Jpm.SendRequest(request(1, 'a', [float('inf')])))
    ev = one(evs, Jpm.RequestFailed)
    assert isinstance(ev.exc, ValueError)
    assert not h.session.pending_outbound_ids


##
# lifecycle


def test_graceful_close_idle():
    h = Harness()
    evs = h.send(Jpm.Close())
    ev = one(evs, Jpm.Closed)
    assert ev.exc is None
    assert h.closed
    assert h.drv.state is ipl.DriverState.CLOSED


def test_abortive_close():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')))
    h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 'x'})
    h.out()
    evs = h.send(Jpm.Close(graceful=False))
    assert isinstance(one(evs, Jpm.RequestFailed).exc, JsonrpcConnectionClosedError)
    assert one(evs, Jpm.RequestHandlingAborted).request.id == 'x'
    assert one(evs, Jpm.Closed).exc is None
    [o] = h.out()
    assert o['id'] == 'x'
    assert o['error']['code'] == SERVER_SHUTTING_DOWN_ERROR_CODE
    assert h.closed


def test_graceful_close_waits_for_inflight_and_pending():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')))
    h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 'x'})
    h.out()

    assert h.send(Jpm.Close()) == []
    assert h.session.state == 'closing'
    assert not h.closed

    # New outbound requests are refused while closing; new inbound requests are refused with an error.
    evs = h.send(Jpm.SendRequest(request(2, 'late')))
    assert isinstance(one(evs, Jpm.RequestFailed).exc, JsonrpcConnectionClosedError)
    assert h.recv({'jsonrpc': '2.0', 'method': 'c', 'id': 'y'}) == []
    [o] = h.out()
    assert o['id'] == 'y' and o['error']['code'] == SERVER_SHUTTING_DOWN_ERROR_CODE

    evs = h.recv({'jsonrpc': '2.0', 'result': 1, 'id': 1})
    one(evs, Jpm.ResponseReceived)
    assert not h.closed

    evs = h.send(Jpm.SendResponse(result('x', 'done')))
    assert one(evs, Jpm.Closed).exc is None
    [o] = h.out()
    assert o['id'] == 'x'
    assert h.closed


def test_graceful_close_drain_timeout():
    h = Harness(_cfg(close_drain_timeout_s=5.))
    h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 'x'})
    h.send(Jpm.Close())
    assert h.tick(4.) == []
    evs = h.tick(1.)
    assert one(evs, Jpm.RequestHandlingAborted).request.id == 'x'
    assert isinstance(one(evs, Jpm.Closed).exc, JsonrpcTimeoutError)
    [o] = h.out()
    assert o['error']['code'] == SERVER_SHUTTING_DOWN_ERROR_CODE
    assert h.closed


def test_peer_eof_closes():
    h = Harness()
    h.send(Jpm.SendRequest(request(1, 'a')))
    h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 'x'})
    h.out()
    evs = h.eof()
    failed = one(evs, Jpm.RequestFailed)
    assert isinstance(failed.exc, JsonrpcConnectionClosedError)
    assert one(evs, Jpm.RequestHandlingAborted).request.id == 'x'
    assert one(evs, Jpm.Closed).exc is None
    assert h.closed


def test_peer_eof_drain():
    h = Harness(_cfg(on_peer_eof='drain'))
    h.recv({'jsonrpc': '2.0', 'method': 'b', 'id': 'x'})
    evs = h.eof()
    assert not only(evs, Jpm.Closed)
    assert h.session.state == 'closing'
    evs = h.send(Jpm.SendResponse(result('x', 1)))
    one(evs, Jpm.Closed)
    [o] = h.out()
    assert o == {'jsonrpc': '2.0', 'result': 1, 'id': 'x'}
    assert h.closed


def test_peer_eof_with_trailing_partial_line():
    h = Harness()
    h.drv.feed_input(b'{"jsonrpc":"2.0","method":"n"}')
    evs = h.eof()
    assert [e.notification.method for e in only(evs, Jpm.NotificationReceived)] == ['n']
    one(evs, Jpm.Closed)


def test_commands_after_close():
    h = Harness()
    h.send(Jpm.Close())
    assert h.closed
    # The driver is closed; the session would refuse anyway. Just make sure nothing explodes on a closed harness.
    assert h.events() == []


def test_idle_timeout():
    h = Harness(_cfg(idle_timeout_s=10.))
    assert h.tick(9.) == []
    h.recv({'jsonrpc': '2.0', 'method': 'n'})
    assert h.tick(9.) == []
    evs = h.tick(1.)
    assert isinstance(one(evs, Jpm.Closed).exc, JsonrpcTimeoutError)
    assert h.closed


def test_idle_timeout_suppressed_while_inflight():
    h = Harness(_cfg(idle_timeout_s=10., default_request_timeout_s=None))
    h.recv({'jsonrpc': '2.0', 'method': 'slow', 'id': 1})
    assert h.tick(25.) == []
    assert not h.closed
    h.send(Jpm.SendResponse(result(1, 'ok')))
    h.out()
    assert h.tick(9.) == []
    evs = h.tick(1.)
    one(evs, Jpm.Closed)


def test_pipeline_error_closes():
    class Boom(ipl.Handler):
        def inbound(self, ctx, msg):
            if isinstance(msg, ipl.FlowMessages.FlushInput):
                raise RuntimeError('boom')  # noqa
            ctx.feed_in(msg)

    h = Harness(outermost_handlers=[Boom()])
    h.send(Jpm.SendRequest(request(1, 'a')))
    h.out()
    evs = h.recv({'jsonrpc': '2.0', 'method': 'n'})
    ev = one(evs, Jpm.Closed)
    assert isinstance(ev.exc, RuntimeError)
    failed = one(evs, Jpm.RequestFailed)
    assert isinstance(failed.exc, JsonrpcConnectionClosedError)
    assert failed.exc.__cause__ is ev.exc


def test_output_pause_events():
    h = Harness(driver_config=ipl.PureDriver.Config(write_high_watermark=64, write_low_watermark=16))
    evs = h.send(Jpm.SendNotification(notification('n', {'x': 'y' * 200})))
    # Output is drained by the harness as soon as the driver settles, which resumes it again.
    assert [type(e) for e in evs] == [Jpm.OutputPaused, Jpm.OutputResumed]


def test_bad_config():
    with pytest.raises(ValueError):  # noqa
        _cfg(max_frame_bytes=0)
    with pytest.raises(ValueError):  # noqa
        _cfg(default_request_timeout_s=0.)
    with pytest.raises(ValueError):  # noqa
        _cfg(inflight_limit_policy='nope')  # noqa
    with pytest.raises(ValueError):  # noqa
        _cfg(max_inflight_inbound=0)


##
# content-length end to end


def test_content_length_end_to_end():
    h = Harness(_cfg(framing='content-length'))
    h.send(Jpm.SendRequest(request(1, 'a')))
    data = h.out_bytes()
    assert data.startswith(b'Content-Length: ')
    body = data.split(b'\r\n\r\n', 1)[1]
    assert data == b'Content-Length: %d\r\n\r\n' % len(body) + body

    resp = b'{"jsonrpc":"2.0","result":5,"id":1}'
    evs = h.recv_bytes(b'Content-Length: %d\r\n\r\n' % len(resp) + resp)
    assert one(evs, Jpm.ResponseReceived).response.result == 5


##
# sent


def test_sent_after_flush():
    h = Harness()
    cmd = Jpm.SendRequest(request(1, 'a'))
    h.send(cmd)
    assert h.sent == [cmd]
    cmd2 = Jpm.SendNotification(notification('n'))
    h.send(cmd2)
    assert h.sent == [cmd, cmd2]


def test_sent_for_refused_request():
    h = Harness(_cfg(max_pending_outbound=1))
    c1 = Jpm.SendRequest(request(1, 'a'))
    c2 = Jpm.SendRequest(request(2, 'b'))
    h.send(c1, c2)
    # Even a refused send is reported Sent so a host blocked on it wakes up; the RequestFailed says what happened.
    # The refused one reports immediately while the accepted one waits for its flush, hence the order.
    assert h.sent == [c2, c1]


def test_sent_without_flow():
    h = Harness(without_flow=True)
    cmd = Jpm.SendNotification(notification('n'))
    h.send(cmd)
    assert h.sent == [cmd]
    assert h.out() == [{'jsonrpc': '2.0', 'method': 'n'}]


def test_fatal_close_surfaces_raw_exception():
    h = Harness(_cfg(on_invalid_message='close'))
    evs = h.recv_bytes(b'garbage\n')
    ev = one(evs, Jpm.Closed)
    assert h.raised == [ev.exc]


def test_clean_close_surfaces_no_exception():
    h = Harness()
    h.send(Jpm.Close())
    assert h.raised == []
