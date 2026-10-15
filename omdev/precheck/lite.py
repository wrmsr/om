import asyncio
import dataclasses as dc
import glob
import inspect
import os.path
import subprocess
import textwrap
import typing as ta

from omcore import cached
from omcore.logs import all as logs
from omcore.os.temp import temp_dir_context
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from .. import magic
from .base import Precheck
from .base import PrecheckContext


log = logs.get_module_logger(globals())


##


class LiteSourceMirror:
    """
    Mirrors source roots into a scratch directory such that lite modules can be imported under an old interpreter
    without executing the non-lite `__init__.py` modules above them.

    Directories which are lite packages (their `__init__.py` is itself lite-marked), or which contain no lite files at
    all, are symlinked wholesale. Any other directory with lite files somewhere beneath it is recreated for real, with
    its `__init__.py` replaced by an empty file and its remaining entries symlinked - non-lite siblings included, so a
    lite module importing one still fails as it should.

    All paths are relative to `src_dir`, which defaults to the current directory.
    """

    def __init__(
            self,
            roots: ta.Sequence[str],
            lite_files: ta.Iterable[str],
            *,
            src_dir: str | None = None,
    ) -> None:
        super().__init__()

        if isinstance(roots, str):
            raise TypeError(roots)

        self._roots = [os.path.normpath(r) for r in roots]
        self._lite_files = frozenset(os.path.normpath(f) for f in lite_files)
        self._src_dir = os.path.abspath(src_dir if src_dir is not None else os.getcwd())

    @property
    def roots(self) -> ta.Sequence[str]:
        return self._roots

    @property
    def lite_files(self) -> ta.AbstractSet[str]:
        return self._lite_files

    @property
    def src_dir(self) -> str:
        return self._src_dir

    #

    @cached.property
    def lite_package_dirs(self) -> ta.AbstractSet[str]:
        return frozenset(
            os.path.dirname(f)
            for f in self._lite_files
            if os.path.basename(f) == '__init__.py'
        )

    def is_in_lite_package(self, path: str) -> bool:
        return any(
            path == p or path.startswith(p + os.sep)
            for p in self.lite_package_dirs
        )

    @cached.property
    def materialized_dirs(self) -> ta.AbstractSet[str]:
        ret: set[str] = set()

        for f in self._lite_files:
            d = os.path.dirname(f)
            while d:
                if not self.is_in_lite_package(d):
                    ret.add(d)
                d = os.path.dirname(d)

        return frozenset(ret)

    #

    def _write_empty_init(self, dst_dir: str) -> None:
        with open(os.path.join(dst_dir, '__init__.py'), 'w'):
            pass

    def _mirror_dir(self, rel: str, dst: str) -> None:
        src = os.path.join(self._src_dir, rel)

        if rel not in self.materialized_dirs:
            os.symlink(src, dst)
            return

        os.mkdir(dst)

        with os.scandir(src) as it:
            entries = sorted(it, key=lambda e: e.name)

        for e in entries:
            e_dst = os.path.join(dst, e.name)

            if e.name == '__pycache__':
                continue

            elif e.is_dir():
                self._mirror_dir(os.path.join(rel, e.name), e_dst)

            elif e.name == '__init__.py':
                self._write_empty_init(dst)

            else:
                os.symlink(e.path, e_dst)

    def build(self, dst_dir: str) -> None:
        for root in self._roots:
            # The parents of a nested root are not mirrored, just created as bare packages leading down to it.
            parent_rel = ''
            for part in os.path.dirname(root).split(os.sep):
                if not part:
                    continue

                parent_rel = os.path.join(parent_rel, part)
                parent_dst = os.path.join(dst_dir, parent_rel)
                if not os.path.lexists(parent_dst):
                    os.mkdir(parent_dst)
                    self._write_empty_init(parent_dst)

            dst = os.path.join(dst_dir, root)
            if not os.path.lexists(dst):
                self._mirror_dir(root, dst)


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

    @dc.dataclass(frozen=True)
    class _Target:
        path: str
        kind: ta.Literal['script', 'module']

    @dc.dataclass(frozen=True)
    class _Plan:
        lite_files: ta.AbstractSet[str]
        targets: ta.Sequence[LitePython8Precheck._Target]

    def _collect_plan(self) -> _Plan:
        lite_files = frozenset(magic.find_magic_files(
            magic.PY_MAGIC_STYLE,
            self._context.src_roots,
            keys=['@om-lite'],
        ))

        # A module both carrying its own marker and sitting under a lite-marked package is reached both ways, hence the
        # set.
        tgts: set[LitePython8Precheck._Target] = set()

        for fp in sorted(lite_files):
            with open(fp) as f:  # noqa  # FIXME
                src = f.read()

            is_script = '# @om-script' in src.splitlines()

            if is_script:
                tgts.add(self._Target(fp, 'script'))

            elif fp.endswith('__init__.py'):
                for g in glob.glob(os.path.join(os.path.dirname(fp), '**/*.py'), recursive=True):
                    tgts.add(self._Target(g, 'module'))

            else:
                tgts.add(self._Target(fp, 'module'))

        return self._Plan(
            lite_files,
            sorted(tgts, key=lambda t: t.path),
        )

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

    async def _run_one(self, tgt: _Target, mirror_dir: str) -> list[Precheck.Violation]:
        if tgt.kind == 'script':
            return await self._run_script(tgt.path)

        elif tgt.kind == 'module':
            return await self._run_module(tgt.path, mirror_dir)

        else:
            raise RuntimeError(f'Unknown target kind: {tgt.kind}')

    async def run(self) -> ta.AsyncGenerator[Precheck.Violation]:
        plan = self._collect_plan()
        if not plan.targets:
            return

        mirror = LiteSourceMirror(
            self._context.src_roots,
            plan.lite_files,
        )

        with temp_dir_context() as mirror_dir:
            log.debug('%s: building lite source mirror in %s', self.__class__.__name__, mirror_dir)
            mirror.build(mirror_dir)

            sem = asyncio.Semaphore(self._config.concurrency)

            async def run(tgt):
                async with sem:
                    return await self._run_one(tgt, mirror_dir)

            tasks = [asyncio.create_task(run(tgt)) for tgt in plan.targets]

            for coro in asyncio.as_completed(tasks):
                for v in await coro:
                    yield v
