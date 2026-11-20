# Overview

LLM code.

# Notable packages

- A conspicuously [pi-mono](https://github.com/badlogic/pi-mono/)-shaped LLM toolbox:
  - **[llm](https://github.com/wrmsr/om/blob/master/omllm/llm)** - A general purpose LLM backend toolbox.
  - **[agent](https://github.com/wrmsr/om/blob/master/omllm/agent)** - A headless general purpose agent built on `llm`
    with tools.
  - **[ui/tui](https://github.com/wrmsr/om/blob/master/omllm/ui/tui)** - A TUI for the agent harness (runnable via
    `om llm`).
  - **[ui/evals](ui/evals/README.md)** - Coding-agent evals with Docker and Linux Landlock runtimes, runnable via
    `om llm evals`.

# Scheduled prompts

Save a job with `om llm jobs add`. A job has a working directory, a prompt, and either an interval such as `--every 1h`
or a UTC time such as `--daily 09:00`. The working directory defaults to where you add it. Use `--model` to select the
model for the job. An optional `--input` at the end supplies a fixed command and its arguments. The worker runs it in
the job's directory and gives its output to the model. The model gets a fresh agent session with no tools.

```sh
om llm jobs add git-check 'Flag unusual commits from the last day. Explain what looks unusual.' \
    --daily 09:00 -C /path/to/repo --input git log --since=24.hours --stat
om llm jobs run git-check
om llm jobs list
om llm jobs runs
```

- **Checkout.** Set `OM_HOME` to the checkout's `.om` and pass `--jobs` to the default TUI. In PyCharm, run the
  `omllm.ui` module with `--jobs`. The worker runs on the TUI's asyncio loop and stops when the TUI exits.
- **Installed CLI.** Run `om llm jobs start` to detach a worker and `om llm jobs stop` to stop it. `om llm jobs serve`
  runs the worker in the foreground for a user service. The worker exits when it detects removal or replacement of
  its installation files. If `uvx` selects a different cached environment and leaves the old one on disk, stop the
  old worker before starting the new one. `start` is explicit and lasts until stopped, including after the TUI exits.

Each `OM_HOME` has its own `state/llm/jobs.db` and one worker. The worker runs one job at a time and collapses missed
occurrences into one run. `jobs run` requests an immediate run while preserving the cadence. An interrupted run is
recorded and the next scheduled occurrence stays in place.

The default TUI shows new findings and failures once after the current turn finishes. If the model returns `NO_ALERT`,
the run is recorded quietly. `jobs runs` shows recent runs and their session IDs. Use `om llm --resume SESSION_ID` to
open a saved job transcript under the same `OM_HOME`.
