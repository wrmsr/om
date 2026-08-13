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
| Lazy access | `LazyDaemon` | Connect first; coordinate launch and relaunch only when explicitly unavailable. |
| Readiness | `ConnectWait`, `HttpWait`, `RpcWait` | Supply pluggable transport- or application-level health checks. |
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

`RpcService` acquires activity for actual requests, not for handshake-only readiness probes. It stops accepting new
work after shutdown begins and waits for connection threads which already own accepted work.

## RPC scope

The RPC transport is intentionally small:

- Unix-domain stream sockets;
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
layer does not currently provide streaming, authentication beyond local filesystem permissions, arbitrary object
marshaling, or pickle transport. In particular, it never assumes a failed connection means a request was not executed.
See the retry contract in [DESIGN.md](DESIGN.md).

## Testing

The suite uses real files, locks, Unix sockets, HTTP servers, subprocesses, multiprocessing children, raw forks,
signals, and execs. It also verifies a thread-backed service through shared in-process state, exercises the RPC core
without a daemon, runs pure sans-I/O transcripts, crosses sync and asyncio clients and servers, drives an fdio server,
and checks compatibility with the original blocking wire helpers. The daemon tests do not mock or patch those
boundaries.

```shell
./python -m pytest omcore/daemons/tests
```

The integration suite covers Linux behavior continuously and includes Darwin-specific execution in CI. Raw fork,
reparenting, `fcntl` locking, Unix sockets, and POSIX signals make this package intentionally non-portable to native
Windows.
