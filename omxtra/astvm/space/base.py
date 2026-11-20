import typing as ta

from ..budget import Budget
from ..capabilities import Capabilities
from ..runtime import Runtime
from ..values import ObjectRef
from ..values import Value


NativeResultT = ta.TypeVar('NativeResultT')


##


class SpaceBase:
    runtime: Runtime
    budget: Budget
    capabilities: Capabilities
    types: dict[str, ObjectRef]
    builtins: ObjectRef
    _scalar_identities: dict[int, tuple[Value, int]]
    _host_objects: ObjectRef

    _BINARY: ta.ClassVar[dict[str, ta.Callable[..., ta.Any]]]
    _ORDER: ta.ClassVar[dict[str, ta.Callable[..., ta.Any]]]
    _METHODS: ta.ClassVar[dict[str, frozenset[str]]]

    if ta.TYPE_CHECKING:
        def data(self, value: Value) -> ta.Any:
            ...

        def error(self, name: str, *args: Value) -> ta.NoReturn:
            ...

        def exception_name(self, ref: ObjectRef) -> str:
            ...

        def import_value(
                self,
                value: object,
                *,
                capabilities: bool = False,
                memo: dict[int, Value] | None = None,
                depth: int = 0,
        ) -> Value:
            ...

        def index(self, value: Value) -> int:
            ...

        def key(self, value: Value, depth: int = 0) -> object:
            ...

        def kind(self, value: Value) -> str:
            ...

        def length(self, value: Value) -> int:
            ...

        def lookup_class(self, cls: ObjectRef, name: str) -> Value:
            ...

        def make_dict(self, pairs: ta.Iterable[tuple[Value, Value]]) -> ObjectRef:
            ...

        def mapping_pairs(self, value: Value) -> list[tuple[Value, Value]]:
            ...

        def native(
                self,
                function: ta.Callable[..., NativeResultT],
                *args: object,
                **kwargs: object,
        ) -> NativeResultT:
            ...

        def new(self, kind: str, data: ta.Any) -> ObjectRef:
            ...

        def set_item(
                self,
                value: Value,
                key: Value,
                item: Value,
                *,
                delete: bool = False,
        ) -> None:
            ...

        def traceback_value(self, value: ObjectRef) -> Value:
            ...
