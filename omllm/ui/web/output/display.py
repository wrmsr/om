from ....core import ui
from ..feed import events as fe
from ..feed.feed import Feed
from ..texts import WebTextRenderer


##


class FeedTextDisplayer(ui.TextDisplayer):
    """The `ui.TextDisplayer`: what is displayed through it - command output, in the main - goes into the feed."""

    def __init__(
            self,
            *,
            feed: Feed,
            renderer: WebTextRenderer,
    ) -> None:
        super().__init__()

        self._feed = feed
        self._renderer = renderer

    async def display_text(self, *texts: ui.CanText) -> None:
        if not (t := ui.Text.of(*texts)):
            return

        self._feed.append(fe.TextFeedEvent(text=self._renderer.render(t)))
