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
- ownership, bounded shutdown, and deterministic reaping of one external child process;
- byte-stream RPC with explicit request identity and honest retry outcomes; and
- small layers which can be used independently.

Non-goals currently include:

- replacing a full external supervisor when restart policy, privilege changes, resource isolation, or machine boot
  integration is required;
- hiding the hazards of `fork(2)`;
- making inherited application state safe automatically;
- built-in transport encryption or user authentication;
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
      | byte stream                  v
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

- `rpc.pipelines` implements runtime-neutral framing, JSON translation, and connection sessions;
- `rpc.registry` and `rpc.dispatch` implement lifecycle-independent identity, replay, and synchronous dispatch;
- `rpc.endpoints` and `rpc.transports` describe and establish byte streams without importing daemon lifecycle;
- `rpc.client`, `rpc.server`, `rpc.asyncio`, `rpc.fdio`, and `rpc.objects` are lifecycle-independent RPC pieces;
- `rpc.services` adapts `RpcServer` to `ServiceRuntime`;
- `rpc.lazy` composes `RpcClient` with `LazyDaemon`; and
- `rpc.waiting` adapts an RPC handshake to the general readiness interface.

`RpcServer` and `FdioRpcServer` depend on the small `RpcServerRuntime` interface rather than on `ServiceRuntime`.
Consequently they can run under a thread, a different supervisor, or an eventual remote-host runtime.
`AsyncioRpcServer` owns its lifecycle directly and drains its tracked connection tasks on `close()`. In the other
direction, daemon code does not require RPC: targets can be ordinary functions, in-process services, HTTP servers, or
other protocols.

### HTTP dependency boundary

Pipeline HTTP follows the same interface-plus-adapter split. `http.pipelines` contains a sans-I/O one-request server
session. `http.server` and `http.asyncio` own sync and asyncio TCP hosting against the narrow `HttpServerRuntime`
interface. Only `http.services` adapts those hosts to `ServiceRuntime`.

This is a provided composition, not the daemon transport. General launch, target, runtime, lazy, and wait modules do
not import it. `HttpWait` intentionally remains a standard-library probe and works identically with the provided
pipeline hosts, another Python web stack, an unmodifiable embedded server, or an externally supervised HTTP process.

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

## 7. External child ownership

`children` is an interface-plus-adapter composition for one directly owned external process:

- `ChildProcessConfig` describes command, working directory, environment, standard streams, explicitly passed file
  descriptors, and session creation;
- `ChildProcessFactory` creates a controllable and waitable `ChildProcess`, with `PopenChildProcessFactory` as the
  default implementation;
- `ChildTerminationConfig` supplies graceful signal, signal-forwarding, process-group, grace-deadline, and kill-deadline
  policy;
- `ChildProcessSupervisor` coordinates those pieces against `ServiceRuntime`; and
- `ChildProcessService` is the only adapter which makes that coordinator a configured daemon service.

Process creation remains distinct from daemon launch readiness. `Popen` reports fork/exec or platform creation errors
to the supervisor, but `Launcher` has already crossed its generic target-run boundary by then. A daemon caller which
needs usable startup confirmation configures `ConnectWait`, `HttpWait`, or another application probe. No health check
is embedded in process ownership.

The supervisor starts one waiter which exclusively calls `wait()` and therefore reaps the direct child. A second
coordinator waits for runtime shutdown. On requested or idle shutdown it sends the configured graceful signal. On
signal shutdown it forwards the original signal by default. If the child does not exit before `grace_timeout_s`, the
coordinator sends `SIGKILL`; failure to observe exit by `kill_timeout_s` raises `ChildProcessStopTimeoutError`. A
`None` deadline explicitly means an unbounded wait at that stage.

Any observed child exit for which no shutdown request existed at reap time is unexpected, including status zero. The
supervisor requests runtime shutdown with diagnostic detail and raises `ChildProcessExitedError`; its attached
`ChildProcessResult` retains PID, return code, absence of the prior shutdown request, and escalation state. An exit
after shutdown returns the same result normally. This distinction propagates external server loss without treating an
ordinary signal-driven stop as failure.

Process-group signaling is allowed only when child session creation is also selected, making the child PID the known
group ID and avoiding accidental signaling of the supervisor's own group. It delivers policy to descendants, but the
supervisor can reap only its direct child; that child remains responsible for its children. The implementation is not
an init system: it has no restart loop, dependency ordering, privilege policy, resource containment, or orphan
adoption. If a process remains unobservable after the kill deadline, the timeout reports that ownership could not be
completed rather than claiming success.

The default factory keeps `close_fds` enabled. Standard input defaults to `/dev/null`; stdout and stderr can inherit,
use `/dev/null`, share stdout, or use supervisor-owned binary files in append or truncate mode. `pass_fds` is explicit.
Owned files remain open through child lifetime and are closed by the waiter after `wait()`. This policy configures child
descriptors, not Python logging and not global handlers.

Finally, direct application traffic to an opaque child does not pass through the supervisor and cannot automatically
acquire or touch a runtime activity lease. Readiness probes likewise remain health observations, not activity. A
traffic-aware idle lifetime requires a proxy, explicit notification, or child-native behavior; configuring a runtime
idle timeout alone creates a fixed supervisor-side deadline.

---

## 8. Pipeline HTTP

`pipeline_http_server_spec()` is built afresh for every connection because the request/response session handler owns
connection-local state. Inbound bytes pass through the shared HTTP request decoder and bounded full-request
aggregator. The host receives a typed `HttpServerRequest`, supplies a typed `HttpServerSendResponse`, and the shared
HTTP encoder writes the response. The pure pipeline driver can exercise this entire protocol without a socket.

The first HTTP session contract is intentionally small:

- one full request and one full response per connection;
- a configurable maximum aggregated request-body size;
- response output is flushed before the connection is finalized;
- malformed, aborted, or oversized input fails the connection; and
- keep-alive, upgrades, and streaming bodies are not yet supported.

`PipelineHttpServer` owns a TCP listener and tracked connection threads; `AsyncioPipelineHttpServer` owns an asyncio
listener and tracked connection tasks. Both use `HttpServerRuntime` for shutdown state, bounded draining, and optional
activity acceptance. `SimpleHttpServerRuntime` supports standalone/manual ownership. The asyncio host requires an
async handler, while `ThreadedAsyncHttpHandler` makes off-loop execution of a synchronous handler explicit.

Health routing is host policy layered above the protocol session. A matching `HttpHealthConfig` route bypasses the
application handler and does not acquire activity, so readiness polling cannot postpone idle shutdown. Healthy probes
return `200`; a probe handled after shutdown begins returns `503`. Each non-health request must acquire activity before
application dispatch. Rejection returns `503` without invoking the handler. An accepted lease is retained through
handler execution and response output drain, so accepted work both survives an idle deadline and participates in
graceful connection draining. Synchronous handler failures become a bounded `500` response rather than terminating the
host; the asyncio dispatcher applies the same policy while preserving task cancellation.

`PipelineHttpService` and `AsyncioPipelineHttpService` are the only adapters to `ServiceRuntime`. The rest of the HTTP
subpackage remains usable without daemon launch, pidfiles, idle policy, or `ServiceDaemon`. Conversely, daemon targets
and `HttpWait` remain fully usable without importing this serving stack.

---

## 9. RPC protocol

RPC runs over a connected byte stream supplied by the endpoint/transport layer. The default implementations support
Unix-domain stream sockets and plaintext TCP. Each message is encoded as UTF-8 JSON preceded by an unsigned four-byte
big-endian byte count. Frame size is checked as soon as its header is available, and inbound and outbound JSON are
validated against the configured bound.

The protocol core is a sans-I/O `IoPipeline.Spec`, freshly constructed for each connection because its handlers own
session-local state. Inbound bytes pass through a bounded frame decoder, a typed JSON wire codec, and a one-request
client or server session. Outbound application commands traverse those handlers in reverse. Connected-stream drivers
own reads, writes, flush completion, half-close observation, output watermarks, and graceful final output. They do not
own listening sockets or application concurrency.

### Endpoints and transports

`UnixRpcEndpoint` and `TcpRpcEndpoint` are behavior-free values. The latter permits server port zero; each server host
publishes the resolved `bound_endpoint` after bind so callers can discover the kernel-selected port. The legacy
`socket_path=` configuration form resolves to `UnixRpcEndpoint` and remains valid for clients, servers, `RpcService`,
`RpcWait`, and lazy compositions.

`SyncRpcTransport` and `AsyncioRpcTransport` separate connection/listener creation from the RPC hosts. Their listener
interfaces own endpoint cleanup and report the resolved endpoint. Default implementations create Unix or TCP sockets;
custom implementations are injected when constructing a client or server. The fdio host consumes the synchronous
listener interface because its poller needs a raw selectable socket, eliminating a separate bind/cleanup policy.

Unix listeners retain the hardened ownership rules: bind refuses to replace a non-socket path, probes an existing
socket before treating it as stale, applies the configured mode, and only unlinks the inode created by that listener.
TCP listeners have no filesystem artifact. Transport selection does not change any RPC message or call-outcome rule.

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

The synchronous server accepts connections concurrently in tracked daemon threads and drives each through the sync
socket pipeline driver. The asyncio host tracks one task and pipeline driver per stream and requires an async handler;
`ThreadedAsyncRpcHandler` is the explicit adapter for synchronous work. The fdio host dispatches driver-visible RPC
events on its single poll loop and retains a runtime activity lease until queued response output has drained. Shutdown
closes the listener and drains tracked connections up to the host's configured deadline.

Unix endpoints use inode-safe socket cleanup: an old instance compares device/inode identity before unlinking and
therefore cannot remove a replacement's socket. Bind refuses to replace a non-socket path, probes an existing socket
for a live owner, and only removes a stale socket.

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
instance, the runtime-neutral response registry has these rules:

- the first request executes the handler and stores its result or remote error;
- a concurrent or later value-equivalent request with the same identity receives the stored response;
- reuse of the identity with different request data is a protocol error; and
- entries are never evicted during the instance lifetime.

The configured cache bound is fail-closed. Once full, new unique requests receive a cache-full remote error. Evicting
an old entry would permit a lost response to cause the same request identity to execute twice, so bounded memory is
preferred over weakening replay safety. Idle-exiting services naturally bound the cache lifetime.

The registry returns execute, pending, replay, or reject claims. It does not run handlers and does not choose a waiting
runtime. Pending entries expose both a condition-backed synchronous wait and completion callbacks; the asyncio
dispatcher turns the latter into a loop-owned future without blocking the event-loop thread. A response is JSON- and
frame-validated before it becomes the authoritative cached value.

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

## 10. Logging and descriptors

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

## 11. Security boundary

This is IPC, not a sandbox. Pidfiles are created mode `0600`, Unix RPC sockets default to mode `0600`, and the default
transport refuses to overwrite a non-socket at a Unix endpoint. Callers remain responsible for choosing and
protecting the containing directory, avoiding symlink-hostile shared locations, validating RPC parameters, and
deciding whether local same-user callers are trusted.

The default TCP transport is plaintext and unauthenticated. Loopback is appropriate for tests and trusted local
compositions, but the library does not restrict the bind address. Selecting a non-loopback endpoint exposes the RPC
handler to that network; authorization, TLS, firewalling, and credential policy belong to the embedding application or
a future explicit secure transport. RPC instance identity detects service replacement but is not peer authentication.

JSON is the only RPC payload format today. Pickle must not be enabled merely because a pidfile reports a package
version or revision. A future pickle capability must compare an authoritative compatibility identity during the live
handshake, fail closed on mismatch, and require an explicit development override.

---

## 12. Testing contract

Behavior at OS boundaries is covered by integration tests without mocks or patches. Tests use real `flock` locks,
Unix sockets, HTTP servers, threads, multiprocessing spawn/fork, raw fork, double-fork reparenting, signals, exec
replacement, concurrent launchers, response loss, and process replacement. A shared-state integration test verifies
that `ThreadSpawning` truly remains in-process. HTTP coverage includes pure split-byte protocol transcripts, sync and
asyncio hosts, activity-aware drain, health probes which do not extend idle life, lazy multiprocessing launch, and an
independent standard-library server using the same readiness abstraction. RPC coverage includes pure split-byte
protocol transcripts, every sync/async client-server pairing over loopback TCP, resolved ephemeral ports, TCP drain,
explicit threaded asyncio handling, fdio over Unix and TCP, blocking-wire compatibility, and standalone servers
without daemon adapters. External-child coverage uses actual fork/exec, file descriptors, output files, process groups,
signals, kill escalation, unexpected exits, and an HTTP process composed with `HttpWait` and a supervisor pidfile.

The LLM demo test invokes the real argparse CLI twice. It verifies that the first process starts a detached service,
the second connects to the same PID and instance ID, both calls traverse RPC, and signal shutdown releases the pidfile.

Future changes to process ownership, pidfile publication, readiness, retry classification, or graceful drain should be
specified here and tested at the same real boundary.
