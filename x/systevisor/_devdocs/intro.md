# Systevisor

Systevisor is a greenfield, single-threaded POSIX process manager for CPython 3.8 and newer. It is intended to run in
the foreground during development, as PID 1 in a container, or as one opaque service owned by systemd or launchd. Its
deployable form will be one amalgamated, third-party-dependency-free Python source file.

The architectural center is a deterministic reconciliation engine surrounded by an operating-system reactor. The
engine owns policy and serializable state. Injected drivers own clocks, file descriptors, child creation, signal
delivery, process waiting, health probes, storage, and transports. Most behavior can therefore be tested in-process by
advancing a manual clock and exchanging facts and effects until the engine becomes quiescent.

Systevisor is informed by Supervisor and by the earlier `x/supervisor` experiment, but is not a continuation or port
of either implementation. Supervisor's useful external vocabulary and configuration capabilities are requirements;
its object graph, polling loop, reload mechanism, event protocol, and test architecture are not foundations here.

## Project promises

- POSIX CPython 3.8+ with Linux and Darwin as primary platforms.
- A single thread and deliberate `fork`/`exec` child setup.
- Atomic configuration candidates and minimally disruptive reconciliation.
- Strong, fail-closed process ownership: no signaling of a naked or unowned PID/PGID.
- Typed, replayable internal events and streaming JSON-over-HTTP.
- Raw stdout/stderr capture with bounded back-buffers and rotating sinks.
- Explicit dependency, readiness, health, restart, and shutdown policy.
- Day-one resource/state rules that permit future in-place `exec` self-update.
- Literal configuration strings by default, with explicit trusted Minja templates later.

## Development records

The files in this directory are durable handoff material. `requirements.md`, `research.md`, `design.md`, and `plan.md`
describe the current intended system. `dev_NN_*.md` files are chronological working journals and should record what
was attempted, what changed, verification performed, surprises, and the next expected work.
