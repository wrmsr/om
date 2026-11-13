"""
The generation scope: one opening per request, seeded with its GenerationParams, holding everything a generation is
made of -- the Generation state, the Sampler, the logit processors, the token source and its draft source, the
terminators, the observers, the loop. ScopedGenerationRunner is the seam between the engine and the injector: the
engine depends on GenerationRunner and never sees the injector.

Logit processors, terminators and observers are unordered item sets (their contracts make order irrelevant: decode/
processors.py, terminators.py, observers.py); other packages contribute items. The draft source is a wrapper chain
whose order is meaning: the composition root (inject/) builds it and binds DraftSource to its top.
"""
import contextvars
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang

from ..core.model import Qwen35
from ..ops.base import Ops
from .drafts import DraftSource
from .generation import Generated
from .generation import Generation
from .loop import GenerationLoop
from .observers import CompositeObserver
from .observers import Observer
from .observers import TokenCallbackObserver
from .processors import CompositeLogitProcessor
from .processors import LogitProcessor
from .processors import NullLogitProcessor
from .processors import PenaltyProcessor
from .runners import GenerationParams
from .runners import GenerationRunner
from .sampling import Sampler
from .terminators import BudgetTerminator
from .terminators import CallbackTerminator
from .terminators import CompositeTerminator
from .terminators import EosTerminator
from .terminators import Terminator
from .tokens import TokenSource
from .tokens import VerifyTokenSource


##


@dc.dataclass(frozen=True)
class DecodeConfig:
    """
    Decode choices. `capacity` pins the decode buffers (and so the captured / compiled steps) to the longest context
    served; a request that needs more grows them (0: every generation gets just what it needs). `static` False decodes
    with the functional reference decoder (plain decode only: drafts need the static one). `prefill_checkpoints`:
    states kept from inside each prefill for the state store, at most (VerifyTokenSource); 0 without a store.
    """

    capacity: int = 32768
    prefill_chunk: int = 4096
    static: bool = True
    prefill_checkpoints: int = 0


class GENERATION_SCOPED(lang.Marker):  # noqa
    pass


_GENERATION_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._GENERATION_SCOPE_CONTEXT')

GENERATION_SCOPE: ta.Final = inj.DelimitedScope(
    GENERATION_SCOPED,
    context=inj.ContextVarScopeContext(_GENERATION_SCOPE_CONTEXT),
)


LogitProcessors = ta.NewType('LogitProcessors', ta.Sequence[LogitProcessor])
Terminators = ta.NewType('Terminators', ta.Sequence[Terminator])
Observers = ta.NewType('Observers', ta.Sequence[Observer])


@lang.cached_function
def logit_processors() -> inj.ItemsBinderHelper[LogitProcessor]:
    return inj.items_binder_helper[LogitProcessor](LogitProcessors)


@lang.cached_function
def terminators() -> inj.ItemsBinderHelper[Terminator]:
    return inj.items_binder_helper[Terminator](Terminators)


@lang.cached_function
def observers() -> inj.ItemsBinderHelper[Observer]:
    return inj.items_binder_helper[Observer](Observers)


##


class ScopedGenerationRunner(GenerationRunner):
    """Each generation in its own opening of the generation scope, seeded with the request."""

    def __init__(self, *, injector: inj.Injector) -> None:
        super().__init__()

        self._injector = injector

    def run(self, params: GenerationParams) -> Generated:
        with inj.enter_scope(
                self._injector,
                GENERATION_SCOPE,
                {
                    inj.as_key(GenerationParams): params,
                },
        ):
            loop = self._injector[GenerationLoop]
            return loop.run(self._injector[Generation])


def _generation(params: GenerationParams, config: DecodeConfig, draft: DraftSource) -> Generation:
    capacity = max(config.capacity, len(params.prompt) + params.max_new_tokens + draft.max_drafts + 2)
    return Generation(prompt=params.prompt, capacity=capacity)


def _sampler(params: GenerationParams, ops: Ops) -> Sampler:
    sampler = Sampler(
        temperature=params.temperature,
        top_k=params.top_k,
        top_p=params.top_p,
        min_p=params.min_p,
        seed=params.seed,
    )
    sampler.bind(ops)
    return sampler


def _penalties(params: GenerationParams, ops: Ops, model: Qwen35) -> LogitProcessor:
    if not (params.presence_penalty or params.frequency_penalty):
        return NullLogitProcessor()
    return PenaltyProcessor(
        ops,
        vocab_size=model.cfg.vocab_size,
        presence=params.presence_penalty,
        frequency=params.frequency_penalty,
    )


def _processor(ops: Ops, items: LogitProcessors) -> LogitProcessor:
    return CompositeLogitProcessor(ops, [p for p in items if not isinstance(p, NullLogitProcessor)])


def _budget(params: GenerationParams) -> Terminator:
    return BudgetTerminator(params.max_new_tokens)


def _eos(params: GenerationParams) -> Terminator:
    return EosTerminator(params.eos_ids)


def _cancel(params: GenerationParams) -> Terminator:
    should_stop = params.should_stop
    return CallbackTerminator(should_stop if should_stop is not None else lambda: False)


def _request_terminators(params: GenerationParams) -> Terminator:
    return CompositeTerminator(params.terminators)


def _terminator(items: Terminators) -> Terminator:
    return CompositeTerminator(items)


def _request_observers(params: GenerationParams) -> Observer:
    obs = list(params.observers)
    if params.on_token is not None:
        obs.append(TokenCallbackObserver(params.on_token))
    return CompositeObserver(obs)


def _observer(items: Observers) -> Observer:
    return CompositeObserver(items)


def _token_source(
        model: Qwen35,
        sampler: Sampler,
        processor: LogitProcessor,
        draft: DraftSource,
        config: DecodeConfig,
) -> TokenSource:
    return VerifyTokenSource(
        model=model,
        sampler=sampler,
        processor=processor,
        draft=draft,
        static=config.static or bool(draft.max_drafts),
        prefill_chunk=config.prefill_chunk,
        prefill_checkpoints=config.prefill_checkpoints,
    )


def bind_decode(config: DecodeConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        inj.bind(DecodeConfig, to_const=config),

        inj.bind_scope(GENERATION_SCOPE),
        inj.bind_scope_seed(GenerationParams, GENERATION_SCOPE),

        inj.bind(ScopedGenerationRunner, singleton=True),
        inj.bind(GenerationRunner, to_key=ScopedGenerationRunner),
    ])

    #

    lst.extend([
        inj.bind(Generation, to_fn=_generation, in_=GENERATION_SCOPE),
        inj.bind(Sampler, to_fn=_sampler, in_=GENERATION_SCOPE),

        logit_processors().bind_items_provider(in_=GENERATION_SCOPE),
        logit_processors().bind_item(to_fn=_penalties, in_=GENERATION_SCOPE),
        inj.bind(LogitProcessor, to_fn=_processor, in_=GENERATION_SCOPE),

        terminators().bind_items_provider(in_=GENERATION_SCOPE),
        terminators().bind_item(to_fn=_budget, in_=GENERATION_SCOPE),
        terminators().bind_item(to_fn=_eos, in_=GENERATION_SCOPE),
        terminators().bind_item(to_fn=_cancel, in_=GENERATION_SCOPE),
        terminators().bind_item(to_fn=_request_terminators, in_=GENERATION_SCOPE),
        inj.bind(Terminator, to_fn=_terminator, in_=GENERATION_SCOPE),

        observers().bind_items_provider(in_=GENERATION_SCOPE),
        observers().bind_item(to_fn=_request_observers, in_=GENERATION_SCOPE),
        inj.bind(Observer, to_fn=_observer, in_=GENERATION_SCOPE),

        inj.bind(TokenSource, to_fn=_token_source, in_=GENERATION_SCOPE),
        inj.bind(GenerationLoop, in_=GENERATION_SCOPE),
    ])

    #

    return inj.as_elements(*lst)
