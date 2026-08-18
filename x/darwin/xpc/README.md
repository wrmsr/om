# ctypes-xpc

`ctypes-xpc` is a small, runtime-dependency-free Python wrapper around the public C `libxpc` API on macOS. It includes two layers:

1. `ctypes_xpc.core`: native XPC objects, dictionaries, arrays, connections, listeners, endpoints, one-way messages, request/reply, peer credentials, peer code-signing requirements, and incoming-message replies.
2. `ctypes_xpc.rpc`: a compact `NSXPCConnection`-like exported-object/remote-proxy layer with bidirectional calls, method allowlists, one-way methods, remote exceptions, code-signing policy, executors, and async method results.

The low-level layer sends ordinary native XPC dictionaries and is directly interoperable with C, Objective-C, Swift, Rust, or any other language using the low-level XPC APIs. The mini-RPC layer deliberately uses its own documented dictionary envelope; it is not wire-compatible with Foundation's `NSXPCConnection`.

There are no runtime dependencies, no PyObjC, and no compiled Python extension. Callback support is implemented by constructing no-capture Objective-C Block literals with `ctypes` according to the Clang Blocks ABI.

## Requirements

- 64-bit macOS on ordinary x86_64 or arm64 CPython
- CPython 3.10 or later
- A real `launchd` registration for named Mach-service listeners

Importing the package on another operating system is harmless. The native library is loaded lazily, and the first XPC operation raises `XPCUnavailableError`.

## Install

From the source tree:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Or simply put the source directory on `PYTHONPATH`.

## Low-level API

### A native dictionary request

```python
from ctypes_xpc import XPCConnection

with XPCConnection.connect_mach_service("com.example.calculator") as connection:
    reply = connection.request(
        {"op": "add", "left": 20, "right": 22},
        timeout=5,
    )
    print(reply)
```

`request()` uses the asynchronous native XPC reply API internally and waits on a standard-library `Future`. `request_async()` exposes that future directly. `request_sync_native()` is also available when the exact synchronous C primitive is desired.

### Peer code-signing requirements

On macOS 12 and later, a connection may ask libxpc to reject peers that do not satisfy an Apple code-signing requirement string:

```python
connection = XPCConnection.connect_mach_service("com.example.calculator")
connection.set_peer_code_signing_requirement(
    'anchor apple generic '
    'and identifier "com.example.calculator" '
    'and certificate leaf[subject.OU] = "ABCDE12345"'
)
connection.activate()
```

The requirement must be installed before `activate()`. The wrapper permits one requirement call per connection, matching the native API's rule that multiple peer-requirement setters on one connection are a programming error. On older macOS releases the method raises `XPCUnavailableError` rather than preventing the rest of the package from loading.

The mini-RPC constructors expose the same facility as `peer_code_signing_requirement=`:

```python
connection = MiniXPCConnection.connect_mach_service(
    "com.example.mini-xpc",
    remote_interface=RPCInterface.of("add"),
    peer_code_signing_requirement='identifier "com.example.mini-xpc"',
)
```

For accepted server peers, pass the option to `MiniXPCMachService`. It is applied to each peer before that connection is activated.

### A launchd Mach-service listener

```python
import os

from ctypes_xpc import XPCConnection, XPCMessage, wait_forever

SERVICE_NAME = "com.example.calculator"


def accept(_listener: XPCConnection, peer: XPCConnection) -> None:
    # Credential checks are policy, so the wrapper does not guess one for you.
    if peer.peer_credentials().euid != os.geteuid():
        peer.cancel()
        return

    def handle(_peer: XPCConnection, message: XPCMessage):
        request = message.payload
        if request.get("op") == "add":
            return {"ok": True, "result": request["left"] + request["right"]}
        return {"ok": False, "error": "unknown operation"}

    peer.set_message_handler(handle, auto_reply=True)
    peer.activate()


listener = XPCConnection.mach_service_listener(SERVICE_NAME)
listener.set_peer_handler(accept)
listener.activate()
wait_forever()
```

A listener cannot claim an arbitrary globally named service by itself. The process must be launched in a bootstrap domain where `launchd` has registered the same name under `MachServices`; an example plist and setup procedure appear below.

### Delayed replies

Incoming dictionaries are represented by `XPCMessage`. The object retains the native request, so it can safely outlive the event callback:

```python
pool = concurrent.futures.ThreadPoolExecutor()


def handle(_connection, message):
    def work():
        try:
            result = expensive_operation(message.payload)
            message.reply({"ok": True, "result": result})
        except Exception as exc:
            message.reply({"ok": False, "error": str(exc)})
        finally:
            message.close()

    pool.submit(work)
    return NO_REPLY
```

A message can be replied to at most once. A failed encoding attempt does not consume its reply opportunity, allowing an RPC layer to replace an unencodable success result with an error response.

`XPCMessage.pointer` exposes a borrowed native pointer while the message remains open. `XPCMessage.retain_pointer()` acquires a reference owned by the caller, which is useful for composing this wrapper with another public C API that accepts the original incoming XPC message. The caller must eventually release that retained pointer with `xpc_release`.

### Anonymous endpoints

```python
listener = XPCConnection.anonymous_listener()
listener.set_peer_handler(accept)
listener.activate()

endpoint = listener.endpoint()       # Send this inside another XPC message.
client = XPCConnection.from_endpoint(endpoint)
client.activate()
```

An endpoint is an XPC capability, not a serializable byte string. It must be transferred through XPC or another Mach-right-aware mechanism.

### Bundled `.xpc` services

For an XPC service embedded in an application bundle, use `run_bundled_service()` rather than creating a `MachServices` listener:

```python
from ctypes_xpc import run_bundled_service


def accept(peer):
    peer.set_message_handler(handle, auto_reply=True)
    peer.activate()


run_bundled_service(accept)  # Enters xpc_main() and normally never returns.
```

## Python/XPC value mapping

| Python value | Native XPC type | Notes |
|---|---|---|
| `None` | null | |
| `bool` | bool | Checked before `int` |
| `int` | int64 or uint64 | Values through signed 64-bit use int64; larger nonnegative values use uint64 |
| `UInt64` | uint64 | Forces unsigned representation even for small values |
| `float` | double | |
| `str` | string | UTF-8; embedded NUL is rejected |
| `bytes`, `bytearray`, `memoryview` | data | Copied into the native object |
| `XPCDate` | date | Exact signed nanoseconds from the Unix epoch |
| aware `datetime.datetime` | date | Naive datetimes are rejected |
| `uuid.UUID` | UUID | |
| `XPCFileDescriptor` | fd | A decoded value owns a duplicated descriptor |
| `list`, `tuple` | array | Recursive |
| string-keyed `Mapping` | dictionary | Recursive |
| `XPCEndpoint` | endpoint | Retained while embedded |
| `XPCObject` | original native type | Retained; useful for forwarding unsupported types |

Unknown incoming native types are returned as owned `XPCObject` instances rather than discarded. Top-level connection messages must be dictionaries, matching the low-level XPC API.

## Mini `NSXPCConnection`-like RPC

The high-level layer gives each side:

- an explicitly allowlisted exported object;
- a dynamic proxy for the remote object;
- request/reply methods returning `concurrent.futures.Future`;
- a one-way proxy;
- interruption and invalidation handlers;
- remote exception propagation;
- optional executor dispatch and optional asyncio-result support.

### Service

```python
import os

from ctypes_xpc import MiniXPCConnection, MiniXPCMachService, RPCInterface, rpc_method

SERVICE = "com.example.mini-xpc"
SERVER = RPCInterface.of("add", "ask_client")
CLIENT = RPCInterface.of("multiply")


class ServiceObject:
    def __init__(self, connection: MiniXPCConnection) -> None:
        self.connection = connection

    @rpc_method
    def add(self, left: int, right: int) -> int:
        return left + right

    @rpc_method
    def ask_client(self, left: int, right: int):
        # This is a reverse RPC. Returning its Future delays the original reply
        # without blocking the XPC event handler.
        return self.connection.remote.multiply(left, right)


service = MiniXPCMachService(
    SERVICE,
    ServiceObject,
    exported_interface=SERVER,
    remote_interface=CLIENT,
    peer_validator=lambda credentials: credentials.euid == os.geteuid(),
)
service.start()
service.run_forever()
```

### Client with an exported callback object

```python
from ctypes_xpc import MiniXPCConnection, RPCInterface, rpc_method


class ClientCallbacks:
    @rpc_method
    def multiply(self, left: int, right: int) -> int:
        return left * right


connection = MiniXPCConnection.connect_mach_service(
    "com.example.mini-xpc",
    exported_object=ClientCallbacks(),
    exported_interface=RPCInterface.of("multiply"),
    remote_interface=RPCInterface.of("add", "ask_client"),
)
try:
    print(connection.remote.add(20, 22).result(timeout=5))
    print(connection.remote.ask_client(6, 7).result(timeout=5))
finally:
    connection.close()
```

`connection.remote.method(...)` returns a future. `connection.remote_oneway.method(...)` sends without a reply and returns `None`. A blocking convenience method is also available as `connection.call("method", ..., timeout=...)`.

For asyncio callers, standard futures can be adapted with `asyncio.wrap_future()`:

```python
result = await asyncio.wrap_future(connection.remote.add(20, 22))
```

An exported method may return a plain value, a `concurrent.futures.Future`, or an awaitable. Awaitables require an active event loop passed as `asyncio_loop=`. A supplied `executor=` moves ordinary exported method execution off the XPC callback queue.

### Interface generation

`RPCInterface.from_object()` includes only methods marked with `@rpc_method`:

```python
interface = RPCInterface.from_object(ServiceObject)
```

The receiver always enforces its exported interface. Supplying a `remote_interface` additionally catches misspelled or disallowed remote methods locally before a message is sent.

### Mini-RPC wire envelope

The custom protocol is intentionally simple and made entirely from native XPC values.

Call:

```python
{
    "__ctypes_xpc_rpc__": 1,
    "kind": "call",
    "method": "add",
    "args": [20, 22],
    "kwargs": {},
}
```

One-way calls use `"kind": "oneway"`. Replies are:

```python
{
    "__ctypes_xpc_rpc__": 1,
    "kind": "reply",
    "ok": True,
    "result": 42,
}
```

or:

```python
{
    "__ctypes_xpc_rpc__": 1,
    "kind": "reply",
    "ok": False,
    "error": {
        "module": "builtins",
        "type": "ValueError",
        "message": "bad input",
        "traceback": "optional and disabled by default",
    },
}
```

That envelope is not Foundation's private proxy/archive protocol. It is self-interoperable as supplied, and small enough to reimplement in another low-level XPC client if desired.

## Cross-language interoperability demo

`examples/raw_peer.c` is both a C client and a C Mach-service implementation. Together with `raw_service.py` and `raw_client.py`, it demonstrates all four directions:

- C request to Python, Python reply to C;
- Python unsolicited event to C;
- Python request to C, C reply to Python;
- C unsolicited event to Python.

Compile on macOS:

```sh
xcrun clang \
  -std=c11 -Wall -Wextra -Wpedantic -fblocks \
  examples/raw_peer.c -o examples/raw_peer
```

The shared raw schema uses `op`, `a`, `b`, `text`, `ok`, `sum`, and `server` keys, all as ordinary native XPC dictionary entries.

## Installing the example LaunchAgents

Named Mach services are registered by `launchd`. Do not double-fork or daemonize the Python service; remain in the foreground and let `launchd` own its lifecycle.

First install the package in the interpreter that the service will use:

```sh
cd /absolute/path/to/ctypes-xpc
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Render and install one example plist with absolute paths:

```sh
# High-level bidirectional Python mini-RPC service:
.venv/bin/python examples/render_plist.py echo

# Low-level Python service for the C client:
.venv/bin/python examples/render_plist.py raw

# Low-level C service for the Python client (compile raw_peer first):
.venv/bin/python examples/render_plist.py raw-c
```

The renderer prints the exact `launchctl` commands. The equivalent sequence is:

```sh
PLIST="$HOME/Library/LaunchAgents/com.example.ctypes-xpc.echo.plist"
DOMAIN="gui/$(id -u)"

plutil -lint "$PLIST"
launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl print "$DOMAIN/com.example.ctypes-xpc.echo"
```

`MachServices` is an on-demand launch condition, so running the client is normally enough to start the service. For debugging, force a start or restart with:

```sh
launchctl kickstart -kp "gui/$(id -u)/com.example.ctypes-xpc.echo"
```

Run the high-level demo:

```sh
.venv/bin/python examples/echo_client.py
```

Run C client against Python service:

```sh
examples/raw_peer client com.example.ctypes-xpc.raw
```

Run Python client against C service:

```sh
.venv/bin/python examples/raw_client.py \
  --service com.example.ctypes-xpc.raw-c
```

Logs from the templates are written under `/tmp/ctypes-xpc-*.stdout.log` and `/tmp/ctypes-xpc-*.stderr.log`.

## Threading and callback rules

XPC event handlers run on libdispatch-managed threads and enter Python through a `ctypes.CFUNCTYPE` trampoline. The wrapper keeps every installed Block and active connection strongly referenced for the native callback lifetime. Each outbound native operation also takes a temporary XPC retain, so a concurrent terminal event cannot release the connection while the C call is still using it. Outstanding reply Blocks remain pinned until their native callbacks arrive, even when connection invalidation is delivered first.

Do not perform a blocking request from inside an XPC event callback. Low-level `request()` and `request_sync_native()`, and high-level `call()`, detect this case and raise `XPCReentrancyError`. Use `request_async()`, a remote-proxy future, an executor, or return a future from the exported method.

The target queue is left as `NULL`, which asks XPC to choose its normal private queue. Async reply callbacks use a global dispatch queue. User handlers should still be written as concurrent code: a client may have reply callbacks and connection events executing on different threads.

## Security boundaries

This wrapper does not bypass any macOS security boundary. The caller still needs the correct bootstrap namespace, launchd registration, sandbox permissions, entitlements where applicable, code-signing policy, and filesystem permissions.

For a real service:

- expose only a small `RPCInterface`;
- validate peer credentials before activating accepted connections;
- install `set_peer_code_signing_requirement()` where the threat model needs identity beyond UID/PID;
- leave remote tracebacks disabled unless both endpoints are trusted;
- validate all argument values inside exported methods.

`peer_credentials()` exposes the PID, effective UID, effective GID, service name, and audit-session identifier reported by libxpc. The sample LaunchAgents reject peers with a different effective UID, but that is only an example policy. PID/UID/session metadata is useful context, not a substitute for code-signing policy when executable identity matters.

## Deliberate limitations

- The mini-RPC protocol is not `NSXPCConnection` compatible and does not implement `NSSecureCoding`, Objective-C selectors, classes-by-argument, or Foundation object graphs.
- The generic codec covers the common public types, but not shared-memory objects, Mach send/receive rights, or activities. It wraps the string-based peer code-signing requirement API, but not the newer lightweight, team-identity, platform-identity, or entitlement-specific requirement helpers.
- There is no attempt to expose or preserve XPC's private wire encoding. Native objects are always passed through public XPC APIs.
- The Block bridge follows the public Clang ABI but is necessarily lower-level and more delicate than compiling an Objective-C shim.
- The pointer-authenticated arm64e process ABI has not been validated. Normal arm64 CPython builds do not use the arm64e ABI, but an arm64e Python build would need target testing of the Block invoke pointer.
- Native XPC behavior and the included C example must be tested on the target macOS versions and architectures. Import, syntax, and the transport-independent RPC logic can be tested elsewhere.

## Tests

```sh
PYTHONPATH=. python -m unittest discover -s tests -v
```

The current suite has 23 tests. An in-memory connection pair exercises simple calls, nested reverse calls, one-way callbacks, remote errors, and interface extraction. A fake native object model exercises recursive codec ownership, delayed-reply retry behavior, malformed UTF-8, Block layout, invalidation/reply ordering, temporary connection retains, peer requirements, credential metadata, and retained incoming-message pointers. The LaunchAgent renderer is tested with both Python and C-service templates. Native integration tests still require a macOS host and launchd bootstrap domain.

## Files

```text
ctypes_xpc/core.py          low-level ctypes/libxpc wrapper
ctypes_xpc/rpc.py           mini exported-object RPC layer
examples/echo_service.py    high-level Python service
examples/echo_client.py     high-level Python client with callbacks
examples/raw_service.py     low-level Python service
examples/raw_client.py      low-level Python client
examples/raw_peer.c         low-level C client/service interoperability demo
examples/*.plist            launchd LaunchAgent templates
tests/test_core_codec.py    fake-native codec, ownership, and Block tests
tests/test_examples.py      LaunchAgent renderer tests
tests/test_rpc.py           transport-independent RPC tests
```

## License

BSD 3-Clause.

## Primary references

- Apple XPC API documentation: <https://developer.apple.com/documentation/xpc>
- Apple XPC Services programming guide: <https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html>
- Apple launchd jobs guide: <https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html>
- Clang Blocks ABI specification: <https://clang.llvm.org/docs/Block-ABI-Apple.html>
