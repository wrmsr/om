import dataclasses as dc
import typing as ta

from ... import lang
from ... import reflect as rfl
from .configs import ConfigValues
from .options import _EMPTY_OPTIONS
from .options import Options


if ta.TYPE_CHECKING:
    from .runtime import Runtime
    from .types import Marshaler
    from .types import Unmarshaler


T = ta.TypeVar('T')


type Context = BoundContext | FactoryContext
type BoundContext = MarshalContext | UnmarshalContext
type FactoryContext = MarshalFactoryContext | UnmarshalFactoryContext


##


@dc.dataclass(frozen=True, kw_only=True)
class BaseContext(lang.Abstract, lang.Sealed):
    runtime: Runtime

    def get_mirror(self) -> rfl.Mirror:
        return self.runtime.get_mirror()


##


@dc.dataclass(frozen=True, kw_only=True)
class BaseFactoryContext(BaseContext, lang.Abstract):
    def get_configs(
            self,
            key: ta.Any = None,
            *,
            identity: bool | None = None,
    ) -> ConfigValues:
        return self.runtime.get_factory_configs(
            key,
            identity=identity,
        )


@dc.dataclass(frozen=True, kw_only=True)
class MarshalFactoryContext(BaseFactoryContext, lang.Final):
    def make_marshaler(self, o: ta.Any) -> Marshaler:
        return self.runtime.make_marshaler(self, o)


@dc.dataclass(frozen=True, kw_only=True)
class UnmarshalFactoryContext(BaseFactoryContext, lang.Final):
    def make_unmarshaler(self, o: ta.Any) -> Unmarshaler:
        return self.runtime.make_unmarshaler(self, o)


##


@dc.dataclass(frozen=True, kw_only=True)
class BaseHandlerContext(BaseContext, lang.Abstract):
    pass


@dc.dataclass(frozen=True, kw_only=True)
class MarshalContext(BaseHandlerContext, lang.Final):
    options: Options = _EMPTY_OPTIONS


@dc.dataclass(frozen=True, kw_only=True)
class UnmarshalContext(BaseHandlerContext, lang.Final):
    options: Options = _EMPTY_OPTIONS
