import sys

import pytest

from .conftest import run_script


def test_no_import_side_effect():
    """Check that importing the module doesn't cause side effects."""

    rv = run_script(
        """
import os

def print_stuff():
    for fn in "cmdline status comm".split():
        if os.path.exists(f"/proc/self/{fn}"):
            with open(f"/proc/self/{fn}") as f:
                print(f.readline().rstrip())

print_stuff()
print("---")
import setproctitle
print_stuff()
""",
    )
    before, after = rv.split('---\n')
    assert before == after


@pytest.mark.skipif(sys.platform != 'darwin', reason='Mac only test')
def test_darwin_argv_preserved():
    rv = run_script(
        """
import ctypes as ct

libc = ct.CDLL('/usr/lib/libSystem.B.dylib')
ns_get_argc = libc._NSGetArgc
ns_get_argc.restype = ct.POINTER(ct.c_int)
ns_get_argc.argtypes = []
ns_get_argv = libc._NSGetArgv
ns_get_argv.restype = ct.POINTER(ct.POINTER(ct.c_void_p))
ns_get_argv.argtypes = []

argc = ns_get_argc().contents.value
argv = ns_get_argv().contents
before = [ct.string_at(argv[i]) for i in range(argc)]

import setproctitle

argv = ns_get_argv().contents
after = [ct.string_at(argv[i]) for i in range(argc)]
print(before == after)
""",
    )
    assert rv == 'True\n'
