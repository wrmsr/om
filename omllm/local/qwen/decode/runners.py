import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .generation import Generated
from .observers import Observer
from .terminators import Terminator


##


@dc.dataclass(frozen=True)
class GenerationParams:
    """
    One generation request: the prompt ids and what this request alone decides -- sampling, penalties, when to stop, a
    grammar, who is watching. What the server decides once (the model, speculation, the store, decode capacity) is not
    here. Seeded into the injector's generation scope (decode/inject.py) or handed to a hand-assembled runner (api.py).
    """

    prompt: ta.Sequence[int]
    max_new_tokens: int = 64

    temperature: float = 0.
    top_k: int = 0
    top_p: float = 1.
    min_p: float = 0.
    seed: int = 0

    presence_penalty: float = 0.
    frequency_penalty: float = 0.

    eos_ids: ta.AbstractSet[int] = frozenset()
    constraint: ta.Any = None  # a constrain.grammar ToolConstraint / JsonConstraint

    on_token: ta.Callable[[int], None] | None = None
    should_stop: ta.Callable[[], bool] | None = None
    terminators: ta.Sequence[Terminator] = ()  # this request's own (stop strings)
    observers: ta.Sequence[Observer] = ()


class GenerationRunner(lang.Abstract):
    """Runs one generation per call. What the serving engine depends on, however the generation is assembled."""

    @abc.abstractmethod
    def run(self, params: GenerationParams) -> Generated:
        raise NotImplementedError
