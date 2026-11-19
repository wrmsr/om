import ast
import importlib
import importlib.util
import os
import runpy
import sys
import zipfile

import pytest

from ..compiler import hy_compile
from ..errors import HyLanguageError
from ..errors import hy_exc_handler
from ..globalruntime import HyLoader
from ..globalruntime import get_global_runtime
from ..reader import read_many
from .helpers import PACKAGE
from .helpers import PACKAGE_DIR


##


RT = get_global_runtime()
hy = RT.hy


def test_basics():
    "Make sure the basics of the importer work"

    resources_mod = importlib.import_module('.resources', __package__)
    assert resources_mod.in_init == 'chippy'

    bin_mod = importlib.import_module('.resources.bin', __package__)
    assert hasattr(bin_mod, '_null_fn_for_import_test')


def test_runpy():
    # `runpy` won't update cached bytecode. It's not clear if that's
    # intentional.

    # Running Hy files by path requires `runpy` to compile them as Hy, which it doesn't do (that requires patching it).
    # The `hy` command runs Hy files itself.
    with pytest.raises(SyntaxError):
        runpy.run_path(f'{PACKAGE_DIR}/tests/resources/importer/basic.hy')

    main_ns = runpy.run_path(f'{PACKAGE_DIR}/tests/resources/bin')
    assert main_ns['visited_main'] == 1
    del main_ns

    main_ns = runpy.run_module(f'{PACKAGE}.tests.resources.bin')
    assert main_ns['visited_main'] == 1

    with pytest.raises(FileNotFoundError):
        runpy.run_path(f'{PACKAGE_DIR}/tests/resources/foobarbaz.py')


def test_stringer():
    _ast = hy_compile(
        read_many('(defn square [x] (* x x))'), __name__, runtime=RT,
    )

    assert type(_ast.body[0]) is ast.FunctionDef


def test_imports():
    test_loader = HyLoader(
        f'{PACKAGE}.tests.resources.importer.a',
        f'{PACKAGE_DIR}/tests/resources/importer/a.hy',
    )
    spec = importlib.util.spec_from_loader(test_loader.name, test_loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)

    with pytest.raises(NameError) as excinfo:
        test_loader.exec_module(mod)

    assert 'thisshouldnotwork' in excinfo.value.args[0]


def test_import_error_reporting():
    "Make sure that (import) reports errors correctly."

    with pytest.raises(HyLanguageError):
        hy_compile(read_many('(import "sys")'), __name__, runtime=RT)


def test_import_error_cleanup():
    "Failed initial imports should not leave dead modules in `sys.modules`."

    with pytest.raises(hy.errors.HyMacroExpansionError):
        importlib.import_module(f'{PACKAGE}.tests.resources.fails')

    assert f'{PACKAGE}.tests.resources.fails' not in sys.modules


@pytest.mark.skipif(sys.dont_write_bytecode, reason='Bytecode generation is suppressed')
def test_import_autocompiles(tmp_path):
    "Test that (import) byte-compiles the module."

    p = tmp_path / 'mymodule.hy'
    p.write_text('(defn pyctest [s] (+ "X" s "Y"))')

    def import_from_path(path):
        # `.hy` isn't a globally registered source suffix, so the loader for source files must be given explicitly.
        spec = importlib.util.spec_from_file_location(
            'mymodule',
            path,
            loader=HyLoader('mymodule', str(path)) if str(path).endswith('.hy') else None,
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    assert import_from_path(p).pyctest('flim') == 'XflimY'
    assert os.path.exists(importlib.util.cache_from_source(p))

    # Try running the bytecode.
    assert (
        import_from_path(importlib.util.cache_from_source(p)).pyctest('flam')
        == 'XflamY'
    )


def test_eval():
    def eval_str(s):
        return hy.eval(hy.read(s))

    assert eval_str('[1 2 3]') == [1, 2, 3]
    assert eval_str('{"dog" "bark" "cat" "meow"}') == {'dog': 'bark', 'cat': 'meow'}
    assert eval_str('#(1 2 3)') == (1, 2, 3)
    assert eval_str('#{3 1 2}') == {1, 2, 3}
    assert eval_str('(.strip " fooooo   ")') == 'fooooo'
    assert (
        eval_str('(if True "this is if true" "this is if false")') == 'this is if true'
    )
    assert eval_str('(lfor num (range 100) :if (= (% num 2) 1) (pow num 2))') == [
        pow(num, 2) for num in range(100) if num % 2 == 1
    ]


def test_reload(tmp_path, monkeypatch):
    """
    Generate a test module, confirm that it imports properly (and puts the
    module in `sys.modules`), then modify the module so that it produces an
    error when reloaded.  Next, fix the error, reload, and check that the
    module is updated and working fine.  Rinse, repeat.

    This test is adapted from CPython's `test_import.py`.
    """

    def unlink(filename):
        os.unlink(source)
        bytecode = importlib.util.cache_from_source(source)
        if os.path.isfile(bytecode):
            os.unlink(bytecode)

    test_module_name = 'testfn'
    source = tmp_path / (test_module_name + '.hy')
    source.write_text('(setv a 1)  (setv b 2)')

    monkeypatch.syspath_prepend(tmp_path)
    try:
        mod = importlib.import_module(test_module_name)
        assert test_module_name in sys.modules
        assert mod.a == 1
        assert mod.b == 2

        # On WinXP, just replacing the .py file wasn't enough to
        # convince importlib.reload() to reparse it.  Maybe the timestamp didn't
        # move enough.  We force it to get reparsed by removing the
        # compiled file too.
        unlink(source)

        # Now damage the module.
        source.write_text('(setv a 10)  (setv b (// 20 0))')

        with pytest.raises(ZeroDivisionError):
            importlib.reload(mod)

        # But we still expect the module to be in sys.modules.
        assert test_module_name in sys.modules
        mod = sys.modules[test_module_name]
        assert mod is not None

        # We should have replaced a w/ 10, but the old b value should
        # stick.
        assert mod.a == 10
        assert mod.b == 2

        # Now fix the issue and reload the module.
        unlink(source)

        source.write_text('(setv a 11)  (setv b (// 20 1))')

        importlib.reload(mod)

        assert test_module_name in sys.modules
        mod = sys.modules[test_module_name]
        assert mod is not None

        assert mod.a == 11
        assert mod.b == 20

        # Now cause a syntax error (a missing parenthesis)
        unlink(source)

        source.write_text('(setv a 11  (setv b (// 20 1))')

        with pytest.raises(hy.PrematureEndOfInput):
            importlib.reload(mod)

        assert test_module_name in sys.modules
        mod = sys.modules[test_module_name]
        assert mod is not None

        assert mod.a == 11
        assert mod.b == 20

        # Fix it and retry
        unlink(source)

        source.write_text('(setv a 12)  (setv b (// 10 1))')

        importlib.reload(mod)

        assert test_module_name in sys.modules
        mod = sys.modules[test_module_name]
        assert mod is not None

        assert mod.a == 12
        assert mod.b == 10

    finally:
        if test_module_name in sys.modules:
            del sys.modules[test_module_name]


def test_reload_reexecute(capsys):
    """
    A module is re-executed when it's reloaded, even if it's
    unchanged.

    https://github.com/hylang/hy/issues/712
    """

    hello_world = importlib.import_module('.resources.hello_world', __package__)

    assert capsys.readouterr().out == 'hello world\n'
    assert capsys.readouterr().out == ''
    importlib.reload(hello_world)
    assert capsys.readouterr().out == 'hello world\n'


def test_circular(monkeypatch):
    """
    Test circular imports by creating a temporary file/module that calls a
    function that imports itself.
    """

    monkeypatch.syspath_prepend(f'{PACKAGE_DIR}/tests/resources/importer')
    assert runpy.run_module('circular')['f']() == 1


def test_shadowed_basename(monkeypatch):
    """
    Make sure Hy loads `.hy` files instead of their `.py` counterparts (.e.g
    `__init__.py` and `__init__.hy`).
    """

    monkeypatch.syspath_prepend(f'{PACKAGE_DIR}/tests/resources/importer')
    # Other tests may have imported different modules of these generic names.
    for name in ['foo', 'foo.some_mod']:
        monkeypatch.delitem(sys.modules, name, raising=False)

    foo = importlib.import_module('foo')
    assert foo.__file__ is not None
    assert os.path.basename(foo.__file__) == '__init__.hy'
    assert foo.ext == 'hy'
    some_mod = importlib.import_module('foo.some_mod')
    assert some_mod.__file__ is not None
    assert os.path.basename(some_mod.__file__) == 'some_mod.hy'
    assert some_mod.ext == 'hy'


def test_docstring(monkeypatch):
    """Make sure a module's docstring is loaded."""

    monkeypatch.syspath_prepend(f'{PACKAGE_DIR}/tests/resources/importer')
    monkeypatch.delitem(sys.modules, 'docstring', raising=False)
    mod = importlib.import_module('docstring')
    expected_doc = 'This module has a docstring.\n\nIt covers multiple lines, too!\n'
    assert mod.__doc__ == expected_doc
    assert mod.a == 1


def test_hy_python_require():
    # https://github.com/hylang/hy/issues/1911
    test = f'(do (require {PACKAGE}.tests.resources.macros [test-macro]) (test-macro) blah)'
    assert hy.eval(hy.read(test)) == 1


def test_filtered_importlib_frames(capsys):
    test_loader = HyLoader(
        f'{PACKAGE}.tests.resources.importer.compiler_error',
        f'{PACKAGE_DIR}/tests/resources/importer/compiler_error.hy',
    )
    spec = importlib.util.spec_from_loader(test_loader.name, test_loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)

    with pytest.raises(hy.PrematureEndOfInput) as execinfo:
        test_loader.exec_module(mod)

    hy_exc_handler(execinfo.type, execinfo.value, execinfo.tb)
    captured_w_filtering = capsys.readouterr()[-1].strip()

    assert 'importlib._' not in captured_w_filtering


def test_zipimport(tmp_path, monkeypatch):
    zpath = tmp_path / 'archive.zip'
    with zipfile.ZipFile(zpath, 'w') as o:
        # Test a Python module as well as a Hy module to ensure that
        # Hy's edits to ZIP imports can still get Python files.
        o.writestr('zip_py.py', 'x = "Py from ZIP"')
        o.writestr('zip_hy.hy', '(setv x "Hy from ZIP")')

    monkeypatch.syspath_prepend(zpath)
    zip_hy = importlib.import_module('zip_hy')
    zip_py = importlib.import_module('zip_py')
    assert zip_py.x == 'Py from ZIP'
    assert zip_py.__file__ == str(zpath / 'zip_py.py')
    assert zip_hy.x == 'Hy from ZIP'
    assert zip_hy.__file__ == str(zpath / 'zip_hy.hy')


def test_eval_requiring_macro():
    # https://github.com/hylang/hy/issues/2695
    hy.eval(hy.read(f'(require {PACKAGE}.tests.resources.macros)'), globals={})
