import codecs
import typing as ta


##


class IncrementalTextDecoder:
    """Per-fd incremental decoding so multibyte sequences split across chunks decode correctly."""

    def __init__(self, encoding: str = 'utf-8', errors: str = 'replace') -> None:
        super().__init__()

        self._encoding = encoding
        self._errors = errors
        self._decoders: dict[int, codecs.IncrementalDecoder] = {}

    def decode(self, fd: int, data: bytes, *, final: bool = False) -> str:
        try:
            dec = self._decoders[fd]
        except KeyError:
            dec = self._decoders[fd] = codecs.getincrementaldecoder(self._encoding)(errors=self._errors)
        return dec.decode(data, final)

    def flush(self, fd: int | None = None) -> str:
        if fd is not None:
            if (dec := self._decoders.get(fd)) is None:
                return ''
            return dec.decode(b'', True)
        return ''.join(d.decode(b'', True) for d in self._decoders.values())


def split_keeping_newlines(s: str) -> ta.Iterator[str]:
    """Yields the pieces of `s` split after each newline (the last piece may lack one)."""

    pos = 0
    while pos < len(s):
        i = s.find('\n', pos)
        if i < 0:
            yield s[pos:]
            return
        yield s[pos:i + 1]
        pos = i + 1
