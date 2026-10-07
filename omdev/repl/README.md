# repl

An embeddable read-eval-print loop: backends for python and javascript (quickjs), frontends for minitui and a bare
stdin/stdout loop, and the interfaces between them, so that a host process - an llm harness, a server, anything with a
loop - can offer an interactive interpreter over its own internals (the 'manhole') without the builtin repl's habits of
owning the process: nothing here touches `sys`, `builtins`, `readline`, or the terminal.

## Try it

```bash
./python -m omdev.repl.minitui             # vim-powered input with syntax highlighting, /py and /js to switch
./python -m omdev.repl.minitui --lang=js   # start in javascript (when the quickjs extension is built)
./python -m omdev.repl.bare                # input() and print, nothing else
```

## Architecture (dependencies point strictly inward)

    frontends (minitui/, bare/) -> sessions, lines -> interpreters -> languages, outputs, executors

- **languages.py** - the stateless half of a backend: prompts, the name highlighters resolve, completeness checking for
  line frontends. One instance per language; interpreters point at it.
- **interpreters.py** - the stateful half: `Interpreter.execute(source, sink) -> Awaitable[Result]`. An error in the
  code is a `Result`, written to the sink; only the host's own failures raise.
- **outputs.py** - the typed stream an execution writes: printed text, a result's displayable form, a formatted error.
  Frontends render these and nothing else.
- **executors.py** / **runners.py** - the two loop-neutral runtime seams: where an interpreter's blocking work runs,
  and how a frontend starts an execution from a key press. `asyncio.py` is their asyncio implementation and the
  package's only asyncio import; the immediate implementations run inline and drive under `lang.sync_await`.
- **sessions.py** - named interpreters, one active: what a frontend holds. Hosts register whatever interpreters they
  like under whatever names.
- **lines.py** - the line-at-a-time read-eval-print core for transport frontends (bare today, a socket manhole later).
- **python/** - the builtin repl's semantics as a good citizen: per-statement execution, a private copy of the builtins
  with a sink-aware `print`, tracebacks trimmed to the user's frames, top-level `await` on whichever loop the caller is
  on. The namespace is a plain dict the host may seed and poke.
- **quickjs/** - one engine context per interpreter (fresh or handed in), evaluating through the executor with the
  engine's interrupt flag wired to cancellation; `print` and `console.*` bound in. Quarantined: the extension may not be
  built.
- **minitui/** - the first-class frontend: `Console` binds a session to any `TextArea` and a commit callback (the
  reusable core a host app composes in), swapping the input's highlighter and prompt with the language; `ReplApp` is
  the standalone app around it.
- **bare/** - `input()` and stdout over `LineRepl`, loop-free.
