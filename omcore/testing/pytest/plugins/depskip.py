"""
https://github.com/pytest-dev/pytest/blob/72c682ff9773ad2690711105a100423ebf7c7c15/src/_pytest/python.py#L494

--

https://github.com/pytest-dev/pytest-asyncio/blob/b1dc0c3e2e82750bdc6dbdf668d519aaa89c036c/pytest_asyncio/plugin.py#L657
"""
import abc
import dataclasses as dc
import re
import typing as ta

import pytest

from .... import check
from .... import lang
from ._registry import register as register_plugin
from .utils import find_plugin


##


@register_plugin
class DepSkipPlugin:
    @dc.dataclass(frozen=True)
    class Context:
        file_name: str

        import_error: ImportError
        import_name: str

    class Entry(lang.Abstract):
        @abc.abstractmethod
        def should_skip(self, ctx: DepSkipPlugin.Context) -> bool:
            raise NotImplementedError

    @dc.dataclass(frozen=True)
    class FnEntry(Entry):
        fn: ta.Callable[[DepSkipPlugin.Context], bool]

        def should_skip(self, ctx: DepSkipPlugin.Context) -> bool:
            return self.fn(ctx)

    @dc.dataclass(frozen=True)
    class PatEntry(Entry):
        file_pats: ta.Sequence[re.Pattern]
        import_pats: ta.Sequence[re.Pattern]

        def should_skip(self, ctx: DepSkipPlugin.Context) -> bool:
            return (
                bool(name := ctx.import_error.name) and
                any(fp.fullmatch(ctx.file_name) for fp in self.file_pats) and
                any(ip.fullmatch(name) for ip in self.import_pats)  # noqa
            )

    #

    def __init__(self) -> None:
        super().__init__()

        self._entries: list[DepSkipPlugin.Entry] = []

    def add_entry(self, e: Entry) -> None:
        self._entries.append(e)

    @pytest.hookimpl
    def pytest_collectstart(self, collector: pytest.Collector) -> None:
        if isinstance(collector, pytest.Module):
            original_attr = f'__{self.__class__.__qualname__.replace(".", "__")}__original_getobj'

            def _patched_getobj():
                try:
                    return getattr(collector, original_attr)()

                except pytest.Collector.CollectError as ce:
                    if (
                            (ie := ce.__cause__) and
                            isinstance(ie, ImportError) and
                            (file_name := collector.nodeid)
                    ):
                        ctx = DepSkipPlugin.Context(
                            file_name=file_name,
                            import_error=ie,
                            import_name='.'.join([
                                check.non_empty_str(ie.name),
                                *([ie.name_from] if ie.name_from else []),
                            ]),
                        )

                        if any(e.should_skip(ctx) for e in self._entries):
                            pytest.skip(
                                f'skipping {file_name} to missing optional dependency {ctx.import_name}',
                                allow_module_level=True,
                            )

                    raise

            setattr(collector, original_attr, collector._getobj)  # noqa
            collector._getobj = _patched_getobj  # type: ignore  # noqa


#


def register(
        pm: pytest.PytestPluginManager,
        e: DepSkipPlugin.Entry,
) -> None:
    pg = check.not_none(find_plugin(pm, DepSkipPlugin))
    pg.add_entry(e)


def fn_register(
        pm: pytest.PytestPluginManager,
        fn: ta.Callable[[DepSkipPlugin.Context], bool],
) -> None:
    register(pm, DepSkipPlugin.FnEntry(fn))


def regex_register(
        pm: pytest.PytestPluginManager,
        file_pats: ta.Iterable[str],
        import_pats: ta.Iterable[str],
) -> None:
    check.not_isinstance(file_pats, str)
    check.not_isinstance(import_pats, str)

    register(pm, DepSkipPlugin.PatEntry(
        [re.compile(fp) for fp in file_pats],
        [re.compile(ip) for ip in import_pats],
    ))


def module_register(
        pm: pytest.PytestPluginManager,
        mods: ta.Iterable[str],
        import_mods: ta.Iterable[str],
) -> None:
    check.not_isinstance(mods, str)
    check.not_isinstance(import_mods, str)

    for m in [*mods, *import_mods]:
        check.non_empty_str(m)
        check.arg(all(p.isidentifier() for p in m.split('.')), m)

    regex_register(
        pm,
        [rf'{re.escape(m.replace(".", "/"))}(/.*)?\.py' for m in mods],
        [rf'{re.escape(m)}(\..*)?' for m in import_mods],
    )
