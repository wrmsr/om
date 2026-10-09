import collections

from ..api.messages import Message


##


def message_size(msg: Message) -> int:
    return sum(len(f) for f in msg)


class MessageQueue:
    """
    A FIFO of whole messages, bounded by count and by payload bytes. There is room while both are under their bounds,
    so one admitted message may overshoot the byte bound - and a maximum-sized message can always be admitted into an
    empty queue.
    """

    def __init__(self, *, max_messages: int, max_bytes: int) -> None:
        super().__init__()

        if max_messages < 1 or max_bytes < 1:
            raise ValueError((max_messages, max_bytes))

        self._max_messages = max_messages
        self._max_bytes = max_bytes

        self._q: collections.deque[Message] = collections.deque()
        self._bytes = 0

    def __len__(self) -> int:
        return len(self._q)

    @property
    def bytes(self) -> int:
        return self._bytes

    def has_room(self) -> bool:
        return len(self._q) < self._max_messages and self._bytes < self._max_bytes

    def push(self, msg: Message) -> None:
        self._q.append(msg)
        self._bytes += message_size(msg)

    def pop(self) -> Message:
        msg = self._q.popleft()
        self._bytes -= message_size(msg)
        return msg

    def clear(self) -> None:
        self._q.clear()
        self._bytes = 0
