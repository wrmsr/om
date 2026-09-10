# JSON-RPC

An implementation of [JSON-RPC 2.0](https://www.jsonrpc.org/specification): message types, strict parsing, method
dispatch, and, in the `pipelines` subpackage, fully configurable clients and servers built on the
[io pipelines](../../io/pipelines) system. It is what the MCP and ACP code speaks over.

## Layout

The package splits into a transport-free core and a pipelines layer on top of it.

- `types.py` - `Request`, `Response`, `Error`, plus `InvalidMessage` (a received value which could not be parsed, and
  the error response answering it) and `Batch`. Params may be an object or an array.
- `parsing.py` - strict conversion between JSON values and messages. The lenient `parse_payload` and `loads_payload`
  never raise on bad input; they return an `InvalidMessage` carrying the spec-mandated error response instead.
- `errors.py` - the error codes and exception hierarchy. Handlers raise `JsonrpcMethodError` to answer with a specific
  error; callers see a peer's error response as `JsonrpcRemoteError`.
- `dispatch.py` - the `JsonrpcDispatcher` / `AsyncJsonrpcDispatcher` interfaces and dict-based implementations which
  bind params to a callable's signature (by name for objects, by position for arrays).
- `ids.py` - request id creators. The default is an integer counter.
- `conns.py` - the `JsonrpcConnection` / `AsyncJsonrpcConnection` interfaces.
- `pipelines/` - the connections and servers, described below.

## Pipelines

JSON-RPC is symmetric: either peer may send requests, notifications, and responses at any time. So there is one
session handler serving both roles, and the client / server distinction lives only in the top-level classes - who
connected to whom, and which dispatcher is installed.

The pipeline for one connection, outermost first:

```
[app handlers]
LoggingHandler                  optional
OutboundBytesBufferHandler      flow control
SslHandler                      optional
WriteTimeoutHandler             stalled flush -> error
NdjsonFramingHandler | ContentLengthFramingHandler
JsonrpcCodecHandler             frames <-> messages, never raises on bad input
IdleStateHandler                inner to the codec: idle means no complete messages
JsonrpcSessionHandler           the sans-io core
[app handlers]
```

`JsonrpcSessionHandler` owns all protocol state: it correlates responses to sent requests, surfaces the peer's
requests for the host to answer, and enforces every timeout and limit expressible without a transport - request
timeouts, in-flight limits, batch aggregation, invalid-message policy, graceful close with draining. Timers come from
the driver's scheduling service, so behavior is identical under every driver and testable with the pure driver's
manual clock.

The host talks to the session through `JsonrpcPipelineMessages`: commands (`SendRequest`, `SendResponse`, `Close`,
...) go in through the driver's `enqueue`, and events (`ResponseReceived`, `RequestReceived`, `Sent`, `Closed`, ...)
come out of the driver's `next`. `Sent` is emitted once a message's bytes have crossed into the transport, and hosts
block sends on it, which is what makes backpressure real against a peer which stops reading.

Every knob lives in `JsonrpcPipelineConfig`; `build_jsonrpc_pipeline_spec` turns it into a pipeline spec.

### Connections

`BaseJsonrpcConnection` holds everything a host does with a session other than pumping the driver: id assignment,
demultiplexing events to waiters, result and error conversion, closure bookkeeping. Two subclasses tape drivers on:

- `AsyncioJsonrpcConnection` (`pipelines/asyncio.py`) runs a pump task over a `PollAsyncioStreamDriver`. Callers await
  futures; inbound requests each get a task running the dispatcher. `AsyncioJsonrpcConnections` builds one over tcp,
  a unix socket, a subprocess's stdio, or the process's own stdio.
- `SyncJsonrpcConnection` (`pipelines/sync.py`) has no pump task: the calling thread pumps a `SyncIoPipelineDriver`
  (socket or file descriptor pair) while it waits. Inbound requests are dispatched inline between driver steps, so a
  handler may call back into the peer. One thread at a time may use it; `serve()` pumps until the peer closes.

`AsyncioJsonrpcServer` (`pipelines/servers.py`) accepts connections on a unix or tcp endpoint and runs one asyncio
connection per client, each a full peer the server may call back into.

### Example

```python
from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl

async def main():
    conn = await jpl.AsyncioConnections.connect_tcp(
        'localhost', 8765,
        jpl.Config(default_request_timeout_s=30.),
        dispatcher=jr.AsyncDictDispatcher({'ping': lambda: 'pong'}),
    )
    async with conn:
        print(await conn.request('add', {'a': 1, 'b': 2}))
        await conn.notify('progress', [50])
```

## Testing

The session is tested on a bare pipeline and under the pure driver with a manual clock (`pipelines/tests/harness.py`),
so every timeout and policy is exercised deterministically. The connections are tested over socketpairs, real
subprocesses over stdio, and unix and tcp servers.
