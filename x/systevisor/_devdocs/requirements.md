# Requirements

## Core lifecycle

- Manage long-running services, oneshot tasks, replica instances, and named collections.
- Preserve Supervisor-equivalent lifecycle states: stopped, starting, running, backoff, stopping, exited, fatal, and
  unknown.
- Keep desired state, lifecycle state, readiness/health, and configuration generation distinct.
- Support explicit dependencies and ordering. Hard requirements, soft wants, and ordering must not be conflated.
- Reconcile an atomic desired snapshot with minimal disruption. Unchanged instances remain running.
- Classify configuration fields as live-update, restart-required, control-plane-only, or handled by an explicit unit
  reload action.

## Process and signal safety

- Operate single-threaded and use deliberate `os.fork`/`os.execve`, permitting controlled pre-exec customization.
- Resolve executable, argv, credentials, groups, environment, cwd, limits, and FD topology before `fork` wherever
  possible.
- Report child setup/exec failure over a close-on-exec status channel.
- Never expose a signaling API accepting a naked PID or PGID.
- Signal only through a live ownership lease which prevents reaping for the duration of delivery.
- Use pidfds where available and fail closed when ownership cannot be proven.
- Permit process-group signaling only for an isolated session owned by the run.
- Reap PID 1/subreaper adoptees but never signal unknown adoptees.
- Support configured forwarding, rewriting, graceful timeout, and escalation without requiring dumb-init.
- Support gosu-equivalent UID, GID, supplementary-group, HOME, and direct-exec behavior.

## Configuration

- Read JSON, TOML, and goyaml-backed YAML.
- Compose deterministic file and directory sources with provenance and strict duplicate handling.
- Validate complete candidates before changing active state.
- Provide offline check/render and active diff/reload operations with structured diagnostics.
- Retain the active snapshot on a rejected live reload.
- Fail loudly and nonzero on invalid cold start; persist diagnostics when a bootstrap state directory is available.
- Persist last-known-good normalized snapshots, without silently booting them by default.
- Provide direct equivalents for all meaningful fields currently exposed by `x/supervisor/configs.py`.
- Keep strings literal by default. Later Minja templating must be explicitly selected and resolved during candidate
  compilation.

## I/O, logging, and events

- Use fdio and `omcore.io.pipelines` without asyncio or worker threads.
- Capture stdout and stderr independently or merged according to configuration.
- Drain child pipes independently of slow consumers.
- Provide raw-byte bounded back-buffers with monotonic offsets and truncation detection.
- Support rotating file sinks and optional journald/syslog adapters.
- Keep manager diagnostics in `omcore.logs`; do not force child bytes through ordinary log records.
- Publish immutable typed events with epoch, sequence, timestamps, and relevant unit/instance/run identity.
- Offer bounded replay and NDJSON HTTP streaming with explicit slow-client policy.

## API and operation

- Expose versioned JSON-over-HTTP, using a Unix socket securely by default and optional TCP explicitly.
- Express API objects as dataclasses marshaled through lite marshal.
- Make the CLI a client of the same API.
- Represent long-running control requests as operations observable through status/events.
- Support compose-like foreground execution of a selected collection.
- Run as an opaque systemd or launchd service without exposing managed units to either manager.
- Run correctly as PID 1 in a container.

## Health and scheduling

- Keep startup, readiness, and liveness checks distinct.
- Support process, TCP, fdio HTTP, transient command, log-activity, and composite probes.
- Provide thresholds, intervals, deadlines, and configurable recovery actions.
- Build calendar scheduling over the same deadline service, with explicit missed-run and persistence policy.
- Begin with replaceable atomic-JSON persistence; add SQLite only if stronger history/claim semantics justify it.

The initial implemented calendar surface is classic five-field cron in UTC. Named civil timezones remain deferred
because stock Python 3.8 does not guarantee either `zoneinfo` or an installed IANA timezone database.

## Testing and deployment

- Test policy through a manual clock and fake drivers without sleeps, threads, sockets, or subprocesses.
- Keep a small real POSIX contract suite for fork, exec, wait, signal, session, and FD behavior.
- Provide an opt-in Docker harness which creates and always removes one temporary container per test.
- Synchronize container scenarios through structured checkpoints rather than arbitrary sleeps.
- Generate one self-contained source artifact and smoke it under CPython 3.8 from early development onward.
- Follow lite syntax and globally collision-safe naming throughout.

## Eventual self-update

- Register every owned FD/resource with stable identity and explicit exec inheritance policy.
- Serialize versioned engine/resource state without runtime object references.
- Probe candidate code in a non-owning process, freeze mutation and I/O, then replace the manager with `exec`.
- Preserve managed child relationships, pipes, back-buffer state, listeners where selected, and process identity.
- Validate rehydrated resources against the live OS and fail closed on ambiguity.
