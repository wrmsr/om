# dev 03 — agent integration (phase 2) (2026-08-18)

The agent's command execution now runs on the process manager. `bash` and `ripgrep` spawn through a `ProcessScope`,
honor their `timeout_s`, and return combined stdout+stderr with exit-code / timeout framing. `make fix gen check`
clean; full `omllm` suite 417 passed / 20 skipped.

## What changed (in `omllm/agent` and `omllm/ui/bare`)

- `agent/exec/ops.py` rewritten over `omllm.core.processes`:
  - `ExecOps.exec(scope, params)` - takes the `ProcessScope` to run in (per the "put the scope on the tool context"
    decision). `ProcessesExecOps` spawns a `ProcessSpec`, `wait(timeout_s)`, `aclose()` (reaps; kills the group on timeout),
    then reads the spool.
  - `ExecResult` gains `timed_out` and `truncated`; keeps `rc`/`stdout`/`stderr` (split by spool fd 1/2).
  - `format_exec_output(result, *, timeout_s=, max_chars=30_000)` -> model-facing text: stdout then stderr, head+tail
    truncation for very large output, and `[exit code N]` / `[command timed out ...]` notes as out-of-band framing.
  - `LocalExecOps` (the old `create_subprocess_exec` one-shot) is gone; `ProcessesExecOps` replaces it.
- `agent/types/tools.py`: `ToolEnvironment.processes: processes.ProcessScope | None`. This is where the tool-call
  process scope lives *for now* - it will move onto a real turn/tool DI scope later, but nothing here waits on that.
- `agent/exec/tools/bash.py` + `.../ripgrep/tools/ripgrep.py`: pull the scope from `ctx.env.processes`, pass `timeout_s`
  through, and render via `format_exec_output` (so stderr and the exit code now reach the model - previously bash
  returned stdout only and dropped stderr/rc).
- `ui/bare/tools.py`: under `--exec`, binds the process manager (`processes.bind_process_manager()`, an async-managed
  singleton) and `ProcessesExecOps` -> `ExecOps`.
- `ui/bare/main.py`: sets `ToolEnvironment(cwd=..., processes=(await injector[processes.ProcessManager]).root)` when
  exec is enabled. The manager is started on provision and closed on injector teardown - no globals.

## Proven end-to-end

- `agent/exec/tests/test_ops.py`: `ProcessesExecOps` basic / nonzero-exit / timeout (partial output preserved, killed);
  `format_exec_output` rendering.
- `agent/tests/test_exec_agent.py`: drives the real `Agent` + `TurnLoop` with a **scripted backend** that emits a
  `bash` tool call. The whole path runs - scripted turn -> loop -> BashTool -> ProcsExecOps -> real subprocess ->
  stdout/stderr/exit-code back as a `ToolResultMessage` -> final turn -> no leftover processes. This is the "make it
  real" validation (a live interactive UI run needs an LLM key, so the scripted backend stands in).

## Deliberately deferred

- **`/ps` command**: deferred to phase 3. Foreground execs complete and are reaped the instant the tool returns, so
  `/ps` would almost always show an empty list today. It becomes useful once background processes exist.
- **Per-tool-call child scopes**: not needed yet. Foreground `run()` reaps its own process (and sweeps its group,
  killing `cmd &`-style stragglers), so nothing lingers between calls. A per-call child scope is a phase-3 concern
  (backgrounding = adopt into an ancestor before the call scope closes).
- **Tool-execution events**: already added to `turns/loop.py` by the user (ToolExecutionStart/EndEvent) - untouched.
- **Truncation spill reference**: `format_exec_output` notes truncation but does not point at the spool spill file
  (it's a framed binary, not cat-able, and is unlinked when the manager closes). A plain-text `dump()` sink for the
  model to `read` is a future nicety.

## Next

Phase 3 (background + `process_*` tools) or the remote targets (docker/ssh). Background is the natural follow-on: it
makes per-call child scopes, `/ps`, and the cursor-based `read_output(wait=)` polling all pay off.
