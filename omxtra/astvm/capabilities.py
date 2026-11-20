import dataclasses as dc
import typing as ta

from .values import BoundaryError
from .values import CapabilityError


##


@dc.dataclass(frozen=True)
class HostCall:
    """
    Explicit host-call policy. Default arguments are copied ordinary data.

    guest_arguments=True passes opaque guest values to trusted adapter code. This is useful for __exit__(), whose
    exception/type arguments are not exportable data. Such callbacks must not reenter the interpreter. Return values
    always undergo the ordinary closed import check; this flag never admits native return objects.
    """

    function: ta.Callable[..., object]
    guest_arguments: bool = False


@dc.dataclass(frozen=True)
class HostObject:
    """An explicit method table, NOT an arbitrary Python object proxy. Callbacks are trusted."""

    methods: ta.Mapping[str, ta.Callable[..., object] | HostCall]
    name: str = 'capability object'


class CapabilityFailure(Exception):  # noqa: N818
    """A trusted callback may explicitly request a data-only guest exception."""

    def __init__(self, name: str, *args: object) -> None:
        super().__init__(*args)

        self.name = name


class Capabilities:
    def __init__(self) -> None:
        super().__init__()

        self._next = 0
        self._calls: dict[int, HostCall] = {}
        self._objects: dict[int, tuple[HostObject, dict[str, int]]] = {}

    def register(self, callback: ta.Callable[..., object] | HostCall) -> int:
        policy = callback if type(callback) is HostCall else HostCall(ta.cast('ta.Callable[..., object]', callback))
        if not callable(policy.function) or type(policy.guest_arguments) is not bool:
            raise TypeError('invalid capability call policy')

        self._next += 1
        self._calls[self._next] = policy
        return self._next

    def guest_arguments(self, identifier: int) -> bool:
        return self._calls[identifier].guest_arguments

    def register_object(self, obj: HostObject) -> tuple[str, dict[str, int]]:
        entry = self._objects.get(id(obj))
        if entry is None:
            methods = {}
            for name, callback in obj.methods.items():
                if type(name) is not str:
                    raise BoundaryError('method name must be an exact str')
                methods[name] = self.register(callback)
            entry = (obj, methods)
            self._objects[id(obj)] = entry
        return obj.name, dict(entry[1])

    def invoke(
            self,
            identifier: int,
            args: list[object],
            kwargs: dict[str, object],
    ) -> object:
        try:
            return self._calls[identifier].function(*args, **kwargs)
        except CapabilityFailure:
            raise
        except Exception as exc:
            # Unexpected host failures never become guest exceptions or guest traceback objects.
            raise CapabilityError('trusted capability failed') from exc
