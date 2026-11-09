# @om-lite
# ruff: noqa: PT009 UP006 UP007
import os
import signal
import subprocess
import sys
import unittest

from ..fakedarwin import FakeDarwinProcessGroups


class TestFakeDarwinProcessGroups(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        if not hasattr(os, 'waitid'):
            self.skipTest('needs os.waitid to observe an exit without reaping')

    def test_a_group_of_nothing_but_zombies_cannot_be_signaled(self) -> None:
        proc = subprocess.Popen(['/bin/sh', '-c', 'exit 0'], start_new_session=True)
        try:
            os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOWAIT)
            real_killpg = os.killpg
            real_platform = sys.platform
            with FakeDarwinProcessGroups():
                self.assertEqual(sys.platform, 'darwin')
                with self.assertRaises(PermissionError):
                    os.killpg(proc.pid, 0)
            self.assertIs(os.killpg, real_killpg)
            self.assertEqual(sys.platform, real_platform)
        finally:
            proc.wait()

    def test_a_group_with_a_live_member_is_signaled(self) -> None:
        proc = subprocess.Popen(['/bin/sleep', '60'], start_new_session=True)
        try:
            with FakeDarwinProcessGroups():
                os.killpg(proc.pid, signal.SIGTERM)
        except BaseException:
            proc.kill()
            raise
        finally:
            returncode = proc.wait()
        self.assertEqual(returncode, -signal.SIGTERM)

    def test_a_group_of_no_one_is_not_found(self) -> None:
        proc = subprocess.Popen(['/bin/sh', '-c', 'exit 0'], start_new_session=True)
        proc.wait()  # reaped, and its group with it
        with FakeDarwinProcessGroups():
            with self.assertRaises(ProcessLookupError):
                os.killpg(proc.pid, 0)

    def test_on_darwin_itself_nothing_is_faked(self) -> None:
        # Played here by any platform: entered on darwin, the real kernel is left to be the reference.
        proc = subprocess.Popen(['/bin/sleep', '60'], start_new_session=True)
        try:
            real_killpg = os.killpg
            real_platform = sys.platform
            sys.platform = 'darwin'
            try:
                with FakeDarwinProcessGroups() as fake:
                    self.assertIs(os.killpg, real_killpg)
                    fake.darwin_killpg(proc.pid, signal.SIGTERM)
            finally:
                sys.platform = real_platform
            self.assertIs(os.killpg, real_killpg)
        except BaseException:
            proc.kill()
            raise
        finally:
            returncode = proc.wait()
        self.assertEqual(returncode, -signal.SIGTERM)

    def test_a_given_killpg_stands_in_instead(self) -> None:
        def eperm(pgid: int, sig: int) -> None:
            raise PermissionError

        proc = subprocess.Popen(['/bin/sleep', '60'], start_new_session=True)
        try:
            with FakeDarwinProcessGroups(killpg=eperm) as fake:
                with self.assertRaises(PermissionError):
                    os.killpg(proc.pid, 0)
                # The darwin-faithful behavior remains available beneath it.
                fake.darwin_killpg(proc.pid, 0)
        finally:
            proc.kill()
            proc.wait()
