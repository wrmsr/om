# Overview

LLM code.

# Notable packages

- **[llm](https://github.com/wrmsr/om/blob/master/omllm/llm)** - A general purpose LLM toolbox.
- **agent** - Conversation state, turn loop, context lifecycle, and tools.
- **harness** - Sessions, commands, prompt construction, and host skills.
- **ui/tui** - Terminal frontends and their injection wiring.

# Harness controls

Run the TUI from the repository root:

```sh
./python -m omllm.ui.tui.minitui --model gpt --effort low --fs --exec --web
```

`--web` installs the HTTP fetcher and DuckDuckGo searcher. Search uses the optional `ddgs` dependency and runs through
the host job runner; HTTP fetches go through the existing permission interface (ask by default).

## Effort

`--effort LEVEL` sets the initial reasoning effort. In a session:

```text
/effort
/effort high
/effort default
```

The first form reports the effective setting and the current model's supported levels. The last clears the session
override, restoring model/provider defaults. `none` is an explicit level, not a synonym for `default`. Unsupported
levels are rejected, not approximated. Programmatic callers use `llm.Options(reasoning_effort=llm.ReasoningEffort.LOW)`;
custom models advertise their exact supported set in `Model.reasoning_efforts`.

Models can further restrict effort when tools are present through `Model.reasoning_efforts_with_tools`. In live tests,
GPT-5.4 Nano's Chat Completions endpoint rejected function tools with non-`none` effort. Its catalog entry therefore
allows only `none` when tools are installed; low and higher remain available for tool-free requests. `/effort` and
startup validation account for the current tool set. No endpoint is silently switched.

Effort and the existing `thinking` option are separate. `--thinking` / `--no-thinking` expose the latter:

- OpenAI Responses: effort controls reasoning; thinking requests readable summaries.
- Anthropic: effort configures output effort; unless explicitly disabled, choosing effort also enables adaptive thinking.
- Gemini 3 Flash: effort maps to `thinkingLevel` (`minimal`, `low`, `medium`, `high`); thinking controls `includeThoughts`.
  `--no-thinking` hides thought summaries, **not** reasoning. `minimal` is not off, and `none` is rejected.

Provider references: [OpenAI reasoning](https://developers.openai.com/api/docs/guides/reasoning),
[Anthropic effort](https://platform.claude.com/docs/en/build-with-claude/effort),
[Gemini thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking).

## Prompts

`har.PromptBuilder` composes injected `PromptContributor`s, ordered by `(order, name)` with unique names.
The standard contributors supply coding guidance and guidance for the tools actually installed. Both terminal
frontends use the same initializer. `--system-prompt TEXT` appends host-supplied instructions.

Extensions register contributors through the same items-binder pattern as commands:

```python
from omcore import inject as inj
from omllm import harness as har
from omllm.ui.tui.inject import prompt_contributors

bindings = inj.as_elements(
    prompt_contributors().bind_item(to_const=har.TextPromptContributor(
        'verification-policy',
        'Always report which tests were run.',
        order=500,
    )),
)
```

Prompt configuration comes from the host application. There is no repository-instruction discovery or `AGENTS.md`
loading, and tool working directories and containers do not participate in configuration discovery.

## Host skills

By default, skills are immediate child directories of the host's `~/.om/config/llm/skills` directory (using the existing
`OM_HOME` home-path configuration). Repeat `--skills-dir PATH` to use explicit host roots instead of the default, or
pass `--no-skills` to disable discovery and the reading tool. Relative roots are relative to the host process, not
`--cwd`. The catalog is loaded once at startup; `/skills` reports invalid-skill diagnostics. Duplicate names are an
error, rather than silently selecting a winner.

Each skill has a `SKILL.md` with YAML frontmatter:

```markdown
---
name: verification
description: Project-independent guidance for testing a change.
---

Read reference/checklist.md with read_skill before choosing the verification steps.
```

The system prompt contains only names and descriptions. The agent reads full instructions and bundled text resources
on demand with `read_skill(name, path="SKILL.md", offset=0, limit=20000)`. Long resources are paginated with an explicit
continuation offset. Reads are bounded to 256 KiB per UTF-8 file and cannot escape the skill directory through `..` or
symlinks. Skill discovery and reads run on the host job runner, never through `FsOps` or process tools; skills work even
when filesystem tools are disabled. Reading bundled scripts does not execute them.

```text
/skills
/skills show verification
/skills show verification reference/checklist.md
/skills use verification check the current change
```

`use` starts a prompt containing the full skill instructions and optional task. It does not install a persistent mode.

## Steering

While a prompt runs in minitui, `/steer NEW INSTRUCTIONS` bypasses the normal prompt queue and enters the agent's
steering inbox. It is consumed at the next turn boundary, ahead of queued ordinary input, even if the current model
response would otherwise finish the prompt. It does not interrupt a model request or cancel running tools. Existing
turn limits and inbox policies still apply: if a run ends early, unconsumed steering remains queued for the next prompt.
Idle, compaction, and terminal-delivery periods do not accept `/steer`. The pump owns and joins its immediate command
tasks during shutdown. Programmatic callers can continue using `Agent.steer` or `Session.steer` directly.

# Focused integration tests

```sh
./python -m pytest omllm/ui/tui/tests/test_configuration.py omllm/ui/tui/minitui/tests/test_steer.py
./python -m pytest omllm/ui/tui/tests/test_features_online.py omllm/ui/tui/tests/test_web.py
```

The live-provider tests exercise OpenAI Responses and Completions, Anthropic, and Gemini in both immediate and streaming
mode: set effort through the command, discover a host skill, read its instructions and a random verification phrase
from a bundled resource, and return that phrase. They use the existing test harness secrets and skip when keys are
unavailable. Web tests cover injected defaults, a permission-checked local HTTP roundtrip, and live search/fetch.
