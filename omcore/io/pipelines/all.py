# @om-recommended-import-alias "ipl"
from ... import lang as _lang


with _lang.auto_proxy_init(
        globals(),
        update_exports=True,
):
    ##

    from .bytes.buffering import (  # noqa
        InboundBytesBufferingIoPipelineHandler as InboundBytesBufferingHandler,
        OutboundBytesBufferingIoPipelineHandler as OutboundBytesBufferingHandler,
    )

    from .bytes.buffers import (  # noqa
        OutboundBytesBufferIoPipelineHandler as OutboundBytesBufferHandler,
    )

    from .bytes.decoders import (  # noqa
        UnicodeDecoderIoPipelineHandler as UnicodeDecoderHandler,

        DelimiterFrameDecoderIoPipelineHandler as DelimiterFrameDecoderHandler,

        BytesToMessageDecoderIoPipelineHandler as BytesToMessageDecoderHandler,
        FnBytesToMessageDecoderIoPipelineHandler as FnBytesToMessageDecoderHandler,

        BufferedBytesToMessageDecoderIoPipelineHandler as BufferedBytesToMessageDecoderHandler,
    )

    #

    from .drivers.asyncio.streams import (  # noqa
        PollAsyncioStreamIoPipelineDriver as PollAsyncioStreamDriver,
    )

    from .drivers.asyncio.hosts import (  # noqa
        AsyncioIoPipelineHost as AsyncioHost,
        AsyncioIoPipelineHostResolver as AsyncioHostResolver,
        LoopAsyncioIoPipelineHostResolver as LoopAsyncioHostResolver,
        SyncAsyncioIoPipelineHostResolver as SyncAsyncioHostResolver,
    )

    from .drivers.fdio.core import (  # noqa
        IoPipelineFdioDriver as FdioDriver,
        IoPipelineFdioTransport as FdioTransport,
    )

    from .drivers.fdio.descriptors import (  # noqa
        DescriptorIoPipelineFdioTransport as DescriptorFdioTransport,
    )

    from .drivers.fdio.duplex import (  # noqa
        IoPipelineDriverDuplexFdioHandler as DriverDuplexFdioHandler,
    )

    from .drivers.fdio.hosts import (  # noqa
        FdioIoPipelineHost as FdioHost,
    )

    from .drivers.fdio.pairs import (  # noqa
        IoPipelineDriverFdPairFdioHandlers as DriverFdPairFdioHandlers,
    )

    from .drivers.fdio.sockets import (  # noqa
        IoPipelineDriverSocketFdioHandler as DriverSocketFdioHandler,
        SocketIoPipelineFdioTransport as SocketFdioTransport,
    )

    from .drivers.metadata import (  # noqa
        DriverIoPipelineMetadata as DriverMetadata,
    )

    from .drivers.fdio.resolvers import (  # noqa
        ThreadedFdioIoPipelineHostResolver as ThreadedFdioHostResolver,
    )

    from .drivers.fdio.running import (  # noqa
        fdio_run_until,
    )

    from .drivers.pure.drivers import (  # noqa
        PureIoPipelineDriver as PureDriver,
    )

    from .drivers.pure.hosts import (  # noqa
        MemoryIoPipelineHost as MemoryHost,
        MemoryIoPipelineLink as MemoryLink,
        MemoryIoPipelineLinkEnd as MemoryLinkEnd,
    )

    from .drivers.pure.links import (  # noqa
        PureLink,
    )

    from .drivers.sync.core import (  # noqa
        SyncIoPipelineDriver as SyncDriver,
    )

    from .drivers.sync.fds import (  # noqa
        FdSyncIoPipelineDriver as FdSyncDriver,
    )

    from .drivers.sync.sockets import (  # noqa
        SocketSyncIoPipelineDriver as SocketSyncDriver,
    )

    from .drivers.types import (  # noqa
        IoPipelineDriverState as DriverState,
    )

    #

    from .flow.stub import (  # noqa
        StubIoPipelineFlowService as StubFlowService,
    )

    from .hosts.base import (  # noqa
        BaseIoPipelineHost as BaseHost,
        BlockingIoPipelineHostResolver as BlockingHostResolver,
    )

    from .hosts.types import (  # noqa
        IoPipelineHostError as HostError,
        ClosedIoPipelineHostError as ClosedHostError,
        ConnectIoPipelineHostError as ConnectHostError,
        ConnectTimeoutIoPipelineHostError as ConnectTimeoutHostError,
        ResolveIoPipelineHostError as ResolveHostError,
        ListenIoPipelineHostError as ListenHostError,

        IoPipelineHostTransportInfo as HostTransportInfo,

        IoPipelineHostHandle as HostHandle,
        IoPipelineHostedDriver as HostedDriver,
        IoPipelineHostedConnect as HostedConnect,
        IoPipelineHostedListener as HostedListener,

        IoPipelineHost as Host,
        IoPipelineHostResolver as HostResolver,
    )

    from .relays.handlers import (  # noqa
        RelayIoPipelineError as RelayError,
        AutoReadRelayIoPipelineError as AutoReadRelayError,
        UnmappedMessageRelayIoPipelineError as UnmappedMessageRelayError,
        PeerGoneRelayIoPipelineError as PeerGoneRelayError,

        IoPipelineRelay as Relay,
        IoPipelineRelayEndHandler as RelayEndHandler,
    )

    from .posting.types import (  # noqa
        ClosedIoPipelinePostingError as ClosedPostingError,

        IoPipelinePost as Post,

        IoPipelinePosting as Posting,
        IoPipelinePostingTarget as PostingTarget,
        TargetIoPipelinePostingService as TargetPostingService,
    )

    from .flow.types import (  # noqa
        IoPipelineFlowMessages as FlowMessages,

        IoPipelineFlow as Flow,
    )

    #

    from .handlers.decoders import (  # noqa
        MessageToMessageDecoderIoPipelineHandler as MessageToMessageDecoderHandler,

        FnMessageToMessageDecoderIoPipelineHandler as FnMessageToMessageDecoderHandler,
    )

    from .handlers.feedback import (  # noqa
        FeedbackInboundIoPipelineHandler as FeedbackHandler,
    )

    from .handlers.flatmap import (  # noqa
        FlatMapIoPipelineHandlerFn as FlatMapHandlerFn,
        FlatMapIoPipelineHandlerFns as FlatMapHandlerFns,

        FlatMapIoPipelineHandler as FlatMapHandler,

        InboundFlatMapIoPipelineHandler as InboundFlatMapHandler,
        OutboundFlatMapIoPipelineHandler as OutboundFlatMapHandler,
        DuplexFlatMapIoPipelineHandler as DuplexFlatMapHandler,

        FlatMapIoPipelineHandlers as FlatMapHandlers,
    )

    from .handlers.fns import (  # noqa
        IoPipelineHandlerFns as HandlerFns,

        FnIoPipelineHandler as FnHandler,
        InboundFnIoPipelineHandler as InboundFnHandler,
        OutboundFnIoPipelineHandler as OutboundFnHandler,
        DuplexFnIoPipelineHandler as DuplexFnHandler,

    )

    from .handlers.logs import (  # noqa
        LoggingIoPipelineHandler as LoggingHandler,
    )

    from .handlers.queues import (  # noqa
        QueueIoPipelineHandler as QueueHandler,
        InboundQueueIoPipelineHandler as InboundQueueHandler,
        OutboundQueueIoPipelineHandler as OutboundQueueHandler,
        DuplexQueueIoPipelineHandler as DuplexQueueHandler,
    )

    #

    from .sched.heap import (  # noqa
        HeapIoPipelineSchedulingService as HeapSchedulingService,
    )

    from .sched.timeouts import (  # noqa
        IoPipelineIdleState as IdleState,
        IdleStateIoPipelineEvent as IdleStateEvent,

        IdleStateIoPipelineHandler as IdleStateHandler,

        ReadTimeoutIoPipelineHandler as ReadTimeoutHandler,

        WriteTimeoutIoPipelineHandler as WriteTimeoutHandler,
    )

    from .sched.types import (  # noqa
        IoPipelineScheduling as Scheduling,
    )

    #

    from .ssl.handlers import (  # noqa
        SslIoPipelineHandler as SslHandler,
    )

    #

    from .asyncs import (  # noqa
        AsyncIoPipelineMessages as AsyncMessages,
    )

    from .core import (  # noqa
        IoPipelineHandlerFn as HandlerFn,

        IoPipelineMessages as Messages,

        IoPipelineHandlerNotification as HandlerNotification,
        IoPipelineHandlerNotifications as HandlerNotifications,

        IoPipelineHandlerRef as HandlerRef,
        IoPipelineHandlerRef_ as HandlerRef_,

        IoPipelineHandlerContext as HandlerContext,

        IoPipelineHandler as Handler,
        ShareableIoPipelineHandler as ShareableHandler,

        IoPipelineDirection as Direction,
        IoPipelineDirectionOrDuplex as DirectionOrDuplex,
        IoPipelineUpdate as Update,
        IoPipelineHandlerUpdate as HandlerUpdate,

        IoPipelineService as Service,
        IoPipelineServices as Services,

        IoPipelineMetadata as Metadata,
        IoPipelineMetadatas as Metadatas,

        IoPipelineMessageTap as MessageTap,
        IoPipelineMessageTapTuple as MessageTapTuple,
        ListIoPipelineMessageTap as ListMessageTap,

        IoPipeline as Pipeline,
    )

    from .errors import (  # noqa
        IoPipelineError as Error,
        TimeoutIoPipelineError as TimeoutError,  # noqa
        AbortedIoPipelineError as AbortedError,

        UnhandleableIoPipelineError as UnhandleableError,

        StateIoPipelineError as StateError,
        ContextInvalidatedIoPipelineError as ContextInvalidatedError,
        SawInitialInputIoPipelineError as SawInitialInputError,
        SawFinalInputIoPipelineError as SawFinalInputError,
        SawFinalOutputIoPipelineError as SawFinalOutputError,

        MessageIoPipelineError as MessageError,
        MessageNotPropagatedIoPipelineError as MessageNotPropagatedError,
        MessageReachedTerminalIoPipelineError as MessageReachedTerminalError,

        DecodingIoPipelineError as DecodingError,
        IncompleteDecodingIoPipelineError as IncompleteDecodingError,
        FlowControlValidationIoPipelineError as FlowControlValidationError,
    )

    from .yielding import (  # noqa
        IoPipelineYieldPolicy as YieldPolicy,

        CountingIoPipelineYieldPolicy as CountingYieldPolicy,

        NeverIoPipelineYieldPolicy as NeverYieldPolicy,
    )
