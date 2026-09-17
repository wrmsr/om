"""
Statement text per dialect. Placeholders are written `%s`; sqlite wants `?` - substitute per whatever the sql layer
normalizes to.
"""
from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True)
class Statements:
    upsert_worker: str
    select_worker_seqs: str
    update_heartbeat: str
    select_workers: str
    insert_message: str
    update_seqs: str
    select_messages: str
    delete_message: str


def make_statements(*, now: str, upsert_conflict: str) -> Statements:
    return Statements(
        upsert_worker=(
            'insert into bus_workers (worker_id, name, started_at, heartbeat_at, seqs) '
            f"values (%s, %s, {now}, {now}, '{{}}') "
            f'{upsert_conflict}'
        ),

        select_worker_seqs='select seqs from bus_workers where worker_id = %s',

        update_heartbeat=f'update bus_workers set heartbeat_at = {now} where worker_id = %s',

        select_workers='select worker_id, name, started_at, heartbeat_at from bus_workers',

        insert_message='insert into bus_messages (dst_id, src_id, seq, payload) values (%s, %s, %s, %s)',

        # A full rewrite of the map: the in-memory copy is authoritative since we're the sole writer of our own row.
        # Bumping heartbeat_at here too makes every flush count as a heartbeat.
        update_seqs=f'update bus_workers set seqs = %s, heartbeat_at = {now} where worker_id = %s',

        select_messages=(
            'select src_id, seq, created_at, payload from bus_messages '
            'where dst_id = %s order by created_at, src_id, seq limit %s'
        ),

        delete_message='delete from bus_messages where dst_id = %s and src_id = %s and seq = %s',
    )


def _standard_upsert_conflict(now: str) -> str:
    # Postgres and sqlite (3.24+). seqs is deliberately left alone: it must survive restarts.
    return f'on conflict (worker_id) do update set name = excluded.name, started_at = {now}, heartbeat_at = {now}'


def _mysql_upsert_conflict(now: str) -> str:
    return f'as new on duplicate key update name = new.name, started_at = {now}, heartbeat_at = {now}'


_SQLITE_NOW = "strftime('%Y-%m-%d %H:%M:%f', 'now')"  # utc and naive: the sqlite caveat

POSTGRES_STATEMENTS = make_statements(now='now()', upsert_conflict=_standard_upsert_conflict('now()'))
MYSQL_STATEMENTS = make_statements(now='now(6)', upsert_conflict=_mysql_upsert_conflict('now(6)'))
SQLITE_STATEMENTS = make_statements(now=_SQLITE_NOW, upsert_conflict=_standard_upsert_conflict(_SQLITE_NOW))
