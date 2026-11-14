import typing as ta

from ..ops.base import Array


##


class StepSlab:
    """
    What a static decoder leaves for the next one of the same capacity: its capacity buffers and the steps captured
    against them.

    A captured step is bound to the arrays it was captured with -- they are the graph's static inputs, and the KV
    buffers among them are written in place -- so a decoder in fresh buffers captures every step it uses again: ~60 ms
    for the one-token step on the 27B, at every generation's first token, and as much again for each other shape and
    attention window it reaches. A decoder that starts in the buffers its predecessor left runs the predecessor's
    captured steps as they are: the prefill writes into those buffers (`Model.prefill`'s `reserve_into`), the decoder
    adopts them, finds them to be the slab's, and takes its steps.

    `layers` is, per layer, the layer's state arrays where that state lives in capacity buffers (None for a fixed-size
    one), as the decoder last held them. What the buffers contain is of no account: a state says how many positions of
    it are valid, and the rest is rewritten before anything reads it.
    """

    def __init__(
            self,
            capacity: int,
            layers: ta.Sequence[tuple[Array, ...] | None],
            fns: dict[ta.Any, ta.Callable[..., tuple[Array, ...]]],
    ) -> None:
        super().__init__()

        self.capacity = capacity
        self.layers = list(layers)
        self.fns = fns

    def holds(self, layers: ta.Sequence[tuple[Array, ...] | None]) -> bool:
        """Whether `layers` (laid out as `self.layers`) are these very buffers, array for array."""

        if len(layers) != len(self.layers):
            return False
        for mine, theirs in zip(self.layers, layers):
            if (mine is None) != (theirs is None):
                return False
            if mine is not None and theirs is not None:
                if len(mine) != len(theirs) or any(a is not b for a, b in zip(mine, theirs)):
                    return False
        return True


class StepSlabHolder:
    """
    Where the last decoder's slab waits for the next (the model, for its decoders; the MTP head, for its own steps).
    One at most: taking hands it over -- two decoders never share buffers -- and one of another capacity is let go, as a
    second set of capacity buffers held idle is gigabytes.
    """

    _slab: StepSlab | None = None

    def take_slab(self, capacity: int) -> StepSlab | None:
        slab, self._slab = self._slab, None
        if slab is not None and slab.capacity != capacity:
            return None
        return slab

    def put_slab(self, slab: StepSlab) -> None:
        self._slab = slab

    def drop_slab(self) -> None:
        """Let the waiting buffers and captured steps go (their memory back, at the cost of the next capture)."""

        self._slab = None
