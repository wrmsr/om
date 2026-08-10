import builtins
import copy
import dataclasses as dc
import sys
import typing as ta

from .._internals import STD_ATOMIC_TYPES
from .._internals import std_is_dataclass_instance


##


_DICT_TYPES: tuple[type, ...] = (
    dict,
    *([getattr(builtins, 'frozendict')] if sys.version_info >= (3, 15) else []),
)


def asdict(obj, *, dict_factory=dict):  # noqa
    if not std_is_dataclass_instance(obj):  # noqa
        raise TypeError('asdict() should be called on dataclass instances')
    return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj: ta.Any, dict_factory: ta.Any) -> ta.Any:
    if type(obj) in STD_ATOMIC_TYPES:
        return obj

    elif std_is_dataclass_instance(obj):
        l = []
        for f in dc.fields(obj):
            value = _asdict_inner(getattr(obj, f.name), dict_factory)
            l.append((f.name, value))
        return dict_factory(l)

    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])

    elif isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_inner(v, dict_factory) for v in obj)

    elif isinstance(obj, _DICT_TYPES):
        if hasattr(type(obj), 'default_factory'):
            d = type(obj)(getattr(obj, 'default_factory'))  # type: ignore
            for k, v in obj.items():  # type: ignore
                d[_asdict_inner(k, dict_factory)] = _asdict_inner(v, dict_factory)  # type: ignore
            return d
        return type(obj)((_asdict_inner(k, dict_factory), _asdict_inner(v, dict_factory)) for k, v in obj.items())  # type: ignore  # noqa

    else:
        return copy.deepcopy(obj)


def astuple(obj, *, tuple_factory=tuple):  # noqa
    if not std_is_dataclass_instance(obj):
        raise TypeError('astuple() should be called on dataclass instances')
    return _astuple_inner(obj, tuple_factory)


def _astuple_inner(obj: ta.Any, tuple_factory: ta.Any) -> ta.Any:
    if type(obj) in STD_ATOMIC_TYPES:
        return obj

    elif std_is_dataclass_instance(obj):
        l = []
        for f in dc.fields(obj):
            value = _astuple_inner(getattr(obj, f.name), tuple_factory)
            l.append(value)
        return tuple_factory(l)

    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_astuple_inner(v, tuple_factory) for v in obj])

    elif isinstance(obj, (list, tuple)):
        return type(obj)(_astuple_inner(v, tuple_factory) for v in obj)

    elif isinstance(obj, _DICT_TYPES):
        obj_type = type(obj)
        if hasattr(obj_type, 'default_factory'):
            d = obj_type(getattr(obj, 'default_factory'))  # type: ignore
            for k, v in obj.items():  # type: ignore
                d[_astuple_inner(k, tuple_factory)] = _astuple_inner(v, tuple_factory)  # type: ignore
            return d
        return obj_type((_astuple_inner(k, tuple_factory), _astuple_inner(v, tuple_factory)) for k, v in obj.items())  # type: ignore  # noqa

    else:
        return copy.deepcopy(obj)
