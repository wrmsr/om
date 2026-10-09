# Multiplexed streams

`omcore.io.pipelines.multiplex` carries many logical streams over one I/O pipeline - SSH channels, HTTP/2 streams, and
the like - with each stream backed by its own child `IoPipeline`. The multiplexing handler drives every child, meeting
for it the same terminal contract a socket driver meets for a top-level pipeline, so anything that runs on an ordinary
pipeline - byte decoders, protocol codecs, timeouts - runs unchanged inside a stream.

The core is protocol-agnostic. A protocol plugs in through a `MultiplexAdapter`. The contracts are recorded in
[DESIGN.md](../DESIGN.md) section 13.

## Public surface

- `MultiplexIoPipelineHandler(adapter, spec_factory, *, config, credit, scheduler)` - placed innermost in the parent
  pipeline, inside the handlers decoding and encoding the protocol's frames.
- `MultiplexAdapter` - the protocol: decodes inbound frames into calls on a `MultiplexConnection`, and encodes what the
  core asks it to emit.
- A stream spec factory - `(MultiplexStreamOpening) -> IoPipeline.Spec | MultiplexRefusal` - for peer-opened streams.
- `MultiplexConfig` and `MultiplexChildConfig` - limits, the per-turn output budget, child batching and watermarks.
- Credit strategies - `StreamMultiplexCreditStrategy` (per stream, like SSH) and `ConnectionMultiplexCreditStrategy`
  (per stream plus connection, like HTTP/2) - with replenish policies.
- `RoundRobinMultiplexOutputScheduler` - deficit round robin between streams with sendable output.
- Messages: `MultiplexMessages.OpenStream` (opens a local stream, completing with a `MultiplexOpenedStream`),
  `MultiplexMessages.Shutdown` (graceful connection shutdown), and `MultiplexMessages.FeedStream` (feeds a stream's
  pipeline at its boundary, like a driver's `enqueue`).
- `MultiplexStreamMetadata` - attached to each child pipeline: the stream's key, origin, and opening information.

The stream table, stream state machine, credit accounting, and output scheduling (`streams`, `credit`, `schedulers`) do
not depend on child pipelines, so a consumer preferring tagged messages to child pipelines can build on them.

## Writing an adapter

A minimal protocol whose frames are `Open`, `Data`, `End`, `Grant` dataclasses, with one shared key space, implicit
opens, and per-stream credit:

```python
class ToyAdapter(MultiplexAdapter):
    def __init__(self, *, window: int = 64 * 1024) -> None:
        super().__init__()
        self._window = window
        self._next_key = 1

    # Inbound: tell the core what arrived.

    def inbound(self, conn: MultiplexConnection, msg: ta.Any) -> bool:
        if isinstance(msg, Open):
            conn.open_remote(msg.key, msg.info, recv_window=self._window, send_credit=msg.window)
        elif isinstance(msg, Data):
            conn.data(msg.key, msg.data)  # raises FlowControlMultiplexError on overrun
        elif isinstance(msg, End):
            conn.end(msg.key)
        elif isinstance(msg, Grant):
            conn.grant(msg.key, msg.n)
        else:
            return False  # not ours: forwarded inward
        return True

    # Local opens: allocate a key and windows.

    def open_local(self, conn: MultiplexConnection, info: ta.Any) -> MultiplexStreamParams:
        key, self._next_key = self._next_key, self._next_key + 1
        return MultiplexStreamParams(key, recv_window=self._window, send_credit=self._window, explicit=False)

    # Outbound: encode what the core decided to emit.

    def encode_open(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [Open(stream.key, stream.info, self._window)]

    def encode_data(self, stream: MultiplexStream, data: SegmentedByteStreamBufferView) -> ta.Sequence[ta.Any]:
        return [Data(stream.key, data.tobytes())]

    def encode_end(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [End(stream.key)]

    def encode_credit(self, stream: ta.Optional[MultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        return [Grant(stream.key, amount)]

    # Policy: a finished stream whose peer has also ended is closed.

    def on_stream_finished(self, conn: MultiplexConnection, stream: MultiplexStream) -> None:
        if stream.remote_ended:
            conn.close(stream.key)
```

Then:

```python
mux = MultiplexIoPipelineHandler(ToyAdapter(), lambda opening: IoPipeline.Spec([EchoHandler()]))
spec = IoPipeline.Spec([ToyFrameCodec(), mux], services=[...])
```

Inside a stream, the application sees an ordinary pipeline: `InitialInput` when the stream is established, bytes and
typed messages as input, `FinalInput` when the peer ends its output, writability transitions derived from the stream's
own backlog. It ends its own output with `ShutdownOutput` and finishes with `FinalOutput`.

The test packages contain two complete toy protocols, `tests/sshlike.py` (explicit opens, a channel number per side,
per-stream credit, typed and flow-controlled messages, a close handshake) and `tests/h2like.py` (implicit opens with
id parity, two-level signed credit with settings shifts, padding, resets, and GOAWAY).
