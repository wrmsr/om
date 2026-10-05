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

Every child is exec'd with default signal dispositions and an empty signal mask, whatever the manager itself inherited
or ignores (the interpreter ignores `PIPE`). A signal sent to a run that has forked but not yet exec'd is held until
the child has shed the manager's handlers, and then acts on the child as it would on the program.

## Stop ordering

Units stop in the reverse of the order they start in. On shutdown, a collection stop, or a reload that removes units,
a unit is signalled only after every unit depending on it (`requires`, `wants`, `after`, or named in its `before`)
that is also stopping has exited; `units` shows a waiting instance still `running` with `blocked_reason` set to, for
example, `web:stopping`. Each unit's `stop.timeout_secs` starts when it is signalled, so allow the sum along the
longest dependency chain when setting a host stop deadline such as systemd `TimeoutStopSec` or `docker stop -t`.

Stopping a single unit never stops or waits for the units that depend on it. `priority` only orders units within the
same step; express anything that must be waited on as a dependency.

## Restart pacing

A run that exits before `restart.start_secs` is a failed start: it is retried after `backoff_initial_secs`, multiplied
by `backoff_multiplier` each time up to `backoff_max_secs`, and the instance goes `fatal` once `start_retries` is
exhausted. A run that exits after becoming `running` is restarted according to `restart.mode`, immediately the first
time and then on the same backoff curve for as long as its runs keep dying young. Such an instance sits in `backoff`
between attempts but never goes `fatal`. A run that stays up for `backoff_max_secs`, a manual start or restart, or a
restart-required config change clears that history.

## Child output

`capture`, `file`, and `stdout` modes give the manager a nonblocking pipe and therefore support byte rings and stream
followers. `inherit` and `devnull` do not. `stderr.mode: stdout` performs `2>&1`. A `file` mode with no path writes a
generated rotating file beneath `manager.child_log_directory`; cold cleanup removes only generated filenames.
`syslog: true` adds an injected syslog sink alongside capture/file output. Sink failure emits an event and is detached
without stopping pipe drainage.

A run's sinks are closed once its process has been reaped and its output pipe has reached end-of-file; a descendant
still holding the pipe keeps the channel open until it lets go. After that the run's byte ring stays readable until
`manager.retained_child_log_runs` (default 2, live-updateable) newer ended runs of the same instance exist, at which
point it is dropped and reads of it return 404. With `cleanup_auto_logs` enabled the generated per-run files of a
dropped run are removed with it, so a unit that restarts often does not accumulate them; configure an explicit `file`
for output that should outlive its run.

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

Cgroups require a pre-delegated cgroup-v2 root, writable by the manager and not shared with another one; Systevisor
does not edit ancestor delegation or use `cgroup.kill`. Run groups are named `sv-<pid>.<start>-<run>-<instance digest>`
so that a restarted manager never collides with an earlier one's. On first use of the root, empty run groups left by
earlier managers are removed. One that is still populated means a previous manager died without stopping its
children: it is logged, published as `resource.cgroup_swept`, and left for the operator.
Activation sockets are adopted only from a valid systemd-style `LISTEN_PID/FDS/FDNAMES` set and only explicitly named
unit selections are inherited. See `nginx.md` for a foreground-master nginx configuration.

## Schedules and the clock

Schedules are five-field cron in UTC. `missed` decides what happens to occurrences that came due while the manager was
down or the clock jumped forward: `skip` fires only an occurrence that is due right now, `latest` fires once, and `all`
fires the most recent `max_catch_up` in order. However long the gap, this is a bounded amount of work.

If the clock is set back by up to three hours, schedules wait for it to pass where they had reached rather than fire
again. A larger step back is treated as a correction: schedules resume from the new time and a `schedule.clock_stepped`
event records it. A cron expression naming a date that never occurs is rejected when the configuration is checked.

## Manager failure

Control connections are disposable: a client that disconnects, stalls, or sends garbage ends only its own connection.
An effect the manager cannot carry out (a signal the kernel refuses, a spawn whose resources cannot be prepared) is
logged, published as a `runtime.effect_failed` event, and where applicable becomes an ordinary start failure.

An internal error the manager cannot contain is fatal by design rather than survived in an unknown state. It is logged
with its traceback, reported on stderr as `runtime_failed`, and the manager exits 70 - but not before every process it
still owns has been sent its unit's stop signal, given its unit's stop timeout, and then killed. No exit path leaves
children running unsupervised, so a service manager restarting Systevisor never starts a second copy of the stack
beside a stranded first one. Exit 2 remains reserved for a start that never got as far as supervising.

## Troubleshooting order

1. Run `config-check` and inspect every structured diagnostic.
2. Query `config`, `operations`, `units`, and `collections` over the Unix endpoint.
3. Read the run's stdout/stderr ring before inspecting external sinks; sink failure does not imply lost ring bytes.
4. Check `resources RUN` for birth-validated process/cgroup samples and observation errors.
5. Follow `events` from a known sequence to see desired, lifecycle, health, operation, and gap transitions.
6. For host-boundary bugs, enable the opt-in one-container-per-test harness rather than adding sleeps to ordinary
   tests.
