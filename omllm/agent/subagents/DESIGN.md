# Subagents

A subagent is an agent spawned by an agent: given one task by its parent, run to completion on it with a context of its
own, and heard from once, through the result of the tool call which spawned it. This document is the collected
reasoning behind the v1 in this package and the `omllm.ui.tui.inject.subagents` wiring over it: what a subagent *is* in
this codebase's own vocabulary, what was decided and why, what was deliberately left out, and where each part is meant
to go. It is not a plan. `TODO.md` beside it is the list of what has to be nailed down before building higher.


## What a subagent is here

The temptation is to treat a subagent as a function call on the turn loop: build a `TurnLoop`, run it inside the tool's
task, return the text. That is mechanically true and architecturally wrong for this codebase. In its own vocabulary a
subagent is an **agent scope**: an `Agent` with a `State` and a `Context` of its own, its own event bus, its own tool
set, its own system prompt, its own process scope, and eventually its own `Session` and its own turn scope. Everything
the root agent has, it has, and nothing of the root agent's is shared with it but the infrastructure beneath both: the
model backends, the permission rules, the ops the tools stand on.

That framing decides most of the layout:

- The subagent runs on a real `Agent`, not a bare loop, so that steering, follow-ups, state updates, and a session can
  attach to it later exactly as they attach to the root agent today.
- In the injector-aware host it is a **child injector** of the app's, binding the per-agent things itself and falling
  through to the app for the shared ones. This is the `DriverManager` pattern from the attic textual ui, and
  `omcore/inject/tests/test_patterns.py::test_child_injectors_per_instance` codifies the per-child items behavior it
  relies on.
- In the injector-oblivious core it is a hand-built `Agent` with its state assembled from the same ingredients. The
  oblivious path is the reference implementation and must stay complete: every behavior the injector path has, the
  manual path has, with more kwargs.

The package is injector-oblivious throughout. It makes no reference to any injector, and is fully usable by manual
threading (see `tests/support.py`). The injector wiring lives in `omllm/ui/tui/inject/subagents.py` because today the
only injector configuration is the tui's; the agent package will eventually own its injector modules, but they will
remain separate from the implementation modules as they are everywhere else.


## The seam

`SubagentRunner` is the seam, the analogue of `TurnRunner`. The tool asks the runner to run a subagent on a
`SubagentRunParams` and gets a `SubagentRunResult`. Two implementations:

- `AgentSubagentRunner` (`runners.py`): manual threading. Takes a `TurnRunner`, a pool of tools, a model, a turn
  config, and extra system prompt contributors, and builds a fresh `Agent` and `State` per run.
- `ChildInjectorSubagentRunner` (`omllm/ui/tui/inject/subagents.py`): creates a child injector per run and provides the
  `Agent`, `AgentSetup` and `AgentEventSubscribers` out of it, exactly as a frontend's `main` does with the root
  injector.

Both end in `drive_subagent` (`driving.py`): prompt the prepared agent once, shape the `TurnResult` into a
`SubagentRunResult`. The runner interface mirrors `TurnRunner.run_turn`'s contract: every outcome the subagent decides
for itself comes back as a result, a failure included; only the caller's own cancellation raises.

The run parameters are **explicit fields**: the profile, the prompt, the parent's `ToolEnvironment`, and the parent's
`ToolProgressSink`. They are not a `ToolContext` passed through. Adding a field here is meant to be a little painful,
because each addition is a statement about what a subagent needs from its parent, and the growing list is the clearest
account there will be of what the eventual replacement for `ToolContext` and `ToolEnvironment` has to carry.


## Events: the relay, and why nothing lands raw

A subagent's events never reach the parent's bus directly. `Session._on_agent_event` stores every `MessageAddedEvent`
it sees and resets its stored-message count on every `AgentStartEvent`. A child's run published raw on the parent's bus
would be recorded as the parent's own, and would reset the parent's bookkeeping mid-run. Frontends keyed on
`AgentStartEvent`/`AgentEndEvent` would open and close turns for the child as if it were the parent.

Instead `SubagentEventRelay` (`progress.py`) subscribes to the child's bus and reports each event to the parent's
`ToolProgressSink` wrapped in a `SubagentEventToolProgressUpdate`, tagged with the run id and the profile name. The
parent's loop publishes that as a `ToolExecutionUpdateEvent` of the spawning call, like any other tool progress. A
frontend which knows nothing of subagents sees a tool call with a lot of progress. One that does (the minitui renderer)
unwraps the child's tool execution events into cards of their own beside the spawning call, titled `profile/tool`.
Nothing else of the child's run is shown live in v1; its final word comes back as the spawning call's result, with a
`SubagentToolResultDetails` carrying the run id, reason, turn count, usage, and the whole child transcript for display.

`ToolProgressUpdate` and `ToolResultDetails` are package-sealed to `omllm.agent`, so the subclasses live here without
touching `types/`.

The relay subscribes before the child's state is set up, so it also relays the child's `StateUpdateEvent`s (its setup,
the application of its run). Renderers ignore those; tests filter them.


## Permissions

Spawning is a permission target like any other: `SubagentPermissionTarget(profile)`, matched by
`SubagentPermissionMatcher(profile=None)` for any or a named profile, both manifest-registered so
`/permissions add allow subagent {}` works. Under the default-deny decider a spawn with no rule is an error result for
the model, which is the right failure. Both yolo modes allow spawning outright.

The child's own tool calls are decided by the **root's** `PermissionDecider`, which the child injector does not shadow.
A child's write goes through the same rules and the same asker as the parent's would, and the asker's card is keyed by
the child's tool call id, so the renderer's unwrapped child card is what the ask attaches to and what finishes it.

There is no permission provenance yet: a rule cannot say "subagents may not write". `PermissionRequestor` carries a
`ToolContext`, and the right fix is agent identity in the child scope, something like the `SubagentRunId` the child
injector already binds, carried on the requestor, not a `ToolContext.parent` chain walked by matchers.


## Profiles

A `SubagentProfile` is what a subagent is spawned *as*: a name and a description the model picks by, a system prompt,
the names of the tools it gets out of the pool it is spawned from, and a turn limit. `SubagentProfiles` is the set a
tool offers, the first being the default. Two profiles in v1:

- `general`: the whole pool, for self-contained multi-step tasks.
- `explore`: read-only tools, for investigation. Assembled at wiring time from the config flags, by the names of the
  read-only tool classes bound for each flag, and offered only when there is something read-only to give it.

**Tool selection by name is an antipattern, accepted for v1.** Tool names are what the llm layer is given and what the
user sees, which does not make them the right internal currency. A profile and the pool it is applied to are assembled
separately and agree only by convention. Two things keep it honest in v1: a profile naming a tool the pool does not have
is an error (`UnknownSubagentToolsError`) wherever it is applied, never a silent omission; and the explore list is built
from the tool classes' own `name` attributes, not literals. Where this should go: the concern owning a tool decides its
membership. The `fs` concern knows which of its tools are read-only; it should contribute them to an explorer's tool
set through the injector the way every concern already contributes to `AgentTools`, and the subagent package should
know nothing of `ls`. Profiles would then name *concerns* or *roles*, or nothing, and tool names would appear nowhere
in them.

Eager validation of the profile set against the root's pool at startup was wanted and is not done: the root's
`ToolSet` provision needs the subagent tool, which needs the profile set, which would need the `ToolSet`. The check
runs instead where the pool is known: in `AgentSubagentRunner`'s constructor, and in the child injector's `ToolSet`
provider per run. See `TODO.md`.

The default turn limit is 30 (`DEFAULT_SUBAGENT_MAX_TURNS`). A subagent has nobody watching it, so the loop's
unbounded default is not the right one; a profile may set `None` for unbounded. Reaching the limit returns what the
subagent had with a note, as does truncation by a token or context limit; a failed child is an error result carrying
the child's error and its last words.


## Tools: per-agent instances

Tools are singletons **within an agent scope**. The root agent has its instances of the configured tool classes; each
subagent has its own, over the same shared infrastructure (`FsOps`, `ExecOps`, the process manager, the web fetcher,
the permission decider). This fell out of the child injector almost for free: items binders do not cross the injector
boundary, so a child binding the tool classes gets an `AgentTools` collection of its own, and `bind_tools` was split
into `bind_tool_infrastructure` (bound once, in the app) and `bind_tool_classes` (bound per agent scope) to let the
child bind only the second.

The split also settles nesting: the subagent tool is bound in the root alone, so no child has it, and `general` needs
no exclusion by name. The child's `ToolSet` provider checks this rather than assuming it.

The hand-built runner takes a pool and selects from it; whoever assembles that pool is responsible for leaving the
subagent tool out of it.


## Turn scopes

The root injector's `ScopedTurnRunner` enters `TURN_SCOPE`, a `DelimitedScope` with a `ContextVarScopeContext`, per
turn, seeded with the `TurnParams`, and provides the `TurnLoopRunner` bound into that scope. It is the seam through
which injector-ness reaches the injector-oblivious loop, and the subagent uses it as designed rather than bypassing it.

A subagent cannot enter `TURN_SCOPE`. The parent's opening is visible in the task the subagent runs in (contextvars
propagate to child tasks), and a nested opening of the same scope on the same store raises `ScopeAlreadyOpenError`.
A child injector also may not redeclare an ancestor's scope (`ScopeAlreadyRegisteredError`), while sibling children
may each declare the same scope of their own. So the subagent wiring declares `SUBAGENT_TURN_SCOPE`, a scope with its
own tag over its own `ContextVar`, in every child injector, and `ScopedTurnRunner` took a `scope` keyword to enter it.
Scope state is per (scope, injector), so any number of subagents run at once without seeing each other's openings.

This is the shape the root agent will take after the split below: every agent injector declaring its turn scope for
itself. Until then the two constants coexist. Nesting subagents would need a scope per depth, or that split.


## The root injector is the root agent's injector, and v1 shadows it

`Agent`, `Session`, `SessionId`, `ToolSet`, `SystemPromptManager`, `AgentSetup`, `AgentEventSubscribers`, the
`TurnRunner`, and the `TurnParams` seed are all bound in the root injector today, because until now the root injector
and the one agent were the same thing. The child injector binds its own `Agent`, `ToolSet`, `SystemPromptManager`,
`AgentEventSubscribers`, `TurnRunner`, `AgentSetup` and `ProcessScope`, **shadowing** the root's bindings of those
keys. `omcore/inject/TODO.md` lists child shadowing of a parent binding as a known wart. It is used here knowingly, as
the escape hatch it is: a temporary, incremental way to get an agent scope running.

The structural fix is to split the root into an **app injector** and one **agent injector per agent**, the root agent's
included. The app injector holds the backends, permissions, tool infrastructure, session storage, the ui, and the
commands; each agent injector holds the per-agent bindings above and declares its own turn scope. `bind_subagent_agent`
is written in the shape that per-agent module should have, so that the root agent can move onto it. After the split
the subagent injector is a *sibling* of the root agent's under the app, not a child of the root agent's, and nothing is
shadowed. This is the first item in `TODO.md`.

Not bound in the child, and deliberately falling through to the root: `BackendManager` (same model, there being no
`/model` yet), `PermissionDecider` and `PermissionsManager`, `PermissionAsker`, `TargetCwd`, `InitialLlmOptions`,
`CwdSystemPromptContributor` (as an instance, contributed to the child's own contributors), `FsOps`, `ExecOps`,
`ProcessManager`, `JobRunner`, the context builder and lifecycle manager, and `ContextCompactionRunner`.


## Processes

The parent's `ToolEnvironment.processes` is the scope the subagent's goes under: `ProcessScope.child(...)`, named for
the run id, closed with the run. Processes a subagent leaves behind die with it, not with the parent's scope. The
`RootProcessScope` `NewType` exists for exactly this: tools and `AgentSetup` depend on a plain `ProcessScope` provided
from on high, which is the root scope for the root agent and a child of its parent's for a subagent. The root binds
`ProcessScope` to `RootProcessScope`; the child injector binds `ProcessScope` to its own, managed on its exit stack.

The hand-built runner tolerates a parent with no scope (the subagent then has none either). The injector path requires
one, since in the ui every agent has one. Adopting a subagent's process into the parent's scope - "keep this server
running after the subagent is done" - is not done.


## Cancellation

A subagent runs inside the parent's tool task. The parent's cancellation reaches the tool task, the child's `prompt`
raises the child's own cancellation, the child loop publishes its `AgentEndEvent(CANCELLED)` under its cancellation
shield, the relay reports it to the parent sink, and the cancellation propagates out of the tool to the parent loop,
which then reports its own run cancelled. The child's exit stack unwinds its process scope on the way out. A stray
cancellation inside the child, something it awaited cancelled out from under it, is the child's own `FAILED`, as the
loop defines it, and comes back to the parent as an error result.


## Sessions

A subagent has no session in v1, and the slot is left open. The child `Agent` has its own bus, so a child `Session`
subscribes to the child directly and the relay never has to know. The child injector would bind its own `SessionId`
and `Session`, `OrmSession` would grow a `parent_id` column, and `OrmSessionStorage` is already keyed per session. The
parent's session records the parent's transcript, in which the subagent is one tool call and one result; the child's
transcript is in the result details for display and is persisted nowhere.


## Usage

The child's `UsageLedger` is on the result details and shown in the subagent card's summary row. It is **not** folded
into the parent's ledger or the status line: the parent's `TurnEndEvent` usage is the parent's own, and the renderer's
status line follows it. The child's `TurnEndEvent`s are relayed and ignored by the renderer, since setting the status
line from them would overwrite the parent's numbers.


## UI

Terse and technical, on purpose. The spawning call is a card titled `subagent` with the call summary
`profile: description-or-prompt`. The child's tool calls are cards of their own beside it, titled `profile/tool`, with
a detail row naming the profile and the run id, keyed by the child's tool call id, which is also how the permission
asker keys its cards, so an allowed child ask finishes on the child's end event. The subagent card's result detail is
a summary row (`run <uuid>; profile <name>; <n> turns; <reason>; tokens in <i> out <o>`) over the child's final text.
Cards commit to scrollback in start order, so the subagent card lands before its children's. The child's stream deltas
and messages are not shown live.

The bare frontend's printers ignore progress events, so child tool activity is invisible there in v1.


## Testing

Offline, the hand-built runner is driven with a parent agent and a child runner each on a scripted model of its own
(`tests/support.py`), so what each says is scripted independently. The injector path is driven through
`headless_tui`, where one scripted model answers both agents in invocation order: parent, child..., parent.
Concurrency is tested with gated tools parked at once before release. Real-backend tests run against OpenAI, Anthropic
and Google when their keys are present and skip otherwise: the hand-built runner has a model spawn a subagent to echo a
word; the tui path has a model spawn an explorer to read a file it may not read itself.
