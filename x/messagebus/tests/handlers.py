import threading

from ..handlers import MessageHandler
from ..types import Message


##


class CollectingHandler(MessageHandler):
    """Collects messages and sets `done` once `expected` have arrived."""

    def __init__(self, expected: int) -> None:
        super().__init__()

        self._expected = expected

        self.received: list[Message] = []
        self.done = threading.Event()

    def handle(self, msg: Message) -> None:
        self.received.append(msg)
        if len(self.received) >= self._expected:
            self.done.set()


class FlakyHandler(CollectingHandler):
    """Raises on the first `failures` attempts, then behaves."""

    def __init__(self, expected: int, *, failures: int) -> None:
        super().__init__(expected)

        self._failures = failures

        self.attempts = 0

    def handle(self, msg: Message) -> None:
        self.attempts += 1
        if self.attempts <= self._failures:
            raise RuntimeError('flaky')
        super().handle(msg)
