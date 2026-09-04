import abc
import typing as ta

from omcore import lang

from .messages import Message


##


class TurnInbox(lang.Abstract):
    """
    Messages which arrive while a run is in progress, held until the loop can take them.

    Steering is taken at the start of every turn - in practice, once the current tool batch has finished, or straight
    away if a run is only just starting. Follow-ups are taken only when the model would otherwise have ended the run,
    and extend it. Whatever is left when a run ends any other way waits for the next one.
    """

    @abc.abstractmethod
    def has_steering(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def take_steering(self) -> ta.Sequence[Message]:
        raise NotImplementedError

    @abc.abstractmethod
    def take_follow_ups(self) -> ta.Sequence[Message]:
        raise NotImplementedError
