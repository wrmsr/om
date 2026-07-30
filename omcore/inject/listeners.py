import typing as ta

from .. import dataclasses as dc
from .. import lang
from .bindings import Binding
from .elements import Element
from .injector import AsyncInjector
from .keys import Key


##


class ProvisionListener(ta.Protocol):
    def __call__(
            self,
            injector: AsyncInjector,
            key: Key,
            binding: Binding | None,
            provide: ta.Callable[[], ta.Awaitable[ta.Any]],
            /,
    ) -> ta.Awaitable[ta.Any]:
        ...


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class ProvisionListenerBinding(Element, lang.Final):
    listener: ProvisionListener


def bind_provision_listener(l: ProvisionListener) -> Element:
    return ProvisionListenerBinding(l)
