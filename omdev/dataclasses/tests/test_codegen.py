import ast
import os.path

import pytest

from omcore import lang
from omcore.dataclasses.impl.api import field
from omcore.dataclasses.impl.generation.globals import FnGlobal
from omcore.dataclasses.impl.generation.keys import implementation_key
from omcore.dataclasses.impl.generation.tests.harness import AotHarness
from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ..codegen import DataclassCodeGen
from ..dumping import DataclassCodegenDumperOutput
from ..dumping import DumpedDataclassCodegen


##


def _write_artifact(tmp_path, aot, names, *, width=120):
    init_path = os.path.join(tmp_path, '__init__.py')
    with open(init_path, 'w') as f:
        f.write('from omcore import dataclasses as dc\ndc.init_package(globals(), codegen=True)\n')

    gen = DataclassCodeGen(target_line_width=width)
    cfg = gen.scan_py_file(init_path)
    assert cfg is not None

    dumped = []
    for name, (prepared, comp) in zip(names, aot.captured, strict=True):
        dumped.append(DumpedDataclassCodegen(
            mod_name=aot.module.__name__,
            cls_module=aot.module.__name__,
            cls_qualname=name,
            spec_key=prepared.spec_key,
            fn_name=comp.fn_name,
            fn_params=comp.fn_params,
            hdr_lines=comp.hdr_lines,
            fn_lines=comp.fn_lines,
            refs=[
                DumpedDataclassCodegen.Ref(
                    kind='global' if isinstance(r, FnGlobal) else 'op',
                    ident=r.ident if isinstance(r, FnGlobal) else r.ident(),
                )
                for r in comp.refs
            ],
        ))

    output = DataclassCodegenDumperOutput(
        init_file_path=init_path,
        out_file_path=os.path.join(tmp_path, 'output.json'),
        processed_modules=[aot.module.__name__],
        import_errors={},
        dumped=dumped,
        implementation_key=implementation_key(),
    )
    output = unmarshal_obj(marshal_obj(output), DataclassCodegenDumperOutput)
    lang.sync_await(gen.process_dumper_output(cfg, output))

    with open(os.path.join(tmp_path, '_dataclasses.py')) as f:
        source = f.read()
    exec(compile(source, '<written-dataclass-aot>', 'exec'), vars(aot.generated))
    return source


def test_codegen_preserves_distinct_binding_recipes(tmp_path):
    def make(name):
        class C:
            x: int = 1

        C.__qualname__ = name
        return C

    with AotHarness() as aot:
        aot.decorate(make('Plain'), train=True)
        aot.decorate(make('Generic'), generic_init=True, train=True)
        assert aot.captured[0][0].ops == aot.captured[1][0].ops
        assert aot.captured[0][1].fn_lines != aot.captured[1][1].fn_lines
        _write_artifact(tmp_path, aot, ('Plain', 'Generic'))
        assert len(aot.generated.REGISTRY_BY_SPEC_KEY) == 2
        assert len({entry[1] for entry in aot.generated.REGISTRY_BY_SPEC_KEY.values()}) == 2

        plain = aot.decorate(make('Plain'))
        generic = aot.decorate(make('Generic'), generic_init=True)
        assert aot.generated_calls[-2:] == [False, False]
        assert plain().x == generic().x == 1
        assert generic.__init__.__annotations__['x'] is int


def test_codegen_deduplicates_source_across_distinct_keys(tmp_path):
    def make(name, priority, default):
        class C:
            x: int = field(default=default, repr_priority=priority)
            y: int = field(default=2, repr_priority=priority * 2)

        C.__qualname__ = name
        return C

    with AotHarness() as aot:
        aot.decorate(make('First', 1, 1), train=True)
        aot.decorate(make('Second', 10, 2), train=True)
        assert aot.captured[0][0].spec_key != aot.captured[1][0].spec_key
        assert aot.captured[0][1].fn_lines == aot.captured[1][1].fn_lines
        _write_artifact(tmp_path, aot, ('First', 'Second'))
        assert len(aot.generated.REGISTRY_BY_SPEC_KEY) == 2
        assert len({entry[1] for entry in aot.generated.REGISTRY_BY_SPEC_KEY.values()}) == 1

        first = aot.decorate(make('First', 1, 3))
        second = aot.decorate(make('Second', 10, 4))
        assert aot.generated_calls[-2:] == [False, False]
        assert first().x == 3
        assert second().x == 4


@pytest.mark.parametrize('width', [80, 120])
def test_codegen_wraps_registry_literals(tmp_path, width):
    name = ('Outer.' * 30) + 'Unicode\u540d\u524d' + "'\\\n"

    def make():
        class C:
            x: int = 1

        C.__qualname__ = name
        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True)
        source = _write_artifact(tmp_path, aot, (name,), width=width)
        lines = source.splitlines()
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('_process_dataclass__'):
                for line in lines[node.decorator_list[0].lineno - 1:node.lineno - 1]:
                    assert len(line) <= width, line
        assert (aot.module.__name__, name) in aot.generated.REGISTRY_BY_CLS_NAME
        assert aot.captured[0][0].spec_key in aot.generated.REGISTRY_BY_SPEC_KEY
        cls = aot.decorate(make())
        assert not aot.generated_calls[-1]
        assert cls().x == 1
