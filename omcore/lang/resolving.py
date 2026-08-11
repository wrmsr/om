import importlib
import string
import typing as ta


##


class ResolvableClassNameError(NameError):
    pass


@ta.overload
def get_cls_fqcn(
    cls: type,
    *,
    nocheck: bool = False,
    optional: ta.Literal[True],
) -> str | None: ...


@ta.overload
def get_cls_fqcn(
    cls: type,
    *,
    nocheck: bool = False,
    optional: ta.Literal[False] = False,
) -> str: ...


def get_cls_fqcn(
    cls,
    *,
    nocheck=False,
    optional=False,
):
    if not isinstance(cls, type):
        raise TypeError(cls)

    try:
        mn = cls.__module__
    except AttributeError:
        if optional:
            return None
        raise
    if set(mn) - set(string.ascii_lowercase + string.digits + '_.'):
        if optional:
            return None
        raise ResolvableClassNameError(cls)

    try:
        qn = cls.__qualname__
    except AttributeError:
        if optional:
            return None
        raise
    if (
            not all(qp[0].isupper() for qp in qn.split('.')) or
            (set(qn) - set(string.ascii_letters + string.digits + '.'))
    ):
        if optional:
            return None
        raise ResolvableClassNameError(cls)

    fqcn = '.'.join([mn, qn])
    if not nocheck:
        checked = get_fqcn_cls(  # noqa
            fqcn,
            nocheck=True,
            optional=optional,
        )
        if checked is not cls:
            if optional:
                return None
            raise ResolvableClassNameError(cls, fqcn)

    return fqcn


@ta.overload
def get_fqcn_cls(
    fqcn: str,
    *,
    nocheck: bool = False,
    optional: ta.Literal[True],
) -> type | None: ...


@ta.overload
def get_fqcn_cls(
    fqcn: str,
    *,
    nocheck: bool = False,
    optional: ta.Literal[False] = False,
) -> type: ...


def get_fqcn_cls(
    fqcn,
    *,
    nocheck=False,
    optional=False,
):
    if not isinstance(fqcn, str) or not fqcn:
        raise TypeError(fqcn)

    parts = fqcn.split('.')
    pos = next((i for i, p in enumerate(parts) if p and p[0].isupper()), None)
    if pos is None:
        raise ResolvableClassNameError(fqcn)
    mps, qps = parts[:pos], parts[pos:]
    mod = importlib.import_module('.'.join(mps))

    o: ta.Any = mod
    for qp in qps:
        try:
            o = getattr(o, qp)
        except AttributeError:
            if optional:
                return None
            raise
        if not isinstance(o, type):
            raise TypeError(o)

    cls = o
    if not isinstance(cls, type):
        raise TypeError(cls)

    if not nocheck:
        checked = get_cls_fqcn(  # noqa
            cls,
            nocheck=True,
            optional=optional,
        )
        if optional and checked is None:
            return None
        if checked != fqcn:
            raise ResolvableClassNameError(cls, fqcn)

    return o


class Resolvable:
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        get_cls_fqcn(cls, nocheck=True)
