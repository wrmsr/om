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
- **Input for a running shell command.** A bash submission runs with nothing on its standard input, so a command which
  wants an answer fails instead of waiting. The terminal is there to carry one: run the command with its input on the
  terminal (one redirection in `BashProtocol.submit`), and have a submission made while a command is running be written
  to the pty rather than queued behind it - which is what type-ahead at a terminal is. `Console` queues today; it needs
  to ask the interpreter whether it takes input.
- **A live region for a shell's unfinished line.** Scrollback is append-only, so a line still being written - a prompt,
  a progress bar redrawing itself - is committed as it stands after a quiet moment, and again when it changes. It
  belongs in the live card of the item above until its newline. The same card, over `omcore.term.vt100` rather than
  `LineTerminal`, is where a program which addresses the cursor across lines (a multi-line progress display) would
  render correctly.
- **Shell completion.** `compgen` knows commands, files and variables; `BashInterpreter.complete` would ask it through
  `BashShell.run_command` - which needs an execution-free moment, and `complete` to be awaitable.
- **A remote python.** A python on the far side of a `PtySpawner` (or of a pipe-flavored sibling of it), driven the way
  bash is here: the manhole's semantics, in the container the tools run in.
- **A shell's `interrupt()`.** `BashInterpreter` interrupts on cancellation of its caller, which is what its frontends
  do. `Interpreter.interrupt` - synchronous, from any thread - has nothing to write the interrupt character with.
