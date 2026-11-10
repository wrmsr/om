from ..core.errors import Cancelled
from .generation import Generated
from .generation import Generation
from .observers import Observer
from .stores import StateStore
from .terminators import Terminator
from .tokens import TokenSource


##


class GenerationLoop:
    """
    Written once, against the extension points: resume or prefill (the token source, from what the store has); store
    the prompt's state; then rounds -- the source's accepted tokens, the terminator's cut, the commit, the observers --
    until the terminator stops; then store the final state. Features are implementations of the collaborators, never
    parameters or branches here.
    """

    def __init__(
            self,
            *,
            source: TokenSource,
            terminator: Terminator,
            observer: Observer,
            store: StateStore,
    ) -> None:
        super().__init__()

        self._source = source
        self._terminator = terminator
        self._observer = observer
        self._store = store

    def run(self, gen: Generation) -> Generated:
        source = self._source
        terminator = self._terminator

        def poll() -> bool:
            return terminator.poll(gen)

        source.start(gen, resume=self._store.lookup(gen.prompt), poll=poll)
        self._store.offer(lambda: source.export(gen))
        self._observer.on_prefill(gen)

        rounds = drafted = accepted = 0
        # (a terminator that would keep nothing of an empty round -- a budget already spent -- stops before stepping)
        while terminator.cut(gen, ()) != 0:
            if poll():
                raise Cancelled

            rnd = source.step(gen)
            n = terminator.cut(gen, rnd.tokens)
            keep = len(rnd.tokens) if n is None else n

            source.commit(gen, rnd, keep)
            kept = rnd.tokens[:keep]
            gen.tokens.extend(kept)

            rounds += 1
            drafted += rnd.drafts.n if rnd.drafts is not None else 0
            accepted += rnd.accepted

            self._observer.on_round(gen, rnd, kept)

            if n is not None:
                break

        self._store.offer(lambda: source.export(gen))

        return Generated(
            tokens=list(gen.tokens),
            prompt_tokens=len(gen.prompt),
            reused=gen.reused,
            rounds=rounds,
            drafted=drafted,
            accepted=accepted,
        )
