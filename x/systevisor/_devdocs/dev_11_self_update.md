# Development 11: self-update and state handoff

## Intent

Phase 10 implements the architectural requirement that a Systevisor manager can replace its own source without
terminating managed services or accidentally closing their manager-side descriptors. This is not a restart disguised
as an update. The manager PID, wait rights, captured-output pipes, pidfds, pidfile lock, activation sockets, engine
state, log back-buffers, operation history, and event cursor must cross one in-place `exec`.

The update is deliberately narrower than an arbitrary checkpoint. It only freezes at a stable reconciliation point.
An update request is rejected while a service is spawning/stopping, a health check is in flight, an ordinary control
operation is pending, a signal lease is held, or an internal child exists. That contract makes the handoff auditable:
the old process never serializes an ambiguous half-effect and the new process never guesses whether a syscall ran.

## Planned protocol

1. Validate and SHA-256 pin an explicitly supplied, regular source file.
2. Atomically write a probe request containing the candidate digest and active configuration.
3. Spawn the candidate as an internally owned Systevisor child. The candidate imports itself, validates the request,
   configuration, handoff schema, and its own source digest, then atomically writes a result and exits.
4. Observe and reap that child only through `SystevisorProcessManager`; timeout termination also requires its signal
   lease. No self-update module may call `kill`, `killpg`, `wait*`, or `subprocess`.
5. After the API response has had a short fdio-driven grace period, enter a single-threaded freeze: do no more polling,
   build the final manifest, inventory and `fstat` every descriptor, write and fsync it, then clear `FD_CLOEXEC` only
   on that exact inventory.
6. `execve` the current Python executable with the candidate script's hidden resume entry point. If `execve` fails,
   restore the original descriptor flags exactly, fail the operation, and continue the old reactor.
7. The candidate validates the manifest and descriptor identities before installing any ownership. It reconstructs
   configuration/engine state, wait rights, output readers and log rings, cgroup bookkeeping, activation sockets,
   pidfile locking, events/operations, deadlines, observers, scheduler, signals, and HTTP listeners.
8. Only after reconstruction succeeds does it remove the handoff file and complete the pending update operation.
9. If candidate reconstruction fails, write a small error document and `exec` the digest-pinned previous artifact.
   The previous image validates the same manifest, resumes ownership, and marks the update operation failed.

HTTP listeners and accepted API connections are intentionally not inherited. API clients may reconnect to the same
configured endpoint. Managed-child descriptors are never put in that disposable category.

## Safety invariants

- A preserved PID is accepted only if `waitid(P_PID, ..., WNOWAIT | WNOHANG)` proves the new image still owns the
  direct-child wait right. A live Linux process with a recorded `/proc` birth identity must still match it.
- A preserved signal lease count must be zero. Rehydration cannot manufacture or transfer a lexical signal lease.
- Only the process manager reconstructs process ownership; it remains the only production module allowed to wait or
  signal.
- Every passed FD has a unique semantic owner plus recorded device, inode, file type, and relevant status flags.
  Duplicate inventory entries and descriptor substitution are fatal before the reactor starts.
- Spawn handshakes and non-service children are not checkpointed. Stable services have no exec-error FD.
- `FD_CLOEXEC` changes are transactional in the old image and are restored after an injected/real exec failure.
- The candidate path is digest-pinned once for probing and checked again immediately before exec and on resume.
- The previous source path/digest is pinned in the final manifest and checked immediately before rollback.
- Both running and candidate sources must carry the generated amalgamation markers; package-mode development entry
  points are not falsely advertised as rollback-capable artifacts.
- Manifests are versioned JSON, written mode `0600` by atomic replacement and directory fsync.

## Initial reconstruction scope

The first complete handoff preserves active configuration including removed-but-draining instance specs, engine and
health/deadline state, owned service processes, log rings and pipe readers, bus sequence/journal, operation history,
cgroup run bookkeeping, inherited activation sockets, and pidfile state. Resource samples are intentionally rebuilt
by immediate observation; scheduler time state already has its own atomic durable store. HTTP connections, transient
subscriptions, logging-library handler FDs, and resolver/health sockets are intentionally recreated or rejected as
in-flight work.

## Work log

- Established the stable-point policy and rejected the tempting approach of serializing arbitrary reactor internals.
  Fdio pipeline objects contain callbacks and transient buffers that should not become a compatibility format.
- Chose explicit schema codecs over pickle. A handoff may be supplied to a different source version and therefore
  needs strict, inspectable, bounded input with clear version rejection.
- Chose a managed candidate child rather than direct `fork`/`wait` code in the updater. This keeps the repository's
  sole wait-right authority intact and exercises the same exec-handshake behavior as all other children.
- Chose to keep the update operation pending across exec. The original response is `202`; after reconnect, the same
  operation becomes succeeded in the new image or failed in the old image if exec returns.
- Added explicit snapshot/rehydration support for engine state, config provenance, owned processes, active/retired log
  channels and rings, events, operations, cgroups, activation sockets, and the manager's pidfile capability. Resource
  samples are refreshed, scheduler state continues through its own atomic store, and HTTP endpoints are rebound.
- Candidate probes and probe timeout termination use the existing internally owned process path. No wait or signal
  primitive escaped the process manager, and the source guards continue to enforce that boundary.
- Added a rollback leg rather than treating a failed candidate resume as a fatal one-way transition. The candidate
  never closes inherited resources before invoking rollback; the old artifact revalidates them before adoption.
- The opt-in Docker scenario now performs a successful update and then patches a second candidate to fail exactly at
  resume, proving rollback preserves the manager PID, child, and captured log bytes when a daemon is available.
- Ran a real host artifact update after regeneration. Manager PID `435725`, child PID `435731`, parentage, run ID, and
  the `before-update` stdout ring all remained unchanged; the pending operation completed after reconnect and normal
  reconciled shutdown then exited cleanly.
- Default-interpreter tests passed with 110 tests and two opt-in Docker skips before the final artifact-only guard;
  focused post-guard tests passed 19/19. Python 3.8 unittest discovery passed all 112 then-current tests with three
  environment-dependent skips. Final whole-tree verification is recorded in the next hardening journal.

## Next

- Harden shutdown/cancellation and partial-resume failure paths.
- Complete the Supervisor configuration compatibility matrix and operator/release documentation.
- Run final whole-tree lint, type, default/Python 3.8 tests, generation checks, and artifact smoke tests.
