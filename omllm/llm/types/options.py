"""
TODO:
 - *already* want typedvalues?
"""
import enum
import typing as ta

from omcore import dataclasses as dc


##


@ta.final
class CacheRetention(enum.Enum):
    """Exact cache retention policies supported by one or more model providers."""

    IN_MEMORY = enum.auto()
    FIVE_MINUTES = enum.auto()
    THIRTY_MINUTES = enum.auto()
    ONE_HOUR = enum.auto()
    ONE_DAY = enum.auto()


##


@dc.dataclass(frozen=True, kw_only=True)
class Options:
    """All fields must be optional and default to `None`"""

    max_tokens: int | None = None

    thinking: bool | None = None

    # A stable opaque key used to improve matching by providers which support caller-supplied cache keys.
    cache_key: str | None = None

    # An exact requested policy. None preserves the provider default, which may still enable implicit caching.
    # Providers reject unsupported policies rather than approximating their duration.
    cache_retention: CacheRetention | None = None

    #

    @ta.final
    def merge(self, *overrides: Options | None) -> Options:
        kw: dict[str, ta.Any] = {}
        for obj in [self, *overrides]:
            if obj is None:
                continue

            for fld in dc.fields(self):  # noqa
                fv = getattr(obj, fld.name)

                mv = self._merge_field(fld, fv)

                if mv is None:
                    continue

                kw[fld.name] = mv

        if not kw:
            return self
        return Options(**kw)

    def _merge_field(self, fld: dc.Field, value: ta.Any) -> ta.Any:
        return value
