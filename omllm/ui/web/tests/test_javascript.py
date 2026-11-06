import os.path
import shutil
import subprocess

import pytest


def test_javascript():
    if (node := shutil.which('node')) is None:
        pytest.skip('node not found')

    subprocess.run(  # noqa: S603
        [node, os.path.join(os.path.dirname(__file__), 'js', 'testall.mjs')],
        check=True,
        timeout=60,
    )
