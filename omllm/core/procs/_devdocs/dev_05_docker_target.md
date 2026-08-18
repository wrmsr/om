# dev 05 — docker exec target (2026-08-18)

Processes can now run inside a running docker container, streamed and managed exactly like local ones.

## What landed

- **`Target`** (`types/options.py`): a new `UniqueTypedValue` ProcOption family - "where a process runs." A Target
  rewrites the spec into the *local* command that reaches the destination, so the manager still spawns/streams/reaps a
  single local process. Absence of a Target == local. The manager applies `options.get(Target).transform_spec(spec)`
  at the very top of `spawn` (before stdio/fd setup), so it composes with everything (pipes, pty, spool, teardown).
- **`DockerExecTarget`** (`targets/docker.py`): wraps argv into `docker exec -i [-t] [--flags] [-w cwd] [-u user]
  [-e K=V]... <container> -- <argv>`. The spec's `cwd`/`env` are interpreted *container-side* (`-w`/`-e`); the local
  docker client's spec gets `cwd=None, env=None` (it inherits the host env to reach the daemon). `PtyStdio` adds `-t`
  (and the client's pty slave gives docker the tty it needs on stdin).
- **`omdev/dockerdev/discovery.py`**: `find_dev_containers()` / `find_dev_container_id(name=)` over
  `omcore.docker.cli.cli_ps`, filtered by the `om.dockerdev` label - the seam for a future "run X in dev container Y"
  API.

Usage: `await scope.run(ProcessSpec(['ls','-la'], cwd='/work', env={...}), DockerExecTarget(container=cid))`.

## Caveat (documented in the target)

Terminating the handle kills the local `docker exec` *client*; depending on the daemon the process inside the
container may keep running. A reliable remote stop needs the in-container pid (`docker exec <c> kill`, or the future
amalgamated in-container agent). Not implemented yet - `Target` is where that signal override will go.

## Tests

- `targets/tests/test_docker.py`: `transform_spec` argv (pipes + pty + minimal); a **fake-`docker` end-to-end** test
  (a bash shim emulating `docker exec ... -- cmd` by running cmd locally, honoring `-w`/`-e`) that exercises the full
  Target -> spawn -> stream path with **no daemon** - verifies stdout, stderr, env-via-`-e`, and cwd-via-`-w`; and a
  **daemon-gated live** test (`busybox sleep`, real `docker exec`) that skips when `/var/run/docker.sock` is absent
  (as here). Run it on a box with dockerd to exercise the real path.

## Next for remote

- `SshTarget` (ssh with a shared ControlMaster) - same `Target` pattern, deferred.
- Remote signal semantics on `Target` (the kill caveat above).
- The in-container amalgamated agent (ominfra/manage pyremote-style) for real remote process control without the
  coarse `docker exec` client - the long-game the user flagged.

## Follow-up (flake fix, 2026-08-18)

The live docker test flaked on macOS with `OCI runtime exec failed` (rc 127): `docker exec` fired before the
just-`docker run -d`'d container was fully up. This is a container-startup race, not a `DockerExecTarget` bug (the
target execs into an assumed-running container). Fixed the test with `_wait_container_ready()` - it probes
`docker exec <cid> true` until it succeeds (20s budget, else `pytest.skip`) before the real exec. No production
change: callers are expected to target an already-running container.
