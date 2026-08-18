"""A tiny spinner state holder - advance it from a timer, read `frame` when rendering."""
import typing as ta

from omcore.term.spinners import SPINNERS


##


class Spinner:
    def __init__(self, name: str = 'dots3') -> None:
        super().__init__()

        self._frames: ta.Sequence[str] = SPINNERS[name]
        self._index = 0

    @property
    def frame(self) -> str:
        return self._frames[self._index % len(self._frames)]

    def advance(self) -> None:
        self._index += 1
