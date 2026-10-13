# dev 14 — remote pty children and ignored signals (2026-10-11)

A process the remote agent started under a pty ran with SIGPIPE (and SIGXFSZ) ignored: `yes | head -n 1` in a remote
shell ended with `yes: standard output: Broken pipe` rather than quietly. Local pty children, and remote pipe children,
were fine.

## Cause

CPython ignores SIGPIPE and SIGXFSZ (and SIGXFZ, where there is one) at interpreter startup, and an ignored disposition
is one of the few things an exec inherits. `subprocess.Popen` knows this and puts them back in its child
(`restore_signals`, on by default) - which covers the pipe path, where the child execs the target directly. The pty
path's child is another python: the bootstrap (`_REMOTE_PTY_CHILD_CODE`) which makes itself a session leader and takes
the pty as its controlling terminal before it execs the target. Popen restored the dispositions for that interpreter,
which ignored them again on its way up, and then handed them to the target.

The local manager never had the problem: its shim resets signal dispositions as one of its stages.

## Fix

The bootstrap sets the three back to `SIG_DFL` before its exec. `omllm/agent/remote/tests/test_remote.py` pins it for
both stdio kinds, through the real payload: a child which sends itself SIGPIPE dies of it.

## Found by

The repl's bash (`omdev/repl/bash`, adapted to this package by `omllm/ui/tui/minitui/repl/ptys.py`) - the first
long-lived, interactive tenant of a remote pty, and the first thing to run a pipeline on one. Two things it needed of
this package which were already here, for the record:

- A hangup as the termination signal (`TerminationPolicy(signal=SIGHUP)`): an interactive shell is deaf to SIGTERM, and
  would otherwise sit out the whole grace period.
- Output end is not process exit, as `handles.py` says, and for a shell the difference is routine: a background job
  outlives it holding the pty, which the kernel does not hang up when a session leader on a pty exits. The adapter
  closes the handle as soon as the leader is seen to exit - sweeping the group - rather than wait for an end of output
  which would not come.
