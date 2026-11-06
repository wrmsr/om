"""How the web frontend names and summarizes a tool call's card."""
import typing as ta

from omcore.formats.json import all as json

from ... import agent as agn
from .texts import WebText
from .texts import WebTextRenderer


##


def tool_card_key(context: agn.ToolContext) -> str:
    if (tool_call := context.llm_tool_call) is not None:
        return tool_call.id
    return f'context:{id(context):x}'


def tool_call_summary(context: agn.ToolContext, renderer: WebTextRenderer) -> WebText | None:
    if (tool := context.tool) is None or (summarizer := tool.summarizer) is None:
        return None

    try:
        summary = summarizer(context)
    except Exception:  # noqa: BLE001
        # A summary is a nicety: a call whose summarizer fails is still shown, by its name and arguments.
        return None

    if summary is None:
        return None

    return renderer.render(summary)


def clip_json_strs(v: ta.Any, n: int) -> ta.Any:
    """The json value with any string in it longer than n cut short."""

    if isinstance(v, str):
        return v if len(v) <= n else f'{v[:n]}... ({len(v) - n:,} characters not shown)'
    elif isinstance(v, list):
        return [clip_json_strs(c, n) for c in v]
    elif isinstance(v, dict):
        return {k: clip_json_strs(c, n) for k, c in v.items()}
    else:
        return v


def tool_call_args(context: agn.ToolContext, *, max_str_chars: int = 16 * 1024) -> ta.Any:
    """
    The call's arguments as plain json, for display: anything json cannot say is said by its repr, and long strings -
    the contents of a file being written, say - are cut short.
    """

    return clip_json_strs(json.loads(json.dumps(dict(context.args), default=repr)), max_str_chars)
