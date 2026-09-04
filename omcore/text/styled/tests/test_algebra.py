import pytest

from ..colors import RgbColor
from ..colors import blend_rgb
from ..styles import DEFAULT_COLOR
from ..styles import ResolvedStyle
from ..styles import StyleName
from ..styles import StylePatch
from ..text import StyledText
from ..text import StyleSpan


BOLD = StylePatch(bold=True)
ITALIC = StylePatch(italic=True)


##


def test_to_patch_is_complete():
    style = ResolvedStyle(fg=RgbColor(1, 2, 3), bold=True)
    patch = style.to_patch()

    assert patch.fg == RgbColor(1, 2, 3)
    assert patch.bg is DEFAULT_COLOR
    assert patch.bold is True
    assert patch.italic is False
    assert patch.resolve(ResolvedStyle(bg=RgbColor(9, 9, 9), italic=True, bold=False)) == style
    assert ResolvedStyle().to_patch().resolve(style) == ResolvedStyle()

    assert patch.is_complete
    assert ResolvedStyle().to_patch().is_complete
    assert not StylePatch(bold=True).is_complete
    assert not StylePatch().is_complete


def test_blend_rgb():
    assert blend_rgb(RgbColor(0, 0, 0), RgbColor(100, 200, 50), .5) == RgbColor(50, 100, 25)
    assert blend_rgb(RgbColor(0, 0, 0), RgbColor(100, 200, 50), 0) == RgbColor(0, 0, 0)
    assert blend_rgb(RgbColor(0, 0, 0), RgbColor(100, 200, 50), 1) == RgbColor(100, 200, 50)

    with pytest.raises(ValueError):  # noqa: PT011
        blend_rgb(RgbColor(0, 0, 0), RgbColor(0, 0, 0), 1.5)


##


def test_assemble():
    text = StyledText.assemble(
        'a',
        ('b', BOLD),
        (StyledText('c').styled(ITALIC), 'base'),
        StyledText('d').styled(BOLD),
        ('', BOLD),
        ('e', None),
    )

    assert text.text == 'abcde'
    assert [run.styles for run in text.runs()] == [
        (),
        (BOLD,),
        (StyleName('base'), ITALIC),
        (BOLD,),
        (),
    ]
    assert StyledText.assemble() == StyledText()


def test_strip():
    text = StyledText('  ab  ').styled(BOLD, 1, 5)

    assert text.strip() == StyledText('ab', (StyleSpan(0, 2, BOLD),))
    assert text.lstrip().text == 'ab  '
    assert text.rstrip().text == '  ab'
    assert StyledText('   ').strip() == StyledText()
    assert StyledText('xax').strip('x') == StyledText('a')


def test_unstyled_and_map_styles():
    text = StyledText('ab', (
        StyleSpan.of(0, 2, 'outer'),
        StyleSpan(1, 2, BOLD),
    ))

    assert text.unstyled() == StyledText('ab')

    renamed = text.map_styles(lambda s: 'inner' if s == StyleName('outer') else None)
    assert renamed == StyledText('ab', (StyleSpan.of(0, 2, 'inner'),))

    assert text.map_styles(lambda s: s) == text


def test_style_at():
    text = StyledText('abc', (
        StyleSpan.of(0, 3, 'outer'),
        StyleSpan(1, 2, BOLD),
    ))

    assert text.style_at(0) == (StyleName('outer'),)
    assert text.style_at(1) == (StyleName('outer'), BOLD)
    assert text.style_at(-1) == (StyleName('outer'),)
    assert StyledText('abc').style_at(2) == ()

    with pytest.raises(IndexError):
        text.style_at(3)
    with pytest.raises(TypeError):
        text.style_at(True)


##


def test_equality_is_structural_but_canonical_forms_compare():
    pieces = StyledText('ab').styled(BOLD, 0, 1).styled(BOLD, 1, 2)
    whole = StyledText('ab').styled(BOLD)

    assert pieces != whole
    assert pieces.canonical() == whole.canonical()
    assert whole.canonical() == StyledText('ab', (StyleSpan(0, 2, BOLD),))


def test_canonical_keeps_last_occurrence_and_order():
    red = StylePatch(fg=RgbColor(255, 0, 0))
    blue = StylePatch(fg=RgbColor(0, 0, 255))

    shadowed = StyledText('a', (StyleSpan(0, 1, red), StyleSpan(0, 1, blue), StyleSpan(0, 1, red)))
    assert shadowed.canonical() == StyledText('a', (StyleSpan(0, 1, blue), StyleSpan(0, 1, red)))
    assert shadowed.canonical().resolved_runs() == shadowed.resolved_runs()

    ordered = StyledText('a', (StyleSpan(0, 1, red), StyleSpan(0, 1, blue)))
    reversed_ = StyledText('a', (StyleSpan(0, 1, blue), StyleSpan(0, 1, red)))
    assert ordered.canonical() != reversed_.canonical()


def test_canonical_merges_runs_equal_after_deduplication_and_is_idempotent():
    # The first character's stack is (ITALIC, BOLD, ITALIC), the second's (BOLD, ITALIC): equal once the shadowed
    # leading ITALIC is dropped, so the two runs merge.
    text = StyledText('ab', (
        StyleSpan(0, 1, ITALIC),
        StyleSpan(0, 2, BOLD),
        StyleSpan(0, 1, ITALIC),
        StyleSpan(1, 2, ITALIC),
    ))
    assert [run.styles for run in text.runs()] == [(ITALIC, BOLD, ITALIC), (BOLD, ITALIC)]

    canonical = text.canonical()
    assert [run.styles for run in canonical.runs()] == [(BOLD, ITALIC)]
    assert canonical == StyledText('ab', (StyleSpan(0, 2, BOLD), StyleSpan(0, 2, ITALIC)))
    assert canonical.canonical() == canonical

    assert StyledText().canonical() == StyledText()
    assert StyledText('x').canonical() == StyledText('x')
