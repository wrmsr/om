import os.path
import sqlite3
import tempfile
import uuid

from ..db import write_run_to_db


##


def test_write_run_to_db():
    path = os.path.join(tempfile.mkdtemp(), 'runs.db')
    run_id = uuid.uuid7()

    write_run_to_db(id=run_id, db_file=path)

    with sqlite3.connect(path) as conn:
        assert conn.execute('select id from runs').fetchall() == [(str(run_id),)]
