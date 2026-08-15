# Daemons

`omcore.daemons` is a POSIX toolbox for background work which belongs to an application rather than to an external
service manager. It can start a worker on first use, coordinate competing launchers with a locked pidfile, wait for
real readiness, keep the worker alive while it is active, let it linger while idle, and shut it down cleanly.

It deliberately includes process machinery which is uncommon in application libraries: multiprocessing spawn,
multiprocessing fork, raw `fork(2)`, double-fork reparenting, inherited file descriptors, and `exec`. These are explicit
tools with different safety and ownership contracts, not interchangeable implementation details.

See [DESIGN.md](DESIGN.md) for the lifecycle, identity, retry, and shutdown contracts.

## Motivating example

The mock LLM demo provides a small end-to-end example:

```shell
./python -m omcore.daemons.tests.demos.llm
```

```text
Mock LLM REPL. Enter /quit to exit.
you> background workers
llm> Fascintating! Tell me more about background workers
you> /quit
```

The first message starts a detached `LlmService` if necessary. A second CLI process using the same state directory
connects to the existing service. Each request sleeps for one second, the worker lingers for ten idle seconds by
default, and then it exits.

Messages can also be sent non-interactively:

```shell
./python -m omcore.daemons.tests.demos.llm --message 'Unix sockets'
./python -m omcore.daemons.tests.demos.llm --message 'same worker, probably!'
```

Use `--linger`, `--timeout`, and `--state-dir` to change its behavior. The default state directory is
`${TMPDIR}/omcore-daemons-llm-${UID}` and contains:

- `llm.pid`: the locked process identity record;
- `llm.sock`: the local RPC socket while the service is running; and
- `llm.log`: worker logs, which remain useful after detached stdio has been closed.

The complete implementation is [tests/demos/llm.py](tests/demos/llm.py).

## Layers

The package is intentionally composable rather than presenting one mandatory daemon class.

| Layer | Main types | Responsibility |
| --- | --- | --- |
| Target | `Target`, `FnTarget`, `NameTarget`, `ExecTarget`, `ServiceTarget` | Describe what the worker runs. |
| Spawning | `ThreadSpawning`, `MultiprocessingSpawning`, `ForkSpawning` | Choose the execution and process boundary. |
| Launching | `Launcher`, `Daemon` | Own startup monitoring, pidfile coordination, optional reparenting, and readiness. |
| Service | `Service`, `RuntimeService`, `ServiceDaemon` | Package configured long-running behavior as a target. |
| Runtime | `ServiceRuntime`, `Activity`, `ShutdownController` | Track activity, idle lifetime, signals, and graceful drain. |
| Child supervision | `ChildProcessSupervisor`, `ChildProcessService` | Own, stop, escalate, and reap one external executable. |
| Inspection | `DaemonInspector`, `DaemonInspection` | Observe pidfile ownership, identity, and optional readiness without signaling. |
| Lazy access | `LazyDaemon` | Connect first; coordinate launch and relaunch only when explicitly unavailable. |
| Readiness | `ConnectWait`, `HttpWait`, `RpcWait` | Supply pluggable transport- or application-level health checks. |
| HTTP core | `pipeline_http_server_spec`, `PipelineHttpServer`, `AsyncioPipelineHttpServer` | Serve bounded HTTP requests through runtime-neutral pipelines and sync or asyncio hosts. |
| HTTP adapters | `PipelineHttpService`, `AsyncioPipelineHttpService` | Compose the optional HTTP hosts with activity-aware service lifetime. |
| RPC endpoint | `UnixRpcEndpoint`, `TcpRpcEndpoint`, sync/async transport interfaces | Choose and establish a byte-stream boundary independently of RPC messages. |
| RPC core | `RpcServer`, `AsyncioRpcServer`, `FdioRpcServer`, `RpcClient`, `AsyncioRpcClient` | Provide pipeline-backed JSON calls independently of daemon lifecycle. |
| RPC facade | `RpcObjectHandler`, `RpcObjectProxy` | Add an opt-in typed-object interface above any `RpcCaller`. |
| RPC adapters | `RpcService`, `LazyRpcClient`, `RpcWait` | Compose RPC with service runtime, lazy daemon launch, and readiness. |

A typical lazy RPC application assembles these pieces as follows:

```text
LazyRpcClient
    -> RpcClient + LazyDaemon
        -> Daemon
            -> Launcher
                -> spawning backend
                -> locked pidfile
                -> ServiceTarget(RpcService)
```

`ServiceDaemon` is a convenience value which ties a `Service` or service config to a `Daemon` or daemon config. It
does not introduce another runtime layer.

The RPC implementation is a subpackage rather than a single lifecycle component. `rpc.pipelines` contains the
runtime-neutral framing, JSON, and session state machines; `rpc.registry` owns request identity without choosing how a
waiter blocks; and sync, asyncio, and fdio hosts drive fresh per-connection specifications. These pieces do not depend
on daemon launching. `rpc.services`, `rpc.lazy`, and `rpc.waiting` are explicit composition adapters. A daemon may serve
HTTP or run entirely in-process, and an RPC server may be run by a thread, a remote host's supervisor, or any other
lifecycle owner.

## Process choices

### Multiprocessing spawn

`MultiprocessingSpawning(StartMethod.SPAWN)` is the normal choice for a clean Python child. Targets, service configs,
handlers, entrypoints, and their reachable state must be picklable.

### Multiprocessing fork

`MultiprocessingSpawning(StartMethod.FORK)` avoids spawn reconstruction but inherits the parent's interpreter state.
It should only be used when that inheritance is understood and safe.

### Raw fork

`ForkSpawning` is the sharpest tool. The child inherits memory, locks, threads' abandoned state, signal dispositions,
and every open descriptor not explicitly closed. Its `post_fork` hook runs in the child before the target and can close
or repair inherited resources. Choosing raw fork means accepting responsibility for the remaining process state.

### Thread

`ThreadSpawning` is useful when process isolation is unnecessary. It shares the PID, address space, descriptors, and
failure domain with its caller, and cannot outlive the containing process.

### Reparenting

`Daemon.Config(reparent_process=True)` performs a traditional double fork in the spawned worker, calls `setsid()`, and
redirects standard streams to `/dev/null`. The pidfile is written only in the final process, so its PID and instance ID
describe the process which actually owns the service. Configure durable logging before entering the target when using
this mode; the LLM demo does so in its multiprocessing entrypoint.

## Pidfiles and identity

The pidfile lock, not a PID lookup, is the single-instance authority. A launcher acquires the lock before spawning and
passes the same open file description into the worker. The final worker writes:

```jsonl
54821
{"pid":54821,"instance_id":"019c4c5e-8654-7f8f-8d8d-706715fd1d08","started_at":"2026-08-10T22:45:12.123456+00:00","format":"omcore.daemon.pidfile","format_version":1}
```

The first line remains a bare integer for existing `Pidfile` APIs and Unix tooling. The second line is compact JSON
produced from the `omcore.lite.marshal`-compatible `DaemonPidfileInfo` dataclass. Its duplicate PID must agree with the
first line. Old one-line pidfiles remain readable.

The file is not a heartbeat. Its record is authoritative only while the file is locked; stale contents may remain
after exit. Each successful launch receives a new `uuid.UUID` `instance_id`, and an RPC service launched under that
daemon exposes the same UUID in its protocol handshake.

## Inspection

`DaemonInspector` takes a pidfile path and an optional `Wait`, and returns a read-only `DaemonInspection` snapshot.
`Daemon.inspect()` is the convenience form using its configured pidfile and readiness probe. Lifecycle state follows
the ownership primitives rather than guessing from process existence:

| State | Meaning |
| --- | --- |
| `ABSENT` | The configured pidfile path did not exist. |
| `STALE` | The pidfile existed but its exclusive lock was available. Old contents are descriptive only. |
| `RUNNING` | Another owner held the lock; readiness was absent, false, or failed. |
| `READY` | Another owner held the lock and a fresh readiness probe succeeded. |

The snapshot includes the opened pidfile's device/inode pair, recoverable numeric PID, structured
`DaemonPidfileInfo`, and separate pidfile/readiness error strings. A locked empty pidfile is a legitimate startup
transition and remains `RUNNING`; malformed contents do not disprove lock ownership. Conversely, a perfectly valid
record in an unlocked file remains `STALE`. Readiness is never probed for absent or stale files, and each inspection
constructs a fresh waiter so a stateful `SequentialWait` cannot retain progress across snapshots.

Inspection compares the opened inode with the path after reading and retries replacement races. Like every status
snapshot, its result can become outdated immediately after return. It does not signal a PID, rewrite the pidfile, or
claim that UUID metadata closes the OS-level PID-reuse race.

`wait_daemon_stopped()` and `Daemon.wait_stopped()` turn an inspection into an identity-aware lifecycle wait. The
waiter opens and retains the expected pidfile inode, then polls its advisory lock. Its typed result is:

- `ALREADY_STOPPED` when the initial snapshot had no running owner;
- `STOPPED` only after the waiter itself acquires the original inode's exclusive lock; or
- `REPLACED` when the path points to another inode, or a different PID/structured instance takes ownership of the same
  inode before lock release is observed.

`REPLACED` is intentionally not reported as stopped: the original process may still be running with an unlinked
pidfile while another owner occupies the configured path. `DaemonWaitStoppedTimeoutError` retains the initial and last
snapshots. Legacy one-line records can use inode and PID comparison, but lack the UUID's stronger semantic identity.
This operation performs no signaling and does not run readiness probes.

## Lazy service behavior

`LazyDaemon` requires both a pidfile and a readiness probe. On a call it first attempts the real operation. Only an
exception classified as explicitly unavailable permits launch or relaunch. It then:

1. serializes local ensure attempts;
2. checks readiness again;
3. launches only if the pidfile is unlocked; and
4. waits for the configured readiness probe.

The pidfile lock coordinates independent processes; the local lock coalesces threads in one caller. Readiness is
separate from process existence. The `Wait`/`Waiter` interface makes health checks independently pluggable:
`ConnectWait` performs the inexpensive connect-and-disconnect door knock, `HttpWait` can require a dedicated
endpoint's status and exact body, and `RpcWait` completes a full protocol handshake. Applications can register their
own `Wait` implementations without changing daemon launch policy.

## Runtime and graceful exit

`ServiceRuntime` gives a service two related controls:

- `runtime.activity.acquire()` accepts a unit of work while shutdown has not begun. Active work suspends idle expiry.
- `runtime.shutdown.request()` begins shutdown. New activity is rejected and accepted activity may drain.

When the final activity is released, a fresh idle linger window begins. `SIGINT` and `SIGTERM` request the same graceful
shutdown by default. `RuntimeService` waits for activity to become inactive and raises `DrainTimeoutError` if the
configured drain deadline expires.

`RpcService` acquires activity for actual requests, not for handshake-only readiness probes. The pipeline HTTP
services follow the same lifetime rule for application requests versus their dedicated health endpoint. They stop
accepting new application work after shutdown begins and drain connections which already own accepted work.

## External child processes

`omcore.daemons.children` covers the case where the service implementation is an executable this repository cannot
adapt: for example, a model server with its own HTTP stack. `ChildProcessSupervisor` is the reusable owner;
`ChildProcessService` is its thin `ServiceRuntime` adapter. Readiness remains ordinary daemon configuration:

```python
service = ChildProcessService.Config(
    process=ChildProcessConfig(
        cmd=('/opt/llama-server', '--port', '8080'),
        stdout=ChildProcessOutput.file('/var/tmp/llama.log'),
        stderr=ChildProcessOutput(mode=ChildProcessOutputMode.STDOUT),
        start_new_session=True,
    ),
    termination=ChildTerminationConfig(
        signal_process_group=True,
        grace_timeout_s=10.,
        kill_timeout_s=5.,
    ),
)
daemon = ServiceDaemon(
    service,
    Daemon.Config(
        spawning=MultiprocessingSpawning(),
        pid_file='/var/tmp/llama-supervisor.pid',
        wait=HttpWait(url='http://127.0.0.1:8080/healthz'),
    ),
).daemon_()
```

The pidfile identifies the Python supervisor, not the external child. A successful `Popen` call establishes that the
executable was created; `HttpWait` establishes that its application is ready. If `Popen` itself fails, the service
raises that startup error. If the child exits before runtime shutdown was requested, the supervisor reaps it, requests
runtime shutdown, and raises `ChildProcessExitedError` with its PID and return code.

On requested or idle shutdown, the configured graceful signal is sent. On signal-originated shutdown, the incoming
signal is forwarded by default. The supervisor waits for the grace deadline, sends `SIGKILL` if necessary, and waits
for the configured kill deadline while a dedicated waiter owns reaping. Process-group signaling is opt-in and requires
`start_new_session=True`; it controls descendants as a group but only the direct child is waitable by this supervisor.

Standard input defaults to `/dev/null`. Output may be inherited, discarded, written to an append-or-truncate file, or
(for stderr) joined to stdout. `pass_fds` is the explicit escape hatch for additional descriptors; ordinary `Popen`
descriptor closing remains enabled. When a daemon reparents and closes its own standard streams, inherited child
output is consequently `/dev/null`, so configure files or child-native logging when output must survive.

An opaque server's traffic bypasses `ServiceRuntime`, so the supervisor cannot infer request activity. An idle timeout
on `ChildProcessService` is therefore a fixed lifetime from its last explicit runtime touch, not traffic-aware linger.
Use no runtime idle timeout, a child-native idle policy, an explicit activity notification channel, or a proxy when
actual requests must renew the lease.

## HTTP services

The `omcore.daemons.http` subpackage provides a small pipeline-native HTTP composition without putting HTTP policy in
`Daemon` itself. `pipeline_http_server_spec()` is a sans-I/O, one-request session built from the repository's HTTP
decoder, request aggregator, response encoder, and I/O flow machinery. `PipelineHttpServer` drives a fresh pipeline
per TCP connection with the synchronous socket driver; `AsyncioPipelineHttpServer` uses the same messages and session
with the asyncio stream driver.

Both hosts depend on the narrow `HttpServerRuntime` interface rather than `ServiceRuntime`. They can therefore be run
standalone with `SimpleHttpServerRuntime`, under another lifecycle owner, or through `PipelineHttpService` and
`AsyncioPipelineHttpService`. The service adapters supply idle lifetime, signal shutdown, activity leases, and bounded
drain. The asyncio host accepts only async handlers; `ThreadedAsyncHttpHandler` is the explicit adapter when blocking
application work should run in a worker thread.

The configured `HttpHealthConfig` route is handled outside the application handler and does not acquire activity.
Repeated readiness probes cannot keep an otherwise idle service alive. An accepted application request holds activity
through handler execution and response output drain; after shutdown begins, new application requests receive `503`.
The initial session deliberately aggregates a bounded request body, emits a full response, closes the connection, and
does not yet provide streaming or keep-alive.

This serving stack is optional. `HttpWait` remains based on the standard library and can probe a daemon running
`http.server`, a framework server which cannot be changed, or a daemon which supervises an external HTTP process. None
of `Daemon`, `Launcher`, `LazyDaemon`, or the general readiness interface imports the pipeline HTTP server.

## RPC scope

The RPC transport is intentionally small:

- Unix-domain or TCP byte streams;
- four-byte big-endian length framing;
- bounded UTF-8 JSON messages;
- a protocol/version handshake and per-launch instance ID;
- one request per connection;
- concurrent server-side request execution;
- stable client/request IDs and same-instance response replay; and
- remote, unavailable, protocol, and indeterminate outcome errors.

Framing and protocol sequencing are sans-I/O pipeline handlers. `RpcServer`/`RpcClient` use the synchronous socket
driver, `AsyncioRpcServer`/`AsyncioRpcClient` use the asyncio stream driver, and `FdioRpcServer` uses the fdio driver.
The wire messages and session handlers are shared; listener ownership, connection tracking, waits, and handler
execution are host policy. The asyncio host accepts only async handlers. A synchronous handler must be wrapped in
`ThreadedAsyncRpcHandler`, making the event-loop/thread choice explicit.

`UnixRpcEndpoint` and `TcpRpcEndpoint` are dumb endpoint values. Existing `socket_path=` configuration remains the
compatibility shorthand for a Unix endpoint. For TCP, pass `endpoint=TcpRpcEndpoint(...)`; a server configured with
port zero exposes the kernel-selected address through `bound_endpoint`. Sync and asyncio transports are injectable at
client/server construction, while the default implementations provide Unix sockets and plaintext TCP. The fdio host
uses the same synchronous listener interface and therefore supports the same default endpoints.

TCP does not alter the handshake, instance identity, replay cache, or retry taxonomy. The default TCP transport also
does not add authentication or encryption. Binding beyond loopback exposes the RPC handler to that network and must be
an explicit application security decision. A future TLS transport belongs behind the transport interface rather than
inside the RPC protocol.

`FdioRpcServer` deliberately executes its synchronous handler on the fdio loop and is therefore suited to short,
nonblocking work. It is a useful first datapoint for a future general pipeline-server abstraction, not an assertion
that every server should share one listener implementation.

`RpcObjectHandler` and `RpcObjectProxy` form an optional interface facade over that transport. Only methods explicitly
marked with `@rpc_method` are exposed; the handler never performs request-controlled attribute lookup. The same
interface supplies local argument binding on the proxy and authoritative binding on the server:

```python
class Greeter(abc.ABC):
    @rpc_method
    @abc.abstractmethod
    def greet(self, name: str) -> str:
        raise NotImplementedError


handler = RpcObjectHandler(Greeter, GreeterImpl())
greeter: Greeter = RpcObjectProxy.of(Greeter, client)
```

This facade does not change the JSON boundary: parameters and return values must still be JSON-representable. The
layer does not currently provide streaming, transport authentication, arbitrary object marshaling, or pickle
transport. In particular, it never assumes a failed connection means a request was not executed. See the retry
contract in [DESIGN.md](DESIGN.md).

## Testing

The suite uses real files, locks, Unix sockets, HTTP servers, subprocesses, multiprocessing children, raw forks,
signals, and execs. It verifies sync and asyncio thread-backed HTTP services through shared in-process state, lazily
launches a pipeline HTTP service in a spawned process, and probes an independent standard-library HTTP server through
the same `HttpWait`. External-child tests pass real descriptors, redirect real output, signal a process group, force
graceful-timeout escalation, propagate unexpected exit, and probe a supervised external HTTP process while separately
tracking its supervisor pidfile. Inspection coverage observes that process through startup, readiness, exit, stale
contents, and replacement UUIDs. Wait-stopped coverage uses separately spawned lock owners to prove lock release,
timeout diagnostics, unlinked/recreated path detection, and same-inode UUID replacement. The suite also exercises the
RPC core without a daemon, runs pure sans-I/O transcripts, crosses every sync/async client-server pairing over real TCP
and Unix sockets, drives fdio through both endpoints, and checks compatibility with the original blocking wire
helpers. The daemon tests do not mock or patch those boundaries.

```shell
./python -m pytest omcore/daemons
```

The integration suite covers Linux behavior continuously and includes Darwin-specific execution in CI. Raw fork,
reparenting, `fcntl` locking, Unix sockets, and POSIX signals make this package intentionally non-portable to native
Windows.
