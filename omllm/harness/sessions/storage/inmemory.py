from ..entries import SessionEntry
from .types import SessionStorage


##


class InMemorySessionStorage(SessionStorage):
    def __init__(self) -> None:
        super().__init__()

        self._entries: list[SessionEntry] = []

    async def add_entry(self, *entries: SessionEntry) -> None:
        if not entries:
            return

        self._entries.extend(entries)
