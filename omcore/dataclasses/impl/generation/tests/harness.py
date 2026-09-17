import cProfile
import sys
import types
import typing as ta
import uuid

from ...api import dataclass
from ...configs import PACKAGE_CONFIG_CACHE
from ...configs import PackageConfig
from ...processing.driving import processing_options_context
from ..keys import implementation_key
from ..processor import Codegen
from ..registry import all_generator_types


##


class AotHarness:
    """
    Exercise real dataclass generation and cache lookup using an in-memory package and generated module.

    Tests usually decorate one class with train=True to generate and cache an installer, then decorate a fresh class
    without train=True to test reuse. Use fresh classes: decorating an already transformed class is a different case.
    The cached source is compiled and executed, not replaced with a mock installer. The omdev writer tests separately
    cover serializing these installers into a generated module on disk.

    generated_calls contains one boolean per decorate() call that returned successfully, in call order. True means at
    least one registered generator's generate() ran; False means none ran. Thus [True, False] normally means "training
    generated the installer, then the second decoration reused it". These are not call counts or timings, and they do
    not describe calls to generated methods such as the resulting class's __init__. A call that raises appends nothing.
    Preparation-only decoration can record True without installing any methods.

    cProfile observes function-call events deterministically, not by sampling. We only inspect which code objects
    executed, ignoring timings entirely. This avoids monkeypatching generators or adding production test hooks. The
    observation covers synchronous decoration in the calling thread, not work dispatched to other threads.
    """

    def __init__(self):
        super().__init__()

        # Unique names keep each harness's imports and package configuration separate from other tests.
        self.pkg = f'_dataclass_cache_test_{uuid.uuid4().hex}'
        self.package = types.ModuleType(self.pkg)
        self.package.__path__ = []
        self.module = types.ModuleType(f'{self.pkg}.models')
        self.generated: ta.Any = types.ModuleType(f'{self.pkg}._dataclasses')
        for a, v in dict(
            IMPLEMENTATION_KEY=implementation_key(),
            REGISTRY_BY_SPEC_KEY={},
            REGISTRY_BY_CLS_NAME={},
        ).items():
            setattr(self.generated, a, v)
        self.captured = []  # (Prepared, CompileResult) pairs from this package's training callbacks.
        self.generated_calls = []

    def __enter__(self):
        # Production lookup imports <package>._dataclasses; sys.modules lets that lookup find our in-memory artifact.
        PACKAGE_CONFIG_CACHE.put(self.pkg, PackageConfig(codegen=True))
        sys.modules[self.pkg] = self.package
        sys.modules[self.module.__name__] = self.module
        sys.modules[self.generated.__name__] = self.generated
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del sys.modules[self.pkg]
        del sys.modules[self.module.__name__]
        del sys.modules[self.generated.__name__]

    def _capture(self, ctx, prepared, comp):
        """Compile a training result into a reusable installer and publish it in the normal cache registries."""

        if ctx.cls.__module__ != self.module.__name__:
            return
        self.captured.append((prepared, comp))
        ns: dict = {}
        exec(compile('\n'.join([*comp.hdr_lines, *comp.fn_lines]), '<dataclass-aot-test>', 'exec'), ns)
        fn = ns[comp.fn_name]
        # Production entries contain metadata and a factory returning the installer, not the installer itself.
        entry: tuple = ({}, lambda: fn)
        # Unsupported installations can still generate correctly, but must not become fast-cache entries.
        if prepared.spec_key is not None:
            self.generated.REGISTRY_BY_SPEC_KEY[prepared.spec_key] = entry
            self.generated.REGISTRY_BY_CLS_NAME[(ctx.cls.__module__, ctx.cls.__qualname__)] = entry

    def decorate(self, cls, *, train=False, trusted=False, **kwargs):
        """
        Decorate a fresh class and record whether generation ran during that call.

        train=True forces generation even if an entry exists, and captures the resulting installer. Otherwise the
        production lookup chooses reuse or fallback; fallback alone does not populate this harness's cache. trusted=True
        selects the module/qualname registry instead of the structural-key registry. Both modes still check the
        implementation stamp. Remaining kwargs go to the dataclass decorator unchanged.
        """

        cls.__module__ = self.module.__name__
        profile = cProfile.Profile()
        with processing_options_context(Codegen(
                style='aot',
                force=train,
                callback=self._capture if train else None,
                cache_mode='trusted' if trusted else 'checked',
        )):
            result = profile.runcall(dataclass, cls, **kwargs)
        # Match generate() code objects, not function names or durations. Even an immediate return is recorded by
        # cProfile, so a fast accidental generation call cannot slip between samples: there are no samples.
        generate_codes = {g.generate.__code__ for g in all_generator_types()}
        self.generated_calls.append(any(e.code in generate_codes for e in profile.getstats()))
        return result
