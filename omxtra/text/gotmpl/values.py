import typing as ta


##


@ta.final
class MissingValue:
    """Represents Go's invalid reflect.Value, which is distinct from a typed nil value."""

    __slots__ = ()


MISSING = MissingValue()


def is_missing(value: ta.Any) -> bool:
    return value is MISSING
