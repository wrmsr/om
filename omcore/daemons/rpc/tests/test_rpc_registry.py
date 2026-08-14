import threading

import pytest

from ...tests.testing import TEST_TIMEOUT_S
from ..dispatch import RpcRequestDispatcher
from ..pipelines import RpcWireError
from ..pipelines import RpcWireResult
from ..protocol import RpcRequest
from ..registry import RpcResponseExecute
from ..registry import RpcResponsePending
from ..registry import RpcResponseRegistry
from ..registry import RpcResponseRejected
from ..registry import RpcResponseReplay


##


def _request(
        request_id: str,
        params: object = None,
) -> RpcRequest:
    return RpcRequest(
        client_id='client',
        request_id=request_id,
        method='echo',
        params=params,
    )


def test_rpc_response_registry_execute_pending_complete_and_replay():
    registry = RpcResponseRegistry(max_entries=2)
    request = _request('one')

    execute = registry.claim(request)
    assert isinstance(execute, RpcResponseExecute)
    pending = registry.claim(request)
    assert isinstance(pending, RpcResponsePending)
    assert pending.entry is execute.entry

    waiter_started = threading.Event()
    waited: list[RpcWireResult | RpcWireError] = []

    def wait() -> None:
        waiter_started.set()
        waited.append(pending.entry.wait(TEST_TIMEOUT_S))

    waiter = threading.Thread(target=wait)
    waiter.start()
    assert waiter_started.wait(TEST_TIMEOUT_S)

    callback_results: list[RpcWireResult | RpcWireError] = []
    execute.entry.add_done_callback(callback_results.append)
    response = RpcWireResult(
        client_id=request.client_id,
        request_id=request.request_id,
        result={'ok': True},
    )
    registry.complete(execute.entry, response)

    waiter.join(TEST_TIMEOUT_S)
    assert not waiter.is_alive()
    assert waited == [response]
    assert callback_results == [response]
    assert execute.entry.done
    assert execute.entry.result() is response

    replay = registry.claim(request)
    assert isinstance(replay, RpcResponseReplay)
    assert replay.response is response

    late_callback_results: list[RpcWireResult | RpcWireError] = []
    execute.entry.add_done_callback(late_callback_results.append)
    assert late_callback_results == [response]


def test_rpc_response_registry_rejects_conflict_and_capacity_without_eviction():
    registry = RpcResponseRegistry(max_entries=1)
    first = _request('one', {'value': 1})
    assert isinstance(registry.claim(first), RpcResponseExecute)

    conflict = registry.claim(_request('one', {'value': 2}))
    assert isinstance(conflict, RpcResponseRejected)
    assert conflict.response.code == 'protocol'
    assert 'reused with different request data' in conflict.response.message

    full = registry.claim(_request('two'))
    assert isinstance(full, RpcResponseRejected)
    assert full.response.code == 'remote'
    assert full.response.remote_type == 'omcore.daemons.rpc.RpcRequestCacheFullError'
    assert len(registry) == 1


def test_rpc_response_registry_rejects_foreign_entry_and_response_identity():
    registry = RpcResponseRegistry(max_entries=1)
    other_registry = RpcResponseRegistry(max_entries=1)
    request = _request('one')
    execute = registry.claim(request)
    other_execute = other_registry.claim(request)
    assert isinstance(execute, RpcResponseExecute)
    assert isinstance(other_execute, RpcResponseExecute)

    wrong_response = RpcWireResult(
        client_id=request.client_id,
        request_id='other',
        result=None,
    )
    with pytest.raises(ValueError, match='identity'):
        registry.complete(execute.entry, wrong_response)

    response = RpcWireResult(
        client_id=request.client_id,
        request_id=request.request_id,
        result=None,
    )
    with pytest.raises(ValueError, match='does not belong'):
        registry.complete(other_execute.entry, response)


@pytest.mark.parametrize('result', [object(), float('nan'), float('inf')])
def test_rpc_request_dispatcher_caches_a_bounded_protocol_error_for_invalid_results(result):
    calls = 0

    def handler(request: RpcRequest):
        nonlocal calls
        calls += 1
        return result

    registry = RpcResponseRegistry(max_entries=1)
    dispatcher = RpcRequestDispatcher(
        handler,
        registry,
        max_frame_bytes=1_024,
    )
    request = _request('invalid-result')

    response = dispatcher.dispatch(request)
    assert isinstance(response, RpcWireError)
    assert response.code == 'remote'
    assert response.remote_type == 'omcore.daemons.rpc.protocol.RpcProtocolError'
    assert dispatcher.dispatch(request) is response
    assert calls == 1
