"""Import-time and error-path smoke tests for the cursor module.

These need no database: they guard against the cursor module failing to import (or its error references failing to
resolve), which would otherwise make the whole `omysql` package unimportable.
"""
import pytest

from ... import errors
from ..sync import Cursor
from ..sync import DictCursor
from ..sync import SSCursor
from ..sync import SSDictCursor


def test_cursor_classes_import():
    assert issubclass(DictCursor, Cursor)
    assert issubclass(SSCursor, Cursor)
    assert issubclass(SSDictCursor, SSCursor)


def test_check_executed_raises_programming_error():
    cur = Cursor(object())
    with pytest.raises(errors.ProgrammingError):
        cur.fetchone()


def test_unknown_scroll_mode_raises_programming_error():
    cur = Cursor(object())
    cur._executed = 'SELECT 1'  # noqa: SLF001
    with pytest.raises(errors.ProgrammingError):
        cur.scroll(0, mode='nonsense')
