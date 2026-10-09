# zmq design

## Layers

```text
api/            Messages, addresses, configuration, errors, and the socket and backend interfaces. No I/O.
core/           Sans-I/O endpoints: peers, bounded queues, routing, subscriptions, fair selection. No I/O.
zmtp/           ZMTP 3.0 greeting, frame, command, and metadata codecs. No I/O.
zmtp/pipelines/ The per-connection pipeline stages.
ipc/            Ownership of bound IPC paths: entry identity and sidecar leases.
backends/       The in-house asyncio runtime, the pyzmq adapter, and selection by name.
```

Dependencies point inward: `backends` on everything, `zmtp/pipelines` on `zmtp`, `core`, and the generic pipeline stack,
`zmtp` and `core` on `api`. Nothing in `omcore.io.pipelines` knows about this package. Only `backends/pyzmq` refers to
pyzmq, through proxy imports, so everything else imports and works without it.

## The connection pipeline

Each transport connection gets a fresh pipeline, outermost first:

1. **`ZmtpCodecIoPipelineHandler`** turns bytes into the peer's greeting, commands, and whole multipart messages, and
   encodes them in the other direction. It never emits a partial message, so the base decoder's read requests already
   cover input which completes nothing. Bounds - frame, message, frame count, command - are checked from frame headers,
   before any body is buffered. A violation is emitted inbound as an `Error` after whatever completed before it, and
   everything after is discarded. Truncation at EOF is a violation; a connection which never sent a byte ends cleanly.
2. **`ZmtpHandshakeIoPipelineHandler`** sends the local greeting on activation and READY once the peer's greeting is
   valid, without waiting for the peer's READY. It accepts later 3.x versions (the peer falls back to 3.0) and requires
   NULL security and a supported peer socket type. Until ready it requests input itself; afterwards messages pass
   through. Its deadline is absolute from activation and is cancelled on readiness.
3. **`ZmtpSessionIoPipelineHandler`** joins the connection to its endpoint: it attaches the peer on readiness, delivers
   messages, pulls output, and detaches when the connection ends - including when the pipeline is destroyed. Commands
   the handshake ignores after readiness, such as a native peer's heartbeats, still reach it: input to read past.
   When the peer ends the connection it emits `ZmtpSessionEnded` to the connection's owner, not ordered behind
   unwritten output: the owner ends the connection abortively, as a peer which has closed reads no more.

The topology is fixed for the connection's lifetime; nothing is added or removed mid-stream.

## Endpoints

An endpoint (`PubEndpoint`, `SubEndpoint`, `DealerEndpoint`, `RouterEndpoint`) owns a socket's ready peers and their
queues. Its operations are synchronous and never block:

- sessions call `attach`, `deliver`, `can_receive`, `take_output`, and `detach`;
- the application side calls the pattern's operations: `publish`, `subscribe`, `try_send`, `send`, `recv`.

It reports to two kinds of synchronous sinks: a `PeerSink` per peer (`wake_send`, `wake_recv`, `close`) and one
`EndpointListener` (`on_readable`, `on_writable`). Every notification follows the state change it reports, and sinks
must not call back into the endpoint synchronously. They only arrange for something to happen later, so no endpoint
operation ever reenters another.

Each peer has a token that increases monotonically, and every session-side call is a no-op for a detached peer, so a
late callback cannot affect a later connection. A router's route is released only by the peer holding it.

## Driver boundary

The endpoint never calls into a pipeline. A peer's sink is its connection object, which turns `wake_send` and
`wake_recv` into a `ZmtpSessionWake` fed through the driver's own `enqueue`. The session acts on the wake in the
pipeline's turn. The driver remains the only reader and writer of its transport, and nothing reaches into its state or
caches a handler context.

## Flow control and bounds

**Output.** Messages wait in the peer's endpoint queue - bounded by count and bytes - until the session pulls them. The
session pulls only while the transport is writable, and at most a budget per turn: it continues through a `Defer`, so
the driver can report output pressure in between. A message's reservation ends when it is pulled into the driver,
whose buffer is itself bounded by its watermarks. So accepted-but-unsent data is bounded by the queue, plus the driver's
high watermark, plus one message and one turn's budget. Sends are admitted only to ready peers.

**Input.** Connections read in manual mode. After each batch the session requests more input only if the endpoint has
room for the peer's messages; otherwise reading pauses until the application's receives make room and the endpoint
wakes the session. The codec decodes everything in a read batch at once, so the overshoot past a queue bound is at most
one batch (64 KiB by default) of decoded messages. Control traffic - handshakes, subscriptions - takes no queue space.

**Fan-out.** A publication is queued to each matching peer with room, sharing the same immutable message, and dropped
for the others. A subscriber applies backpressure like any other socket. A slow subscriber therefore stops reading, its
publisher's queue for it fills, and only that subscriber loses messages.

**Limits.** Peers per socket (including connections still in their handshake), waiting sends, distinct subscription
prefixes per peer, prefix size, and command size are all bounded. A peer exceeding a bound is disconnected; a full queue
is ordinary backpressure.

**Not bounded.** There is no aggregate byte budget across a socket's peers beyond per-peer bounds times the peer limit.
Python object overhead is not counted.

## Delivery and cancellation

Transport flush fences are not used for acknowledgement: a send completes when its message is admitted to a queue,
which is all either backend can honestly promise. Pipeline fences guarantee transport acceptance at best, which is
neither receipt nor processing, and native completion means no more than local queueing.

Waiting operations are cancellation-safe. Each one checks its condition, takes the message in a step which does not
suspend, and otherwise waits on a generation notifier, so a notification between the check and the wait is not lost. A
cancelled receive therefore never consumes a message, and a cancelled send is either admitted whole or not at all. The
pyzmq adapter keeps the same discipline: it waits by polling, which consumes nothing, and then sends or receives one
whole multipart message without blocking through a synchronous shadow of the socket.

## Runtime

`AsyncioPipelinesBackend` gives each connection a `PollAsyncioStreamIoPipelineDriver` run by its own task.

- **Listeners** bind their own sockets and accept in their own tasks, rather than through an asyncio server, so that
  stopping one is a hard stop. An IPC bind fails if anything exists at the path, so no bind ever removes one.
- **Connectors** connect with a timeout, run the connection to its end, and reconnect after a jittered exponential delay
  (`reconnect_delay`, testable with an injected sample). The delay resets after a connection that became ready.
- **Closing a socket** stops its attachments, closes its endpoint (which aborts every peer's connection), aborts
  connections still in their handshake, and waits for all their tasks.

An idle socket has no timers, and its only tasks are listeners, connectors, and connections waiting on I/O. A
connection is aborted at most once, and a connection aborted before its task ran still cleans up when it does.

## Extension points

- **Other socket types.** REQ/REP, PUSH/PULL, and PAIR are new `Endpoint` subclasses composing the same pieces:
  - PUSH sends like a DEALER and does not receive;
  - PULL receives fairly and does not send;
  - REQ and REP add a small envelope state machine to DEALER and ROUTER behavior.

  The ZMTP compatibility table already includes them; enabling one means adding it to `SUPPORTED_PEERS`.
- **Inproc.** An endpoint is reached only through `attach`, `deliver`, `take_output`, and the sink interface. An inproc
  transport could join two endpoints directly with a pair of sinks, with no codec or pipeline.
- **Other runtimes.** Everything below `backends/` is runtime-independent. Another runtime needs a driver to run
  pipelines, a sink to feed wakes through it, and a way to wait.

## Changes to the pipeline stack

Building this found one defect in the generic stack, fixed with a driver conformance scenario. The asyncio driver
noticed its transport catching up only after writes and drains, and drained only for fences. A producer which honored
`PauseOutput` but never flushed - as the session does - therefore waited forever. While output is paused, the driver
now keeps a drain pending; its completion returns output to writable.

## Deviations from the implementation spec

- Message queues are bounded per peer, with no aggregate budget per socket.
- The codec decodes a whole read batch at once, allowing a bounded overshoot, rather than stopping mid-batch at a
  queue bound.
- After the handshake, unknown commands are ignored rather than rejected.
- Connection setup failures, including incompatible peers, are retried with backoff rather than disabling the
  connector.
- `bind()` takes no timeout: binding completes or fails at once, with nothing to wait for.
- The throughput smoke measurement was run by hand rather than kept as a test. On the development host the in-house
  backend managed about 27k small messages/s and 600 MB/s with large ones, against pyzmq's 79k and 1.5 GB/s.
- No import-tracking or source-scanning guardrail tests, by request. The code is written to satisfy them.
- Verified on Linux only.
