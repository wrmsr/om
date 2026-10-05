-- Postgres ddl. Deltas for the other backends are noted inline; the sql abstraction owns the actual substitution.

create table bus_workers (
    worker_id     uuid primary key,              -- mysql: char(36) / binary(16), sqlite: text
    name          text not null,
    started_at    timestamptz not null,          -- mysql: datetime(6), sqlite: text (utc, naive - the sqlite caveat)
    heartbeat_at  timestamptz not null,
    seqs          jsonb not null default '{}'    -- {dst_id: last seq sent to it}; mysql: json, sqlite: text
) with (fillfactor = 20);

-- This row is rewritten on every heartbeat and every flush. Never index heartbeat_at or seqs: with nothing indexed
-- but the pk, and the low fillfactor above, every update is a HOT update, the table stays a single page forever, and
-- autovacuum has nothing to chase.

create table bus_messages (
    dst_id      uuid not null,
    src_id      uuid not null,
    seq         bigint not null,
    created_at  timestamptz not null default now(),  -- server clock: the only cross-src ordering there is
    payload     jsonb not null,

    -- Also a tripwire: if the sole-writer-per-src_id invariant ever breaks, this fails loudly instead of silently.
    primary key (dst_id, src_id, seq)
);

-- Serves the poll: `where dst_id = ? order by created_at, src_id, seq limit ?`. Ties on created_at are resolved by an
-- incremental sort over what is, at this scale, a handful of rows.
create index bus_messages_dst_created on bus_messages (dst_id, created_at);
