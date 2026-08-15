from ...blocks.leaves import BufferedLine
from ..emphasis import resolve_emphasis
from ..nodes import DelimNode
from ..nodes import EmphasisGroup
from ..nodes import TextNode
from ..tokenize import tokenize_inline


def _resolve(text, *, strikethrough=False):
    nodes = tokenize_inline(
        (BufferedLine(text=text, line_start=0, line_next=len(text) + 1),),
        strikethrough=strikethrough,
    )
    return resolve_emphasis(nodes)


def _summarize(nodes, depth=0):
    """Compact stringification for assertions."""

    out = []
    for n in nodes:
        if isinstance(n, TextNode):
            out.append(repr(n.text))
        elif isinstance(n, EmphasisGroup):
            tag = {'emphasis': 'E', 'strong': 'S', 'strikethrough': 'X'}[n.kind]
            out.append(f'{tag}[{_summarize(n.children, depth + 1)}]')
        elif isinstance(n, DelimNode):
            out.append(f'<UNRESOLVED {n.char * n.count}>')
        else:
            out.append(type(n).__name__)
    return ' '.join(out)


def test_basic_emphasis():
    out = _resolve('*foo*')
    assert _summarize(out) == "E['foo']"


def test_basic_strong():
    out = _resolve('**foo**')
    assert _summarize(out) == "S['foo']"


def test_triple_emphasis_inside_strong():
    out = _resolve('***foo***')
    assert _summarize(out) == "E[S['foo']]"


def test_underscore_emphasis():
    out = _resolve('_foo_')
    assert _summarize(out) == "E['foo']"


def test_intraword_underscore_no_emphasis():
    out = _resolve('foo_bar_baz')
    assert _summarize(out) == "'foo' '_' 'bar' '_' 'baz'"


def test_intraword_asterisk_emphasis():
    out = _resolve('5*6*78')
    assert _summarize(out) == "'5' E['6'] '78'"


def test_adjacent_emphasis_pairs():
    out = _resolve('*foo* *bar*')
    assert _summarize(out) == "E['foo'] ' ' E['bar']"


def test_nested_strong_in_emphasis():
    out = _resolve('*foo **bar** baz*')
    assert _summarize(out) == "E['foo ' S['bar'] ' baz']"


def test_asymmetric_left_loses_to_mod3():
    # `*foo**bar*` - D2 (count=2) doesn't pair with D3 (count=1) due to mod-3 rule; D3 falls through to D1, emphasis
    # wraps everything.
    out = _resolve('*foo**bar*')
    assert _summarize(out) == "E['foo' '**' 'bar']"


def test_unmatched_left_emphasis_is_text():
    out = _resolve('*foo')
    assert _summarize(out) == "'*' 'foo'"


def test_unmatched_right_emphasis_is_text():
    out = _resolve('foo*')
    assert _summarize(out) == "'foo' '*'"


def test_mixed_marker_no_pairing():
    out = _resolve('*foo_')
    # `*` cannot pair with `_`.
    summary = _summarize(out)
    assert 'E[' not in summary and 'S[' not in summary


def test_emphasis_inside_emphasis_same_marker():
    # `*foo *bar* baz*` - inner emphasis nested in outer.
    out = _resolve('*foo *bar* baz*')
    assert _summarize(out) == "E['foo ' E['bar'] ' baz']"


# Strikethrough delimiters (GFM)


def test_strikethrough_basic():
    assert _summarize(_resolve('~~foo~~', strikethrough=True)) == "X['foo']"


def test_strikethrough_single_tilde():
    assert _summarize(_resolve('~foo~', strikethrough=True)) == "X['foo']"


def test_strikethrough_intraword():
    assert _summarize(_resolve('a~~b~~c', strikethrough=True)) == "'a' X['b'] 'c'"


def test_strikethrough_triple_tilde_does_not_pair():
    out = _resolve('~~~foo~~~', strikethrough=True)
    assert 'X[' not in _summarize(out)


def test_tilde_without_option_is_text():
    out = _resolve('~~foo~~')
    assert _summarize(out) == "'~~foo~~'"


# Flanking with non-ASCII characters


def test_nbsp_counts_as_whitespace_for_flanking():
    # U+00A0 is Zs: a delimiter followed by it cannot open.
    out = _resolve('* foo *')
    assert 'E[' not in _summarize(out)


def test_intraword_underscore_unicode_letters():
    out = _resolve('а_б_в')  # Cyrillic letters
    assert 'E[' not in _summarize(out)


def test_intraword_asterisk_unicode_letters():
    out = _resolve('а*б*в')
    assert _summarize(out) == "'а' E['б'] 'в'"


def test_unicode_punctuation_flanking():
    # « (Pi) is unicode punctuation: `*` after it and before a letter is left-flanking.
    assert _summarize(_resolve('«*foo*»')) == "'«' E['foo'] '»'"
