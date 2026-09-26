import typing as ta

from .records import LsmRecord


##


class Memtable:
    def __init__(self) -> None:
        super().__init__()

        self._entries: dict[bytes, bytes | None] = {}
        self._size = 0

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def size(self) -> int:
        """Approximate bytes of keys and values held."""

        return self._size

    def set(self, key: bytes, value: bytes | None) -> None:
        if key in self._entries:
            old = self._entries[key]
            self._size -= len(key) + (len(old) if old is not None else 0)
        self._entries[key] = value
        self._size += len(key) + (len(value) if value is not None else 0)

    def get(self, key: bytes) -> LsmRecord | None:
        if key not in self._entries:
            return None
        return LsmRecord(key, self._entries[key])

    def records(self, start: bytes | None = None, end: bytes | None = None) -> list[LsmRecord]:
        """A sorted snapshot, including tombstones, with start <= key < end."""

        return [
            LsmRecord(k, self._entries[k])
            for k in sorted(self._entries)
            if (start is None or k >= start) and (end is None or k < end)
        ]

    def clear(self) -> None:
        self._entries.clear()
        self._size = 0


async def iter_records(records: ta.Iterable[LsmRecord]) -> ta.AsyncIterator[LsmRecord]:
    for r in records:
        yield r
