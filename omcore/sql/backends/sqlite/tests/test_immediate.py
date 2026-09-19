import os.path
import sqlite3
import tempfile

import pytest

from ....api import querierfuncs as qf
from ....api.dbapi import ClosingDbapiConnector
from ....api.dbapi import DbapiDb
from ..adapters import sqlite_adapter


##


def _db(path: str, **kwargs) -> DbapiDb:
    # No busy timeout: whoever would have to wait for a lock fails on the spot instead, which is what is asserted on.
    return DbapiDb(
        ClosingDbapiConnector(sqlite3.connect, path, autocommit=True, timeout=0.),
        adapter=sqlite_adapter(**kwargs),
    )


def _setup(exit_stack, **kwargs):
    path = os.path.join(tempfile.mkdtemp(), 'immediate.db')
    a = exit_stack.enter_context(_db(path, **kwargs).connect())
    b = exit_stack.enter_context(_db(path, **kwargs).connect())

    assert qf.query_scalar(a, 'pragma journal_mode=wal') == 'wal'
    qf.exec(a, 'create table t (id integer primary key, v text)')
    qf.exec(a, "insert into t (v) values ('first')")

    return a, b


def test_deferred_read_then_write_loses_to_a_writer(exit_stack) -> None:
    a, b = _setup(exit_stack)

    with pytest.raises(sqlite3.OperationalError):  # noqa
        with a.begin():
            assert qf.query_scalar(a, 'select count(*) from t') == 1
            qf.exec(b, "insert into t (v) values ('from b')")
            qf.exec(a, "insert into t (v) values ('from a')")

    assert qf.query_scalar(a, 'select count(*) from t') == 2


def test_immediate_read_then_write_holds_off_a_writer(exit_stack) -> None:
    a, b = _setup(exit_stack, immediate=True)

    with a.begin():
        assert qf.query_scalar(a, 'select count(*) from t') == 1
        with pytest.raises(sqlite3.OperationalError):
            qf.exec(b, "insert into t (v) values ('from b')")
        qf.exec(a, "insert into t (v) values ('from a')")

    qf.exec(b, "insert into t (v) values ('from b')")
    assert qf.query_scalar(a, 'select count(*) from t') == 3
