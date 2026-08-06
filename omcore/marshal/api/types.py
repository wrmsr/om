import abc
import typing as ta

from ... import lang
from .specs import Spec


if ta.TYPE_CHECKING:
    from .contexts import MarshalContext
    from .contexts import MarshalFactoryContext
    from .contexts import UnmarshalContext
    from .contexts import UnmarshalFactoryContext
    from .values import Value


type Handler = Marshaler | Unmarshaler
type Factory = MarshalerFactory | UnmarshalerFactory


##


def _check_pair_subclass(cls: type, l: type, r: type, pair: type) -> None:
    if issubclass(cls, l) and issubclass(cls, r) and not issubclass(cls, pair):
        raise TypeError(
            f'{cls!r} subclasses both {l.__name__} and {r.__name__} and must therefore subclass {pair.__name__}',
        )


##


class Marshaler(lang.Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            _check_pair_subclass(cls, Marshaler, Unmarshaler, HandlerPair)
        except NameError:
            pass

    @abc.abstractmethod
    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        raise NotImplementedError


class Unmarshaler(lang.Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            _check_pair_subclass(cls, Marshaler, Unmarshaler, HandlerPair)
        except NameError:
            pass

    @abc.abstractmethod
    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        raise NotImplementedError


class HandlerPair(Marshaler, Unmarshaler, lang.Abstract):
    """
    The mandatory (and mro-order-fixing) base class of anything subclassing both Marshaler and Unmarshaler - enforced by
    those classes themselves. This makes dual-role handlers a nominal concept: an `isinstance(h, HandlerPair)` check is
    always sufficient, there is no such thing as an object which is both a Marshaler and an Unmarshaler but not a
    HandlerPair.
    """


##


class MarshalerFactory(lang.Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            _check_pair_subclass(cls, MarshalerFactory, UnmarshalerFactory, FactoryPair)
        except NameError:
            pass

    @abc.abstractmethod
    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        raise NotImplementedError


class UnmarshalerFactory(lang.Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            _check_pair_subclass(cls, MarshalerFactory, UnmarshalerFactory, FactoryPair)
        except NameError:
            pass

    @abc.abstractmethod
    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        raise NotImplementedError


class FactoryPair(MarshalerFactory, UnmarshalerFactory, lang.Abstract):
    """The factory equivalent of HandlerPair, under the same enforcement."""
