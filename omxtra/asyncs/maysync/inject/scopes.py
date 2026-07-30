import typing as ta

from omcore import lang
from omcore.inject.injector import AsyncInjector
from omcore.inject.keys import Key
from omcore.inject.scopes import DelimitedScope
from omcore.inject.scopes import async_enter_scope


if ta.TYPE_CHECKING:
    from . import maysync as _maysync
else:
    _maysync = lang.proxy_import('.maysync', __package__)


def maysync_enter_scope(
        i: _maysync.MaysyncInjector,
        ss: DelimitedScope,
        seeds: ta.Mapping[Key, ta.Any] | None = None,
) -> ta.ContextManager[None]:
    return lang.sync_async_with(async_enter_scope(
        i[AsyncInjector],
        ss,
        seeds,
    ))
