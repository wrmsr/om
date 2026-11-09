# ruff: noqa: PYI034 UP006 UP007 UP037 UP045
# @om-lite
"""
Darwin's process group signaling, stood in for tests run on Linux.

Linux delivers a group signal to a process group of nothing but zombies without complaint. Darwin does not: XNU's
`killpg1` skips zombie members, and when that leaves nothing to signal it fails with EPERM rather than ESRCH - so a
group whose unreaped leader has exited, and in which nothing else lives, cannot be signaled at all. Code tolerating
that cannot be exercised against the Linux kernel, so `FakeDarwinProcessGroups` makes a Linux process look like it is
on darwin for the duration: `sys.platform` reads 'darwin', and `os.killpg` fails as darwin's does, judging group
membership and liveness from procfs. On darwin itself it changes nothing, the real kernel being the reference.
"""
import errno
import os
import sys
import types
import typing as ta


##


def fake_darwin_process_group_states(pgid: int) -> ta.Dict[int, str]:
    """The procfs state letter of each member of the process group, 'Z' for a zombie, by pid."""

    states: ta.Dict[int, str] = {}
    for name in os.listdir('/proc'):
        if not name.isdigit():
            continue
        try:
            with open(os.path.join('/proc', name, 'stat')) as stat_file:
                stat = stat_file.read()
        except OSError:
            continue
        # The fields follow the parenthesized command name, which may itself contain spaces and parentheses.
        fields = stat.rpartition(')')[2].split()
        if int(fields[2]) == pgid:
            states[int(name)] = fields[0]
    return states


class FakeDarwinProcessGroups:
    """
    While entered, `sys.platform` reads 'darwin' and `os.killpg` behaves as darwin's does: ESRCH for a group with no
    members, EPERM for one with no live members, and the real thing otherwise. On darwin itself nothing is changed. A
    `killpg` given replaces it either way - for injecting what no arrangement of real processes can produce, such as
    EPERM for a live leader - and may itself fall back on `darwin_killpg`.
    """

    def __init__(self, *, killpg: ta.Optional[ta.Callable[[int, int], None]] = None) -> None:
        super().__init__()

        self._killpg = killpg

        self._entered = False
        self._real_platform: ta.Optional[str] = None
        self._real_killpg: ta.Optional[ta.Callable[[int, int], None]] = None

    def darwin_killpg(self, pgid: int, sig: int) -> None:
        """Signals the group as darwin would, over the real `os.killpg` saved on entry."""

        real_killpg = self._real_killpg
        if real_killpg is None:
            raise RuntimeError(f'{self.__class__.__name__} is not entered')
        states = fake_darwin_process_group_states(pgid)
        if not states:
            raise ProcessLookupError(errno.ESRCH, os.strerror(errno.ESRCH))
        if all(state == 'Z' for state in states.values()):
            raise PermissionError(errno.EPERM, os.strerror(errno.EPERM))
        real_killpg(pgid, sig)

    def __enter__(self) -> 'FakeDarwinProcessGroups':
        if self._entered:
            raise RuntimeError(f'{self.__class__.__name__} is not reentrant')
        self._entered = True

        sys_platform: ta.Any = sys.platform  # untyped, or mypy prunes the other platform's branch as unreachable
        if sys_platform == 'darwin':
            killpg = self._killpg
        else:
            if not sys_platform.startswith('linux'):
                raise RuntimeError(f'{self.__class__.__name__} needs procfs, which {sys_platform} lacks')
            killpg = self._killpg if self._killpg is not None else self.darwin_killpg
            self._real_platform = sys_platform
            sys.platform = 'darwin'

        if killpg is not None:
            self._real_killpg = os.killpg
            os.killpg = killpg
        return self

    def __exit__(
            self,
            exc_type: ta.Optional[ta.Type[BaseException]],
            exc_val: ta.Optional[BaseException],
            exc_tb: ta.Optional[types.TracebackType],
    ) -> None:
        if self._real_killpg is not None:
            os.killpg = self._real_killpg
            self._real_killpg = None
        if self._real_platform is not None:
            sys.platform = self._real_platform
            self._real_platform = None
        self._entered = False
