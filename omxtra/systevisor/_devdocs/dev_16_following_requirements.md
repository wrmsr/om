# Development 16: following a requirement

## Intent

`requires` gated a start and, since Development 14, ordered a stop, but stopping or restarting a requirement did
nothing to the units depending on it. Init systems with hard dependencies propagate a deliberate stop and restart by
default (systemd `Requires=`, OpenRC `need`, s6-rc, monit); orchestrators do not (Compose, with restart propagation as
a per-edge opt-in); almost nothing propagates a crash unless asked (systemd `BindsTo=`, OTP `rest_for_one`). This
phase makes it a per-edge, opt-in choice.

## Shape

- A requirement is a bare condition, as before, or an object `{condition, follow}` where `follow` is any of `stop`,
  `restart`, and `failure`. Per edge rather than per unit because one unit commonly requires both a long-running
  service and a oneshot that has completed, and those should not be followed alike.
- The bare form is still what a requirement that follows nothing marshals to, so existing configurations keep their
  digests.

## Semantics chosen

- `stop` and `failure` are holds, recomputed with every reconciliation like the dependency claims they sit beside,
  rather than one-shot propagated stops. That is what makes the follower return by itself when its requirement does.
  A held instance is `inactive` with origin `follow` and a `blocked_reason` naming the edge.
- "Down on purpose" is any instance of the required unit left inactive by an operator, a stopped collection, its
  health check, or shutdown - not one that simply was never asked for, which the follower's own claim activates.
- A claim through an edge that follows stops does not resurrect a unit its collection stopped, where an ordinary
  `requires` claim always has. Otherwise following a stop would be undone by the follower's own claim.
- A hold applies to manually started instances too, since anything started through the API is manual from then on and
  would otherwise never follow. `resume_manual` on the instance remembers that for when the hold ends (engine state
  schema 4).
- "Failed" is the definition collections already use for `stop_together`: fatal, exited without being restarted, or
  stopped by its own health check. It is judged from process state alone, so holding the follower - which withdraws
  its claim on the requirement - cannot flip the answer.
- `restart` is triggered by the three places a restart is requested on purpose: the restart command, a
  restart-required configuration change, and liveness recovery. A crash the restart policy recovers from is not
  followed under any of the three values.
- A requirement restarted while it was not running - a completed oneshot being re-run - has no stop to order behind
  its followers', so its start is gated on theirs.

## Verification log

- Engine tests cover a chain of followers held and released in order, manual intent across a hold, restart following
  including a configuration change, the re-run of a completed requirement, failure holds and their release, and a
  self-recovering crash following nothing. The existing claim, collection, and ordering tests pass unchanged.
- Live, with `web` following `db` on `[stop, restart]` and `cache` merely requiring it: stopping `db` stopped `web`
  first and left `cache` on the same run; starting `db` brought `web` back; restarting `db` produced
  `web stopping, web stopped, db stopping, db stopped, db starting, db running, web starting, web running`.

## Next

- Whether a crash-and-restart of a requirement should be followable as a fourth value.
- An operation deadline, which holds make slightly more visible: a start of a held unit stays pending until the hold
  ends.
