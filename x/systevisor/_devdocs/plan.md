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

- Implement startup/readiness/liveness roles and process/TCP/HTTP/command/log/composite probes.
- Complete dependency propagation and compose-like foreground collection behavior.

## Phase 7: deployment and artifact

- Finish continuous amalgamation, PID 1 behavior, daemon compatibility, systemd/launchd opaque integration, process
  title updates, and realistic Docker scenarios.

## Phase 8: schedules and platform capabilities

- Add oneshot tasks, cron triggers, atomic JSON schedule state, socket adoption, resource sampling, cgroup v2, and
  optional namespace configuration.

## Phase 9: self-update

- Implement candidate probing, freeze, final snapshot, FD inheritance, in-place exec, rehydration, validation, and
  failure reporting.

Each phase updates a chronological dev journal, runs focused tests, runs manual Ruff and mypy over `x/systevisor`, and
is committed only after the required repository checks pass.
