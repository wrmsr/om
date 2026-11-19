import os
import sys
import typing as ta


##


class ShiftUid(ta.NamedTuple):
    uid: int
    gid: int


def resolve_auto_shift_uid() -> ShiftUid | None:
    if sys.platform == 'linux':
        return ShiftUid(os.getuid(), os.getgid())
    else:
        return None


##


ShiftUidParam: ta.TypeAlias = ShiftUid | ta.Literal['off'] | None


def resolve_shift_uid(param: ShiftUidParam) -> ShiftUid | None:
    if param is None:
        return resolve_auto_shift_uid()
    elif param == 'off':
        return None
    else:
        return param


def parse_shift_uid(s: str | None) -> ShiftUidParam:
    if s is None:
        return None
    elif s == 'off':
        return 'off'
    else:
        return ShiftUid(*map(int, s.split(':')))
