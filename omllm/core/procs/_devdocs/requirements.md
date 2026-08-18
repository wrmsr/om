# Requirements & decisions

## Asked for (user, 2026-08-17)

- All the launch/management customization of the stdlib `subprocess` module (and more: gosu-like privilege drop,
  rlimits, deathsig, session/group control) — through a uniform path.
- Stream input and output to LLM sessions — in practice *batched*: the model reads output via cursor-based polling
  with a wait window; the UI gets live events.
- Safe, scoped teardown — graceful (SIGTERM → grace → SIGKILL → hard timeout), on error, on timeout, on
  cancellation. Scopes: single tool call, an LLM turn, background across turns, agent lifetime (MCP servers),
  ui lifetime (ACP server / worker mesh). Same manager code for all.
- Zero tolerance for resource leaks / zombies. **NEVER signal a pid/pgid we don't provably own** — the pid must be
  "locked" (unreapable by anyone, including asyncio internals) at the moment of signaling.
- Eventually remote processes: `docker` CLI first (dev containers from `omdev/dockerdev`), `ssh` with a shared
  master; later possibly an in-container lite/amalgamated om agent.
- Async interface; a dedicated `Asyncio` impl (may couple deeply to asyncio, all 3.14 features), asyncio quarantined
  inside it. Anyio ignored. A threads-backed sync impl with the same async interface is future room-for-expansion.
- No global state, not even hidden singletons; injector-instantiated; graceful teardown and re-instantiation.
- No `os.fork` ever (threads exist). `omcore.os.forkhooks` available if ever needed.
- Output spool must be *frameable* to LLMs: out-of-band info (truncation, dropped bytes, spill path, exit) so a
  tool can phrase things distinguishably from process output. Rendering policies pluggable, day 1: raw,
  arrival-merged, tagged lines with fixed-width timestamps + `fd=` tags + "resumption timestamp" injection after a
  configurable gap. Default: separate pipes, arrival-interleaved.
- Memory ring + spill file, default cap, cap `None`-able.
- Pipes first; PTY immediate follow-up; tty/tmux-style controllable subprocesses on the far radar (vt100 emulator
  exists in `omcore/term/vt100`) — keep spool records raw bytes.
- Every local spawn goes through a stdlib-only python **spawn shim** (user chose shim-only from day 1).
- Policies as `TypedValues` families (`ProcOption`).
- Stuck processes (ignore SIGKILL past hard timeout): abandon + log + event by default; `on_stuck='raise'` option.
- Location: `omllm/core/procs`. Tool-call scope goes on `ToolContext` for now (turn/tool DI scopes come later).
- Multiprocessing: not avoided if genuinely best; not the focus. A demo for python children can come later.
- Keep `_devdocs` up to date (this dir).

## Explicitly out of scope for phase 1

Agent/tool integration (phase 2), background `process_*` tools (3), sandbox/ulimit transforms (4), PTY (5),
docker/ssh targets (6). See `design.md` for the phase list.
