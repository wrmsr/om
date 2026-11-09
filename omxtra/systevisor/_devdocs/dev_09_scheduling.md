# Development 09: deterministic schedules and durable time state

## Goal and choices

This phase adds cron-style actions without creating a second process-control system. The key choice is that a schedule
fires a normal `SystevisorControlService` operation. It can start/stop a unit, collection, or instance; restart a unit
or instance; or request manager shutdown. Scheduled oneshot work is therefore modeled as restarting a normal oneshot
unit, preserving its identity, logs, health behavior, dependencies, and owned-process safety.

The persistence choice is the deliberately small one from the requirements: a versioned, atomically replaced JSON
document. SQLite would add little for one single-threaded writer unless schedule history, external queries, or
multi-manager claims become requirements. `SystevisorScheduleStateStore` is injected, so that decision is reversible.

## Configuration and cron

`SystevisorConfig.schedules` maps stable names to a fine-grained schedule config:

- classic five-field `cron` text;
- an action kind plus optional target kind/name;
- enabled state;
- timezone;
- missed-run policy (`skip`, `latest`, or `all`);
- a positive catch-up bound; and
- concurrency policy (`allow` or `skip`).

Validation parses the expression, checks the action/target combination against units, collections, and replica IDs,
and rejects unsupported collection restarts. Shutdown intentionally has no target. The initial timezone is UTC only.
Stock Python 3.8 has no guaranteed `zoneinfo` module or IANA database, and silently using the host's local timezone
would make artifacts non-reproducible. Named timezone support stays explicit future work.

The parser supports lists, ranges, steps, Sunday as 0 or 7, and classic cron's OR behavior when both day-of-month and
day-of-week are restricted. Calculation is pure and returns epoch wall timestamps. Tests cover parsing and calendar
semantics without reading the host clock.

## Runtime model

The scheduler is both a configuration participant and an fdio deadline handler. Configuration preparation parses all
expressions and loads/validates durable state before the engine accepts a candidate. Commit swaps an ordinary mapping
of schedule dataclass state. Removed and disabled schedules disappear immediately; unchanged fingerprints keep their
last evaluated occurrence and pending operation identity; changed fingerprints start at the current minute and do not
retroactively apply a new definition.

Wall time answers which occurrence is next. Each poll maps that delta onto the injected monotonic clock. The handler
also wakes at least once per minute, so backward or forward wall-clock jumps are noticed without contaminating
lifecycle deadlines. No sleep, background thread, or asyncio timer is involved.

An occurrence is considered on-time within its minute. Multiple or stale due occurrences are handled by policy:

- `skip` discards stale occurrences but still fires the current minute;
- `latest` coalesces a backlog to its newest occurrence; and
- `all` runs only the configured `max_catch_up` prefix and counts the rest as skipped.

If concurrency is `skip`, an occurrence is suppressed while the previous control operation remains pending. `allow`
submits another independent operation. Fired and skipped decisions publish typed `schedule` events. State exposes last
evaluated/fired times, next due time, operation ID, and cumulative fire/skip counts at `GET /v1/schedules` and through
the `schedules` CLI client command.

## Persistence

`schedules.json` lives in the CLI state-directory override when supplied, otherwise in the configured manager state
directory. It stores only the definition fingerprint, last evaluated/fired wall timestamps, and counters. Runtime
operation IDs are intentionally not durable because the operation store and live process state are not yet rehydrated
across manager restart.

Writes use a same-directory temporary file, full write loop, file fsync, atomic replace, and directory fsync. A missing
file means first start. A malformed or wrong-schema file rejects cold configuration preparation rather than silently
guessing. A write failure after activation publishes `schedule.persistence_failed`; it does not roll back an already
accepted process snapshot.

Every evaluated occurrence advances `last_due_wall_time`, including skipped ones. This avoids retrying the same missed
action forever after restart. A matching fingerprint enables explicit catch-up after downtime, while a changed
fingerprint resets the baseline.

## Tests and observations

Virtual-clock tests cover exact monotonic arming, normal control-operation dispatch, latest coalescing, pending-operation
suppression, bounded all catch-up, durable restart catch-up, event emission, and JSON round trips. Control tests compile
schedule config and serialize live scheduler state through the API. All run without sleeps or subprocesses.

The full suite now has 94 tests: 93 pass and the opt-in Docker scenario skips without its enabling environment. The
same suite passes under Python 3.8 (with the development-only amalgamation regeneration test skipped), and the newly
generated single-file artifact starts under isolated Python 3.8.

## Next

The next phase is resource observation and optional Linux isolation. It should begin read-only: typed procfs/Darwin
samples keyed by run identity and exposed through state/API. Any cgroup or namespace mutation must be represented as a
prepared child capability/config plan, remain optional, and never become another way to signal a numeric PID.
