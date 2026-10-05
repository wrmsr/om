"""
Process isolation for tests that execute Triton kernels: `triton_modes` runs a test's body in a child process whose
environment fixes how Triton executes them, once per requested mode.

  interpret  TRITON_INTERPRET=1 and no visible GPU: kernels run on CPU through Triton's numpy interpreter (slow, f32
             only). All a machine without CUDA can do.
  compiled   TRITON_INTERPRET unset: kernels are compiled and run on CUDA. Skipped where there is none.

Why a process each: interpreted and compiled Triton cannot share one. Triton picks between them every time a kernel is
jitted, and three things then stay as they were first made for the life of the process:

  - Triton's own `tl` helpers (tl.sum, tl.sigmoid, ...), jitted when triton is first imported. That import is not
    always ours: torch.compile on CUDA imports triton for inductor's kernels.
  - Our kernels, jitted once per process by torch_triton.ensure_kernels.
  - TRITON_INTERPRET itself once something has set it, which every child process then inherits.

Mixed, they fail either way round. Kernels jitted as interpreted functions over compiled helpers raise "Cannot call
@triton.jit'd outside of the scope of a kernel". Kernels jitted interpreted and then handed CUDA tensors hit what the
interpreter cannot do there: bf16 comes out as garbage, and some arguments cannot be moved to the host
("'ConstTensorWrapper' object has no attribute 'untyped_storage'"). So a test must never execute Triton, nor set
TRITON_INTERPRET, in the pytest process itself. With every such test behind `triton_modes`, the order and grouping of
tests in a pytest run no longer matter, with or without xdist, and a machine with CUDA exercises both modes.

A body picks its device with torch.cuda.is_available(), which is False in an interpret child. Each item costs a process
(a couple of seconds of imports), and a body runs without pytest: no fixtures, no assertion rewriting.

This is a start rather than the last word: one child per (module, mode) reporting back per test would amortize the
startup, and the same isolation would serve any other state that is fixed per process.
"""
import importlib
import os
import subprocess
import sys
import typing as ta

import pytest

from omcore import check
from omcore import lang


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')


TritonMode: ta.TypeAlias = ta.Literal['interpret', 'compiled']


##


# What each mode sets in its child's environment (None: the variable is removed)
MODE_ENVS: ta.Mapping[str, ta.Mapping[str, str | None]] = {
    'interpret': {
        'TRITON_INTERPRET': '1',
        'CUDA_VISIBLE_DEVICES': '',
    },
    'compiled': {
        'TRITON_INTERPRET': None,
    },
}

# A body gets the time a test gets by default (pyproject's pytest timeout); the pytest item wrapped around it gets a
# margin on top, so that a child that hangs is killed and reported with its output rather than cut off from outside.
DEFAULT_TIMEOUT_S = 60.
TIMEOUT_MARGIN_S = 15.

BODY_ATTR = '_triton_modes_body'


def has_cuda() -> bool:
    return lang.can_import('torch') and torch.cuda.is_available()


def child_env(mode: str) -> dict[str, str]:
    env = dict(os.environ)

    for k, v in MODE_ENVS[mode].items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v

    # the child must be able to import whatever this process can, however pytest was launched
    env['PYTHONPATH'] = os.pathsep.join(p for p in sys.path if p)

    # its prints and its traceback share one pipe: unbuffered keeps them in the order they happened
    env['PYTHONUNBUFFERED'] = '1'

    return env


def run_body(
        fn: ta.Callable[[], None],
        mode: str,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
) -> None:
    """
    Runs the body `fn` of a `triton_modes` test in a child process set up for `mode`, failing the calling test with the
    child's output if the child fails or times out.
    """

    try:
        proc = subprocess.run(  # noqa
            [sys.executable, '-m', __name__, fn.__module__, fn.__name__],
            env=child_env(mode),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors='replace',
            timeout=timeout_s,
            check=False,
        )

    except subprocess.TimeoutExpired as e:
        out: ta.Any = e.stdout  # str or bytes at runtime, depending on how far the read got
        if isinstance(out, bytes):
            out = out.decode(errors='replace')
        out = out or ''
        failure: str | None = f'{mode} child timed out after {timeout_s:g}s'

    else:
        out = proc.stdout
        failure = f'{mode} child exited with {proc.returncode}' if proc.returncode else None

    if failure is not None:  # (outside the handler, so the report is not chained to the TimeoutExpired)
        pytest.fail(f'{failure}:\n{out}', pytrace=False)

    sys.stdout.write(out)


def triton_modes(
        *modes: TritonMode,
        timeout_s: float = DEFAULT_TIMEOUT_S,
) -> ta.Callable[[ta.Callable[[], None]], ta.Callable[..., None]]:
    """
    Decorates a module-level test function taking no arguments: it becomes one pytest item per mode
    (`test_x[interpret]`, `test_x[compiled]`), each of which runs the function's body in a child process in that mode.
    See the module docstring.
    """

    check.not_empty(modes)
    for mode in modes:
        check.in_(mode, MODE_ENVS)

    def inner(fn: ta.Callable[[], None]) -> ta.Callable[..., None]:
        def test(triton_mode: str) -> None:
            if triton_mode == 'compiled' and not has_cuda():
                pytest.skip('cuda not available')

            run_body(fn, triton_mode, timeout_s=timeout_s)

        test.__name__ = fn.__name__
        test.__qualname__ = fn.__qualname__
        test.__module__ = fn.__module__
        test.__doc__ = fn.__doc__
        setattr(test, BODY_ATTR, fn)  # (not __wrapped__: pytest would then read the body's signature, not this one's)

        return pytest.mark.parametrize('triton_mode', modes)(
            pytest.mark.timeout(timeout_s + TIMEOUT_MARGIN_S)(test),
        )

    return inner


##


def _main() -> None:
    """The child: `python -m <this module> <test module> <test function>` runs that test's undecorated body."""

    mod_name, fn_name = sys.argv[1:]
    test = getattr(importlib.import_module(mod_name), fn_name)
    getattr(test, BODY_ATTR)()


if __name__ == '__main__':
    _main()
