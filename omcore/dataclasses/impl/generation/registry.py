import typing as ta

from .... import check
from .... import lang
from ..utils import SealableRegistry
from .base import Generator


GeneratorT = ta.TypeVar('GeneratorT', bound=Generator)


##


_GENERATOR_TYPES: SealableRegistry[type[Generator], type[Generator]] = SealableRegistry()


def register_generator_type(g_ty: type[GeneratorT]) -> type[GeneratorT]:
    check.issubclass(g_ty, Generator)
    _GENERATOR_TYPES[g_ty] = g_ty
    return g_ty


@lang.cached_function
def all_generator_types() -> tuple[type[Generator], ...]:
    return tuple(sorted(
        (g for g, _ in _GENERATOR_TYPES.items()),
        key=lambda g_ty: g_ty.__name__,
    ))
