import typing as ta


##


def cached_hash(
    fn: ta.Callable[[ta.Any], int],
    *,
    attr: str = '_hash',
) -> ta.Callable[..., int]:
    def __hash__(self) -> int:  # noqa
        try:
            return getattr(self, attr)
        except AttributeError:
            pass

        h = fn(self)

        object.__setattr__(self, attr, h)
        return h

    return __hash__
