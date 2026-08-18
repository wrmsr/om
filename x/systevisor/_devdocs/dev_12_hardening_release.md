# Development 12: compatibility, hardening, and release

## Intent

The final initial phase turns the implemented subsystems into an operable package rather than merely a broad feature
set. The concrete gates are: account for every field in the shelved rebuild's config dataclasses, close real behavioral
gaps instead of papering over them in a matrix, harden replaceable boundaries, document safe operation, and validate
the generated artifact on the oldest supported interpreter.

## Compatibility findings and changes

- The earlier stop policy collapsed Supervisor's `stop_as_group` and `kill_as_group`. Added optional `kill_scope` so a
  graceful direct signal can escalate to an owned session. Either session scope now prepares `setsid` before exec, and
  changing a session requirement is restart-required rather than an unsafe live policy update.
- The old output config could write a rotating file and syslog simultaneously. Added an injected child syslog writer
  and independent `syslog` output flag; sink failures detach only that sink while the ring and other sinks continue.
- Made `child_log_directory` and `cleanup_auto_logs` functional. A null file in file mode generates a run-specific path
  in an absolute manager directory. Cleanup matches only the exact Systevisor auto-log namespace and leaves unrelated
  files and symlinks alone.
- Manager signal delegation previously handled graceful termination but did not provide configurable non-termination
  forwarding. Added validated per-unit incoming-to-outgoing rewrites, dynamic signal handler reconfiguration, a typed
  engine command/event/effect path, and session preparation when forwarding scope requires it. Reserved manager
  control signals cannot be shadowed.
- Self-update close now terminally fails an in-flight operation after lease-protected probe termination, rather than
  leaving an observable pending record in an embedded/test context.
- Rehydrated rotating-file sinks now always reopen in append mode even when their cold-start policy was truncate. This
  prevents a successful self-update from destroying pre-exec log bytes; later cold runs still honor `append: false`.
- CLI self-update canonicalizes its candidate path, and the manager rejects ambiguous relative source paths.

## Documentation

- `compatibility.md` is the field-by-field mapping for all three old rebuild dataclasses and names intentional product
  exclusions separately from deferred extensions.
- `operator.md` covers artifact deployment, split configuration, lifecycle commands, reload failure visibility,
  signal/group safety, child logs, self-update/rollback, systemd/launchd/container operation, and troubleshooting.
- `release.md` records generation, lint/type/test, Python 3.8, Docker, host-gate, and atomic publishing requirements.

## Verification log

- Focused compatibility/hardening tests initially passed 70/70 after signal routing, split escalation scope, injected
  syslog, automatic logs, config validation, and source guards were added.
- Whole-tree Systevisor Ruff and mypy passed across 83 source files, as did `git diff --check`.
- The freshly generated artifact is 1,214,857 bytes / 35,105 lines with SHA-256
  `d842b5e72a89cbf9adc56c57a7fbc9378302484595a86c5dfcab95d1da26776e` at this checkpoint.
- Default pytest collected 121 cases: 119 passed and the two explicitly opt-in Docker scenarios skipped.
- CPython 3.8 unittest discovery ran all 121 cases successfully with three expected skips (Docker plus the
  development-interpreter-only regeneration check).
- Enabling `SYSTEVISOR_DOCKER_TESTS=1` still produced two explicit `Docker daemon is unavailable` skips. No container
  was created in this sandbox; the successful handoff remains covered by the host live exec from Phase 10 and the
  rollback scenario remains ready for a daemon-equipped host.
- Repository-wide `make fix gen check` passed, including the lite Python 3.8 syntax precheck, flake8, Ruff, mypy over
  3,672 source files, manifest checks, and generated-file bookkeeping.

## Next

- Phase 11 is release-gated and ready to commit. The final pass regenerated the artifact after repository-wide
  generation, reproduced the recorded digest, passed Ruff/mypy over all 83 Systevisor source files, passed all 121
  default-interpreter cases (119 pass plus two Docker skips), and passed all 121 CPython 3.8 unittest cases (three
  expected skips).
- Future work should begin a new journal rather than reopening the initial implementation phases. The explicit
  deferred list in `compatibility.md` is the starting backlog, with opt-in Minja rendering and a typed unit reload
  action the most natural next slices.
