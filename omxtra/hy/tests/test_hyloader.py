import ast
import importlib.util
import os
import sys

import pytest

from ..compiler import hy_compile
from ..errors import HyLanguageError
from ..errors import hy_exc_handler
from ..globalruntime import HyLoader
from ..reader import read_many
from .helpers import PACKAGE
from .helpers import PACKAGE_DIR
from .helpers import new_test_runtime


##


def test_stringer():
    tree = hy_compile(read_many('(defn square [x] (* x x))'), __name__, runtime=new_test_runtime())
    assert type(tree.body[0]) is ast.FunctionDef


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
    with pytest.raises(HyLanguageError):
        hy_compile(read_many('(import "sys")'), __name__, runtime=new_test_runtime())


@pytest.mark.skipif(sys.dont_write_bytecode, reason='Bytecode generation is suppressed')
def test_import_autocompiles(tmp_path):
    path = tmp_path / 'mymodule.hy'
    path.write_text('(defn pyctest [s] (+ "X" s "Y"))')

    def import_from_path(source_path):
        spec = importlib.util.spec_from_file_location(
            'mymodule',
            source_path,
            loader=HyLoader('mymodule', str(source_path)) if str(source_path).endswith('.hy') else None,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    assert import_from_path(path).pyctest('flim') == 'XflimY'
    cache_path = importlib.util.cache_from_source(path)
    assert os.path.exists(cache_path)
    assert import_from_path(cache_path).pyctest('flam') == 'XflamY'


def test_eval():
    runtime = new_test_runtime()
    hy = runtime.hy
    module = runtime.new_module('test_eval')

    def eval_str(source):
        return hy.eval(hy.read(source), module=module)

    assert eval_str('[1 2 3]') == [1, 2, 3]
    assert eval_str('{"dog" "bark" "cat" "meow"}') == {'dog': 'bark', 'cat': 'meow'}
    assert eval_str('#(1 2 3)') == (1, 2, 3)
    assert eval_str('#{3 1 2}') == {1, 2, 3}
    assert eval_str('(.strip " fooooo   ")') == 'fooooo'
    assert eval_str('(if True "this is if true" "this is if false")') == 'this is if true'
    assert eval_str('(lfor num (range 100) :if (= (% num 2) 1) (pow num 2))') == [
        pow(num, 2) for num in range(100) if num % 2 == 1
    ]


def test_filtered_importlib_frames(capsys):
    test_loader = HyLoader(
        f'{PACKAGE}.tests.resources.importer.compiler_error',
        f'{PACKAGE_DIR}/tests/resources/importer/compiler_error.hy',
    )
    spec = importlib.util.spec_from_loader(test_loader.name, test_loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)

    with pytest.raises(new_test_runtime().hy.PrematureEndOfInput) as execinfo:
        test_loader.exec_module(mod)

    hy_exc_handler(execinfo.type, execinfo.value, execinfo.tb)
    captured_w_filtering = capsys.readouterr()[-1].strip()

    assert 'importlib._' not in captured_w_filtering
