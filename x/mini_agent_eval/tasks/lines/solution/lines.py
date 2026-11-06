##


class LineDecoder:
    def __init__(self) -> None:
        super().__init__()

        self._closed = False
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> list[bytes]:
        if self._closed:
            raise ValueError('decoder is closed')

        self._buffer.extend(chunk)
        lines: list[bytes] = []
        start = 0
        while (end := self._buffer.find(b'\n', start)) >= 0:
            line = bytes(self._buffer[start:end])
            if line.endswith(b'\r'):
                line = line[:-1]
            lines.append(line)
            start = end + 1

        if start:
            del self._buffer[:start]
        return lines

    def finish(self) -> list[bytes]:
        if self._closed:
            return []
        self._closed = True
        tail = bytes(self._buffer)
        self._buffer.clear()
        return [tail] if tail else []
