"""
`generate`: a generation assembled by hand from the pieces, for scripts, tests and the CLIs -- what the injector
bindings (inject/) assemble for the server. The only module besides the bindings that names every implementation.
"""
import typing as ta

from .constrain.grammar import JsonConstraint
from .constrain.grammar import ToolConstraint
from .constrain.processors import GrammarProcessor
from .core.model import Qwen35
from .decode.drafts import DraftSource
from .decode.drafts import NullDraftSource
from .decode.generation import Generated
from .decode.generation import Generation
from .decode.loop import GenerationLoop
from .decode.observers import CompositeObserver
from .decode.observers import Observer
from .decode.observers import TokenCallbackObserver
from .decode.processors import CompositeLogitProcessor
from .decode.processors import LogitProcessor
from .decode.processors import PenaltyProcessor
from .decode.runners import GenerationParams
from .decode.runners import GenerationRunner
from .decode.sampling import Sampler
from .decode.stores import NullStateStore
from .decode.stores import StateStore
from .decode.terminators import BudgetTerminator
from .decode.terminators import CallbackTerminator
from .decode.terminators import CompositeTerminator
from .decode.terminators import EosTerminator
from .decode.terminators import Terminator
from .decode.tokens import VerifyTokenSource
from .prefix.cache import PrefixCache
from .prefix.store import PrefixStateStore
from .spec.lookup import LookupDraftSource
from .spec.mtp import MtpDraftSource


##


def generation_capacity(
        prompt_len: int,
        max_new_tokens: int,
        spec: int,
        capacity: int | None = None,
) -> int:
    """Decode buffer length: `capacity` when it suffices (pinned, captured / compiled steps are reused), else enough."""

    return max(capacity or 0, prompt_len + max_new_tokens + spec + 2)


def generate(
        model: Qwen35,
        prompt_ids: ta.Sequence[int],
        *,
        max_new_tokens: int = 64,
        eos_ids: ta.Iterable[int] | None = None,
        on_token: ta.Callable[[int], None] | None = None,
        static: bool = True,
        sampler: Sampler | None = None,
        presence_penalty: float = 0.,
        frequency_penalty: float = 0.,
        spec: int = 0,
        capacity: int | None = None,
        draft_vocab: int = 0,
        lookup_ngram: int = 0,
        lookup_k: int = 3,
        draft: DraftSource | None = None,
        prefix_cache: PrefixCache | None = None,
        constraint: ToolConstraint | JsonConstraint | None = None,
        prefill_chunk: int = 4096,
        prefill_checkpoints: int = 0,
        step_prefill_max: int = 0,
        should_stop: ta.Callable[[], bool] | None = None,
        terminators: ta.Iterable[Terminator] = (),
        observers: ta.Iterable[Observer] = (),
) -> Generated:
    """
    Generate up to `max_new_tokens` after `prompt_ids`. `sampler` defaults to greedy;

    `spec=k` drafts k tokens a round with the MTP head (`draft_vocab` restricts its output head to a vocabulary prefix),
    or with `draft` when given;

    `lookup_ngram=n` drafts `lookup_k` tokens by prompt lookup first (n-gram matches against the context), falling back
    to those;

    `static=False` decodes with the functional reference decoder (plain decode only).

    With a `prefix_cache` the longest cached state whose tokens are a prefix of the prompt is resumed, and the states
    after the prompt and after the generation are stored -- and, with `prefill_checkpoints`, up to that many states
    from inside the prefill (after its 1st, 2nd, 4th ... chunk of `prefill_chunk` tokens), which a later prompt that
    shares only the start of this one resumes from.

    `step_prefill_max`: a prefill of up to that many tokens (a short prompt, or what a resumed one has left) runs
    through the decoder's captured 16-token step instead of the eager forward, whose fixed cost dominates there.

    `constraint` masks every token to a grammar.

    `should_stop` (polled between prefill chunks and rounds) and `on_token` may raise or trigger `Cancelled`.

    `observers` see the generation as it happens (the prefill's reuse, every round), which is how a caller gets
    statistics out of a generation that was cancelled.
    """

    ops = model.ops
    vocab_size = model.cfg.vocab_size

    sampler = sampler if sampler is not None else Sampler()
    sampler.bind(ops)

    processors: list[LogitProcessor] = []
    if constraint is not None:
        processors.append(GrammarProcessor(
            ops,
            vocab_size=vocab_size,
            constraint=constraint,
        ))
    if presence_penalty or frequency_penalty:
        processors.append(PenaltyProcessor(
            ops,
            vocab_size=vocab_size,
            presence=presence_penalty,
            frequency=frequency_penalty,
        ))
    processor = CompositeLogitProcessor(ops, processors)

    if draft is None:
        if spec:
            draft = MtpDraftSource(
                model=model,
                sampler=sampler,
                processor=processor,
                k=spec,
                draft_vocab=draft_vocab,
            )
        else:
            draft = NullDraftSource()

    if lookup_ngram:
        draft = LookupDraftSource(
            ops,
            vocab_size=vocab_size,
            wrapped=draft,
            ngram=lookup_ngram,
            k=lookup_k,
        )

    source = VerifyTokenSource(
        model=model,
        sampler=sampler,
        processor=processor,
        draft=draft,
        static=static or bool(draft.max_drafts),
        prefill_chunk=prefill_chunk,
        prefill_checkpoints=prefill_checkpoints if prefix_cache is not None else 0,  # (kept for a store only)
        step_prefill_max=step_prefill_max,
    )

    all_terminators: list[Terminator] = [BudgetTerminator(max_new_tokens), *terminators]
    if eos_ids:
        all_terminators.append(EosTerminator(eos_ids))
    if should_stop is not None:
        all_terminators.append(CallbackTerminator(should_stop))

    all_observers: list[Observer] = list(observers)
    if on_token is not None:
        all_observers.append(TokenCallbackObserver(on_token))

    store: StateStore = PrefixStateStore(prefix_cache) if prefix_cache is not None else NullStateStore()

    loop = GenerationLoop(
        source=source,
        terminator=CompositeTerminator(all_terminators),
        observer=CompositeObserver(all_observers),
        store=store,
    )

    capacity = generation_capacity(len(prompt_ids), max_new_tokens, draft.max_drafts, capacity)
    return loop.run(Generation(prompt=prompt_ids, capacity=capacity))


class ManualGenerationRunner(GenerationRunner):
    """
    `generate` behind the GenerationRunner interface: what the serving engine runs on without an injector (the
    bindings' ScopedGenerationRunner, decode/inject.py, is the other implementation). The server's own choices --
    the model, speculation, the store, the decode capacity -- are fixed here; each request brings the rest.
    """

    def __init__(
            self,
            model: Qwen35,
            *,
            spec: int = 0,
            draft_vocab: int = 0,
            lookup_ngram: int = 0,
            lookup_k: int = 3,
            capacity: int | None = None,
            prefix_cache: PrefixCache | None = None,
            prefill_chunk: int = 4096,
            prefill_checkpoints: int = 0,
            step_prefill_max: int = 0,
            static: bool = True,
    ) -> None:
        super().__init__()

        self._model = model
        self._spec = spec
        self._draft_vocab = draft_vocab
        self._lookup_ngram = lookup_ngram
        self._lookup_k = lookup_k
        self._capacity = capacity
        self._prefix_cache = prefix_cache
        self._prefill_chunk = prefill_chunk
        self._prefill_checkpoints = prefill_checkpoints
        self._step_prefill_max = step_prefill_max
        self._static = static

    def run(self, params: GenerationParams) -> Generated:
        return generate(
            self._model,
            params.prompt,
            max_new_tokens=params.max_new_tokens,
            eos_ids=params.eos_ids,
            on_token=params.on_token,
            static=self._static,
            sampler=Sampler(
                temperature=params.temperature,
                top_k=params.top_k,
                top_p=params.top_p,
                min_p=params.min_p,
                seed=params.seed,
            ),
            presence_penalty=params.presence_penalty,
            frequency_penalty=params.frequency_penalty,
            spec=self._spec,
            capacity=self._capacity,
            draft_vocab=self._draft_vocab,
            lookup_ngram=self._lookup_ngram,
            lookup_k=self._lookup_k,
            prefix_cache=self._prefix_cache,
            constraint=params.constraint,
            prefill_chunk=self._prefill_chunk,
            prefill_checkpoints=self._prefill_checkpoints,
            step_prefill_max=self._step_prefill_max,
            should_stop=params.should_stop,
            terminators=params.terminators,
            observers=params.observers,
        )
