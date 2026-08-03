# ruff: noqa: FURB188 UP006 UP045
# @om-lite
import dataclasses as dc
import typing as ta

from ...io.pipelines.core import IoPipelineHandler
from ...io.pipelines.core import IoPipelineHandlerContext
from ...io.pipelines.core import IoPipelineMessages


##


@dc.dataclass(frozen=True)
class IoPipelineSseEvent:
    event: ta.Optional[str] = None
    data: str = ''
    id: ta.Optional[str] = None
    retry: ta.Optional[int] = None


##


class IoPipelineSseDecoder(IoPipelineHandler):
    """
    Consumes lines and emits SseEvent objects; ignores comment lines and handles blank-line termination.

    Lines may retain their terminators (the delimiter framing upstream of this handler is customarily configured with
    keep_ends), so they are stripped here rather than assumed absent.
    """

    def __init__(self) -> None:
        super().__init__()

        self._event: ta.Optional[str] = None
        self._data: ta.List[str] = []
        self._id: ta.Optional[str] = None
        self._retry: ta.Optional[int] = None
        self._pending = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            # An event whose terminating blank line never arrived is incomplete and is discarded, per the spec.
            self._reset()
            ctx.feed_in(msg)
            return

        if not isinstance(msg, str):
            ctx.feed_in(msg)
            return

        line = msg

        if line.endswith('\n'):
            line = line[:-1]
        if line.endswith('\r'):
            line = line[:-1]

        if not line:
            self._emit_if_any(ctx)
            return

        if line.startswith(':'):
            return

        if ':' in line:
            field, value = line.split(':', 1)
            if value.startswith(' '):
                value = value[1:]
        else:
            field, value = line, ''

        if field == 'event':
            self._event = value
            self._pending = True
        elif field == 'data':
            self._data.append(value)
            self._pending = True
        elif field == 'id':
            self._id = value
            self._pending = True
        elif field == 'retry':
            try:
                self._retry = int(value)
            except ValueError:
                return
            self._pending = True

    def _reset(self) -> None:
        # The last event id persists across events - only the current event's fields are cleared.
        self._event = None
        self._data.clear()
        self._retry = None
        self._pending = False

    def _emit_if_any(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._pending:
            return

        ev = IoPipelineSseEvent(
            event=self._event,
            data='\n'.join(self._data),
            id=self._id,
            retry=self._retry,
        )

        self._reset()

        ctx.feed_in(ev)
