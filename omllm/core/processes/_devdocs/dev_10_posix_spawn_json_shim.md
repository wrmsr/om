# dev 10 — os.posix_spawn + a json ShimPayload (2026-08-19)

Two clean-ups of the spawn path that had drifted from the original intent.

## `_posixsubprocess.fork_exec` -> `os.posix_spawn`

The only reason to reach for CPython's private `_posixsubprocess` was its between-fork-and-exec fd hygiene (close
everything but `pass_fds`, clear CLOEXEC on them in the child). But that work is exactly what the **shim** exists for:
a full python process of ours that runs before the real exec, where anything goes. So:

- `managers/spawn.py::spawn_child(argv, *, env, stdin_fd, stdout_fd, stderr_fd, pass_fds, session_mode)` is now
  `os.posix_spawn` (public API; glibc >= 2.24 / macOS / musl report exec errors properly): `POSIX_SPAWN_DUP2` file
  actions for 0/1/2 (sources in the 0-2 range are lifted to a CLOEXEC copy first), `setsid` / `setpgroup=0`,
  `setsigdef` for SIGPIPE/SIGXFSZ, PATH search done in the parent like `execvpe` (ENOENT/ENOTDIR keep looking, EACCES
  is remembered). `pass_fds` are made inheritable in the parent for the duration of the spawn and restored - the same
  exposure the launcher always had for its payload fd. No `cwd` (the shim chdirs; `LaunchPlan.cwd` is gone).
- The shim's `close_fds` (default on) closes every fd >= 3 except `status_fd` + `keep_fds` (`/proc/self/fd` or
  `/dev/fd` listing, else `closerange` over the gaps). Since everything python opens is CLOEXEC anyway, a stray
  inheritable fd can reach the shim interpreter, never the target.
- Tests: `test_fd_hygiene_and_pass_fds` (a stray inheritable fd is invisible to the target, a `PassFd` is usable, our
  flags are restored), plus the existing spawn-error / session-mode / pty coverage unchanged.

## stdlib `marshal` -> json `ShimPayload`

"Marshalable" in the original requirement meant the om sense, not `marshal` - whose format is explicitly
version-dependent, i.e. the one thing a hermetic shim meant to be run by *some other* python must not rely on. Now:

- `spawn/shim.py::ShimPayload` - a plain `@dataclasses.dataclass(frozen=True)` (3.8-safe: no kw-only), fields
  restricted to json-native types (`str`/`int`/`bool`/`None`/lists/dicts), `to_json()` / `from_json()`. OS strings
  (argv, env, cwd, names) travel as `str`; undecodable bytes survive as surrogate escapes, which json emits as
  `\udcXX` and `os.fsencode` / `execvpe` turn back into the original bytes (`test_non_utf8_argv_and_env`).
- The rest of the package imports the shim module (it runs nothing at import) and builds the dataclass directly:
  `launch/shim.py::build_payload -> ShimPayload`. The payload file is one json line + the shim source; the bootstrap
  reads both, execs the source as a real module (`sys.modules['__procs_shim__']`, so `dataclasses` is happy) and calls
  `main(ShimPayload(**p))`.
- Status records are json too: `[stage, errno, message]` (`encode_error` in the shim, `decode_shim_status` in the
  launcher). No `marshal` anywhere.
- `spawn/tests/test_shim.py`: payload round-trip (incl. surrogates, defaults, tuples-as-lists), status round-trip, the
  shim still compiles (and the dataclass works) under 3.8 / 3.9 when those interpreters are around, and the
  `python -m ...spawn.shim <fd>` debug entrypoint.

Suite: `pytest omllm` 448 passed / 23 skipped; `make fix gen check` clean.
