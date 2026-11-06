import asyncio
import dataclasses as dc
import inspect
import os.path
import subprocess
import textwrap
import typing as ta

from omcore import cached
from omcore.logs import all as logs
from omcore.os.temp import temp_dir_context
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ..lite.discovery import LiteSourceTarget
from ..lite.discovery import discover_lite_sources
from ..lite.mirror import LiteSourceMirror
from .base import Precheck
from .base import PrecheckContext


log = logs.get_module_logger(globals())


##


class LitePython8Precheck(Precheck['LitePython8Precheck.Config']):
    @dc.dataclass(frozen=True)
    class Config(Precheck.Config):
        python: str = '.venvs/8/bin/python'
        concurrency: int = 4

    def __init__(self, context: PrecheckContext, config: Config = Config()) -> None:
        super().__init__(config)

        self._context = context

    #

    @cached.function
    def _python_exe(self) -> str:
        # Subprocesses may run with a different cwd, so a path to an executable must not be left relative.
        python = self._config.python
        if os.path.exists(python):
            return os.path.abspath(python)
        return python

    #

    @staticmethod
    def _load_file_module(fp: str) -> None:
        import os.path  # noqa
        import sys  # noqa
        import types  # noqa

        fp = os.path.abspath(fp)

        with open(fp) as f:
            src = f.read()

        mn = os.path.basename(fp).rpartition('.')[0]

        mod = types.ModuleType(mn)
        mod.__name__ = mn
        mod.__file__ = fp
        mod.__builtins__ = __builtins__  # type: ignore
        mod.__spec__ = None

        sys.modules[mn] = mod

        code = compile(src, fp, 'exec')
        exec(code, mod.__dict__, mod.__dict__)

    @cached.function
    def _load_file_module_payload(self) -> str:
        return '\n'.join([
            'import sys',
            'fp = sys.argv[-1]',
            '',
            textwrap.dedent('\n'.join(inspect.getsource(LitePython8Precheck._load_file_module).splitlines()[2:])),
        ])

    #

    async def _run_script(self, fp: str) -> list[Precheck.Violation]:
        log.debug('%s: loading script %s', self.__class__.__name__, fp)

        vs: list[Precheck.Violation] = []

        proc = await asyncio.create_subprocess_exec(
            *subprocess_maybe_shell_wrap_exec(
                self._python_exe(),
                '-c',
                self._load_file_module_payload(),
                fp,
            ),
            stderr=subprocess.PIPE,
        )

        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            vs.append(Precheck.Violation(self, f'lite script {fp} failed to load in python8: {stderr.decode()}'))

        return vs

    async def _run_module(self, fp: str, mirror_dir: str) -> list[Precheck.Violation]:
        vs: list[Precheck.Violation] = []

        mod = fp.rpartition('.')[0].replace(os.sep, '.')

        log.debug('%s: loading module %s', self.__class__.__name__, mod)

        proc = await asyncio.create_subprocess_exec(
            *subprocess_maybe_shell_wrap_exec(
                self._python_exe(),
                '-c',
                f'import {mod}',
            ),
            cwd=mirror_dir,
            stderr=subprocess.PIPE,
        )

        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            vs.append(Precheck.Violation(self, f'lite module {fp} failed to import in python8: {stderr.decode()}'))  # noqa

        return vs

    #

    async def _run_one(self, tgt: LiteSourceTarget, mirror_dir: str) -> list[Precheck.Violation]:
        if tgt.kind == 'script':
            return await self._run_script(tgt.path)

        elif tgt.kind == 'module':
            return await self._run_module(tgt.path, mirror_dir)

        else:
            raise RuntimeError(f'Unknown target kind: {tgt.kind}')

    async def run(self) -> ta.AsyncGenerator[Precheck.Violation]:
        sources = discover_lite_sources(self._context.src_roots)
        if not sources.targets:
            return

        mirror = LiteSourceMirror(
            self._context.src_roots,
            sources.lite_files,
        )

        with temp_dir_context() as mirror_dir:
            log.debug('%s: building lite source mirror in %s', self.__class__.__name__, mirror_dir)
            mirror.build(mirror_dir)

            sem = asyncio.Semaphore(self._config.concurrency)

            async def run(tgt):
                async with sem:
                    return await self._run_one(tgt, mirror_dir)

            tasks = [asyncio.create_task(run(tgt)) for tgt in sources.targets]

            for coro in asyncio.as_completed(tasks):
                for v in await coro:
                    yield v
