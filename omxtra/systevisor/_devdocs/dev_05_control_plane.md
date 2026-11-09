# Development 05: control plane and transactional reload

## Intent

Make the deterministic engine operable without compromising its ordering model: config changes must be atomic,
process transitions must not block HTTP, and event/log following must remain bounded and single-threaded.

## Configuration work

- Added a long-lived config controller over the existing compiler. It owns source paths, recursive discovery policy,
  attempt sequencing, active/last-attempt views, HUP reload subscription, and application of one compiled snapshot.
- Invalid live candidates emit `config.rejected` and never submit an engine command. Successful candidates emit
  `config.applied`; checks emit `config.checked` without changing desired state.
- Added two-phase runtime participants. Each candidate's participants prepare resources before the engine sees the
  snapshot, then commit after reconciliation accepts it. Preparation failure rolls earlier participants back and
  becomes a normal `prepare_failed` diagnostic. This was introduced after noticing that applying autostart changes
  before discovering an occupied API socket could otherwise leave children running after a failed cold start.
- Config attempt state is atomically replaced at `config-status.json` under the explicit/active state directory, with
  file and directory fsync. Persistence failure is itself an event and does not undo a successfully applied config.
- Applying API config also resizes the shared event journal, while manager ANSI policy was already live-applied to the
  log manager.

## Commands and operations

- Added bounded operation storage with stable `op-NNNNNNNN` IDs and created/completed events.
- Unit, collection, instance, restart, shutdown, check, and reload commands all return operations.
- Lifecycle operations remain pending until the corresponding instance state is observed. Starts complete at RUNNING,
  oneshots complete only after successful observed exit, restarts require a different run generation, stops require no
  owned run, and fatal/terminal startup failures fail the operation.
- Engine command rejection is correlated through the operation ID in `request_id`; the HTTP handler never waits for
  these asynchronous transitions.

## API and streaming

- Added a marshal-backed JSON codec which preserves enum wire values and standard base64 byte handling.
- Added a transport-independent application/router and the route set documented in `api.md`.
- Added custom omcore HTTP pipeline handling for finite and chunked responses. Streams retain a handler ref and receive
  event/log pushes through pipeline notifications, avoiding cached handler contexts and out-of-band socket writes.
- Stream production is pumped in bounded batches through deferred pipeline work. Transport high-watermark pause signals
  stop the pump; the per-connection application queue drops old records with an explicit gap rather than growing or
  applying pressure to child output.
- Added direct log subscriptions independent of optional general `process.log` events. Range records retain byte
  offsets and carry base64 so arbitrary child output stays lossless JSON.
- Added Unix and TCP fdio listeners. Unix collision handling probes an existing socket, refuses to replace an active
  listener or a non-socket path, and removes only a socket whose device/inode still matches the one this server bound.
- Listener reconciliation retains unchanged endpoints, prepares new endpoints before retiring obsolete endpoints,
  updates Unix mode, and closes owned connections/listeners on shutdown.

## Client and executable

- Added an omcore pipeline HTTP client and endpoint parsing for `unix:PATH`, absolute paths, and HTTP host/port values.
- Added the shared `python -m x.systevisor` entrypoint with offline config checking, daemon serving, finite control
  commands, event following, and decoded raw log following.
- Added an omcore.lite.inject control graph layered over the stable runtime graph. Bootstrap source paths are the only
  seeded values; compiler, codec, controller, operation store, application, server, and control plane are singletons.
- Daemon startup instantiates the control-plane participant before initial reload, so API binding failure happens before
  autostart reconciliation. HUP and API reload use the same transaction.

## Testing and problems found

The phase tests contain no sleeps and use hard deadlines only at real OS boundaries. They cover:

- invalid reload retaining the active digest and persisting parse diagnostics;
- occupied listener preparation rejecting a cold snapshot before any child is created;
- command rejection and real fork/exec oneshot operation completion;
- enum JSON values, event filtering/following, log range/follow without `emit_events`;
- request encoding and chunked response decoding through the client pipeline;
- incremental response delivery through the fdio socket pipeline;
- a real Unix listener on the shared manager, permission updates, inode retention, endpoint replacement/removal, and
  refusal to unlink a colliding ordinary file;
- import and source guards on Python 3.8.

An early streaming version emitted body data into the HTTP chunker but used the optional flow helper to flush. Since
the base fdio pipeline has no flow service by default, bytes remained buffered forever. Streaming now emits an
explicit flush fence after each bounded pump batch; a socket test prevents regression.

An early operation test also exposed that oneshots were considered started at RUNNING and could complete before their
exit was observed. They now require successful EXITED state, and restart correlation retains the last observed run ID.

## Known edges and next work

- Authentication/authorization is not yet defined. Unix permissions are the current primary access boundary; TCP must
  be explicitly configured and should be treated as trusted-network only.
- Operation waiting is exposed through polling/events but the CLI does not yet provide a convenience `--wait` policy.
- Retired log channels are bounded individually but do not yet have a global retention/count policy.
- A listener change whose new wildcard bind conflicts with a retained concrete bind is rejected rather than briefly
  dropping the old listener to make the bind possible.
- Manager logging setup, process title, service integration, and final amalgamated artifact remain deployment-phase
  work.
- Next is health/dependency completion: typed probe state/facts/effects, fdio TCP/HTTP probes, owned command probes, log
  activity probes, readiness propagation, and deterministic recovery tests.
