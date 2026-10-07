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
./python -m omdev.repl.manhole --serve /tmp/m.sock   # a manhole into this (idle) process; then, elsewhere:
./python -m omdev.repl.manhole /tmp/m.sock           # ...connect to it (or: nc -U /tmp/m.sock)
```

## The manhole

`omdev.repl.manhole` is the socket frontend: a plain text line protocol (`nc`, `socat`, `telnet`, or its own client)
into a live process - the successor to `omcore.diag.replserver`, and python only, on purpose: a shell *inside* the
process, in the process's language. Each connection gets a `PythonInterpreter` of its own whose namespace starts with
the host's seed (the objects shared, the dict per connection) over a standard one (`sys`, `os`, `gc`, `threading`), and
whose `print` falls back to that connection, so a callback defined at the manhole and called later from elsewhere in the
process still reports to whoever wrote it.

```python
from omdev.repl import manhole

mh = manhole.start_manhole('/tmp/app.sock', seed={'app': app, 'injector': injector})   # a thread, its own loop
...
mh.stop()
```

Any entrypoint gets one through bootstrap, no code of its own involved:

```bash
./python -m omcore.bootstrap --manhole:address=/tmp/app.sock -m yourpackage.yourmain
```

Hostings: `start_manhole` / `AsyncioThreadManhole` on a dedicated thread with its own loop (the default - it stays
answerable whatever the host's loop is doing); `AsyncioManholeServer` on the host's own loop (`async with`); and
`sync.serve_inline`, which blocks the calling thread on a plain socket until the one client it accepts leaves - a remote
pdb of sorts, no loop involved. A `Dispatcher` says where the code runs relative to where its connection is served: an
`AsyncioLoopDispatcher` over the host's loop lets a thread-hosted manhole's python await the host's coroutines.
`sync.SyncThreadManhole` (a selectors-driven background thread, no asyncio anywhere) is a stub awaiting a need.

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
- **manhole/** - the python-only socket frontend over `LineRepl`: `base.py` (addresses, the `Connection` and
  `ManholeServer` interfaces), `protocol.py` (the conversation, telnet noise stripped), `server.py` (`Manhole`: a python
  interpreter per connection over the host's seed), `asyncio.py` (the asyncio hostings, the package's one asyncio
  import), `sync.py` (the inline blocking hosting; the sync thread hosting's stub), `client.py`.
- **dispatch.py** - the `Dispatcher` seam: run code here or on another loop; asyncio's cross-loop one is in
  `asyncio.py`.
