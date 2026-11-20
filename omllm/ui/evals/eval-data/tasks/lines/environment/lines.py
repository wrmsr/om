##


class LineDecoder:
    def __init__(self) -> None:
        super().__init__()

        self._closed = False

    def feed(self, chunk: bytes) -> list[bytes]:
        return [line.rstrip(b'\r') for line in chunk.split(b'\n')[:-1]]

    def finish(self) -> list[bytes]:
        self._closed = True
        return []
