"""Input history: prev/next navigation with the in-progress draft stashed at the bottom."""
import typing as ta


##


class InputHistory:
    def __init__(self, entries: ta.Iterable[str] = ()) -> None:
        super().__init__()

        self._entries: list[str] = list(entries)
        self._pos: int | None = None
        self._draft = ''

    @property
    def entries(self) -> ta.Sequence[str]:
        return tuple(self._entries)

    def add(self, text: str) -> None:
        if text and (not self._entries or self._entries[-1] != text):
            self._entries.append(text)
        self.reset()

    def reset(self) -> None:
        self._pos = None
        self._draft = ''

    def previous(self, current: str) -> str | None:
        """Step back in history; stashes `current` as the draft on first step. None at the oldest entry."""

        if not self._entries:
            return None
        if self._pos is None:
            self._draft = current
            self._pos = len(self._entries) - 1
        elif self._pos > 0:
            self._pos -= 1
        else:
            return None
        return self._entries[self._pos]

    def next(self, current: str) -> str | None:  # noqa
        """Step forward; returns the stashed draft when walking off the newest entry. None when not navigating."""

        if self._pos is None:
            return None
        if self._pos < len(self._entries) - 1:
            self._pos += 1
            return self._entries[self._pos]
        self._pos = None
        draft = self._draft
        self._draft = ''
        return draft
