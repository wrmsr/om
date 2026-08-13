from .. import sexp as sx


def test_render():
    assert sx.render('hi') == 'hi'
    assert sx.render(['hi', ['there']]) == '(hi (there))'
