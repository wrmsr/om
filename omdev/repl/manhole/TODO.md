# TODO

## Runaway code

A connection has no way to stop what it started. A `while True: pass` typed at the prompt runs until it finishes, which
is never, and the only thing the client can do is disconnect - which the server only notices once the execution returns
and the handler reads again, so even that does nothing.

How bad it is depends on the hosting:

- **Inline dispatch (the default).** The code runs on the manhole thread's loop, in the handler task. A cpu-bound
  statement stalls that loop, so *every* connection to that manhole freezes until it finishes, and `stop()` runs into
  its timeout. The manhole thread is a daemon, so interpreter exit is unaffected.
- **Host-loop dispatch (`AsyncioLoopDispatcher`).** The stall moves to the host's loop - the manhole loop stays live,
  but the host is now stuck on the client's behalf, which is the opposite of what a manhole is for. Cancelling the
  dispatched task (a `stop()`, a cancelled handler) marks the future cancelled and lets the manhole side unwind, but the
  code itself keeps running on the host until it yields.
- **`sync.serve_inline`.** The calling thread is the one running the code, by design: that is what blocking the program
  means here. A runaway is the program hanging, which it would have anyway; ctrl+c of the process still works.

Awaits are fine everywhere: a statement that awaits yields, and cancellation reaches it.

### What was considered and rejected

Running each statement on a pool thread through the existing `Executor` seam (`PythonInterpreter(executor=
AsyncioThreadExecutor())`) keeps the manhole loop live during cpu-bound statements, and top-level await still works
(the thread returns the coroutine object; the handler awaits it on the loop). But `asyncio.to_thread` uses the loop's
default `ThreadPoolExecutor`, whose threads are non-daemon and joined at interpreter exit: a runaway on one of them
turns a stuck manhole into a process that cannot exit. Strictly worse than the status quo.

### What it should probably be

- **A daemon thread per execution (or per connection), owned by the manhole**, through an `Executor` implementation
  of its own rather than `to_thread`: the manhole loop stays live, other connections keep working, `stop()` returns, and
  exit is unaffected because nobody joins the runaway. The old `omcore.diag.replserver` had thread-per-connection by
  accident; this would have it by seam. Interruption stays best effort - cpython offers nothing clean for stopping a
  thread mid-statement (`PyThreadState_SetAsyncExc` via ctypes is the folk remedy, and it only fires at bytecode
  boundaries, never inside a blocking C call).
- **Wire-level interrupt.** Telnet's Interrupt Process (`IAC IP`, `0xff 0xf4`) is currently stripped as noise in
  `protocol.py`; it should instead cancel the running execution the way the minitui console's ctrl+c does. `nc` has no
  equivalent - a `/cancel` line would need the handler to be reading while executing, which is the same
  execution-off-the-handler change as above.
- **Disconnect should cancel.** Once execution runs off the handler, the handler can keep reading, notice EOF, and
  cancel/interrupt the execution rather than wait for it.

## Smaller

- The omcore bootstrap's lazy `omdev.repl.manhole` import surfaces as a raw `ModuleNotFoundError` at `enter()` when
  omdev is not installed and `--manhole:address` is given. A clearer message would be kind.
- `SyncThreadManhole` is a stub: the selectors-driven, no-asyncio background hosting (see `sync.py`).
- All hostings are asyncio-only by agreement; the interfaces are loop-neutral and nothing else should need to change.
