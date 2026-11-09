# Development 17: handoff and startup windows, host template, probes

## Intent

The self-update spine - exec, resume, rollback - had only ever been run by the opt-in Docker scenarios, and the audit
had found several ways for a manager to die around an exec or a cold start and leave its children behind. This phase
tests that spine for real in the ordinary suite and closes the windows that can be closed from inside the process.

## Findings and changes

- Handlers do not survive an exec, and for about half a second after one the new image had none: a `TERM` or `HUP` in
  that time met its default disposition and killed the manager. The signal mask does survive, so every signal is now
  blocked before the exec and released once the new image has installed its handlers. The same is done before the
  rollback exec, and the mask is restored if the exec itself fails.
- The cold start had the same window in miniature: the configuration was applied, spawning the first children, before
  handlers were installed. They are now installed first, so a signal during startup is an ordinary shutdown of what
  was started.
- A candidate whose hidden resume command line had changed died in its own argument parser, before any of its
  recovery code could run. The probe request now carries the exact resume arguments and the candidate's probe refuses
  if it cannot parse them. An image that predates the check ignores the field. A probe's stated reason for refusing is
  now quoted in the failed operation rather than only its exit status.
- A handoff failed outright, in both directions, if the pidfile's path had been removed or replaced - something a
  running manager tolerates. Only the descriptor's identity is checked now; the path is a pointer to it, not the lock.
- When a resume failed and could not be rolled back, the image exited and whatever it had not got round to adopting
  was orphaned. It now proves ownership of the handed-off processes afresh and stops them before exiting 2.
- The systemd template used `KillMode=process`, which leaves children running whenever systemd kills the manager -
  made likelier by ordered shutdowns taking longer. It is now `KillMode=mixed`, with `--stop-timeout` to set
  `TimeoutStopSec`.
- Health probes resolved host names with a blocking lookup on the only thread. Probe hosts must now be IP literals or
  `localhost` (taken as the IPv4 loopback), checked at validation, and the runtime asks only for numeric addresses.
- Notes left for decisions that are not this phase's to make: a TODO on the candidate format check, which is not a
  trust check and is acceptable only while the control socket is treated like the Docker daemon socket; a TODO on the
  event bus dropping a subscriber that raises once; and a block comment on what `priority` does and does not do.

## On an external watchdog

Considered and not built. What remains unhandled after this phase is an image that cannot run at all once exec'd -
killed outright, or failing before its first line of recovery. Nothing in the process can act then, and a helper
process could not take the children over either: they are reparented to a subreaper or init, and only a parent can
wait on them, so a watchdog could do no more than kill them and start again. That is exactly what the service manager
around Systevisor already does, provided it is told to - `KillMode=mixed` under systemd, and the kernel itself when
the manager is PID 1 of a container. A watchdog would only add something for a manager run bare, outside either.

## Verification log

- `tests/test_handoff.py` runs a manager from the artifact in its own process and drives it over its socket, with
  candidates patched to misbehave at a chosen point: two successive updates keeping the manager pid, the child, and
  its run; a failed resume rolling back and the rolled-back image then updating successfully; a candidate refused by
  its probe for its resume command line; a `TERM` delivered between the exec and the resume, held at a FIFO so the
  ordering is exact, becoming a clean shutdown; a resume that can neither complete nor roll back stopping the child;
  and twenty-four units each signalling the manager as it starts them.
- These add about fifteen seconds to the suite, nearly all of it the interpreter compiling the single-file artifact
  on every exec.
- Docker, root, and PID 1 remain unexercised here.
