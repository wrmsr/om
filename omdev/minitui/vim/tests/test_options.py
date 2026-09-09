import pytest

from ..options import DEFAULT_OPTIONS
from ..options import SetOptionError
from ..options import VimOptions
from ..options import apply_set


##


def test_apply_set_number():
    assert apply_set(DEFAULT_OPTIONS, 'number').number is True
    assert apply_set(DEFAULT_OPTIONS, 'nu').number is True
    assert apply_set(VimOptions(number=True), 'nonumber').number is False
    assert apply_set(VimOptions(number=True), 'nonu').number is False
    assert apply_set(DEFAULT_OPTIONS, 'nu!').number is True
    assert apply_set(VimOptions(number=True), 'nu!').number is False
    assert apply_set(DEFAULT_OPTIONS, 'invnumber').number is True
    assert apply_set(VimOptions(number=True), 'invnu').number is False
    assert apply_set(DEFAULT_OPTIONS, '  nu  ').number is True


def test_apply_set_preserves_other_fields():
    opts = VimOptions(tabstop=8, shiftwidth=2, expandtab=False, numberwidth=1)
    new = apply_set(opts, 'nu')
    assert new == VimOptions(tabstop=8, shiftwidth=2, expandtab=False, number=True, numberwidth=1)
    assert opts.number is False  # frozen: the input is untouched


def test_apply_set_rejects_unknown():
    with pytest.raises(SetOptionError, match='Unknown option: foo'):
        apply_set(DEFAULT_OPTIONS, 'foo')
    with pytest.raises(SetOptionError, match='Unknown option: nofoo!'):
        apply_set(DEFAULT_OPTIONS, 'nofoo!')
    with pytest.raises(SetOptionError, match='Unknown option: no'):
        apply_set(DEFAULT_OPTIONS, 'no')
    with pytest.raises(SetOptionError, match='Argument required'):
        apply_set(DEFAULT_OPTIONS, '')
