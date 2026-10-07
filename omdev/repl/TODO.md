# TODO

Follow-ups the interfaces already leave room for; nothing here is blocked on a redesign.

- **Tab completion in the minitui frontend.** `Interpreter.complete(source, cursor)` exists (python's is a
  dependency-free attribute walker over the namespace; javascript's is the default empty one). Wire it to the
  `SuggestionsPopup` on tab from `Console` / the host's `InputMode`, the way the slash-command popup already works. A
  javascript completer would walk `globalThis` and object keys through the `Object` handle.
- **A live card for long-running evaluations.** Today every output commits straight to scrollback as it arrives. An
  evaluation that awaits or runs off-loop could instead show a `Card` in RUNNING with streaming detail, then commit as
  displayed - the tool-card lifecycle the chat app already has, for repl code.
- **Snapshot-restored quickjs sessions.** `QuickjsInterpreter` takes an existing `Context`; `omdev.js.quickjs.snapshots`
  can restore one from a blob. The missing piece is the host-side plumbing (and a frontend command) to register a
  restored, cloned, or already-running engine context as another named interpreter on the `Session`.
- **A sandboxed python interpreter.** `PythonInterpreter(builtins_base=...)` already takes a restricted builtins
  mapping; a real sandbox needs the import story, resource limits, and probably a thread or subprocess `Executor`.
  Register it on the session beside the manhole-style one and switch between them.
- **Streaming quickjs output mid-evaluation.** `print` / `console.*` output is parked on the engine thread and written
  to the sink once the evaluation returns. Streaming it would need the sink marshalled back to the caller's context
  (the manhole's `Connection.post` already is; the minitui console's commit path is not).
- **The manhole**: see `manhole/TODO.md` - runaway code and interruption, the sync thread hosting.
