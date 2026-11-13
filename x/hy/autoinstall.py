"""
Importing this module installs the global Hy runtime - see :mod:`.globalruntime`.

This deliberately side-effecting module exists to be named where only a module import can be requested: it's what the
preamble of Hy code compiled for the global runtime (such as bytecode-cached modules, or the output of ``hy2py``)
imports ``hy`` from, and it's in a :mod:`multiprocessing` forkserver's preload list once the global runtime is
installed. It should otherwise never be imported - call :func:`.globalruntime.install` instead.
"""
import typing as ta

from .globalruntime import install


if ta.TYPE_CHECKING:
    from .runtime import HyNamespace


##


hy: HyNamespace = install().hy
