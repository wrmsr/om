# dev 07 — ssh target (2026-08-18)

Remote execution over ssh, completing the Target family (local / docker / ssh). Same shape as `DockerExecTarget`.

## What landed (`omllm/core/processes/targets/ssh.py`)

- **`SshTarget`** (`Target`): rewrites the spec into `ssh [-p port] [-i key] [-tt] [ControlMaster opts]
  [StrictHostKeyChecking=no] [extra] user@host <remote-command>`. The spec's cwd/env are folded into the remote
  command string (`cd <cwd> && exec env K=V ... <argv>`, all `shlex.quote`d - ssh runs a *string* through the remote
  shell, not an argv vector). Local client gets `cwd=None, env=None` (inherits host ssh config / agent).
- **ControlMaster sharing**: setting `control_path` adds `-o ControlMaster=auto -o ControlPath=... -o
  ControlPersist=60s`, so many execs to one host reuse a single connection (the user's "shared managing master").
- **`build_remote_command(spec)`** is factored out and unit-tested for the quoting.
- `PtyStdio` -> `-tt` (force a remote tty); `no_host_key_checking` for throwaway hosts; `extra_options` for raw `-o`.

Usage: `await scope.run(spec, SshTarget(host='dev', user='om', control_path='/tmp/cm-%r@%h:%p'))`.

## Tested

- `build_remote_command` quoting (spaces in cwd / env / argv), `transform_spec` argv (port/key/control/pty/host).
- **fake-`ssh` end-to-end**: a shim that runs the remote-command string (its last arg) locally via `sh -c`, proving
  the quoting round-trips and output streams - verifies cwd (via `cd`), env (via `env`), stdout + stderr, no daemon.
- **gated live** localhost test (skipped here - no sshd on 127.0.0.1:22).

## Caveat (documented)

Killing the handle kills the local `ssh` client; without a remote tty (`-tt`) the remote command can outlive it. A
reliable remote stop is the same open item as docker - the future in-container/remote agent, or a control-socket
`ssh -O exit` / remote `kill`. `Target` is where that signal override goes.

## Roadmap status

All planned processes phases (1-6) are now done: core manager, agent integration, background tools, sandbox, PTY, and
the docker + ssh targets. Remaining ideas live in the individual dev notes (remote-signal semantics, per-turn DI
scopes, plain-text output dump, the in-container amalgamated agent, migrating the rg-specific sandbox onto the
general one).
