# Mini agent eval

A small coding-agent evaluator: one standard-library Python runner, Docker and local runtimes, three starter tasks, and
optional Codex, Claude Code, and Pi adapters. Your own host agent can work against a Docker container or a local trial
workspace.

The runner targets Python 3.11+ on Linux and macOS, including Python 3.14. Docker is the default runtime and requires an
ordinary running Linux Docker daemon: Docker Engine on Linux or Docker Desktop on macOS. The local runtime requires
Linux Landlock ABI 3 or newer, host Git, and a Python interpreter. Neither runtime needs extra host Python packages.
Host Node is only needed for host agents which use it.

## First run

Unpack this directory, enter it, and run:

```sh
python3 -m minieval list
python3 -m minieval check
```

`check` builds the three task images and runs each task twice: once with no changes, then with its reference solution.
It succeeds only when all three starters fail their grading tests and all three reference solutions pass. It requires
no model credentials and makes no model requests. The first image build downloads base images and OS packages.

For a quicker first check:

```sh
python3 -m minieval check --task intervals
```

### Without Docker

From the monorepo root, use its Python launcher and select the local runtime:

```sh
./python -m x.mini_agent_eval.minieval check --runtime local --tasks x/mini_agent_eval/tasks
./python -m x.mini_agent_eval.minieval run --runtime local --tasks x/mini_agent_eval/tasks --agent oracle
```

`check` creates fresh workspaces and a fresh grader for every trial. It verifies that all three starters fail and all
three reference solutions pass. Local processes inherit Linux Landlock rules that permit filesystem writes only in the
trial workspace and its temporary directory. The runner gives them a trial HOME and TMPDIR, and kills the process group
after each command. No Docker socket or model credentials are needed.

The local runtime currently supports task images with `COPY *.py ./` as their sole Dockerfile copy operation, as in the
three included tasks. It copies those Python sources into each workspace and uses the host interpreter and Git. A task
with build-time dependencies or other Dockerfile copy operations needs a local setup implementation before it can run
locally. `local.json` records the host platform, Python version, executable, and Landlock ABI; results retain each task's
content hash. Use the same host toolchain when comparing local runs.

Landlock here restricts **writes**, not reads or network access. A local agent can read host files, including the bundled
reference solutions, so this runtime is suitable for trusted development and wiring checks. Use Docker for isolated
benchmark runs or untrusted agent code. Docker remains the default.

The in-repo `omllm` agent can run with an internally configured scripted backend, without provider keys:

```sh
./python -m x.mini_agent_eval.minieval run --runtime local --tasks x/mini_agent_eval/tasks \
    --task intervals --agent scripted
```

The default script calls `bash` to inspect the workspace and then ends; the grader should report `failed` because no
repair was made. Supply `--script FILE` to replace those turns. The file is a JSON array: each turn has either a `text`
string or a nonempty `tool_calls` array. Every tool call has a `name` and an `args` object. For example:

```json
[
  {"tool_calls": [{"name": "bash", "args": {"command": "pwd"}}]},
  {"text": "Workspace inspected."}
]
```

The adapter builds an `omllm.llm.BackendScript`, injects a `ScriptedImmediateBackend` into the normal `omllm.ui` agent,
and grants its tools access to the trial workspace. This is a deterministic integration control, not an agent score.
`--agent scripted` is available from this monorepo checkout and requires `--runtime local`.

Ordinary runs use `run`:

```sh
python3 -m minieval run --agent oracle
python3 -m minieval run --agent nop
```

The second command is expected to exit 1 because the supplied source is buggy. The first should exit 0.
`oracle` is a reference implementation control, not a model or a useful agent score.

## Your host agent

Supply a host command after `--`. With Docker, the runner starts the task container, then runs your command once per
task, sending a single JSON object followed by a newline to its stdin:

```sh
python3 -m minieval run --agent external --task intervals -- \
    python3 -m your_agent.eval_adapter
```

With Docker, the command runs in the caller's current directory and inherits the caller's environment. The task
container is already running and has a writable Git workspace at `/work`. Its `agent` user owns that workspace. The
request includes:

```json
{
  "task_id": "intervals",
  "container_id": "<running Docker container ID>",
  "docker_executable": "docker",
  "workdir": "/work",
  "user": "agent",
  "instruction": "<complete assignment>",
  "instruction_file": "<absolute host path to the assignment>",
  "container_instruction_file": "/tmp/mini-eval-instruction.md",
  "output_dir": "<absolute host path to this attempt's output directory>",
  "timeout_seconds": 600
}
```

With `--runtime local`, the same external agent contract sends `runtime: "local"` and a host `workdir` path. It does not
send `container_id` or `docker_executable`. The command runs under the local write restrictions and should edit that
workspace directly. It may write extra metrics to the request's `artifact_dir`; the rest of `output_dir` is read-only to
the local agent. The Docker-only example below still expects a container ID.

Your integration entrypoint can load that request and call your existing harness. This is an illustration of the adapter
body; `run_my_agent` is your own function:

```python
request = json.load(sys.stdin)
run_my_agent(
    container_id=request['container_id'],
    instruction=request['instruction'],
    timeout=request['timeout_seconds'],
)
```

Edit files in the given container and return when finished. Exit 0 for normal completion and nonzero for an agent error.
Write logs to stdout/stderr; both are captured in `agent.log`. You may write extra metrics or your native transcript into
`output_dir`. The runner grades the files, so stdout has no required response format. Leave container lifetime to the
runner. Each attempt gets a new container and your entrypoint gets a fresh process.

If your program already accepts command-line arguments instead of JSON, placeholders are available within individual
arguments. The JSON request is still sent to stdin:

```sh
python3 -m minieval run --agent external -- \
    my-agent --container-id '{container_id}' --prompt-file '{instruction_file}'
```

Supported placeholders are `{container_id}`, `{workdir}`, `{instruction_file}`, `{prompt_file}`, and `{output_dir}`.
`instruction_file` is on the host; `prompt_file` is the container path. Arguments are passed directly without an implicit
shell. Unknown braces remain literal.

### Exercise the external interface without a model

The included example reads the JSON request, drives Docker from the host, and installs the known reference fix:

```sh
python3 -m minieval run --agent external -- \
    python3 -m examples.externaloracle --solutions tasks
```

This should solve all three tasks. It deliberately reads the reference solution and exists only to test the integration
contract. Your real agent should use the instruction and the running container.

## Codex, Claude Code, and Pi

Their small Dockerfile overlays install the CLI into the task image. The host runner remains dependency-free. Supply API
credentials through environment variables, then select an adapter:

```sh
# If OPENAI_API_KEY is already exported:
export CODEX_API_KEY="$OPENAI_API_KEY"
python3 -m minieval run --agent codex --task intervals

# With ANTHROPIC_API_KEY already exported:
python3 -m minieval run --agent claude --task intervals

# With a supported provider's API key already exported:
python3 -m minieval run --agent pi --task intervals
```

These commands make real provider requests. The deterministic `check` and `externaloracle` commands do not.

No model is hardcoded. To choose one, append native agent arguments:

```sh
python3 -m minieval run --agent codex --task intervals \
    --agent-arg=--model --agent-arg=YOUR_MODEL_ID

python3 -m minieval run --agent pi --task intervals \
    --agent-arg=--provider --agent-arg=anthropic \
    --agent-arg=--model --agent-arg=YOUR_MODEL_ID
```

Use the equals form when a value begins with `--`. All three adapters accept `--model`; Pi accepts `--provider` as well.
Select explicit models and matching budgets when comparing harnesses.

The adapters use unattended execution inside the disposable container. Codex and Claude disable their interactive
permission prompts there. Claude runs as the non-root `agent` user. API-key authentication is the initial supported
path; host login profiles are not imported.

Agent package versions are pinned in their Dockerfiles. `--agent-version VERSION` overrides the selected package
version. This changes a package version, not a model. The actual installed CLI version is recorded in each trial's
`agent-version.log`.

Additional provider environment variables can be forwarded with repeated `--env NAME`. The runner passes names to
`docker exec`; it does not put secret values in build arguments or command logs. An explicitly requested variable must
exist in the host environment. Only selected variables reach the container's agent process. Use environment variables
for credentials rather than `--agent-arg`.

See [agents/README.md](agents/README.md) for package versions, current Pi naming, exact CLI commands, and source links.

### Another installed harness

Create `agents/myagent/agent.json` and, if installation is needed, `agents/myagent/Dockerfile`:

```json
{
  "name": "myagent",
  "kind": "container",
  "dockerfile": "Dockerfile",
  "command": ["my-agent", "--noninteractive"],
  "stdin": "prompt",
  "user": "agent",
  "env": ["MY_PROVIDER_API_KEY"],
  "required_env": ["MY_PROVIDER_API_KEY"],
  "version_command": ["my-agent", "--version"]
}
```

The example names and flags above stand for your CLI's real interface. The Dockerfile receives `TASK_IMAGE` as a build
argument and must derive from it. It must preserve `/work`, the `agent` user, Git, Python, and the task dependencies.
Use the provided Dockerfiles as examples. Omit `dockerfile` if the CLI is already present in the task image.

`stdin` is either `prompt` or `none`. The assignment is also available at `{prompt_file}` inside the container.
An optional `environment` object supplies fixed, nonsecret environment settings. The `env` list forwards existing host
variables; `required_env` checks mandatory ones. Select the adapter with `--agent myagent` or pass the JSON path.

## Tasks and grading

| Task | Representative work |
| --- | --- |
| `intervals` | Sorting and merging half-open intervals, validation, boundaries, and preserving caller input |
| `lines` | Stateful byte-stream parsing, split delimiters, CRLF, empty lines, and EOF handling |
| `csvtotals` | A library and CLI change involving CSV, exact decimal aggregation, validation, and JSON output |

These are deliberately small authored fixtures, not a representative benchmark score. They include passing visible
tests for existing behavior and separate grading tests for the missing behavior. The instructions fully specify the
requirements checked by the grader.

Each task borrows the basic Harbor directory organization:

| Path | Purpose |
| --- | --- |
| `instruction.md` | Full assignment |
| `environment/Dockerfile` and its build context | Starting source and dependencies |
| `tests/test.sh` and supporting files | Authoritative grading tests |
| `solution/solve.sh` and supporting files | Reference fix, required only for `oracle` and `check` |

There is no task metadata file or reward-file protocol. This is Harbor-inspired organization, not a Harbor-compatible
runner. The current fixed contract is a Linux image with `sh`, `sleep`, `find`, `chown`, Git, an `agent` user, and a
writable `/work`. The supplied images satisfy it. The grader runs `sh /tests/test.sh` as `agent` from `/work`.

`test.sh` must return 0 for success, 1 for a candidate failure, and another exit code for a grader/setup failure.
Both failing assertions and candidate import/syntax errors produce 1 in the supplied unittest graders. The tests are
copied to `/tests` only during grading. The task build context is exactly `environment`, so it excludes tests and
solutions.

A trial starts from the task image and creates an initial Git commit. After the agent finishes or times out, the runner
stops its container and copies `/work` into the run directory. It strips the agent's `.git` metadata, starts a fresh
container from the task image, and replaces its source tree with the submitted snapshot. Deletions survive this process.
The fresh grader's Git metadata is retained to produce `patch.diff`, including new files and agent-committed changes.
The snapshot is the actual graded submission. Only `/work` changes are transferred: dependencies required for grading
must be baked into the task image. The grader has no network and receives no agent credentials or reference solution.

For real repository tasks later, prepare the desired starting tree in `environment/Dockerfile` and provide its tests and
instruction. A dedicated commit/task importer can be added later without changing the external agent protocol.

## Platforms

Linux amd64, Linux arm64, and arm64 Docker Desktop on macOS are equal design targets. The runner uses ordinary Docker
build/create/start/exec/cp/stop/rm commands. File transfers use `docker cp`, with no host bind mounts, host UID mapping,
host binaries, nested Docker daemon, or custom runtime.

By default Docker selects its native platform, respecting the user's existing Docker configuration. The Python and Node
base images publish both Linux amd64 and Linux arm64 variants. Optional agent packages select their Linux native
components during the build. A macOS host runs Linux containers; Darwin agent binaries are not used.

An explicit platform is available when needed:

```sh
python3 -m minieval check --platform linux/arm64
python3 -m minieval check --platform linux/amd64
```

An explicit nonnative platform relies on whatever emulation your normal Docker installation provides. Native execution
does not need emulation. Use the matching platform on each machine for comparable timings.

## Results and options

Each run has a fresh directory under `runs/`. A supplied `--run-id` must not already exist; there is no result reuse or
resume behavior. Repeat task selection and attempt count as needed:

```sh
python3 -m minieval run --agent codex \
    --task intervals --task lines --repeat 2 \
    --timeout 300 --test-timeout 60 --run-id codex-experiment-1
```

Important outputs:

| File | Contents |
| --- | --- |
| `run.json` | Runner invocation settings |
| `docker.json` or `local.json` | Runtime version and platform metadata |
| `setup.log` | Image preparation and Docker operations, or local Git setup |
| `results.jsonl` and `summary.json` | Per-attempt records and outcome counts |
| Per attempt: `request.json`, `instruction.md` | Exact external request and assignment |
| Per attempt: `workspace/`, `patch.diff` | Submitted files and a diff against the starting tree |
| Per local attempt: `agent-artifacts/` | Writable agent metrics and transcript directory |
| Per attempt: `agent.log`, `agent-version.log` | Agent output and installed CLI version, when applicable |
| Per attempt: `verifier.log`, `result.json` | Test output and final outcome |

Results include task-content hashes, agent and verifier elapsed time, return codes, and timeout flags. Docker results
also include concrete image IDs. An agent crash or timeout remains a failed attempt even if its partial changes pass the
tests; `tests_passed` records that separate fact. Outcomes include `passed`, `failed`, `agent_error`, `agent_timeout`,
`test_timeout`,
`grader_error`, `submission_error`, and `infrastructure_error`. Token counts and provider costs are not normalized yet;
native CLI logs and your external agent's extra files retain the material for that next step.

`--timeout` defaults to 600 seconds for the agent, `--test-timeout` to 120 seconds, and `--setup-timeout` to 1800 seconds
per setup command. Agent timing excludes image installation and grading. Trials run serially. Host processes get their
own process group, and timed-out groups are terminated; the task container is then stopped before collecting files.
Containers are removed after each attempt. `--keep-containers` keeps them stopped for inspection. Built images remain
cached in Docker for subsequent runs. This runner does not prune unrelated images or containers.

For local runs, `local.json` replaces `docker.json`. Container images, container IDs, `--platform`, and
`--keep-containers` do not apply. A local agent process receives PATH, HOME, TMPDIR, PYTHONPATH, the trial paths, and
variables explicitly forwarded with `--env NAME`. The runner kills its process group when it exits.

Exit status is 0 when every requested attempt meets its expected result, 1 for completed runs with a failed expectation,
2 for configuration/setup errors, and 130 for an interrupt. For `check`, the expected no-op result is `failed`.

## Verification included with this starting point

Run the local standard-library tests with:

```sh
python3 -m unittest discover -s tests -v
```

Those tests exercise fixture behavior, runner helpers, local write restrictions, snapshot transfer, and the scripted
`omllm` adapter without a Docker daemon. The live Docker integration check is `python3 -m minieval check`, and the
external-interface integration check uses `examples.externaloracle` above. Both are intentionally model-free.

For the extended Docker tests, including committed/staged/new/deleted file transfer and container cleanup:

```sh
MINIEVAL_DOCKER_TESTS=1 python3 -m unittest tests.test_docker -v
```

Those tests accept optional `MINIEVAL_DOCKER` and `MINIEVAL_PLATFORM` selectors. Explicitly enabling them with an
unavailable Docker engine fails the tests rather than silently skipping them.

In this development container, `check --runtime local` passed all six controls: three starter failures and three
reference successes. A scripted `omllm` tool call installed the reference fix for `intervals`, and its trial passed
grading. Docker image builds, live container execution, arm64 execution, and authenticated model calls remain untested
here because the Docker socket and provider credentials are unavailable.

The next useful addition is a real repository task importer. The current version keeps the core loop small: task setup,
agent invocation, snapshot transfer, independent grading, and files on disk.
