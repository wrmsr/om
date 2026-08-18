"""
`subprocess.Popen` used strictly as a *spawner*. INVARIANT: after `Popen()` returns, nothing here (or anywhere) may call
`wait/poll/communicate/send_signal/terminate/kill` on it, or use it as a context manager. Every one of those paths calls
`waitpid` and would reap - or race with - the child whose pid we deliberately hold. `Popen.__del__` does the same (and,
for still-running children, parks the object in `subprocess._active` to be reaped by the *next* `Popen()` call anywhere
in the process), so it is neutralized too. We hold a strong ref to the object for the handle's lifetime and set
`returncode` ourselves after our own reap.
"""
import subprocess
import typing as ta

from omcore import check

from ..launch.launcher import LaunchPlan


##


class _SpawnerPopen(subprocess.Popen):
    def __del__(self) -> None:  # noqa
        # NEVER waitpid behind the manager's back.
        pass

    def _forbidden(self, *args: ta.Any, **kwargs: ta.Any) -> ta.NoReturn:
        raise TypeError('This Popen is a spawner only - process lifecycle is owned by the processes manager')

    poll = _forbidden
    wait = _forbidden
    communicate = _forbidden
    send_signal = _forbidden
    terminate = _forbidden
    kill = _forbidden
    __enter__ = _forbidden
    __exit__ = _forbidden


def spawn_popen(
        plan: LaunchPlan,
        *,
        stdin: ta.Any,
        stdout: ta.Any,
        stderr: ta.Any,
        session_mode: ta.Literal['session', 'group'],
) -> _SpawnerPopen:
    """Must be called from the event loop thread (a `Deathsig` binds to the *thread* that forked)."""

    kw: dict[str, ta.Any]
    if session_mode == 'session':
        kw = dict(start_new_session=True)
    elif session_mode == 'group':
        kw = dict(process_group=0)
    else:
        raise ValueError(session_mode)

    return _SpawnerPopen(
        list(check.not_empty(plan.argv)),
        env=dict(plan.env),
        cwd=plan.cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        pass_fds=list(plan.pass_fds),
        close_fds=True,
        restore_signals=True,
        **kw,
    )
