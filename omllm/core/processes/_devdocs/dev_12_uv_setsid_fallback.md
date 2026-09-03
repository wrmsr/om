# dev 12 — uv/python-build-standalone setsid fallback (2026-09-03)

Linux uv-managed interpreters can now launch the process manager, including real controlling-terminal PTYs. The
failure was `NotImplementedError: posix_spawn: setsid unavailable on this platform` during the manager's startup
self-test.

## Cause

uv's managed CPython comes from python-build-standalone. Its portable GNU/Linux build targets glibc 2.17, predating
glibc 2.26's `POSIX_SPAWN_SETSID`. CPython compiles the `os.posix_spawn(setsid=True)` branch only when its build headers
define `POSIX_SPAWN_SETSID` (or the `_NP` equivalent), so a portable interpreter rejects the argument even when it is
running on a newer libc. Locally-built pyenv CPython sees the host's newer headers and supports it; macOS builds expose
their corresponding spawn flag as well.

The problem entered with dev 10's `_posixsubprocess.fork_exec` -> `os.posix_spawn` change. It is a build-capability
difference, not a kernel or container restriction.

## Fix

- The existing live SIGCHLD disposition check now doubles as a per-manager spawn-time setsid capability probe. If the
  session spawn raises `NotImplementedError`, the check retries without a session so it can still verify that children
  are not auto-reaped.
- Native-capable interpreters keep the existing `os.posix_spawn(..., setsid=True)` path unchanged.
- On an incapable build, `BaseProcessManager` spawns the shim without group changes and asks it to call `os.setsid()`
  before pass-fd placement, credentials, ctty acquisition, or target exec. This is valid because the shim has not first
  been made a process-group leader; the EPERM observed in the original research came from trying setsid after
  `setpgroup=0` / `start_new_session=True` had already made it one.
- Until the exec-status handshake proves the shim completed setsid, teardown signals the held pid directly and also
  sweeps pgid == pid in case the session already exists. After handshake, the existing group signaling and held-zombie
  ownership rules are unchanged.
- Explicit `SessionMode('group')` still uses `setpgroup=0`; it is not silently substituted for session semantics. PTYs
  therefore remain proper session leaders with a controlling terminal under the fallback.

## Verification

- Simulated unsupported-setsid tests cover manager startup, default session vs explicit group semantics, cancellation
  at the first post-spawn suspension point, and PTY controlling-terminal acquisition.
- The focused launch/asyncio/PTY suite is 39 passed / 1 skipped (root-only credentials).
- The full process suite is 64 passed / 5 skipped.
- Both process-manager demos were run successfully using the actual uv-managed CPython 3.14.7 that rejects a direct
  `os.posix_spawn(..., setsid=True)`: ordinary/background/stubborn-process teardown left no children, and the PTY demo
  reported a real `/dev/pts/*` ctty with working resize and interactive echo.
- The original `om llm --exec --model qwen` path reached its idle prompt under that interpreter and exited cleanly on
  interrupt.
