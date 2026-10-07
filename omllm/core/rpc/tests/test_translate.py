import pytest

from ..errors import RpcRemoteError
from ..errors import RpcRemoteErrorData
from ..translate import translate_rpc_remote_builtin_error


def _remote_error(remote_type: str, message: str = 'boom') -> RpcRemoteError:
    return RpcRemoteError(RpcRemoteErrorData(code='remote', remote_type=remote_type, message=message))


def test_translates_known_builtins():
    translated = translate_rpc_remote_builtin_error(_remote_error('builtins.FileNotFoundError', '/nope'))
    assert type(translated) is FileNotFoundError
    assert str(translated) == '/nope'


def test_leaves_the_rest_alone():
    error = _remote_error('some.module.CustomError')
    assert translate_rpc_remote_builtin_error(error) is error
    with pytest.raises(RpcRemoteError):
        raise translate_rpc_remote_builtin_error(error)
