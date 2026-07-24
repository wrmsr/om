from omcore.testing.pytest import plugins as ptp
from omcore.testing.pytest.inject.harnesses import harness  # noqa


def pytest_addhooks(pluginmanager):
    ptp.add_hooks(pluginmanager)
