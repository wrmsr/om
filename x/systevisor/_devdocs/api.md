# Control API

## Transport

The control surface is HTTP/1.1 JSON over an fdio-driven Unix socket and/or an explicitly configured TCP listener.
Unix sockets are the intended default deployment transport. Each connection serves one request and closes; this keeps
request ownership and failure handling small while persistent application-level streams remain available through
chunked responses.

Finite JSON responses use `application/json`. Event and log ranges/follows use newline-delimited JSON. Follow responses
use chunked transfer encoding and stay open until the peer disconnects. Each connection owns a bounded pending queue;
output backpressure can evict queued application records, but cannot stop child-pipe draining. The stream emits an
explicit `stream_gap` record after an eviction.

Log bytes are encoded as base64 in records with absolute byte offsets. A reconnecting reader supplies its last offset;
the first record reports `gap_bytes` when that offset has already fallen out of the configured process back-buffer.
Direct log subscriptions exist below the general event bus, so log following does not require `emit_events` on the
child output configuration.

## Routes

- `GET /` returns manager identity, API version, config generation, and shutdown state.
- `GET /v1/state` returns the serializable engine state.
- `GET /v1/units` returns current instance states.
- `GET /v1/collections` returns collection desired/status/failure state.
- `GET /v1/schedules` returns configured schedule timing, counters, and last operation identity.
- `GET /v1/resources` returns retained per-run samples, cgroup lifecycle state, and adopted listener descriptors.
- `GET /v1/resources/{run}` returns the retained sample and cgroup state for one run.
- `GET /v1/config` returns the active snapshot, last config attempt, and source settings.
- `GET /v1/self-update` returns the current probe/prepare/exec state.
- `POST /v1/config/_check` compiles without applying.
- `POST /v1/config/_reload` prepares and atomically applies a candidate.
- `GET /v1/operations` and `GET /v1/operations/{id}` expose asynchronous command records.
- `POST /v1/units/{name}/_start|_stop` changes a unit's desired state.
- `POST /v1/collections/{name}/_start|_stop` changes a collection's desired state.
- `POST /v1/instances/{id}/_start|_stop|_restart` acts on one replica.
- `POST /v1/_shutdown` begins reconciled shutdown.
- `POST /v1/_self_update` with `{"source": "/absolute/candidate.py"}` probes and schedules an in-place artifact
  update.
- `GET /v1/events?after=N&topic=T&follow=true` replays and optionally follows events.
- `GET /v1/logs` lists retained log channels.
- `GET /v1/logs/{run}/{stdout|stderr}?offset=N&limit=N&follow=true` reads or follows bytes.

Mutation responses contain an operation. A `200` means it already reached a terminal operation state; a `202` means
the HTTP request was accepted but the lifecycle goal is still pending. Callers observe the operation endpoint or event
stream rather than keeping a handler blocked on process state.

## CLI

`./python -m x.systevisor` is the shared entrypoint. `serve` runs the manager; `run` manages one collection as a
foreground compose-like unit; `config-check` works offline; `status`,
`units`, `collections`, `schedules`, `resources [RUN]`, `config`, `operations`, `check`, `reload`, `start`, `stop`, `restart`, `shutdown`, `self-update`, `events`,
and `logs` use the
same HTTP API. Client HTTP framing uses omcore I/O pipelines over a synchronous socket because the CLI is a separate
short-lived process; the server always uses the fdio driver.

`self-update SOURCE` accepts only a regular generated amalgamated Systevisor artifact. The response operation remains
pending while the client connection closes, the candidate probe exits, and the old image reaches its short response
grace deadline. Clients reconnect to inspect completion because control listeners and accepted connections are not
part of the handoff.

`service-template systemd|launchd --executable PATH -c CONFIG...` is intentionally local rather than an HTTP command.
It emits a direct-exec opaque service definition and never installs or activates it. The user remains in control of
the platform service manager and filesystem locations.

## Configuration failure visibility

A live invalid candidate leaves the active snapshot and managed processes unchanged. The attempt appears in the API,
the event journal, and—when a state directory is known—an atomically replaced `config-status.json`. A cold invalid
candidate is printed to stderr and exits with status 2. This intentionally uses ordinary service logs/status rather
than desktop notifications or a platform-specific UI.

Runtime participants can prepare resources before reconciliation. The HTTP participant binds candidate listeners
first. If a path or address is unavailable, reload is rejected at the `prepare` diagnostic stage and no process config
is changed. Prepared resources are rolled back if another participant rejects the transaction.
