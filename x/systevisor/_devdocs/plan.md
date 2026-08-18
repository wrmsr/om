# Plan

## Phase 0: contracts and guardrails

- Create the lite package and durable development documentation.
- Enforce globally unique amalgamation-safe names with an AST test.
- Confine process-control syscalls with an AST test.
- Establish Python 3.8 import/testing commands.

## Phase 1: configuration and domain model

- Add stable identities, nested configuration dataclasses, diagnostics, provenance, and normalized desired snapshots.
- Load individual JSON/TOML/YAML files and deterministic directories.
- Reject duplicate definitions unless a future explicit overlay mechanism is selected.
- Implement offline check/render foundations and thorough pure tests.

## Phase 2: deterministic engine

- Add commands, facts, effects, events, operation records, runtime state, dependency graphs, and reconciliation.
- Drive transitions through a manual clock and fake effect executor until quiescent.
- Cover start, success, early exit, backoff, fatal, stop, escalation request, expected/unexpected exit, and config
  add/change/remove behavior without real processes.

## Phase 3: process kernel

- Add resource registry, precomputed child exec plans, error/status pipes, fork/exec driver, owned process handles,
  anti-reap signal leases, centralized waiting, and Linux/Darwin implementations.
- Add narrowly scoped real boundary tests and the opt-in Docker harness skeleton.

## Phase 4: reactor, output, and event journal

- Connect effects to fdio, signals through a wakeup pipe, and child output through raw-byte fanout.
- Add bounded rings, offsets, rotating files, manager log adapters, typed event envelopes, replay, and subscriber queues.

## Phase 5: control plane and reload

- Add the Unix-socket HTTP server, JSON routes, NDJSON streams, operations, API client, and CLI.
- Connect configuration attempts to atomic validation and process-level reconciliation.

## Phase 6: health, dependencies, and collections

- Complete: startup/readiness/liveness roles and process/TCP/HTTP/command/log probes, including owned command children
  and readiness-driven dependencies.
- Complete: collection desired claims and aggregate state, releasable transitive dependency claims, `stop_together`,
  readiness-aware operations, state/API visibility, and compose-like foreground collection runs.
- Deferred pending a concrete configuration contract: composite probe expressions.

## Phase 7: deployment and artifact

- Complete: continuous checked-in amalgamation and isolated Python 3.8 artifact smoke tests.
- Complete: manager bootstrap, daemon mode, locked pidfile, resource limits, identity reduction, process title,
  rotating manager logs, optional journald, Linux subreaper/PID 1 behavior, and reap-only unknown adoptees.
- Complete: systemd notification and opaque systemd/launchd templates.
- Complete: an opt-in, one-container-per-test Docker harness with FIFO JSON checkpoints and unconditional cleanup.

## Phase 8: schedules and durable time state

- Complete: five-field UTC cron/calendar triggers over fdio deadlines, wall-jump rechecks, missed-run/concurrency
  policy, ordinary scheduled control actions, events/API state, and replaceable atomic-JSON persistence.
- Deferred: named/non-UTC timezones until a self-contained Python 3.8 timezone-data policy is selected.

## Phase 9: observation and platform capabilities

- Add procfs/Darwin resource sampling, cgroup v2 delegation, optional namespace configuration, and socket adoption.

## Phase 10: self-update

- Implement candidate probing, freeze, final snapshot, FD inheritance, in-place exec, rehydration, validation, and
  failure reporting.

## Phase 11: hardening and release

- Close the Supervisor config-compatibility matrix, broaden fault injection and platform contracts, finalize operator
  documentation, and exercise release artifacts across supported interpreters and hosts.

Each phase updates a chronological dev journal, runs focused tests, runs manual Ruff and mypy over `x/systevisor`, and
is committed only after the required repository checks pass.
