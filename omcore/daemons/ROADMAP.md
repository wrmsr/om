# Daemon Roadmap

This roadmap describes likely directions for `omcore.daemons`, not a compatibility promise or release schedule. The
package should remain a toolbox whose pieces can be assembled independently. A convenient default composition must not
turn into a mandatory runtime, transport, protocol, or process model.

See [README.md](README.md) for current usage and [DESIGN.md](DESIGN.md) for behavior which is already contractual.

## Design constraints

Future work should preserve these boundaries:

- launching, ownership, readiness, activity, and shutdown are distinct concerns;
- thread, multiprocessing, raw-fork, reparented, exec, and externally managed workers remain explicit choices;
- a daemon target may be an in-process callable, an internal server, an unmodifiable third-party server, or a
  supervisor for an external child process;
- readiness is pluggable and does not imply use of the same I/O stack as the target;
- `omcore.io.pipelines` and `omcore.http.pipelines` are the preferred provided serving stacks, not dependencies of the
  basic daemon machinery;
- RPC remains independently usable without daemon launching or `ServiceRuntime`; and
- interfaces and small adapters should connect implementations instead of central classes accumulating policy.

## 1. Pipeline-native RPC

Rework RPC around a sans-I/O protocol core and `omcore.io.pipelines` message flow. Framing, JSON protocol state,
request identity, replay, and error classification should operate on messages rather than directly on blocking
sockets. Connected-stream reads, writes, cancellation, and backpressure belong in pipeline drivers. Listener ownership,
acceptance, concurrency, and connection-group draining belong in separate sync, asyncio, or fdio server hosts.

The same protocol and handler implementation should be driveable by synchronous and asynchronous drivers with no
semantic fork in the RPC core. Unix-domain sockets should remain supported while endpoint and transport interfaces
make TCP and other byte-stream transports possible. Existing synchronous `RpcClient` and daemon `RpcService` APIs
should be retained initially as adapters over the pipeline implementation so migration is incremental and testable.
Pipeline specifications must be built afresh per connection because protocol handlers carry connection-local state.

Acceptance should include:

- protocol tests which run entirely without sockets;
- the same conversation corpus exercised through sync and async pipeline drivers;
- real Unix-socket integration tests retaining request replay and indeterminate-outcome behavior;
- bounded inbound and outbound buffering with explicit backpressure behavior;
- clean cancellation, peer disconnect, shutdown, and drain semantics; and
- no import dependency from the RPC core to daemon lifecycle modules.

### Planned implementation slices

The RPC rewrite should proceed without changing `omcore.io.pipelines` or `omcore.http.pipelines`:

1. **Complete:** Add typed wire messages, a bounded length-frame codec, a JSON message codec, and client/server session handlers
   under `omcore.daemons.rpc`. Prove them first with the deterministic pure driver and split-input transcripts.
2. **Complete:** Add a nonblocking, server-instance-wide response registry. Connection hosts may wait synchronously or asynchronously
   for an in-progress duplicate without the registry itself depending on an event loop.
3. **Complete:** Reimplement the existing synchronous `RpcClient` and `RpcServer` APIs over the sync socket pipeline driver. Retain
   the current Unix-socket wire protocol, hardened bind/unlink behavior, lazy retry semantics, and daemon adapters.
4. **Complete:** Add asyncio client and server hosts using the same pipeline specifications and protocol/session handlers. Handler
   execution policy must be explicit so a synchronous handler is not accidentally run on the event-loop thread.
5. **Complete:** Add an fdio server host as a separate connection-group implementation over the same specs. If this exposes more
   than two defects in the existing fdio pipeline driver, or requires more than four total lines of fixes outside
   `omcore.daemons`, preserve the attempted regression tests as expected failures, document the obstruction, and
   continue the sync/async work rather than expanding this project into an fdio repair effort.
6. **Complete:** Run old-client/new-server and new-client/old-server interoperability tests. The blocking helpers remain
   as a small compatibility API and independent wire-format oracle.

The initial hosts may remain RPC-specific. They should record what listener ownership, wakeup, connection tracking,
driver construction, dispatch, graceful drain, and abort behavior a future general-purpose pipeline server actually
needs, rather than prematurely placing an unproven abstraction in `omcore.io.pipelines`.

## 2. First-class non-RPC services

**Initial slice complete.** The package now provides a runtime-managed HTTP composition using
`omcore.http.pipelines`. Its sans-I/O one-request core is driveable by pure, synchronous socket, and asyncio stream
drivers. Separate sync and asyncio hosts depend on `HttpServerRuntime`; thin `PipelineHttpService` and
`AsyncioPipelineHttpService` adapters supply `ServiceRuntime` lifecycle. Async handler policy is explicit, with a
threaded adapter for blocking handlers.

The composition demonstrates request activity leases, application-level readiness, idle linger, graceful rejection
of new work, and bounded draining without making HTTP part of `Daemon` itself. A dedicated health route bypasses
application dispatch and activity acquisition, so repeated probes do not extend the service's life. Accepted
application activity is held until response output drains.

The generic path must remain equally valid: `FnTarget`, `ExecTarget`, or a custom `Service` can run another web stack,
an embedded third-party server, or a supervisor which starts and monitors an external process such as a `llama.cpp`
server. `HttpWait` should continue to probe those services without assuming how they are implemented. Pipeline-backed
HTTP readiness may later be added as an alternative waiter, not as a replacement for the dependency-light probe.

Integration coverage should include:

- **Complete:** a thread-backed HTTP service which shares in-process state, for both sync and asyncio hosts;
- **Complete:** a multiprocessing HTTP service started lazily and restarted with a new identity after idle exit;
- **Complete:** a dedicated health endpoint whose status differs from mere TCP acceptance and does not extend idle;
- **Complete:** long-running requests extending activity and accepted requests draining during shutdown; and
- **Complete:** an independently implemented standard-library HTTP target probed through the same readiness interface.

Likely follow-ons are streaming request/response sessions, keep-alive, an fdio host if useful, richer error-response
policy, and an explicit lazy HTTP client facade which classifies transport unavailability at the actual call boundary.

## 3. RPC endpoints and transports

Separate RPC protocol state from byte-stream connection establishment. Unix sockets are the local default; TCP should
be a first-class endpoint for services managed elsewhere or on remote systems. Security policy must remain explicit:
local socket permissions are not authentication for TCP, and adding TCP must not silently imply that plaintext remote
RPC is safe.

Likely follow-on implementations include TLS-wrapped TCP and user-supplied connected streams. Endpoint configuration,
connection factories, listener factories, and driver selection should be independently replaceable. Protocol
handshake behavior must remain identical across transports.

### Planned implementation slices

1. **Complete:** Add dumb `UnixRpcEndpoint` and `TcpRpcEndpoint` values. Preserve `socket_path=` as the Unix
   compatibility spelling in existing client, server, service, wait, and lazy compositions.
2. **Complete:** Extract injectable synchronous and asyncio transport interfaces. Listener implementations own bind cleanup and
   expose the resolved bound endpoint, including the kernel-assigned port when configured with TCP port zero.
3. **Complete:** Move hardened Unix stale-socket detection, permission setting, and inode-safe unlinking into the default transport
   implementation. Use the same synchronous listener boundary from the fdio host rather than retaining a third Unix
   bind implementation.
4. **Complete:** Add default TCP connection and listener implementations for synchronous and asyncio hosts. The default is a plain
   byte stream with no transport authentication or encryption; selecting a TCP endpoint must not be documented as a
   security boundary.
5. **Complete:** Exercise all sync/async client-server TCP combinations with real loopback sockets, plus lifecycle drain, protocol
   identity, Unix compatibility, and import-dependency tests. No RPC wire messages or retry classifications should
   differ by endpoint.

TLS should follow as a transport implementation, not a protocol fork. User-supplied connected streams may require a
separate driver factory once a concrete use case establishes how stream ownership and closure should compose.

## 4. Handler composition and object interfaces

Add a routing layer which can combine ordinary `RpcHandler` implementations and multiple `RpcObjectHandler`
interfaces without request-controlled attribute access. Namespaces, duplicate-name detection, middleware-like handler
wrappers, and method metadata should compose without requiring inheritance from one server class.

Evolve the object facade only where it preserves the explicit JSON boundary. Useful additions may include configured
per-call policy, typed method metadata, and generated static typing support. Properties, arbitrary attribute access,
and implicit exposure of undecorated methods should remain out of scope.

## 5. Capability and code identity negotiation

Extend the live handshake with explicit capabilities and an authoritative code compatibility identity. Compatibility
must be negotiated with the running peer, not inferred from a stale pidfile. The identity format should account for
the executable environment and relevant source or package revision while allowing a clearly marked local-development
mode.

Only after this exists should an optional pickle codec be considered. It must be opt-in, fail closed unless both peers
report an exact compatible identity, retain bounded framing, and never be enabled merely because a peer is local or
shares a UID. JSON remains the interoperable default.

## 6. External-child supervision

**Initial slice complete.** The package provides composable process configuration and factory interfaces, a
runtime-driven supervisor, and a service adapter for the common case where the daemon process owns and babysits
another executable. This is intentionally smaller than a general init system, but covers startup observation, signal
forwarding, graceful termination followed by a configured kill deadline, child reaping, logging/descriptor policy,
and propagation of unexpected child exit.

Readiness should remain orthogonal: callers may use `ConnectWait`, `HttpWait`, a process-specific probe, or a sequence
of checks. This path is important for tools such as model servers whose HTTP implementation is outside this repository
and cannot be adapted to internal pipeline APIs.

### Planned implementation slices

1. **Complete:** Separate an immutable child command/descriptor specification, an injectable process factory, and
   termination policy from the runtime coordinator. The default factory should use `subprocess.Popen`, inherit no
   accidental input, expose explicit inherited descriptors, and support inherited, discarded, redirected, and
   append-or-truncate file output.
2. **Complete:** Have the coordinator observe `Popen` startup errors, reap the direct child deterministically, treat any
   exit before a runtime shutdown request as a service failure, and request runtime shutdown so sibling lifecycle
   machinery sees the loss.
3. **Complete:** Forward signal-originated shutdown using the original signal, use a configured signal for requested or
   idle shutdown, escalate after a grace deadline, and report the pathological case where the child remains unreaped
   after the kill deadline. Process-group signaling must be explicit and paired with a new child session.
4. **Complete:** Supply a thin `RuntimeService` adapter without coupling readiness to process ownership. Prove
   composition with a real external HTTP child, `HttpWait`, a daemon pidfile for the supervisor, and graceful shutdown
   through the daemon.
5. **Complete:** Document the opaque-child activity boundary: direct traffic to an external server cannot automatically
   renew a `ServiceRuntime` idle lease. Fixed linger, explicit activity notification, a proxy, or child-native idle
   behavior remain separate policies rather than hidden inference in the supervisor.

## 7. Operations and observability

Expose read-only status and inspection building blocks around locked pidfile identity, launch state, readiness,
shutdown reason, and configured endpoints. A small CLI may compose these into inspect, wait, stop, and log-location
commands, while programmatic APIs remain primary.

Logging should stay application-configurable. Future helpers can provide structured lifecycle events and convenient
file logging without installing global handlers implicitly.

### Planned implementation slices

1. **Complete:** Add a read-only inspection snapshot whose lifecycle state distinguishes an absent pidfile, an unlocked
   stale file, a locked owner, and a locked owner whose optional readiness probe succeeds. Preserve numeric and
   structured identity when parseable, but report record and readiness errors orthogonally instead of confusing them
   with ownership.
2. **Complete:** Exercise absent, starting, ready, exited, stale, malformed, and replacement-instance transitions
   against real locks, processes, pidfiles, and health endpoints. Each inspection should create a fresh waiter so
   stateful wait adapters do not leak success between snapshots.
3. **Complete:** Add a wait-for-stopped operation based on lock release and inode/instance observation rather than PID
   disappearance. Report path or identity replacement separately without claiming that an unlinked original process
   exited, and retain initial/last snapshots on timeout.
4. Define the race contract for signaling before adding a stop helper. Linux pidfds can close the PID-reuse window,
   while the portable POSIX fallback must expose its weaker guarantees rather than treating UUID metadata as an OS
   process handle.
5. Build a small CLI over the programmatic inspect, wait, and stop APIs after those contracts settle. Endpoint and log
   reporting should consume explicit application metadata rather than growing mutable fields in the pidfile by default.

## 8. Hardening and portability

Continue real integration testing across Linux, Darwin, supported Python versions, and free-threaded Python. Add race
tests for simultaneous launch, shutdown versus activity acquisition, connection cancellation, partial frames,
backpressure, and replacement instances. Keep raw fork explicitly expert-only and preserve post-fork repair hooks.

Native Windows support is not currently a goal for POSIX pidfiles, Unix sockets, `fork`, or signal behavior. Sans-I/O
protocol components and transport-independent interfaces should nevertheless avoid unnecessary POSIX dependencies.
