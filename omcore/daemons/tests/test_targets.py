import functools
import os
import sys
import tempfile

from ..launching import Launcher
from ..spawning import ForkSpawning
from ..spawning import ThreadSpawning
from ..targets import ExecTarget
from ..targets import FnTarget
from ..targets import NameTarget
from ..targets import Target
from ..targets import target_runner_for
from .helpers import run_controlled_worker
from .testing import accept_worker
from .testing import launch_forking
from .testing import make_unix_listener
from .testing import release_worker
from .testing import wait_fork_child


def test_target_of():
    fn = lambda: None

    assert Target.of('pkg.mod') == NameTarget('pkg.mod')
    assert Target.of(fn) == FnTarget(fn)


def test_fn_target_runner_chains_returned_target():
    calls = []

    def inner():
        calls.append('inner')

    def outer():
        calls.append('outer')
        return inner

    target_runner_for(FnTarget(outer)).run()

    assert calls == ['outer', 'inner']


def test_fn_target_runs_in_background_thread():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')

        with make_unix_listener(control_path) as listener:
            assert Launcher(
                target=FnTarget(functools.partial(
                    run_controlled_worker,
                    control_path,
                    label='fn-target',
                )),
                spawning=ThreadSpawning(linger=True),
            ).launch()

            conn, info = accept_worker(listener)
            assert info['label'] == 'fn-target'
            assert info['pid'] == os.getpid()
            release_worker(conn)


def test_exec_target_replaces_forked_process_and_honors_cwd():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')

        with make_unix_listener(control_path) as listener:
            assert launch_forking(Launcher(
                target=ExecTarget(
                    [
                        sys.executable,
                        sys.executable,
                        '-m',
                        'omcore.daemons.tests.helpers',
                        'worker',
                        control_path,
                        '--label',
                        'exec-target',
                    ],
                    cwd=temp_dir,
                ),
                spawning=ForkSpawning(),
            ))

            conn, info = accept_worker(listener)
            worker_pid = info['pid']
            assert info['label'] == 'exec-target'
            assert info['cwd'] == temp_dir
            release_worker(conn)

            assert wait_fork_child(worker_pid) == 0
