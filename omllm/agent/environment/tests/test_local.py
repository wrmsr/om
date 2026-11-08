import os
import platform

import pytest

from omcore import lang

from ..local import LocalEnvironmentOps
from ..local import environment_detect_container
from ..ops import EnvironmentInfo
from ..static import StaticEnvironmentOps


def test_local_describes_this_process():
    info = lang.sync_await(LocalEnvironmentOps().inspect_environment())

    assert info.cwd == os.path.realpath(os.getcwd())
    assert info.system == platform.system()
    assert info.release == platform.release()
    assert info.machine == platform.machine()
    assert info.hostname
    assert info.container == environment_detect_container()
    assert not info.remote


def test_local_resolves_the_requested_cwd(tmp_path):
    root = os.path.realpath(tmp_path)
    real = os.path.join(root, 'real')
    os.mkdir(real)
    link = os.path.join(root, 'link')
    os.symlink(real, link)

    ops = LocalEnvironmentOps()

    assert lang.sync_await(ops.inspect_environment(cwd=link)).cwd == real
    assert lang.sync_await(ops.inspect_environment(cwd=os.path.join(link, '.', 'x', '..'))).cwd == real

    # Relative to this process's own directory, as a shell started here would take it.
    assert lang.sync_await(ops.inspect_environment(cwd=os.path.relpath(real, os.getcwd()))).cwd == real

    with pytest.raises(FileNotFoundError):
        lang.sync_await(ops.inspect_environment(cwd=os.path.join(root, 'missing')))

    file = os.path.join(root, 'file')
    with open(file, 'w') as f:  # noqa
        f.write('x')
    with pytest.raises(NotADirectoryError):
        lang.sync_await(ops.inspect_environment(cwd=file))


def test_static_says_what_it_was_given():
    info = EnvironmentInfo(
        cwd='/w',
        system='Linux',
        release='6.8.0',
        machine='x86_64',
        hostname='box',
    )
    ops = StaticEnvironmentOps(info)

    assert lang.sync_await(ops.inspect_environment()) is info
    assert lang.sync_await(ops.inspect_environment(cwd='/elsewhere')).cwd == '/elsewhere'
