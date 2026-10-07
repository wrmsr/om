# ruff: noqa: UP006 UP007 UP045
"""Translation of remote errors back into local exception types, for clients layering a typed api over the rpc."""
import typing as ta

from .errors import RpcRemoteError


##


# Builtin exceptions a remote handler may raise which mean the same thing on both sides, keyed by the qualified type
# name the error data carries.
RPC_TRANSLATED_BUILTIN_EXCEPTIONS: ta.Mapping[str, ta.Type[Exception]] = {
    'builtins.BrokenPipeError': BrokenPipeError,
    'builtins.FileExistsError': FileExistsError,
    'builtins.FileNotFoundError': FileNotFoundError,
    'builtins.IsADirectoryError': IsADirectoryError,
    'builtins.NotADirectoryError': NotADirectoryError,
    'builtins.PermissionError': PermissionError,
    'builtins.ProcessLookupError': ProcessLookupError,
}


def translate_rpc_remote_builtin_error(exc: RpcRemoteError) -> Exception:
    """The local builtin equivalent of a remote error, or the error itself when it has none."""

    if (cls := RPC_TRANSLATED_BUILTIN_EXCEPTIONS.get(exc.remote_type)) is not None:
        return cls(exc.remote_message)
    return exc
