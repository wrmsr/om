"""Cases drawn from section 7 of https://www.jsonrpc.org/specification, plus edge cases the spec leaves implicit."""
import math

import pytest

from ....formats.json import all as json
from ..errors import JsonrpcInvalidMessageError
from ..errors import KnownErrors
from ..parsing import ParseOptions
from ..parsing import Payloads
from ..parsing import dump_message
from ..parsing import dumps_payload
from ..parsing import loads_payload
from ..parsing import parse_message
from ..parsing import parse_payload
from ..types import Batch
from ..types import Error
from ..types import InvalidMessage
from ..types import NotSpecified
from ..types import Request
from ..types import Response
from ..types import error
from ..types import notification
from ..types import request
from ..types import result


def _parse(s):
    return loads_payload(s.encode('utf-8'))


##
# spec section 7


def test_positional_params():
    msg = _parse('{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
    assert msg == request(1, 'subtract', [42, 23])

    resp = _parse('{"jsonrpc": "2.0", "result": 19, "id": 1}')
    assert resp == result(1, 19)


def test_named_params():
    msg = _parse('{"jsonrpc": "2.0", "method": "subtract", "params": {"subtrahend": 23, "minuend": 42}, "id": 3}')
    assert msg == request(3, 'subtract', {'subtrahend': 23, 'minuend': 42})


def test_notification():
    msg = _parse('{"jsonrpc": "2.0", "method": "update", "params": [1,2,3,4,5]}')
    assert msg == notification('update', [1, 2, 3, 4, 5])
    assert msg.is_notification

    msg = _parse('{"jsonrpc": "2.0", "method": "foobar"}')
    assert msg == notification('foobar')
    assert msg.params is None


def test_method_not_found_response():
    resp = _parse('{"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"}')
    assert resp == error('1', Error(-32601, 'Method not found'))
    assert resp.is_error
    assert resp.error.data is NotSpecified


def test_invalid_json():
    inv = _parse('{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]')
    assert isinstance(inv, InvalidMessage)
    assert inv.error.code == KnownErrors.PARSE_ERROR.code
    assert inv.id is None
    assert not inv.looks_like_response
    assert dump_message(inv) == {'jsonrpc': '2.0', 'error': {'code': -32700, 'message': 'Parse error'}, 'id': None}


def test_invalid_request_object():
    inv = _parse('{"jsonrpc": "2.0", "method": 1, "params": "bar"}')
    assert isinstance(inv, InvalidMessage)
    assert inv.error.code == KnownErrors.INVALID_REQUEST.code
    assert inv.id is None


def test_batch_invalid_json():
    inv = _parse('[ {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"}, {"jsonrpc": "2.0", "method" ]')
    assert isinstance(inv, InvalidMessage)
    assert inv.error.code == KnownErrors.PARSE_ERROR.code


def test_empty_batch():
    inv = _parse('[]')
    assert isinstance(inv, InvalidMessage)
    assert inv.error.code == KnownErrors.INVALID_REQUEST.code
    assert not isinstance(inv, Batch)


def test_batch_of_one_invalid():
    b = _parse('[1]')
    assert isinstance(b, Batch)
    assert len(b) == 1
    assert isinstance(b.items[0], InvalidMessage)
    assert b.items[0].error.code == KnownErrors.INVALID_REQUEST.code


def test_batch_of_three_invalid():
    b = _parse('[1,2,3]')
    assert isinstance(b, Batch)
    assert [type(i) for i in b] == [InvalidMessage] * 3


def test_mixed_batch():
    b = _parse("""[
        {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
        {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
        {"jsonrpc": "2.0", "method": "subtract", "params": [42,23], "id": "2"},
        {"foo": "boo"},
        {"jsonrpc": "2.0", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
        {"jsonrpc": "2.0", "method": "get_data", "id": "9"}
    ]""")
    assert isinstance(b, Batch)
    assert len(b) == 6
    assert b.items[0] == request('1', 'sum', [1, 2, 4])
    assert b.items[1] == notification('notify_hello', [7])
    assert b.items[2] == request('2', 'subtract', [42, 23])
    assert isinstance(b.items[3], InvalidMessage)
    assert b.items[3].id is None
    assert b.items[4] == request('5', 'foo.get', {'name': 'myself'})
    assert b.items[5] == request('9', 'get_data')
    assert not Payloads.is_notification_only(b)


def test_all_notification_batch():
    b = _parse('[{"jsonrpc": "2.0", "method": "notify_sum", "params": [1,2,4]}, {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]}]')  # noqa
    assert isinstance(b, Batch)
    assert Payloads.is_notification_only(b)


def test_batch_of_responses():
    b = _parse('[{"jsonrpc": "2.0", "result": 7, "id": "1"}, {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null}]')  # noqa
    assert isinstance(b, Batch)
    assert b.items[0] == result('1', 7)
    assert b.items[1] == error(None, Error(-32600, 'Invalid Request'))


##
# edge cases


def test_invalid_id_detection_keeps_valid_id():
    inv = _parse('{"jsonrpc": "2.0", "method": 1, "id": 7}')
    assert isinstance(inv, InvalidMessage)
    assert inv.id == 7
    assert dump_message(inv)['id'] == 7


def test_invalid_id_is_nulled():
    inv = _parse('{"jsonrpc": "2.0", "method": "x", "id": {"a": 1}}')
    assert isinstance(inv, InvalidMessage)
    assert inv.id is None


def test_bool_id_rejected():
    inv = _parse('{"jsonrpc": "2.0", "method": "x", "id": true}')
    assert isinstance(inv, InvalidMessage)


def test_null_request_id():
    msg = _parse('{"jsonrpc": "2.0", "method": "x", "id": null}')
    assert isinstance(msg, Request)
    assert msg.id is None
    assert not msg.is_notification

    inv = parse_payload({'jsonrpc': '2.0', 'method': 'x', 'id': None}, ParseOptions(allow_null_request_id=False))
    assert isinstance(inv, InvalidMessage)


def test_float_id():
    msg = _parse('{"jsonrpc": "2.0", "method": "x", "id": 1.5}')
    assert isinstance(msg, Request)
    assert msg.id == 1.5


def test_missing_version():
    inv = _parse('{"method": "x", "id": 1}')
    assert isinstance(inv, InvalidMessage)
    assert inv.id == 1

    msg = parse_payload({'method': 'x', 'id': 1}, ParseOptions(require_version=False))
    assert msg == request(1, 'x')


def test_wrong_version():
    inv = _parse('{"jsonrpc": "1.0", "method": "x", "id": 1}')
    assert isinstance(inv, InvalidMessage)


def test_string_params_rejected():
    inv = _parse('{"jsonrpc": "2.0", "method": "x", "params": "nope", "id": 1}')
    assert isinstance(inv, InvalidMessage)
    assert inv.id == 1


def test_response_both_result_and_error():
    inv = _parse('{"jsonrpc": "2.0", "result": 1, "error": {"code": 1, "message": "m"}, "id": 1}')
    assert isinstance(inv, InvalidMessage)
    assert inv.looks_like_response


def test_response_missing_id():
    inv = _parse('{"jsonrpc": "2.0", "result": 1}')
    assert isinstance(inv, InvalidMessage)
    assert inv.looks_like_response


def test_response_bad_error():
    for s in [
        '{"jsonrpc": "2.0", "error": "boom", "id": 1}',
        '{"jsonrpc": "2.0", "error": {"message": "m"}, "id": 1}',
        '{"jsonrpc": "2.0", "error": {"code": "1", "message": "m"}, "id": 1}',
        '{"jsonrpc": "2.0", "error": {"code": true, "message": "m"}, "id": 1}',
        '{"jsonrpc": "2.0", "error": {"code": 1}, "id": 1}',
        '{"jsonrpc": "2.0", "error": {"code": 1, "message": 2}, "id": 1}',
    ]:
        inv = _parse(s)
        assert isinstance(inv, InvalidMessage), s
        assert inv.looks_like_response, s


def test_error_with_data():
    resp = _parse('{"jsonrpc": "2.0", "error": {"code": 1, "message": "m", "data": {"x": [1]}}, "id": 1}')
    assert resp == error(1, Error(1, 'm', {'x': [1]}))


def test_null_result():
    resp = _parse('{"jsonrpc": "2.0", "result": null, "id": 1}')
    assert isinstance(resp, Response)
    assert resp.is_result
    assert resp.result is None


def test_no_method_no_result_no_error():
    inv = _parse('{"jsonrpc": "2.0", "id": 1}')
    assert isinstance(inv, InvalidMessage)
    assert not inv.looks_like_response
    assert inv.id == 1


def test_non_object_top_level():
    for s in ['1', '"x"', 'null', 'true']:
        inv = _parse(s)
        assert isinstance(inv, InvalidMessage), s
        assert inv.error.code == KnownErrors.INVALID_REQUEST.code


def test_extra_members_ignored():
    msg = _parse('{"jsonrpc": "2.0", "method": "x", "id": 1, "extra": 5}')
    assert msg == request(1, 'x')


def test_strict_parse_message_raises():
    with pytest.raises(JsonrpcInvalidMessageError):
        parse_message({'jsonrpc': '2.0'})
    with pytest.raises(JsonrpcInvalidMessageError):
        parse_message([])


def test_invalid_utf8():
    inv = loads_payload(b'\xff\xfe')
    assert isinstance(inv, InvalidMessage)
    assert inv.error.code == KnownErrors.PARSE_ERROR.code


def test_memoryview_input():
    msg = loads_payload(memoryview(b'{"jsonrpc": "2.0", "method": "x"}'))
    assert msg == notification('x')


##
# dumping


def test_dump_roundtrip():
    msgs: list = [
        request(1, 'a'),
        request('s', 'a', {'k': 'v'}),
        request(2, 'a', [1, 2]),
        request(3, 'a', {}),
        request(None, 'a'),
        notification('n'),
        notification('n', [1]),
        result(1, None),
        result(1, {'x': 1}),
        error(1, Error(1, 'm')),
        error(None, Error(1, 'm', [1, 2])),
    ]
    for msg in msgs:
        s = dumps_payload(msg)
        assert '\n' not in s
        back = loads_payload(s)
        assert back == msg, msg


def test_dump_omits_only_none_params():
    assert 'params' not in dump_message(request(1, 'a'))
    assert dump_message(request(1, 'a', {}))['params'] == {}
    assert dump_message(request(1, 'a', []))['params'] == []


def test_dump_batch_roundtrip():
    b = Batch([request(1, 'a'), notification('n'), result(2, 3)])
    s = dumps_payload(b)
    back = loads_payload(s)
    assert back == b


def test_dump_invalid_message_as_error_response():
    inv = InvalidMessage(KnownErrors.PARSE_ERROR.to_error(), id=None)
    assert json.loads(dumps_payload(inv)) == {
        'jsonrpc': '2.0',
        'error': {'code': -32700, 'message': 'Parse error'},
        'id': None,
    }


def test_dump_rejects_non_finite():
    with pytest.raises(ValueError):  # noqa
        dumps_payload(result(1, math.nan))
    with pytest.raises(ValueError):  # noqa
        dumps_payload(result(1, {'a': [math.inf]}))


def test_dump_rejects_circular():
    d: dict = {}
    d['self'] = d
    with pytest.raises(ValueError):  # noqa
        dumps_payload(result(1, d))


def test_dump_normalizes_abstract_params():
    import types
    msg = request(1, 'a', types.MappingProxyType({'k': 1}))
    assert dump_message(msg)['params'] == {'k': 1}
    msg = request(1, 'a', (1, 2))
    assert dump_message(msg)['params'] == [1, 2]
