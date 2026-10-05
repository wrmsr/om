import abc

from omcore import lang

from .types import Message


##


class MessageHandler(lang.Abstract):
    """
    Called on the bus loop thread, so a slow handler delays polling, flushing, and heartbeats alike. Hand off to an
    executor if that matters; either way keep the stale-heartbeat threshold well above the slowest handler.
    """

    @abc.abstractmethod
    def handle(self, msg: Message) -> None:
        raise NotImplementedError
