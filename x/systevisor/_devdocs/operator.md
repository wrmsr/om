# Operator guide

## Artifact and configuration

Deploy `_bin/systevisor.py` as one atomically replaceable file. It needs only a POSIX host with CPython 3.8 or newer;
the checkout, a virtualenv, and third-party packages are not runtime dependencies. Generate it in the repository with:

```text
./python -m omdev.amalg gen -m omcore x/systevisor
```

Pass one or more JSON, TOML, or YAML files/directories. Directory entries are sorted and merged strictly; duplicate
leaf definitions are errors. `--recursive` enables nested discovery. Always check a candidate before deployment:

```text
python3 systevisor.py config-check -c /etc/systevisor
python3 systevisor.py serve -c /etc/systevisor --recursive --state-directory /var/lib/systevisor
```

A representative YAML configuration is:

```yaml
manager:
  identifier: app-stack
  pid_file: /run/systevisor.pid
  state_directory: /var/lib/systevisor
  child_log_directory: /var/log/systevisor/children
  log:
    level: INFO
    file: /var/log/systevisor/manager.log
    stderr: true
    journald: false
  self_update:
    enabled: true
    probe_timeout_secs: 10
    response_grace_secs: 0.1

api:
  unix_socket: /run/systevisor.sock
  unix_socket_mode: 384  # 0600 in decimal JSON/YAML-compatible form

units:
  redis:
    exec:
      argv: [/usr/bin/redis-server, /etc/redis.conf, --daemonize, "no"]
    restart:
      mode: unexpected
      start_secs: 1
    stop:
      signal: TERM
      timeout_secs: 20
      scope: process
    stdio:
      stdout:
        mode: file
        back_buffer_bytes: 1048576
        syslog: false
      stderr:
        mode: file
    health:
      - name: ready
        role: readiness
        kind: tcp
        host: 127.0.0.1
        port: 6379

  web:
    exec:
      argv: [/opt/app/python, -m, app]
      working_directory: /opt/app
      environment:
        PORT: "8000"
    dependencies:
      requires:
        redis: ready
    signals:
      forward:
        USR1: HUP
      scope: process
    stdio:
      stdout:
        mode: capture
        syslog: true
      stderr:
        mode: capture

collections:
  app:
    units: [redis, web]
    stop_together: true
```

`argv` is always an array and is never interpreted by a shell. Use `/bin/sh -c ...` explicitly only when shell
behavior is actually wanted. Current strings are literal; `variables` are reserved for future opt-in Minja rendering.

## Starting and controlling

Global client options precede the command:

```text
python3 systevisor.py --endpoint unix:/run/systevisor.sock status
python3 systevisor.py --endpoint unix:/run/systevisor.sock units
python3 systevisor.py --endpoint unix:/run/systevisor.sock start app --kind collection
python3 systevisor.py --endpoint unix:/run/systevisor.sock logs 1 stdout --offset 0 --follow
python3 systevisor.py --endpoint unix:/run/systevisor.sock events --after 0 --follow
python3 systevisor.py --endpoint unix:/run/systevisor.sock shutdown
```

`run COLLECTION` is the compose-like foreground mode. It starts only the selected collection plus its dependencies,
returns zero for successful all-oneshot completion or a clean stop, and returns nonzero for startup/failure outcomes.

Mutations return operation records. `pending` means reconnect to `/v1/operations/{id}` or follow operation events;
HTTP handlers never wait for a process transition. A unit is addressed by name, an instance by `{unit}:{slot}`, and an
execution by its monotonic run ID. No API accepts a PID or PGID.

## Reload and failed configuration

`check` compiles current sources without applying; `reload` prepares all runtime consumers and then atomically commits
the candidate. Unchanged units keep their runs. Execution/identity/FD/session/isolation changes drain and replace only
affected runs; live health/restart/log policy changes do not restart them.

An invalid live candidate leaves the active snapshot untouched. Diagnostics appear in `GET /v1/config`, events, the
operation result, and `config-status.json` under the effective state directory. Invalid cold start prints structured
diagnostics to stderr and exits 2. Systevisor never silently boots a stale last-known-good snapshot.

## Process and signal rules

Run services in the foreground. Do not configure them to daemonize and do not use their pidfiles as a control path.
Group delivery uses an isolated child session. `stop.scope` controls the graceful signal; `stop.kill_scope` controls
escalation and inherits the graceful scope when null. Changing either session requirement restarts the run so
Systevisor never attempts a group signal against a process which was not prepared as an owned session leader.

Manager `TERM`, `INT`, and `QUIT` start dependency-ordered graceful shutdown; `HUP` checks/reloads config; `CHLD` is
reaping. Other configured catchable signals enter the engine and use each unit's `signals.forward` rewrite. Signal
delivery always resolves a run, acquires its non-reaping lease, revalidates ownership, and then uses pidfd/direct-child
or owned-session delivery. `KILL` and `STOP` cannot be incoming forwarding signals.

## Child output

`capture`, `file`, and `stdout` modes give the manager a nonblocking pipe and therefore support byte rings and stream
followers. `inherit` and `devnull` do not. `stderr.mode: stdout` performs `2>&1`. A `file` mode with no path writes a
generated rotating file beneath `manager.child_log_directory`; cold cleanup removes only generated filenames.
`syslog: true` adds an injected syslog sink alongside capture/file output. Sink failure emits an event and is detached
without stopping pipe drainage.

Clients track absolute byte offsets. A positive `gap_bytes` means the requested prefix fell out of the bounded ring.
Slow HTTP followers have independent bounded queues and cannot backpressure child pipes.

## Self-update

Supply an absolute path to a newly generated artifact:

```text
python3 systevisor.py --endpoint unix:/run/systevisor.sock self-update /opt/systevisor/new/systevisor.py
```

Systevisor pins and probes the candidate as an owned child, waits for a stable reconciliation point, responds, and
then replaces itself with `execve`. The manager PID, children, wait rights, pidfds, output pipes/rings, pidfile lock,
activation sockets, events, and operations survive. Control connections/listeners are intentionally recreated, so
the client reconnects. A reconstruction failure execs the pinned previous artifact and marks the operation failed.
Do not modify either source path during the operation; digest changes fail closed.

## Host integration

Use `service-template systemd` or `service-template launchd` to print an opaque service definition. The command never
installs or activates it. systemd should own only Systevisor, use `Type=notify`, and retain `KillMode=process` so the
manager can drain children itself. Container deployments should run the artifact directly as PID 1 without dumb-init;
subreaper/unknown-child cleanup and configured signal delegation are built in.

Cgroups require a pre-delegated cgroup-v2 root; Systevisor does not edit ancestor delegation or use `cgroup.kill`.
Activation sockets are adopted only from a valid systemd-style `LISTEN_PID/FDS/FDNAMES` set and only explicitly named
unit selections are inherited. See `nginx.md` for a foreground-master nginx configuration.

## Troubleshooting order

1. Run `config-check` and inspect every structured diagnostic.
2. Query `config`, `operations`, `units`, and `collections` over the Unix endpoint.
3. Read the run's stdout/stderr ring before inspecting external sinks; sink failure does not imply lost ring bytes.
4. Check `resources RUN` for birth-validated process/cgroup samples and observation errors.
5. Follow `events` from a known sequence to see desired, lifecycle, health, operation, and gap transitions.
6. For host-boundary bugs, enable the opt-in one-container-per-test harness rather than adding sleeps to ordinary
   tests.
