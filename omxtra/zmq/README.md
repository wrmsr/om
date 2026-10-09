# zmq

A small ZeroMQ-compatible messaging library with two interchangeable backends:

- **`pipelines`** - an in-house implementation of ZMTP 3.0 over the `omcore.io.pipelines` stack, with no external
  dependencies, driven by asyncio.
- **`pyzmq`** - an adapter over pyzmq's asyncio sockets, available with the optional `omxtra[zmq]` extra.

It implements PUB, SUB, DEALER, and ROUTER over TCP and filesystem Unix-domain (IPC) sockets, and interoperates with
native ZeroMQ peers. It is meant to be small and understandable, not a complete or fast replacement for libzmq. See
[DESIGN.md](DESIGN.md) for the architecture.

## Usage

```python
from omxtra.zmq.backends.selection import new_backend

async with new_backend('pipelines') as backend:
    router = backend.create_router()
    bound = await router.bind('ipc:///run/myapp/router.sock')

    dealer = backend.create_dealer(routing_id=b'worker-1')
    await dealer.connect(bound.address)

    await dealer.send((b'hello', b'world'))
    msg = await router.recv()  # RoutedMessage(route=b'worker-1', message=(b'hello', b'world'))
    await router.send(msg.route, (b'reply',))
    assert await dealer.recv() == (b'reply',)
```

Runnable examples: `./python -m omxtra.zmq.examples.directed` and `./python -m omxtra.zmq.examples.pubsub`, each taking
`--backend` and `--address`.

## Backends

A backend is chosen explicitly - `new_backend('pipelines' | 'pyzmq')`, or by constructing `AsyncioPipelinesBackend` or
`PyzmqBackend`. Nothing is selected implicitly, and importing the package initializes nothing. Choosing `pyzmq` without
pyzmq installed raises `BackendUnavailableError`.

A backend owns the sockets it creates: closing it closes them. The pyzmq backend owns a fresh native context unless one
is given, which then stays the caller's. Sockets belong to the event loop they were created on and are not thread-safe.

## Messages

A message is a nonempty tuple of `bytes` frames: `(b'',)` is valid, `()` is not. Lists are accepted and normalized;
anything else is rejected with `InvalidMessageError`. `MessageLimits` bound frame size (8 MiB), message size (16 MiB),
frame count (1024), and subscription prefix size (4 KiB) by default, for what is sent and what is received.

A ROUTER receives `RoutedMessage(route, message)` and sends to a route given separately: routing never appears as an
extra frame of the message. Nothing adds or strips empty delimiter frames.

## Sockets

| Socket | Operations | Waits for capacity? |
|---|---|---|
| `Publisher` | `send(message)` | Never: a subscriber without room misses the message |
| `Subscriber` | `subscribe(prefix)`, `unsubscribe(prefix)`, `recv()` | - |
| `Dealer` | `send(message)`, `recv()` | Yes: round robin over ready peers with room, until the deadline |
| `Router` | `send(route, message)`, `recv()` | Never: `UnroutableError` if unknown, `WouldBlockError` if full |

Every socket also has `bind(address)`, `connect(address)`, and `aclose()`. `bind` returns once the listener exists, with
its actual address; `connect` returns once the connection intent is registered - connecting before the other side binds
is fine. Both return attachments whose `aclose()` stops listening or reconnecting.

**Subscriptions** match prefixes of the first frame; the empty prefix matches everything. They are reference-counted:
subscribing twice needs two unsubscribes. A message matching several prefixes is delivered once per connection.
A subscription takes effect only once it reaches the publisher, so messages published before then are missed ("slow
joiner"), and messages already queued may still arrive after unsubscribing.

**Sending** succeeds once the message is accepted locally. That is not transmission, delivery, or processing.

**Receiving** delivers whole messages, FIFO per peer connection, fairly across peers. One receive may be outstanding per
socket; another raises `ConcurrentReceiveError`. A receive cancelled before it returns leaves its message in place.

**Timeouts**, in seconds, default to the socket's `SocketConfig` (five minutes); pass `math.inf` for no deadline.
Timing out raises `ZmqTimeoutError`, a `TimeoutError`.

**Reconnection** of outgoing connections is automatic, with jittered exponential backoff; subscriptions are replayed on
each new connection. No message is resent: across a disconnection, an accepted message may or may not have arrived, and
order is not guaranteed across connections.

**Closing** is abortive and bounded: waiters fail with `SocketClosedError`, attachments stop, and queued messages are
discarded. There is no linger. When a peer disconnects, messages already received from it whole stay receivable, while
messages still queued to it are discarded.

## Addresses

- `tcp://host:port`, with `[...]` for IPv6 literals. For binding, `*` may stand for the host (all interfaces) or the
  port (an ephemeral one); the returned address carries the actual port.
- `ipc:///absolute/path`. Relative, abstract, and wildcard paths are rejected, as are paths over 103 bytes (macOS's
  limit). The parent directory must exist.

Binding an IPC path never removes anything already there - a stale socket, a file, a symlink - which must be cleaned up
explicitly. Cooperating binders using this library take a lease on a sidecar `<path>.lock` file for the bind's
lifetime, so they never take each other's path; an unwrapped native socket binding the same path does not respect it.
On close, a binder removes its path only if it is still the one its bind created.

## Security

NULL security only: no authentication, no encryption. Use private directories for IPC, and TCP only on trusted
networks.

## Backend differences

Both backends implement the contract above; they differ in what is beneath it.

- Queue sizes are per-peer message counts in both, but the in-house backend also bounds bytes per queue
  (`PipelinesBackendConfig`), and the native high-water marks are not exact byte or count budgets.
- An over-limit received message is a protocol violation that ends its connection in the in-house backend; the pyzmq
  backend discards it (counting it in `dropped_oversized`). Native frame-size limits apply before Python sees anything;
  native buffering may allocate first.
- A peer claiming an identity already in use is refused by both; the in-house backend then ends that connection, while
  a native ROUTER keeps it unidentified.
- The in-house backend ends connections which fail the handshake or exceed bounds at once; a native socket treats a
  peer not starting with a ZMTP 3 greeting as a legacy peer.
- The in-house backend bounds the sends waiting for capacity on one socket (`max_waiting_sends`), raising
  `WouldBlockError` beyond it.
- IPC path ownership compares the path's device and inode numbers with those its bind created: a path removed by
  someone else and recreated with a reused inode number would be taken for the original.

## Limitations

- No REQ/REP, PUSH/PULL, PAIR, XPUB/XSUB sockets, inproc transport, heartbeats, CURVE/PLAIN security, or monitor API.
- The in-house backend speaks ZMTP 3.0 only (a 3.1 peer falls back to it), and runs only under asyncio.
- Verified on Linux with Python 3.14 (including free-threaded 3.14), pyzmq 27.2.0, and libzmq 4.3.5. macOS is
  supported in principle but not yet verified.
