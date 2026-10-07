import unittest

from ..uv import Uv
from ..uv import UvConfig


def _pytest_mark_timeout(timeout):
    def inner(fn):
        try:
            import pytest
        except ImportError:
            return fn
        else:
            return pytest.mark.timeout(timeout)(fn)

    return inner


class TestUv(unittest.IsolatedAsyncioTestCase):
    @_pytest_mark_timeout(120)
    async def test_uv(self):
        uv = Uv(UvConfig(
            ignore_path=True,
            pip_bootstrap=True,
        ))
        print(await uv.uv_exe())
