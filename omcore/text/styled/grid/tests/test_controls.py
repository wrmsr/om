from ...text import StyledText
from ..controls import show_controls
from ..measuring import cell_width


##


def test_controls_become_one_cell_pictures():
    shown = show_controls('a\x1b[31mb\rc\x7fd\x9be\tf')

    assert shown.text == 'a␛[31mb␍c␡d�e\tf'
    assert cell_width(shown) == len(shown.text)


def test_spans_stay_put_and_plain_text_is_untouched():
    styled = StyledText.assemble(('x\x1by', 'red'), ('z', 'blue'))

    shown = show_controls(styled)
    assert shown.text == 'x␛yz'
    assert shown.spans == styled.spans

    plain = StyledText.assemble(('xyz', 'red'))
    assert show_controls(plain) is plain
