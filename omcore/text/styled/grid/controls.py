"""
Visible stand-ins for control characters, which a grid cannot lay out and a terminal would act on rather than show.
"""
import typing as ta

from ..text import StyledText
from ..text import StyledTextLike


##


def _build_control_pictures() -> dict[int, str]:
    # C0 controls and DEL have unicode control pictures. The C1 controls have none, but some terminals act on them too.
    pictures = {c: chr(0x2400 + c) for c in range(0x20) if c != 0x09}
    pictures[0x7f] = '␡'
    pictures.update({c: '�' for c in range(0x80, 0xa0)})
    return pictures


_CONTROL_PICTURES: ta.Mapping[int, str] = _build_control_pictures()


def show_controls(text: StyledTextLike) -> StyledText:
    """
    Replaces each control character but tab - which `expand_tabs` lays out - with a visible stand-in one cell wide: its
    unicode control picture, or a replacement character for the C1 controls. Styled spans stay where they were.
    """

    value = StyledText.of(text)
    if (shown := value.text.translate(_CONTROL_PICTURES)) == value.text:
        return value
    return StyledText(shown, value.spans)
