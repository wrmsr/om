# Supervisor configuration compatibility

This matrix closes the compatibility checklist against the dataclasses in `x/supervisor/configs.py`. It describes
behavioral equivalents, not an INI compatibility parser. Systevisor's JSON/TOML/YAML schema is intentionally nested,
uses literal argv arrays, and separates identity, restart, stop, stdio, dependency, health, and resource policy.

## `ProcessConfig`

| Supervisor rebuild field | Systevisor equivalent | Notes |
| --- | --- | --- |
| `name`, `group`, `namespec` | `units` mapping key, `collections`, generated `{unit}:{slot}` instance ID | Names are stable typed identities; collections can overlap and are more expressive than one group. |
| `command` | `unit.exec.argv`, optional `unit.exec.executable` | No shell splitting or implicit interpolation. Each argument is literal unless a future explicit Minja mode is selected. |
| `num_procs` | `unit.replicas` | Replica slots are distinct stable instance identities. |
| `num_procs_start` | `unit.replica_start` | Used in generated instance IDs. |
| `user`, `uid` | `unit.identity.user`, `.uid` | Systevisor additionally supports group/GID, supplementary groups, `initgroups`, and optional HOME setup. |
| `umask` | `unit.exec.umask` | Applied in the child after fork and before exec. |
| `directory` | `unit.exec.working_directory` | Applied directly; no shell is involved. |
| `environment` | `unit.exec.environment`, `.inherit_environment` | Explicit mapping plus controllable inheritance. |
| `priority` | `unit.priority` | Lower starts earlier; reverse order is used for stopping. Dependencies override mere priority when required. |
| `auto_start` | `unit.autostart` | Collection and dependency claims remain separate from configured autostart. |
| `auto_restart` | `unit.restart.mode` | `never`, `unexpected`, or `always`. |
| `start_secs` | `unit.restart.start_secs` | Monotonic deadline; zero is supported. |
| `start_retries` | `unit.restart.start_retries` | Includes explicit initial/multiplier/maximum backoff controls. |
| `stop_signal` | `unit.stop.signal` | Named signals are normalized and validated before activation. |
| `stop_wait_secs` | `unit.stop.timeout_secs` | Monotonic escalation deadline. |
| `stop_as_group` | `unit.stop.scope: session` | A session is created before exec and is signaled only through the leader run's active lease. |
| `kill_as_group` | `unit.stop.kill_scope: session` | May differ from graceful scope. A null kill scope inherits graceful scope. |
| `exitcodes` | `unit.restart.expected_exit_codes` | Kept separate from startup-stability failure. |
| `stdout`, `stderr` log `file` | `unit.stdio.stdout|stderr.mode: file` and `.file` | Rotation is built in. A null file uses the manager's absolute `child_log_directory`. |
| log `capture_max_bytes` | output `.back_buffer_bytes` | Raw bytes use absolute offsets and gap reporting. |
| log `events_enabled` | output `.emit_events` | Independent log streams remain directly available even when events are disabled. |
| log `syslog` | output `.syslog` | An additional injected sink, so file plus syslog works together. |
| log `backups`, `max_bytes` | output `.backups`, `.max_bytes` | Zero maximum disables rotation; zero backups truncates in place on rotation. |
| `redirect_stderr` | `unit.stdio.redirect_stderr` | Child FD topology is prepared before fork. |

Systevisor also exposes stdin policy, service versus oneshot behavior, explicit dependency conditions, startup/readiness/
liveness probes, cgroup limits, namespaces, activation sockets, resource observation, tags, and manager-signal rewriting.

## `ProcessGroupConfig`

`name` maps to a named collection and `priority` is represented by the priorities of its selected units. Collections
also carry autostart, failure/stop-together behavior, a description, aggregate status, and explicit desired claims.
One unit may appear in more than one collection, which deliberately avoids Supervisor's one-parent object hierarchy.

## `ServerConfig`

| Supervisor rebuild field | Systevisor equivalent | Notes |
| --- | --- | --- |
| `user` | `manager.user` | `manager.group` is also supported; identity reduction happens during cold bootstrap. |
| `no_daemon` | `manager.foreground` | Foreground is the safer default. |
| `umask` | `manager.umask` | Applied before runtime files are opened. |
| `directory` | `manager.working_directory` | Process-global and immutable during reload. |
| `pidfile` | `manager.pid_file` | Held as an open exclusive lock and never used as signal authority. |
| `identifier` | `manager.identifier` | Also used in service templates and manager status. |
| `min_fds`, `min_procs` | same manager fields | Best-effort soft-limit elevation with hard-limit checks. |
| `no_cleanup` | inverse of `manager.cleanup_auto_logs` | Cleanup matches only Systevisor's generated child-log filename namespace. |
| `strip_ansi` | `manager.strip_ansi`, output `.strip_ansi` override | Applied before rings and sinks. |
| `log_file` | `manager.log.file` | Optional rotating manager log. |
| `log_file_max_bytes`, `log_file_backups` | `manager.log.max_bytes`, `.backups` | Uses the manager-owned omcore logging handlers. |
| `log_level` | `manager.log.level` | Validated standard logging name. |
| `child_log_dir` | `manager.child_log_directory` | Must be absolute; created under the final manager identity. |
| `silent` | inverse of `manager.log.stderr` | File and journald sinks remain independent. |
| `groups`, `processes` | top-level `collections`, `units` mappings | Directory sources allow one definition per file. |
| `group_config_dirs` | repeated config paths and `--recursive` directory discovery | Deterministic extension-filtered JSON/TOML/YAML composition with provenance. |
| `http_port` | `api.tcp_host`, `api.tcp_port` | TCP is explicit; there is no HTML or XML-RPC surface. |
| `http_socket_path` | `api.unix_socket`, `.unix_socket_mode` | Unix JSON-over-HTTP is the intended default. |

## Intentionally absent Supervisor surfaces

The HTML UI, XML-RPC, persistent XML-RPC client connections, and text event-listener subprocess protocol have no
compatibility layer. Their supported replacements are JSON HTTP operations, replayable typed events, chunked NDJSON
streams, and injected in-process subscribers. Systevisor also does not parse Supervisor INI syntax or its Python `%`
string expressions. Those omissions are product choices rather than unfinished mappings.

## Deferred extensions

- Explicit Minja rendering modes for selected fields; all strings remain literal today.
- Composite boolean health expressions; individual startup/readiness/liveness probes are implemented.
- Named civil timezones beyond UTC cron without bundling a timezone database.
- PID/user namespaces and launchd named-socket acquisition pending stronger ownership protocols.
- A typed arbitrary unit reload action (for example nginx `HUP`) through the control API. Manager-originated configured
  signal forwarding and rewriting already use the same safe run-lease path.
