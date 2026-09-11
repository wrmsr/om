import uuid

from omcore import check
from omcore import typedvalues as tv


##


class UiId(tv.UniqueScalarTypedValue[uuid.UUID], final=True):
    def __post_init__(self) -> None:
        check.isinstance(self.v, uuid.UUID)
