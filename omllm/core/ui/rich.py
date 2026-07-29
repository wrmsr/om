from omdev.tui import rich

from .text import CanText
from .text import ConcatText
from .text import DiffText
from .text import StrText
from .text import StyleText
from .text import Text
from .text import TextStyle


##


def ui_text_to_rich_text(t: CanText) -> rich.Text:
    """Convert Text tree into rich.Text with correct nested style inheritance."""

    root = Text.of(t)
    out = rich.Text()

    def merge_style(
            parent: TextStyle,
            child: TextStyle,
    ) -> TextStyle:
        return TextStyle(
            color=child.color if child.color is not None else parent.color,
            bold=child.bold if child.bold is not None else parent.bold,
            italic=child.italic if child.italic is not None else parent.italic,
        )

    def to_rich_style(s: TextStyle) -> rich.Style | None:
        if (
                s.color is None and
                s.bold is None and
                s.italic is None
        ):
            return None

        return rich.Style(
            color=s.color,
            bold=s.bold,
            italic=s.italic,
        )

    def visit(node: Text, style: TextStyle) -> None:
        if isinstance(node, StrText):
            if node.s:
                out.append(node.s, style=to_rich_style(style))

        elif isinstance(node, ConcatText):
            for c in node.l:
                visit(c, style)

        elif isinstance(node, StyleText):
            new_style = merge_style(style, node.y)
            visit(node.c, new_style)

        elif isinstance(node, DiffText):
            for l in node.diff_lines:
                if not l.endswith('\n'):
                    l += '\n'

                if l.startswith('+'):
                    out.append(l, style=rich.Style(color='green'))
                elif l.startswith('-'):
                    out.append(l, style=rich.Style(color='red'))
                elif l.startswith('@@'):
                    out.append(l, style=rich.Style(color='cyan'))
                else:
                    out.append(l, style=to_rich_style(style))

        else:
            raise TypeError(node)

    visit(root, TextStyle.DEFAULT)

    return out
