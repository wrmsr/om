import asyncio

from ....core import ui


##


class RecordingTextDisplayer(ui.TextDisplayer):
    def __init__(self):
        super().__init__()

        self.lines = []
        self.displayed = asyncio.Event()

    async def display_text(self, *texts):
        self.lines.append(ui.Text.str_of(list(texts)))
        self.displayed.set()
