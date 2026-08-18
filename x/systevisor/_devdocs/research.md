# Research notes

## `x/supervisor`

The complete non-generated implementation and tests were reviewed before beginning Systevisor. The experiment added
an `omcore.lite.inject` composition root and began using fdio/HTTP pipeline pieces, but preserved Supervisor's central
runtime structure:

- the loop polls with a fixed one-second timeout and scans all process objects;
- process objects mix policy, wall-clock access, state mutation, PIDs, pipes, logging, and spawning;
- SIGHUP tears down and reconstructs the injector rather than reconciling a candidate snapshot;
- configuration comparison is process-group-granular;
- logging and event streaming remain incomplete; and
- integration tests launch an entire supervisor subprocess and coordinate with sleeps and HTTP polling.

Its dataclasses remain the checklist for compatibility. Its TODO identifies dynamic updates, logs, richer HTTP,
events, scheduling, serializable state, self-update, an explicit `step()`, injected signals, and sleep-free tests. In
Systevisor these are treated as consequences of one missing engine/runtime boundary rather than separate patches.

## Relevant omcore foundations

- `omcore.lite.inject` provides conservative constructor injection, singleton bindings, arrays, factories, scopes,
  and overrides. Systevisor will use it at stable composition boundaries, not to turn configuration into a mutable
  injector graph.
- `omcore.lite.marshal` handles dataclasses, enums, mappings, and sequences. It is suitable for configuration, API
  objects, and versioned state DTOs. Runtime objects and callbacks must never enter serialized state.
- `omcore.configs.formats` switches among JSON, TOML, YAML, and INI loaders. Systevisor will select JSON/TOML/YAML and
  construct an atomic multi-source snapshot above them.
- `omcore.io.pipelines` has synchronous message flow, lifecycle, flow control, completion, and scheduling. Its fdio
  driver handles nonblocking sockets and partial I/O. Its pure driver supplies manual time and deterministic transport
  input/output, making it the preferred HTTP protocol test driver.
- `omcore.io.fdio.FdioManager` already selects the earliest handler deadline. Its real clock will eventually need an
  injectable seam for completely controlled reactor tests.
- `omcore.logs`, `omcore.os.journald`, and `omcore.os.setproctitle` provide manager diagnostics and platform
  integrations. Child output will use a separate raw-byte path rather than ordinary Python logging records.
- `omcore.text.minja` is lite and compiles a small Jinja-like syntax to Python. It supports expressions, statements,
  loops, and conditionals. It is not a sandbox and will be exposed only through explicit trusted template values.

## `omcore.daemons`

The non-lite daemon package was reviewed as separate prior art and will not be imported or modified for Systevisor.
Useful ideas include:

- separation of process existence, launch completion, and application readiness;
- immutable external-child configuration;
- structured per-launch UUID identity;
- startup reporting channels;
- pidfile inode/lock identity and replacement-aware waiting; and
- independent sync, asyncio, and fdio adapters over protocol cores.

Its child supervision is threaded, based on `subprocess.Popen`, and signals a stored PID/PGID directly. That is not
compatible with Systevisor's single-threaded runtime or ownership guarantee. Its external-daemon stopper is more
relevant: on Linux it relates a locked pidfile owner to a pidfd before signaling, while its Darwin/lsof route retains a
documented PID-reuse race. Systevisor can be stricter for its own direct children by remaining their sole waiter.

## Upstream behavior retained or rejected

Supervisor's public lifecycle states and retry semantics are familiar and useful. Internally they need orthogonal
desired state, health/readiness, configuration generation, and run generation. Supervisor's `RUNNING` means survival
through `startsecs`, not application readiness.

Supervisor distinguishes config reread/update from SIGHUP, but update still restarts affected programs and its core
comparison is group-oriented. Systevisor will compile and validate an entire candidate, classify changes by field,
and reconcile individual stable instances.

Supervisor's subprocess event-listener protocol, XML-RPC surface, HTML interface, and persistent client connections
are deliberately excluded. Typed in-process events and bounded HTTP JSON streams replace them.

## Process identity conclusion

For a direct child, the parent owns the wait right. An exited child retains its PID as a zombie until reaped, which can
serve as a portable identity pin if all waiting is centralized. Linux pidfds strengthen this and provide an
identity-safe individual signal path. Safe group signaling additionally requires a session created for the owned run;
the unreaped session leader pins the numeric SID/PGID until group cleanup is complete. Adopted unknown descendants are
reap-only.
