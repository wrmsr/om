# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
The embedded driver for one stream's child pipeline.

A multiplexing handler hosts one child pipeline per established stream and acts as its driver, satisfying for it the
terminal contract that socket drivers satisfy for a top-level pipeline. This module holds the per-child half of that
work - building the child, delivering stream input to it under its own input flow, collecting its output into the
stream's ordered outbound queue, deriving its writability, completing its fences, and tearing it down. Connection-level
concerns - credit, scheduling between streams, emission into the parent, parent fences - belong to the host.

Nothing here owns or caches the parent pipeline or its context. Child timers reach the host through the parent's
scheduling service, which supplies the host's context to the callback; the host is told about activity it did not
itself cause through `MultiplexChildHost.on_child_activity`.
"""
import abc
import dataclasses as dc
import functools
import typing as ta
import weakref

from ....lite.abstract import Abstract
from ....lite.check import check
from ...streambufs.segmented import SegmentedByteStreamBuffer
from ...streambufs.utils import ByteStreamBuffers
from ..asyncs import AsyncIoPipelineMessages
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineHandlerUpdate
from ..core import IoPipelineMessages
from ..core import IoPipelineService
from ..core import IoPipelineUpdate
from ..errors import AbortedIoPipelineError
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.types import IoPipelineScheduling
from .streams import MultiplexInputData
from .streams import MultiplexInputEnd
from .streams import MultiplexInputMessage
from .streams import MultiplexStream
from .types import MultiplexStreamMetadata
from .types import MultiplexStreamOpening
from .types import UnclaimedOutputMultiplexError


##


class MultiplexChildHost(Abstract):
    """
    Implemented by the handler hosting child drivers. Child machinery reaches it only through a parent context given to
    a callback - a scheduled callback, or a completion listener holding the context weakly - never through a cached
    reference.
    """

    @abc.abstractmethod
    def on_child_activity(self, ctx: IoPipelineHandlerContext) -> None:
        """Something happened in a child outside the host's own turn; the host should advance."""

        raise NotImplementedError


##


@ta.final
class MultiplexChildFlowService(IoPipelineFlow, IoPipelineService):
    """The flow service installed in a child whose spec does not supply one."""

    def __init__(self, *, auto_read: bool = True) -> None:
        super().__init__()

        self._auto_read = auto_read

    def __repr__(self) -> str:
        return f'{type(self).__name__}(auto_read={self._auto_read!r})'

    def is_auto_read(self) -> bool:
        return self._auto_read


@ta.final
class MultiplexChildScheduling(IoPipelineScheduling, IoPipelineService):
    """
    Child timers, delegated to the parent's scheduling service under the host handler's ownership.

    Removing a child handler cancels its timers, as does destroying the child pipeline; removing the host from the
    parent cancels everything the parent scheduled on its behalf. The parent callback holds only weak references to
    the child side, so a cancelled timer cannot keep a closed stream alive.
    """

    def __init__(
            self,
            parent_ctx: IoPipelineHandlerContext,
            on_failure: ta.Callable[[BaseException], None],
    ) -> None:
        super().__init__()

        self.__parent_ctx_ref = weakref.ref(parent_ctx)
        self._on_failure = on_failure

        self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None
        self._live: ta.Set[MultiplexChildScheduling._Handle] = set()

    @property
    def _pipeline(self) -> ta.Optional[IoPipeline]:
        if self.__pipeline_ref is None:
            return None
        return self.__pipeline_ref()

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'added':
            check.none(self._pipeline)
            self.__pipeline_ref = weakref.ref(pipeline)

        elif kind == 'removed':
            self.cancel_all()
            self.__pipeline_ref = None

    def handler_update(self, handler_ref: IoPipelineHandlerRef, kind: IoPipelineHandlerUpdate) -> None:
        if kind == 'removing':
            self.cancel_all(handler_ref)

    @ta.final
    class _Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                sched: 'MultiplexChildScheduling',
                handler_ref: IoPipelineHandlerRef,
                fn: ta.Callable[..., None],
                with_context: bool,
        ) -> None:
            super().__init__()

            self.__sched_ref = weakref.ref(sched)
            self.__child_ctx_ref = weakref.ref(handler_ref._context)  # noqa
            self._fn: ta.Optional[ta.Callable[..., None]] = fn
            self._with_context = with_context

            self._parent_handle: ta.Optional[IoPipelineScheduling.Handle] = None
            self._cancelled = False
            self._done = False

        @property
        def _sched(self) -> ta.Optional['MultiplexChildScheduling']:
            return self.__sched_ref()

        @property
        def _child_ctx(self) -> ta.Optional[IoPipelineHandlerContext]:
            return self.__child_ctx_ref()

        def cancel(self) -> None:
            if self._cancelled or self._done:
                return

            self._cancelled = True
            self._fn = None
            if (sched := self._sched) is not None:
                sched._live.discard(self)  # noqa
            if (ph := self._parent_handle) is not None:
                self._parent_handle = None
                ph.cancel()

    @staticmethod
    def _fire(handle_ref: ta.Callable[[], ta.Optional['MultiplexChildScheduling._Handle']], ctx: IoPipelineHandlerContext) -> None:  # noqa
        if (h := handle_ref()) is None or h._cancelled or h._done:  # noqa
            return

        h._done = True  # noqa
        h._parent_handle = None  # noqa
        fn = check.not_none(h._fn)  # noqa
        h._fn = None  # noqa

        if (sched := h._sched) is None:  # noqa
            return
        sched._live.discard(h)  # noqa

        if (
                (pipeline := sched._pipeline) is not None and  # noqa
                pipeline.is_ready and
                (child_ctx := h._child_ctx) is not None and  # noqa
                not child_ctx.invalidated
        ):
            try:
                with pipeline.enter():
                    if h._with_context:  # noqa
                        fn(child_ctx)
                    else:
                        fn()

            except Exception as e:  # noqa
                sched._on_failure(e)  # noqa

        check.isinstance(ctx.handler, MultiplexChildHost).on_child_activity(ctx)

    def _schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[..., None],
            *,
            with_context: bool,
    ) -> IoPipelineScheduling.Handle:
        pipeline = check.not_none(self._pipeline)
        check.is_(handler_ref.pipeline, pipeline)
        check.state(pipeline.is_ready)
        check.state(not handler_ref.invalidated)

        parent_ctx = check.not_none(self.__parent_ctx_ref())
        check.state(not parent_ctx.invalidated)

        h = self._Handle(self, handler_ref, fn, with_context)
        h._parent_handle = parent_ctx.services[IoPipelineScheduling].schedule_context(  # noqa
            parent_ctx.ref,
            delay_s,
            functools.partial(MultiplexChildScheduling._fire, weakref.ref(h)),
        )
        self._live.add(h)
        return h

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        return self._schedule(handler_ref, delay_s, fn, with_context=False)

    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        return self._schedule(handler_ref, delay_s, fn, with_context=True)

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for h in tuple(self._live):
            if handler_ref is None or h._child_ctx is handler_ref._context:  # noqa
                h.cancel()


@ta.final
class _MultiplexChildLifecycleService(IoPipelineService):
    """Notices the child pipeline being destroyed - by its driver, or by anyone else holding it, such as its opener."""

    def __init__(self, on_destroyed: ta.Callable[[], None]) -> None:
        super().__init__()

        self._on_destroyed = on_destroyed

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'removed':
            self._on_destroyed()


##


@ta.final
@dc.dataclass(frozen=True)
class MultiplexChildConfig:
    # The most input bytes delivered in one batch, as one buffer followed by FlushInput. In manual-read mode one
    # ReadyForInput permits one batch.
    read_batch_max_bytes: int = 1024 * 1024

    # Hysteresis watermarks, in the stream's queued outbound bytes, for the child's PauseOutput / ReadyForOutput.
    write_high_watermark: int = 64 * 1024
    write_low_watermark: int = 16 * 1024

    # Input mode for children whose spec supplies no flow service.
    default_auto_read: bool = True

    strict_input_flow: bool = False

    def __post_init__(self) -> None:
        """Validate batch size and watermarks."""

        if self.read_batch_max_bytes < 1:
            raise ValueError(self.read_batch_max_bytes)
        if not (0 <= self.write_low_watermark <= self.write_high_watermark):
            raise ValueError((self.write_low_watermark, self.write_high_watermark))


@ta.final
class MultiplexChild:
    """
    Drives one stream's child pipeline.

    Every call into the child is guarded: a child failure - a handler error escaping as an unhandleable pipeline error,
    an error raised by a timer callback, a construction failure - is recorded as `failure` and stops further driving,
    and is never raised into the host. The host reacts by aborting the stream.
    """

    def __init__(
            self,
            stream: MultiplexStream,
            spec: IoPipeline.Spec,
            opening: MultiplexStreamOpening,
            *,
            config: MultiplexChildConfig,
            parent_ctx: ta.Optional[IoPipelineHandlerContext] = None,
    ) -> None:
        super().__init__()

        self._stream = stream
        self._config = config

        self._failure: ta.Optional[BaseException] = None
        self._finished = False

        self._want_read = False
        self._final_input_delivered = False
        self._writable = True
        self._output_ended = False  # a ShutdownOutput or FinalOutput has been collected
        self._pending_awaits: ta.List[AsyncIoPipelineMessages.Await] = []

        services: ta.List[IoPipelineService] = list(spec.services)
        flow: ta.Optional[IoPipelineFlow] = None
        for svc in services:
            if isinstance(svc, IoPipelineFlow):
                flow = svc
        if flow is None:
            flow = MultiplexChildFlowService(auto_read=config.default_auto_read)
            services.append(flow)
        self._flow = flow

        self._sched: ta.Optional[MultiplexChildScheduling] = None
        if parent_ctx is not None and parent_ctx.services.find(IoPipelineScheduling) is not None:
            # The service reports failures back without owning this child: the child owns the service.
            self._sched = MultiplexChildScheduling(
                parent_ctx,
                functools.partial(MultiplexChild._fail_ref, weakref.ref(self)),
            )
            services.append(self._sched)

        # Like the scheduling service, it holds the child and the parent context only weakly.
        services.append(_MultiplexChildLifecycleService(functools.partial(
            MultiplexChild._destroyed_ref,
            weakref.ref(self),
            weakref.ref(parent_ctx) if parent_ctx is not None else None,
        )))

        self._pipeline: ta.Optional[IoPipeline] = None
        try:
            self._pipeline = IoPipeline(dc.replace(
                spec,
                metadata=[*spec.metadata, MultiplexStreamMetadata(opening)],
                services=services,
            ))
        except Exception as e:  # noqa
            self._fail(e)

        self._want_read = self._auto_read

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._stream.key!r}>'

    @property
    def stream(self) -> MultiplexStream:
        return self._stream

    @property
    def pipeline(self) -> ta.Optional[IoPipeline]:
        return self._pipeline

    @property
    def failure(self) -> ta.Optional[BaseException]:
        return self._failure

    @property
    def is_running(self) -> bool:
        return self._failure is None and not self._finished and self._pipeline is not None and self._pipeline.is_ready

    @property
    def wants_input(self) -> bool:
        return self.is_running and self._want_read and not self._final_input_delivered

    @property
    def final_input_delivered(self) -> bool:
        return self._final_input_delivered

    @property
    def _auto_read(self) -> bool:
        return self._flow.is_auto_read()

    def _fail(self, e: BaseException) -> None:
        if self._failure is None:
            self._failure = e

    @staticmethod
    def _fail_ref(child_ref: ta.Callable[[], ta.Optional['MultiplexChild']], e: BaseException) -> None:
        if (child := child_ref()) is not None:
            child._fail(e)  # noqa

    @staticmethod
    def _destroyed_ref(
            child_ref: ta.Callable[[], ta.Optional['MultiplexChild']],
            parent_ctx_ref: ta.Optional[ta.Callable[[], ta.Optional[IoPipelineHandlerContext]]],
    ) -> None:
        # The child's own finish and abort mark it finished before destroying it; any other destruction abandons the
        # stream, which is then reset like a failed one - and the host must hear of it now, not at its next turn.
        if (child := child_ref()) is None or child._finished:  # noqa
            return
        child._fail(AbortedIoPipelineError('stream pipeline destroyed'))  # noqa

        if parent_ctx_ref is None or (ctx := parent_ctx_ref()) is None or ctx.invalidated:
            return
        host = check.isinstance(ctx.handler, MultiplexChildHost)
        with ctx.pipeline.enter():
            host.on_child_activity(ctx)

    ##
    # input

    def start(self) -> None:
        """Feeds InitialInput: called when the stream is established."""

        if not self.is_running:
            return
        try:
            check.not_none(self._pipeline).feed_initial_input()
        except Exception as e:  # noqa
            self._fail(e)

    def feed(self, *msgs: ta.Any) -> bool:
        """Feeds messages at the child's boundary, bypassing its input flow, as a driver's enqueue does."""

        if not self.is_running:
            return False
        return self._feed(*msgs)

    def _feed(self, *msgs: ta.Any) -> bool:
        try:
            check.not_none(self._pipeline).feed_in(*msgs)
        except Exception as e:  # noqa
            self._fail(e)
            return False
        return self.is_running

    def deliver_input(self) -> ta.List[int]:
        """
        Delivers queued stream input under the child's input flow, returning the flow-controlled cost delivered (for
        receive credit replenishment).

        In automatic-read mode everything queued is delivered, in batches of at most `read_batch_max_bytes`. In
        manual-read mode one ReadyForInput permits one batch - whatever is queued up to that bound - and a token
        arriving with nothing queued remains outstanding. Contiguous data is delivered as one buffer, typed messages
        individually and in order, and each batch containing either is followed by FlushInput. End-of-input becomes
        FinalInput after everything queued before it, delivered as part of a batch (in manual mode, under a token).
        """

        consumed: ta.List[int] = []
        stream = self._stream
        while self.is_running and stream.in_head() is not None:
            if not self._auto_read and not self._want_read:
                break

            segs: ta.List[memoryview] = []
            batch_bytes = 0
            delivered = False
            end = False

            def flush_segs() -> bool:
                # As the reference drivers do, each batch's data is one consumable buffer which a decoder may adopt.
                # Whole bytes-like segments are held by reference rather than copied.
                nonlocal segs
                if not segs:
                    return True
                buf = SegmentedByteStreamBuffer()
                for seg in segs:
                    buf.write(seg)
                segs = []
                return self._feed(buf)

            while (head := stream.in_head()) is not None:
                if isinstance(head, MultiplexInputData):
                    if batch_bytes and batch_bytes + len(head.data) > self._config.read_batch_max_bytes:
                        break
                    stream.pop_in()
                    for seg in ByteStreamBuffers.iter_segments(head.data):
                        if seg:
                            segs.append(seg)
                    batch_bytes += len(head.data)
                    consumed.append(head.cost)
                    delivered = True

                elif isinstance(head, MultiplexInputMessage):
                    stream.pop_in()
                    if head.cost:
                        consumed.append(head.cost)
                    if not flush_segs() or not self._feed(head.msg):
                        return consumed
                    delivered = True

                elif isinstance(head, MultiplexInputEnd):
                    stream.pop_in()
                    end = True
                    break

                else:
                    raise TypeError(head)

            if not flush_segs():
                return consumed

            # Typed messages may follow end-of-input (marked AfterFinalInput); batches of them carry no FlushInput.
            if delivered and not self._final_input_delivered and not self._feed(IoPipelineFlowMessages.FlushInput()):
                return consumed

            if end:
                self._final_input_delivered = True
                if not self._feed(IoPipelineMessages.FinalInput()):
                    return consumed

            if not self._auto_read:
                self._want_read = False

        return consumed

    ##
    # output

    def collect_output(self, claim: ta.Callable[[ta.Any], bool]) -> None:
        """
        Moves the child's terminal output into the stream's outbound queue, in order.

        Bytes, FlushOutput, ShutdownOutput, and FinalOutput are queued; Defer runs at once; ReadyForInput grants a read
        token; Await is held for the host to forward. Anything else is offered to `claim` (the protocol adapter) and
        queued as a typed message if claimed - otherwise it fails within the child, as an inbound Error there.
        """

        pipeline = self._pipeline
        if pipeline is None:
            return

        stream = self._stream
        while self.is_running and (msg := pipeline.output.poll()) is not None:
            if ByteStreamBuffers.can_bytes(msg):
                stream.push_out_data(msg)

            elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
                stream.push_out_fence('flush', msg)

            elif isinstance(msg, IoPipelineMessages.ShutdownOutput):
                self._output_ended = True
                stream.push_out_fence('shutdown', msg)

            elif isinstance(msg, IoPipelineMessages.FinalOutput):
                self._output_ended = True
                stream.push_out_fence('final', msg)

            elif isinstance(msg, IoPipelineMessages.Defer):
                try:
                    pipeline.run_deferred(msg)
                except Exception as e:  # noqa
                    self._fail(e)

            elif isinstance(msg, IoPipelineFlowMessages.ReadyForInput):
                if self._config.strict_input_flow and self._want_read:
                    self._fail(RuntimeError('duplicate ReadyForInput'))
                    break
                self._want_read = True

            elif isinstance(msg, AsyncIoPipelineMessages.Await):
                self._pending_awaits.append(msg)

            elif claim(msg):
                stream.push_out_message(msg)

            else:
                self._reject_output(msg)

    def _reject_output(self, msg: ta.Any) -> None:
        exc = UnclaimedOutputMultiplexError(msg)
        pipeline = check.not_none(self._pipeline)
        try:
            if isinstance(msg, IoPipelineMessages.Completable) and not msg.is_done():
                with pipeline.enter():
                    msg.set_failed(exc)
            pipeline.feed_in(IoPipelineMessages.Error(exc, 'outbound'))
        except Exception as e:  # noqa
            self._fail(e)

    def take_awaits(self) -> ta.List[AsyncIoPipelineMessages.Await]:
        out = self._pending_awaits
        self._pending_awaits = []
        return out

    def update_writability(self) -> None:
        """Announces writability transitions, derived from the stream's queued outbound bytes, into the child."""

        if not self.is_running or self._output_ended:
            return

        size = self._stream.out_bytes
        if self._writable:
            if size > self._config.write_high_watermark:
                self._writable = False
                self._feed(IoPipelineFlowMessages.PauseOutput())
        elif size <= self._config.write_low_watermark:
            self._writable = True
            self._feed(IoPipelineFlowMessages.ReadyForOutput())

    ##
    # completion

    def complete(self, msg: IoPipelineMessages.Completable, exc: ta.Optional[BaseException] = None) -> None:
        """Completes a child completable - a fence or an Await - inside the child, if it is still pending."""

        if msg.is_done() or (pipeline := self._pipeline) is None or not pipeline.is_ready:
            return
        try:
            with pipeline.enter():
                if exc is None:
                    msg.set_succeeded(None)
                else:
                    msg.set_failed(exc)
        except Exception as e:  # noqa
            self._fail(e)

    def complete_await(
            self,
            msg: AsyncIoPipelineMessages.Await,
            *,
            result: ta.Any = None,
            exc: ta.Optional[BaseException] = None,
    ) -> None:
        if msg.is_done() or (pipeline := self._pipeline) is None or not pipeline.is_ready:
            return
        try:
            with pipeline.enter():
                if exc is None:
                    msg.set_succeeded(result)
                else:
                    msg.set_failed(exc)
        except Exception as e:  # noqa
            self._fail(e)

    ##
    # teardown

    def finish(self) -> None:
        """Gracefully ends the child after its FinalOutput completed, as a driver does."""

        self._finished = True
        self._destroy()

    def abort(
            self,
            exc: BaseException,
            *,
            notify: bool = True,
    ) -> None:
        """
        Abortively ends the child: optionally reports `exc` to it as an inbound Error first, fails its queued fences
        with `exc`, and destroys it, which fails anything else pending.
        """

        if notify and self.is_running:
            self._feed(IoPipelineMessages.Error(exc))

        self._finished = True
        for item in self._stream.clear_out():
            if isinstance(msg := getattr(item, 'msg', None), IoPipelineMessages.Completable):
                self.complete(msg, exc)
        for awt in self.take_awaits():
            self.complete_await(awt, exc=exc)
        self._destroy()

    def _destroy(self) -> None:
        if (pipeline := self._pipeline) is None or not pipeline.is_ready:
            return
        try:
            pipeline.destroy()
        except Exception as e:  # noqa
            self._fail(e)
