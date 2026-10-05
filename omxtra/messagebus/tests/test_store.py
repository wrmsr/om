import datetime
import json

from ..locks import PostgresAdvisoryIdentityLock
from ..signaling import PostgresSignaling
from ..statements import MYSQL_STATEMENTS
from ..statements import POSTGRES_STATEMENTS
from ..statements import SQLITE_STATEMENTS
from ..store import SqlMessageStore
from ..types import Message
from ..types import new_worker_id
from ..waker import Waker
from .conns import RecordingSqlConn


def test_load_seqs_accepts_encoded_and_decoded_json():
    a, b = new_worker_id(), new_worker_id()
    conn = RecordingSqlConn([
        [[json.dumps({str(b): 3})]],
        [[{str(b): 4}]],
    ])
    st = SqlMessageStore(conn, POSTGRES_STATEMENTS)
    assert st.load_seqs(a) == {b: 3}
    assert st.load_seqs(a) == {b: 4}
    assert [p for _, p in conn.calls] == [[str(a)], [str(a)]]


def test_update_seqs_writes_the_whole_map():
    a, b, c = new_worker_id(), new_worker_id(), new_worker_id()
    conn = RecordingSqlConn()
    SqlMessageStore(conn, POSTGRES_STATEMENTS).update_seqs(a, {b: 7, c: 1})
    [(sql, [seqs_json, wid])] = conn.calls
    assert sql == POSTGRES_STATEMENTS.update_seqs
    assert json.loads(seqs_json) == {str(b): 7, str(c): 1}
    assert wid == str(a)


def test_message_round_trip():
    a, b = new_worker_id(), new_worker_id()
    now = datetime.datetime.now(datetime.UTC)
    conn = RecordingSqlConn([
        [],
        [[str(a), 5, now, json.dumps({'k': [1, 2]})]],
    ])
    st = SqlMessageStore(conn, POSTGRES_STATEMENTS)

    st.insert_message(Message(b, a, 5, {'k': [1, 2]}))
    [m] = st.select_messages(b, limit=10)
    assert m == Message(b, a, 5, {'k': [1, 2]}, now)

    st.delete_message(m)
    assert [s for s, _ in conn.calls] == [
        POSTGRES_STATEMENTS.insert_message,
        POSTGRES_STATEMENTS.select_messages,
        POSTGRES_STATEMENTS.delete_message,
    ]
    assert conn.calls[0][1] == [str(b), str(a), 5, json.dumps({'k': [1, 2]})]
    assert conn.calls[2][1] == [str(b), str(a), 5]


def test_upserts_never_touch_seqs():
    for stmts in (POSTGRES_STATEMENTS, MYSQL_STATEMENTS, SQLITE_STATEMENTS):
        _, update = stmts.upsert_worker.lower().split('update', 1)
        assert 'seqs' not in update


def test_postgres_lock_folds_uuid_to_an_int8_key():
    a = new_worker_id()
    conn = RecordingSqlConn([[[True]], [[False]]])
    lk = PostgresAdvisoryIdentityLock(conn, a)
    assert lk.try_acquire()
    assert not lk.try_acquire()
    for sql, [key] in conn.calls:
        assert sql == 'select pg_try_advisory_lock(%s)'
        assert isinstance(key, int)
        assert -2 ** 63 <= key < 2 ** 63


def test_postgres_signaling_sql():
    a, b = new_worker_id(), new_worker_id()
    conn = RecordingSqlConn()
    w = Waker()
    try:
        sig = PostgresSignaling(conn, a)
        sig.listen(w)
        sig.notify([b, b])
    finally:
        w.close()
    assert conn.calls == [
        (f'listen bus_{a.hex}', []),
        ('select pg_notify(%s, %s)', [f'bus_{b.hex}', '']),
        ('select pg_notify(%s, %s)', [f'bus_{b.hex}', '']),
    ]
    assert len(f'bus_{a.hex}') <= 63
