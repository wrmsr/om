"""
TODO:
 - refactor dc gen to just Execute and Codegen
 - need to bubble up imports, preamble, deduped
 - _gen subdirs
 - static analyze codegen kwarg if possible
 - better ignore configurability than just tests dirs lol
"""
import ast
import asyncio
import hashlib
import inspect
import json
import os.path
import shlex
import sys
import tempfile
import time
import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore.asyncs.asyncio import all as au
from omcore.lite.marshal import unmarshal_obj
from omcore.logs import all as logs

from ..py.asts.toplevel import TopLevelCall
from ..py.asts.toplevel import analyze_module_top_level
from ..py.reprs import textwrap_repr
from ..py.srcheaders import get_py_header_lines
from .dumping import DataclassCodegenDumperOutput
from .dumping import DumpedDataclassCodegen


log = logs.get_module_logger(globals())


##


def _find_dir_py_files(dir_path: str) -> list[str]:
    return sorted(
        os.path.join(p, fn)
        for p, dns, fns in os.walk(dir_path)
        for fn in fns
        if fn.endswith('.py')
    )


@lang.cached_function
def _module_manifest_dumper_payload_src() -> str:
    from . import _dumping
    return inspect.getsource(_dumping)


def _is_generated_py_file(fp: str) -> bool:
    with open(fp) as f:
        gen_file_src = f.read()

    gen_hdr_lines = get_py_header_lines(gen_file_src)
    return any(hl.src.strip() == '# @om-generated' for hl in gen_hdr_lines)


#


class DataclassCodeGen:
    DEFAULT_TARGET_LINE_WIDTH: ta.ClassVar[int] = 120

    def __init__(
            self,
            *,
            target_line_width: int | None = None,
            dump_inline: bool = False,
            dry_run: bool = False,
            print_code: bool = False,
            debug: bool = False,
            subprocess_kwargs: ta.Mapping[str, ta.Any] | None = None,
    ) -> None:
        super().__init__()

        self._target_line_width = target_line_width or self.DEFAULT_TARGET_LINE_WIDTH
        self._dump_inline = dump_inline
        self._dry_run = dry_run
        self._print_code = print_code
        self._debug = debug
        self._subprocess_kwargs = subprocess_kwargs

    #

    @dc.dataclass(frozen=True)
    class ConfiguredPackage:
        name: str

        init_file_path: str
        init_module_name: str

        init_package_call: TopLevelCall

    def scan_py_file(self, file_path: str) -> ConfiguredPackage | None:
        with open(file_path) as f:
            source = f.read()

        module = check.isinstance(ast.parse(source), ast.Module)
        module_name = '.'.join([
            *os.path.dirname(file_path).split(os.path.sep),
            os.path.basename(file_path).removesuffix('.py'),
        ])

        tl = analyze_module_top_level(module, module_name)

        init_calls: list[TopLevelCall] = []
        for call in tl.calls:
            if call.imp.spec != 'omcore.dataclasses':
                continue
            match call.node:
                case ast.Call(func=ast.Attribute(attr='init_package')):
                    init_calls.append(call)

        if not init_calls:
            return None
        if os.path.basename(file_path) != '__init__.py':
            raise ValueError(f'File {file_path} has init_package call and is not an __init__.py: {init_calls!r}')
        if len(init_calls) > 1:
            raise ValueError(f'File {file_path} has multiple init_package calls: {init_calls!r}')

        return DataclassCodeGen.ConfiguredPackage(
            '.'.join(module_name.split('.')[:-1]),
            file_path,
            module_name,
            check.single(init_calls),
        )

    def find_configured_packages(self, root_dirs: ta.Iterable[str]) -> list[ConfiguredPackage]:
        check.not_isinstance(root_dirs, str)

        py_files = (
            fp
            for rd in root_dirs
            for fp in _find_dir_py_files(rd)
        )

        return [
            cfg_pkg
            for file_path in py_files
            if (cfg_pkg := self.scan_py_file(file_path)) is not None
        ]

    #

    async def _run_dumper_subprocess(
            self,
            cfg_pkg: ConfiguredPackage,
            dumper_kwargs: ta.Mapping[str, ta.Any],
            *,
            shell_wrap: bool = True,
    ) -> None:
        dumper_payload_src = _module_manifest_dumper_payload_src()

        subproc_src = '\n\n'.join([
            dumper_payload_src,
            f'_DataclassCodegenDumper()(**{dumper_kwargs!r})\n',
        ])

        args = [
            sys.executable,
            '-c',
            subproc_src,
        ]

        if shell_wrap:
            args = ['sh', '-c', ' '.join(map(shlex.quote, args))]

        proc = await asyncio.create_subprocess_exec(
            *args,
            **(self._subprocess_kwargs or {}),
        )

        if await proc.wait():
            raise Exception('Subprocess failed')

    async def _run_dumper_inline(
            self,
            cfg_pkg: ConfiguredPackage,
            dumper_kwargs: ta.Mapping[str, ta.Any],
    ) -> None:
        from . import dumping

        dumping._DataclassCodegenDumper()(**dumper_kwargs)  # noqa

    async def process_configured_package(
            self,
            cfg_pkg: ConfiguredPackage,
            *,
            warn_threshold_s: float | None = 10.,
    ) -> None:
        log.info(lambda: f'Running codegen on package: {cfg_pkg.name}')

        out_dir = tempfile.mkdtemp()
        out_file_path = os.path.join(out_dir, 'output.json')

        dumper_kwargs = dict(
            init_file_path=cfg_pkg.init_file_path,
            out_file_path=out_file_path,
            cfg_pkg_name=cfg_pkg.name,
            **(dict(debug=True) if self._debug else {}),
        )

        start_time = time.time()

        if self._dump_inline:
            await self._run_dumper_inline(cfg_pkg, dumper_kwargs)
        else:
            await self._run_dumper_subprocess(cfg_pkg, dumper_kwargs)

        end_time = time.time()

        if warn_threshold_s is not None and (elapsed_time := (end_time - start_time)) >= warn_threshold_s:
            log.warning('Dataclass codegen took a long time: %s, %.2f s', cfg_pkg.name, elapsed_time)

        with open(out_file_path) as f:  # noqa
            out_s = f.read()

        output: DataclassCodegenDumperOutput = unmarshal_obj(json.loads(out_s), DataclassCodegenDumperOutput)

        await self.process_dumper_output(cfg_pkg, output)

    #

    PROCESS_FN_NAME: ta.ClassVar[str] = '_process_dataclass'

    def _string_literal_lines(self, value: str, *, indent: int, suffix: str = '') -> list[str]:
        prefix = ' ' * indent
        literal = repr(value)
        if indent + len(literal) + len(suffix) <= self._target_line_width:
            return [f'{prefix}{literal}{suffix}']
        return [
            f'{prefix}(',
            *[
                f'{prefix}    {line}'
                for line in textwrap_repr(value, self._target_line_width - indent - 4)
            ],
            f'{prefix}){suffix}',
        ]

    async def process_dumper_output(
            self,
            cfg_pkg: ConfiguredPackage,
            output: DataclassCodegenDumperOutput,
    ) -> None:
        gen_file_path = os.path.join(os.path.dirname(cfg_pkg.init_file_path), '_dataclasses.py')

        for err_mod, err_str in output.import_errors.items():
            log.error(lambda: f'Failed to import {err_mod}: {err_str}')

        if os.path.isfile(gen_file_path):
            if not _is_generated_py_file(gen_file_path):
                raise RuntimeError(f'Refusing to overwrite non-generated file: {gen_file_path!r}')

        #

        lines = [
            '# @om-generated',
        ]

        from . import _template
        lines.extend(inspect.getsource(_template).strip().split('\n'))
        lines.extend(['', '', f'IMPLEMENTATION_KEY = {output.implementation_key!r}'])

        #

        processed_modules = set(output.processed_modules)

        # The emitted source includes binding expressions, helper lookups, and installation behavior. Different
        # conservative keys may share exactly the same installer without a separate normalized plan representation.
        dumped_by_source: dict[
            tuple[
                tuple[str, ...],  # hdr_lines
                tuple[str, ...],  # fn_lines
            ],
            list[DumpedDataclassCodegen],
        ] = {}

        seen_cls_name_tups: set[tuple[str, str]] = set()

        for x in output.dumped:
            if x.cls_module not in processed_modules or x.spec_key is None:
                continue

            cls_name_tup = (x.cls_module, x.cls_qualname)
            check.not_in(
                cls_name_tup,
                seen_cls_name_tups,
                f'Class {cls_name_tup!r} has already been seen - this is usually caused by the module failing to '
                f'successfully import (and trying again) - ensure the module imports successfully.',
            )
            seen_cls_name_tups.add(cls_name_tup)

            source_key = (
                tuple(x.hdr_lines),
                tuple(x.fn_lines),
            )
            try:
                lst = dumped_by_source[source_key]
            except KeyError:
                dumped_by_source[source_key] = [x]
                continue

            y = lst[0]
            if set(x.refs) != set(y.refs):
                raise RuntimeError(f'Mismatched refs: {x!r} != {y!r}')

            lst.append(x)

        #

        # Sorted by first cls name for more stable diffs than say sha1
        for grp in sorted(
                dumped_by_source.values(),
                key=lambda grp: min([(y.cls_module, y.cls_qualname) for y in grp]),
        ):
            x = grp[0]
            installer_sha1 = hashlib.sha1(repr((tuple(x.hdr_lines), tuple(x.fn_lines))).encode()).hexdigest()  # noqa

            fn_name = f'{self.PROCESS_FN_NAME}__{installer_sha1}'

            lines.extend(['', ''])

            lines.append(
                '@_register(',
            )

            lines.extend([
                f'    installer_sha1={installer_sha1!r},',
                f'    spec_keys=(',
                *[
                    line
                    for key in sorted({check.not_none(y.spec_key) for y in grp})
                    for line in self._string_literal_lines(key, indent=8, suffix=',')
                ],
                f'    ),',
                f'    cls_names=(',
            ])
            for cn in sorted((y.cls_module, y.cls_qualname) for y in grp):
                if len(line := f'        {cn!r},') <= self._target_line_width:
                    lines.append(line)
                else:
                    lines.extend([
                        '        (',
                        *self._string_literal_lines(cn[0], indent=12, suffix=','),
                        *self._string_literal_lines(cn[1], indent=12, suffix=','),
                        '        ),',
                    ])
            lines.append('    ),')

            lines.append(
                ')',
            )

            lines.extend([
                f'def {fn_name}():',
            ])

            lines.extend([
                f'    {l}' if l.strip() else ''
                for l in x.fn_lines
            ])

            lines.extend([
                '',
                f'    return {x.fn_name}',
            ])

        lines.append('')

        code = '\n'.join(lines)

        if self._print_code:
            print(code)

        if not self._dry_run:
            with open(gen_file_path, 'w') as f:  # noqa
                f.write(code)

    async def run(
            self,
            root_dirs: ta.Iterable[str],
            *,
            concurrency: int | None = 4,
    ) -> None:
        check.not_isinstance(root_dirs, str)

        cfg_pkgs = self.find_configured_packages(root_dirs)

        cfg_pkg_trie = col.Trie([  # noqa
            (cfg_pkg.name.split('.'), cfg_pkg)
            for cfg_pkg in cfg_pkgs
        ])

        await au.wait_maybe_concurrent([
            self.process_configured_package(cfg_pkg)
            for cfg_pkg in cfg_pkgs
        ], concurrency)
