# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Relays: joining two pipelines at their innermost positions so that data, backpressure, end-of-stream, and failure
cross correctly in both directions. Either pipeline may be a hosted transport or a multiplexed stream's child.

Each side reaches the other only by posting into it, through the other's posting service: a batch of input read on
one side under one manual-read token is posted to the other, which feeds it outbound followed by a flush fence. The
reading side asks for its next token only once the other has accepted the batch and is writable, so at most one batch
is in flight per direction and a side whose output is paused stops the other's reading until it resumes. End of input
on one side becomes output shutdown on the other after all relayed data; once both directions have ended, both sides
finish with FinalOutput. A failure or abort on one side aborts the other. The relay object owns the pair and holds
each side's context only weakly, so two joined pipelines form no strong cycle.
"""
import functools
import typing as ta
import weakref

from ....lite.abstract import Abstract
from ....lite.check import check
from ...streambufs.segmented import SegmentedByteStreamBuffer
from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerNotification
from ..core import IoPipelineHandlerNotifications
from ..core import IoPipelineMessages
from ..core import IoPipelineMetadata
from ..core import IoPipelineService
from ..errors import AbortedIoPipelineError
from ..errors import IoPipelineError
from ..flow.stub import StubIoPipelineFlowService
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..posting.types import IoPipelinePosting


IoPipelineRelaySide = ta.Literal['a', 'b']  # ta.TypeAlias

IoPipelineRelayMessageMapper = ta.Callable[[ta.Any], ta.Optional[ta.Any]]  # ta.TypeAlias


##


class RelayIoPipelineError(IoPipelineError):
    pass


class AutoReadRelayIoPipelineError(RelayIoPipelineError):
    """A relay end was added to a pipeline whose input is automatic: backpressure could not cross it."""


class UnmappedMessageRelayIoPipelineError(RelayIoPipelineError):
    """A message other than bytes arrived at a relay end which has no mapping for it."""

    def __init__(self, msg: ta.Any) -> None:
        super().__init__(msg)

        self.msg = msg


class PeerGoneRelayIoPipelineError(RelayIoPipelineError, AbortedIoPipelineError):
    """The other side of the relay failed, was aborted, or went away before this side finished."""


##


class IoPipelineRelayPeer(Abstract):
    """What a relay end knows of the other side: enough to post into it."""


@ta.final
class IoPipelineRelay:
    """
    Owns a pair of relay ends. Make the ends with `end()`, or whole specs with `spec()`, which installs a manual-read
    flow service when the spec has none, since a relay end refuses to be added where input is automatic.
    """

    @ta.final
    class _Attachment:
        def __init__(self, ctx: IoPipelineHandlerContext, posting: IoPipelinePosting) -> None:
            self.ctx_ref = weakref.ref(ctx)
            self.posting = posting

        @property
        def ctx(self) -> ta.Optional[IoPipelineHandlerContext]:
            if (ctx := self.ctx_ref()) is None or ctx.invalidated:
                return None
            return ctx

    def __init__(self) -> None:
        super().__init__()

        self._attachments: ta.Dict[IoPipelineRelaySide, ta.Optional[IoPipelineRelay._Attachment]] = {
            'a': None,
            'b': None,
        }
        self._ends_made: ta.Set[IoPipelineRelaySide] = set()
        self._aborted = False
        self._abort_cause: ta.Optional[BaseException] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @staticmethod
    def other(side: IoPipelineRelaySide) -> IoPipelineRelaySide:
        return 'b' if side == 'a' else 'a'

    @property
    def aborted(self) -> bool:
        return self._aborted

    @property
    def abort_cause(self) -> ta.Optional[BaseException]:
        return self._abort_cause

    def is_attached(self, side: IoPipelineRelaySide) -> bool:
        return (a := self._attachments[side]) is not None and a.ctx is not None

    #

    def end(
            self,
            side: IoPipelineRelaySide,
            *,
            map_message: ta.Optional[IoPipelineRelayMessageMapper] = None,
    ) -> 'IoPipelineRelayEndHandler':
        check.in_(side, ('a', 'b'))
        check.not_in(side, self._ends_made)
        self._ends_made.add(side)
        return IoPipelineRelayEndHandler(self, side, map_message=map_message)

    def spec(
            self,
            side: IoPipelineRelaySide,
            handlers: ta.Sequence[IoPipelineHandler] = (),
            *,
            map_message: ta.Optional[IoPipelineRelayMessageMapper] = None,
            metadata: ta.Sequence[IoPipelineMetadata] = (),
            services: ta.Sequence[IoPipelineService] = (),
            config: ta.Optional[IoPipeline.Config] = None,
    ) -> IoPipeline.Spec:
        """A spec with the relay end innermost, behind `handlers`, and manual-read flow unless `services` has flow."""

        svcs = list(services)
        if not any(isinstance(s, IoPipelineFlow) for s in svcs):
            svcs.append(StubIoPipelineFlowService(auto_read=False))
        return IoPipeline.Spec(
            [*handlers, self.end(side, map_message=map_message)],
            metadata=metadata,
            services=svcs,
            **({'config': config} if config is not None else {}),
        )

    #

    def _attach(self, side: IoPipelineRelaySide, ctx: IoPipelineHandlerContext) -> None:
        posting = check.not_none(
            ctx.services.find(IoPipelinePosting),
            'a relay end needs a posting service: the pipeline must be driven',
        )
        self._attachments[side] = IoPipelineRelay._Attachment(ctx, posting)

        if self._aborted:
            # Aborted before this side came: it is told as the other side would have told it.
            self._post(side, functools.partial(IoPipelineRelayEndHandler._abort_posted, check.not_none(self._abort_cause)))  # noqa
            return

        # The other side, if waiting for this one, may start reading, and send what it held for this one.
        self._post(self.other(side), IoPipelineRelayEndHandler._peer_ready_posted)  # noqa

    def _detach(self, side: IoPipelineRelaySide) -> None:
        self._attachments[side] = None

    def _post(
            self,
            side: IoPipelineRelaySide,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> bool:
        """Posts work into a side's handler; False if that side is not attached, or can no longer be posted into."""

        if (a := self._attachments[side]) is None or (ctx := a.ctx) is None:
            return False
        try:
            a.posting.post_context(ctx.ref, fn)
        except Exception:  # noqa  # Its driver closed: as good as gone.
            return False
        return True

    def _abort(self, from_side: IoPipelineRelaySide, exc: BaseException) -> None:
        if self._aborted:
            return
        self._aborted = True
        self._abort_cause = exc
        self._post(self.other(from_side), functools.partial(IoPipelineRelayEndHandler._abort_posted, exc))  # noqa


##


class IoPipelineRelayEndHandler(IoPipelineHandler):
    """
    One side of a relay, innermost in its pipeline.

    Input is read in batches under manual-read tokens and posted to the other side; what the other side posts here is
    fed outbound. Messages other than bytes are given to `map_message`, whose result, unless None, is relayed as a
    message fed outbound on the other side; without a mapping, one aborts the relay with
    UnmappedMessageRelayIoPipelineError.
    """

    def __init__(
            self,
            relay: IoPipelineRelay,
            side: IoPipelineRelaySide,
            *,
            map_message: ta.Optional[IoPipelineRelayMessageMapper] = None,
    ) -> None:
        super().__init__()

        self._relay = relay
        self._side = side
        self._map_message = map_message

        self._batch: ta.List[memoryview] = []
        self._batch_bytes = 0
        # Posts for the other side made before it was attached: sent, in order, once it is.
        self._held_posts: ta.List[ta.Callable[[IoPipelineHandlerContext], None]] = []

        self._started = False
        self._token_out = False
        self._awaiting_ack = False
        self._paused = False
        self._peer_awaits_resume = False
        self._input_ended = False
        self._output_ended = False
        self._finished = False
        self._aborted = False
        self._abort_cause: ta.Optional[BaseException] = None

        self.relayed_in = 0  # bytes read here and posted to the other side
        self.relayed_out = 0  # bytes posted here and fed outbound

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._side}>'

    @property
    def relay(self) -> IoPipelineRelay:
        return self._relay

    @property
    def side(self) -> IoPipelineRelaySide:
        return self._side

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def awaiting_ack(self) -> bool:
        return self._awaiting_ack

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def aborted(self) -> bool:
        return self._aborted

    @property
    def abort_cause(self) -> ta.Optional[BaseException]:
        """Why this side aborted: its own failure, or what the other side reported."""

        return self._abort_cause

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            flow = ctx.services.find(IoPipelineFlow)
            if flow is None or flow.is_auto_read():
                raise AutoReadRelayIoPipelineError(
                    'a relay end needs manual-read input flow, or its reading could not be paused',
                )
            self._relay._attach(self._side, ctx)  # noqa

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._relay._detach(self._side)  # noqa
            self._batch.clear()
            self._batch_bytes = 0
            self._held_posts.clear()
            if not self._finished and not self._aborted:
                # Gone without finishing: the transport failed, or the pipeline was destroyed. The other side follows.
                self._aborted = True
                self._relay._abort(self._side, PeerGoneRelayIoPipelineError(f'relay side {self._side!r} removed'))  # noqa

    #

    def _peer_post(self, fn: ta.Callable[[IoPipelineHandlerContext], None]) -> bool:
        other = self._relay.other(self._side)
        if not self._relay.is_attached(other) or self._held_posts:
            # Held until the other side is attached - and, once it is, until what was held before it has been sent,
            # which the peer-ready post it makes does - so that nothing overtakes what was held.
            if self._relay.aborted:
                return False
            self._held_posts.append(fn)
            return True
        return self._relay._post(other, fn)  # noqa

    def _send_held_posts(self) -> bool:
        held = self._held_posts
        self._held_posts = []
        other = self._relay.other(self._side)
        return all(self._relay._post(other, fn) for fn in held)  # noqa

    def _maybe_read(self, ctx: IoPipelineHandlerContext) -> None:
        if (
                self._started and
                not self._input_ended and
                not self._token_out and
                not self._awaiting_ack and
                not self._aborted and
                self._relay.is_attached(self._relay.other(self._side))
        ):
            self._token_out = True
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _flush_batch(self, ctx: IoPipelineHandlerContext) -> None:
        self._token_out = False
        if not self._batch:
            self._maybe_read(ctx)
            return

        segs = self._batch
        self._batch = []
        self._batch_bytes = 0
        self._awaiting_ack = True
        if not self._peer_post(functools.partial(IoPipelineRelayEndHandler._deliver_batch_posted, segs)):
            self._abort(ctx, PeerGoneRelayIoPipelineError('the other side is gone'))

    def _maybe_finish(self, ctx: IoPipelineHandlerContext) -> None:
        if self._input_ended and self._output_ended and not self._finished and not self._aborted:
            self._finished = True
            ctx.feed_final_output()

    def _abort(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        if self._aborted or self._finished:
            return
        self._aborted = True
        self._abort_cause = exc
        self._batch.clear()
        self._batch_bytes = 0
        self._held_posts.clear()
        self._relay._abort(self._side, exc)  # noqa
        # Destroyed from the driver's side of the boundary, not from within this handler's own call.
        ctx.defer(IoPipelineRelayEndHandler._destroy_deferred)

    @staticmethod
    def _destroy_deferred(ctx: IoPipelineHandlerContext) -> None:
        if ctx.pipeline.is_ready:
            ctx.pipeline.destroy()

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if ByteStreamBuffers.can_bytes(msg):
            # Held by reference: a producer must not mutate what it fed, as the byte buffer contract says.
            for seg in ByteStreamBuffers.iter_segments(msg):
                if seg:
                    self._batch.append(seg)
                    self._batch_bytes += len(seg)
                    self.relayed_in += len(seg)
            return

        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._flush_batch(ctx)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            self._started = True
            self._maybe_read(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            if self._batch:
                self._flush_batch(ctx)
            self._token_out = False
            self._input_ended = True
            if not self._aborted:
                if not self._peer_post(IoPipelineRelayEndHandler._deliver_end_posted):
                    self._abort(ctx, PeerGoneRelayIoPipelineError('the other side is gone'))
                    return
            self._maybe_finish(ctx)
            return

        if isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._paused = True
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._paused = False
            ctx.feed_in(msg)
            if self._peer_awaits_resume:
                self._peer_awaits_resume = False
                self._peer_post(IoPipelineRelayEndHandler._resume_posted)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self._abort(ctx, msg.exc)
            return

        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)
            return

        if (mapper := self._map_message) is None:
            # Innermost, an error raised here would have nowhere to go: the relay is aborted outright instead.
            self._abort(ctx, UnmappedMessageRelayIoPipelineError(msg))
            return
        if (mapped := mapper(msg)) is not None:
            if not self._peer_post(functools.partial(IoPipelineRelayEndHandler._deliver_message_posted, mapped)):
                self._abort(ctx, PeerGoneRelayIoPipelineError('the other side is gone'))

    #
    # posted by the other side, run here with this handler's context

    @staticmethod
    def _of(ctx: IoPipelineHandlerContext) -> 'IoPipelineRelayEndHandler':
        return check.isinstance(ctx.handler, IoPipelineRelayEndHandler)

    @staticmethod
    def _peer_ready_posted(ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if not self._send_held_posts():  # noqa
            self._abort(ctx, PeerGoneRelayIoPipelineError('the other side is gone'))  # noqa
            return
        self._maybe_read(ctx)  # noqa

    @staticmethod
    def _deliver_batch_posted(segs: ta.Sequence[memoryview], ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if self._aborted or self._output_ended:  # noqa
            return
        buf = SegmentedByteStreamBuffer()
        for seg in segs:
            buf.write(seg)
            self.relayed_out += len(seg)
        ctx.feed_out(buf)
        ctx.feed_out(IoPipelineFlowMessages.FlushOutput())
        # Acknowledged once the driver has taken the batch and, if it paused on it, only once it resumes.
        ctx.defer(IoPipelineRelayEndHandler._after_batch_deferred)

    @staticmethod
    def _after_batch_deferred(ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if self._aborted:  # noqa
            return
        if self._paused:  # noqa
            self._peer_awaits_resume = True  # noqa
        else:
            self._peer_post(IoPipelineRelayEndHandler._resume_posted)  # noqa

    @staticmethod
    def _resume_posted(ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        self._awaiting_ack = False  # noqa
        self._maybe_read(ctx)  # noqa

    @staticmethod
    def _deliver_message_posted(msg: ta.Any, ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if self._aborted or self._output_ended:  # noqa
            return
        ctx.feed_out(msg)
        ctx.feed_out(IoPipelineFlowMessages.FlushOutput())

    @staticmethod
    def _deliver_end_posted(ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if self._aborted or self._output_ended:  # noqa
            return
        self._output_ended = True  # noqa
        # A transport which cannot half-close fails this; the side then stays open until FinalOutput.
        ctx.feed_shutdown_output()
        self._maybe_finish(ctx)  # noqa

    @staticmethod
    def _abort_posted(exc: BaseException, ctx: IoPipelineHandlerContext) -> None:
        self = IoPipelineRelayEndHandler._of(ctx)
        if self._aborted or self._finished:  # noqa
            return
        self._aborted = True  # noqa
        self._abort_cause = exc  # noqa
        self._batch.clear()  # noqa
        self._held_posts.clear()  # noqa
        self._batch_bytes = 0  # noqa
        if ctx.pipeline.is_ready:
            ctx.pipeline.destroy()
