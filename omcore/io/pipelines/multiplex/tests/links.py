# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
import typing as ta

from ...drivers.pure import PureIoPipelineDriver
from ...drivers.types import IoPipelineDriverState


##


class PureLink:
    """
    Two pure drivers back to back, stepped explicitly: bytes move between them through a bounded simulated link, and
    an output shutdown or close delivers EOF to the other side. Unhandled driver output is collected per side.
    """

    def __init__(
            self,
            a: PureIoPipelineDriver,
            b: PureIoPipelineDriver,
            *,
            capacity: ta.Optional[int] = None,
    ) -> None:
        super().__init__()

        self.a = a
        self.b = b
        self._capacity = capacity
        self._eof_sent: ta.Set[int] = set()
        self.unhandled: ta.Dict[int, ta.List[ta.Any]] = {id(a): [], id(b): []}
        self.moved: ta.Dict[int, int] = {id(a): 0, id(b): 0}

        # Per pump step: the largest number of bytes one side had queued as transport output.
        self.max_pending_output: ta.Dict[int, int] = {id(a): 0, id(b): 0}

    def unhandled_of(self, d: PureIoPipelineDriver) -> ta.List[ta.Any]:
        return self.unhandled[id(d)]

    def _step(self, d: PureIoPipelineDriver) -> bool:
        progressed = False
        while d.is_running or d.state is IoPipelineDriverState.NEW:
            out = d.next(read=True, raise_on_stall=False)
            if out is None:
                break
            self.unhandled[id(d)].append(out)
            progressed = True
        return progressed

    def _move(self, src: PureIoPipelineDriver, dst: PureIoPipelineDriver) -> bool:
        moved = False
        if src.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and src.has_pending_output:
            self.max_pending_output[id(src)] = max(self.max_pending_output[id(src)], src.pending_output_bytes)
            room: ta.Optional[int] = None
            if self._capacity is not None and dst.is_running:
                room = max(self._capacity - dst.pending_input_bytes, 0)
            if room is None or room > 0 or not src.pending_output_bytes:
                data = src.drain_output(room)
                if data and dst.is_running:
                    dst.feed_input(data)
                    self.moved[id(src)] += len(data)
                moved = True

        src_ended = src.output_shutdown or src.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)
        if src_ended and not src.has_pending_output and id(src) not in self._eof_sent:
            self._eof_sent.add(id(src))
            if dst.is_running:
                dst.feed_eof()
            moved = True

        return moved

    def pump(self, max_rounds: int = 100_000, *, until: ta.Optional[ta.Callable[[], bool]] = None) -> None:
        for _ in range(max_rounds):
            if until is not None and until():
                return
            progressed = self._step(self.a)
            progressed |= self._step(self.b)
            progressed |= self._move(self.a, self.b)
            progressed |= self._move(self.b, self.a)
            if not progressed:
                if until is not None and not until():
                    raise RuntimeError('link quiesced before condition')
                return

        raise RuntimeError('link did not quiesce')

    def close(self) -> None:
        self.a.close()
        self.b.close()
