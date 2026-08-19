from ..seatbelt import _sx_render


def test_render():
    assert _sx_render('hi') == 'hi'
    assert _sx_render(['hi', ['there']]) == '(hi (there))'
