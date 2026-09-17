# sqlbus

A point-to-point message bus over a sql database, for when the database is the only infrastructure you intend to keep.
Postgres is the real backend (advisory locks + listen/notify); mysql and sqlite work by polling alone.

## Invariants

- Every worker has a durable uuid identity and exactly one row in `bus_workers`.
- All bus io for a worker goes through one dedicated, pinned connection. That connection holds the identity lock, the
  listen subscription, and the heartbeat; if it dies, all three die with it, and the worker reconnects and starts over.
  Never pool or proxy this connection.
- A worker is the sole writer of messages with its own `src_id` and the sole reader of messages with its own `dst_id`.
  There are no competing consumers and therefore no `for update skip locked`.
- Seqs are per (src, dst) pair, assigned in memory, and committed to the sender's `bus_workers.seqs` in the same
  transaction as the messages that use them. After a reconnect the row says exactly whether an in-flight batch landed.
- Notify is a wakeup hint, not transport. The loop always polls on wake and on a timer.
- Delivery is at-least-once: a message is deleted after its handler returns, so a crash mid-handler redelivers it on
  restart. `(src_id, seq)` is the idempotency key if the layer above needs one.

## Ops

| op        | when                       | sql                                                                |
| --------- | -------------------------- | ------------------------------------------------------------------ |
| lock      | connect                    | `pg_try_advisory_lock(fold64(worker_id))` / `get_lock(...)`        |
| register  | after lock                 | upsert `bus_workers`, preserving `seqs`                            |
| load seqs | after register             | `select seqs from bus_workers where worker_id = ?`                 |
| listen    | after load                 | `listen bus_<hex>`                                                 |
| flush     | outbox non-empty           | txn: insert messages, rewrite `seqs` (+ heartbeat), notify dsts    |
| poll      | every loop iteration       | `select ... where dst_id = ? order by created_at, src_id, seq`     |
| delete    | after each handler returns | `delete ... where dst_id = ? and src_id = ? and seq = ?`           |
| heartbeat | every `heartbeat_interval` | `update bus_workers set heartbeat_at = now() where worker_id = ?`  |
| wait      | nothing left to do         | `select()` on db socket + waker, bounded by `poll_interval`        |

## Layout

- `types`, `errors`, `handlers` - the data, and the one interface a user implements.
- `sql` - the seam onto the existing sql abstraction.
- `statements`, `store` - the sql text, and the store that runs it.
- `locks`, `signaling`, `waker` - identity locking, wakeups, and the self-pipe.
- `dialects`, `sessions` - per-backend assembly of a connected session.
- `outbox`, `loop`, `bus` - the seq counters, the loop thread, and the public facade.
- `memory` - an in-process `DictBusSessionFactory` for tests and single-process use.
