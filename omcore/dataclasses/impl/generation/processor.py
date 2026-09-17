"""
TODO:
 - continue rolling back old 'OpExecutor' mode / merging in compilation code
 - (optionally) populate linecache
"""
import abc
import dataclasses as dc
import sys
import typing as ta
import warnings

from .... import check
from .... import lang
from ..processing.base import ProcessingContext
from ..processing.base import ProcessingOption
from ..processing.base import Processor
from ..processing.phases import ProcessorPhase
from ..processing.registry import register_processor_type
from .compilation import OpCompiler
from .globals import FN_GLOBAL_VALUES
from .globals import FnGlobal
from .keys import implementation_key
from .keys import processing_key
from .ops import Op
from .ops import OpRef
from .ops import OpRefMap
from .registry import all_generator_types
from .values import Bindings
from .values import Val


##


@dc.dataclass(frozen=True)
class PrepareOnly(ProcessingOption):
    b: bool


@dc.dataclass(frozen=True, kw_only=True)
class Verbosity(ProcessingOption):
    warn: bool = False
    debug: bool = False


class CompileCallback(ta.Protocol):
    def __call__(
            self,
            ctx: ProcessingContext,
            prepared: GeneratorProcessor.Prepared,
            comp: OpCompiler.CompileResult,
    ) -> None:
        ...


@dc.dataclass(frozen=True, kw_only=True)
class Codegen(ProcessingOption):
    style: ta.Literal['jit', 'aot'] = 'jit'

    force: bool = False
    callback: CompileCallback | None = None

    cache_mode: ta.Literal['checked', 'trusted'] | None = None


##


class CodegenMissingWarning(Warning):
    pass


@register_processor_type(phase=ProcessorPhase.GENERATION)
class GeneratorProcessor(Processor):
    PROCESS_FN_NAME: ta.ClassVar[str] = '_process_dataclass'

    class Mode(lang.Abstract):
        @abc.abstractmethod
        def _process(self, gp: GeneratorProcessor, cls: type) -> None:
            raise NotImplementedError

    class CompilerMode(Mode):
        def __init__(
                self,
                *,
                codegen: Codegen,
        ) -> None:
            super().__init__()

            self._codegen = codegen

        def _process(self, gp: GeneratorProcessor, cls: type) -> None:
            style: OpCompiler.Style = {
                'jit': OpCompiler.JitStyle,
                'aot': OpCompiler.AotStyle,
            }[self._codegen.style]()

            compiler = OpCompiler(style)

            comp = compiler.compile(
                GeneratorProcessor.PROCESS_FN_NAME,
                gp.prepare().ops,
                bindings=gp.prepare().bindings,
            )

            comp_src = '\n'.join([
                *comp.hdr_lines,
                *(['', ''] if comp.hdr_lines else []),
                *comp.fn_lines,
            ])

            if (vo := gp._ctx.option(Verbosity)) is not None and vo.debug:  # noqa
                print('\n\n'.join([
                    f'cache_key={gp.cache_key()!r}',
                    comp_src,
                    '',
                ]), file=sys.stderr)

            ns: dict = {}
            ns.update(compiler.style.globals_ns())  # noqa

            exec(comp_src, ns)
            o_fn = ns[GeneratorProcessor.PROCESS_FN_NAME]

            if cls.__module__ in sys.modules:
                gl = sys.modules[cls.__module__].__dict__
            else:
                gl = {}

            # TODO: comment why lol
            fn = lang.new_function(**{
                **lang.new_function_kwargs(o_fn),
                **dict(
                    globals=gl,
                ),
            })

            kw = {}
            orm = gp.prepare().ref_map
            for r in comp.refs:
                if isinstance(r, OpRef) and r not in gp.prepare().bindings:
                    kw[r.ident()] = orm[r]
                elif isinstance(r, (OpRef, FnGlobal)):
                    pass
                else:
                    raise TypeError(r)

            fn(cls, gp._ctx.cs, gp._ctx, FN_GLOBAL_VALUES, **kw)  # noqa

            if (cg := self._codegen) is not None and (cb := cg.callback) is not None:
                cb(  # noqa
                    gp._ctx,  # noqa
                    gp.prepare(),
                    comp,
                )

    #

    @dc.dataclass(frozen=True)
    class Prepared:
        ops: ta.Sequence[Op]
        ref_map: OpRefMap
        bindings: Bindings
        spec_key: str | None

    @lang.cached_function(no_wrapper_update=True)
    def prepare(self) -> Prepared:
        cg = self._ctx.option(Codegen)
        key = self.cache_key() if cg is not None and cg.callback is not None else None
        gs = [g_ty() for g_ty in all_generator_types()]

        ops: list[Op] = []
        orm: dict[OpRef, ta.Any] = {}
        bindings: dict[OpRef, Val] = {}
        for g in gs:
            if (gen := g.generate(self._ctx)) is None:
                continue

            for k, v in (gen.ref_map or {}).items():
                if k in orm:
                    check.equal(orm[k], v)
                else:
                    orm[k] = v

            ops.extend(gen.ops)

            for k, v in (gen.bindings or {}).items():
                if k in bindings:
                    check.equal(bindings[k], v)
                else:
                    bindings[k] = v

        check.arg(not (orm.keys() & bindings.keys()))

        return self.Prepared(
            tuple(ops),
            orm,
            bindings,
            key if not orm else None,
        )

    @lang.cached_function(no_wrapper_update=True)
    def cache_key(self) -> str | None:
        return processing_key(self._ctx)

    #

    def _process_from_codegen(self, cls: type) -> bool:
        cg_pkg = check.not_none(self._ctx.pkg_cfg.pkg)
        cg_mod_spec = f'{cg_pkg}._dataclasses'

        try:
            __import__(cg_mod_spec)
        except ImportError:
            if (vo := self._ctx.option(Verbosity)) is not None and vo.warn:  # noqa
                warnings.warn(
                    f'Codegen module missing for {cls.__module__}.{cls.__qualname__} at {cg_mod_spec}',
                    CodegenMissingWarning,
                )
            return False

        cg_mod = sys.modules[cg_mod_spec]

        # Plan-keyed and incompatible artifacts are cache misses, not alternate generation protocols.
        if getattr(cg_mod, 'IMPLEMENTATION_KEY', None) != implementation_key():
            return False

        cg = self._ctx.option(Codegen)
        cache_mode = (cg.cache_mode if cg is not None else None) or self._ctx.pkg_cfg.cfg.codegen_mode
        if cache_mode == 'trusted':
            entry = cg_mod.REGISTRY_BY_CLS_NAME.get((cls.__module__, cls.__qualname__))
        else:
            key = self.cache_key()
            entry = cg_mod.REGISTRY_BY_SPEC_KEY.get(key) if key is not None else None
        if entry is None:
            if (vo := self._ctx.option(Verbosity)) is not None and vo.warn:  # noqa
                warnings.warn(
                    f'Codegen missing for {cls.__module__}.{cls.__qualname__} in {cg_mod_spec}',
                    CodegenMissingWarning,
                )
            return False

        _, factory = entry
        factory()(
            cls,
            self._ctx.cs,
            self._ctx,
            FN_GLOBAL_VALUES,
        )

        return True

    #

    def process(self, cls: type) -> type:
        if (po := self._ctx.option(PrepareOnly)) is not None and po.b:
            self.prepare()
            return cls

        cg = self._ctx.option(Codegen)

        if not (cg is not None and cg.force) and self._ctx.pkg_cfg.cfg.codegen:
            if self._process_from_codegen(cls):
                return cls

        if cg is None:
            cg = Codegen()

        mode = GeneratorProcessor.CompilerMode(codegen=cg)

        mode._process(self, cls)  # noqa
        return cls
