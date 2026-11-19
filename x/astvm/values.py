import dataclasses as dc
import typing as ta


type Value = ta.Union[  # noqa: UP007
    None,
    bool,
    int,
    float,
    complex,
    str,
    bytes,
    ObjectRef,
    _Singleton,
]


##


@dc.dataclass(frozen=True, slots=True)
class _Singleton:
    name: str

    def __deepcopy__(self, memo: dict[int, object]) -> _Singleton:
        return self


_MISSING = _Singleton('missing')
_ELLIPSIS = _Singleton('Ellipsis')
_NOT_IMPLEMENTED = _Singleton('NotImplemented')

_SCALARS = (
    type(None),
    bool,
    int,
    float,
    complex,
    str,
    bytes,
)

_NUMBERS = (
    bool,
    int,
    float,
    complex,
)


@dc.dataclass(frozen=True, slots=True)
class ObjectRef:
    owner: object
    serial: int

    def __deepcopy__(self, memo: dict[int, object]) -> ObjectRef:
        return self


class InterpreterError(Exception):
    pass


class UnsupportedSyntaxError(InterpreterError):
    pass


class BoundaryError(InterpreterError):
    pass


class CapabilityError(InterpreterError):
    pass


class ResourceLimitError(InterpreterError):
    pass


class GuestError(InterpreterError):
    def __init__(
            self,
            name: str,
            message: str,
            exception: ObjectRef,
    ) -> None:
        super().__init__(f'{name}: {message}')

        self.name = name
        self.message = message
        self.exception = exception


class _GuestRaise(Exception):  # noqa: N818
    def __init__(self, value: ObjectRef) -> None:
        super().__init__()

        self.value = value
