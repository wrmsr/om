from .... import agent as agn
from ....core import ui


##


class ShownPreviews:
    """
    The permission previews already on screen, by the tool call that asked. Everything bare shows is scrollback, so a
    result displaying the very text its ask just showed would only repeat what is right above it.
    """

    def __init__(self) -> None:
        super().__init__()

        self._texts: dict[str, ui.Text] = {}

    @staticmethod
    def _key(context: agn.ToolContext | None) -> str | None:
        if context is None or (tool_call := context.llm_tool_call) is None:
            return None
        return tool_call.id

    def add(self, context: agn.ToolContext | None, text: ui.Text) -> None:
        if (key := self._key(context)) is not None:
            self._texts[key] = text

    def pop(self, context: agn.ToolContext) -> ui.Text | None:
        if (key := self._key(context)) is None:
            return None
        return self._texts.pop(key, None)
