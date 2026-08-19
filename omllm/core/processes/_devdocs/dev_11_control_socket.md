# dev 11 — control socket (SCM_RIGHTS), base64 OS strings, shim moves to launch/ (2026-08-19)

Follow-ups to dev 10 after review.

## No fd is ever made inheritable in the parent any more

dev 10 flipped `pass_fds` (incl. the payload fd and the status pipe, i.e. on *every* spawn) inheritable around the
`posix_spawn` and restored them - fundamentally racy against any concurrent fork+exec in the process. Now:

- The child receives exactly one fd from the parent: an AF_UNIX stream socket (`make_control_socketpair`), delivered
  by a `POSIX_SPAWN_DUP2` file action onto `LaunchPlan.control_fd` (a dup2 always yields a non-CLOEXEC descriptor, and
  it happens in the child's own table). Sources that are also dup2 targets are lifted first.
- Everything else - the payload blob and the caller's `PassFd`s - is **sent over that socket with SCM_RIGHTS**
  (`managers/spawn.py::send_control_fds`: a `{"n": N}` header line, then the fds, chunked at 200 per message), queued
  *before* the child runs. Verified: queued rights survive the sender closing; the kernel dups them straight into the
  child's table.
- The bootstrap / `_shim.receive_control` drain the handshake; the shim `place_passed_fds` lifts the received fds above
  every number in play and dup2's them onto `ShimPayload.keep_fds` (so the target sees the parent's numbers), then
  `close_other_fds` closes the rest. `ShimLauncher` picks `control_fd = max(3, max(keep_fds) + 1)` so a relocation can
  never land on the socket.
- Exec status rides the same socket (the shim keeps it close-on-exec; EOF == exec happened). The status pipe is gone;
  `LaunchPlan` is `(argv, env, control_fd, send_fds, owned_fds)`; `Launcher.plan` takes no fds.
- This gives the shim a real bidirectional channel to the manager for later (in-sandbox / remote helpers).

## argv / env / cwd as base64 OS bytes

json is not injective over all python strs: a high+low surrogate *pair* as two code points (unencodable as an OS
string) collapses into one astral char on the way through - a value that should fail to exec would exec with a
different value. `encode_os` / `decode_os` (base64 of `os.fsencode`d bytes) make argv / env / cwd byte-exact on both
sides, independent of either side's filesystem encoding, and an unencodable str now fails loudly in the parent. User /
group *names* stay plain str.

## Misc

- `spawn/shim.py` -> `launch/_shim.py` (the `spawn/` package only existed for a `__main__` helper that is long gone);
  tests in `launch/tests/test_shim.py` (OS-string and payload round-trips, status records, 3.8/3.9 compile check,
  `receive_control`, and the `python -m ...launch._shim <control_fd>` debug entrypoint end-to-end incl. relocation).
- The payload temp file write carries a SECURITY comment: it holds the target's full environment (secrets);
  `TemporaryFile` is 0600 and on Linux an `O_TMPFILE` that never has a name, but it does live on the temp filesystem for
  a few ms - `os.memfd_create` is the next step if that window ever matters.
- `test_fd_hygiene_and_pass_fds` now also passes two fds at once with one at fd 300 (control fd above it, relocation).

Suite: `pytest omllm` 450 passed / 23 skipped; `make fix gen check` clean.
