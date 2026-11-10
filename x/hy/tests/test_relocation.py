import os
import shutil
import subprocess
import textwrap

import pytest

from .test_bin import REPO_PYTHON


##


@pytest.mark.parametrize('parent_package', ['relocated', 'relocated.nested'])
def test_relocated_package(tmp_path, parent_package):
    package_dir = str(tmp_path)
    for part in parent_package.split('.'):
        package_dir = os.path.join(package_dir, part)
        os.mkdir(package_dir)
        with open(os.path.join(package_dir, '__init__.py'), 'w'):
            pass
    shutil.copytree(
        os.path.dirname(os.path.dirname(__file__)),
        os.path.join(package_dir, 'hy'),
        ignore=shutil.ignore_patterns('__pycache__', 'tests'),
    )

    package = f'{parent_package}.hy'
    env = {**os.environ, 'PYTHONPATH': str(tmp_path)}
    source = textwrap.dedent(f"""\
        import ast
        import importlib
        import sys
        import types

        hy = importlib.import_module({package!r})
        assert hy.__package__ == {package!r}
        assert hy.eval(hy.read('(cond False 0 True (str (+ 2 3)))')) == '5'
        assert hy.repr(hy.read('(hello :world)')) == "'(hello :world)"
        assert str(hy.gensym()).startswith('_hy_gensym_')
        assert hy.macroexpand_1(hy.read('(when True 7)'))[0] == hy.models.Symbol('if')
        assert hy.as_model(2) == hy.models.Integer(2)
        assert hy.pyops.hyx_Xplus_signX(2, 3) == 5
        assert hy.Reader.__module__ == {package!r}
        assert hy.HyReader.__module__ == {package!r}
        assert hy.PrematureEndOfInput.__module__ == {package!r}
        assert hy.REPL().banner().startswith('Hy using ')

        module = types.ModuleType('runtime_binding')
        tree = hy.compiler.hy_compile(hy.read_many("(setv model 'hello)"), module)
        source = ast.unparse(tree)
        assert 'from {parent_package} import hy' in source
        assert 'hy.models.Symbol' in source
        namespace = {{}}
        exec(compile(tree, '<test>', 'exec'), namespace)
        assert namespace['hy'] is hy
        assert namespace['model'] == hy.models.Symbol('hello')

        command = hy.importer.spawn_gcl_for_hy(tracker_fd=0, pipe_handle=1)
        assert command[command.index('-c') + 1].startswith('import {package}; ')
        assert not any(name == 'hy' or name.startswith('hy.') for name in sys.modules)
    """)
    result = subprocess.run(
        [REPO_PYTHON, '-c', source],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr

    result = subprocess.run(
        [REPO_PYTHON, '-m', package, '-c', '(print (cond False 0 True (+ 2 3)))'],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == '5\n'
