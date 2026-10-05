# Development 14: stop ordering, scheduler clock handling, and cgroup naming

## Intent

Three findings from the first audit that Development 13 left alone, each a place where the documented behaviour and
the implemented one had parted: shutdown was described as dependency-ordered and was not, schedules were described as
recalculating on clock jumps and instead stalled or went silent, and run cgroups could not survive a manager restart.

## Findings and changes

- Stops are now the reverse of starts. `_stabilize` used to signal every instance due to stop in one step, sorted by
  priority, so a database got `TERM` at the same moment as - and, alphabetically, before - the web tier using it.
  An instance is now signalled only once every unit depending on it that is also on its way down has exited. A
  waiting instance is visible through `blocked_reason` (`web:stopping`) and the existing dependency-blocked events.
- Deliberately unchanged: a dependent that is staying up does not hold its dependency, and stopping a dependency does
  not stop its dependents. Priority remains an ordering within a step and is not waited on, which differs from
  Supervisor's sequential reverse-priority stop; `compatibility.md` now says so.
- Validation rejects ordering cycles, but the engine does not rely on that to terminate: instances which only wait on
  each other, with nothing they lead to already exiting, are stopped together.
- Cron's next occurrence was a minute-by-minute scan: 0.46 s for a yearly expression, 2.2 s for a leap day, 4.3 s to
  give up on an impossible date, all on the reactor thread and repeated on every reload. It and a new
  previous-occurrence search now step whole fields and take microseconds. An impossible date is rejected at
  validation rather than at prepare.
- Catch-up walked every missed occurrence and raised past five million, so a manager started before its clock was set
  blocked for seconds and then died, again on every restart. What to fire is now derived from the present, the walk is
  only a count and stops at a thousand, and bounded `all` catch-up replays the most recent occurrences where it used
  to replay the oldest and leave out the one actually due.
- A backward clock step silenced schedules until wall time re-reached the last evaluated occurrence, and persisted
  that future time across restarts. Steps of up to three hours are still waited out, so nothing fires twice; larger
  ones re-baseline to the new time and publish `schedule.clock_stepped`. Vixie cron uses the same rule and threshold.
- Scheduler state is written only when something changed, not on every wake.
- Run cgroup names were `sv-<run>-<digest>`, and run identities restart from 1 with every manager, so any directory a
  previous manager left behind made the next start fail with `EEXIST`. Names now carry the manager incarnation (pid and
  start time), which is stable across a self-update exec, and a validated root is swept of other incarnations' empty
  groups on first use. Populated leftovers are reported, not touched. An unwritable root is rejected at configuration
  time. Cgroup run state schema is now 2.

## Deliberately not changed

- Stop propagation to dependents, and priority-gated stops.
- A damaged `schedules.json` still fails a cold start, and a schedule whose previous operation never finishes is still
  suppressed by `concurrency: skip`.
- Cron day fields beginning with `*/N` still follow the plain either-matches rule rather than Vixie's.
- Removed cgroup run states are still only pruned by the observer's sampling pass.

## Verification log

- Engine: the stop-ordering tests cover a five-unit graph with every edge type and replicas, a lone dependency stop,
  and an ordering loop. Live, with a web unit taking 0.6 s to stop and a database it requires, the database's stop was
  logged 50 ms after the web unit's exit.
- Cron searches agree with scanning every minute across a spread of expressions and start times, in both directions.
- Scheduler, with a fake clock: a 56-year forward step on an every-minute schedule takes about 2 ms under each
  policy, where it previously blocked for 14 s and raised.
- Cgroups: the real sweep was exercised against an ordinary directory tree, whose `rmdir` semantics match for this
  purpose. The cgroup filesystem here is read-only, so creating and joining a real run group remains unexercised.
- Default interpreter: 152 passed, 2 Docker scenarios skipped. CPython 3.8 unittest discovery: 154 run, 3 skipped.

## Next

- The control-API bind rule, self-update trust check, and the remaining smaller audit items.
- A delegated-cgroup host gate, so the real cgroup filesystem paths are exercised somewhere.
