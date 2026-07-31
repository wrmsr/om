import pytest

from ..clsdct import cls_dct_fn
from ..clsdct import get_caller_cls_dct
from ..clsdct import is_possibly_cls_dct


@cls_dct_fn()
def _install(cls_dct, name, value):
    cls_dct[name] = value


def _install_from_caller(name, value):
    get_caller_cls_dct()[name] = value


def test_class_dictionary_helpers():
    class Foo:
        _install('first', 1)
        _install_from_caller('second', 2)

    assert getattr(Foo, 'first') == 1
    assert getattr(Foo, 'second') == 2

    explicit = {
        '__module__': __name__,
        '__qualname__': 'Explicit',
    }
    assert is_possibly_cls_dct(explicit)
    _install('value', 3, cls_dct=explicit)
    assert explicit['value'] == 3


def test_class_dictionary_helpers_reject_regular_mappings():
    with pytest.raises(TypeError):
        _install('value', 1)
    with pytest.raises(TypeError):
        _install('value', 1, cls_dct={})
