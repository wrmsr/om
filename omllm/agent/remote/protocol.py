# ruff: noqa: UP006 UP007 UP045
"""JSON-compatible values shared by the host adapter and the remote agent payload."""
import base64
import binascii
import typing as ta


##


FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
FS_STAT_METHOD = 'fs.stat'
FS_READ_FILE_METHOD = 'fs.read_file'
FS_WRITE_FILE_METHOD = 'fs.write_file'
FS_LIST_DIR_METHOD = 'fs.list_dir'
FS_GLOB_METHOD = 'fs.glob'

PROCESS_SPAWN_METHOD = 'process.spawn'
PROCESS_SIGNAL_METHOD = 'process.signal'
PROCESS_CLOSE_METHOD = 'process.close'
PROCESS_WRITE_METHOD = 'process.write'
PROCESS_WRITE_EOF_METHOD = 'process.write_eof'
PROCESS_RESIZE_METHOD = 'process.resize'

PROCESS_OUTPUT_METHOD = 'process.output'
PROCESS_OUTPUT_END_METHOD = 'process.output_end'
PROCESS_EXITED_METHOD = 'process.exited'


##


def encode_remote_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def decode_remote_bytes(value: ta.Any) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f'Expected base64 string, got {type(value).__name__}')
    try:
        return base64.b64decode(value.encode('ascii'), validate=True)
    except (UnicodeEncodeError, binascii.Error) as e:
        raise ValueError('Invalid base64 data') from e


def check_remote_dict(
        value: ta.Any,
        required: ta.AbstractSet[str],
        optional: ta.AbstractSet[str] = frozenset(),
) -> ta.Dict[str, ta.Any]:
    if not isinstance(value, dict):
        raise TypeError(f'Expected object, got {type(value).__name__}')
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise ValueError(
            f'Invalid object fields: required {sorted(required)!r}, '
            f'optional {sorted(optional)!r}, got {sorted(keys)!r}',
        )
    return value


def check_remote_str(value: ta.Any, *, non_empty: bool = False) -> str:
    if not isinstance(value, str) or (non_empty and not value):
        raise TypeError(f'Expected {"non-empty " if non_empty else ""}string, got {value!r}')
    return value


def check_remote_optional_str(value: ta.Any) -> ta.Optional[str]:
    if value is None:
        return None
    return check_remote_str(value)


def check_remote_bool(value: ta.Any) -> bool:
    if type(value) is not bool:
        raise TypeError(f'Expected bool, got {value!r}')
    return value


def check_remote_int(value: ta.Any, *, minimum: ta.Optional[int] = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise TypeError(f'Expected integer >= {minimum!r}, got {value!r}')
    return value


def check_remote_optional_int(value: ta.Any, *, minimum: ta.Optional[int] = None) -> ta.Optional[int]:
    if value is None:
        return None
    return check_remote_int(value, minimum=minimum)


def check_remote_float(value: ta.Any, *, minimum: ta.Optional[float] = None) -> float:
    if type(value) not in (int, float):
        raise TypeError(f'Expected number, got {value!r}')
    out = float(value)
    if minimum is not None and out < minimum:
        raise ValueError(f'Expected number >= {minimum!r}, got {value!r}')
    return out


def check_remote_optional_float(value: ta.Any, *, minimum: ta.Optional[float] = None) -> ta.Optional[float]:
    if value is None:
        return None
    return check_remote_float(value, minimum=minimum)


def check_remote_str_list(value: ta.Any, *, non_empty: bool = False) -> ta.List[str]:
    if not isinstance(value, list) or (non_empty and not value):
        raise TypeError(f'Expected {"non-empty " if non_empty else ""}string list, got {value!r}')
    for item in value:
        check_remote_str(item)
    return value


def check_remote_optional_str_dict(value: ta.Any) -> ta.Optional[ta.Dict[str, str]]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f'Expected string object, got {value!r}')
    for key, item in value.items():
        check_remote_str(key, non_empty=True)
        check_remote_str(item)
    return value
