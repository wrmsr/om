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
    def __init__(self):
        super().__init__()

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
        self.captured = []
        self.generated_calls = []

    def __enter__(self):
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
        if ctx.cls.__module__ != self.module.__name__:
            return
        self.captured.append((prepared, comp))
        ns: dict = {}
        exec(compile('\n'.join([*comp.hdr_lines, *comp.fn_lines]), '<dataclass-aot-test>', 'exec'), ns)
        fn = ns[comp.fn_name]
        entry: tuple = ({}, lambda: fn)
        if prepared.spec_key is not None:
            self.generated.REGISTRY_BY_SPEC_KEY[prepared.spec_key] = entry
            self.generated.REGISTRY_BY_CLS_NAME[(ctx.cls.__module__, ctx.cls.__qualname__)] = entry

    def decorate(self, cls, *, train=False, trusted=False, **kwargs):
        cls.__module__ = self.module.__name__
        profile = cProfile.Profile()
        with processing_options_context(Codegen(
                style='aot',
                force=train,
                callback=self._capture if train else None,
                cache_mode='trusted' if trusted else 'checked',
        )):
            result = profile.runcall(dataclass, cls, **kwargs)
        generate_codes = {g.generate.__code__ for g in all_generator_types()}
        self.generated_calls.append(any(e.code in generate_codes for e in profile.getstats()))
        return result
