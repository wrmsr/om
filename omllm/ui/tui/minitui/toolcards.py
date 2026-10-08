from omdev import minitui as mt

from .... import agent as agn
from ....core import ui
from ..rendering import render_text_rows


##


_MAX_CALL_SUMMARY_LEN = 160


def tool_card_key(context: agn.ToolContext) -> str:
    if (tool_call := context.llm_tool_call) is not None:
        return tool_call.id
    return f'context:{id(context):x}'


def tool_call_summary(context: agn.ToolContext) -> str | None:
    if (tool := context.tool) is None or (summarizer := tool.summarizer) is None:
        return None

    try:
        summary = summarizer(context)
    except Exception:  # noqa: BLE001
        # FIXME: display error lol
        return None

    if summary is None:
        return None

    # The summary rides a single header row, so only its characters survive - styling and blocks have nowhere to go.
    if not (summary := ' '.join(ui.Text.str_of(summary).split())):
        return None

    if len(summary) > _MAX_CALL_SUMMARY_LEN:
        summary = summary[:_MAX_CALL_SUMMARY_LEN - 3] + '...'

    return summary


def card_text_rows(text: ui.CanText, width: int) -> list[list[mt.Segment]]:
    """
    UI text as card detail rows, laid out for the width beside the card's detail indent so the card never re-wraps it -
    fixed-width layouts like a rendered diff stay intact.
    """

    rows = render_text_rows(
        ui.StyledTextRenderer().render(text),
        max(width - mt.CARD_DETAIL_INDENT, 1),
    )

    # Text ending in a newline leaves the cursor on a fresh, empty row, which is not a row of the text.
    if rows and not rows[-1]:
        rows.pop()

    return rows
