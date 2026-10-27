# Subagents TODO

Near-term first: what v1 punted on and has to be nailed down before building higher on it. Then mid-term goals. See
`DESIGN.md` for the reasoning behind each.


## Near-term

- **Split the root injector into an app injector and an agent injector per agent**, the root agent's included.
  `bind_subagent_agent` is the shape of the per-agent module; the root agent moves onto it, declares `TURN_SCOPE` and
  `TOOL_INVOCATION_SCOPE` for itself, and the subagent injector becomes a sibling under the app rather than a child
  shadowing the root's `Agent`, `ToolSet`, `SystemPromptManager`, `AgentEventSubscribers`, `TurnRunner`,
  `ToolInvoker`, `AgentSetup` and `ProcessScope`. Then `SUBAGENT_TURN_SCOPE` and `SUBAGENT_TOOL_INVOCATION_SCOPE`
  collapse into `TURN_SCOPE` and `TOOL_INVOCATION_SCOPE`, and the child shadowing wart in `omcore/inject/TODO.md` is no
  longer relied on here.
- **Tool membership by concern, not by name.** The `fs` concern should contribute its read-only tools to an explorer's
  tool set through the injector the way every concern contributes to `AgentTools`; `_explore_tool_names` in the tui
  wiring and `SubagentProfile.tool_names` go away, and the subagent package stops knowing that `ls` exists. Until then
  names are validated wherever a profile is applied, never intersected.
- **Eager profile validation at startup.** Blocked by the cycle `ToolSet -> SubagentTool -> SubagentProfiles ->
  ToolSet`. Resolves itself once membership is by concern; otherwise the subagent tool's description must stop needing
  the profile set at construction.
- **Child sessions.** The child injector binds its own `SessionId` and `Session`; `OrmSession` grows a `parent_id`
  column; the parent's `SubagentToolResultDetails` carries the child's session id so a frontend can open it. Decide
  what resuming a parent does about its children's sessions (nothing, probably: they are complete).
- **Token usage.** The child's ledger is on the result details only. Decide whether and how it folds into the parent's
  ledger and the status line: a separate "subagents" figure, or added in, or both. `TurnEndEvent.usage` is the
  parent's own and must stay so.
- **Steering and killing a running subagent.** The child `Agent` has an inbox nobody writes to. A `/steer` or a kill
  needs a handle on the running child: a registry of live runs by `SubagentRunId` in the parent's scope, which is also
  the first step toward background subagents.
- **Permission provenance.** A rule cannot yet say "subagents may not write" or "this profile may". The requestor
  should carry agent identity from the child scope (the `SubagentRunId`, or an agent id above it), not a
  `ToolContext.parent` chain. Related: a child's ask shows in the parent's ui with no indication it is a child's.
- **Wall-clock timeout.** A subagent is bounded by turns only. Everything that does IO needs a timeout; a profile
  should carry one, enforced around `drive_subagent`.
- **Nested card rendering.** v1 shows a child's tool cards as prefixed siblings. Decide whether a subagent's card should
  contain its children's, how deep, and what of the child's stream text (if anything) is shown live. The bare frontend
  shows nothing of a child's tool activity.
- **Event volume.** Every child event, stream deltas included, is relayed and published as a parent
  `ToolExecutionUpdateEvent`. Fine at one level; decide whether the relay should filter (no deltas) or the sink should,
  before nesting multiplies it.
- **Transcript persistence for display.** The child transcript rides the result details in memory only. If the parent's
  session is resumed, the child transcript is gone; the child session above is the answer, the details should carry a
  reference rather than the messages.
- **Tool call id collision.** Child cards are keyed by the child's tool call id, from the provider, assumed unique
  across the parent's and children's calls. A scripted or odd provider could collide. Key by `(run_id, call_id)` or
  prefix.
- **Empty final text.** A child which ends without a final message returns a placeholder. Decide whether the child
  should be nudged (a follow-up asking for its report) before giving up.
- **Model selection.** The child uses the parent's model because there is no `/model` yet and one backend is bound. A
  profile should be able to name a model (a cheap one for exploration) once the backend manager holds more than one.
- **Profile configuration.** Profiles are hardcoded. User-defined profiles (a file, a command) need a marshalable
  profile shape and a story for their tool membership that is not names.
- **The relay also relays `StateUpdateEvent`s** from the child's setup. Harmless; decide whether it should.


## Mid-term

- **Background subagents.** A `SubagentScope` on the tool environment mirroring `ProcessScope`: spawn returns a run
  id, read polls the child's transcript or progress, steer writes to its inbox, kill cancels it, list shows them. The
  child injector is kept alive past the spawning call and closed with the parent's scope. The sync tool becomes
  spawn-and-wait over the same machinery.
- **Nesting and depth.** A child spawning children: the subagent tool bound per agent scope, a depth limit on the
  profile, a turn scope per depth (or the app/agent split making each agent's scope its own), relayed events wrapping
  wrappers (the renderer already recurses).
- **Richer per-profile configuration.** Different tool sets by concern, different models, different turn configs,
  different system prompt contributors, a cwd of their own, a sandbox of their own.
- **Citizens of `TOOL_INVOCATION_SCOPE`.** Every tool call is carried out through a `ToolInvoker`, and in the tui in
  an opening of a per-call injector scope seeded with the `Tool` and its `ToolContext` (`ScopedToolInvoker`), but
  nothing lives in it yet beyond the `DirectToolInvoker` it delegates to. The subagent runner is a natural first
  citizen of it, and it is the eventual cure for `ToolContext` and `ToolEnvironment`: what a tool call needs is bound
  in its scope rather than reached for through a context object.
- **Process adoption.** A subagent handing a process up to its parent's scope ("keep this server running"), via
  `ProcessScope.adopt`.
- **Subagent-level compaction.** A long-running child hitting its context window compacts like the root agent does, on
  the same lifecycle manager, which falls through to the root's today and should.
- **Result shaping.** Structured results (a schema the parent asks for) rather than free text, once tool results carry
  more than text.
