# Optional in-container agents

Each directory contains an `agent.json` command definition and a Dockerfile that
adds one CLI to the task image. The runner is still standard-library Python;
Node and the agent packages live in the optional agent images.

| Adapter | npm package | Default package version | Authentication |
| --- | --- | --- | --- |
| `codex` | `@openai/codex` | `0.167.0` | `CODEX_API_KEY` |
| `claude` | `@anthropic-ai/claude-code` | `2.1.319` | `ANTHROPIC_API_KEY` |
| `pi` | `@earendil-works/pi-coding-agent` | `1.5.0` | Provider API key |

Pi is the current continuation of the project formerly at `badlogic/pi-mono`.
Its current package is `@earendil-works/pi-coding-agent`.

## Credentials and models

Use API keys for this initial implementation. For Codex, set `CODEX_API_KEY`;
if you already have an exported `OPENAI_API_KEY`, this is sufficient:

```sh
export CODEX_API_KEY="$OPENAI_API_KEY"
```

Claude Code uses `ANTHROPIC_API_KEY`. The Pi adapter forwards whichever of
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `OPENROUTER_API_KEY`
you have set. Select Pi's provider and model explicitly when comparing runs.
The adapter has no fixed required key because different providers use different
variables; Pi reports a missing credential for the selected provider.

The runner's repeated `--agent-arg` option appends arguments to the selected
CLI. For example, `--agent-arg=--model --agent-arg=MODEL_ID` works for all three.
Pi also accepts `--agent-arg=--provider --agent-arg=PROVIDER`; when supplying a
provider, supply its model as well. No default model is baked into these files.
For another Pi provider, pass `--env PROVIDER_KEY_VARIABLE` or add the variable
to the adapter's `env` list, and use that provider's documented model identifier.

The runner forwards environment variables listed in the adapter or supplied
with `--env NAME`.
The runner passes secrets to `docker exec` using `--env NAME`, so values do not
appear in build arguments or the saved command. Agent subprocesses can still
read their inherited environment. Do not pass API keys through `--agent-arg`.
Existing host login directories are not copied into these images.

## Invocation

All adapters consume the task instruction through stdin and stream their native
JSON event logs to stdout. The runner executes them as `agent` in `/work`:

```sh
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -
claude --print --verbose --output-format stream-json --dangerously-skip-permissions
pi --mode json --no-session
```

These settings allow the agent to edit the task and run commands unattended
inside the disposable container. They rely on Docker as the outer execution
boundary. Claude runs as a non-root user; its automatic updates are disabled.
Pi's session is in memory. The runner's `agent.log` retains the native stdout
and stderr needed to inspect a trial.

## Images and platforms

Each Dockerfile derives from `TASK_IMAGE`, installs Node's Debian runtime
libraries (`libatomic1` and `libstdc++6`), copies Node from the matching
`node:22-bookworm-slim` platform, then installs the CLI. The supplied task images
provide the `agent` user and `/work`. Pi requires Node 22.19 or newer, which the
current Node 22 image satisfies.

There is no fixed CPU architecture and no host binary is copied into a
container. Docker resolves the Linux image for the selected platform on Linux
amd64, Linux arm64, and arm64 Docker Desktop for macOS. The npm packages include
Linux x64 and arm64 native components where needed. No privileged container,
custom runtime, or host Node installation is required.

The Dockerfiles accept `AGENT_VERSION` so a CLI version can be pinned or changed:

```sh
docker build \
    --build-arg TASK_IMAGE=your-task-image \
    --build-arg AGENT_VERSION=0.167.0 \
    --tag your-codex-task-image \
    agents/codex
```

The defaults above are explicit package versions, not moving `latest` tags.
Base image tags and transitive npm dependencies can still change. Retain the
built image IDs alongside the recorded CLI version for comparisons; this is a
small starting point rather than a fully locked image supply chain.

## Sources and verification

The install and non-interactive interfaces were checked against primary
sources on 2026-11-06:

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/)
  documents stdin, JSON output, and `CODEX_API_KEY`.
- [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
  documents execution settings and flags.
- [Claude Code setup](https://code.claude.com/docs/en/setup)
  documents the npm package and Linux x64/arm64 optional dependencies.
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
  documents print mode, streaming JSON, and permission flags.
- [Claude Code non-interactive mode](https://code.claude.com/docs/en/headless)
  documents piped stdin.
- [Pi README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent)
  documents its current package, Node requirement, and `--ignore-scripts` install.
- [Pi CLI reference](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/cli.md)
  and [providers](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/providers.md)
  document JSON mode, stdin, model selection, and credential variables.
- [Official Node 22 slim Dockerfile](https://github.com/nodejs/docker-node/blob/main/22/bookworm-slim/Dockerfile)
  installs `libatomic1` and retains the shared libraries discovered by `ldd`.
  Those libraries live outside the `/usr/local` tree copied between stages.

No paid model calls are part of the runner's self-tests. Actual provider calls
need your API key and remain a separate check from the deterministic oracle.

The pinned packages installed successfully on Linux amd64, and their version
commands and exact configured commands with `--help` all exited successfully.
Docker image builds, arm64 execution, and authenticated model runs were not
executed in the authoring environment.
