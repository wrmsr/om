"""
What a pattern is matched against, as the binding needs it - bytes, and offsets into them - and as `re` reports it.

For a bytes pattern the two are the same thing. For a str pattern the subject is matched as its UTF-8, so each offset
that is asked for has to be translated between the two, which for anything but ASCII means counting characters.
"""
import bisect
import sys
import typing as ta

from .... import lang


##


# A UTF-8 character is one byte which is not one of these and then any number which are.
_CONTINUATION_BYTES = bytes(range(0x80, 0xC0))


class Utf8Offsets(lang.Final):
    """
    Translates offsets into valid UTF-8 to offsets into the str it encodes.

    Offsets are mostly asked for in order, as a search works its way through a subject, so each is counted from the
    nearest one already known rather than from the start. The translations kept are only ever a help: finding one that
    is of no use, as can happen when threads add to them at once, costs time and not correctness.
    """

    def __init__(self, data: bytes) -> None:
        super().__init__()

        self._data = data
        self._known: list[tuple[int, int]] = [(0, 0)]

    def to_char(self, byte_offset: int) -> int:
        known = self._known
        i = bisect.bisect_right(known, (byte_offset, sys.maxsize)) - 1
        base_byte, base_char = known[i] if i >= 0 else (0, 0)
        if base_byte > byte_offset:
            base_byte, base_char = 0, 0
        if base_byte == byte_offset:
            return base_char

        char_offset = base_char + len(self._data[base_byte:byte_offset].translate(None, _CONTINUATION_BYTES))
        known.insert(i + 1, (byte_offset, char_offset))
        return char_offset


class Subject(lang.Final):
    def __init__(self, string: ta.Any, *, is_str: bool) -> None:
        super().__init__()

        self._string = string
        self._is_str = is_str

        self._data: ta.Any
        self._offsets: Utf8Offsets | None = None
        if is_str:
            if not isinstance(string, str):
                raise TypeError('cannot use a string pattern on a bytes-like object')
            self._data = string.encode()
            if len(self._data) != len(string):
                self._offsets = Utf8Offsets(self._data)
        else:
            if isinstance(string, str):
                raise TypeError('cannot use a bytes pattern on a string-like object')
            self._data = string

    @property
    def string(self) -> ta.Any:
        return self._string

    @property
    def data(self) -> ta.Any:
        """What is handed to the binding: the bytes of a str, and otherwise whatever buffer the subject is."""

        return self._data

    def __len__(self) -> int:
        return len(self._string)

    def to_byte(self, offset: int) -> int:
        if self._offsets is None:
            return offset
        return len(self._string[:offset].encode())

    def to_offset(self, byte_offset: int) -> int:
        if self._offsets is None:
            return byte_offset
        return self._offsets.to_char(byte_offset)

    def slice(self, byte_start: int, byte_end: int) -> ta.Any:
        if not self._is_str:
            return bytes(self._data[byte_start:byte_end])
        if self._offsets is None:
            # All ASCII, so the same offsets serve for the str itself.
            return self._string[byte_start:byte_end]
        return self._data[byte_start:byte_end].decode()
