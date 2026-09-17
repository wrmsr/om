"""
Exercise the on-disk AOT writer using real generation results captured by AotHarness.

Unlike the runtime-only tests, these replace the harness's initial cache entries with registries loaded from the
writer's output. Subsequent decorations must therefore reuse the written artifact, not the harness's training factory.
"""
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
    """
    Serialize captured training results, run the production writer, and load its artifact into the harness.

    names corresponds to aot.captured in training order. The marshal round trip exercises the dumper/writer data
    boundary without launching the module-scanning subprocess. Executing the output replaces the harness registries
    with the generated file's own registrations and factories. Return the source for formatting assertions.
    """

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
    """The writer must keep separate installers when identical methods obtain annotations through different recipes."""

    def make(name):
        class C:
            x: int = 1

        C.__qualname__ = name
        return C

    with AotHarness() as aot:
        aot.decorate(make('Plain'), train=True)
        aot.decorate(make('Generic'), generic_init=True, train=True)
        # Method bodies agree, but direct spec annotations and generic-substituted annotations need different bindings.
        assert aot.captured[0][0].ops == aot.captured[1][0].ops
        assert aot.captured[0][1].fn_lines != aot.captured[1][1].fn_lines
        _write_artifact(tmp_path, aot, ('Plain', 'Generic'))
        assert len(aot.generated.REGISTRY_BY_SPEC_KEY) == 2
        # Count distinct factories, not registry entries: two keys must not have been folded into one installer here.
        assert len({entry[1] for entry in aot.generated.REGISTRY_BY_SPEC_KEY.values()}) == 2

        plain = aot.decorate(make('Plain'))
        generic = aot.decorate(make('Generic'), generic_init=True)
        # Ignore the two training calls: Plain and Generic must both hit the written cache without generation.
        assert aot.generated_calls[-2:] == [False, False]
        assert plain().x == generic().x == 1
        assert generic.__init__.__annotations__['x'] is int


def test_codegen_deduplicates_source_across_distinct_keys(tmp_path):
    """Conservative keys may differ even when one installer is correct for both classes."""

    def make(name, priority, default):
        class C:
            x: int = field(default=default, repr_priority=priority)
            y: int = field(default=2, repr_priority=priority * 2)

        C.__qualname__ = name
        return C

    with AotHarness() as aot:
        aot.decorate(make('First', 1, 1), train=True)
        aot.decorate(make('Second', 10, 2), train=True)
        # (1, 2) and (10, 20) are different priorities but sort the fields identically. Defaults remain opaque.
        assert aot.captured[0][0].spec_key != aot.captured[1][0].spec_key
        assert aot.captured[0][1].fn_lines == aot.captured[1][1].fn_lines
        _write_artifact(tmp_path, aot, ('First', 'Second'))
        assert len(aot.generated.REGISTRY_BY_SPEC_KEY) == 2
        # Both lookup keys should point at the same factory emitted by the writer.
        assert len({entry[1] for entry in aot.generated.REGISTRY_BY_SPEC_KEY.values()}) == 1

        first = aot.decorate(make('First', 1, 3))
        second = aot.decorate(make('Second', 10, 4))
        assert aot.generated_calls[-2:] == [False, False]  # Both fresh classes reused that shared installer.
        # Sharing source must not share the runtime defaults extracted for each class.
        assert first().x == 3
        assert second().x == 4


@pytest.mark.parametrize('width', [80, 120])
def test_codegen_wraps_registry_literals(tmp_path, width):
    """Wrapping must respect the requested columns while preserving exact lookup strings, including escapes."""

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
        # Only the registration metadata is under test here, not formatting arbitrary generated method bodies.
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('_process_dataclass__'):
                for line in lines[node.decorator_list[0].lineno - 1:node.lineno - 1]:
                    assert len(line) <= width, line
        assert (aot.module.__name__, name) in aot.generated.REGISTRY_BY_CLS_NAME
        assert aot.captured[0][0].spec_key in aot.generated.REGISTRY_BY_SPEC_KEY
        cls = aot.decorate(make())
        assert not aot.generated_calls[-1]  # The written, wrapped key still finds the installer without regeneration.
        assert cls().x == 1
