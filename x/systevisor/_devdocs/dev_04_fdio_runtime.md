# Development 04: fdio runtime, events, and logs

## Intent

Connect the deterministic engine to owned OS resources without giving up single-threaded ordering or testability. The
reactor should translate descriptor readiness and deadlines into facts, execute effects, and keep slow observers
strictly outside child-pipe backpressure paths.

## Runtime coordination

- Added an fdio coordinator that serializes input through a queue. Subscriber callbacks may submit commands, but they
  enqueue behind the current input/effect transaction instead of reentering the engine.
- Spawn effects create exec-handshake, pidfd, stdout, and stderr handlers. A bounded wait deadline remains as a
  portable fallback and SIGCHLD can prompt immediate observation.
- Exec/exit races are explicit: an exit cannot be delivered before the exec handshake is classified. Exec failures
  produce one spawn-failure fact and are still explicitly observed, session-cleaned, and reaped by the process owner.
- Deadline effects are owned by a no-FD fdio handler and produce deadline facts from an injected monotonic clock.
- TERM/INT/QUIT map to engine shutdown, SIGCHLD to wait observation, HUP to a reload-request event, and other managed
  signals to events. Signal intake uses Python's nonblocking wakeup FD rather than doing work in a signal callback.

## Event bus

The shared bus assigns its own monotonic sequence across engine, log, signal, and future API/config events. It keeps a
bounded replay journal, synchronous callback subscriptions, and independent bounded stream subscriptions. A slow
stream drops its oldest entries and reports an explicit dropped count. A failing callback is unsubscribed and
reported without preventing delivery to other subscribers.

## Child logs

- Child output stays bytes. Fdio handlers drain to EAGAIN/EOF into per-run/per-stream byte rings with absolute offsets.
- Reads report both byte eviction gaps and the next offset. Resizing a live back-buffer preserves absolute offsets.
- Slow event/HTTP consumers only interact with bounded bus queues or rings and cannot backpressure the child pipe.
- Capture, manager stdout/stderr forwarding, ANSI filtering, emit-events, rotating files, and live sink/back-buffer
  reconfiguration are represented. Sink failures remove only that sink and emit an internal error event.
- Output descriptor ownership transfers out of the process record into log handlers, while process retirement leaves
  tail descriptors available to drain through EOF.

## Dependency injection

Added an `omcore.lite.inject` runtime binding graph for poller, fdio manager, clock, engine, process manager, event bus,
log manager, and coordinator. These are stable singleton capabilities; desired config remains ordinary transactional
data and is never an injector binding.

## Testing

Pure tests cover virtual deadlines, event replay/overflow/callback failure, byte ring gaps/resizing, and file rotation.
Boundary tests cover signal wakeup-FD dispatch and one end-to-end engine -> fork/exec -> fdio -> wait -> log flow with
event-driven polling and hard timeouts, never sleeps. The injector graph is also assembled and singleton identity is
asserted.

## Next

Build the JSON-over-HTTP control plane and CLI on the existing fdio pipeline driver. Config reload will compile a
candidate outside the engine, publish diagnostics on failure, and submit one atomic snapshot command on success.
