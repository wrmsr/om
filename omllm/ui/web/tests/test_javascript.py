import os.path
import shutil
import subprocess

import pytest


def test_javascript():
    if (node := shutil.which('node')) is None:
        pytest.skip('node not found')

    version_str = subprocess.check_output(
        [node, '-p', 'process.versions.node'],
        timeout=60,
    ).decode().strip()
    version = tuple(map(int, version_str.split('.')[:3]))
    if version < (20,):
        pytest.skip(f'node too old: {version_str!r}')

    subprocess.run(  # noqa: S603
        [node, os.path.join(os.path.dirname(__file__), 'js', 'testall.mjs')],
        check=True,
        timeout=60,
    )
