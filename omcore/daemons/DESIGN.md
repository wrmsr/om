# Daemon Design

This document records the durable contracts of `omcore.daemons`: process ownership, startup, identity, readiness,
activity, shutdown, and RPC call outcomes. Introductory usage and the runnable example live in
[README.md](README.md).

---

## 1. Scope

The package supports application-owned background services without requiring `systemd`, `launchd`, a container
orchestrator, or another external supervisor. Its central use case is a worker which is started on demand, may outlive
the caller which started it, serves concurrent local clients, lingers for a bounded idle period, and exits gracefully.

Primary goals are:

- explicit selection of thread, multiprocessing, raw-fork, reparent, and exec boundaries;
- cross-process single-instance coordination through a locked pidfile;
- observable startup failure and bounded startup waiting;
- readiness based on a real application probe rather than process existence;
- lazy launch which is safe under concurrent callers;
- activity-aware idle exit and bounded graceful drain;
- local RPC with explicit request identity and honest retry outcomes; and
- small layers which can be used independently.

Non-goals currently include:

- replacing a full external supervisor when restart policy, privilege changes, resource isolation, or machine boot
  integration is required;
- hiding the hazards of `fork(2)`;
- making inherited application state safe automatically;
- remote-network RPC, transport encryption, or user authentication;
- promising exactly-once effects across service replacement or durable storage loss;
- serializing arbitrary Python objects; and
- inferring code compatibility strongly enough to make pickle safe.

---

## 2. Structural model

The principal composition is:

```text
application call
      |
      v
LazyRpcClient ----------------------+
      |                              |
      v                              v
  RpcClient                     LazyDaemon
      |                              |
      | Unix socket                  v
      |                           Daemon
      |                              |
      |                              v
      |                           Launcher
      |                        /     |      \
      |                 pidfile   monitor   Spawner
      |                                      |
      +-------------------------------> RpcService
                                              |
                                              v
                                       ServiceRuntime
```

The pieces are not required to occur together. `Launcher` can run any `Target`; `RuntimeService` does not require RPC;
`RpcService` can be run directly; and `Daemon` can launch a service which never exits on idle.

Targets describe work. Spawners create an execution context. Launchers coordinate ownership and startup. Daemons add
readiness. Services package configuration and execution. Runtime supplies activity and shutdown state. Lazy controllers
connect these into an on-demand policy.

### RPC dependency boundary

RPC is colocated under `omcore.daemons` for now, but it is not part of the daemon lifecycle abstraction. Its modules
make the boundary explicit:

- `rpc.protocol`, `rpc.client`, `rpc.server`, and `rpc.objects` are lifecycle-independent RPC pieces;
- `rpc.services` adapts `RpcServer` to `ServiceRuntime`;
- `rpc.lazy` composes `RpcClient` with `LazyDaemon`; and
- `rpc.waiting` adapts an RPC handshake to the general readiness interface.

`RpcServer` depends on the small `RpcServerRuntime` interface rather than on `ServiceRuntime`. Consequently it can run
under a thread, a different supervisor, or an eventual remote-host runtime. In the other direction, daemon code does
not require RPC: targets can be ordinary functions, in-process services, HTTP servers, or other protocols.

---

## 3. Launch ownership and startup

`Launcher.launch()` returns `False` only when another owner already holds the configured pidfile lock. Returning `True`
means the new worker crossed the launch boundary; it does not mean that an application-specific endpoint is ready.
`Daemon.launch()` follows launch with its configured readiness probe.

The launch sequence is:

1. Create the selected spawner.
2. Open the pidfile, acquire its exclusive nonblocking lock, and arrange controlled descriptor inheritance.
3. Create a startup reporting channel and include its descriptor in the inherited set.
4. Spawn the worker.
5. In the worker, optionally reparent before producing final identity.
6. Duplicate/enter the inherited pidfile, create `DaemonPidfileInfo`, and write PID plus JSON suffix while locked.
7. Resolve the target runner and report launch success.
8. Run the target.

An exception before the one-shot success report is serialized as `LaunchErrorInfo`. If a launcher owns the new child
and startup fails, it explicitly joins/reaps that child before raising `LaunchError`. A startup timeout is also bounded.
After success, the worker is intentionally permitted to outlive the launcher; the happy path does not retain a join
handle as a supervision policy.

Target failure after the launch boundary is a service/process failure, not a retroactive startup failure. Readiness may
still fail if the target exits before becoming usable.

### Spawner contracts

`ThreadSpawning` runs `_run_spawn` in a thread. It shares all process state. `linger=False` makes that thread a Python
daemon thread; `linger=True` gives it ordinary thread shutdown behavior.

`MultiprocessingSpawning` uses either a clean spawn context with explicitly passed descriptors or multiprocessing fork.
Its optional entrypoint runs in the new child before the launch function and is the appropriate place for bootstrap
work such as logging configuration.

`ForkSpawning` calls `os.fork()` directly. Its parent owns a `ForkSpawned` handle capable of `waitpid`-based joining.
Its child invokes `post_fork`, runs the target, and terminates through `SystemExit`. The
hook can close inherited descriptors, but the library cannot repair arbitrary locks, thread state, buffered I/O, or
foreign-library state.

`reparent_process()` double-forks, creates a session, and closes standard streams. It is intentionally explicit and
POSIX-only. Identity is generated afterward, in the final process.

---

## 4. Pidfile identity

The open-file lock is the ownership primitive. The numeric PID is descriptive and operational, but PID existence alone
does not establish ownership and is subject to reuse.

The launcher acquires the lock before spawning so competing launchers cannot create duplicate workers. The locked open
file description is inherited or duplicated into the worker. The final worker rewrites the same inode using the
existing `Pidfile.write(suffix=...)` operation; it never publishes ownership through an atomic rename because replacing
the inode would separate the contents from the lock.

A current daemon pidfile has two JSONL-compatible lines:

1. a bare JSON integer containing the PID; and
2. compact JSON marshaled from `DaemonPidfileInfo`.

`DaemonPidfileInfo` contains:

- `pid`: duplicate, self-contained PID which must match line one;
- `instance_id`: a `uuid.UUID` unique to this launch and marshaled in canonical hyphenated form;
- `started_at`: an aware UTC datetime created after final reparenting;
- `format`: `omcore.daemon.pidfile`; and
- `format_version`: currently `1`.

The dataclass is deliberately dumb and round-trips through `omcore.lite.marshal`. Daemon-specific decoding accepts an
old one-line file as having no structured info, ignores unknown fields within a known format version, rejects unknown
formats/versions, and rejects disagreement between the two PIDs.

The record is immutable for the launch. It is not a heartbeat or mutable status channel. The file may retain old
contents after the process exits, so readers must only trust structured info while the lock is held by an owner.

The launch context makes the same info available to the target. `RpcService` uses its `instance_id` for the live
handshake. A directly run RPC service without a daemon pidfile creates its own instance ID.

---

## 5. Readiness and lazy launch

Readiness is an application predicate represented by `Wait`/`Waiter`. It is separate from PID ownership, socket path
existence, successful bind, and launch-channel success. Composite waits can be built with `SequentialWait`.
`ConnectWait` provides the weak but useful connect-and-disconnect probe, `HttpWait` can require an application health
endpoint's status and exact response body, and `RpcWait` performs a complete handshake and verifies protocol name,
version, and instance identity. New probes register through the same `waiter_for` dispatch rather than modifying
`Daemon`.

`LazyDaemon` requires both a pidfile and a readiness wait. Its call policy first attempts the caller's operation. It may
enter launch logic only when the operation raises an exception which the caller explicitly classifies as unavailable.
This distinction prevents an application error or an indeterminate outcome from silently causing a duplicate call.

Within one process, an ensure lock coalesces concurrent threads. Across processes, the pidfile lock elects a launcher.
While holding its local ensure lock, `LazyDaemon.ensure()` repeatedly:

1. checks real readiness;
2. checks whether the pidfile is locked;
3. attempts launch only when it is unlocked; and
4. sleeps for the configured bounded interval until readiness or timeout.

The operation is tried again only after readiness. Races with idle shutdown are expected: readiness can disappear
between the probe and the call, at which point an explicitly unavailable operation returns to the same ensure loop.

---

## 6. Runtime, activity, and shutdown

`ServiceRuntime` is a one-shot context with a shared synchronized state. Shutdown transitions only once. Its reason is
one of explicit request, idle expiry, or signal, accompanied by a monotonic request time and optional detail.

Activity acquisition and shutdown request are serialized by the same lock:

- acquisition before shutdown succeeds and increments the active count;
- acquisition after shutdown raises `ActivityRejectedError`;
- active work suppresses idle expiry;
- releasing the last activity starts a fresh full idle window; and
- a manual `touch()` refreshes the idle window while inactive.

The idle monitor is condition-driven and tickless. With no idle timeout configured, no idle thread is created. `SIGINT`
and `SIGTERM` request shutdown when runtime runs on the main thread and signal handling is enabled.

`RuntimeService` runs `_run_runtime`, then waits for accepted activity to become inactive. Failure to drain within
`drain_timeout_s` raises `DrainTimeoutError`. This gives a concrete boundary: shutdown rejects new work but honors work
which already obtained an activity lease, up to the configured deadline.

---

## 7. RPC protocol

RPC currently uses an `AF_UNIX`/`SOCK_STREAM` socket. Each message is encoded as UTF-8 JSON preceded by an unsigned
four-byte big-endian byte count. Frame size is checked before allocating or decoding, and JSON encoding rejects data
which cannot be represented by the configured bound.

`RpcServer` owns this transport, concurrent connection handling, and response replay independently of daemon services.
It is driven by `RpcServerRuntime`, the narrow interface for shutdown, drain timeout, and optional activity acquisition.
`SimpleRpcServerRuntime` supplies explicit shutdown for standalone use; `RpcService` is the adapter which maps
`ServiceRuntime` onto that interface.

Each connection carries:

1. a client hello containing protocol name and requested version;
2. a server hello containing protocol name, actual version, and instance ID;
3. at most one request; and
4. one result or error response.

Handshake-only probes do not acquire activity and therefore do not keep an idle service alive. A parsed request must
acquire runtime activity before handler execution. Once shutdown begins, the service sends an explicit unavailable
response instead of accepting the request.

The server accepts connections concurrently in tracked daemon threads. Shutdown closes the listener, waits for tracked
connections to drain, and closes their sockets on drain timeout. Socket cleanup compares device/inode identity before
unlinking so an old instance cannot remove a replacement's socket. Bind refuses to replace a non-socket path, probes an
existing socket for a live owner, and only removes a stale socket.

### Object interface facade

The object facade is an optional layer above method-and-parameters RPC. `@rpc_method` marks the methods which form an
interface's explicit remote allowlist. `RpcObjectHandler` binds calls against those interface signatures and invokes
the corresponding pre-resolved implementation methods; it never uses a request value in `getattr`. `RpcObjectProxy`
creates an implementation of the same interface and binds arguments locally before passing `args` and `kwargs` to an
arbitrary `RpcCaller`.

An optional namespace and per-method wire name let independently defined interfaces share a server method namespace.
Undecorated methods, properties, and arbitrary attributes remain local and unexposed. The facade is not a new serializer:
its values must still fit the bounded JSON protocol. The handler and proxy depend only on the RPC request/caller
interfaces, not on daemon launch or service runtime.

### Request identity and replay

A request is identified by `(client_id, request_id)` and includes its method and parameters. Within one service
instance, the response cache has these rules:

- the first request executes the handler and stores its result or remote error;
- a concurrent or later value-equivalent request with the same identity receives the stored response;
- reuse of the identity with different request data is a protocol error; and
- entries are never evicted during the instance lifetime.

The configured cache bound is fail-closed. Once full, new unique requests receive a cache-full remote error. Evicting
an old entry would permit a lost response to cause the same request identity to execute twice, so bounded memory is
preferred over weakening replay safety. Idle-exiting services naturally bound the cache lifetime.

### Outcome taxonomy

RPC distinguishes four outcomes which callers must not collapse:

| Outcome | Meaning | Automatic retry |
| --- | --- | --- |
| Result or `RpcRemoteError` | The instance executed the request and returned an authoritative response. | No. |
| `RpcUnavailableError` | The request is known not to have been accepted/executed. | Safe. |
| Lost response from the same instance | The request may have executed; replay uses the identical request ID and expected instance ID. | Safe only as constrained replay. |
| `RpcCallIndeterminateError` with a different instance | The old request may have executed, but its cache is gone and a replacement answered. | Never automatic. |

`LazyRpcClient` creates a request once. Ordinary unavailability enters lazy ensure/relaunch. If sending may have
succeeded but the response is lost, it records the original instance and retries the identical request only against
that instance. Encountering another instance raises `RpcCallIndeterminateError` without executing the request there.

This is not globally exactly-once RPC. A durable external effect and the in-memory response cache do not participate in
one transaction, and process loss destroys the cache. Applications requiring stronger semantics need their own durable
idempotency key or transaction boundary.

---

## 8. Logging and descriptors

The library does not impose a global logging configuration. A multiprocessing entrypoint can configure logging before
the launch function; file handlers then survive reparenting while standard streams are redirected. The LLM demo uses
this pattern.

Descriptor ownership is explicit:

- the launcher passes only designated descriptors through multiprocessing spawn;
- pidfile and startup-report descriptors are included automatically when needed;
- raw fork inherits all descriptors, by definition; and
- `ForkSpawning.post_fork` is the application hook for closing or repairing inherited resources.

No hook can make an arbitrary multithreaded process universally fork-safe. Raw fork remains an expert-mode operation.

---

## 9. Security boundary

This is local IPC, not a sandbox. Pidfiles are created mode `0600`, RPC sockets default to mode `0600`, and the service
refuses to overwrite a non-socket at its configured endpoint. Callers remain responsible for choosing and protecting
the containing directory, avoiding symlink-hostile shared locations, validating RPC parameters, and deciding whether
local same-user callers are trusted.

JSON is the only RPC payload format today. Pickle must not be enabled merely because a pidfile reports a package
version or revision. A future pickle capability must compare an authoritative compatibility identity during the live
handshake, fail closed on mismatch, and require an explicit development override.

---

## 10. Testing contract

Behavior at OS boundaries is covered by integration tests without mocks or patches. Tests use real `flock` locks,
Unix sockets, HTTP servers, threads, multiprocessing spawn/fork, raw fork, double-fork reparenting, signals, exec
replacement, concurrent launchers, response loss, and process replacement. A shared-state integration test verifies
that `ThreadSpawning` truly remains in-process, while a standalone server test verifies that the RPC core runs without
daemon or service-runtime adapters.

The LLM demo test invokes the real argparse CLI twice. It verifies that the first process starts a detached service,
the second connects to the same PID and instance ID, both calls traverse RPC, and signal shutdown releases the pidfile.

Future changes to process ownership, pidfile publication, readiness, retry classification, or graceful drain should be
specified here and tested at the same real boundary.
