from .testing.pytest import plugins as ptp
from .testing.pytest.inject.harnesses import harness  # noqa


def pytest_addhooks(pluginmanager):
    ptp.add_hooks(pluginmanager)
