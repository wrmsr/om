import typing as ta

from ..types.inboxes import TurnInbox
from ..types.messages import Message


##


class ListTurnInbox(TurnInbox):
    """Plain in-memory queues, filled from the agent's side and drained from the loop's."""

    def __init__(self) -> None:
        super().__init__()

        self._steering: list[Message] = []
        self._follow_ups: list[Message] = []

    #

    def add_steering(self, *messages: Message) -> None:
        self._steering.extend(messages)

    def add_follow_ups(self, *messages: Message) -> None:
        self._follow_ups.extend(messages)

    #

    def has_steering(self) -> bool:
        return bool(self._steering)

    def take_steering(self) -> ta.Sequence[Message]:
        out = tuple(self._steering)
        self._steering.clear()
        return out

    def take_follow_ups(self) -> ta.Sequence[Message]:
        out = tuple(self._follow_ups)
        self._follow_ups.clear()
        return out
