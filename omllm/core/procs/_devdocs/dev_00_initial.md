# dev 00 — initial build (2026-08-17)

## Goal
Land phase 1: a tested, injector-bindable `AsyncioProcessManager` under `omllm/core/procs` per `design.md`.

## Plan of attack
1. `types/` (specs, options, states, events, errors, ids)
2. `spool/` + tests
3. `_spawn/shim.py` + `launch/` + tests
4. `scopes/`, `handles.py`, `manager.py`
5. `asyncio/` impl + tests
6. `inject.py` binding helper, `__init__.py` exports, demo, `make fix check`

## Journal
(appended below as work proceeds)

### types + spool landed
- `types/`: `ProcessSpec`/`ProcessStdio` (channels as literals or int fds; `env=None` = inherit, `{}` = clean),
  `ProcOption` TypedValues (`TerminationPolicy`, `SpoolPolicy`, `SessionMode`, `Credentials`, `Umask`, `Rlimit`,
  `Deathsig`, `RunTimeout`, `Tag`, `PassFd`) with `layer_options()`; states/events/errors/ids.
- `spool/`: framed stream (`frames.py`), memory-suffix + spill-prefix storage (`storage.py`), `OutputSpool` with
  `read_available` / `read(cursor, wait=, max_bytes=)` / `subscribe` (`spool.py`), renderers (`render.py`).
  `read(wait=)` semantics chosen: *collect for the window*, returning early only on end-of-output or `max_bytes` —
  the codex `yield_time_ms` shape, batches naturally for a polling model.
- Gotcha: `procs/types` shadows stdlib `types` **only** if you run python with cwd = the procs dir (sys.path[0]).
  Same precedent as `omllm/llm/types`. Always run from repo root.
- Gotcha: forgot `procs/__init__.py` at first -> "relative import beyond top-level package".
- Tests: `tests/test_spool.py` (7) green.
