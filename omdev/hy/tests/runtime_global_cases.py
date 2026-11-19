import inspect
import sys

from .. import globalruntime


##


def test_global_runtime():
    assert globalruntime.is_installed()

    grt = globalruntime.get_global_runtime()
    assert globalruntime.install() is grt
    assert grt.modules.get_module('sys') is sys

    pkg = __package__
    tlib = grt.import_module(f'{pkg}.resources.tlib')
    assert sys.modules[f'{pkg}.resources.tlib'] is tlib
    assert tlib.hy is grt.hy


def test_global_runtime_uninstall_reinstall():
    hooks = list(sys.path_hooks)
    getsource = inspect.getsource

    globalruntime.uninstall()
    try:
        assert not globalruntime.is_installed()
        assert len(sys.path_hooks) == len(hooks) - 2
        assert inspect.getsource is not getsource
    finally:
        globalruntime.install()

    assert globalruntime.is_installed()
    assert len(sys.path_hooks) == len(hooks)
    assert inspect.getsource.__module__ == getsource.__module__
