import dataclasses as dc
import typing as ta

from .values import ResourceLimitError
from .values import Value


##


@dc.dataclass(frozen=True, slots=True)
class Limits:
    steps: int = 1_000_000
    objects: int = 100_000
    allocation: int = 10_000_000
    container: int = 100_000
    string: int = 1_000_000
    integer_bits: int = 16_384
    call_depth: int = 512
    source_chars: int = 200_000
    ast_nodes: int = 50_000
    ast_depth: int = 100
    conversion_depth: int = 100


class Budget:
    def __init__(self, limits: Limits | None = None) -> None:
        super().__init__()

        self.limits = limits if limits is not None else Limits()
        for field in dc.fields(self.limits):
            value = getattr(self.limits, field.name)
            if type(value) is not int or value <= 0:
                raise ValueError(f'invalid limit: {field.name}')

        self.steps = 0
        self.objects = 0
        self.allocation = 0
        self.exhausted = False

    def fail(self, reason: str) -> ta.NoReturn:
        self.exhausted = True
        raise ResourceLimitError(reason)

    def tick(self, amount: int = 1) -> None:
        self.steps += amount
        if self.exhausted or self.steps > self.limits.steps:
            self.fail('execution budget exhausted')

    def allocate(
            self,
            amount: int = 1,
            *,
            object_count: int = 0,
    ) -> None:
        self.allocation += amount
        self.objects += object_count
        if self.allocation > self.limits.allocation or self.objects > self.limits.objects:
            self.fail('allocation budget exhausted')

    def size(
            self,
            size: int,
            *,
            string: bool = False,
    ) -> None:
        limit = self.limits.string if string else self.limits.container
        if size > limit:
            self.fail('string size limit' if string else 'container size limit')

    def scalar(self, value: Value) -> Value:
        if type(value) is int and value.bit_length() > self.limits.integer_bits:
            self.fail('integer size limit')

        if type(value) in (str, bytes):
            self.size(len(ta.cast('str | bytes', value)), string=True)

        return value


##
# Frontend. Programs and AST nodes are treated as immutable after preparation.
