# Development 15: API bind opt-in, reactor error hook, and scheduler loose ends

## Intent

Four follow-ups from the audit, all small: the unauthenticated control API should not be bindable beyond loopback by
accident, the fdio manager should use the error hook its handlers already declared, and two scheduler findings left
over from Development 14 had simple fixes.

## Findings and changes

- The control API has no authentication and a non-loopback `tcp_host` was accepted silently. It is now rejected with
  `remote_api_not_allowed` unless `api.allow_remote` is set. Loopback is decided from the text alone - a literal
  loopback address or the name `localhost` - so validity never depends on a resolver. An opt-in rather than a warning,
  because the compile pipeline rejects on any diagnostic and has no channel for non-fatal ones.
- `FdioHandler.on_error` existed and nothing called it. The omcore fdio manager now passes whatever a handler callback
  raises to that handler's `on_error`, and the default implementation re-raises, so a handler that does not override
  it behaves exactly as before. Systevisor is the manager's only consumer.
- That made five dormant `on_error` overrides live, written before anything could call them. Three of them would have
  turned a failure in a handler that drives the engine into a silently closed handler - signal handling lost, an exec
  handshake never delivered, an exit observed twice - and were removed so those failures stay fatal. The output pipe
  handler now contains only a failed read. The health connect handler already did the right thing.
- Control connections use the hook instead of the wrapper added in Development 13.
- A `schedules.json` that could not be loaded failed the cold start, so a damaged convenience file stopped every unit.
  It is now moved aside to `schedules.json.damaged`, reported, and schedules begin again from the present.
- A start or restart operation waited on instance state, and an instance whose run dies after reaching `running` is
  already on its way back up by the time anyone looks, so the operation never finished and - under `concurrency: skip`
  - suppressed its schedule forever. Restart backoff made this more reachable, since such a unit no longer goes fatal.
  The control service now fails the operation when a run it is waiting on exits unexpectedly from `running`.

## Deliberately not changed

- An operation blocked on a dependency that never becomes ready, or on readiness that never arrives, still has no
  deadline. That needs a policy for how long an operation may wait, not a fix.
- The scheduler, resource observer, and self-update handlers do not override `on_error`: a failure in them is still
  fatal rather than degrading to a manager without schedules or samples.
- Cron day fields beginning with `*/N` still follow the plain either-matches rule rather than Vixie's.
- Stop propagation from a dependency to its dependents remains absent, pending a decision on its shape.

## Verification log

- The new fdio manager test fails against the previous manager: a contained handler's failure used to abort the poll
  before the other handler was serviced. omcore's fdio, pipeline driver, and HTTP server suites pass unchanged.
- Live: a `0.0.0.0` bind is rejected at `config-check` and accepted with `allow_remote`; a manager cold-started over a
  truncated `schedules.json` starts, logs the discard, and leaves `schedules.json.damaged`; an abandoned half request
  and an interrupted event follower leave the manager serving.
