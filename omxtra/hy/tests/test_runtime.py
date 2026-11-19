# ruff: noqa: SLF001
import ast
import builtins
import functools
import inspect
import os
import subprocess
import sys
import textwrap
import threading
import types
import typing as ta

import pytest

from omcore import check

from .. import globalruntime
from ..errors import HyRequireError
from ..finders import DirectoryHyModuleFinder
from ..finders import MappingHyModuleFinder
from ..finders import PackageHyModuleFinder
from ..importing import HyModuleOverlay
from ..importing import IsolatedHyModules
from ..models import Expression
from ..models import Symbol
from ..runtime import HyCoreCodeCache
from ..runtime import HyPreludeImport
from ..runtime import HyRuntime
from .helpers import REPO_PYTHON
from .helpers import REPO_ROOT


##


def mapping_runtime(sources, **kwargs):
    return HyRuntime(
        modules=functools.partial(IsolatedHyModules, finders=[MappingHyModuleFinder(sources)]),
        **kwargs,
    )


def test_eval_exec_compile():
    rt = HyRuntime()

    assert rt.eval('(+ 1 2)') == 3
    assert rt.eval('(setv x 1) (+ x 1)') == 2
    assert rt.eval(rt.hy.read('(* 2 3)')) == 6

    mod = rt.exec("""
        (defmacro twice [x] `(do ~x ~x))
        (setv n 0)
        (defn bump [] (global n) (twice (+= n 1)) n)
    """)
    assert mod.bump() == 2
    assert rt.eval('(twice (bump))', mod) == 6
    assert 'twice' in mod._hy_macros

    assert rt.eval('(+ a b)', globals={'a': 1}, locals={'b': 2}) == 3

    src = rt.compile("(setv x 'foo)")
    assert not any(isinstance(s, (ast.Import, ast.ImportFrom)) for s in src.body)


def test_runtime_hy_namespace():
    rt = HyRuntime()
    hy = rt.hy

    assert isinstance(hy, types.ModuleType)
    assert hy.__package__ == __package__.rpartition('.')[0]
    assert hy.runtime is rt
    assert hy.__name__ not in sys.modules or sys.modules[hy.__name__] is not hy

    assert rt.eval('(is hy hy.runtime.hy)')
    assert rt.eval('hy') is hy
    assert rt.eval('(hy.repr [1 "a" :b])') == '[1 "a" :b]'
    assert rt.eval('(hy.pyops.+ 1 2)') == 3
    assert rt.eval('(hy.I.math.sqrt 4)') == 2
    assert rt.eval('(.startswith (str (hy.gensym)) "_hy_gensym_")')
    assert rt.eval("(hy.macroexpand '(when 1 2))")[0] == Symbol('if')
    assert rt.eval("(hy.eval '(+ 1 1))") == 2
    assert rt.eval('(in "when" hy._hy_macros)')
    assert rt.eval('(is (get-macro when) (get hy._hy_macros "when"))')


def test_prelude():
    rt = HyRuntime()
    assert rt.eval('ta') is ta
    assert rt.eval('(get ta.Sequence int)') == ta.Sequence[int]

    # User definitions win over the prelude.
    assert rt.eval('(setv ta 5) ta') == 5

    rt = HyRuntime(prelude=[HyPreludeImport('ta', 'typing'), HyPreludeImport('os_', 'os')])
    assert rt.eval('os_') is os
    stmts = rt.preamble_statements()
    assert [ast.unparse(s) for s in stmts] == ['import typing as ta', 'import os as os_']

    rt = HyRuntime(prelude=[])
    with pytest.raises(NameError):
        rt.eval('ta')


def _global_state():
    return (
        dict(builtins.__dict__),
        list(sys.path_hooks),
        list(sys.meta_path),
        inspect.getsource,
        set(sys.modules),
    )


def test_runtime_touches_no_global_state():
    # Run in a fresh interpreter, so the state isn't affected by the global runtime installed for the other tests.
    pkg = __package__.rpartition('.')[0]
    source = textwrap.dedent(f"""
        import ast, builtins, codeop, inspect, sys
        before = (dict(builtins.__dict__), list(sys.path_hooks), list(sys.meta_path), inspect.getsource, dict(vars(codeop)), ast.unparse)
        import {pkg} as hy
        rt = hy.HyRuntime()
        m = rt.exec('(import json) (defn f [#^ta.Sequence[int] xs] (hy.repr (sum xs)))')
        assert m.f([1, 2]) == '3'
        assert rt.eval('(hy.pyops.+ 1 2)') == 3
        rt.hy.REPL()
        after = (dict(builtins.__dict__), list(sys.path_hooks), list(sys.meta_path), inspect.getsource, dict(vars(codeop)), ast.unparse)
        assert before == after
        assert not [n for n in sys.modules if n == 'hy' or n.startswith('hy.')]
        assert not [n for n in sys.modules if n.startswith('{pkg}.') and n.endswith(('.pyops', '.core.util', '.core.reprs', '.core.macros'))]
        assert not hasattr(builtins, '_hy_macros')
    """)  # noqa
    result = subprocess.run(
        [REPO_PYTHON, '-c', source],
        env={**os.environ, 'PYTHONPATH': REPO_ROOT},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_runtimes_are_independent():
    rt1 = HyRuntime()
    rt2 = HyRuntime()

    assert rt1.hy is not rt2.hy
    assert rt1.hy.pyops is not rt2.hy.pyops

    # Core macros.
    rt1.eval('(eval-when-compile (setv (get hy._hy_macros "when") (fn [#* a] "rt1 when")))')
    assert rt1.eval('(when 1 2)') == 'rt1 when'
    assert rt2.eval('(when 1 2)') == 2
    assert HyRuntime().eval('(when 1 2)') == 2

    # `hy.repr` registrations.
    class C:
        pass

    rt1.hy.repr_register(C, lambda _: 'see')
    assert rt1.hy.repr(C()) == 'see'
    assert rt2.hy.repr(C()) != 'see'

    # Module registries.
    mod = rt1.new_module('shared_name')
    rt1.modules.add_module(mod)
    assert rt1.import_module('shared_name') is mod
    with pytest.raises(ModuleNotFoundError):
        rt2.import_module('shared_name')


def test_core_code_cache():
    cache = HyCoreCodeCache()
    rt = HyRuntime(core_code_cache=cache)
    assert rt.eval('(when 1 2)') == 2
    code = cache.get(f'{rt.hy.__package__}.core.macros')
    assert code is not None

    rt2 = HyRuntime(core_code_cache=cache)
    assert rt2.eval('(when 1 2)') == 2
    assert cache.get(f'{rt.hy.__package__}.core.macros') is code
    assert rt2.get_core_module(f'{rt.hy.__package__}.core.macros') is not rt.get_core_module(
        f'{rt.hy.__package__}.core.macros',
    )


def test_threads():
    rt = HyRuntime(core_code_cache=HyCoreCodeCache())
    results: list[ta.Any] = []

    def run(i):
        results.append(rt.eval(f'(hy.repr (cond False 0 True {i}))'))

    threads = [threading.Thread(target=run, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [str(i) for i in range(8)]


def test_mapping_finder_imports():
    rt = mapping_runtime({
        'pkg.a': '(defmacro m [] \'(setv x (.upper "hello"))) (defn f [] "a.f")',
        'pkg.b': '(require .a [m]) (import .a [f]) (m)',
        'pkg.sub.c': '(import .. [b]) (setv y b.x)',
        'top': '(import pkg.sub.c) (setv z pkg.sub.c.y)',
    })

    b = rt.import_module('pkg.b')
    assert b.x == 'HELLO'
    assert b.f() == 'a.f'
    assert b.__package__ == 'pkg'

    pkg = rt.import_module('pkg')
    assert pkg.__path__ == []
    assert pkg.b is b

    assert rt.import_module('top').z == 'HELLO'

    assert rt.eval('(import pkg.a :as a) (a.f)') == 'a.f'
    assert rt.eval('(import pkg [a]) (a.f)') == 'a.f'

    with pytest.raises(ModuleNotFoundError):
        rt.import_module('pkg.nope')

    assert 'pkg.b' not in sys.modules


def test_isolated_require_errors():
    rt = mapping_runtime({'mods.m': '(defmacro m [] 1)'})
    assert rt.eval('(require mods.m [m]) (m)') == 1
    with pytest.raises(HyRequireError):
        rt.eval('(require mods.nope [m])')


def test_failed_import_is_unregistered():
    rt = mapping_runtime({'bad': '(setv x 1) (/ 1 0)'})
    with pytest.raises(ZeroDivisionError):
        rt.import_module('bad')
    assert rt.modules.get_module('bad') is None


def test_directory_finder(tmp_path):
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'scripts' / 'util.hy').write_text('(defn greet [#^str name] (+ "hi " name))')
    (tmp_path / 'scripts' / 'pkg').mkdir()
    (tmp_path / 'scripts' / 'pkg' / '__init__.hy').write_text('(setv init-ran True)')
    (tmp_path / 'scripts' / 'pkg' / 'mod.hy').write_text('(import util [greet]) (setv msg (greet "pkg"))')

    rt = HyRuntime(modules=functools.partial(
        IsolatedHyModules,
        finders=[DirectoryHyModuleFinder(str(tmp_path / 'scripts'))],
    ))

    util = rt.import_module('util')
    assert util.greet('you') == 'hi you'
    assert util.__file__ == str(tmp_path / 'scripts' / 'util.hy')

    mod = rt.import_module('pkg.mod')
    assert mod.msg == 'hi pkg'
    assert rt.import_module('pkg').init_ran

    assert 'util' not in sys.modules


def test_package_finder():
    # The test resources are Hy modules living inside a regular Python package.
    pkg = __package__
    rt = HyRuntime(modules=functools.partial(
        IsolatedHyModules,
        finders=[PackageHyModuleFinder(prefixes=[pkg])],
    ))

    tlib = rt.import_module(f'{pkg}.resources.tlib')
    assert 'qplah' in tlib._hy_macros
    assert rt.eval(f'(require {pkg}.resources.tlib [qplah]) (qplah 1 2)') == [8, 1, 2]

    # A Hy module inside a Python package is visible through an overlay of the Python package, rather than by adding
    # attributes to it.
    resources = rt.eval(f'(import {pkg}.resources.tlib) {pkg}.resources')
    assert isinstance(resources, HyModuleOverlay)
    assert resources.tlib is tlib
    assert not hasattr(sys.modules[f'{pkg}.resources'], 'tlib') or sys.modules[f'{pkg}.resources'].tlib is not tlib

    # A Hy package (with an `__init__.hy`) inside a Python package.
    rt_bin = rt.import_module(f'{pkg}.resources.bin')
    assert callable(rt_bin._null_fn_for_import_test)
    assert rt_bin.__path__ == [os.path.dirname(check.not_none(rt_bin.__file__))]
    assert rt_bin is not sys.modules.get(f'{pkg}.resources.bin')

    # The core Hy modules are always found, as the runtime's own instances.
    assert rt.import_module(f'{pkg.rpartition(".")[0]}.pyops') is rt.hy.pyops


def test_hy_eval_finds_calling_module():
    rt = HyRuntime()
    mod = rt.exec("""
        (defmacro m [] 5)
        (defn f [] (hy.eval '(m)))
    """)
    assert mod.f() == 5

    # Code running in namespaces unknown to the runtime must say where to look for macros.
    ns: dict[str, ta.Any] = {}
    exec('def g(hy): return hy.eval(hy.read("(+ 1 1)"))', ns)  # noqa: S102
    with pytest.raises(TypeError):
        ns['g'](rt.hy)
    assert rt.hy.eval(rt.hy.read('(+ 1 1)'), module=rt.new_module()) == 2


def test_global_runtime():
    # The conftest installs the global runtime.
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


def test_global_and_isolated_coexist():
    grt = globalruntime.get_global_runtime()
    rt = HyRuntime()
    assert rt.hy is not grt.hy
    assert rt.eval('(hy.pyops.+ 1 2)') == grt.eval('(hy.pyops.+ 1 2)') == 3
    assert rt.hy.pyops is not grt.hy.pyops


def test_expression_model_roundtrip():
    rt = HyRuntime()
    e = rt.eval("'(foo bar)")
    assert e == Expression([Symbol('foo'), Symbol('bar')])
    assert rt.eval(e, globals={'foo': lambda x: x * 2, 'bar': 21}) == 42
