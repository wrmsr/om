# dev 04 — background process_* tools (phase 3) (2026-08-18)

The LLM can now run and drive long-lived background processes. Five tools in `omllm/agent/exec/tools/process.py`,
all operating on the session process scope (`ToolEnvironment.processes`):

- **process_spawn** — starts a bash command in the background (interactive: stdin/stdout/stderr piped), returns a
  short id (`p1`, ...). Permission-checked like `bash` (ExecPermissionTarget). Does not wait.
- **process_read** — cursor + wait-window read. Returns the output since `cursor` plus a status line ending
  `next_cursor=N`; the model passes N back to continue. Uses the new `OutputSpool.poll()` (long-poll: returns on the
  first available output, or after `wait_s`, or on exit) - responsive, not whole-window batching.
- **process_write** — write to stdin, optional `eof`.
- **process_kill** — graceful `aclose()` (SIGTERM -> grace -> SIGKILL -> reap), or `force` for immediate SIGKILL.
  Also the way to reap/clean up an already-exited background process.
- **process_list** — id / pid / state / rc / elapsed / argv for everything live in the scope.

## Notes / decisions

- Added `OutputSpool.poll(cursor, *, timeout, max_bytes)` next to `read(...)`. `read` collects for the whole window
  (codex `yield_time_ms` shape); `poll` returns as soon as there is output (or end/timeout). The tool wants `poll` -
  a model following a process shouldn't eat the full `wait_s` when a line is already there. `read` stays for
  batch-collect callers.
- Surfaced `created_at` on the `ProcessInfo` interface (was impl-only) for `process_list` elapsed.
- Background processes live in `ctx.env.processes` (= `manager.root`, the session scope) - no per-turn/per-tool child
  scopes yet (those wait on the DI-scope work). So "background" == session lifetime; the manager reaps everything on
  close. An exited-but-unread background process stays a held zombie (visible in process_list as `exited`) until
  `process_kill` reaps it or the manager closes - cheap, and it keeps the id valid for final reads.
- `bash` stays foreground-only; backgrounding is the explicit `process_spawn` path (no `run_in_background` flag).
- Bound in `ui/bare/tools.py` under `--exec`, exported from `omllm/agent/__init__.py`.

## Tests

`agent/exec/tools/tests/test_process.py`: interactive cat (spawn/list/write/read-with-cursor/kill/not-found),
follow-an-exiting-process loop (read until `exited (rc=4)`), and the ToolClass reflect path via `.tool().executor()`
incl. the empty-params list tool.

## Deferred (still)

- Human `/ps` slash command (process_list is the LLM-facing equivalent; a human command is a small ui add).
- Per-tool-call child scopes + reparent-on-background (the "adopt into an ancestor" flow) - lands with DI scopes.
- Plain-text output dump for the model to `read` a huge process's full log (spill file is framed).
