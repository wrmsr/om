from ..decode.sampling import Sampler
from ..ops.base import Array
from ..ops.base import Ops


##


class DraftDraws:
    """
    What a captured run of drafts is handed of a sampler besides its operations: the settings as arrays -- so one
    captured run serves every setting of a sampler `shape` -- and the uniform draws, which a captured function cannot
    make itself (it cannot hold the generator).
    """

    def __init__(self, ops: Ops, sampler: Sampler) -> None:
        super().__init__()

        self._ops = ops
        self._sampler = sampler
        self._settings: tuple[Array, ...] | None = None
        self._no_noise: Array | None = None

    def settings(self) -> tuple[Array, ...]:
        """The sampler's `settings` as 0-d float32 arrays: `Sampler.warp`'s arguments."""

        if self._settings is None:
            ops = self._ops
            f32 = ops.dtype('f32')
            self._settings = tuple(ops.zeros((), f32) + v for v in self._sampler.settings())
        return self._settings

    def noise(self, count: int, width: int) -> Array:
        """
        The uniform draws a run of `count` sampled drafts makes, a [1, width] row each as `Sampler.draw` would take
        them one at a time (so a seed's stream is what it was when drafts were drawn one by one). Greedy takes none.
        """

        ops = self._ops
        if self._sampler.greedy:
            if self._no_noise is None:
                self._no_noise = ops.zeros((1, 1), ops.dtype('f32'))
            return self._no_noise
        rows = [ops.random_uniform((1, width)) for _ in range(count)]
        return rows[0] if count == 1 else ops.concat(rows, 0)
