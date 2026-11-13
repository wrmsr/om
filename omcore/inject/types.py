import typing as ta

from .. import lang


if ta.TYPE_CHECKING:
    from . import injector as _injector
    from . import sync as _sync
else:
    _injector = lang.proxy_import('.injector', __package__)
    _sync = lang.proxy_import('.sync', __package__)


type AnyInjector = _injector.AsyncInjector | _sync.Injector


##


class Tag(ta.NamedTuple):
    """
    Used to tag dependencies from within `ta.Annotation` type forms. *NOT* to be used as an explicit `tag=` param
    passed to other injector machinery: it's explicitly forbidden (and checked at runtime) to do something like
    `inj.as_key(int, tag=inj.Tag('my-int'))` - you should instead just do `inj.as_key(int, tag='my-int')`.
    """

    tag: ta.Any


##


class Scope(lang.Abstract):
    def __repr__(self) -> str:
        return type(self).__name__


class Unscoped(Scope, lang.Singleton, lang.Final):
    pass
