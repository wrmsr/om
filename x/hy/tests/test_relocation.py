import os
import shutil
import subprocess
import textwrap

import pytest

from .test_bin import REPO_PYTHON


##


@pytest.mark.parametrize('package', [
    'relocated.hy',
    'relocated.nested.hy',
    'relocated.lisp',
    'relocated.nested.hylang',
])
def test_relocated_package(tmp_path, package):
    """The package works wherever it lives, and under whatever name - it never refers to its own absolute name."""

    parent_package, _, name = package.rpartition('.')

    package_dir = str(tmp_path)
    for part in parent_package.split('.'):
        package_dir = os.path.join(package_dir, part)
        os.mkdir(package_dir)
        with open(os.path.join(package_dir, '__init__.py'), 'w'):
            pass
    shutil.copytree(
        os.path.dirname(os.path.dirname(__file__)),
        os.path.join(package_dir, name),
        ignore=shutil.ignore_patterns('__pycache__', 'tests'),
    )

    with open(os.path.join(str(tmp_path), 'hymod.hy'), 'w') as f:
        f.write('(defn #^int double [#^int x] (* x 2))')

    env = {**os.environ, 'PYTHONPATH': str(tmp_path)}
    source = textwrap.dedent(f"""\
        import ast
        import builtins
        import importlib
        import sys

        def hy_named():
            return [n for n in sys.modules if n == 'hy' or n.startswith('hy.')]

        hooks_before = list(sys.path_hooks)
        builtins_before = dict(builtins.__dict__)

        pkg = importlib.import_module({package!r})
        assert pkg.__package__ == {package!r}
        assert pkg.Reader.__module__ == {package!r}
        assert pkg.HyReader.__module__ == {package!r}
        assert pkg.PrematureEndOfInput.__module__ == {package!r}

        # An isolated runtime.

        rt = pkg.HyRuntime()
        hy = rt.hy
        assert hy.__package__ == {package!r}
        assert rt.eval('(cond False 0 True (str (+ 2 3)))') == '5'
        assert hy.repr(hy.read('(hello :world)')) == "'(hello :world)"
        assert str(hy.gensym()).startswith('_hy_gensym_')
        assert hy.macroexpand_1(hy.read('(when True 7)'), rt.new_module())[0] == hy.models.Symbol('if')
        assert hy.as_model(2) == hy.models.Integer(2)
        assert hy.pyops.hyx_Xplus_signX(2, 3) == 5
        assert rt.eval('(ta.get-origin (get ta.Sequence int))').__name__ == 'Sequence'
        assert hy.REPL().banner().startswith('Hy using ')

        tree = rt.compile("(setv model 'hello)")
        source = ast.unparse(tree)
        assert 'import' not in source
        assert 'hy.models.Symbol' in source

        assert sys.path_hooks == hooks_before
        assert dict(builtins.__dict__) == builtins_before
        core_hy_modules = [{package!r} + '.' + n for n in ['core.macros', 'core.util', 'core.hy_repr', 'pyops']]
        assert not [n for n in core_hy_modules if n in sys.modules]
        assert not hy_named()

        # The global runtime.

        globalruntime = importlib.import_module({package!r} + '.globalruntime')
        grt = globalruntime.install()
        tree = grt.compile("(setv model 'hello)", preamble=True)
        assert 'from {package}.autoinstall import hy' in ast.unparse(tree)

        import hymod
        assert hymod.double(2) == 4
        assert hymod.hy is grt.hy

        globalruntime.uninstall()
        assert sys.path_hooks == hooks_before
        assert not hy_named()
    """)
    result = subprocess.run(
        [REPO_PYTHON, '-c', source],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr

    result = subprocess.run(
        [REPO_PYTHON, '-m', package, '-c', '(print (cond False 0 True (+ 2 3)))'],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == '5\n'
