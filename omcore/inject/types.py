import typing as ta

from .. import lang


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
