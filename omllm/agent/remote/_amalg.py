#!/usr/bin/env python3
# noinspection DuplicatedCode
# @om-lite
# @om-script
# @om-generated
# @om-amalg-output _main.py
# @om-git-diff-omit
# ruff: noqa: FURB188 PYI034 UP006 UP007 UP036 UP037 UP041 UP043 UP045 UP046
"""Entrypoint for the ephemeral remote agent payload launched through pyremote."""
import abc
import asyncio
import base64
import collections
import collections.abc
import contextlib
import dataclasses as dc
import datetime
import decimal
import enum
import errno
import fractions
import functools
import glob as glob_
import hashlib
import heapq
import inspect
import io
import itertools
import json
import logging
import math
import operator
import os
import os.path
import platform
import pwd
import queue
import select
import signal
import site
import socket
import stat as stat_
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import types
import typing as ta
import uuid
import weakref
import zlib


########################################


if sys.version_info < (3, 8):
    raise OSError(f'Requires python (3, 8), got {sys.version_info} from {sys.executable}')  # noqa


__om_amalg_sha1__ = 'f2779264723fe1e79bb6b3e450add15bb43d9ed1'


def __om_amalg__():  # noqa
    return dict(
        src_files=[
            dict(sha1='980c47ed90047f93bdcc9effe70d5249eeeb8eab', mod='omcore.asyncs.asyncio.streams', path='../../../omcore/asyncs/asyncio/streams.py'),  # noqa
            dict(sha1='74626aba05c6869daeede82de3b7fec562abe2a7', mod='omcore.io.pipelines.drivers.types', path='../../../omcore/io/pipelines/drivers/types.py'),  # noqa
            dict(sha1='422d99f57e249f77f8a06ee0a1baca69539d8ee7', mod='omcore.io.pipelines.errors', path='../../../omcore/io/pipelines/errors.py'),  # noqa
            dict(sha1='6b04cc2e4ba5461692128938a2bd5c261486746b', mod='omcore.io.streambufs.errors', path='../../../omcore/io/streambufs/errors.py'),  # noqa
            dict(sha1='a2fc3f3697fa8de5247761e9d554e70176f37aac', mod='omcore.lite.abstract', path='../../../omcore/lite/abstract.py'),  # noqa
            dict(sha1='6bd4b8ecc310ac1df19bafaf6eb85a1a284f65d5', mod='omcore.lite.asyncs', path='../../../omcore/lite/asyncs.py'),  # noqa
            dict(sha1='3d2d2c29ac4e1b0b86f34975beaa7d3ea43b3afe', mod='omcore.lite.bytes', path='../../../omcore/lite/bytes.py'),  # noqa
            dict(sha1='4f5466ce20a485428519e284b2a388a9ef8e4786', mod='omcore.lite.cached', path='../../../omcore/lite/cached.py'),  # noqa
            dict(sha1='62b9ccea94c4f7bcef97e7adae8674b8cb11d4af', mod='omcore.lite.check', path='../../../omcore/lite/check.py'),  # noqa
            dict(sha1='cb20ca2cb6f69b1519851282b4b8a3418b62103e', mod='omcore.lite.dataclasses', path='../../../omcore/lite/dataclasses.py'),  # noqa
            dict(sha1='27b12b6592403c010fb8b2a0af7c24238490d3a1', mod='omcore.lite.namespaces', path='../../../omcore/lite/namespaces.py'),  # noqa
            dict(sha1='9566bbf3530fd71fcc56321485216b592fae21e9', mod='omcore.lite.objects', path='../../../omcore/lite/objects.py'),  # noqa
            dict(sha1='64d51b5de91131349d56e4154ed235eb7fff4fd0', mod='omcore.lite.reflect', path='../../../omcore/lite/reflect.py'),  # noqa
            dict(sha1='1365cb6046eb929358e7c86a3fda20d95fd4a296', mod='omcore.lite.resources', path='../../../omcore/lite/resources.py'),  # noqa
            dict(sha1='b31b8e4b0e4fec4562ea3fa602e4ef2475e5fe7c', mod='omcore.lite.strings', path='../../../omcore/lite/strings.py'),  # noqa
            dict(sha1='9d6caabc7b31534109e3f2e249d21f8610c9c079', mod='omcore.lite.typing', path='../../../omcore/lite/typing.py'),  # noqa
            dict(sha1='bd87ff6a281e361cbab4f205802187b2080044e6', mod='omcore.logs.levels', path='../../../omcore/logs/levels.py'),  # noqa
            dict(sha1='03e6c5d0c4c25b51cdd225c029e652cdf741a51a', mod='omcore.logs.warnings', path='../../../omcore/logs/warnings.py'),  # noqa
            dict(sha1='e0ccddd9b2a4604e74eb9c67a1a85516b3796aec', mod='omcore.os.pyremote.core', path='../../../omcore/os/pyremote/core.py'),  # noqa
            dict(sha1='2ac241e59ff5a7aadd487f43ceb715f6c57cce95', mod='omcore.rpc.configs', path='../../../omcore/rpc/configs.py'),  # noqa
            dict(sha1='82cf262159e3d057c2c5398394a282b06887bb58', mod='omllm.agent.environment.remote.protocol', path='../environment/remote/protocol.py'),  # noqa
            dict(sha1='f6572b8c34185813301434c2b1243c2641f52eef', mod='omllm.agent.fs.common', path='../fs/common.py'),
            dict(sha1='6c881b9d48a55ce791b21dfdc7469c9507432ebd', mod='omcore.asyncs.asynclite.base', path='../../../omcore/asyncs/asynclite/base.py'),  # noqa
            dict(sha1='4b0061643d8b8818651695761faf4c19459a6421', mod='omcore.io.pipelines.core', path='../../../omcore/io/pipelines/core.py'),  # noqa
            dict(sha1='b4bb4d4128321c01c58f01bf20397731509e5927', mod='omcore.io.streambufs.types', path='../../../omcore/io/streambufs/types.py'),  # noqa
            dict(sha1='9b3f4ff802344313147f412f8f028922afc52b2f', mod='omcore.lite.marshal', path='../../../omcore/lite/marshal.py'),  # noqa
            dict(sha1='627d486a678e9dd2dfdba3acfc015a5aa026f95f', mod='omcore.lite.maybes', path='../../../omcore/lite/maybes.py'),  # noqa
            dict(sha1='f534acc131c6506d485f4d29e9597dfd3f0fb072', mod='omcore.lite.timeouts', path='../../../omcore/lite/timeouts.py'),  # noqa
            dict(sha1='c6a4599ad727fbee7c3d8eb1bce80846f8106079', mod='omcore.logs.infos', path='../../../omcore/logs/infos.py'),  # noqa
            dict(sha1='38429b7e804533da9a1dd356cf563ac4cff82aa2', mod='omcore.logs.metrics.base', path='../../../omcore/logs/metrics/base.py'),  # noqa
            dict(sha1='2e13388c65699c4aa89f32b78be8496b94fc40bb', mod='omcore.logs.protocols', path='../../../omcore/logs/protocols.py'),  # noqa
            dict(sha1='ad20a59ef95f12688de0f2e13e105eab6f149b75', mod='omcore.rpc.ids', path='../../../omcore/rpc/ids.py'),  # noqa
            dict(sha1='223d5eaf5fa37145ebc5a2dceef2a724cb21b20f', mod='omllm.agent.environment.ops', path='../environment/ops.py'),  # noqa
            dict(sha1='a1a612dc895e5944561dbfcd40e13209c0b9c302', mod='omllm.agent.fs.ops', path='../fs/ops.py'),
            dict(sha1='e9c931c9b1aafae94c5b5a6468cc218c74483692', mod='omllm.agent.fs.remote.protocol', path='../fs/remote/protocol.py'),  # noqa
            dict(sha1='995eba7586af040b569b0ff77fb5e3a2d132f18e', mod='omllm.core.processes.remote.protocol', path='../../core/processes/remote/protocol.py'),  # noqa
            dict(sha1='79905340353b28e51bcd02a62026787f41b731b9', mod='omcore.asyncs.asyncio.timeouts', path='../../../omcore/asyncs/asyncio/timeouts.py'),  # noqa
            dict(sha1='0d8b13a0e2db34d50c6dc05a9d9aa37c4d1a89b9', mod='omcore.asyncs.asynclite.asyncio.base', path='../../../omcore/asyncs/asynclite/asyncio/base.py'),  # noqa
            dict(sha1='2e9a88b28c93e6ba503f09e8ad16ed092e4696e6', mod='omcore.asyncs.asynclite.events', path='../../../omcore/asyncs/asynclite/events.py'),  # noqa
            dict(sha1='a8c275c24aa9b9ca6962ee042cb8514ff7b18641', mod='omcore.asyncs.asynclite.promises', path='../../../omcore/asyncs/asynclite/promises.py'),  # noqa
            dict(sha1='6e87c8b0feec5428ba4ed9ed0c871fa8ed88d036', mod='omcore.io.pipelines.asyncs', path='../../../omcore/io/pipelines/asyncs.py'),  # noqa
            dict(sha1='bf1d8923427f11b35a9ebde1e10944786c81262f', mod='omcore.io.pipelines.bytes.buffering', path='../../../omcore/io/pipelines/bytes/buffering.py'),  # noqa
            dict(sha1='e961e3afbbbba46fcf7f1907543b3dfd3ece764e', mod='omcore.io.pipelines.drivers.metadata', path='../../../omcore/io/pipelines/drivers/metadata.py'),  # noqa
            dict(sha1='53f7bc76bff67bc342e8156c2e2eb72fd160598b', mod='omcore.io.pipelines.flow.types', path='../../../omcore/io/pipelines/flow/types.py'),  # noqa
            dict(sha1='d79643be1e692e0ff2a3dc3b6daa330333406775', mod='omcore.io.pipelines.posting.types', path='../../../omcore/io/pipelines/posting/types.py'),  # noqa
            dict(sha1='823850ee7ea1ef8baffd94b4e80b6e3d7812933f', mod='omcore.io.pipelines.sched.types', path='../../../omcore/io/pipelines/sched/types.py'),  # noqa
            dict(sha1='aeaf1ba2f72c4fc8557de728e9688c0f0513a267', mod='omcore.io.streambufs.base', path='../../../omcore/io/streambufs/base.py'),  # noqa
            dict(sha1='cd3956ccfc59c3e60098225af3e7c19a8dc638f4', mod='omcore.io.streambufs.utils', path='../../../omcore/io/streambufs/utils.py'),  # noqa
            dict(sha1='529adb527492309bf8cde342271ac6ea2ebbf8a1', mod='omcore.logs.contexts', path='../../../omcore/logs/contexts.py'),  # noqa
            dict(sha1='7dd07873ddd48f99bda0cf3837e01c4c7c4cc96c', mod='omcore.logs.utils', path='../../../omcore/logs/utils.py'),  # noqa
            dict(sha1='3d6b40c040640a850360da97ae6400784af9b85b', mod='omcore.rpc.errors', path='../../../omcore/rpc/errors.py'),  # noqa
            dict(sha1='310aabd42641c20768a4b8627028d9a2a232be14', mod='omllm.agent.environment.local', path='../environment/local.py'),  # noqa
            dict(sha1='e388e9282a7a01d535c7691883351bb8d58d5d11', mod='omllm.agent.fs.local', path='../fs/local.py'),
            dict(sha1='ff50841e3d4ffa489e490d3403edd10b28485bff', mod='omcore.asyncs.asynclite.asyncio.events', path='../../../omcore/asyncs/asynclite/asyncio/events.py'),  # noqa
            dict(sha1='17452fd7825201c915b8df4114941d283de54d2d', mod='omcore.asyncs.asynclite.eventpromises', path='../../../omcore/asyncs/asynclite/eventpromises.py'),  # noqa
            dict(sha1='a68c9f698b62e02157af6864bfb14cdd5f22bc21', mod='omcore.io.pipelines.flow.stub', path='../../../omcore/io/pipelines/flow/stub.py'),  # noqa
            dict(sha1='db882a29d87bd38eb59c00140174a8af5e6325d1', mod='omcore.io.pipelines.sched.heap', path='../../../omcore/io/pipelines/sched/heap.py'),  # noqa
            dict(sha1='b3dff93590f5122ab3de67fc5ba0866d261ff9cf', mod='omcore.io.pipelines.sched.timeouts', path='../../../omcore/io/pipelines/sched/timeouts.py'),  # noqa
            dict(sha1='417d6f20e64dc1088a4a065a549b532bd9be389c', mod='omcore.io.streambufs.direct', path='../../../omcore/io/streambufs/direct.py'),  # noqa
            dict(sha1='5189edf484ef79bcea92069a55e0aafbdcff83bf', mod='omcore.io.streambufs.scanning', path='../../../omcore/io/streambufs/scanning.py'),  # noqa
            dict(sha1='9ee00768f53de350ac8d1f2b98917a9afcf885f5', mod='omcore.logs.base', path='../../../omcore/logs/base.py'),  # noqa
            dict(sha1='fb1e2d887248cc24b0463156836d9965a06c8ab6', mod='omcore.logs.std.records', path='../../../omcore/logs/std/records.py'),  # noqa
            dict(sha1='946120a610fe335aac9b7b301127511addff8eec', mod='omcore.rpc.messages', path='../../../omcore/rpc/messages.py'),  # noqa
            dict(sha1='f9a245b2fd6f7379116a5b4d5f0cedd082d7f506', mod='omcore.rpc.runtime', path='../../../omcore/rpc/runtime.py'),  # noqa
            dict(sha1='4ef65169c8706bd86c91a9ad92aae1fb9c2092df', mod='omcore.io.streambufs.framing', path='../../../omcore/io/streambufs/framing.py'),  # noqa
            dict(sha1='551e6377cf1152cb40536cc10c46a959dd940da7', mod='omcore.io.streambufs.segmented', path='../../../omcore/io/streambufs/segmented.py'),  # noqa
            dict(sha1='6b444494a0512f7b7ea2c93be5c4a9868deb7251', mod='omcore.logs.asyncs', path='../../../omcore/logs/asyncs.py'),  # noqa
            dict(sha1='144a96b3b190a5641f3b7cc2656d6ffa4e45b5a9', mod='omcore.logs.std.loggers', path='../../../omcore/logs/std/loggers.py'),  # noqa
            dict(sha1='4c3e5a1ee3fb7feb016a343a2f8f0afeca29586f', mod='omcore.rpc.keepalive', path='../../../omcore/rpc/keepalive.py'),  # noqa
            dict(sha1='9f1d9c52817a484d62eee8ec49b2b5abaa14e3e6', mod='omcore.io.pipelines.bytes.buffers', path='../../../omcore/io/pipelines/bytes/buffers.py'),  # noqa
            dict(sha1='44f0ed191a654bf66dcb03b99bf81b4dbb680ef3', mod='omcore.io.pipelines.bytes.decoders', path='../../../omcore/io/pipelines/bytes/decoders.py'),  # noqa
            dict(sha1='b51c2d4396854b515d29cee17f906d5cc47eb7f2', mod='omcore.logs.modules', path='../../../omcore/logs/modules.py'),  # noqa
            dict(sha1='6f1c8fc23d5b5cb8c80cddc0cc0190fab6e44712', mod='omcore.io.pipelines.drivers.asyncio.streams', path='../../../omcore/io/pipelines/drivers/asyncio/streams.py'),  # noqa
            dict(sha1='aeac0f77a018bb20d9dfbdc8ecd5538da333e3d2', mod='omcore.rpc.dispatch', path='../../../omcore/rpc/dispatch.py'),  # noqa
            dict(sha1='06854fb803e6ec9cbf87d4d76f44bccd180b5a54', mod='omcore.rpc.framing', path='../../../omcore/rpc/framing.py'),  # noqa
            dict(sha1='e93a3ce2e3c836ca431ec638faa921a22b94aad8', mod='omcore.rpc.session', path='../../../omcore/rpc/session.py'),  # noqa
            dict(sha1='7b010944f06cf59d6c3ece8ed6472c7888fa6c4d', mod='omcore.rpc.codecs', path='../../../omcore/rpc/codecs.py'),  # noqa
            dict(sha1='7e78b3a83293eb745623f0cc7ea2acaba2ad6b8a', mod='omcore.rpc.connection', path='../../../omcore/rpc/connection.py'),  # noqa
            dict(sha1='69d86f30730851b5d21cd38daa442d32cb5f2c0a', mod='omllm.agent.environment.remote.server', path='../environment/remote/server.py'),  # noqa
            dict(sha1='1c922f568c67fa82941c8833abb728f378e9ca4d', mod='omllm.agent.fs.remote.server', path='../fs/remote/server.py'),  # noqa
            dict(sha1='ca8a8fb82ebe6265b38e35e4e375a483377e7b74', mod='omcore.rpc.specs', path='../../../omcore/rpc/specs.py'),  # noqa
            dict(sha1='cf016bde329cc9d87ae5940551d04f8c9d885565', mod='omllm.core.processes.remote.server', path='../../core/processes/remote/server.py'),  # noqa
            dict(sha1='3558e03f33fcb35f5afc06f23103bec306cef809', mod='omcore.rpc.asyncio', path='../../../omcore/rpc/asyncio.py'),  # noqa
            dict(sha1='176775e8c00eaef01d437c80ac93e9f979da37aa', mod='omllm.agent.remote.server', path='server.py'),
            dict(sha1='8bad618c4bae0d2120cd99b80e8fd82967ff086b', mod='-', path='_main.py'),
        ],
    )


########################################


# ../../../omcore/lite/abstract.py
T = ta.TypeVar('T')

# ../../../omcore/lite/bytes.py
Bytes = ta.Union[bytes, bytearray]  # ta.TypeAlias
BytesLike = ta.Union[Bytes, memoryview]  # ta.TypeAlias

# ../../../omcore/lite/cached.py
CallableT = ta.TypeVar('CallableT', bound=ta.Callable)

# ../../../omcore/lite/check.py
SizedT = ta.TypeVar('SizedT', bound=ta.Sized)
CheckMessage = ta.Union[str, ta.Callable[..., ta.Optional[str]], ta.Type[Exception], None]  # ta.TypeAlias
CheckLateConfigureFn = ta.Callable[['Checks'], None]  # ta.TypeAlias
CheckOnRaiseFn = ta.Callable[[Exception], None]  # ta.TypeAlias
CheckExceptionFactory = ta.Callable[..., Exception]  # ta.TypeAlias
CheckArgsRenderer = ta.Callable[..., ta.Optional[str]]  # ta.TypeAlias

# ../../../omcore/lite/typing.py
A0 = ta.TypeVar('A0')
A1 = ta.TypeVar('A1')
A2 = ta.TypeVar('A2')

# ../../../omcore/logs/levels.py
LogLevel = int  # ta.TypeAlias

# ../../../omcore/asyncs/asynclite/base.py
AsyncliteCloseableT = ta.TypeVar('AsyncliteCloseableT', bound='AsyncliteCloseable')

# ../../../omcore/io/pipelines/core.py
F = ta.TypeVar('F')
IoPipelineHandlerFn = ta.Callable[['IoPipelineHandlerContext', F], T]  # ta.TypeAlias
IoPipelineHandlerT = ta.TypeVar('IoPipelineHandlerT', bound='IoPipelineHandler')
ShareableIoPipelineHandlerT = ta.TypeVar('ShareableIoPipelineHandlerT', bound='ShareableIoPipelineHandler')  # noqa
IoPipelineMetadataT = ta.TypeVar('IoPipelineMetadataT', bound='IoPipelineMetadata')

# ../../../omcore/lite/maybes.py
U = ta.TypeVar('U')

# ../../../omcore/lite/timeouts.py
TimeoutLike = ta.Union['Timeout', ta.Type['Timeout.DEFAULT'], ta.Iterable['TimeoutLike'], 'CanFloat', float, int, bool, None]  # ta.TypeAlias  # noqa

# ../../../omcore/logs/infos.py
LoggingMsgFn = ta.Callable[[], ta.Union[str, tuple]]  # ta.TypeAlias
LoggingExcInfoTuple = ta.Tuple[ta.Type[BaseException], BaseException, ta.Optional[types.TracebackType]]  # ta.TypeAlias
LoggingExcInfo = ta.Union[BaseException, LoggingExcInfoTuple]  # ta.TypeAlias
LoggingExcInfoArg = ta.Union[LoggingExcInfo, bool, None]  # ta.TypeAlias
LoggingContextInfo = ta.Any  # ta.TypeAlias

# ../../../omcore/rpc/ids.py
RpcIdCreatorLike = ta.Union['RpcIdCreator', ta.Callable[[], ta.Any]]  # ta.TypeAlias

# ../../../omcore/asyncs/asyncio/timeouts.py
AwaitableT = ta.TypeVar('AwaitableT', bound=ta.Awaitable)

# ../../../omcore/io/streambufs/utils.py
CanByteStreamBuffer = ta.Union[BytesLike, 'ByteStreamBufferLike']  # ta.TypeAlias

# ../../../omcore/logs/contexts.py
LoggingContextInfoT = ta.TypeVar('LoggingContextInfoT', bound=LoggingContextInfo)

# ../../../omcore/rpc/messages.py
RpcResponseMessage = ta.Union['RpcResultMessage', 'RpcErrorMessage']  # ta.TypeAlias

# ../../../omcore/rpc/dispatch.py
RpcMethodFn = ta.Callable[[ta.Any], ta.Awaitable[ta.Any]]  # ta.TypeAlias  # params -> result
RpcInlineNotificationFn = ta.Callable[[ta.Any], None]  # ta.TypeAlias  # params -> None

# ../../../omcore/rpc/session.py
RpcSessionState = ta.Literal['new', 'open', 'closing', 'closed']  # ta.TypeAlias

# ../../../omcore/rpc/connection.py
BaseRpcConnectionT = ta.TypeVar('BaseRpcConnectionT', bound='BaseRpcConnection')
BaseSyncRpcConnectionT = ta.TypeVar('BaseSyncRpcConnectionT', bound='BaseSyncRpcConnection')
RpcConnectionCloseCallback = ta.Callable[[ta.Any], None]  # ta.TypeAlias
RpcNotificationErrorHandler = ta.Callable[['RpcNotificationMessage', BaseException], None]  # ta.TypeAlias
RpcTimeoutArg = ta.Union[float, None, ta.Type['RpcUnspecified']]  # ta.TypeAlias


########################################
# ../../../../omcore/asyncs/asyncio/streams.py


##


ASYNCIO_DEFAULT_BUFFER_LIMIT = 2 ** 16


async def asyncio_open_stream_reader(
        f: ta.IO,
        loop: ta.Any = None,
        *,
        limit: int = ASYNCIO_DEFAULT_BUFFER_LIMIT,
) -> asyncio.StreamReader:
    if loop is None:
        loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader(limit=limit, loop=loop)
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader, loop=loop),
        f,
    )

    return reader


class AsyncioWritePipeProtocol(asyncio.streams.FlowControlMixin):
    """
    The protocol behind `asyncio_open_stream_writer`: flow control, plus the close waiter that
    `StreamWriter.wait_closed` awaits through the protocol's `_get_close_waiter` hook. A bare `FlowControlMixin` raises
    NotImplementedError there.
    """

    def __init__(self, loop: ta.Any = None) -> None:
        super().__init__(loop=loop)

        self._close_waiter: asyncio.Future = self._loop.create_future()  # type: ignore[attr-defined]

    def connection_lost(self, exc: ta.Optional[Exception]) -> None:
        if not self._close_waiter.done():
            if exc is None:
                self._close_waiter.set_result(None)
            else:
                self._close_waiter.set_exception(exc)
                # Marked retrieved: a failed close nobody waits for is not an unhandled error.
                self._close_waiter.exception()
        super().connection_lost(exc)

    def _get_close_waiter(self, stream: asyncio.StreamWriter) -> asyncio.Future:
        return self._close_waiter


async def asyncio_open_stream_writer(
        f: ta.IO,
        loop: ta.Any = None,
) -> asyncio.StreamWriter:
    if loop is None:
        loop = asyncio.get_running_loop()

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: AsyncioWritePipeProtocol(loop=loop),
        f,
    )

    return asyncio.streams.StreamWriter(
        writer_transport,
        writer_protocol,
        None,
        loop,
    )


########################################
# ../../../../omcore/io/pipelines/drivers/types.py


##


class IoPipelineDriverState(enum.Enum):
    """
    Transport-facing lifecycle shared by I/O pipeline drivers.

    DRAINING means the transport terminal has accepted FinalOutput and is finishing output that preceded it. Explicit
    close remains abortive in RUNNING or DRAINING. CLOSED records successful graceful or explicit closure; FAILED is a
    terminal record of transport, pipeline-driving, or teardown failure.
    """

    NEW = 'new'
    RUNNING = 'running'
    DRAINING = 'draining'
    CLOSED = 'closed'
    FAILED = 'failed'


########################################
# ../../../../omcore/io/pipelines/errors.py


##


class IoPipelineError(Exception):
    pass


class TimeoutIoPipelineError(IoPipelineError, TimeoutError):
    pass


class AbortedIoPipelineError(IoPipelineError):
    pass


class UnsupportedIoPipelineError(IoPipelineError):
    """An operation is not supported by the transport or component asked to perform it."""


##


class UnhandleableIoPipelineError(IoPipelineError):
    pass


##
# state


class StateIoPipelineError(IoPipelineError):
    pass


class ContextInvalidatedIoPipelineError(StateIoPipelineError):
    pass


class SawInitialInputIoPipelineError(StateIoPipelineError):
    pass


class SawFinalInputIoPipelineError(StateIoPipelineError):
    pass


class SawFinalOutputIoPipelineError(StateIoPipelineError):
    pass


class SawShutdownOutputIoPipelineError(StateIoPipelineError):
    pass


##
# messages


@dc.dataclass()
class MessageIoPipelineError(IoPipelineError):
    @ta.final
    @dc.dataclass(frozen=True)
    class Item:
        direction: ta.Literal['inbound', 'outbound']
        msg: ta.Any

        # _: dc.KW_ONLY

        last_seen: ta.Optional[ta.Any] = None

        def __repr__(self) -> str:
            return (
                f'{self.__class__.__name__}('
                f'{self.direction!r}'
                f', {self.msg!r}' +
                (f', last_seen={self.last_seen!r}' if self.last_seen is not None else '') +
                ')'
            )

    items: ta.Sequence[Item]

    @classmethod
    def new(
            cls,
            *,
            inbound: ta.Optional[ta.Sequence[ta.Any]] = None,
            inbound_with_last_seen: ta.Optional[ta.Sequence[ta.Tuple[ta.Any, ta.Any]]] = None,
            outbound: ta.Optional[ta.Sequence[ta.Any]] = None,
            outbound_with_last_seen: ta.Optional[ta.Sequence[ta.Tuple[ta.Any, ta.Any]]] = None,
    ) -> 'MessageIoPipelineError':
        items: ta.List[MessageIoPipelineError.Item] = []
        for msg in inbound or ():
            items.append(MessageIoPipelineError.Item('inbound', msg))
        for msg, last_seen in inbound_with_last_seen or ():
            items.append(MessageIoPipelineError.Item('inbound', msg, last_seen=last_seen))
        for msg in outbound or ():
            items.append(MessageIoPipelineError.Item('outbound', msg))
        for msg, last_seen in outbound_with_last_seen or ():
            items.append(MessageIoPipelineError.Item('outbound', msg, last_seen=last_seen))
        return cls(items)

    @classmethod
    def new_single(
            cls,
            direction: ta.Literal['inbound', 'outbound'],
            msg: ta.Any,
            *,
            last_seen: ta.Optional[ta.Any] = None,
    ) -> 'MessageIoPipelineError':
        return cls([
            MessageIoPipelineError.Item(
                direction,
                msg,
                last_seen=last_seen,
            ),
        ])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.items!r})'


@dc.dataclass(repr=False)
class MessageNotPropagatedIoPipelineError(MessageIoPipelineError, UnhandleableIoPipelineError):
    pass


@dc.dataclass(repr=False)
class MessageReachedTerminalIoPipelineError(MessageIoPipelineError, UnhandleableIoPipelineError):
    pass


##
# misc (TODO: move/cleanup)


class DecodingIoPipelineError(IoPipelineError):
    pass


class IncompleteDecodingIoPipelineError(DecodingIoPipelineError):
    pass


class FlowControlValidationIoPipelineError(IoPipelineError):
    pass


########################################
# ../../../../omcore/io/streambufs/errors.py


##


class ByteStreamBufferError(Exception):
    pass


#


class NeedMoreDataByteStreamBufferError(ByteStreamBufferError):
    """
    Raised when an operation cannot complete because insufficient bytes are currently buffered.

    This is intentionally distinct from EOF: it means "try again after feeding more bytes".
    """


#


class LimitByteStreamBufferError(ValueError, ByteStreamBufferError):
    """
    Base class for buffer/framing limit violations.

    Subclasses inherit from ValueError so existing tests expecting ValueError continue to pass.
    """


class BufferTooLargeByteStreamBufferError(LimitByteStreamBufferError):
    """
    Buffered data exceeded a configured cap without finding a boundary that would allow progress.

    Typically indicates an unframed stream, a missing delimiter, or an upstream not enforcing limits.
    """


class FrameTooLargeByteStreamBufferError(LimitByteStreamBufferError):
    """A single decoded frame (payload before its boundary delimiter/length) exceeded a configured max size."""


#


class StateByteStreamBufferError(RuntimeError, ByteStreamBufferError):
    """
    Base class for invalid buffer state transitions (e.g., coalescing while a reservation is outstanding).

    Subclasses inherit from RuntimeError so existing tests expecting RuntimeError continue to pass.
    """


class OutstandingReserveByteStreamBufferError(StateByteStreamBufferError):
    """A reserve() is outstanding; an operation requiring stable storage cannot proceed."""


class NoOutstandingReserveByteStreamBufferError(StateByteStreamBufferError):
    """commit() was called without a preceding reserve()."""


########################################
# ../../../../omcore/lite/abstract.py


##


_ABSTRACT_METHODS_ATTR = '__abstractmethods__'
_IS_ABSTRACT_METHOD_ATTR = '__isabstractmethod__'


def is_abstract_method(obj: ta.Any) -> bool:
    return bool(getattr(obj, _IS_ABSTRACT_METHOD_ATTR, False))


def compute_abstract_methods(cls: type) -> ta.FrozenSet[str]:
    # ~> https://github.com/python/cpython/blob/f3476c6507381ca860eec0989f53647b13517423/Modules/_abc.c#L358

    # Stage 1: direct abstract methods

    abstracts = {
        a
        # Get items as a list to avoid mutation issues during iteration
        for a, v in list(cls.__dict__.items())
        if is_abstract_method(v)
    }

    # Stage 2: inherited abstract methods

    for base in cls.__bases__:
        # Get __abstractmethods__ from base if it exists
        if (base_abstracts := getattr(base, _ABSTRACT_METHODS_ATTR, None)) is None:
            continue

        # Iterate over abstract methods in base
        for key in base_abstracts:
            # Check if this class has an attribute with this name
            try:
                value = getattr(cls, key)
            except AttributeError:
                # Attribute not found in this class, skip
                continue

            # Check if it's still abstract
            if is_abstract_method(value):
                abstracts.add(key)

    return frozenset(abstracts)


def update_abstracts(cls: ta.Type[T], *, force: bool = False) -> ta.Type[T]:
    if not force and not hasattr(cls, _ABSTRACT_METHODS_ATTR):
        # Per stdlib: We check for __abstractmethods__ here because cls might by a C implementation or a python
        # implementation (especially during testing), and we want to handle both cases.
        return cls

    abstracts = compute_abstract_methods(cls)
    setattr(cls, _ABSTRACT_METHODS_ATTR, abstracts)
    return cls


#


class AbstractTypeError(TypeError):
    pass


_FORCE_ABSTRACT_ATTR = '__forceabstract__'


class Abstract:
    """
    Different from, but interoperable with, abc.ABC / abc.ABCMeta:

     - This raises AbstractTypeError during class creation, not instance instantiation - unless Abstract or abc.ABC are
       explicitly present in the class's direct bases.
     - This will forbid instantiation of classes with Abstract in their direct bases even if there are no
       abstractmethods left on the class.
     - This is a mixin, not a metaclass.
     - As it is not an ABCMeta, this does not support virtual base classes. As a result, operations like `isinstance`
       and `issubclass` are ~7x faster.
     - It additionally enforces a base class order of (Abstract, abc.ABC) to preemptively prevent common mro conflicts.

    If not mixed-in with an ABCMeta, it will update __abstractmethods__ itself.
    """

    __slots__ = ()

    __abstractmethods__: ta.ClassVar[ta.FrozenSet[str]] = frozenset()

    #

    def __forceabstract__(self):
        raise TypeError

    # This is done manually, rather than through @abc.abstractmethod, to mask it from static analysis.
    setattr(__forceabstract__, _IS_ABSTRACT_METHOD_ATTR, True)

    #

    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        setattr(
            cls,
            _FORCE_ABSTRACT_ATTR,
            getattr(Abstract, _FORCE_ABSTRACT_ATTR) if Abstract in cls.__bases__ else False,
        )

        super().__init_subclass__(**kwargs)

        if not (Abstract in cls.__bases__ or abc.ABC in cls.__bases__):
            if ams := compute_abstract_methods(cls):
                amd = {
                    a: mcls
                    for mcls in cls.__mro__[::-1]
                    for a in ams
                    if a in mcls.__dict__
                }

                raise AbstractTypeError(
                    f'Cannot subclass abstract class {cls.__name__} with abstract methods: ' +
                    ', '.join(sorted([
                        '.'.join([
                            *([
                                *([m] if (m := getattr(c, '__module__')) else []),
                                getattr(c, '__qualname__', getattr(c, '__name__')),
                            ] if c is not None else '?'),
                            a,
                        ])
                        for a in ams
                        for c in [amd.get(a)]
                    ])),
                )

        xbi = (Abstract, abc.ABC)  # , ta.Generic ?
        bis = [(cls.__bases__.index(b), b) for b in xbi if b in cls.__bases__]
        if bis != sorted(bis):
            raise TypeError(
                f'Abstract subclass {cls.__name__} must have proper base class order of '
                f'({", ".join(getattr(b, "__name__") for b in xbi)}), got: '
                f'({", ".join(getattr(b, "__name__") for _, b in sorted(bis))})',
            )

        if not isinstance(cls, abc.ABCMeta):
            update_abstracts(cls, force=True)


########################################
# ../../../../omcore/lite/asyncs.py


##


async def opt_await(aw: ta.Optional[ta.Awaitable[T]]) -> ta.Optional[T]:
    return (await aw if aw is not None else None)


async def async_list(ai: ta.AsyncIterable[T]) -> ta.List[T]:
    return [v async for v in ai]


async def async_enumerate(ai: ta.AsyncIterable[T]) -> ta.AsyncIterable[ta.Tuple[int, T]]:
    i = 0
    async for e in ai:
        yield (i, e)
        i += 1


##


def as_async(fn: ta.Callable[..., T], *, wrap: bool = False) -> ta.Callable[..., ta.Awaitable[T]]:
    async def inner(*args, **kwargs):
        return fn(*args, **kwargs)

    return functools.wraps(fn)(inner) if wrap else inner


##


class SyncAwaitCoroutineNotTerminatedError(Exception):
    pass


def sync_await(aw: ta.Awaitable[T]) -> T:
    """
    Allows for the synchronous execution of async functions which will never actually *externally* await anything. These
    functions are allowed to await any number of other functions - including contextmanagers and generators - so long as
    nothing ever actually 'leaks' out of the function, presumably to an event loop.
    """

    ret = missing = object()

    async def thunk():
        nonlocal ret

        ret = await aw

    cr = thunk()
    try:
        try:
            cr.send(None)
        except StopIteration:
            pass

        if ret is missing or cr.cr_await is not None or cr.cr_running:  # type: ignore[attr-defined]
            raise SyncAwaitCoroutineNotTerminatedError('Not terminated')

    finally:
        cr.close()

    return ta.cast(T, ret)


#


def sync_aiter(ai: ta.AsyncIterator[T]) -> ta.Iterator[T]:
    while True:
        try:
            o = sync_await(ai.__anext__())
        except StopAsyncIteration:
            break
        yield o


def sync_async_list(ai: ta.AsyncIterable[T]) -> ta.List[T]:
    """
    Uses `sync_await` to synchronously read the full contents of a function call returning an async iterator, given that
    the function never externally awaits anything.
    """

    lst: ta.Optional[ta.List[T]] = None

    async def inner():
        nonlocal lst

        lst = [v async for v in ai]

    sync_await(inner())

    if not isinstance(lst, list):
        raise TypeError(lst)

    return lst


#


@ta.final
class SyncAwaitContextManager(ta.Generic[T]):
    def __init__(self, acm: ta.AsyncContextManager[T]) -> None:
        self._acm = acm

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._acm!r})'

    def __enter__(self) -> T:
        return sync_await(self._acm.__aenter__())

    def __exit__(self, exc_type, exc_val, exc_tb):
        return sync_await(self._acm.__aexit__(exc_type, exc_val, exc_tb))


sync_async_with = SyncAwaitContextManager


##


@ta.final
class SyncToAsyncContextManager(ta.Generic[T]):
    def __init__(self, cm: ta.ContextManager[T]) -> None:
        self._cm = cm

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._cm!r})'

    async def __aenter__(self) -> T:
        return self._cm.__enter__()

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        return self._cm.__exit__(exc_type, exc_value, traceback)


as_async_context_manager = SyncToAsyncContextManager


########################################
# ../../../../omcore/lite/bytes.py


##


BYTES_TYPES: ta.Tuple[ta.Union[ta.Type[bytes], ta.Type[bytearray]], ...] = (
    bytes,
    bytearray,
)

BYTES_LIKE_TYPES: ta.Tuple[ta.Union[ta.Type[bytes], ta.Type[bytearray], ta.Type[memoryview]], ...] = (
    *BYTES_TYPES,
    memoryview,
)


##


def bytes_like_to_bytes(bl: BytesLike, /) -> Bytes:
    if isinstance(bl, BYTES_TYPES):
        return bl

    return memoryview_to_bytes(bl)  # type: ignore[arg-type]


def bytes_like_to_bytes_strict(bl: BytesLike, /) -> bytes:
    if isinstance(bl, bytes):
        return bl

    if isinstance(bl, bytearray):
        return bytes(bl)

    return memoryview_to_bytes_strict(bl)


#


def memoryview_to_bytes(mv: memoryview, /) -> Bytes:
    if (mv.c_contiguous and ((ot := type(obj := mv.obj)) is bytes or ot is bytearray or isinstance(obj, BYTES_TYPES)) and len(mv) == len(obj)):  # type: ignore[arg-type]  # noqa
        return obj  # type: ignore[return-value]

    return mv.tobytes()


def memoryview_to_bytes_strict(mv: memoryview, /) -> bytes:
    if (mv.c_contiguous and ((ot := type(obj := mv.obj)) is bytes or isinstance(obj, bytes)) and len(mv) == len(obj)):  # type: ignore[arg-type]  # noqa
        return obj  # type: ignore[return-value]

    return mv.tobytes()


########################################
# ../../../../omcore/lite/cached.py


##


class _AbstractCachedNullary:
    def __init__(self, fn):
        super().__init__()

        self._fn = fn
        self._value = self._missing = object()
        functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):  # noqa
        raise TypeError

    def __get__(self, instance, owner=None):  # noqa
        if instance is None:
            return self
        bound = instance.__dict__[self._fn.__name__] = self.__class__(self._fn.__get__(instance, owner))
        return bound


##


class _CachedNullary(_AbstractCachedNullary):
    def __call__(self, *args, **kwargs):  # noqa
        if self._value is self._missing:
            self._value = self._fn()
        return self._value


def cached_nullary(fn: CallableT) -> CallableT:
    return _CachedNullary(fn)  # type: ignore


def static_init(fn: CallableT) -> CallableT:
    fn = cached_nullary(fn)
    fn()
    return fn


##


class _AsyncCachedNullary(_AbstractCachedNullary):
    async def __call__(self, *args, **kwargs):
        if self._value is self._missing:
            self._value = await self._fn()
        return self._value


def async_cached_nullary(fn):  # ta.Callable[..., T]) -> ta.Callable[..., T]:
    return _AsyncCachedNullary(fn)


##


cached_property = functools.cached_property


class _cached_property:  # noqa
    """Backported to pick up https://github.com/python/cpython/commit/056dfc71dce15f81887f0bd6da09d6099d71f979 ."""

    def __init__(self, func):
        self.func = func
        self.attrname = None  # noqa
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__

    _NOT_FOUND = object()

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name  # noqa
        elif name != self.attrname:
            raise TypeError(
                f'Cannot assign the same cached_property to two different names ({self.attrname!r} and {name!r}).',
            )

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError('Cannot use cached_property instance without calling __set_name__ on it.')

        try:
            cache = instance.__dict__
        except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
            raise TypeError(
                f"No '__dict__' attribute on {type(instance).__name__!r} instance to cache {self.attrname!r} property.",
            ) from None

        val = cache.get(self.attrname, self._NOT_FOUND)

        if val is self._NOT_FOUND:
            val = self.func(instance)
            try:
                cache[self.attrname] = val
            except TypeError:
                raise TypeError(
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance does not support item "
                    f"assignment for caching {self.attrname!r} property.",
                ) from None

        return val


globals()['cached_property'] = _cached_property


########################################
# ../../../../omcore/lite/check.py
"""
TODO:
 - def maybe(v: lang.Maybe[T])
 - def not_ ?
 - ** class @dataclass Raise - user message should be able to be an exception type or instance or factory
"""


##


class Checks:
    def __init__(self) -> None:
        super().__init__()

        self._config_lock = threading.RLock()
        self._on_raise_fns: ta.Sequence[CheckOnRaiseFn] = []
        self._exception_factory: CheckExceptionFactory = Checks.default_exception_factory
        self._args_renderer: ta.Optional[CheckArgsRenderer] = None
        self._late_configure_fns: ta.Sequence[CheckLateConfigureFn] = []

    #

    def register_on_raise(self, fn: CheckOnRaiseFn) -> None:
        with self._config_lock:
            self._on_raise_fns = [*self._on_raise_fns, fn]

    def unregister_on_raise(self, fn: CheckOnRaiseFn) -> None:
        with self._config_lock:
            self._on_raise_fns = [e for e in self._on_raise_fns if e != fn]

    #

    def register_on_raise_breakpoint_if_env_var_set(self, key: str) -> None:
        import os

        def on_raise(exc: Exception) -> None:  # noqa
            if key in os.environ:
                breakpoint()  # noqa

        self.register_on_raise(on_raise)

    #

    @staticmethod
    def default_exception_factory(exc_cls: ta.Type[Exception], *args, **kwargs) -> Exception:
        return exc_cls(*args, **kwargs)  # noqa

    def set_exception_factory(self, factory: CheckExceptionFactory) -> None:
        self._exception_factory = factory

    def set_args_renderer(self, renderer: ta.Optional[CheckArgsRenderer]) -> None:
        self._args_renderer = renderer

    #

    def register_late_configure(self, fn: CheckLateConfigureFn) -> None:
        with self._config_lock:
            self._late_configure_fns = [*self._late_configure_fns, fn]

    def _late_configure(self) -> None:
        if not self._late_configure_fns:
            return

        with self._config_lock:
            if not (lc := self._late_configure_fns):
                return

            for fn in lc:
                fn(self)

            self._late_configure_fns = []

    #

    class _ArgsKwargs:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    def _raise(
            self,
            exception_type: ta.Type[Exception],
            default_message: str,
            message: CheckMessage,
            ak: _ArgsKwargs = _ArgsKwargs(),
            *,
            render_fmt: ta.Optional[str] = None,
    ) -> ta.NoReturn:
        self._late_configure()

        exc_args: tuple = ()

        if isinstance(message, type):
            exception_type = message

        else:
            if callable(message):
                message = ta.cast(ta.Callable, message)(*ak.args, **ak.kwargs)
                if isinstance(message, tuple):
                    message, *exc_args = message  # type: ignore

            if message is None:
                message = default_message

            if render_fmt is not None and (af := self._args_renderer) is not None:
                rendered_args = af(render_fmt, *ak.args)
                if rendered_args is not None:
                    message = f'{message} : {rendered_args}'

            exc_args = (message, *exc_args)

        exc = self._exception_factory(
            exception_type,
            *exc_args,
            *ak.args,
            **ak.kwargs,
        )

        for fn in self._on_raise_fns:
            fn(exc)

        raise exc

    #

    def _unpack_isinstance_spec(self, spec: ta.Any) -> ta.Any:
        if spec == ta.Any:
            return object
        if spec is None:
            return None.__class__
        if not isinstance(spec, tuple):
            return spec
        if ta.Any in spec:
            return object
        if None in spec:
            spec = tuple(filter(None, spec)) + (None.__class__,)  # noqa
        return spec

    @ta.overload
    def isinstance(self, v: ta.Any, spec: ta.Type[T], msg: CheckMessage = None, /) -> T: ...

    @ta.overload
    def isinstance(self, v: ta.Any, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Any: ...

    def isinstance(self, v, spec, msg=None):
        if not isinstance(v, spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)):  # noqa
            self._raise(
                TypeError,
                'Must be instance',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='not isinstance(%s, %s)',
            )

        return v

    @ta.overload
    def of_isinstance(self, spec: ta.Type[T], msg: CheckMessage = None, /) -> ta.Callable[[ta.Any], T]: ...

    @ta.overload
    def of_isinstance(self, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Callable[[ta.Any], ta.Any]: ...

    def of_isinstance(self, spec, msg=None, /):
        spec = spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)  # noqa

        def inner(v):
            return self.isinstance(v, spec, msg)

        return inner

    def cast(self, v: ta.Any, cls: ta.Type[T], msg: CheckMessage = None, /) -> T:
        if not isinstance(v, cls):
            self._raise(
                TypeError,
                'Must be instance',
                msg,
                Checks._ArgsKwargs(v, cls),
            )

        return v

    def of_cast(self, cls: ta.Type[T], msg: CheckMessage = None, /) -> ta.Callable[[T], T]:
        def inner(v):
            return self.cast(v, cls, msg)

        return inner

    def not_isinstance(self, v: T, spec: ta.Any, msg: CheckMessage = None, /) -> T:  # noqa
        if isinstance(v, spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)):  # noqa
            self._raise(
                TypeError,
                'Must not be instance',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='isinstance(%s, %s)',
            )

        return v

    def of_not_isinstance(self, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Callable[[T], T]:
        spec = spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)  # noqa

        def inner(v):
            return self.not_isinstance(v, spec, msg)

        return inner

    ##

    def issubclass(self, v: ta.Type[T], spec: ta.Any, msg: CheckMessage = None, /) -> ta.Type[T]:  # noqa
        if not issubclass(v, spec):
            self._raise(
                TypeError,
                'Must be subclass',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='not issubclass(%s, %s)',
            )

        return v

    def not_issubclass(self, v: ta.Type[T], spec: ta.Any, msg: CheckMessage = None, /) -> ta.Type[T]:
        if issubclass(v, spec):
            self._raise(
                TypeError,
                'Must not be subclass',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='issubclass(%s, %s)',
            )

        return v

    def not_issubclass_except_nameerror(self, v: ta.Type[T], spec: ta.Callable[[], type], msg: CheckMessage = None, /) -> ta.Type[T]:  # noqa
        try:
            c = spec()
        except NameError:
            return v

        if issubclass(v, c):
            self._raise(
                TypeError,
                'Must not be subclass',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='issubclass(%s, %s)',
            )

        return v

    #

    def in_(self, v: T, c: ta.Container[T], msg: CheckMessage = None, /) -> T:
        if v not in c:
            self._raise(
                ValueError,
                'Must be in',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='%s not in %s',
            )

        return v

    def not_in(self, v: T, c: ta.Container[T], msg: CheckMessage = None, /) -> T:
        if v in c:
            self._raise(
                ValueError,
                'Must not be in',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='%s in %s',
            )

        return v

    def empty(self, v: SizedT, msg: CheckMessage = None, /) -> SizedT:
        if len(v) != 0:
            self._raise(
                ValueError,
                'Must be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def iterempty(self, v: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Iterable[T]:
        it = iter(v)
        try:
            next(it)
        except StopIteration:
            pass
        else:
            self._raise(
                ValueError,
                'Must be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def not_empty(self, v: SizedT, msg: CheckMessage = None, /) -> SizedT:
        if len(v) == 0:
            self._raise(
                ValueError,
                'Must not be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def unique(self, it: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Iterable[T]:
        dupes = [e for e, c in collections.Counter(it).items() if c > 1]
        if dupes:
            self._raise(
                ValueError,
                'Must be unique',
                msg,
                Checks._ArgsKwargs(it, dupes),
            )

        return it

    def single(self, obj: ta.Iterable[T], msg: CheckMessage = None, /) -> T:
        try:
            [value] = obj
        except ValueError:
            self._raise(
                ValueError,
                'Must be single',
                msg,
                Checks._ArgsKwargs(obj),
                render_fmt='%s',
            )

        return value

    def opt_single(self, obj: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Optional[T]:
        it = iter(obj)
        try:
            value = next(it)
        except StopIteration:
            return None

        try:
            next(it)
        except StopIteration:
            return value  # noqa

        self._raise(
            ValueError,
            'Must be empty or single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    async def async_single(self, obj: ta.AsyncIterable[T], msg: CheckMessage = None, /) -> T:
        ait = obj.__aiter__()

        try:
            try:
                value = await ait.__anext__()
            except StopAsyncIteration:
                pass

            else:
                try:
                    await ait.__anext__()
                except StopAsyncIteration:
                    return value

        finally:
            if inspect.isasyncgen(ait):
                await ait.aclose()

        self._raise(
            ValueError,
            'Must be single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    async def async_opt_single(self, obj: ta.AsyncIterable[T], msg: CheckMessage = None, /) -> ta.Optional[T]:
        ait = obj.__aiter__()

        try:
            try:
                value = await ait.__anext__()
            except StopAsyncIteration:
                return None

            try:
                await ait.__anext__()
            except StopAsyncIteration:
                return value  # noqa

        finally:
            if inspect.isasyncgen(ait):
                await ait.aclose()

        self._raise(
            ValueError,
            'Must be empty or single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    #

    def none(self, v: ta.Any, msg: CheckMessage = None, /) -> None:
        if v is not None:
            self._raise(
                ValueError,
                'Must be None',
                msg,
                render_fmt='%s',
            )

    def not_none(self, v: ta.Optional[T], msg: CheckMessage = None, /) -> T:
        if v is None:
            self._raise(
                ValueError,
                'Must not be None',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    #

    def equal(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o != v:
            self._raise(
                ValueError,
                'Must be equal',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s != %s',
            )

        return v

    def not_equal(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o == v:
            self._raise(
                ValueError,
                'Must not be equal',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s == %s',
            )

        return v

    def is_(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o is not v:
            self._raise(
                ValueError,
                'Must be the same',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s is not %s',
            )

        return v

    def is_not(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o is v:
            self._raise(
                ValueError,
                'Must not be the same',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s is %s',
            )

        return v

    def callable(self, v: T, msg: CheckMessage = None, /) -> T:  # noqa
        if not callable(v):
            self._raise(
                TypeError,
                'Must be callable',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def non_empty_str(self, v: ta.Optional[str], msg: CheckMessage = None, /) -> str:
        if not isinstance(v, str) or not v:
            self._raise(
                ValueError,
                'Must be non-empty str',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def replacing(self, expected: ta.Any, old: ta.Any, new: T, msg: CheckMessage = None, /) -> T:
        if old != expected:
            self._raise(
                ValueError,
                'Must be replacing',
                msg,
                Checks._ArgsKwargs(expected, old, new),
                render_fmt='%s -> %s -> %s',
            )

        return new

    def replacing_none(self, old: ta.Any, new: T, msg: CheckMessage = None, /) -> T:
        if old is not None:
            self._raise(
                ValueError,
                'Must be replacing None',
                msg,
                Checks._ArgsKwargs(old, new),
                render_fmt='%s -> %s',
            )

        return new

    #

    def arg(self, v: bool, msg: CheckMessage = None, /) -> None:
        if not v:
            self._raise(
                RuntimeError,
                'Argument condition not met',
                msg,
                render_fmt='%s',
            )

    def state(self, v: bool, msg: CheckMessage = None, /) -> None:
        if not v:
            self._raise(
                RuntimeError,
                'State condition not met',
                msg,
                render_fmt='%s',
            )

    def inline(self, v: T, c: bool, msg: CheckMessage = None, /) -> T:
        if not c:
            self._raise(
                RuntimeError,
                'State condition not met',
                msg,
                render_fmt='%s',
            )
        return v


check = Checks()


########################################
# ../../../../omcore/lite/dataclasses.py


##


def dataclass_shallow_astuple(o: ta.Any) -> ta.Tuple[ta.Any, ...]:
    return tuple(getattr(o, f.name) for f in dc.fields(o))


def dataclass_shallow_asdict(o: ta.Any) -> ta.Dict[str, ta.Any]:
    return {f.name: getattr(o, f.name) for f in dc.fields(o)}


##


def is_immediate_dataclass(cls: type) -> bool:
    if not isinstance(cls, type):
        raise TypeError(cls)
    return dc._FIELDS in cls.__dict__  # type: ignore[attr-defined]  # noqa


##


def _install_dataclass_fn(cls: type, fn: ta.Any, fn_name: ta.Optional[str] = None) -> None:
    if fn_name is None:
        fn_name = str(fn.__name__)
    setattr(cls, fn_name, fn)
    fn.__qualname__ = f'{cls.__qualname__}.{fn_name}'


##


def install_dataclass_cache_hash(
        *,
        cached_hash_attr: str = '__dataclass_hash__',
) -> ta.Callable[[ta.Type[T]], ta.Type[T]]:
    def inner(cls: ta.Type[T]) -> ta.Type[T]:
        if not (isinstance(cls, type) and dc.is_dataclass(cls)):
            raise TypeError(cls)

        # dict lookup, not attribute - an eq=True/frozen=False dataclass sets __hash__ to None in the class dict, which
        # is just as unusable here as an absent or inherited one.
        if (
                (real_hash := cls.__dict__.get('__hash__')) is None or
                real_hash is object.__hash__
        ):
            raise TypeError(cls)

        def cached_hash(self) -> int:
            try:
                return object.__getattribute__(self, cached_hash_attr)
            except AttributeError:
                object.__setattr__(self, cached_hash_attr, h := real_hash(self))
            return h

        _install_dataclass_fn(cls, cached_hash, '__hash__')

        return cls

    return inner


##


def dataclass_maybe_post_init(sup: ta.Any) -> bool:
    if not isinstance(sup, super):
        raise TypeError(sup)
    try:
        fn = sup.__post_init__  # type: ignore
    except AttributeError:
        return False
    fn()
    return True


##


def dataclass_repr(
        obj: ta.Any,
        *,
        terse: bool = False,
        filter: ta.Union[  # noqa
            ta.Callable[[ta.Any, dc.Field, ta.Any], bool],
            ta.Literal['omit_none', 'omit_falsey'],
            None,
        ] = None,
) -> str:
    if filter == 'omit_none':
        filter = lambda o, f, v: v is not None  # noqa
    elif filter == 'omit_falsey':
        filter = lambda o, f, v: bool(v)  # noqa

    lst: ta.List[str] = [
        f'{obj.__class__.__qualname__}(',
    ]

    i = 0
    for f in dc.fields(obj):
        if not f.repr:
            continue

        v = getattr(obj, f.name)

        if filter is not None and not filter(obj, f, v):
            continue

        if i:
            lst.append(', ')
        i += 1

        if not terse:
            lst.append(f.name)
            lst.append('=')

        lst.append(repr(v))

    lst.append(')')

    return ''.join(lst)


def dataclass_repr_omit_none(obj: ta.Any) -> str:
    return dataclass_repr(obj, filter='omit_none')


def dataclass_repr_omit_falsey(obj: ta.Any) -> str:
    return dataclass_repr(obj, filter='omit_falsey')


def install_dataclass_repr(
        *,
        terse: bool = False,
        filter: ta.Union[  # noqa
            ta.Callable[[ta.Any, dc.Field, ta.Any], bool],
            ta.Literal['omit_none', 'omit_falsey'],
            None,
        ] = None,
) -> ta.Callable[[ta.Type[T]], ta.Type[T]]:
    def inner(cls: ta.Type[T]) -> ta.Type[T]:
        if not (isinstance(cls, type) and dc.is_dataclass(cls)):
            raise TypeError(cls)

        def repr_impl(self) -> str:
            return dataclass_repr(
                self,
                terse=terse,
                filter=filter,
            )

        _install_dataclass_fn(cls, repr_impl, '__repr__')

        return cls

    return inner


##


def dataclass_descriptor_method(*bind_attrs: str, bind_owner: bool = False) -> ta.Callable:
    if not bind_attrs:
        def __get__(self, instance, owner=None):  # noqa
            return self

    elif bind_owner:
        def __get__(self, instance, owner=None):  # noqa
            # Guaranteed to return a new instance even with no attrs
            return dc.replace(self, **{
                a: v.__get__(instance, owner) if (v := getattr(self, a)) is not None else None
                for a in bind_attrs
            })

    else:
        def __get__(self, instance, owner=None):  # noqa
            if instance is None:
                return self

            # Guaranteed to return a new instance even with no attrs
            return dc.replace(self, **{
                a: v.__get__(instance, owner) if (v := getattr(self, a)) is not None else None
                for a in bind_attrs
            })

    return __get__


##


def install_dataclass_kw_only_init() -> ta.Callable[[ta.Type[T]], ta.Type[T]]:
    def inner(cls: ta.Type[T]) -> ta.Type[T]:
        if not (isinstance(cls, type) and dc.is_dataclass(cls)):
            raise TypeError(cls)

        real_init = cls.__init__

        # The real __init__'s params are the init=True fields plus InitVar pseudo-fields (which dc.fields omits), in
        # field order - init=False fields must be excluded or the generated call will not match its signature.
        flds = [
            f
            for f in getattr(cls, dc._FIELDS).values()  # type: ignore[attr-defined]  # noqa
            if f._field_type is dc._FIELD_INITVAR or (f._field_type is dc._FIELD and f.init)  # type: ignore[attr-defined]  # noqa
        ]

        if any(f.name == 'self' for f in flds):
            self_name = '__dataclass_self__'
        else:
            self_name = 'self'

        # default_factory fields cannot have their default baked into the signature - a MISSING sentinel default is
        # filtered out of the forwarded kwargs so the real init invokes the factory per-call.
        src = '\n'.join([
            'def __init__(',
            f'    {self_name},',
            '    *,',
            *[
                ''.join([
                    f'    {f.name}: __dataclass_type_{f.name}__',
                    (
                        f' = __dataclass_default_{f.name}__' if f.default is not dc.MISSING else
                        ' = __dataclass_MISSING__' if f.default_factory is not dc.MISSING else  # noqa
                        ''
                    ),
                    ',',
                ])
                for f in flds
            ],
            ') -> __dataclass_None__:',
            '    __dataclass_real_init__(',
            f'        {self_name},',
            *[
                f'        {f.name}={f.name},'
                for f in flds
                if f.default_factory is dc.MISSING  # noqa
            ],
            '        **{',
            '            k: v',
            '            for k, v in [',
            *[
                f'                ({f.name!r}, {f.name}),'
                for f in flds
                if f.default_factory is not dc.MISSING  # noqa
            ],
            '            ]',
            '            if v is not __dataclass_MISSING__',
            '        },',
            '    )',
        ])

        ns: dict = {
            '__dataclass_None__': None,
            '__dataclass_MISSING__': dc.MISSING,
            '__dataclass_real_init__': real_init,
            **{
                f'__dataclass_type_{f.name}__': f.type
                for f in flds
            },
            **{
                f'__dataclass_default_{f.name}__': f.default
                for f in flds
                if f.default is not dc.MISSING
            },
        }

        exec(src, ns)

        kw_only_init = ns['__init__']

        functools.update_wrapper(kw_only_init, real_init)

        _install_dataclass_fn(cls, kw_only_init, '__init__')

        return cls

    return inner


##


@dc.dataclass()
class DataclassFieldRequiredError(Exception):
    name: str


def dataclass_field_required(name: str) -> ta.Callable[[], ta.Any]:
    def inner() -> ta.NoReturn:
        raise DataclassFieldRequiredError(name)
    return inner


########################################
# ../../../../omcore/lite/namespaces.py


class NamespaceClass:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    def __init_subclass__(cls, **kwargs):  # noqa
        super().__init_subclass__(**kwargs)

        if any(issubclass(b, NamespaceClass) and b is not NamespaceClass for b in cls.__bases__):
            raise TypeError


########################################
# ../../../../omcore/lite/objects.py


##


def deep_subclasses(cls: ta.Type[T]) -> ta.Iterator[ta.Type[T]]:
    seen = set()
    todo = list(reversed(cls.__subclasses__()))
    while todo:
        cur = todo.pop()
        if cur in seen:
            continue
        seen.add(cur)
        yield cur
        todo.extend(reversed(cur.__subclasses__()))


##


def mro_owner_dict(
        instance_cls: type,
        owner_cls: ta.Optional[type] = None,
        *,
        bottom_up_key_order: bool = False,
        sort_keys: bool = False,
) -> ta.Mapping[str, ta.Tuple[type, ta.Any]]:
    if owner_cls is None:
        owner_cls = instance_cls

    mro = instance_cls.__mro__[-2::-1]
    try:
        pos = mro.index(owner_cls)
    except ValueError:
        raise TypeError(f'Owner class {owner_cls} not in mro of instance class {instance_cls}') from None

    dct: ta.Dict[str, ta.Tuple[type, ta.Any]] = {}
    if not bottom_up_key_order:
        for cur_cls in mro[:pos + 1][::-1]:
            for k, v in cur_cls.__dict__.items():
                if k not in dct:
                    dct[k] = (cur_cls, v)

    else:
        for cur_cls in mro[:pos + 1]:
            dct.update({k: (cur_cls, v) for k, v in cur_cls.__dict__.items()})

    if sort_keys:
        dct = dict(sorted(dct.items(), key=lambda t: t[0]))

    return dct


def mro_dict(
        instance_cls: type,
        owner_cls: ta.Optional[type] = None,
        *,
        bottom_up_key_order: bool = False,
        sort_keys: bool = False,
) -> ta.Mapping[str, ta.Any]:
    return {
        k: v
        for k, (o, v) in mro_owner_dict(
            instance_cls,
            owner_cls,
            bottom_up_key_order=bottom_up_key_order,
            sort_keys=sort_keys,
        ).items()
    }


def dir_dict(o: ta.Any) -> ta.Dict[str, ta.Any]:
    return {
        a: getattr(o, a)
        for a in dir(o)
    }


########################################
# ../../../../omcore/lite/reflect.py


##


_GENERIC_ALIAS_TYPES = (
    ta._GenericAlias,  # type: ignore  # noqa
    *([ta._SpecialGenericAlias] if hasattr(ta, '_SpecialGenericAlias') else []),  # noqa
    *([types.GenericAlias] if hasattr(types, 'GenericAlias') else []),  # noqa
)


def is_generic_alias(obj: ta.Any, *, origin: ta.Any = None) -> bool:
    return (
        isinstance(obj, _GENERIC_ALIAS_TYPES) and
        (origin is None or ta.get_origin(obj) is origin)
    )


# ta.get_origin returns the collections.abc class, never the typing alias.
is_callable_alias = functools.partial(is_generic_alias, origin=ta.get_origin(ta.Callable[..., ta.Any]))


##


_UNION_ALIAS_ORIGINS = frozenset([
    ta.get_origin(ta.Optional[int]),
    *(
        [
            ta.get_origin(int | None),
            ta.get_origin(getattr(ta, 'TypeVar')('_T') | None),
        ] if sys.version_info >= (3, 10) else ()
    ),
])


def is_union_alias(obj: ta.Any) -> bool:
    return ta.get_origin(obj) in _UNION_ALIAS_ORIGINS


#


def is_optional_alias(spec: ta.Any) -> bool:
    return (
        is_union_alias(spec) and
        len(ta.get_args(spec)) == 2 and
        any(a in (None, type(None)) for a in ta.get_args(spec))
    )


def get_optional_alias_arg(spec: ta.Any) -> ta.Any:
    [it] = [it for it in ta.get_args(spec) if it not in (None, type(None))]
    return it


##


def is_new_type(spec: ta.Any) -> bool:
    if isinstance(ta.NewType, type):
        return isinstance(spec, ta.NewType)
    else:
        # Before https://github.com/python/cpython/commit/c2f33dfc83ab270412bf243fb21f724037effa1a
        return isinstance(spec, types.FunctionType) and spec.__code__ is ta.NewType.__code__.co_consts[1]  # type: ignore  # noqa


def get_new_type_supertype(spec: ta.Any) -> ta.Any:
    return spec.__supertype__


##


def is_literal_type(spec: ta.Any) -> bool:
    if hasattr(ta, '_LiteralGenericAlias'):
        return isinstance(spec, ta._LiteralGenericAlias)  # noqa
    else:
        return (
            isinstance(spec, ta._GenericAlias) and  # type: ignore  # noqa
            spec.__origin__ is ta.Literal
        )


def get_literal_type_args(spec: ta.Any) -> ta.Iterable[ta.Any]:
    return spec.__args__


##


def type_form_repr(ty: ta.Any) -> str:
    if isinstance(ty, type):
        return f'{ty.__module__}.{ty.__qualname__}'

    elif ty is ta.Any:
        return 'typing.Any'

    elif is_optional_alias(ty):
        ety = get_optional_alias_arg(ty)
        return f'typing.Optional[{type_form_repr(ety)}]'

    elif is_union_alias(ty):
        args = ta.get_args(ty)
        return f'typing.Union[{", ".join(sorted(type_form_repr(a) for a in args))}]'

    elif is_callable_alias(ty):
        ptys, rty = ta.get_args(ty)
        return (
            f'typing.Callable[['
            f'{"..." if isinstance(ptys, types.EllipsisType) else ", ".join(type_form_repr(a) for a in ptys)}], '
            f'{type_form_repr(rty)}]'
        )

    elif is_literal_type(ty):
        args = ta.get_args(ty)
        return f'typing.Literal[{", ".join(sorted(repr(a) for a in args))}]'

    elif is_new_type(ty):
        raise NotImplementedError

    elif is_generic_alias(ty):
        origin = ta.get_origin(ty)
        args = ta.get_args(ty)
        if origin is tuple and args and isinstance(args[-1], types.EllipsisType):
            return (
                f'{type_form_repr(origin)}['
                f'{", ".join(type_form_repr(a) for a in args[:-1])}, ...]'
            )
        else:
            return (
                f'{type_form_repr(origin)}['
                f'{", ".join(type_form_repr(a) for a in args)}]'
            )

    else:
        raise TypeError(ty)


########################################
# ../../../../omcore/lite/resources.py


def read_package_resource_binary(package: str, resource: str) -> bytes:
    import importlib.resources
    return importlib.resources.read_binary(package, resource)


def read_package_resource_text(package: str, resource: str) -> str:
    import importlib.resources
    return importlib.resources.read_text(package, resource)


########################################
# ../../../../omcore/lite/strings.py


##


def camel_case(name: str, *, lower: bool = False) -> str:
    if not name:
        return ''
    s = ''.join(map(str.capitalize, name.split('_')))  # noqa
    if lower:
        s = s[0].lower() + s[1:]
    return s


def snake_case(name: str) -> str:
    uppers: list[int | None] = [i for i, c in enumerate(name) if c.isupper()]
    return '_'.join([name[l:r].lower() for l, r in zip([None, *uppers], [*uppers, None])]).strip('_')


##


def is_dunder(name: str) -> bool:
    return (
        name[:2] == name[-2:] == '__' and
        name[2:3] != '_' and
        name[-3:-2] != '_' and
        len(name) > 4
    )


def is_sunder(name: str) -> bool:
    return (
        len(name) > 2 and
        name[0] == name[-1] == '_' and
        name[1:2] != '_' and
        name[-2:-1] != '_'
    )


##


def strip_with_newline(s: str) -> str:
    if not s:
        return ''
    return s.strip() + '\n'


@ta.overload
def split_keep_delimiter(s: str, d: str) -> ta.List[str]: ...


@ta.overload
def split_keep_delimiter(s: bytes, d: bytes) -> ta.List[bytes]: ...


def split_keep_delimiter(s, d):
    if not d:
        raise ValueError(d)
    dl = len(d)
    ps = []
    i = 0
    while i < len(s):
        if (n := s.find(d, i)) < i:
            ps.append(s[i:])
            break
        ps.append(s[i:n + dl])
        i = n + dl
    return ps


##


FORMAT_NUM_BYTES_SUFFIXES: ta.Sequence[str] = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB']


def format_num_bytes(num_bytes: int) -> str:
    for i, suffix in enumerate(FORMAT_NUM_BYTES_SUFFIXES):
        value = num_bytes / 1024 ** i
        if num_bytes < 1024 ** (i + 1):
            if value.is_integer():
                return f'{int(value)}{suffix}'
            else:
                return f'{value:.2f}{suffix}'

    return f'{num_bytes / 1024 ** (len(FORMAT_NUM_BYTES_SUFFIXES) - 1):.2f}{FORMAT_NUM_BYTES_SUFFIXES[-1]}'


########################################
# ../../../../omcore/lite/typing.py


##
# A workaround for typing deficiencies (like `Argument 2 to NewType(...) must be subclassable`).
#
# Note that this problem doesn't happen at runtime - it happens in mypy:
#
#   mypy <(echo "import typing as ta; MyCallback = ta.NewType('MyCallback', ta.Callable[[], None])")
#   /dev/fd/11:1:22: error: Argument 2 to NewType(...) must be subclassable (got "Callable[[], None]")  [valid-newtype]
#


@dc.dataclass(frozen=True)
class AnyFunc(ta.Generic[T]):
    fn: ta.Callable[..., T]

    def __call__(self, *args: ta.Any, **kwargs: ta.Any) -> T:
        return self.fn(*args, **kwargs)


@dc.dataclass(frozen=True)
class Func0(ta.Generic[T]):
    fn: ta.Callable[[], T]

    def __call__(self) -> T:
        return self.fn()


@dc.dataclass(frozen=True)
class Func1(ta.Generic[A0, T]):
    fn: ta.Callable[[A0], T]

    def __call__(self, a0: A0) -> T:
        return self.fn(a0)


@dc.dataclass(frozen=True)
class Func2(ta.Generic[A0, A1, T]):
    fn: ta.Callable[[A0, A1], T]

    def __call__(self, a0: A0, a1: A1) -> T:
        return self.fn(a0, a1)


@dc.dataclass(frozen=True)
class Func3(ta.Generic[A0, A1, A2, T]):
    fn: ta.Callable[[A0, A1, A2], T]

    def __call__(self, a0: A0, a1: A1, a2: A2) -> T:
        return self.fn(a0, a1, a2)


##


@dc.dataclass(frozen=True)
class CachedFunc0(ta.Generic[T]):
    fn: ta.Callable[[], T]

    def __call__(self) -> T:
        try:
            return object.__getattribute__(self, '_value')
        except AttributeError:
            pass

        value = self.fn()
        object.__setattr__(self, '_value', value)
        return value


@dc.dataclass(frozen=True)
class AsyncCachedFunc0(ta.Generic[T]):
    fn: ta.Callable[[], ta.Awaitable[T]]

    async def __call__(self) -> T:
        try:
            return object.__getattribute__(self, '_value')
        except AttributeError:
            pass

        value = await self.fn()
        object.__setattr__(self, '_value', value)
        return value


##


_TYPING_ANNOTATIONS_ATTR = '__annotate__' if sys.version_info >= (3, 14) else '__annotations__'


def typing_annotations_attr() -> str:
    return _TYPING_ANNOTATIONS_ATTR


##


@ta.runtime_checkable
class CanInt(ta.Protocol):
    def __int__(self) -> int:
        ...


@ta.runtime_checkable
class CanFloat(ta.Protocol):
    def __float__(self) -> float:
        ...


########################################
# ../../../../omcore/logs/levels.py


##


@ta.final
class NamedLogLevel(int):
    # logging.getLevelNamesMapping (or, as that is unavailable <3.11, logging._nameToLevel) includes the deprecated
    # aliases.
    _NAMES_BY_INT: ta.ClassVar[ta.Mapping[LogLevel, str]] = dict(sorted(logging._levelToName.items(), key=lambda t: -t[0]))  # noqa

    _INTS_BY_NAME: ta.ClassVar[ta.Mapping[str, LogLevel]] = {v: k for k, v in _NAMES_BY_INT.items()}

    _NAME_INT_PAIRS: ta.ClassVar[ta.Sequence[ta.Tuple[str, LogLevel]]] = list(_INTS_BY_NAME.items())

    #

    _CACHE: ta.ClassVar[ta.MutableMapping[int, 'NamedLogLevel']] = {}

    @ta.overload
    def __new__(cls, name: str, offset: int = 0, /) -> 'NamedLogLevel': ...

    @ta.overload
    def __new__(cls, i: int, /) -> 'NamedLogLevel': ...

    def __new__(cls, x, offset=0, /):
        if isinstance(x, str):
            return cls(cls._INTS_BY_NAME[x.upper()] + offset)
        elif not offset and (c := cls._CACHE.get(x)) is not None:
            return c
        else:
            return super().__new__(cls, x + offset)

    #

    _name_and_offset: ta.Tuple[str, int]

    @property
    def name_and_offset(self) -> ta.Tuple[str, int]:
        try:
            return self._name_and_offset
        except AttributeError:
            pass

        if (n := self._NAMES_BY_INT.get(self)) is not None:
            t = (n, 0)
        else:
            for n, i in self._NAME_INT_PAIRS:  # noqa
                if self >= i:
                    t = (n, (self - i))
                    break
            else:
                t = ('NOTSET', int(self))

        self._name_and_offset = t
        return t

    @property
    def exact_name(self) -> ta.Optional[str]:
        n, o = self.name_and_offset
        return n if not o else None

    @property
    def effective_name(self) -> str:
        n, _ = self.name_and_offset
        return n

    #

    def __str__(self) -> str:
        return self.exact_name or f'{self.effective_name}{int(self):+}'

    def __repr__(self) -> str:
        n, o = self.name_and_offset
        return f'{self.__class__.__name__}({n!r}{f", {int(o)}" if o else ""})'

    #

    CRITICAL: ta.ClassVar['NamedLogLevel']
    ERROR: ta.ClassVar['NamedLogLevel']
    WARNING: ta.ClassVar['NamedLogLevel']
    INFO: ta.ClassVar['NamedLogLevel']
    DEBUG: ta.ClassVar['NamedLogLevel']
    NOTSET: ta.ClassVar['NamedLogLevel']


NamedLogLevel.CRITICAL = NamedLogLevel(logging.CRITICAL)
NamedLogLevel.ERROR = NamedLogLevel(logging.ERROR)
NamedLogLevel.WARNING = NamedLogLevel(logging.WARNING)
NamedLogLevel.INFO = NamedLogLevel(logging.INFO)
NamedLogLevel.DEBUG = NamedLogLevel(logging.DEBUG)
NamedLogLevel.NOTSET = NamedLogLevel(logging.NOTSET)


NamedLogLevel._CACHE.update({i: NamedLogLevel(i) for i in NamedLogLevel._NAMES_BY_INT})  # noqa


########################################
# ../../../../omcore/logs/warnings.py


##


class LoggingSetupWarning(Warning):
    pass


########################################
# ../../../../omcore/os/pyremote/core.py
"""
Basically (the first part of) this: https://mitogen.networkgenomics.com/howitworks.html

TODO:
 - log: ta.Optional[logging.Logger] = None + log.debug's
"""


##


@dc.dataclass(frozen=True)
class PyremoteBootstrapOptions:
    debug: bool = False

    DEFAULT_MAIN_NAME_OVERRIDE: ta.ClassVar[str] = '__pyremote__'
    main_name_override: ta.Optional[str] = DEFAULT_MAIN_NAME_OVERRIDE


##


@dc.dataclass(frozen=True)
class PyremoteEnvInfo:
    @dc.dataclass(frozen=True)
    class Sys:
        base_prefix: str
        byteorder: str
        defaultencoding: str
        exec_prefix: str
        executable: str
        implementation_name: str
        path: ta.List[str]
        platform: str
        prefix: str
        version: str
        version_info: ta.List[ta.Union[int, str]]

    sys: Sys

    @dc.dataclass(frozen=True)
    class Platform:
        architecture: ta.List[str]
        machine: str
        platform: str
        processor: str
        system: str
        release: str
        version: str

    platform: Platform

    @dc.dataclass(frozen=True)
    class Site:
        userbase: str

    site: Site

    @dc.dataclass(frozen=True)
    class Os:
        cwd: str
        gid: int
        loadavg: ta.List[float]
        login: ta.Optional[str]
        pgrp: int
        pid: int
        ppid: int
        uid: int

    os: Os

    @dc.dataclass(frozen=True)
    class Pw:
        name: str
        uid: int
        gid: int
        gecos: str
        dir: str
        shell: str

    pw: Pw

    @dc.dataclass(frozen=True)
    class Env:
        path: ta.Optional[str]

    env: Env

    #

    def to_dict(self) -> dict:
        return {
            f.name: dc.asdict(v) if dc.is_dataclass(v := getattr(self, f.name)) else v  # type: ignore[arg-type]
            for f in dc.fields(self)
        }

    @classmethod
    def from_dict(cls, dct: dict) -> 'PyremoteEnvInfo':
        flds_dct = {f.name: f for f in dc.fields(cls)}
        return cls(**{
            k: ft(**v) if isinstance((ft := flds_dct[k].type), type) and dc.is_dataclass(ft) is not None else v
            for k, v in dct.items()
        })


def _get_pyremote_env_info() -> PyremoteEnvInfo:
    os_uid = os.getuid()

    pw = pwd.getpwuid(os_uid)

    os_login: ta.Optional[str]
    try:
        os_login = os.getlogin()
    except OSError:
        os_login = None

    return PyremoteEnvInfo(
        sys=PyremoteEnvInfo.Sys(
            base_prefix=sys.base_prefix,
            byteorder=sys.byteorder,
            defaultencoding=sys.getdefaultencoding(),
            exec_prefix=sys.exec_prefix,
            executable=sys.executable,
            implementation_name=sys.implementation.name,
            path=sys.path,
            platform=sys.platform,
            prefix=sys.prefix,
            version=sys.version,
            version_info=list(sys.version_info),
        ),

        platform=PyremoteEnvInfo.Platform(
            architecture=list(platform.architecture()),
            machine=platform.machine(),
            platform=platform.platform(),
            processor=platform.processor(),
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
        ),

        site=PyremoteEnvInfo.Site(
            userbase=site.getuserbase(),
        ),

        os=PyremoteEnvInfo.Os(
            cwd=os.getcwd(),
            gid=os.getgid(),
            loadavg=list(os.getloadavg()),
            login=os_login,
            pgrp=os.getpgrp(),
            pid=os.getpid(),
            ppid=os.getppid(),
            uid=os_uid,
        ),

        pw=PyremoteEnvInfo.Pw(
            name=pw.pw_name,
            uid=pw.pw_uid,
            gid=pw.pw_gid,
            gecos=pw.pw_gecos,
            dir=pw.pw_dir,
            shell=pw.pw_shell,
        ),

        env=PyremoteEnvInfo.Env(
            path=os.environ.get('PATH'),
        ),
    )


##


class _PyremoteBootstrapConsts:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    TIMEOUT_S = 3 * 60
    GRACE_S = 10
    REAP_S = 3
    REAP_SLEEP_S = .02

    INPUT_FD = 100
    SRC_FD = 101
    DISARM_FD = 102

    WATCHDOG_PID_VAR = '_OPYR_WATCHDOG_PID'
    CHILD_PID_VAR = '_OPYR_CHILD_PID'
    ARGV0_VAR = '_OPYR_ARGV0'
    CONTEXT_NAME_VAR = '_OPYR_CONTEXT_NAME'
    SRC_FILE_VAR = '_OPYR_SRC_FILE'
    OPTIONS_JSON_VAR = '_OPYR_OPTIONS_JSON'

    ACK0 = b'OPYR000\n'
    ACK1 = b'OPYR001\n'
    ACK2 = b'OPYR002\n'
    ACK3 = b'OPYR003\n'

    PROC_TITLE_FMT = '(pyremote:%s)'

    IMPORTS = (
        'base64',
        'os',
        'select',
        'signal',
        'struct',
        'sys',
        'time',
        'zlib',
    )


def _pyremote_bootstrap_main(context_name: str) -> None:
    # Setup watchdog
    dl = time.monotonic() + _PyremoteBootstrapConsts.TIMEOUT_S + _PyremoteBootstrapConsts.GRACE_S
    pp = os.getpid()
    dr, dw = os.pipe()
    pfd = None  # type: int | None
    try:
        pfd = os.pidfd_open(os.getpid())  # type: ignore[attr-defined,unused-ignore]
    except (AttributeError, OSError):
        pass

    if not (wp := os.fork()):  # noqa
        # Watchdog process

        # Survive group-wide signals the target survives
        for s in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM]:
            signal.signal(s, signal.SIG_IGN)

        # Cleanup fd's
        nfd = os.open(os.devnull, os.O_WRONLY)
        for fd in [0, 1]:
            os.dup2(nfd, fd)

        wrl = [dr] + ([pfd] if pfd is not None else [])
        while (rem := dl - time.monotonic()) > 0:
            if not wrl:
                time.sleep(rem)
                continue

            rdy, _, _ = select.select(wrl, [], [], rem)
            if pfd in rdy:
                # Target exited
                break

            if dr in rdy:
                if os.read(dr, 1):
                    break  # explicit disarm

                # EOF: target died (with no pidfd, ppid tells) or fd closed behind our back -> clock
                if pfd is None and os.getppid() != pp:
                    break

                wrl.remove(dr)

        else:
            # No break: deadline passed
            try:
                if pfd is not None:
                    signal.pidfd_send_signal(pfd, signal.SIGALRM)  # type: ignore[attr-defined,unused-ignore]
                    rdy, _, _ = select.select([pfd], [], [], _PyremoteBootstrapConsts.GRACE_S)
                    if rdy:
                        signal.pidfd_send_signal(pfd, signal.SIGKILL)  # type: ignore[attr-defined,unused-ignore]

                elif os.getppid() == pp:  # FIXME: TOCTOU :/
                    os.kill(pp, signal.SIGALRM)
                    time.sleep(_PyremoteBootstrapConsts.GRACE_S)
                    if os.getppid() == pp:
                        os.kill(pp, signal.SIGKILL)

            except ProcessLookupError:
                pass

        os._exit(0)

    else:
        # Finish watchdog setup
        os.close(dr)
        if pfd is not None:
            os.close(pfd)
        os.environ[_PyremoteBootstrapConsts.WATCHDOG_PID_VAR] = str(wp)

        # Install timeout
        def timeout(*_):
            raise TimeoutError

        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(_PyremoteBootstrapConsts.TIMEOUT_S)

        # Get pid
        pid = os.getpid()

        # Two copies of payload src to be sent to parent
        pr0, pw0 = os.pipe()
        pr1, pw1 = os.pipe()

        if (cp := os.fork()):
            # Parent process

            # Dup original stdin to comm_fd for use as comm channel
            os.dup2(0, _PyremoteBootstrapConsts.INPUT_FD)

            # Overwrite stdin (fed to python repl) with first copy of src
            os.dup2(pr0, 0)

            # Dup second copy of src to src_fd to recover after launch
            os.dup2(pr1, _PyremoteBootstrapConsts.SRC_FD)

            # Dup disarm fd to disarm_fd
            os.dup2(dw, _PyremoteBootstrapConsts.DISARM_FD)

            # Close remaining fd's
            for f in [pr0, pw0, pr1, pw1]:
                os.close(f)

            # Save vars
            env = os.environ
            exe = sys.executable
            env[_PyremoteBootstrapConsts.CHILD_PID_VAR] = str(cp)
            env[_PyremoteBootstrapConsts.ARGV0_VAR] = exe
            env[_PyremoteBootstrapConsts.CONTEXT_NAME_VAR] = context_name

            # Re-arm timeout. It survives the exec (with SIGALRM back at its default, terminating disposition) and
            # bounds finalization, which cancels it.
            signal.alarm(_PyremoteBootstrapConsts.TIMEOUT_S)

            # Start repl reading stdin from r0
            os.execl(exe, exe + (_PyremoteBootstrapConsts.PROC_TITLE_FMT % (context_name,)))

        else:
            # Child process

            # Write first ack
            os.write(1, _PyremoteBootstrapConsts.ACK0)

            # Write pid
            os.write(1, struct.pack('<Q', pid))

            # Read payload src from stdin
            payload_z_len = struct.unpack('<I', os.read(0, 4))[0]
            if len(payload_z := os.fdopen(0, 'rb').read(payload_z_len)) != payload_z_len:
                raise EOFError
            payload_src = zlib.decompress(payload_z)

            # Write both copies of payload src. Must write to w0 (parent stdin) before w1 (copy pipe) as pipe will
            # likely fill and block and need to be drained by pyremote_bootstrap_finalize running in parent.
            for w in [pw0, pw1]:
                fp = os.fdopen(w, 'wb', 0)
                fp.write(payload_src)
                fp.close()

            # Write second ack
            os.write(1, _PyremoteBootstrapConsts.ACK1)

            # Exit child
            os._exit(0)


##


def pyremote_build_bootstrap_source(context_name: str) -> str:
    if any(c in context_name for c in '\'"'):
        raise NameError(context_name)

    import inspect
    import textwrap
    bs_src = textwrap.dedent(inspect.getsource(_pyremote_bootstrap_main))

    for an, av in sorted(_PyremoteBootstrapConsts.__dict__.items(), key=lambda kv: -len(kv[0])):
        bs_src = bs_src.replace(f'_PyremoteBootstrapConsts.{an}', repr(av))

    bs_src = '\n'.join(
        cl
        for l in bs_src.splitlines()
        if (cl := (l.split('#')[0]).rstrip())
        if cl.strip()
    )

    bs_z = zlib.compress(bs_src.encode('utf-8'), 9)
    bs_z85 = base64.b85encode(bs_z).replace(b'\n', b'')
    if b'"' in bs_z85:
        raise ValueError(bs_z85)

    stmts = [
        f'import {",".join(_PyremoteBootstrapConsts.IMPORTS)}',
        f'exec(zlib.decompress(base64.b85decode(b"{bs_z85.decode("ascii")}")))',
        f'_pyremote_bootstrap_main("{context_name}")',
    ]

    cmd = ';'.join(stmts)
    return cmd


##


@dc.dataclass(frozen=True)
class PyremotePayloadRuntime:
    input: ta.BinaryIO
    output: ta.BinaryIO
    context_name: str
    payload_src: str
    options: PyremoteBootstrapOptions
    env_info: PyremoteEnvInfo


def pyremote_bootstrap_finalize() -> PyremotePayloadRuntime:
    # If src file var is not present we need to do initial finalization
    if _PyremoteBootstrapConsts.SRC_FILE_VAR not in os.environ:
        # Read second copy of payload src
        pr1 = os.fdopen(_PyremoteBootstrapConsts.SRC_FD, 'rb', 0)
        payload_src = pr1.read().decode('utf-8')
        pr1.close()

        # Reap boostrap child. Must be done after reading second copy of source because source may be too big to fit in
        # a pipe at once.
        os.waitpid(int(os.environ.pop(_PyremoteBootstrapConsts.CHILD_PID_VAR)), 0)

        # Read options
        options_json_len = struct.unpack('<I', os.read(_PyremoteBootstrapConsts.INPUT_FD, 4))[0]
        if len(options_json := os.read(_PyremoteBootstrapConsts.INPUT_FD, options_json_len)) != options_json_len:
            raise EOFError
        options = PyremoteBootstrapOptions(**json.loads(options_json.decode('utf-8')))

        # If debugging, re-exec as file
        if options.debug:
            # Write temp source file
            import tempfile
            tfd, tfn = tempfile.mkstemp('-pyremote.py')
            os.write(tfd, payload_src.encode('utf-8'))
            os.close(tfd)

            # Set vars
            os.environ[_PyremoteBootstrapConsts.SRC_FILE_VAR] = tfn
            os.environ[_PyremoteBootstrapConsts.OPTIONS_JSON_VAR] = options_json.decode('utf-8')

            # Re-exec temp file
            exe = os.environ[_PyremoteBootstrapConsts.ARGV0_VAR]
            context_name = os.environ[_PyremoteBootstrapConsts.CONTEXT_NAME_VAR]
            os.execl(exe, exe + (_PyremoteBootstrapConsts.PROC_TITLE_FMT % (context_name,)), tfn)

    else:
        # Load options json var
        options_json_str = os.environ.pop(_PyremoteBootstrapConsts.OPTIONS_JSON_VAR)
        options = PyremoteBootstrapOptions(**json.loads(options_json_str))

        # Read temp source file
        with open(os.environ.pop(_PyremoteBootstrapConsts.SRC_FILE_VAR)) as sf:
            payload_src = sf.read()

    # Restore vars
    sys.executable = os.environ.pop(_PyremoteBootstrapConsts.ARGV0_VAR)
    context_name = os.environ.pop(_PyremoteBootstrapConsts.CONTEXT_NAME_VAR)

    # Write third ack
    os.write(1, _PyremoteBootstrapConsts.ACK2)

    # Write env info
    env_info = _get_pyremote_env_info()
    env_info_json = json.dumps(env_info.to_dict(), indent=None, separators=(',', ':'))  # noqa
    os.write(1, struct.pack('<I', len(env_info_json)))
    os.write(1, env_info_json.encode('utf-8'))

    # Setup IO
    input = os.fdopen(_PyremoteBootstrapConsts.INPUT_FD, 'rb', 0)  # noqa
    output = os.fdopen(os.dup(1), 'wb', 0)  # noqa
    os.dup2(nfd := os.open(os.devnull, os.O_WRONLY), 1)
    os.close(nfd)

    if (mn := options.main_name_override) is not None:
        # Inspections like typing.get_type_hints need an entry in sys.modules.
        sys.modules[mn] = sys.modules['__main__']

    # Cancel the bootstrap's alarm. It was re-armed right before the exec into this interpreter and survived it, and
    # SIGALRM is at its default disposition here: left alone, it would terminate the payload TIMEOUT_S after launch.
    signal.alarm(0)

    # Disarm watchdog
    try:
        os.write(_PyremoteBootstrapConsts.DISARM_FD, b'1')
    except OSError:
        pass  # watchdog already gone; the reap below tells the story
    os.close(_PyremoteBootstrapConsts.DISARM_FD)

    # Reap watchdog. It's our unreaped child: its pid can't be recycled, so waiting on it and killing it are both
    # race-free. Wait on a pidfd where available, poll otherwise.
    wp = int(os.environ.pop(_PyremoteBootstrapConsts.WATCHDOG_PID_VAR))
    pfd = None  # type: int | None
    try:
        pfd = os.pidfd_open(wp)  # type: ignore[attr-defined,unused-ignore]
    except (AttributeError, OSError):
        pass

    try:
        if pfd is not None:
            try:
                # Readable once it has exited
                select.select([pfd], [], [], _PyremoteBootstrapConsts.REAP_S)
            finally:
                os.close(pfd)
            done, _ = os.waitpid(wp, os.WNOHANG)

        else:
            reap_dl = time.monotonic() + _PyremoteBootstrapConsts.REAP_S
            while not (done := os.waitpid(wp, os.WNOHANG)[0]) and time.monotonic() < reap_dl:
                time.sleep(_PyremoteBootstrapConsts.REAP_SLEEP_S)

        if not done:
            os.kill(wp, signal.SIGKILL)
            os.waitpid(wp, 0)
            raise TimeoutError(f'Timeout reaping pyremote watchdog pid {wp}')

    except ChildProcessError:
        pass

    # Write fourth ack
    output.write(_PyremoteBootstrapConsts.ACK3)

    # Return
    return PyremotePayloadRuntime(
        input=input,
        output=output,
        context_name=context_name,
        payload_src=payload_src,
        options=options,
        env_info=env_info,
    )


##


class PyremoteBootstrapDriver:
    def __init__(
            self,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions = PyremoteBootstrapOptions(),
    ) -> None:
        super().__init__()

        self._payload_src = payload_src
        self._options = options

        self._prepared_payload_src = self._prepare_payload_src(payload_src, options)
        self._payload_z = zlib.compress(self._prepared_payload_src.encode('utf-8'))

        self._options_json = json.dumps(dc.asdict(options), indent=None, separators=(',', ':')).encode('utf-8')  # noqa

    #

    @classmethod
    def _prepare_payload_src(
            cls,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions,
    ) -> str:
        parts: ta.List[str]
        if isinstance(payload_src, str):
            parts = [payload_src]
        else:
            parts = []
            for i, p in enumerate(payload_src):
                if i:
                    parts.append('\n\n')
                parts.append(p)

        if (mn := options.main_name_override) is not None:
            # Must go on same single line as first line of user payload to preserve '<stdin>' line numbers. If more
            # things wind up having to be done here, it can still be crammed on one line into a single `exec()`.
            #
            # The overriding name is registered in sys.modules right away, not just at finalization: module-level code
            # runs first, and some of it inspects its module while it does - dataclasses with string-annotated fields
            # look the module up in sys.modules while the class is being created, on Python 3.8 at least.
            parts.insert(0, (
                f'__name__ = {mn!r}; '
                f'__import__("sys").modules.setdefault(__name__, __import__("sys").modules["__main__"]); '
            ))

        if len(parts) == 1:
            return parts[0]
        else:
            return ''.join(parts)

    #

    @dc.dataclass(frozen=True)
    class Read:
        sz: int

    @dc.dataclass(frozen=True)
    class Write:
        d: bytes

    class ProtocolError(Exception):
        pass

    @dc.dataclass(frozen=True)
    class Result:
        pid: int
        env_info: PyremoteEnvInfo

    def gen(self) -> ta.Generator[ta.Union[Read, Write], ta.Optional[bytes], Result]:
        # Read first ack (after fork)
        yield from self._expect(_PyremoteBootstrapConsts.ACK0)

        # Read pid
        d = yield from self._read(8)
        pid = struct.unpack('<Q', d)[0]

        # Write payload src
        yield from self._write(struct.pack('<I', len(self._payload_z)))
        yield from self._write(self._payload_z)

        # Read second ack (after writing src copies)
        yield from self._expect(_PyremoteBootstrapConsts.ACK1)

        # Write options
        yield from self._write(struct.pack('<I', len(self._options_json)))
        yield from self._write(self._options_json)

        # Read third ack (after reaping child process)
        yield from self._expect(_PyremoteBootstrapConsts.ACK2)

        # Read env info
        d = yield from self._read(4)
        env_info_json_len = struct.unpack('<I', d)[0]
        d = yield from self._read(env_info_json_len)
        env_info_json = d.decode('utf-8')
        env_info = PyremoteEnvInfo.from_dict(json.loads(env_info_json))

        # Read fourth ack (after finalization completed)
        yield from self._expect(_PyremoteBootstrapConsts.ACK3)

        # Return
        return self.Result(
            pid=pid,
            env_info=env_info,
        )

    def _read(self, sz: int) -> ta.Generator[Read, bytes, bytes]:
        d = yield self.Read(sz)
        if not isinstance(d, bytes):
            raise self.ProtocolError(f'Expected bytes after read, got {d!r}')
        if len(d) != sz:
            raise self.ProtocolError(f'Read {len(d)} bytes, expected {sz}')
        return d

    def _expect(self, e: bytes) -> ta.Generator[Read, bytes, None]:
        d = yield from self._read(len(e))
        if d != e:
            raise self.ProtocolError(f'Read {d!r}, expected {e!r}')

    def _write(self, d: bytes) -> ta.Generator[Write, ta.Optional[bytes], None]:
        i = yield self.Write(d)
        if i is not None:
            raise self.ProtocolError('Unexpected input after write')

    #

    def run(
            self,
            input: ta.IO,  # noqa
            output: ta.IO,
    ) -> Result:
        gen = self.gen()

        gi: ta.Optional[bytes] = None
        while True:
            try:
                if gi is not None:
                    go = gen.send(gi)
                else:
                    go = next(gen)
            except StopIteration as e:
                return e.value

            if isinstance(go, self.Read):
                buf = bytearray()
                while len(buf) < go.sz:
                    if not (d := input.read(go.sz - len(buf))):
                        raise EOFError
                    buf.extend(d)
                gi = bytes(buf)
            elif isinstance(go, self.Write):
                gi = None
                output.write(go.d)
                output.flush()
            else:
                raise TypeError(go)

    async def async_run(
            self,
            input: ta.Any,  # asyncio.StreamReader  # noqa
            output: ta.Any,  # asyncio.StreamWriter
    ) -> Result:
        gen = self.gen()

        gi: ta.Optional[bytes] = None
        while True:
            try:
                if gi is not None:
                    go = gen.send(gi)
                else:
                    go = next(gen)
            except StopIteration as e:
                return e.value

            if isinstance(go, self.Read):
                gi = await input.readexactly(go.sz)
            elif isinstance(go, self.Write):
                gi = None
                output.write(go.d)
                await output.drain()
            else:
                raise TypeError(go)


##


def pyremote_get_core_source() -> ta.Optional[str]:
    try:
        mod = sys.modules[__name__]
    except KeyError:
        return None

    import inspect
    return inspect.getsource(mod)


##


class PyremoteApi:
    def build_bootstrap_source(self, context_name: str) -> str:
        return pyremote_build_bootstrap_source(context_name)

    def bootstrap_finalize(self) -> PyremotePayloadRuntime:
        return pyremote_bootstrap_finalize()

    def make_driver(
            self,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions = PyremoteBootstrapOptions(),
    ) -> PyremoteBootstrapDriver:
        return PyremoteBootstrapDriver(
            payload_src,
            options,
        )

    def get_core_source(self) -> ta.Optional[str]:
        return pyremote_get_core_source()


pyremote = PyremoteApi()


########################################
# ../../../../omcore/rpc/configs.py


##


def _rpc_config_check_opt_timeout(v: ta.Optional[float]) -> None:
    if v is not None and (not math.isfinite(v) or v <= 0.):
        raise ValueError(f'timeout must be a positive finite number or None: {v!r}')


def _rpc_config_check_opt_limit(v: ta.Optional[int]) -> None:
    if v is not None and v < 1:
        raise ValueError(f'limit must be a positive integer or None: {v!r}')


@dc.dataclass(frozen=True)
class RpcConfig:
    """
    Every knob for an rpc pipeline and the connection driving it, from wire framing up through session policy. All
    timeouts are in seconds, and a value of None disables the corresponding timeout or limit.

    The defaults suit the toolbox's home use: two ends of the same code, over a stream the harness owns, exchanging
    requests which may legitimately run for a long time. In particular no request timeout is applied by default.
    """

    ##
    # wire

    # Enforced on both received and sent frames, excluding the length prefix. An oversized received frame is fatal to
    # the connection, as the stream cannot be resynchronized; an oversized sent message fails only that message.
    max_frame_bytes: int = 16 * 1024 * 1024

    ##
    # outbound requests

    default_request_timeout_s: ta.Optional[float] = None
    max_pending_outbound: ta.Optional[int] = 1024

    # Whether abandoning a sent request - because it timed out or its caller gave up - also sends the peer a cancel
    # envelope, so it may stop handling it.
    cancel_abandoned_requests: bool = True

    default_ping_timeout_s: ta.Optional[float] = 10.

    ##
    # inbound requests

    # How long the host may take to answer an inbound request before the session answers it with an error itself.
    inbound_handling_timeout_s: ta.Optional[float] = None

    max_inflight_inbound: ta.Optional[int] = 1024

    # What to do when the in-flight limit is reached: 'reject' answers further requests with a `busy` error
    # immediately, 'pause' stops reading from the transport until in-flight requests complete. Pausing is only safe for
    # pure server roles - a session which also sends requests can deadlock waiting for responses it has stopped
    # reading.
    inflight_limit_policy: ta.Literal['reject', 'pause'] = 'reject'

    ##
    # connection

    # Closes the connection if no complete envelope is received or sent for this long while nothing is in flight.
    idle_timeout_s: ta.Optional[float] = None

    # Keepalive: after this long without receiving anything, send a ping; if nothing at all is received within
    # `keepalive_timeout_s` of that, fail the connection. Both None means no keepalive handler is installed.
    keepalive_interval_s: ta.Optional[float] = None
    keepalive_timeout_s: ta.Optional[float] = None

    # Fails the connection if output cannot be flushed to the transport within this long.
    write_timeout_s: ta.Optional[float] = 30.

    # How long a graceful close waits for in-flight inbound requests to be answered before giving up on them.
    close_drain_timeout_s: ta.Optional[float] = 10.

    ##
    # policies

    # A response whose id matches no pending request. Late responses to timed-out or cancelled requests are expected,
    # so the default is to drop them.
    on_unmatched_response: ta.Literal['ignore', 'close'] = 'ignore'

    # What to do when the peer closes its side of the transport while inbound requests are in flight: 'close' aborts
    # them immediately, 'drain' waits for them to be answered (up to close_drain_timeout_s) so the responses still reach
    # a half-closed peer.
    on_peer_eof: ta.Literal['close', 'drain'] = 'close'

    # Whether inbound requests aborted by a graceful close or handling timeout are answered with an error response
    # before the connection closes.
    respond_to_aborted_inbound: bool = True

    # Whether sends share flushes. With no flush under way a send flushes at once, exactly as with this off; sends made
    # while one is under way wait for it, then share the next. A burst - many callers at once, or a server answering
    # many requests - so costs a few writes and flushes instead of one each, and a lone send costs what it did. Every
    # send is still reported sent only once its bytes are out. Off, each send flushes on its own.
    consolidate_flushes: bool = False

    ##
    # errors

    # Whether handler exceptions are reported to the peer with their traceback, bounded by `max_traceback_chars`.
    include_tracebacks: bool = True
    max_traceback_chars: int = 64 * 1024

    ##

    def __post_init__(self) -> None:
        if self.max_frame_bytes < 1:
            raise ValueError(self.max_frame_bytes)

        _rpc_config_check_opt_timeout(self.default_request_timeout_s)
        _rpc_config_check_opt_limit(self.max_pending_outbound)
        _rpc_config_check_opt_timeout(self.default_ping_timeout_s)

        _rpc_config_check_opt_timeout(self.inbound_handling_timeout_s)
        _rpc_config_check_opt_limit(self.max_inflight_inbound)
        if self.inflight_limit_policy not in ('reject', 'pause'):
            raise ValueError(self.inflight_limit_policy)

        _rpc_config_check_opt_timeout(self.idle_timeout_s)
        _rpc_config_check_opt_timeout(self.keepalive_interval_s)
        _rpc_config_check_opt_timeout(self.keepalive_timeout_s)
        if (self.keepalive_interval_s is None) != (self.keepalive_timeout_s is None):
            raise ValueError('keepalive_interval_s and keepalive_timeout_s must be set together')
        _rpc_config_check_opt_timeout(self.write_timeout_s)
        _rpc_config_check_opt_timeout(self.close_drain_timeout_s)

        if self.on_unmatched_response not in ('ignore', 'close'):
            raise ValueError(self.on_unmatched_response)
        if self.on_peer_eof not in ('close', 'drain'):
            raise ValueError(self.on_peer_eof)

        if self.max_traceback_chars < 0:
            raise ValueError(self.max_traceback_chars)

    def update(self, **kwargs: ta.Any) -> 'RpcConfig':
        return dc.replace(self, **kwargs)

    DEFAULT: ta.ClassVar['RpcConfig']


RpcConfig.DEFAULT = RpcConfig()


########################################
# ../../environment/remote/protocol.py
"""
The wire shape of the remote environment: the one request the host's `RemoteEnvironmentOps` makes of the agent's
`RemoteEnvironmentService`, and its result. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and
marshaled with the lite marshaler.
"""


##


REMOTE_ENVIRONMENT_INFO_METHOD = 'environment.info'


@dc.dataclass(frozen=True)
class RemoteEnvironmentInfoParams:
    cwd: ta.Optional[str]


@dc.dataclass(frozen=True)
class RemoteEnvironmentInfo:
    """The agent's `EnvironmentInfo`, less what only the host can say of it: that it is remote."""

    cwd: str

    system: str
    release: str
    machine: str

    hostname: str

    @dc.dataclass(frozen=True)
    class User:
        name: ta.Optional[str]
        home: ta.Optional[str]
        shell: ta.Optional[str]

    user: ta.Optional[User]

    container: ta.Optional[str]


########################################
# ../../fs/common.py
"""
Filesystem primitives shared by the local `FsOps` and the remote agent's filesystem service. Lite: this is included in
the remote agent amalgam, so it is Python 3.8 compatible and imports nothing but the standard library.
"""


##


class FsFileChangedError(RuntimeError):
    """A compare-before-write found the file's content no longer matching the digest it was read with."""


def fs_file_digest(data: ta.Union[bytes, bytearray, memoryview]) -> str:
    return hashlib.sha256(data).hexdigest()


def fs_resolve_path(path: str) -> str:
    """The absolute, symlink-resolved form of a path."""

    return os.path.abspath(os.path.realpath(path))


_FS_GLOB_MAGIC = frozenset('*?[')


def fs_glob_root(pattern: str) -> str:
    """Returns the non-pattern prefix of an absolute glob without touching the filesystem."""

    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)

    drive, tail = os.path.splitdrive(pattern)
    root = drive + os.sep

    for part in tail.lstrip(os.sep).split(os.sep):
        if any(c in part for c in _FS_GLOB_MAGIC):
            break
        root = os.path.join(root, part)

    return root


def fs_glob_paths(
        pattern: str,
        *,
        max_results: ta.Optional[int] = None,
) -> ta.Tuple[ta.List[str], bool]:
    """
    Returns an absolute pattern's matched paths as the glob produced them, and whether more were available than
    `max_results` allowed. Nothing is filtered: what a caller may see of the matches is the caller's to decide.
    """

    if max_results is not None and max_results < 0:
        raise ValueError(max_results)

    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    paths: ta.List[str] = []
    has_more = False
    for path in glob_.iglob(pattern, recursive=True):
        if max_results is not None and len(paths) >= max_results:
            has_more = True
            break

        paths.append(path)

    return paths, has_more


def fs_check_expected_digest(path: str, expected_digest: str) -> None:
    try:
        with open(path, 'rb') as f:  # noqa
            actual_digest = fs_file_digest(f.read())
    except FileNotFoundError:
        actual_digest = None

    if actual_digest != expected_digest:
        raise FsFileChangedError(f'File changed since it was read: {path!r}')


##


class FsStagedWrite:
    """
    A file being written next to its destination, invisible there until `commit` makes it so atomically, or `abort`
    discards it. Either finishes the stage and cleans up after it, as does a commit that fails. Content may arrive in
    any number of `write`s, so a caller which has it in pieces need not hold all of them at once.
    """

    def __init__(self, path: str) -> None:
        super().__init__()

        self._path = path

        self._tmp_dir: ta.Optional[str] = tempfile.mkdtemp(prefix='.omllm-write-', dir=os.path.dirname(path))
        self._tmp_path: ta.Optional[str] = os.path.join(self._tmp_dir, 'file')
        self._file: ta.Optional[ta.BinaryIO] = None
        self._size = 0
        self._finished = False

        try:
            fd = os.open(self._tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            try:
                self._file = os.fdopen(fd, 'wb')
            except BaseException:
                os.close(fd)
                raise
        except BaseException:
            self.abort()
            raise

    @property
    def path(self) -> str:
        return self._path

    @property
    def size(self) -> int:
        """How many bytes have been written so far."""

        return self._size

    @property
    def finished(self) -> bool:
        return self._finished

    def write(self, data: ta.Union[bytes, bytearray, memoryview]) -> None:
        if self._finished or self._file is None:
            raise RuntimeError('staged write is finished')
        self._file.write(data)
        self._size += len(data)

    def _close_file(self) -> None:
        if (f := self._file) is not None:
            self._file = None
            f.close()

    def abort(self) -> None:
        """Discards whatever is staged. Idempotent, and harmless after a commit."""

        self._finished = True
        self._close_file()

        if (tmp_path := self._tmp_path) is not None:
            self._tmp_path = None
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

        if (tmp_dir := self._tmp_dir) is not None:
            self._tmp_dir = None
            try:
                os.rmdir(tmp_dir)
            except FileNotFoundError:
                pass

    def commit(
            self,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> bool:
        """
        Makes the staged content visible at the destination, optionally replacing an existing regular file.
        `expected_digest` makes replacement fail if the current content no longer matches a previous read. Returns
        whether the file was created rather than replaced.
        """

        if self._finished or (tmp_path := self._tmp_path) is None:
            raise RuntimeError('staged write is finished')
        path = self._path

        try:
            # Everything buffered is on disk under the temporary name before that name is linked or renamed.
            self._close_file()

            try:
                lst = os.lstat(path)
            except FileNotFoundError:
                if expected_digest is not None:
                    raise FsFileChangedError(f'File changed since it was read: {path!r}') from None

                # A hard link makes the fully-written file visible without replacing a path which appeared after the
                # lstat above. Both names are in the destination directory, so they are necessarily on one filesystem.
                os.link(tmp_path, path)
                return True

            if not overwrite:
                raise FileExistsError(path)
            if not stat_.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                fs_check_expected_digest(path, expected_digest)

            # Preserve the replaced file's permissions; the rename itself is atomic.
            os.chmod(tmp_path, stat_.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            self._tmp_path = None  # Consumed by the rename: only the directory is left to remove.
            return False

        finally:
            self.abort()


def fs_write_file(
        path: str,
        content: ta.Union[bytes, bytearray, memoryview],
        *,
        overwrite: bool = False,
        expected_digest: ta.Optional[str] = None,
) -> bool:
    """
    Writes a complete file, optionally replacing an existing regular file. `expected_digest` makes replacement fail if
    the current content no longer matches a previous read. Returns whether the file was created rather than replaced.
    """

    stage = FsStagedWrite(path)
    try:
        stage.write(content)
    except BaseException:
        stage.abort()
        raise
    return stage.commit(
        overwrite=overwrite,
        expected_digest=expected_digest,
    )


########################################
# ../../../../omcore/asyncs/asynclite/base.py


##


class AsyncliteObject(Abstract):
    pass


class AsyncliteApi(Abstract):
    pass


##


class AsyncliteCloseable(Abstract):
    async def __aenter__(self: AsyncliteCloseableT) -> AsyncliteCloseableT:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        raise NotImplementedError


########################################
# ../../../../omcore/io/pipelines/core.py


##


class IoPipelineMessages(NamespaceClass):
    """Standard messages sent through a pipeline."""

    #

    class NeverInbound(Abstract):
        pass

    class NeverOutbound(Abstract):
        pass

    #

    class MayPropagate(Abstract):
        """
        These *may* be propagated all the way through the pipeline without being an error. These will be silently
        dropped when fed inbound and reaching the innermost pipeline position, but will still be emitted as pipeline
        output when fed outbound.
        """

    class MustPropagate(MayPropagate, Abstract):
        """
        These *must* be propagated all the way through the pipeline when sent in either direction. This is enforced via
        object identity - the same *instance* of the message must be seen at the end of the pipeline to be considered
        caught. This is intentional.
        """

    #

    class AfterFinalInput(Abstract):
        """
        These may be fed inbound at the pipeline boundary after FinalInput has been seen.

        FinalInput is only an *input* half-close - output may still flow until FinalOutput - so transport-originated
        control signals which concern output (notably writability) must remain deliverable afterwards. Ordinary input
        messages must not, and remain rejected.
        """

    class AfterShutdownOutput(Abstract):
        """
        These may reach the outbound pipeline terminal after ShutdownOutput has reached it.

        ShutdownOutput is only an *output* half-close - input continues until FinalInput - so control messages which
        concern input or driver interaction (notably read requests and deferred work) must remain deliverable
        afterwards. Ordinary output must not, and is rejected.
        """

    #

    class Pinning(Abstract):
        @property
        @abc.abstractmethod
        def pinned(self) -> ta.Optional[ta.Sequence['IoPipelineMessages.MustPropagate']]:
            raise NotImplementedError

    #

    @ta.final
    @dc.dataclass(frozen=True, eq=False)
    class InitialInput(NeverOutbound, MustPropagate):  # ~ Netty `ChannelInboundHandler::channelActive`
        """Signals that the inbound stream has begun producing input (`connected`)."""

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}()'

    @ta.final
    @dc.dataclass(frozen=True, eq=False)
    class FinalInput(NeverOutbound, MustPropagate):  # ~ Netty `ChannelInboundHandler::channelInactive`
        """
        Signals that the inbound stream has produced its final message (`eof`).

        This records peer/input completion only. It does not itself request outbound closure; an application or
        protocol policy may still produce output before sending FinalOutput.
        """

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}()'

    @ta.final
    @dc.dataclass(frozen=True)
    class Error(NeverOutbound, AfterFinalInput):
        """
        Signals an exception occurred in the pipeline.

        Errors can arise after input has ended - a failed write, a timeout, an aborted stream - so they remain
        deliverable at the pipeline boundary after FinalInput.
        """

        exc: BaseException

        direction: ta.Optional['IoPipelineDirection'] = None
        handler: ta.Optional['IoPipelineHandlerRef'] = None

    #

    class Completable(Abstract, ta.Generic[T]):
        # Management of completable state is implemented as 'hidden' / dynamic attributes to allow mixing in with
        # otherwise frozen dataclasses.

        # _completion_state: ta.Literal['pending', 'succeeded', 'failed'] = 'pending'
        # _completion_: _Completion

        @ta.final
        class _Completion:
            result: ta.Any
            exc: ta.Optional[BaseException]
            listeners: ta.Optional[ta.List[ta.Callable[[ta.Any], None]]] = None

        def is_done(self) -> bool:
            try:
                cps = self._completion_state  # type: ignore[attr-defined]
            except AttributeError:
                return False
            return cps != 'pending'

        def is_succeeded(self) -> bool:
            try:
                cps = self._completion_state  # type: ignore[attr-defined]
            except AttributeError:
                return False
            return cps == 'succeeded'

        def _outcome(self) -> _Completion:
            try:
                return self._completion_  # type: ignore[attr-defined]
            except AttributeError:
                raise StateIoPipelineError(
                    'A completable\'s outcome is only available from its completion listeners',
                ) from None

        def get_result(self) -> T:
            """The result, available only from a completion listener: outcomes are released with the listeners."""

            check.state(self._completion_state == 'succeeded')  # type: ignore[attr-defined]

            return self._outcome().result

        def is_failed(self) -> bool:
            try:
                cps = self._completion_state  # type: ignore[attr-defined]
            except AttributeError:
                return False
            return cps == 'failed'

        def get_exception(self) -> ta.Optional[BaseException]:
            """The exception, available only from a completion listener: outcomes are released with the listeners."""

            check.state(self._completion_state == 'failed')  # type: ignore[attr-defined]

            return self._outcome().exc

        def _completion(self) -> _Completion:
            try:
                return self._completion_  # type: ignore[attr-defined]
            except AttributeError:
                pass

            cpl = IoPipelineMessages.Completable._Completion()  # noqa
            object.__setattr__(self, '_completion_', cpl)
            return cpl

        def add_listener(self, fn: ta.Callable[['IoPipelineMessages.Completable[T]'], None]) -> None:
            check.state(not self.is_done())

            cpl = self._completion()
            if (lst := cpl.listeners) is None:
                lst = cpl.listeners = []
            lst.append(fn)

        def _bind_pipeline(self, pipeline: 'IoPipeline') -> None:
            check.state(not self.is_done())

            try:
                pipeline_ref = self._completion_pipeline_ref  # type: ignore[attr-defined]
            except AttributeError:
                object.__setattr__(self, '_completion_pipeline_ref', weakref.ref(pipeline))
            else:
                check.is_(pipeline_ref(), pipeline)

            pipeline._pending_completables[id(self)] = self  # noqa

        def _unbind_pipeline(self) -> None:
            try:
                pipeline_ref = self._completion_pipeline_ref  # type: ignore[attr-defined]
            except AttributeError:
                return

            object.__delattr__(self, '_completion_pipeline_ref')
            if (pipeline := pipeline_ref()) is not None:
                pipeline._pending_completables.pop(id(self), None)  # noqa

        def _finish(
                self,
                state: ta.Literal['succeeded', 'failed'],
                *,
                result: ta.Any = None,
                exc: ta.Optional[BaseException] = None,
        ) -> None:
            check.state(not self.is_done())

            object.__setattr__(self, '_completion_state', state)
            self._unbind_pipeline()

            try:
                cpl = self._completion_  # type: ignore[attr-defined]
            except AttributeError:
                return

            if state == 'succeeded':
                cpl.result = result
            else:
                cpl.exc = exc

            listeners = cpl.listeners
            cpl.listeners = None
            first_listener_exc: ta.Optional[BaseException] = None
            try:
                if listeners is not None:
                    for fn in listeners:
                        try:
                            fn(self)
                        except BaseException as listener_exc:  # noqa
                            if first_listener_exc is None:
                                first_listener_exc = listener_exc
            finally:
                object.__delattr__(self, '_completion_')

            if first_listener_exc is not None:
                raise first_listener_exc

        def set_succeeded(self, result: T) -> None:
            self._finish('succeeded', result=result)

        def set_failed(self, exc: ta.Optional[BaseException] = None) -> None:
            self._finish('failed', exc=exc)

    #

    @ta.final
    @dc.dataclass(frozen=True, eq=False)
    class FinalOutput(NeverInbound, MustPropagate, Completable[None]):  # ~ Netty `ChannelOutboundHandler::close`
        """
        Requests graceful output completion and driver termination.

        This is an ordered barrier, not an abort: handlers may retain it while flushing accepted output or completing
        protocol shutdown, and must forward it only after all output preceding it. Successful completion means that
        protocol shutdown reached the transport and the driver completed its graceful-output responsibility; it does
        not require closing a caller-owned transport or imply peer receipt. No output may reach the pipeline terminal
        after FinalOutput. Use pipeline/driver destruction for immediate abortive teardown.
        """

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}()'

    @ta.final
    @dc.dataclass(frozen=True, eq=False)
    class ShutdownOutput(NeverInbound, MustPropagate, Completable[None]):  # ~ Netty `DuplexChannel::shutdownOutput`
        """
        Ends output while input continues: an output half-close.

        This is an ordered barrier like FlushOutput: handlers emit all output accepted before it, and may retain it
        while finishing protocol-level output shutdown, then forward the same instance. Once it reaches the pipeline
        terminal only `AfterShutdownOutput` messages and FinalOutput may follow it there. Unlike FinalOutput it does not
        terminate the driver, which keeps delivering input; FinalOutput remains required to finish the pipeline.

        Successful completion means all preceding output crossed the driver's transport boundary and the transport's
        output half was shut down (for a socket, `shutdown(SHUT_WR)`). It does not imply peer receipt. A transport which
        cannot half-close fails the message and is otherwise left intact.
        """

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}()'

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class Defer(NeverInbound, AfterShutdownOutput, Pinning, Completable[T], ta.Generic[T]):
        fn: ta.Union[
            ta.Callable[['IoPipelineHandlerContext'], T],
            ta.Callable[[], T],
        ]

        no_context: bool = False

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}({self.fn!r}{", no_context=True" if self.no_context else ""})'

        # _: dc.KW_ONLY

        _ctx: ta.Optional['IoPipelineHandlerContext'] = dc.field(default=None, repr=False)

        _pinned: ta.Optional[ta.Sequence['IoPipelineMessages.MustPropagate']] = dc.field(default=None, repr=False)

        @property
        def pinned(self) -> ta.Optional[ta.Sequence['IoPipelineMessages.MustPropagate']]:
            return self._pinned


##


class IoPipelineHandlerNotification(Abstract):  # ~ Netty `ChannelHandler` methods
    """
    Directionless, private events sent to a specific handler that are not to be forwarded to any other handler in either
    direction.
    """


class IoPipelineHandlerNotifications(NamespaceClass):
    @ta.final
    @dc.dataclass(frozen=True)
    class Added(IoPipelineHandlerNotification):
        ctx: 'IoPipelineHandlerContext'

    @ta.final
    @dc.dataclass(frozen=True)
    class Removed(IoPipelineHandlerNotification):
        ctx: 'IoPipelineHandlerContext'


##


@ta.final
class IoPipelineHandlerRef(ta.Generic[T]):
    """
    Encapsulates a reference to a unique position of a handler instance in a pipeline, used at public api boundaries.

    Should the handler be removed from the relevant position in the pipeline, the ref instance becomes permanently
    invalidated.

    Note that this is definitionally identity hash/eq: given some valid ref, removing that ref from the pipeline and
    re-adding the same handler instance to the same effective position in a pipeline results in a different ref.
    """

    def __init__(self, *, _context: 'IoPipelineHandlerContext') -> None:
        self._context = _context
        self._pipeline = _context._pipeline  # noqa

    @property
    def pipeline(self) -> 'IoPipeline':
        return self._pipeline

    @property
    def handler(self) -> T:
        return self._context._handler  # type: ignore[return-value]  # noqa

    @property
    def name(self) -> ta.Optional[str]:
        return self._context._name  # noqa

    @property
    def invalidated(self) -> bool:
        return self._context._invalidated  # noqa

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}'
            f'{"!INVALIDATED" if self.invalidated else ""}'
            f'{f"<{self.name!r}>" if self.name is not None else ""}'
            f'<context@{id(self._context):x}>'
            f'({self.handler!r})'  # {f"@{id(self.handler):x}"})'
        )


IoPipelineHandlerRef_ = IoPipelineHandlerRef['IoPipelineHandler']  # ta.TypeAlias  # om-amalg-typing-no-move  # noqa


##


@ta.final
class IoPipelineHandlerContext:
    """
    The embodiment of an instance of a handler at a position in a pipeline. Passed to IoPipelineHandler methods,
    providing handler-specific access to the pipeline. As instances of `ShareableIoPipelineHandler` may validly be
    simultaneously present at multiple positions in a pipeline, a single handler may have multiple active context
    instances associated with it in any given pipeline.

    Instances of this class are considered private to a handler instance and are not to be cached or shared in any way.
    The method names reflect this: they are operations available to the handler in the context of a pipeline processing
    operation.
    """

    def __init__(
            self,
            *,
            _pipeline: 'IoPipeline',
            _handler: 'IoPipelineHandler',

            _name: ta.Optional[str] = None,
    ) -> None:
        super().__init__()

        self.__pipeline_ref = weakref.ref(_pipeline)
        self._handler: ta.Final[IoPipelineHandler] = _handler

        self._name: ta.Final[ta.Optional[str]] = _name

        self.__ref_ref: ta.Optional[weakref.ReferenceType] = None

        hty = type(_handler)
        self._handles_inbound = hty.inbound is not IoPipelineHandler.inbound
        self._handles_outbound = hty.outbound is not IoPipelineHandler.outbound

    _next_in: 'IoPipelineHandlerContext'  # 'next', owning
    __next_out_ref: weakref.ReferenceType  # 'prev', non-owning

    @property
    def _next_out(self) -> 'IoPipelineHandlerContext':
        return check.not_none(self.__next_out_ref())

    @_next_out.setter
    def _next_out(self, ctx: 'IoPipelineHandlerContext') -> None:
        self.__next_out_ref = weakref.ref(ctx)

    @_next_out.deleter
    def _next_out(self) -> None:
        del self.__next_out_ref

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}@{id(self):x}'
            f'{"!INVALIDATED" if self._invalidated else ""}'
            f'{f"<{self._name!r}>" if self._name is not None else ""}'
            f'<pipeline@{id(self.pipeline):x}>'
            f'({self._handler!r})'  # @{id(self._handler):x})'
        )

    @property
    def ref(self) -> IoPipelineHandlerRef_:
        if (ref_ref := self.__ref_ref) is not None and (ref := ref_ref()) is not None:
            return ref

        ref = IoPipelineHandlerRef(_context=self)
        self.__ref_ref = weakref.ref(ref)
        return ref

    @property
    def _pipeline(self) -> 'IoPipeline':
        return check.not_none(self.__pipeline_ref())

    @property
    def pipeline(self) -> 'IoPipeline':
        return self._pipeline

    @property
    def services(self) -> 'IoPipelineServices':  # noqa
        return self._pipeline._services  # noqa

    @property
    def handler(self) -> 'IoPipelineHandler':
        return self._handler

    @property
    def name(self) -> ta.Optional[str]:
        return self._name

    #

    def defer(
            self,
            fn: ta.Callable[['IoPipelineHandlerContext'], T],
            *,
            pin: ta.Optional[ta.Sequence[IoPipelineMessages.MustPropagate]] = None,
    ) -> IoPipelineMessages.Defer[T]:
        return self._pipeline._defer(self, fn, pin=pin)  # noqa

    def defer_no_context(
            self,
            fn: ta.Callable[[], T],
            *,
            pin: ta.Optional[ta.Sequence[IoPipelineMessages.MustPropagate]] = None,
    ) -> IoPipelineMessages.Defer[T]:
        return self._pipeline._defer(self, fn, no_context=True, pin=pin)  # noqa

    #

    _invalidated = False

    @property
    def invalidated(self) -> bool:
        return self._invalidated

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class StorageKey(ta.Generic[T]):
        name: str

    @ta.final
    class Storage:
        def __init__(self) -> None:
            self.__dict: ta.Dict[IoPipelineHandlerContext.StorageKey, ta.Any] = {}

        @property
        def dict(self) -> ta.Dict['IoPipelineHandlerContext.StorageKey', ta.Any]:
            return self.__dict

        def __getitem__(self, key: 'IoPipelineHandlerContext.StorageKey[T]') -> T:
            return self.__dict[key]

        @ta.overload
        def get(
                self,
                key: 'IoPipelineHandlerContext.StorageKey[T]',
                default: T,
                /,
        ) -> T:
            ...

        @ta.overload
        def get(
                self,
                key: 'IoPipelineHandlerContext.StorageKey[T]',
                default: ta.Optional[T] = None,
                /,
        ) -> ta.Optional[T]:
            ...

        def get(self, key, default=None, /):
            return self.__dict.get(key, default)

        def __setitem__(self, key: 'IoPipelineHandlerContext.StorageKey[T]', value: T) -> None:
            self.__dict[key] = value

        def __delitem__(self, key: 'IoPipelineHandlerContext.StorageKey[T]') -> None:
            del self.__dict[key]

        def __len__(self) -> int:
            return len(self.__dict)

        def __contains__(self, key: 'IoPipelineHandlerContext.StorageKey[T]') -> bool:
            return key in self.__dict

        def __iter__(self) -> ta.Iterator['IoPipelineHandlerContext.StorageKey[T]']:
            return iter(self.__dict)

        def items(self) -> ta.Iterator[ta.Tuple['IoPipelineHandlerContext.StorageKey[T]', T]]:
            return iter(self.__dict.items())

    _storage_: Storage

    @property
    def storage(self) -> Storage:
        try:
            return self._storage_
        except AttributeError:
            pass
        self._storage_ = ret = IoPipelineHandlerContext.Storage()
        return ret

    #

    def _notify(self, no: IoPipelineHandlerNotification) -> None:
        # Avoids `check._unpack_isinstance_spec` machinery unless it matches.
        if not isinstance(no, IoPipelineHandlerNotification):
            check.isinstance(no, IoPipelineHandlerNotification)  # type: ignore[unreachable,unused-ignore]
        check.state(self._pipeline._execution_depth > 0)  # noqa

        self._handler.notify(self, no)

    ##
    # Feeding `type`'s is forbidden as it's almost always going to be an error - usually forgetting to instantiate a
    # marker dataclass)

    _FORBIDDEN_INBOUND_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.NeverInbound,
        IoPipelineHandlerNotification,
        type,
        type(None),
    )

    def _inbound(self, msg: ta.Any) -> None:
        check.state(not self._invalidated, ContextInvalidatedIoPipelineError)
        check.state((pipeline := self._pipeline)._state == IoPipeline.State.READY and pipeline._execution_depth > 0)  # noqa

        # Avoids `check._unpack_isinstance_spec` machinery unless it matches.
        if isinstance(msg, self._FORBIDDEN_INBOUND_TYPES):
            check.not_isinstance(msg, self._FORBIDDEN_INBOUND_TYPES)

        if (mt := pipeline._message_tap) is not None:  # noqa
            mt(self, 'inbound', msg)

        if isinstance(msg, IoPipelineMessages.MustPropagate):
            pipeline._propagation.add_must(self, 'inbound', msg)  # noqa

        try:
            self._handler.inbound(self, msg)

        except pipeline._all_never_handle_exceptions:  # type: ignore[misc]  # noqa
            raise

        except BaseException as e:
            if self._handling_error or pipeline._config.raise_immediately:  # noqa
                raise
            self._handle_error(e, 'inbound')

    _FORBIDDEN_OUTBOUND_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.NeverOutbound,
        IoPipelineHandlerNotification,
        type,
        type(None),
    )

    def _outbound(self, msg: ta.Any) -> None:
        check.state(not self._invalidated, ContextInvalidatedIoPipelineError)
        check.state((pipeline := self._pipeline)._state == IoPipeline.State.READY and pipeline._execution_depth > 0)  # noqa

        # Avoids `check._unpack_isinstance_spec` machinery unless it matches.
        if isinstance(msg, self._FORBIDDEN_OUTBOUND_TYPES):
            check.not_isinstance(msg, self._FORBIDDEN_OUTBOUND_TYPES)

        if (mt := pipeline._message_tap) is not None:  # noqa
            mt(self, 'outbound', msg)

        try:
            if isinstance(msg, IoPipelineMessages.Completable):
                msg._bind_pipeline(pipeline)  # noqa

            if isinstance(msg, IoPipelineMessages.MustPropagate):
                pipeline._propagation.add_must(self, 'outbound', msg)  # noqa

            self._handler.outbound(self, msg)

        except pipeline._all_never_handle_exceptions as e:  # type: ignore[misc]  # noqa
            if isinstance(msg, IoPipelineMessages.Completable) and not msg.is_done():
                msg.set_failed(e)
            raise

        except BaseException as e:
            if isinstance(msg, IoPipelineMessages.Completable) and not msg.is_done():
                msg.set_failed(e)
            if self._handling_error or pipeline._config.raise_immediately:  # noqa
                raise
            self._handle_error(e, 'outbound')

    #

    def _run_deferred(self, dfl: IoPipelineMessages.Defer) -> None:
        check.state(not self._invalidated, ContextInvalidatedIoPipelineError)
        check.state((pipeline := self._pipeline)._state == IoPipeline.State.READY and pipeline._execution_depth > 0)  # noqa

        check.state(dfl._ctx is self)  # noqa

        try:
            if dfl.no_context:
                res = dfl.fn()  # type: ignore[call-arg]
            else:
                res = dfl.fn(self)  # type: ignore[call-arg]

        except pipeline._all_never_handle_exceptions:  # type: ignore[misc]  # noqa
            raise

        except BaseException as e:  # noqa
            # Already done if the callback destroyed the pipeline, which fails every pending completable - this one
            # among them.
            if not dfl.is_done():
                dfl.set_failed(e)

            if self._handling_error or pipeline._config.raise_immediately:  # noqa
                raise
            if not self._invalidated:
                self._handle_error(e, 'inbound')

        else:
            if not dfl.is_done():
                dfl.set_succeeded(res)

    #

    _handling_error: bool = False

    def _handle_error(self, e: BaseException, direction: 'IoPipelineDirection') -> None:
        check.state(not self._handling_error)
        self._handling_error = True

        try:
            try:
                self.feed_in(IoPipelineMessages.Error(e, direction, self.ref))

            except self._pipeline._all_never_handle_exceptions:  # type: ignore[misc]  # noqa
                raise

            except BaseException as e2:  # noqa
                raise

        finally:
            self._handling_error = False

    ##
    # The following overloads attempts to catch invalid inputs statically, but there's no explicit way to do this in
    # mypy - the following trick only works if there's an unconditional statement after the attempted calls, but it's
    # better than nothing.

    @ta.overload
    def feed_in(
            self,
            msg: ta.Union[
                IoPipelineMessages.NeverInbound,
                IoPipelineHandlerNotification,
                type,
                None,
            ],
    ) -> 'ta.Never':
        ...

    @ta.overload
    def feed_in(self, msg: object) -> None:
        ...

    def feed_in(self, msg):  # ~ Netty `ChannelInboundInvoker::fireChannelRead`
        if self._invalidated:
            raise ContextInvalidatedIoPipelineError
        nxt = self._next_in
        while not nxt._handles_inbound:  # noqa
            nxt = nxt._next_in  # noqa
        nxt._inbound(msg)  # noqa

    @ta.overload
    def feed_out(
            self,
            msg: ta.Union[
                IoPipelineMessages.NeverOutbound,
                IoPipelineHandlerNotification,
                type,
                None,
            ],
    ) -> 'ta.Never':
        ...

    @ta.overload
    def feed_out(self, msg: object) -> None:
        ...

    def feed_out(self, msg):  # ~ Netty `ChannelOutboundInvoker::write`
        if self._invalidated:
            raise ContextInvalidatedIoPipelineError
        nxt = self._next_out  # noqa
        while not nxt._handles_outbound:  # noqa
            nxt = nxt._next_out  # noqa
        nxt._outbound(msg)  # noqa

    #

    def feed_final_output(self) -> IoPipelineMessages.FinalOutput:
        msg = IoPipelineMessages.FinalOutput()
        self.feed_out(msg)
        return msg

    def feed_shutdown_output(self) -> IoPipelineMessages.ShutdownOutput:
        msg = IoPipelineMessages.ShutdownOutput()
        self.feed_out(msg)
        return msg

    #

    def mark_propagated(
            self,
            direction: 'IoPipelineDirection',
            msg: IoPipelineMessages.MustPropagate,
    ) -> None:
        self._pipeline._propagation.remove_must(self, direction, msg)  # noqa


##


class IoPipelineHandler(Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        if not (
            cls.__hash__ is object.__hash__ and
            cls.__eq__ is object.__eq__ and
            cls.__ne__ is object.__ne__
        ):
            raise TypeError(
                f'IoPipelineHandler subclass {cls.__name__} must not override __hash__, __eq__ or __ne__',
            )

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        pass

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)


class ShareableIoPipelineHandler(IoPipelineHandler, Abstract):
    pass


##


IoPipelineDirection = ta.Literal[  # ta.TypeAlias  # om-amalg-typing-no-move
    'inbound',
    'outbound',
]

IoPipelineDirectionOrDuplex = ta.Literal[  # ta.TypeAlias  # om-amalg-typing-no-move
    IoPipelineDirection,
    'duplex',
]

IoPipelineUpdate = ta.Literal[  # ta.TypeAlias  # om-amalg-typing-no-move
    'added',
    'removed',
]

IoPipelineHandlerUpdate = ta.Literal[  # ta.TypeAlias  # om-amalg-typing-no-move
    'adding',
    'added',
    'removing',
    'removed',
]


##


class IoPipelineService(Abstract):
    def pipeline_update(self, pipeline: 'IoPipeline', kind: IoPipelineUpdate) -> None:
        pass

    def handler_update(self, handler_ref: IoPipelineHandlerRef, kind: IoPipelineHandlerUpdate) -> None:
        pass

    def pipeline_enter(self, pipeline: 'IoPipeline') -> None:
        pass

    def pipeline_exit(self, pipeline: 'IoPipeline') -> None:
        pass


@ta.final
class IoPipelineServices:
    def __init__(self, lst: ta.Sequence[IoPipelineService]) -> None:
        self._lst = lst

        self._by_type_cache: ta.Dict[type, ta.Sequence[ta.Any]] = {}
        self._single_by_type_cache: ta.Dict[type, ta.Optional[ta.Any]] = {}

        self._handles_pipeline_update = handles_pipeline_update = []
        self._handles_handler_update = handles_handler_update = []
        self._handles_pipeline_enter = handles_pipeline_enter = []
        self._handles_pipeline_exit = handles_pipeline_exit = []

        for svc in lst:
            sty = type(svc)
            if sty.pipeline_update is not IoPipelineService.pipeline_update:
                handles_pipeline_update.append(svc)
            if sty.handler_update is not IoPipelineService.handler_update:
                handles_handler_update.append(svc)
            if sty.pipeline_enter is not IoPipelineService.pipeline_enter:
                handles_pipeline_enter.append(svc)
            if sty.pipeline_exit is not IoPipelineService.pipeline_exit:
                handles_pipeline_exit.append(svc)

    _handles_pipeline_update: ta.Sequence[IoPipelineService]
    _handles_handler_update: ta.Sequence[IoPipelineService]
    _handles_pipeline_enter: ta.Sequence[IoPipelineService]
    _handles_pipeline_exit: ta.Sequence[IoPipelineService]

    _EMPTY: ta.ClassVar['IoPipelineServices']

    @classmethod
    def of(cls, obj: ta.Union['IoPipelineServices', ta.Sequence[IoPipelineService]]) -> 'IoPipelineServices':  # noqa
        if isinstance(obj, cls):
            return obj
        elif not obj:
            return cls._EMPTY
        else:
            return cls(list(obj))

    def __len__(self) -> int:
        return len(self._lst)

    def __iter__(self) -> ta.Iterator[IoPipelineService]:
        return iter(self._lst)

    def __contains__(self, item: IoPipelineService) -> bool:
        return item in self._lst

    @dc.dataclass(frozen=True)
    class _ServiceType(ta.Generic[T]):
        """This is entirely just a workaround for mypy's `type-abstract` deficiency."""

        ty: ta.Type[T]

    def find_all(self, ty: ta.Union[_ServiceType[T], ta.Type[T]]) -> ta.Sequence[T]:
        if isinstance(ty, self._ServiceType):
            ty = ty.ty

        try:
            return self._by_type_cache[ty]
        except KeyError:
            pass

        self._by_type_cache[ty] = ret = [svc for svc in self._lst if isinstance(svc, ty)]
        return ret

    def find(self, ty: ta.Union[_ServiceType[T], ta.Type[T]]) -> ta.Optional[T]:
        if isinstance(ty, self._ServiceType):
            ty = ty.ty

        try:
            return self._single_by_type_cache[ty]
        except KeyError:
            pass

        self._single_by_type_cache[ty] = ret = check.opt_single(self.find_all(ty))
        return ret

    def __getitem__(self, ty: ta.Union[_ServiceType[T], ta.Type[T]]) -> T:
        if (svc := self.find(ty)) is None:
            raise KeyError(ty)
        return svc


IoPipelineServices._EMPTY = IoPipelineServices([])  # noqa


##


class IoPipelineMetadata(Abstract):
    pass


@ta.final
class IoPipelineMetadatas:
    def __init__(self, lst: ta.Sequence[IoPipelineMetadata]) -> None:
        dct: ta.Dict[type, ta.Any] = {}
        for md in lst:
            mty = type(md)
            check.not_in(mty, dct)
            dct[mty] = md
        self._dct = dct

    _EMPTY: ta.ClassVar['IoPipelineMetadatas']

    @classmethod
    def of(cls, obj: ta.Union['IoPipelineMetadatas', ta.Sequence[IoPipelineMetadata]]) -> 'IoPipelineMetadatas':  # noqa
        if isinstance(obj, cls):
            return obj
        elif not obj:
            return cls._EMPTY
        else:
            return cls(list(obj))

    def __len__(self) -> int:
        return len(self._dct)

    def __contains__(self, ty: ta.Type[IoPipelineMetadata]) -> bool:
        return ty in self._dct

    def __iter__(self) -> ta.Iterator[IoPipelineMetadata]:
        return iter(self._dct.values())

    @dc.dataclass(frozen=True)
    class MetadataType(ta.Generic[IoPipelineMetadataT]):
        """This is entirely just a workaround for mypy's `type-abstract` deficiency."""

        ty: ta.Type[IoPipelineMetadataT]

    def __getitem__(
            self,
            ty: ta.Union[
                MetadataType[IoPipelineMetadataT],
                ta.Type[IoPipelineMetadataT],
            ],
    ) -> IoPipelineMetadataT:
        if isinstance(ty, self.MetadataType):
            ty = ty.ty

        return self._dct[ty]

    @ta.overload
    def get(
            self,
            ty: ta.Union[
                MetadataType[IoPipelineMetadataT],
                ta.Type[IoPipelineMetadataT],
            ],
            default: IoPipelineMetadataT,
            /,
    ) -> IoPipelineMetadataT:
        ...

    @ta.overload
    def get(
            self,
            ty: ta.Union[
                MetadataType[IoPipelineMetadataT],
                ta.Type[IoPipelineMetadataT],
            ],
            default: ta.Optional[IoPipelineMetadataT] = None,
            /,
    ) -> ta.Optional[IoPipelineMetadataT]:
        ...

    def get(self, ty, default=None, /):
        if isinstance(ty, self.MetadataType):
            ty = ty.ty

        return self._dct.get(ty, default)


IoPipelineMetadatas._EMPTY = IoPipelineMetadatas([])  # noqa


##


@ta.final
class _IoPipelinePropagation:
    @dc.dataclass()
    class _PendingMustEntry:
        msg: ta.Any
        direction: IoPipelineDirection
        last_seen: IoPipelineHandlerContext
        pinned_by: ta.Optional[IoPipelineMessages.Pinning] = None

    def __init__(self, p: 'IoPipeline') -> None:
        self.__p_ref = weakref.ref(p)

        if not self._p._config.disable_propagation_checking:  # noqa
            self._pending_must: ta.Final[ta.Dict[int, _IoPipelinePropagation._PendingMustEntry]] = {}

    @property
    def _p(self) -> 'IoPipeline':
        return check.not_none(self.__p_ref())

    def add_must(
            self,
            ctx: IoPipelineHandlerContext,
            direction: IoPipelineDirection,
            msg: IoPipelineMessages.MustPropagate,
    ) -> None:
        if self._p._config.disable_propagation_checking:  # noqa
            return

        i = id(msg)
        try:
            x = self._pending_must[i]
        except KeyError:
            self._pending_must[i] = _IoPipelinePropagation._PendingMustEntry(  # noqa
                msg,
                direction,
                ctx,
            )
            return

        check.is_(msg, x.msg)
        check.equal(direction, x.direction)
        check.state(x.pinned_by is None)
        x.last_seen = ctx

    def pin_musts(
            self,
            pinning: IoPipelineMessages.Pinning,
    ) -> None:
        if self._p._config.disable_propagation_checking or not (lst := pinning.pinned):  # noqa
            return

        for msg in lst:
            x = self._pending_must[id(msg)]
            check.none(x.pinned_by)
            x.pinned_by = pinning

    def unpin_musts(
            self,
            pinning: IoPipelineMessages.Pinning,
    ) -> None:
        if self._p._config.disable_propagation_checking or not (lst := pinning.pinned):  # noqa
            return

        for msg in lst:
            x = self._pending_must[id(msg)]
            check.is_(x.pinned_by, pinning)
            x.pinned_by = None

    def remove_must(
            self,
            ctx: IoPipelineHandlerContext,
            direction: IoPipelineDirection,
            msg: IoPipelineMessages.MustPropagate,
    ) -> None:
        if self._p._config.disable_propagation_checking:  # noqa
            return

        i = id(msg)
        try:
            x = self._pending_must.pop(i)
        except KeyError:
            raise MessageNotPropagatedIoPipelineError.new_single(
                direction,
                msg,
                last_seen=ctx.ref,  # noqa
            ) from None

        if (
                x.msg is not msg or
                x.direction != direction or
                x.pinned_by is not None
        ):
            raise MessageNotPropagatedIoPipelineError.new_single(
                direction,
                msg,
                last_seen=ctx.ref,  # noqa
            )

    def check_and_clear(self) -> None:
        if self._p._config.disable_propagation_checking:  # noqa
            return

        if not self._pending_must:
            return

        il: ta.List[ta.Tuple[ta.Any, ta.Any]] = []
        ol: ta.List[ta.Tuple[ta.Any, ta.Any]] = []

        for x in self._pending_must.values():
            if x.pinned_by is None:
                (il if x.direction == 'inbound' else ol).append((x.msg, x.last_seen.ref))  # noqa

        if not (il or ol):
            return

        e = MessageNotPropagatedIoPipelineError.new(
            inbound_with_last_seen=il,
            outbound_with_last_seen=ol,
        )

        for lst in (il, ol):
            for msg, _ in lst:
                del self._pending_must[id(msg)]

        raise e


##


IoPipelineMessageTap = ta.Callable[  # ta.TypeAlias  # om-amalg-typing-no-move
    [
        IoPipelineHandlerContext,
        IoPipelineDirection,
        ta.Any,
    ],
    None,
]


IoPipelineMessageTapTuple = ta.Tuple[  # ta.TypeAlias  # om-amalg-typing-no-move
    IoPipelineHandlerContext,
    IoPipelineDirection,
    ta.Any,
]


class ListIoPipelineMessageTap(ta.Sequence[IoPipelineMessageTapTuple]):
    def __init__(self, lst: ta.Optional[ta.List[IoPipelineMessageTapTuple]] = None) -> None:
        super().__init__()

        if lst is None:
            lst = []
        self.lst: ta.List[IoPipelineMessageTapTuple] = lst  # noqa

    def __iter__(self) -> ta.Iterator[IoPipelineMessageTapTuple]:
        return iter(self.lst)

    def __len__(self) -> int:
        return len(self.lst)

    def __getitem__(self, index):
        return self.lst[index]

    def __call__(
            self,
            ctx: IoPipelineHandlerContext,
            direction: IoPipelineDirection,
            msg: ta.Any,
    ) -> None:
        self.lst.append((ctx, direction, msg))


##


@ta.final
class IoPipeline:
    @ta.final
    @dc.dataclass(frozen=True)
    class Config:
        # TODO: 'close'? 'deadletter'? combination? composition? ...
        inbound_terminal: ta.Literal['drop', 'raise'] = 'raise'

        disable_propagation_checking: bool = False

        raise_immediately: bool = False

        def __post_init__(self) -> None:
            check.in_(self.inbound_terminal, ('drop', 'raise'))

        #

        def update(self, **kwargs: ta.Any) -> 'IoPipeline.Config':
            return dc.replace(self, **kwargs)

        DEFAULT: ta.ClassVar['IoPipeline.Config']

    Config.DEFAULT = Config()

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class Spec:
        # Initial handlers are optional - handlers may be freely added and removed later.
        handlers: ta.Sequence[IoPipelineHandler] = ()

        config: 'IoPipeline.Config' = dc.field(default_factory=lambda: IoPipeline.Config.DEFAULT)

        # _: dc.KW_ONLY

        # Metadata and ervices are fixed for the lifetime of the pipeline.
        metadata: ta.Union[ta.Sequence[IoPipelineMetadata], IoPipelineMetadatas] = ()
        services: ta.Union[ta.Sequence[IoPipelineService], IoPipelineServices] = ()

        #

        def update_config(self, **kwargs: ta.Any) -> 'IoPipeline.Spec':
            return dc.replace(self, config=self.config.update(**kwargs))

    @classmethod
    def new(
            cls,
            handlers: ta.Sequence[IoPipelineHandler] = (),
            config: 'IoPipeline.Config' = Config.DEFAULT,
            *,
            metadata: ta.Union[ta.Sequence[IoPipelineMetadata], IoPipelineMetadatas] = (),
            services: ta.Union[ta.Sequence[IoPipelineService], IoPipelineServices] = (),
    ) -> 'IoPipeline':
        return cls(IoPipeline.Spec(
            handlers=handlers,
            config=config,
            metadata=metadata,
            services=services,
        ))

    #

    def __init__(
            self,
            spec: Spec,
            *,
            never_handle_exceptions: ta.Tuple[type, ...] = (),
            message_tap: ta.Optional[IoPipelineMessageTap] = None,
            on_state_change: ta.Optional[ta.Callable[['IoPipeline'], None]] = None,
    ) -> None:
        super().__init__()

        self._config: ta.Final[IoPipeline.Config] = spec.config
        self._never_handle_exceptions = never_handle_exceptions
        self._message_tap = message_tap
        self._on_state_change = on_state_change

        self._metadata: ta.Final[IoPipelineMetadatas] = IoPipelineMetadatas.of(spec.metadata)
        self._services: ta.Final[IoPipelineServices] = IoPipelineServices.of(spec.services)

        #

        self._all_never_handle_exceptions: ta.Tuple[type, ...] = (
            UnhandleableIoPipelineError,
            *never_handle_exceptions,
        )

        self._propagation: _IoPipelinePropagation = _IoPipelinePropagation(self)

        #

        self._output: ta.Final[IoPipeline._Output] = IoPipeline._Output()

        self._pending_completables: ta.Final[ta.Dict[int, IoPipelineMessages.Completable]] = {}

        #

        self._outermost = outermost = IoPipelineHandlerContext(
            _pipeline=self,
            _handler=IoPipeline._Outermost(),
        )
        self._innermost = innermost = IoPipelineHandlerContext(
            _pipeline=self,
            _handler=IoPipeline._Innermost(),
        )

        # Explicitly does not form a ring, iteration past the outermost/innermost is always an error and will
        # intentionally raise AttributeError if not caught earlier.
        outermost._next_in = innermost  # noqa
        innermost._next_out = outermost  # noqa

        self._unique_contexts: ta.Final[ta.Dict[IoPipelineHandler, IoPipelineHandlerContext]] = {}
        self._shareable_contexts: ta.Final[ta.Dict[ShareableIoPipelineHandler, ta.Set[IoPipelineHandlerContext]]] = {}  # noqa

        self._contexts_by_name: ta.Final[ta.Dict[str, IoPipelineHandlerContext]] = {}

        #

        self._set_state(IoPipeline.State.READY)

        #

        try:
            for svc in self._services._handles_pipeline_update:  # noqa
                svc.pipeline_update(self, 'added')

            for h in spec.handlers:
                self.add_innermost(h)

        except self._all_never_handle_exceptions:  # type: ignore[misc]
            raise

        except BaseException:  # noqa
            self.destroy()
            raise

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> Config:
        return self._config

    ##
    # state

    class State(enum.Enum):
        NEW = 'new'
        READY = 'ready'
        DESTROYING = 'destroying'
        DESTROYED = 'destroyed'

    _state: State = State.NEW

    def _set_state(self, state: State) -> None:
        if self._state == state:
            return
        self._state = state
        if (cb := self._on_state_change) is not None:
            cb(self)

    @property
    def state(self) -> State:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state is IoPipeline.State.READY

    #

    _saw_any_input = False
    _saw_initial_input = False
    _saw_final_input = False
    _saw_final_output = False
    _saw_shutdown_output = False

    @property
    def saw_any_input(self) -> bool:
        return self._saw_any_input

    @property
    def saw_initial_input(self) -> bool:
        return self._saw_initial_input

    @property
    def saw_final_input(self) -> bool:
        return self._saw_final_input  # Note: only 'pipeline-level'

    @property
    def saw_final_output(self) -> bool:
        return self._saw_final_output

    @property
    def saw_shutdown_output(self) -> bool:
        return self._saw_shutdown_output

    ##
    # sub-collections

    @property
    def metadata(self) -> IoPipelineMetadatas:
        return self._metadata

    @property
    def services(self) -> IoPipelineServices:
        return self._services

    ##
    # execution

    _execution_depth = 0

    def _step_in(self) -> None:
        self._execution_depth += 1

        if self._execution_depth == 1:
            for svc in self._services._handles_pipeline_enter:  # noqa
                svc.pipeline_enter(self)

    def _step_out(self) -> None:
        check.state(self._execution_depth > 0)

        self._execution_depth -= 1

        if not self._execution_depth:
            for svc in self._services._handles_pipeline_exit:  # noqa
                svc.pipeline_exit(self)

            self._propagation.check_and_clear()

    @ta.final
    class _EnterContextManager:
        def __init__(self, p: 'IoPipeline') -> None:
            self._p = p

        def __enter__(self) -> None:
            self._p._step_in()  # noqa

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            self._p._step_out()  # noqa

    def enter(self) -> ta.ContextManager[None]:
        return self._EnterContextManager(self)

    #

    def _notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        self._step_in()
        try:
            ctx._notify(no)  # noqa

        finally:
            self._step_out()

    def notify(self, handler_ref: IoPipelineHandlerRef, no: IoPipelineHandlerNotification) -> None:
        ctx = handler_ref._context  # noqa
        check.is_(ctx._pipeline, self)  # noqa
        self._notify(ctx, no)

    #

    def _feed_in_to(self, ctx: IoPipelineHandlerContext, msgs: ta.Iterable[ta.Any]) -> None:
        self._step_in()
        try:
            # The input lifetime - one InitialInput, then input until FinalInput - is transport input crossing the
            # pipeline boundary. A message injected at a handler's position is not that, and is not checked against it.
            boundary = ctx is self._outermost
            for msg in msgs:
                if boundary:
                    if self._saw_final_input:
                        if not isinstance(msg, IoPipelineMessages.AfterFinalInput):
                            raise SawFinalInputIoPipelineError
                    elif isinstance(msg, IoPipelineMessages.FinalInput):
                        self._saw_final_input = True

                    if isinstance(msg, IoPipelineMessages.InitialInput):
                        if self._saw_any_input:
                            raise SawInitialInputIoPipelineError
                        check.state(not self._saw_initial_input)
                        self._saw_initial_input = True
                    self._saw_any_input = True

                ctx._inbound(msg)  # noqa

        finally:
            self._step_out()

    def feed_in_to(self, handler_ref: IoPipelineHandlerRef, *msgs: ta.Any) -> None:
        # TODO: remove? internal only? used by replace-self pattern
        ctx = handler_ref._context  # noqa
        check.is_(ctx._pipeline, self)  # noqa
        self._feed_in_to(ctx, msgs)

    def feed_in(self, *msgs: ta.Any) -> None:
        self._feed_in_to(self._outermost, msgs)  # noqa

    def feed_initial_input(self) -> None:
        self._feed_in_to(self._outermost, (IoPipelineMessages.InitialInput(),))  # noqa

    def feed_final_input(self) -> None:
        self._feed_in_to(self._outermost, (IoPipelineMessages.FinalInput(),))  # noqa

    #

    def _defer(
            self,
            ctx: IoPipelineHandlerContext,
            fn: ta.Union[
                ta.Callable[[IoPipelineHandlerContext], T],
                ta.Callable[[], T],
            ],
            *,
            no_context: bool = False,
            pin: ta.Optional[ta.Sequence[IoPipelineMessages.MustPropagate]] = None,
    ) -> IoPipelineMessages.Defer[T]:
        check.is_(ctx._pipeline, self)  # noqa
        check.state(not ctx._invalidated)  # noqa

        dfl = IoPipelineMessages.Defer(
            fn,
            no_context,
            _ctx=ctx,
            _pinned=pin,
        )

        if pin:
            self._propagation.pin_musts(dfl)

        ctx.feed_out(dfl)

        return dfl

    def run_deferred(self, dfl: IoPipelineMessages.Defer) -> None:
        ctx = check.not_none(dfl._ctx)  # noqa
        check.is_(ctx._pipeline, self)  # noqa
        check.state(not ctx._invalidated)  # noqa

        self._step_in()
        try:
            if dfl._pinned:  # noqa
                self._propagation.unpin_musts(dfl)

            ctx._run_deferred(dfl)  # noqa

        finally:
            self._step_out()

    ##
    # output

    @ta.final
    class _Output:
        def __init__(self) -> None:
            self._q: ta.Final[collections.deque[ta.Any]] = collections.deque()

        def __repr__(self) -> str:
            return (
                f'{type(self).__qualname__}@{id(self):x}'
                f'<len={len(self._q)}>'
                '()'
            )

        def peek(self) -> ta.Optional[ta.Any]:
            if not self._q:
                return None

            return self._q[0]

        def poll(self) -> ta.Optional[ta.Any]:
            if not self._q:
                return None

            return self._q.popleft()

        def drain(self) -> ta.List[ta.Any]:
            out: ta.List[ta.Any] = []

            while self._q:
                out.append(self._q.popleft())

            return out

    @property
    def output(self) -> _Output:
        return self._output

    ##
    # handlers

    def _handler_update(self, ctx: IoPipelineHandlerContext, kind: IoPipelineHandlerUpdate) -> None:
        for svc in self._services._handles_handler_update:  # noqa
            svc.handler_update(ctx.ref, kind)  # noqa

    #

    def _terminal_inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:  # noqa
        if (tm := self._config.inbound_terminal) == 'drop':
            pass

        elif tm == 'raise':
            if not isinstance(msg, IoPipelineMessages.MayPropagate):
                raise MessageReachedTerminalIoPipelineError.new_single('inbound', msg)

        else:
            raise RuntimeError(f'unknown inbound terminal mode {tm}')

    def _terminal_outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:  # noqa
        if self._saw_final_output:
            # Includes a second FinalOutput: nothing may follow the first.
            raise SawFinalOutputIoPipelineError
        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            self._saw_final_output = True
        elif self._saw_shutdown_output:
            # Includes a second ShutdownOutput, which is not an AfterShutdownOutput.
            if not isinstance(msg, IoPipelineMessages.AfterShutdownOutput):
                raise SawShutdownOutputIoPipelineError
        elif isinstance(msg, IoPipelineMessages.ShutdownOutput):
            self._saw_shutdown_output = True

        self._output._q.append(msg)  # noqa

    #

    _outermost: ta.Final[IoPipelineHandlerContext]
    _innermost: ta.Final[IoPipelineHandlerContext]

    def _check_can_add(
            self,
            handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
            ignore_name_of: ta.Optional[IoPipelineHandlerContext] = None,
    ) -> IoPipelineHandler:
        check.state(self._state == IoPipeline.State.READY)  # noqa
        check.isinstance(handler, IoPipelineHandler)

        if not isinstance(handler, ShareableIoPipelineHandler):
            check.not_in(handler, self._unique_contexts)

        if name is not None and (ctx := self._contexts_by_name.get(name)) is not None:
            # A replace() may reuse the name of the handler it is about to remove.
            check.is_(ctx, check.not_none(ignore_name_of))

        return handler

    def _check_can_add_relative_to(self, ctx: IoPipelineHandlerContext) -> IoPipelineHandlerContext:
        check.is_(ctx._pipeline, self)  # noqa
        check.state(not ctx._invalidated)  # noqa

        return ctx

    def _add(
            self,
            handler: IoPipelineHandler,
            *,
            inner_to: ta.Optional[IoPipelineHandlerContext] = None,
            outer_to: ta.Optional[IoPipelineHandlerContext] = None,

            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        self._check_can_add(handler, name=name)

        if inner_to is not None:
            check.none(outer_to)
            check.is_not(inner_to, self._innermost)
            self._check_can_add_relative_to(inner_to)
        elif outer_to is not None:
            check.none(inner_to)
            check.is_not(outer_to, self._outermost)
            self._check_can_add_relative_to(outer_to)
        else:
            raise ValueError('Must specify exactly one of inner_to or outer_to')

        ctx = IoPipelineHandlerContext(
            _pipeline=self,
            _handler=handler,

            _name=name,
        )

        self._handler_update(ctx, 'adding')  # noqa

        if isinstance(handler, ShareableIoPipelineHandler):
            self._shareable_contexts.setdefault(handler, set()).add(ctx)
        else:
            check.not_in(handler, self._unique_contexts)  # also pre-checked by _check_can_add
            self._unique_contexts[handler] = ctx

        if name is not None:
            self._contexts_by_name[name] = ctx

        if inner_to is not None:
            prv = inner_to._next_in  # noqa
            ctx._next_out = inner_to  # noqa
            ctx._next_in = prv  # noqa
            inner_to._next_in = ctx  # noqa
            prv._next_out = ctx  # noqa

        if outer_to is not None:
            prv = outer_to._next_out  # noqa
            ctx._next_out = prv  # noqa
            ctx._next_in = outer_to  # noqa
            prv._next_in = ctx  # noqa
            outer_to._next_out = ctx  # noqa

        self._clear_caches()

        self._handler_update(ctx, 'added')  # noqa

        # FIXME: exceptions?
        self._notify(ctx, IoPipelineHandlerNotifications.Added(ctx))

        return ctx.ref  # noqa

    def add_innermost(
            self,
            handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        return self._add(handler, outer_to=self._innermost, name=name)

    def add_outermost(
            self,
            handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        return self._add(handler, inner_to=self._outermost, name=name)

    def add_inner_to(
            self,
            inner_to: IoPipelineHandlerRef,
            handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        ctx = inner_to._context  # noqa
        return self._add(handler, inner_to=ctx, name=name)

    def add_outer_to(
            self,
            outer_to: IoPipelineHandlerRef,
            handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        ctx = outer_to._context  # noqa
        return self._add(handler, outer_to=ctx, name=name)

    #

    def _check_can_remove(self, handler_ref: IoPipelineHandlerRef) -> IoPipelineHandler:
        ctx = handler_ref._context  # noqa
        check.is_(ctx._pipeline, self)  # noqa

        check.state(self._state in (IoPipeline.State.READY, IoPipeline.State.DESTROYING))  # noqa

        check.state(not ctx._invalidated)  # noqa

        handler = ctx._handler  # noqa
        if isinstance(handler, ShareableIoPipelineHandler):
            check.in_(ctx, self._shareable_contexts[handler])
        else:
            check.equal(ctx, self._unique_contexts[handler])

        check.is_not(ctx, self._innermost)
        check.is_not(ctx, self._outermost)

        return handler

    def _remove(self, handler_ref: IoPipelineHandlerRef) -> None:
        self._check_can_remove(handler_ref)

        ctx = handler_ref._context  # noqa
        handler = ctx._handler  # noqa

        self._handler_update(ctx, 'removing')  # noqa

        if ctx._name is not None:  # noqa
            del self._contexts_by_name[ctx._name]  # noqa

        if isinstance(handler, ShareableIoPipelineHandler):
            cs = self._shareable_contexts[handler]
            cs.remove(ctx)
            if not cs:
                del self._shareable_contexts[handler]
        else:
            del self._unique_contexts[handler]

        ctx._next_in._next_out = ctx._next_out  # noqa
        ctx._next_out._next_in = ctx._next_in  # noqa

        ctx._invalidated = True  # noqa
        del ctx._next_in  # noqa
        del ctx._next_out  # noqa

        self._clear_caches()

        self._handler_update(ctx, 'removed')  # noqa

        # FIXME: exceptions? defer?
        self._notify(ctx, IoPipelineHandlerNotifications.Removed(ctx))

    def remove(self, handler_ref: IoPipelineHandlerRef) -> None:
        self._remove(handler_ref)

    #

    def replace(
            self,
            old_handler_ref: IoPipelineHandlerRef,
            new_handler: IoPipelineHandler,
            *,
            name: ta.Optional[str] = None,
    ) -> IoPipelineHandlerRef:
        self._check_can_remove(old_handler_ref)
        self._check_can_add(new_handler, name=name, ignore_name_of=old_handler_ref._context)  # noqa

        inner_to = old_handler_ref._context._next_out  # noqa
        self._remove(old_handler_ref)
        return self._add(new_handler, inner_to=inner_to, name=name)

    #

    @ta.final
    class _Outermost(IoPipelineHandler):
        """'Head' in Netty terms."""

        def __repr__(self) -> str:
            return f'{type(self).__name__}'

        def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
            if isinstance(msg, IoPipelineMessages.MustPropagate):
                ctx._pipeline._propagation.remove_must(ctx, 'outbound', msg)  # noqa

            ctx._pipeline._terminal_outbound(ctx, msg)  # noqa

    @ta.final
    class _Innermost(IoPipelineHandler):
        """'Tail' in Netty terms."""

        def __repr__(self) -> str:
            return f'{type(self).__name__}'

        def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
            if isinstance(msg, IoPipelineMessages.MustPropagate):
                ctx._pipeline._propagation.remove_must(ctx, 'inbound', msg)  # noqa

            ctx._pipeline._terminal_inbound(ctx, msg)  # noqa

    ##
    # caches

    @ta.final
    class _Caches:
        def __init__(self, p: 'IoPipeline') -> None:
            self.__p_ref = weakref.ref(p)

            self._handlers_by_type_cache: ta.Dict[type, ta.Sequence[IoPipelineHandlerContext]] = {}
            self._single_handlers_by_type_cache: ta.Dict[type, ta.Optional[IoPipelineHandlerContext]] = {}

        @property
        def _p(self) -> 'IoPipeline':
            return check.not_none(self.__p_ref())

        _handler_contexts: ta.Sequence[IoPipelineHandlerContext]

        def handlers(self) -> ta.Sequence[IoPipelineHandlerRef_]:
            try:
                contexts = self._handler_contexts
            except AttributeError:
                contexts = []
                ctx = self._p._outermost  # noqa
                while (ctx := ctx._next_in) is not self._p._innermost:  # noqa
                    contexts.append(ctx)
                self._handler_contexts = contexts

            return [ctx.ref for ctx in contexts]  # noqa

        _handler_contexts_by_name: ta.Mapping[str, IoPipelineHandlerContext]

        def handlers_by_name(self) -> ta.Mapping[str, IoPipelineHandlerRef_]:
            try:
                contexts_by_name = self._handler_contexts_by_name
            except AttributeError:
                contexts_by_name = {}
                ctx = self._p._outermost  # noqa
                while (ctx := ctx._next_in) is not self._p._innermost:  # noqa
                    if (n := ctx._name) is not None:  # noqa
                        contexts_by_name[n] = ctx
                self._handler_contexts_by_name = contexts_by_name

            return {name: ctx.ref for name, ctx in contexts_by_name.items()}  # noqa

        def find_handlers_of_type(self, ty: ta.Type[T]) -> ta.Sequence[IoPipelineHandlerRef[T]]:
            try:
                contexts = self._handlers_by_type_cache[ty]
            except KeyError:
                contexts = []
                ctx = self._p._outermost  # noqa
                while (ctx := ctx._next_in) is not self._p._innermost:  # noqa
                    if isinstance(ctx._handler, ty):  # noqa
                        contexts.append(ctx)
                self._handlers_by_type_cache[ty] = contexts

            return [ctx.ref for ctx in contexts]  # type: ignore[misc]  # noqa

        def find_single_handler_of_type(self, ty: ta.Type[T]) -> ta.Optional[IoPipelineHandlerRef[T]]:
            try:
                ctx = self._single_handlers_by_type_cache[ty]
            except KeyError:
                refs = self.find_handlers_of_type(ty)
                ref = check.opt_single(refs)
                self._single_handlers_by_type_cache[ty] = None if ref is None else ref._context  # noqa
                return ref

            return None if ctx is None else ctx.ref  # type: ignore[return-value]  # noqa

    __caches: _Caches

    def _caches(self) -> _Caches:
        try:
            return self.__caches
        except AttributeError:
            pass
        self.__caches = caches = IoPipeline._Caches(self)
        return caches

    def _clear_caches(self) -> None:
        try:
            del self.__caches
        except AttributeError:
            pass

    def handlers(self) -> ta.Sequence[IoPipelineHandlerRef]:
        return self._caches().handlers()

    def handlers_by_name(self) -> ta.Mapping[str, IoPipelineHandlerRef_]:
        return self._caches().handlers_by_name()

    @dc.dataclass(frozen=True)
    class _HandlerType(ta.Generic[T]):
        """This is entirely just a workaround for mypy's `type-abstract` deficiency."""

        ty: ta.Type[T]

    def find_handlers_of_type(
            self,
            ty: ta.Union[_HandlerType[T], ta.Type[T]],
    ) -> ta.Sequence[IoPipelineHandlerRef[T]]:
        if isinstance(ty, IoPipeline._HandlerType):
            ty = ty.ty
        return self._caches().find_handlers_of_type(ty)

    def find_single_handler_of_type(
            self,
            ty: ta.Union[_HandlerType[T], ta.Type[T]],
    ) -> ta.Optional[IoPipelineHandlerRef[T]]:
        if isinstance(ty, IoPipeline._HandlerType):
            ty = ty.ty
        return self._caches().find_single_handler_of_type(ty)

    #

    @ta.overload
    def find_handler(  # type: ignore[overload-overlap]
            self,
            handler: ShareableIoPipelineHandlerT,
    ) -> ta.Sequence[IoPipelineHandlerRef[ShareableIoPipelineHandlerT]]:
        ...

    @ta.overload
    def find_handler(
            self,
            handler: IoPipelineHandlerT,
    ) -> ta.Optional[IoPipelineHandlerRef[IoPipelineHandlerT]]:
        ...

    def find_handler(self, handler):
        if isinstance(handler, ShareableIoPipelineHandler):
            out: ta.List[ta.Any] = []
            ctx = self._outermost
            while (ctx := ctx._next_in) is not self._innermost:  # noqa
                if handler == ctx._handler:  # noqa
                    out.append(ctx.ref)  # noqa
            return out

        else:
            # Relies on existing uniqueness checks
            ctx = self._outermost
            while (ctx := ctx._next_in) is not self._innermost:  # noqa
                if handler == ctx._handler:  # noqa
                    return ctx.ref  # noqa
            return None

    ##
    # destroy

    def __enter__(self) -> 'IoPipeline':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.destroy()

    def destroy(self) -> None:
        """
        Immediately tear down the pipeline without graceful output draining.

        Destruction does not synthesize FinalInput or FinalOutput. Callers that require graceful closure must drive a
        FinalOutput to the pipeline terminal before destroying it.
        """

        if self._state in (IoPipeline.State.DESTROYED, IoPipeline.State.DESTROYING):
            # Destroying removes every handler; one whose Removed callback asks for destruction is answered by the
            # destruction in progress.
            return

        check.state(self._state == IoPipeline.State.READY)
        self._set_state(IoPipeline.State.DESTROYING)

        first_exc: ta.Optional[BaseException] = None
        try:
            self._step_in()
            try:
                im_ctx = self._innermost  # noqa
                om_ctx = self._outermost  # noqa
                while (ctx := im_ctx._next_out) is not om_ctx:  # noqa
                    try:
                        self.remove(ctx.ref)  # noqa
                    except BaseException as e:  # noqa
                        # One handler's Removed callback failing must neither strand the remaining handlers nor hide
                        # behind DESTROYED: the first failure is raised once everything has been torn down.
                        if first_exc is None:
                            first_exc = e
                        if im_ctx._next_out is ctx:  # noqa
                            # The removal failed before unlinking the handler: no progress is possible.
                            raise

            finally:
                self._step_out()

            for svc in self._services._handles_pipeline_update:  # noqa
                svc.pipeline_update(self, 'removed')

        finally:
            try:
                self._fail_pending_completables(AbortedIoPipelineError('Pipeline destroyed before completion'))
            finally:
                # Output nothing consumed can no longer be used by anyone; completables among it were just failed.
                self._output._q.clear()  # noqa
                self._set_state(IoPipeline.State.DESTROYED)

        if first_exc is not None:
            raise first_exc

    def _fail_pending_completables(self, exc: BaseException) -> None:
        first_listener_exc: ta.Optional[BaseException] = None

        for completable in tuple(self._pending_completables.values()):
            if completable.is_done():
                continue
            try:
                completable.set_failed(exc)
            except BaseException as listener_exc:  # noqa
                if first_listener_exc is None:
                    first_listener_exc = listener_exc

        check.empty(self._pending_completables)
        if first_listener_exc is not None:
            raise first_listener_exc


########################################
# ../../../../omcore/io/streambufs/types.py


##


class ByteStreamBufferLike(Abstract):
    @ta.final
    def __bool__(self) -> bool:
        raise TypeError('Do not use bool() for ByteStreamBufferLike, use len().')

    @abc.abstractmethod
    def __len__(self) -> int:
        """
        Return the number of readable bytes.

        This is expected to be O(1). Many drivers and codecs use `len(buf)` in tight loops to decide whether more data
        is needed before attempting to parse a frame.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def peek(self) -> memoryview:
        """
        Return a contiguous, read-only `memoryview` of the first available bytes.

        This is the "next chunk" fast-path: for segmented views, the returned memoryview may represent only the first
        segment (and thus may be shorter than `len(self)`), but it must be non-copying. This is the fast-path for codecs
        that can parse headers from an initial contiguous region.

        The returned view should be treated as ephemeral: callers must assume it may be invalidated by subsequent buffer
        mutations (advance/write/reserve/commit), depending on the implementation.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def segments(self) -> ta.Sequence[memoryview]:
        """
        Return the readable contents as an ordered sequence of non-copying `memoryview` segments.

        This method is required because efficient operations in pure Python typically depend on delegating work to
        CPython's optimized implementations for searching/slicing within contiguous regions. By exposing
        already-contiguous segments, the buffer enables implementations of `find/rfind` and higher-level framing to
        avoid Python-level per-byte iteration.

        The returned segments must:
          - collectively represent exactly the readable bytes, in order
          - be 1-D, byte-oriented views (itemsize 1)
          - be non-copying views of the underlying storage
          - be non-empty - lack of data is represented by returning no segments, not empty segments

        Callers must assume that the returned views may be invalidated by subsequent mutations of the originating
        buffer/view (e.g., advancing, writing, reserving, committing), depending on the implementation's rules.
        """

        raise NotImplementedError


class ByteStreamBufferView(ByteStreamBufferLike, Abstract):
    """
    A read-only, possibly non-contiguous view of bytes.

    This is the result type of operations like `ByteStreamBuffer.split_to()`: it represents a *logical* byte sequence
    without requiring a copy. A `ByteStreamBufferView` is intentionally minimal: it is not a general-purpose container
    API, not a random-access sequence, and not intended for arbitrary indexing/slicing-heavy use.

    `ByteStreamBufferView` exists to make copy boundaries explicit:
      - Use `segments()` / `peek()` to access data without copying.
      - Use `tobytes()` (or `bytes(view)`) to intentionally materialize a contiguous `bytes` object.

    Implementations may be backed by one or many `memoryview` segments; the semantics are defined as if all readable
    bytes were concatenated in order.
    """

    def __bytes__(self) -> bytes:
        b = self.tobytes()
        if type(b) is bytes:
            return b
        return bytes(b)

    @abc.abstractmethod
    def tobytes(self) -> Bytes:
        """
        Materialize this view as a contiguous `bytes` object (copying).

        This is the explicit copy boundary: callers should prefer `peek()` / `segments()` for zero-copy-ish access when
        feasible, and use `tobytes()` only when a contiguous owned `bytes` is required.
        """

        raise NotImplementedError


class ByteStreamBuffer(ByteStreamBufferLike, Abstract):
    """
    An incremental, consumption-oriented byte accumulator intended for protocol parsing.

    A `ByteStreamBuffer` is a *stream buffer*: bytes are appended by a driver/transport and then consumed by codecs via
    peeking, searching, splitting, and advancing-without forcing repeated concatenation or reallocation. It is
    explicitly designed to support segmented storage (to avoid "a huge buffer pinned by a tiny tail") and to enable
    low-copy pipeline-style decoding (Netty/Tokio-inspired).

    What it is for:
      - buffering raw bytes between I/O and protocol codecs,
      - framing (delimiters/length-prefixed) using split/advance,
      - efficient searching over buffered bytes using C-accelerated primitives via `memoryview` segments.

    What it is *not* for:
      - a general-purpose replacement for `bytes`/`bytearray`,
      - a `collections.abc.Sequence` or random-access container abstraction,
      - arbitrary indexing/slicing-heavy workloads (use `bytes`/`bytearray`/`memoryview` directly).

    `ByteStreamBuffer` deliberately exposes `memoryview` at its boundary. This is foundational: it allows both immutable
    (`bytes`) and mutable (`bytearray`) internal storage to be viewed in O(1) without copying. It also avoids relying
    on `io.BytesIO` as a core backing store: while `BytesIO.getbuffer()` can expose a view, exported views pin the
    underlying buffer against resizing, which makes it awkward as a general-purpose buffer substrate.

    Semantics note:
      Many methods describe behavior in terms of the *conceptual concatenation* of readable bytes, even if the buffer
      is physically segmented. This is what "stream-correct" means here: results must be correct regardless of how the
      buffered bytes are chunked internally.
    """

    @abc.abstractmethod
    def advance(self, n: int, /) -> None:
        """
        Consume (discard) exactly `n` readable bytes from the front of the buffer.

        This operation must not copy remaining bytes unnecessarily. For segmented buffers, this typically adjusts a head
        offset and drops exhausted segments.

        Implementations must raise if `n` is negative or greater than `len(self)`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def split_to(self, n: int, /) -> ByteStreamBufferView:
        """
        Split off and return a read-only view of the first `n` readable bytes, consuming them from this buffer.

        This is the core "low-copy framing" primitive:
          - codecs can `split_to(frame_len)` to obtain a view of an entire frame without copying,
          - then immediately continue parsing subsequent frames from the remaining bytes.

        Implementations should strive for O(1) or amortized O(1) behavior, returning a view that references underlying
        segments rather than materializing a new contiguous `bytes`.

        Implementations must raise if `n` is negative or greater than `len(self)`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def coalesce(self, n: int, /) -> memoryview:
        """
        Ensure the first `n` readable bytes are available contiguously and return a view of them.

        Semantics:
          - Non-consuming: does not advance.
          - May restructure internal segments (content-preserving) to make the prefix contiguous.
          - Returns a read-only-ish `memoryview` (callers must not mutate readable bytes).

        Copying behavior:
          - If `peek()` already exposes >= n contiguous bytes, this is zero-copy.
          - Otherwise, it copies exactly the first `n` bytes into a new contiguous segment and rewrites the internal
            segment list so that segment[0] contains that prefix.

        Reserve interaction:
          - Disallowed while an outstanding reservation exists, since reserve() hands out a view that must not be
            invalidated by internal reshaping.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def find(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        """
        Find the first occurrence of `sub` within the readable bytes and return its offset, or -1 if not found.

        This operation is "stream-correct": it must behave as if searching within the conceptual concatenation of all
        readable bytes, even if the buffer is physically segmented. In particular, matches that span segment boundaries
        must be detected.

        `start` and `end` are offsets into the readable region, matching the semantics of `bytes.find()`:
          - `start` defaults to 0 (the beginning of readable bytes),
          - `end` defaults to `len(self)`.

        Rationale for being part of the core interface:
          In pure Python, higher-level codecs cannot efficiently implement correct cross-segment searching byte-by-byte.
          Keeping `find` near the owning storage allows implementations to exploit contiguous segments and CPython's
          optimized search within each segment while still providing correct stream semantics.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def rfind(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        """
        Find the last occurrence of `sub` within the readable bytes and return its offset, or -1 if not found.

        This operation is also stream-correct and matches `bytes.rfind()` semantics for `start`/`end`, interpreted as
        offsets into the readable region of this buffer.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def find_all_in_prefix(self, sub: bytes, start: int = 0) -> ta.Sequence[int]:
        """
        Return the offsets of all non-overlapping occurrences of `sub` lying entirely within the *contiguous readable
        prefix* (the region exposed by `peek()`), scanning left to right from `start` and stepping past each match.

        This is the bulk-scanning primitive: implementations run the whole scan as a tight loop over their underlying
        storage using C-accelerated search, amortizing per-call overhead across many hits - the per-call cost of
        `find()` dominates codecs decoding many small frames otherwise. It is intentionally *not* stream-correct:
        occurrences extending beyond the contiguous prefix are not found. Callers batch over the prefix and fall back to
        `find()` to resolve possible cross-segment matches.

        `sub` must be non-empty. `start` must be non-negative, and is an offset into the readable region as with
        `find()`. Returned offsets are likewise readable-region offsets, in ascending order.
        """

        raise NotImplementedError


class MutableByteStreamBuffer(ByteStreamBuffer, Abstract):
    """
    A writable `ByteStreamBuffer`: supports appending bytes and (optionally) reserving writable space.

    `MutableByteStreamBuffer` is the primary target for drivers/transports feeding data into protocol pipelines, and for
    encoders building outbound byte sequences. It intentionally does not imply any particular I/O model (blocking,
    asyncio, custom reactors); it is simply the mutable byte substrate.

    Implementations may be linear (single `bytearray` + indices), segmented (multiple chunks), or adaptive.
    """

    @property
    @abc.abstractmethod
    def max_size(self) -> ta.Optional[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: BytesLike, /) -> None:
        """
        Append `data` to the end of the readable region (after any existing unread bytes).

        Implementations should avoid needless copying; e.g., segmented buffers may store large `bytes` chunks directly,
        while linear buffers may copy into a `bytearray`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def reserve(self, n: int, /) -> memoryview:
        """
        Reserve writable space for at least `n` bytes and return a writable `memoryview` into that space.

        This method exists to support "close to the metal" drivers that can fill buffers directly (e.g., `recv_into`,
        `readinto`) without allocating temporary `bytes` objects.

        The returned view represents capacity that is not yet part of the readable region. The caller must write into
        some prefix of the view and then call `commit(written)` to make those bytes readable.

        Implementations should document their rules regarding outstanding reservations; a simple and robust rule is:
          - only one active reservation may exist at a time,
          - mutations that would reallocate storage are forbidden while a reservation is outstanding.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def commit(self, n: int, /) -> None:
        """
        Commit `n` bytes from the most recent reservation, making them readable.

        Conceptually, `reserve()` may provide more capacity than the caller actually uses; `commit(n)` "shrinks" that
        over-reservation by only publishing the first `n` bytes as readable.

        Implementations must validate:
          - that a reservation is outstanding,
          - that `0 <= n <= reserved_length`.

        After commit, the reservation is considered consumed; subsequent reads and searches must include the committed
        bytes as part of the readable region.
        """

        raise NotImplementedError


########################################
# ../../../../omcore/lite/marshal.py
"""
TODO:
 - pickle stdlib objs? have to pin to 3.8 pickle protocol, will be cross-version
 - Options.sequence_cls = list, mapping_cls = dict, ... - def with_mutable_containers() -> Options
"""


##


@dc.dataclass(frozen=True)
class ObjMarshalOptions:
    raw_bytes: bool = False
    non_strict_fields: bool = False


class ObjMarshaler(Abstract):
    @abc.abstractmethod
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        raise NotImplementedError


class NopObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o


class ProxyObjMarshaler(ObjMarshaler):
    def __init__(self, m: ta.Optional[ObjMarshaler] = None) -> None:
        super().__init__()

        self._m = m

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.not_none(self._m).marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.not_none(self._m).unmarshal(o, ctx)


class CastObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(o)


class DynamicObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return ctx.manager.marshal_obj(o, opts=ctx.options)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o


class Base64ObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return base64.b64encode(o).decode('ascii')

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(base64.b64decode(o))


class BytesSwitchedObjMarshaler(ObjMarshaler):
    def __init__(self, m: ObjMarshaler) -> None:
        super().__init__()

        self._m = m

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if ctx.options.raw_bytes:
            return o
        return self._m.marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if ctx.options.raw_bytes:
            return o
        return self._m.unmarshal(o, ctx)


class EnumObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o.name

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty.__members__[o]  # type: ignore


class OptionalObjMarshaler(ObjMarshaler):
    def __init__(self, item: ObjMarshaler) -> None:
        super().__init__()

        self._item = item

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if o is None:
            return None
        return self._item.marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if o is None:
            return None
        return self._item.unmarshal(o, ctx)


class PrimitiveUnionObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            pt: ta.Tuple[type, ...],
            x: ta.Optional[ObjMarshaler] = None,
    ) -> None:
        super().__init__()

        self._pt = pt
        self._x = x

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if isinstance(o, self._pt):
            return o
        elif self._x is not None:
            return self._x.marshal(o, ctx)
        else:
            raise TypeError(o)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if self._x is not None:
            # The non-primitive member must be tried first - its marshaled form may itself be one of the union's
            # primitive types (e.g. Union[str, Decimal] wires Decimal as a str), which primitive-first dispatch would
            # shadow entirely. Such wire values are inherently ambiguous - the non-primitive parse is accepted only
            # when it faithfully round-trips back to the wire value, so lenient member unmarshalers (e.g. a Sequence
            # member iterating a str) don't capture values belonging to a primitive member.
            try:
                v = self._x.unmarshal(o, ctx)
            except Exception:  # noqa
                pass
            else:
                if not isinstance(o, self._pt):
                    return v
                try:
                    if self._x.marshal(v, ctx) == o:
                        return v
                except Exception:  # noqa
                    pass
        if isinstance(o, self._pt):
            return o
        raise TypeError(o)


class LiteralObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            item: ObjMarshaler,
            vs: frozenset,
    ) -> None:
        super().__init__()

        self._item = item
        self._vs = vs

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._item.marshal(check.in_(o, self._vs), ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.in_(self._item.unmarshal(o, ctx), self._vs)


class MappingObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            km: ObjMarshaler,
            vm: ObjMarshaler,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._km = km
        self._vm = vm

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return {self._km.marshal(k, ctx): self._vm.marshal(v, ctx) for k, v in o.items()}

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty((self._km.unmarshal(k, ctx), self._vm.unmarshal(v, ctx)) for k, v in o.items())


class IterableObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            item: ObjMarshaler,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._item = item

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return [self._item.marshal(e, ctx) for e in o]

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(self._item.unmarshal(e, ctx) for e in o)


class FieldsObjMarshaler(ObjMarshaler):
    @dc.dataclass(frozen=True)
    class Field:
        att: str
        key: str
        m: ObjMarshaler

        omit_if_none: bool = False

    def __init__(
            self,
            ty: type,
            fs: ta.Sequence[Field],
            *,
            non_strict: bool = False,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._fs = fs
        self._non_strict = non_strict

        fs_by_att: dict = {}
        fs_by_key: dict = {}
        for f in self._fs:
            check.not_in(check.non_empty_str(f.att), fs_by_att)
            check.not_in(check.non_empty_str(f.key), fs_by_key)
            fs_by_att[f.att] = f
            fs_by_key[f.key] = f

        self._fs_by_att: ta.Mapping[str, FieldsObjMarshaler.Field] = fs_by_att
        self._fs_by_key: ta.Mapping[str, FieldsObjMarshaler.Field] = fs_by_key

    @property
    def ty(self) -> type:
        return self._ty

    @property
    def fs(self) -> ta.Sequence[Field]:
        return self._fs

    #

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        d = {}
        for f in self._fs:
            mv = f.m.marshal(getattr(o, f.att), ctx)
            if mv is None and f.omit_if_none:
                continue
            d[f.key] = mv
        return d

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        kw = {}
        for k, v in o.items():
            if (f := self._fs_by_key.get(k)) is None:
                if not (self._non_strict or ctx.options.non_strict_fields):
                    raise KeyError(k)
                continue
            kw[f.att] = f.m.unmarshal(v, ctx)
        return self._ty(**kw)


class SingleFieldObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            fld: str,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._fld = fld

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return getattr(o, self._fld)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(**{self._fld: o})


class PolymorphicObjMarshaler(ObjMarshaler):
    class Impl(ta.NamedTuple):
        ty: type
        tag: str
        m: ObjMarshaler

    def __init__(
            self,
            impls_by_ty: ta.Mapping[type, Impl],
            impls_by_tag: ta.Mapping[str, Impl],
    ) -> None:
        super().__init__()

        self._impls_by_ty = impls_by_ty
        self._impls_by_tag = impls_by_tag

    @classmethod
    def of(cls, impls: ta.Iterable[Impl]) -> 'PolymorphicObjMarshaler':
        return cls(
            {i.ty: i for i in impls},
            {i.tag: i for i in impls},
        )

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        impl = self._impls_by_ty[type(o)]
        return {impl.tag: impl.m.marshal(o, ctx)}

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        [(t, v)] = o.items()
        impl = self._impls_by_tag[t]
        return impl.m.unmarshal(v, ctx)


class DatetimeObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
    ) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o.isoformat()

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty.fromisoformat(o)  # type: ignore


class DecimalObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return str(check.isinstance(o, decimal.Decimal))

    def unmarshal(self, v: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return decimal.Decimal(check.isinstance(v, str))


class FractionObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        fr = check.isinstance(o, fractions.Fraction)
        return [fr.numerator, fr.denominator]

    def unmarshal(self, v: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        num, denom = check.isinstance(v, list)
        return fractions.Fraction(num, denom)


class UuidObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return str(o)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return uuid.UUID(o)


##


_DEFAULT_OBJ_MARSHALERS: ta.Dict[ta.Any, ObjMarshaler] = {
    **{t: NopObjMarshaler() for t in (type(None),)},
    **{t: CastObjMarshaler(t) for t in (int, float, str, bool)},
    **{t: BytesSwitchedObjMarshaler(Base64ObjMarshaler(t)) for t in (bytes, bytearray)},
    **{t: IterableObjMarshaler(t, DynamicObjMarshaler()) for t in (list, tuple, set, frozenset)},
    **{t: MappingObjMarshaler(t, DynamicObjMarshaler(), DynamicObjMarshaler()) for t in (dict,)},

    **{t: DynamicObjMarshaler() for t in (ta.Any, object)},

    **{t: DatetimeObjMarshaler(t) for t in (datetime.date, datetime.time, datetime.datetime)},
    decimal.Decimal: DecimalObjMarshaler(),
    fractions.Fraction: FractionObjMarshaler(),
    uuid.UUID: UuidObjMarshaler(),
}

_OBJ_MARSHALER_GENERIC_MAPPING_TYPES: ta.Dict[ta.Any, type] = {
    **{t: t for t in (dict,)},
    **{t: dict for t in (collections.abc.Mapping, collections.abc.MutableMapping)},  # noqa
}

_OBJ_MARSHALER_GENERIC_ITERABLE_TYPES: ta.Dict[ta.Any, type] = {
    **{t: t for t in (list, tuple, set, frozenset)},
    collections.abc.Set: frozenset,
    collections.abc.MutableSet: set,
    collections.abc.Sequence: tuple,
    collections.abc.MutableSequence: list,
}

_OBJ_MARSHALER_PRIMITIVE_TYPES: ta.Set[type] = {
    int,
    float,
    bool,
    str,
}


##


_REGISTERED_OBJ_MARSHALERS_BY_TYPE: ta.MutableMapping[type, ObjMarshaler] = weakref.WeakKeyDictionary()


def register_type_obj_marshaler(ty: type, om: ObjMarshaler) -> None:
    _REGISTERED_OBJ_MARSHALERS_BY_TYPE[ty] = om


def register_single_field_type_obj_marshaler(fld, ty=None):
    def inner(ty):  # noqa
        register_type_obj_marshaler(ty, SingleFieldObjMarshaler(ty, fld))
        return ty

    if ty is not None:
        return inner(ty)
    else:
        return inner


##


class ObjMarshalerFieldMetadata:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError


class OBJ_MARSHALER_FIELD_KEY(ObjMarshalerFieldMetadata):  # noqa
    pass


class OBJ_MARSHALER_OMIT_IF_NONE(ObjMarshalerFieldMetadata):  # noqa
    pass


##


class ObjMarshalerManager(Abstract):
    @abc.abstractmethod
    def make_obj_marshaler(
            self,
            ty: ta.Any,
            rec: ta.Callable[[ta.Any], ObjMarshaler],
            *,
            non_strict_fields: bool = False,
    ) -> ObjMarshaler:
        raise NotImplementedError

    @abc.abstractmethod
    def set_obj_marshaler(
            self,
            ty: ta.Any,
            m: ObjMarshaler,
            *,
            override: bool = False,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_obj_marshaler(
            self,
            ty: ta.Any,
            *,
            no_cache: bool = False,
            **kwargs: ta.Any,
    ) -> ObjMarshaler:
        raise NotImplementedError

    @abc.abstractmethod
    def make_context(self, opts: ta.Optional[ObjMarshalOptions]) -> 'ObjMarshalContext':
        raise NotImplementedError

    #

    def marshal_obj(
            self,
            o: ta.Any,
            ty: ta.Any = None,
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> ta.Any:
        m = self.get_obj_marshaler(ty if ty is not None else type(o))
        return m.marshal(o, self.make_context(opts))

    def unmarshal_obj(
            self,
            o: ta.Any,
            ty: ta.Union[ta.Type[T], ta.Any],
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> T:
        m = self.get_obj_marshaler(ty)
        return m.unmarshal(o, self.make_context(opts))

    def roundtrip_obj(
            self,
            o: ta.Any,
            ty: ta.Any = None,
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> ta.Any:
        if ty is None:
            ty = type(o)
        m: ta.Any = self.marshal_obj(o, ty, opts)
        u: ta.Any = self.unmarshal_obj(m, ty, opts)
        return u


#


class ObjMarshalerManagerImpl(ObjMarshalerManager):
    def __init__(
            self,
            *,
            default_options: ObjMarshalOptions = ObjMarshalOptions(),

            default_obj_marshalers: ta.Dict[ta.Any, ObjMarshaler] = _DEFAULT_OBJ_MARSHALERS,  # noqa
            generic_mapping_types: ta.Dict[ta.Any, type] = _OBJ_MARSHALER_GENERIC_MAPPING_TYPES,  # noqa
            generic_iterable_types: ta.Dict[ta.Any, type] = _OBJ_MARSHALER_GENERIC_ITERABLE_TYPES,  # noqa

            registered_obj_marshalers: ta.Mapping[type, ObjMarshaler] = _REGISTERED_OBJ_MARSHALERS_BY_TYPE,
    ) -> None:
        super().__init__()

        self._default_options = default_options

        self._obj_marshalers = dict(default_obj_marshalers)
        self._generic_mapping_types = generic_mapping_types
        self._generic_iterable_types = generic_iterable_types
        self._registered_obj_marshalers = registered_obj_marshalers

        self._lock = threading.RLock()
        self._derived_obj_marshalers: ta.Dict[ta.Any, ObjMarshaler] = {}
        self._proxies: ta.Dict[ta.Any, ProxyObjMarshaler] = {}

    #

    @classmethod
    def _is_abstract(cls, ty: type) -> bool:
        return abc.ABC in ty.__bases__ or Abstract in ty.__bases__

    @classmethod
    def _get_field_type_hints(cls, ty: type) -> ta.Optional[ta.Mapping[str, ta.Any]]:
        """
        Best-effort resolution of string / forward-ref field annotations (`from __future__ import annotations` modules,
        self-referential fields) against their defining modules' namespaces, mro-aware. Returns None on failure (e.g.
        TYPE_CHECKING-only names, classes exec'd into namespaces absent from sys.modules) - callers fall back to the
        raw annotations, preserving behavior for already-evaluated ones.
        """

        try:
            return ta.get_type_hints(ty)
        except Exception:  # noqa
            return None

    #

    def make_obj_marshaler(
            self,
            ty: ta.Any,
            rec: ta.Callable[[ta.Any], ObjMarshaler],
            *,
            non_strict_fields: bool = False,
    ) -> ObjMarshaler:
        if isinstance(ty, type):
            if (reg := self._registered_obj_marshalers.get(ty)) is not None:
                return reg

            if self._is_abstract(ty):
                tn = ty.__name__
                impls: ta.List[ta.Tuple[type, str]] = [  # type: ignore[var-annotated]
                    (ity, ity.__name__)
                    for ity in deep_subclasses(ty)
                    if not self._is_abstract(ity)
                ]

                if all(itn.endswith(tn) for _, itn in impls):
                    impls = [
                        (ity, snake_case(itn[:-len(tn)]))
                        for ity, itn in impls
                    ]

                dupe_tns = sorted(
                    dn
                    for dn, dc in collections.Counter(itn for _, itn in impls).items()
                    if dc > 1
                )
                if dupe_tns:
                    raise KeyError(f'Duplicate impl names for {ty}: {dupe_tns}')

                return PolymorphicObjMarshaler.of([
                    PolymorphicObjMarshaler.Impl(
                        ity,
                        itn,
                        rec(ity),
                    )
                    for ity, itn in impls
                ])

            if issubclass(ty, enum.Enum):
                return EnumObjMarshaler(ty)

            if dc.is_dataclass(ty):
                hints = self._get_field_type_hints(ty) or {}
                return FieldsObjMarshaler(
                    ty,
                    [
                        FieldsObjMarshaler.Field(
                            att=f.name,
                            key=check.non_empty_str(fk),
                            m=rec(hints.get(f.name, f.type)),
                            omit_if_none=check.isinstance(f.metadata.get(OBJ_MARSHALER_OMIT_IF_NONE, False), bool),
                        )
                        for f in dc.fields(ty)
                        # init=False fields are excluded from both directions - unmarshal passes every key as a ctor
                        # kwarg, so marshaling them would produce round-trip-asymmetric output.
                        if f.init
                        if (fk := f.metadata.get(OBJ_MARSHALER_FIELD_KEY, f.name)) is not None
                    ],
                    non_strict=non_strict_fields,
                )

            if issubclass(ty, tuple) and hasattr(ty, '_fields'):
                hints = self._get_field_type_hints(ty) or {}
                return FieldsObjMarshaler(
                    ty,
                    [
                        FieldsObjMarshaler.Field(
                            att=p.name,
                            key=p.name,
                            # Untyped collections.namedtuple fields have empty annotations - marshal them dynamically.
                            m=rec(hints.get(
                                p.name,
                                p.annotation if p.annotation is not inspect.Parameter.empty else ta.Any,
                            )),
                        )
                        for p in inspect.signature(ty).parameters.values()
                    ],
                    non_strict=non_strict_fields,
                )

        if is_new_type(ty):
            return rec(get_new_type_supertype(ty))

        if is_literal_type(ty):
            lvs = frozenset(get_literal_type_args(ty))
            if None in lvs:
                is_opt = True
                lvs -= frozenset([None])
            else:
                is_opt = False
            lty = check.single(set(map(type, lvs)))
            lm: ObjMarshaler = LiteralObjMarshaler(rec(lty), lvs)
            if is_opt:
                lm = OptionalObjMarshaler(lm)
            return lm

        if is_generic_alias(ty):
            try:
                mt = self._generic_mapping_types[ta.get_origin(ty)]
            except KeyError:
                pass
            else:
                k, v = ta.get_args(ty)
                return MappingObjMarshaler(mt, rec(k), rec(v))

            try:
                st = self._generic_iterable_types[ta.get_origin(ty)]
            except KeyError:
                pass
            else:
                [e] = ta.get_args(ty)
                return IterableObjMarshaler(st, rec(e))

        if is_union_alias(ty):
            uts = frozenset(ta.get_args(ty))
            if None in uts or type(None) in uts:
                is_opt = True
                uts = frozenset(ut for ut in uts if ut not in (None, type(None)))
            else:
                is_opt = False

            um: ObjMarshaler
            if not uts:
                raise TypeError(ty)
            elif len(uts) == 1:
                um = rec(check.single(uts))
            else:
                pt = tuple({ut for ut in uts if ut in _OBJ_MARSHALER_PRIMITIVE_TYPES})
                np_uts = {ut for ut in uts if ut not in _OBJ_MARSHALER_PRIMITIVE_TYPES}
                if not np_uts:
                    um = PrimitiveUnionObjMarshaler(pt)
                elif len(np_uts) == 1:
                    um = PrimitiveUnionObjMarshaler(pt, x=rec(check.single(np_uts)))
                else:
                    raise TypeError(ty)

            if is_opt:
                um = OptionalObjMarshaler(um)
            return um

        raise TypeError(ty)

    #

    def set_obj_marshaler(
            self,
            ty: ta.Any,
            m: ObjMarshaler,
            *,
            override: bool = False,
    ) -> None:
        with self._lock:
            if not override and ty in self._obj_marshalers:
                raise KeyError(ty)
            self._obj_marshalers[ty] = m

    def get_obj_marshaler(
            self,
            ty: ta.Any,
            *,
            no_cache: bool = False,
            **kwargs: ta.Any,
    ) -> ObjMarshaler:
        with self._lock:
            ck = (ty, tuple(sorted(kwargs.items())))
            if not no_cache:
                # Explicitly set marshalers (and the defaults) are authoritative regardless of construction kwargs.
                try:
                    return self._obj_marshalers[ty]
                except KeyError:
                    pass

                # Derived marshalers are cached under their construction kwargs - a strict marshaler must not be
                # returned for a non-strict request, nor vice versa.
                try:
                    return self._derived_obj_marshalers[ck]
                except KeyError:
                    pass

            try:
                return self._proxies[ty]
            except KeyError:
                pass

            rec = functools.partial(
                self.get_obj_marshaler,
                no_cache=no_cache,
                **kwargs,
            )

            p = ProxyObjMarshaler()
            self._proxies[ty] = p
            try:
                m = self.make_obj_marshaler(ty, rec, **kwargs)
            finally:
                del self._proxies[ty]
            p._m = m  # noqa

            if not no_cache:
                self._derived_obj_marshalers[ck] = m
            return m

    def make_context(self, opts: ta.Optional[ObjMarshalOptions]) -> 'ObjMarshalContext':
        return ObjMarshalContext(
            options=opts or self._default_options,
            manager=self,
        )


def new_obj_marshaler_manager(**kwargs: ta.Any) -> ObjMarshalerManager:
    return ObjMarshalerManagerImpl(**kwargs)


##


@dc.dataclass(frozen=True)
class ObjMarshalContext:
    options: ObjMarshalOptions
    manager: ObjMarshalerManager


##


OBJ_MARSHALER_MANAGER = new_obj_marshaler_manager()

set_obj_marshaler = OBJ_MARSHALER_MANAGER.set_obj_marshaler
get_obj_marshaler = OBJ_MARSHALER_MANAGER.get_obj_marshaler

marshal_obj = OBJ_MARSHALER_MANAGER.marshal_obj
unmarshal_obj = OBJ_MARSHALER_MANAGER.unmarshal_obj


########################################
# ../../../../omcore/lite/maybes.py


##


@functools.total_ordering
class Maybe(ta.Generic[T]):
    class ValueNotPresentError(BaseException):
        pass

    #

    @property
    @abc.abstractmethod
    def present(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def must(self) -> T:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def __eq__(self, other) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __lt__(self, other) -> bool:
        raise NotImplementedError

    #

    @ta.final
    def __ne__(self, other):
        return not (self == other)

    @ta.final
    def __iter__(self) -> ta.Iterator[T]:
        if self.present:
            yield self.must()

    @ta.final
    def __bool__(self) -> ta.NoReturn:
        raise TypeError

    #

    @ta.final
    def if_present(self, consumer: ta.Callable[[T], None]) -> None:
        if self.present:
            consumer(self.must())

    @ta.final
    def filter(self, predicate: ta.Callable[[T], bool]) -> 'Maybe[T]':
        if self.present and predicate(self.must()):
            return self
        else:
            return Maybe.nothing()

    @ta.final
    def map(self, mapper: ta.Callable[[T], U]) -> 'Maybe[U]':
        if self.present:
            return Maybe.just(mapper(self.must()))
        else:
            return Maybe.nothing()

    @ta.final
    def flat_map(self, mapper: ta.Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        if self.present:
            if not isinstance(v := mapper(self.must()), Maybe):
                raise TypeError(v)
            return v
        else:
            return Maybe.nothing()

    @ta.final
    def or_else(self, other: ta.Union[T, U]) -> ta.Union[T, U]:
        if self.present:
            return self.must()
        else:
            return other

    @ta.final
    def or_none(self) -> ta.Optional[T]:
        if self.present:
            return self.must()
        else:
            return None

    @ta.final
    def or_else_get(self, supplier: ta.Callable[[], ta.Union[T, U]]) -> ta.Union[T, U]:
        if self.present:
            return self.must()
        else:
            return supplier()

    @ta.final
    def or_else_raise(self, exception_supplier: ta.Callable[[], Exception]) -> T:
        if self.present:
            return self.must()
        else:
            raise exception_supplier()

    #

    @classmethod
    def of_optional(cls, v: ta.Optional[T]) -> 'Maybe[T]':
        if v is not None:
            return cls.just(v)
        else:
            return cls.nothing()

    @classmethod
    def just(cls, v: T) -> 'Maybe[T]':
        return _JustMaybe(v)

    _nothing: ta.ClassVar['Maybe']

    @classmethod
    def nothing(cls) -> 'Maybe[T]':
        return Maybe._nothing


##


class _Maybe(Maybe[T], Abstract):
    def __lt__(self, other):
        if not isinstance(other, _Maybe):
            return NotImplemented
        sp = self.present
        op = other.present
        if self.present and other.present:
            return self.must() < other.must()
        else:
            return op and not sp


@ta.final
class _JustMaybe(_Maybe[T]):
    __slots__ = ('_v', '_hash')

    def __init__(self, v: T) -> None:
        self._v = v

    @property
    def present(self) -> bool:
        return True

    def must(self) -> T:
        return self._v

    #

    def __repr__(self) -> str:
        return f'just({self._v!r})'

    _hash: int

    def __hash__(self) -> int:
        try:
            return self._hash
        except AttributeError:
            pass
        h = self._hash = hash((_JustMaybe, self._v))
        return h

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__ and
            self._v == other._v  # noqa
        )


@ta.final
class _NothingMaybe(_Maybe[T]):
    __slots__ = ()

    @property
    def present(self) -> bool:
        return False

    def must(self) -> T:
        raise Maybe.ValueNotPresentError

    #

    def __repr__(self) -> str:
        return 'nothing()'

    def __hash__(self) -> int:
        return hash(_NothingMaybe)

    def __eq__(self, other):
        return self.__class__ is other.__class__


Maybe._nothing = _NothingMaybe()  # noqa


##


setattr(Maybe, 'just', _JustMaybe)  # noqa
setattr(Maybe, 'nothing', functools.partial(operator.attrgetter('_nothing'), Maybe))


########################################
# ../../../../omcore/lite/timeouts.py
"""
TODO:
 - Event (/ Predicate)
"""


##


class Timeout(Abstract):
    @property
    @abc.abstractmethod
    def can_expire(self) -> bool:
        """Indicates whether or not this timeout will ever expire."""

        raise NotImplementedError

    @abc.abstractmethod
    def expired(self) -> bool:
        """Return whether or not this timeout has expired."""

        raise NotImplementedError

    @abc.abstractmethod
    def remaining(self) -> float:
        """Returns the time (in seconds) remaining until the timeout expires. May be negative and/or infinite."""

        raise NotImplementedError

    @abc.abstractmethod
    def __call__(self) -> float:
        """Returns the time (in seconds) remaining until the timeout expires, or raises if the timeout has expired."""

        raise NotImplementedError

    @abc.abstractmethod
    def remaining_or(self, o: T) -> ta.Union[float, T]:
        """Evaluates time remaining via remaining() if this timeout can expire, otherwise returns `o`."""

        raise NotImplementedError

    #

    @classmethod
    def _now(cls) -> float:
        return time.monotonic()

    #

    class DEFAULT:  # Noqa
        def __new__(cls, *args, **kwargs):  # noqa
            raise TypeError

    class _NOT_SPECIFIED:  # noqa
        def __new__(cls, *args, **kwargs):  # noqa
            raise TypeError

    @classmethod
    def of(
            cls,
            obj: TimeoutLike,
            default: ta.Union[TimeoutLike, ta.Type[_NOT_SPECIFIED]] = _NOT_SPECIFIED,
    ) -> 'Timeout':
        if isinstance(obj, bool):
            if obj:
                obj = Timeout.DEFAULT
            else:
                obj = None

        if obj is None:
            return InfiniteTimeout()

        if isinstance(obj, Timeout):
            return obj

        if isinstance(obj, (float, int)):
            return DeadlineTimeout(cls._now() + obj)

        # if isinstance(obj, CanInt):
        #     return DeadlineTimeout(cls._now() + int(obj))

        if isinstance(obj, CanFloat):
            return DeadlineTimeout(cls._now() + float(obj))

        # str/bytes are Iterable but iterate to themselves, which would recurse forever.
        if isinstance(obj, ta.Iterable) and not isinstance(obj, (str, bytes)):
            return CompositeTimeout(*[Timeout.of(c) for c in obj])

        if obj is Timeout.DEFAULT:
            if default is Timeout._NOT_SPECIFIED or default is Timeout.DEFAULT:
                raise RuntimeError('Must specify a default timeout')

            else:
                return Timeout.of(default)  # type: ignore[arg-type]

        raise TypeError(obj)

    @classmethod
    def of_deadline(cls, deadline: float) -> 'DeadlineTimeout':
        return DeadlineTimeout(deadline)

    @classmethod
    def of_predicate(cls, expired_fn: ta.Callable[[], bool]) -> 'PredicateTimeout':
        return PredicateTimeout(expired_fn)


class DeadlineTimeout(Timeout):
    def __init__(
            self,
            deadline: float,
            exc: ta.Union[ta.Type[BaseException], BaseException] = TimeoutError,
    ) -> None:
        super().__init__()

        self.deadline = deadline
        self.exc = exc

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.deadline!r}, {self.exc!r})'

    @property
    def can_expire(self) -> bool:
        return True

    def expired(self) -> bool:
        return not (self.remaining() > 0)

    def remaining(self) -> float:
        return self.deadline - self._now()

    def __call__(self) -> float:
        if (rem := self.remaining()) > 0:
            return rem
        raise self.exc

    def remaining_or(self, o: T) -> ta.Union[float, T]:
        return self()


class InfiniteTimeout(Timeout):
    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    @property
    def can_expire(self) -> bool:
        return False

    def expired(self) -> bool:
        return False

    def remaining(self) -> float:
        return float('inf')

    def __call__(self) -> float:
        return float('inf')

    def remaining_or(self, o: T) -> ta.Union[float, T]:
        return o


class CompositeTimeout(Timeout):
    def __init__(self, *children: Timeout) -> None:
        super().__init__()

        self.children = children

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.children!r})'

    @property
    def can_expire(self) -> bool:
        return any(c.can_expire for c in self.children)

    def expired(self) -> bool:
        return any(c.expired() for c in self.children)

    def remaining(self) -> float:
        return min((c.remaining() for c in self.children), default=float('inf'))

    def __call__(self) -> float:
        return min((c() for c in self.children), default=float('inf'))

    def remaining_or(self, o: T) -> ta.Union[float, T]:
        if self.can_expire:
            return self()
        return o


class PredicateTimeout(Timeout):
    def __init__(
            self,
            expired_fn: ta.Callable[[], bool],
            exc: ta.Union[ta.Type[BaseException], BaseException] = TimeoutError,
    ) -> None:
        super().__init__()

        self.expired_fn = expired_fn
        self.exc = exc

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.expired_fn!r}, {self.exc!r})'

    @property
    def can_expire(self) -> bool:
        return True

    def expired(self) -> bool:
        return self.expired_fn()

    def remaining(self) -> float:
        return float('inf')

    def __call__(self) -> float:
        if not self.expired_fn():
            return float('inf')
        raise self.exc

    def remaining_or(self, o: T) -> ta.Union[float, T]:
        if not math.isinf(f := self()):
            return f
        return o


########################################
# ../../../../omcore/logs/infos.py
"""
TODO:
 - remove redundant info fields only present for std adaptation (Level.name, ...)
"""


##


def logging_context_info(cls):
    return cls


@ta.final
class LoggingContextInfos:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    #

    @logging_context_info
    @ta.final
    class Name(ta.NamedTuple):
        name: str

    @logging_context_info
    @ta.final
    class Level(ta.NamedTuple):
        level: NamedLogLevel
        name: str

        @classmethod
        def build(cls, level: int) -> 'LoggingContextInfos.Level':
            nl: NamedLogLevel = level if level.__class__ is NamedLogLevel else NamedLogLevel(level)  # noqa
            return cls(
                level=nl,
                name=logging.getLevelName(nl),
            )

    @logging_context_info
    @ta.final
    class Msg(ta.NamedTuple):
        msg: str
        args: ta.Union[tuple, ta.Mapping[ta.Any, ta.Any], None]

        @classmethod
        def build(
                cls,
                msg: ta.Union[str, tuple, LoggingMsgFn],
                *args: ta.Any,
        ) -> 'LoggingContextInfos.Msg':
            s: str
            a: ta.Any

            if callable(msg):
                if args:
                    raise TypeError(f'Must not provide both a message function and args: {msg=} {args=}')
                x = msg()
                if isinstance(x, str):
                    s, a = x, ()
                elif isinstance(x, tuple):
                    if x:
                        s, a = x[0], x[1:]
                    else:
                        s, a = '', ()
                else:
                    raise TypeError(x)

            elif isinstance(msg, tuple):
                if args:
                    raise TypeError(f'Must not provide both a tuple message and args: {msg=} {args=}')
                if msg:
                    s, a = msg[0], msg[1:]
                else:
                    s, a = '', ()

            elif isinstance(msg, str):
                s, a = msg, args

            else:
                raise TypeError(msg)

            # https://github.com/python/cpython/blob/e709361fc87d0d9ab9c58033a0a7f2fef0ad43d2/Lib/logging/__init__.py#L307  # noqa
            if a and len(a) == 1 and isinstance(a[0], collections.abc.Mapping) and a[0]:
                a = a[0]

            return cls(
                msg=s,
                args=a,
            )

    @logging_context_info
    @ta.final
    class Extra(ta.NamedTuple):
        extra: ta.Mapping[ta.Any, ta.Any]

    @logging_context_info
    @ta.final
    class Time(ta.NamedTuple):
        ns: int
        secs: float
        msecs: float
        relative_secs: float

        @classmethod
        def get_std_start_ns(cls) -> int:
            x: ta.Any = logging._startTime  # type: ignore[attr-defined]  # noqa

            # Before 3.13.0b1 this will be `time.time()`, a float of seconds. After that, it will be `time.time_ns()`,
            # an int.
            #
            # See:
            #  - https://github.com/python/cpython/commit/1316692e8c7c1e1f3b6639e51804f9db5ed892ea
            #
            if isinstance(x, float):
                return int(x * 1e9)
            else:
                return x

        @classmethod
        def build(
                cls,
                ns: int,
                *,
                start_ns: ta.Optional[int] = None,
        ) -> 'LoggingContextInfos.Time':
            # https://github.com/python/cpython/commit/1316692e8c7c1e1f3b6639e51804f9db5ed892ea
            secs = ns / 1e9  # ns to float seconds

            # Get the number of whole milliseconds (0-999) in the fractional part of seconds.
            # Eg: 1_677_903_920_999_998_503 ns --> 999_998_503 ns--> 999 ms
            # Convert to float by adding 0.0 for historical reasons. See gh-89047
            msecs = (ns % 1_000_000_000) // 1_000_000 + 0.0

            # https://github.com/python/cpython/commit/1500a23f33f5a6d052ff1ef6383d9839928b8ff1
            if msecs == 999.0 and int(secs) != ns // 1_000_000_000:
                # ns -> sec conversion can round up, e.g:
                # 1_677_903_920_999_999_900 ns --> 1_677_903_921.0 sec
                msecs = 0.0

            if start_ns is None:
                start_ns = cls.get_std_start_ns()
            relative_secs = (ns - start_ns) / 1e6

            return cls(
                ns=ns,
                secs=secs,
                msecs=msecs,
                relative_secs=relative_secs,
            )

    @logging_context_info
    @ta.final
    class Exc(ta.NamedTuple):
        info: LoggingExcInfo
        info_tuple: LoggingExcInfoTuple

        @classmethod
        def build(
                cls,
                arg: LoggingExcInfoArg = False,
        ) -> ta.Optional['LoggingContextInfos.Exc']:
            if arg is True:
                sys_exc_info = sys.exc_info()
                if sys_exc_info[0] is not None:
                    arg = sys_exc_info
                else:
                    arg = None
            elif arg is False:
                arg = None
            if arg is None:
                return None

            info: LoggingExcInfo = arg
            if isinstance(info, BaseException):
                info_tuple: LoggingExcInfoTuple = (type(info), info, info.__traceback__)  # noqa
            else:
                info_tuple = info

            return cls(
                info=info,
                info_tuple=info_tuple,
            )

    @logging_context_info
    @ta.final
    class Caller(ta.NamedTuple):
        file_path: str
        line_no: int
        func_name: str
        stack_info: ta.Optional[str]

        @classmethod
        def is_internal_frame(cls, frame: types.FrameType) -> bool:
            file_path = os.path.normcase(frame.f_code.co_filename)

            # Yes, really.
            # https://github.com/python/cpython/blob/e709361fc87d0d9ab9c58033a0a7f2fef0ad43d2/Lib/logging/__init__.py#L204  # noqa
            # https://github.com/python/cpython/commit/5ca6d7469be53960843df39bb900e9c3359f127f
            if 'importlib' in file_path and '_bootstrap' in file_path:
                return True

            return False

        @classmethod
        def find_frame(cls, stack_offset: int = 0) -> ta.Optional[types.FrameType]:
            f: ta.Optional[types.FrameType] = sys._getframe(2 + stack_offset)  # noqa

            while f is not None:
                # NOTE: We don't check __file__ like stdlib since we may be running amalgamated - we rely on careful,
                # manual stack_offset management.
                if hasattr(f, 'f_code'):
                    return f

                f = f.f_back

            return None

        @classmethod
        def build(
                cls,
                stack_offset: int = 0,
                *,
                stack_info: bool = False,
        ) -> ta.Optional['LoggingContextInfos.Caller']:
            if (f := cls.find_frame(stack_offset + 1)) is None:
                return None

            # https://github.com/python/cpython/blob/08e9794517063c8cd92c48714071b1d3c60b71bd/Lib/logging/__init__.py#L1616-L1623  # noqa
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                sio.close()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]

            return cls(
                file_path=f.f_code.co_filename,
                line_no=f.f_lineno or 0,
                func_name=f.f_code.co_name,
                stack_info=sinfo,
            )

    @logging_context_info
    @ta.final
    class SourceFile(ta.NamedTuple):
        file_name: str
        module: str

        @classmethod
        def build(cls, caller_file_path: ta.Optional[str]) -> ta.Optional['LoggingContextInfos.SourceFile']:
            if caller_file_path is None:
                return None

            # https://github.com/python/cpython/blob/e709361fc87d0d9ab9c58033a0a7f2fef0ad43d2/Lib/logging/__init__.py#L331-L336  # noqa
            try:
                file_name = os.path.basename(caller_file_path)
                module = os.path.splitext(file_name)[0]
            except (TypeError, ValueError, AttributeError):
                return None

            return cls(
                file_name=file_name,
                module=module,
            )

    @logging_context_info
    @ta.final
    class Thread(ta.NamedTuple):
        ident: int
        native_id: ta.Optional[int]
        name: str

        @classmethod
        def build(cls) -> 'LoggingContextInfos.Thread':
            return cls(
                ident=threading.get_ident(),
                native_id=threading.get_native_id() if hasattr(threading, 'get_native_id') else None,
                name=threading.current_thread().name,
            )

    @logging_context_info
    @ta.final
    class Process(ta.NamedTuple):
        pid: int

        @classmethod
        def build(cls) -> 'LoggingContextInfos.Process':
            return cls(
                pid=os.getpid(),
            )

    @logging_context_info
    @ta.final
    class Multiprocessing(ta.NamedTuple):
        process_name: str

        @classmethod
        def build(cls) -> ta.Optional['LoggingContextInfos.Multiprocessing']:
            # https://github.com/python/cpython/blob/e709361fc87d0d9ab9c58033a0a7f2fef0ad43d2/Lib/logging/__init__.py#L355-L364  # noqa
            if (mp := sys.modules.get('multiprocessing')) is None:
                return None

            return cls(
                process_name=mp.current_process().name,
            )

    @logging_context_info
    @ta.final
    class AsyncioTask(ta.NamedTuple):
        name: str

        @classmethod
        def build(cls) -> ta.Optional['LoggingContextInfos.AsyncioTask']:
            # https://github.com/python/cpython/blob/e709361fc87d0d9ab9c58033a0a7f2fef0ad43d2/Lib/logging/__init__.py#L372-L377  # noqa
            if (asyncio := sys.modules.get('asyncio')) is None:
                return None

            try:
                task = asyncio.current_task()
            except Exception:  # noqa
                return None

            if task is None:
                return None

            return cls(
                name=task.get_name(),  # Always non-None
            )


##


class UnexpectedLoggingStartTimeWarning(LoggingSetupWarning):
    pass


def _check_logging_start_time() -> None:
    if (x := LoggingContextInfos.Time.get_std_start_ns()) < (t := time.time()):
        import warnings  # noqa

        warnings.warn(
            f'Unexpected logging start time detected: '
            f'get_std_start_ns={x}, '
            f'time.time()={t}',
            UnexpectedLoggingStartTimeWarning,
        )


_check_logging_start_time()


########################################
# ../../../../omcore/logs/metrics/base.py


##


class LoggerMetricUnit(Abstract):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            mut = LOGGER_METRIC_UNIT_TYPES
        except NameError:
            pass
        else:
            bcs = [bc for bc in mut if issubclass(cls, bc)]
            if len(bcs) != 1:
                raise TypeError(f'{cls.__name__} must be a subclass of exactly one of {mut}, got {bcs}.')

        try:
            mtc = LoggerMetric
        except NameError:
            pass
        else:
            if issubclass(cls, mtc):
                mp = cls.__mro__.index(mtc)
                mup = cls.__mro__.index(LoggerMetricUnit)
                if mup > mp:
                    raise TypeError(f'{cls.__name__} must have Metric before MetricUnit in its MRO.')


class CountLoggerMetricUnit(LoggerMetricUnit):
    @classmethod
    def default_value(cls) -> ta.Optional[float]:
        return 1


class RatioLoggerMetricUnit(LoggerMetricUnit):
    pass


class SecondsLoggerMetricUnit(LoggerMetricUnit):
    pass


class BytesLoggerMetricUnit(LoggerMetricUnit):
    pass


LOGGER_METRIC_UNIT_TYPES: ta.Tuple[ta.Type[LoggerMetricUnit], ...] = (
    CountLoggerMetricUnit,
    RatioLoggerMetricUnit,
    SecondsLoggerMetricUnit,
    BytesLoggerMetricUnit,
)


##


class LoggerMetricTag(Abstract):
    pass


##


class LoggerMetric(Abstract):
    @ta.final
    def __init__(self, value: ta.Optional[float] = None, *tags: LoggerMetricTag) -> None:
        if value is None:
            value = self.default_value()
        if value is None:
            raise ValueError(f'{type(self).__name__} has no default value.')

        self.__value = value
        self.__tags = tags

    @property
    def value(self) -> float:
        return self.__value

    @classmethod
    def default_value(cls) -> ta.Optional[float]:
        return None

    @property
    def tags(self) -> ta.Sequence[LoggerMetricTag]:
        return self.__tags

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value!r}, {", ".join(map(repr, self.tags))})'

    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        try:
            mtt = LOGGER_METRIC_TYPES
        except NameError:
            pass
        else:
            bcs = [bc for bc in mtt if issubclass(cls, bc)]
            if Abstract in cls.__bases__:
                if len(bcs) > 1:
                    raise TypeError(f'{cls.__name__} must be a subclass of at most one of {mtt}, got {bcs}.')
            else:
                if len(bcs) != 1:
                    raise TypeError(f'{cls.__name__} must be a subclass of exactly one of {mtt}, got {bcs}.')

        # if Abstract not in cls.__bases__ and not issubclass(cls, LoggerMetricUnit):
        #     raise TypeError(f'{cls.__name__} must be a subclass of LoggerMetricUnit.')


class CounterLoggerMetric(CountLoggerMetricUnit, LoggerMetric, Abstract):
    pass


class GaugeLoggerMetric(LoggerMetric, Abstract):
    pass


class HistogramLoggerMetric(LoggerMetric, Abstract):
    pass


LOGGER_METRIC_TYPES: ta.Tuple[ta.Type[LoggerMetric], ...] = (
    CounterLoggerMetric,
    GaugeLoggerMetric,
    HistogramLoggerMetric,
)


##


class AnyLoggerMetricCollector(Abstract, ta.Generic[T]):
    @ta.final
    def metric(self, m: LoggerMetric) -> T:
        return self._metric(m)

    @abc.abstractmethod
    def _metric(self, m: LoggerMetric) -> T:
        raise NotImplementedError


class LoggerMetricCollector(AnyLoggerMetricCollector[None], Abstract):
    @abc.abstractmethod
    def _metric(self, m: LoggerMetric) -> None:
        raise NotImplementedError


class AsyncLoggerMetricCollector(AnyLoggerMetricCollector[ta.Awaitable[None]], Abstract):
    @abc.abstractmethod
    def _metric(self, m: LoggerMetric) -> ta.Awaitable[None]:
        raise NotImplementedError


##


class AnyNopLoggerMetricCollector(AnyLoggerMetricCollector[T], Abstract):
    pass


class NopLoggerMetricCollector(AnyNopLoggerMetricCollector[None], LoggerMetricCollector):
    @ta.final
    def _metric(self, m: LoggerMetric) -> None:
        pass


class AsyncNopLoggerMetricCollector(AnyNopLoggerMetricCollector[ta.Awaitable[None]], AsyncLoggerMetricCollector):
    @ta.final
    async def _metric(self, m: LoggerMetric) -> None:
        pass


########################################
# ../../../../omcore/logs/protocols.py


##


@ta.runtime_checkable
class LoggerLike(ta.Protocol):
    """Satisfied by both our Logger and stdlib logging.Logger."""

    def isEnabledFor(self, level: LogLevel) -> bool: ...  # noqa

    def getEffectiveLevel(self) -> LogLevel: ...  # noqa

    #

    def log(self, level: LogLevel, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def debug(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def info(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def warning(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def error(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def exception(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa

    def critical(self, msg: str, /, *args: ta.Any, **kwargs: ta.Any) -> None: ...  # noqa


########################################
# ../../../../omcore/rpc/ids.py
"""
Request id creators. Ids are opaque and scoped to the direction they were issued in, so they only need to be unique
among the issuing side's pending requests and pings: a counter suffices, and is the default.
"""


##


class RpcIdCreator(Abstract):
    @abc.abstractmethod
    def __call__(self) -> ta.Any:
        raise NotImplementedError


class IntRpcIdCreator(RpcIdCreator):
    def __init__(self, start: int = 1) -> None:
        super().__init__()

        # itertools.count is atomic under both the GIL and free-threading.
        self._counter = itertools.count(start)

    def __call__(self) -> ta.Any:
        return next(self._counter)


class UuidRpcIdCreator(RpcIdCreator):
    def __call__(self) -> ta.Any:
        return str(uuid.uuid4())


class FnRpcIdCreator(RpcIdCreator):
    def __init__(self, fn: ta.Callable[[], ta.Any]) -> None:
        super().__init__()

        self._fn = fn

    def __call__(self) -> ta.Any:
        return self._fn()


def rpc_id_creator_of(obj: ta.Optional[RpcIdCreatorLike]) -> RpcIdCreator:
    if obj is None:
        return IntRpcIdCreator()
    if isinstance(obj, RpcIdCreator):
        return obj
    if callable(obj):
        return FnRpcIdCreator(obj)
    raise TypeError(obj)


########################################
# ../../environment/ops.py
"""
What an environment - the machine or container the tools work in - says of itself. `EnvironmentOps` is asked once, at
an agent's setup, for the facts which go into its system prompt and for its working directory; a remote environment
answers through the remote agent. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and standard
library only.
"""


##


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class EnvironmentInfo:
    # The working directory, absolute and symlink-resolved in the environment's own namespace.
    cwd: str

    # `platform.system()`, `platform.release()`, and `platform.machine()` there: 'Linux', '6.8.0-138-generic', 'x86_64'.
    system: str
    release: str
    machine: str

    hostname: str

    @ta.final
    @install_dataclass_kw_only_init()
    @dc.dataclass(frozen=True)
    class User:
        name: ta.Optional[str] = None
        home: ta.Optional[str] = None
        shell: ta.Optional[str] = None

    # The user the tools run as, and that user's home and shell, where they can be told.
    user: ta.Optional[User] = None

    # The container runtime the environment finds itself running under - 'docker', 'podman' - or None where none is
    # detected. Detected from inside, so it says nothing of how the environment is reached.
    container: ta.Optional[str] = None

    # Whether the environment is somewhere other than where the harness runs, so that the tools' files and processes are
    # not the user's own machine's. Set by whatever reaches a remote environment, never by the environment itself.
    remote: bool = False


EnvironmentInfoGetter = ta.Callable[[], ta.Awaitable[EnvironmentInfo]]  # ta.TypeAlias  # om-amalg-typing-no-move


##


class EnvironmentOps(Abstract):
    @abc.abstractmethod
    def inspect_environment(
            self,
            *,
            cwd: ta.Optional[str] = None,
    ) -> ta.Awaitable[EnvironmentInfo]:
        """
        Describes the environment, with its working directory resolved: the one given, in the environment's own
        namespace and relative to its own directory if not absolute, or that directory itself. A directory which does
        not exist there raises FileNotFoundError, and a path there which is not a directory NotADirectoryError.
        """

        raise NotImplementedError


########################################
# ../../fs/ops.py


##


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsFile:
    data: bytes

    # Opaque content identity suitable for a compare-before-write check.
    digest: str


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsEntry:
    """
    A path's metadata, following symlinks as `os.stat` does - `is_symlink` alone is of the path itself, and an entry
    listed from a directory or a glob which is a dangling symlink is of the link. The numeric fields are
    `os.stat_result`'s, less their `st_` prefix; the optional ones are those not every platform has.
    """

    # The path as given, and its absolute, symlink-resolved form.
    path: str
    resolved_path: str

    is_dir: bool
    is_file: bool
    is_symlink: bool

    mode: int
    ino: int
    dev: int
    nlink: int
    uid: int
    gid: int
    size: int

    atime_ns: int
    mtime_ns: int
    ctime_ns: int

    blksize: int
    blocks: int
    rdev: int

    flags: ta.Optional[int] = None
    gen: ta.Optional[int] = None
    birthtime_ns: ta.Optional[int] = None

    @property
    def atime(self) -> float:
        return self.atime_ns / 1e9

    @property
    def mtime(self) -> float:
        return self.mtime_ns / 1e9

    @property
    def ctime(self) -> float:
        return self.ctime_ns / 1e9

    @property
    def birthtime(self) -> ta.Optional[float]:
        return self.birthtime_ns / 1e9 if self.birthtime_ns is not None else None


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsWriteResult:
    created: bool


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsGlobResult:
    entries: ta.Sequence[FsEntry]

    has_more: bool = False


##


class FsOps(Abstract):
    @abc.abstractmethod
    def resolve_path(self, path: str) -> ta.Awaitable[str]:
        """Returns the target filesystem's absolute, symlink-resolved form of a path."""

        raise NotImplementedError

    @abc.abstractmethod
    def stat(self, path: str) -> ta.Awaitable[FsEntry]:
        raise NotImplementedError

    @abc.abstractmethod
    def read_file(self, path: str) -> ta.Awaitable[FsFile]:
        raise NotImplementedError

    @abc.abstractmethod
    def write_file(
            self,
            path: str,
            content: BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> ta.Awaitable[FsWriteResult]:
        """
        Writes a complete file, optionally replacing an existing regular file. `expected_digest` makes replacement
        fail if the current content no longer matches a previously-read `FsFile`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def list_dir(self, path: str) -> ta.Awaitable[ta.Sequence[FsEntry]]:
        raise NotImplementedError

    @abc.abstractmethod
    def glob(
            self,
            pattern: str,
            *,
            max_results: ta.Optional[int] = None,
    ) -> ta.Awaitable[FsGlobResult]:
        """
        The entries matching an absolute pattern, as the glob produced them and with nothing filtered: what a caller
        may see of them is the caller's to decide, from their resolved paths.
        """

        raise NotImplementedError


########################################
# ../../fs/remote/protocol.py
"""
The wire shapes of the remote filesystem: the requests the host's `RemoteFsOps` makes of the agent's `RemoteFsService`,
and their results. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and marshaled with the lite
marshaler.

File content crosses the connection in chunks, so a file's size is bounded by memory rather than by the rpc's frame
limit. A read starts with `fs.read_file`, which returns either the whole file or its first chunk and a handle through
which `fs.read_chunk` fetches the rest; the agent releases the handle with the last chunk, or on `fs.read_abort`. A
write which fits one chunk is a single `fs.write_file`; a larger one is staged with `fs.write_begin` and
`fs.write_chunk`, then made visible atomically by `fs.write_commit` (or discarded by `fs.write_abort`), with exactly the
semantics of the single call.
"""


##


REMOTE_FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
REMOTE_FS_STAT_METHOD = 'fs.stat'
REMOTE_FS_LIST_DIR_METHOD = 'fs.list_dir'
REMOTE_FS_GLOB_METHOD = 'fs.glob'

REMOTE_FS_READ_FILE_METHOD = 'fs.read_file'
REMOTE_FS_READ_CHUNK_METHOD = 'fs.read_chunk'
REMOTE_FS_READ_ABORT_METHOD = 'fs.read_abort'

REMOTE_FS_WRITE_FILE_METHOD = 'fs.write_file'
REMOTE_FS_WRITE_BEGIN_METHOD = 'fs.write_begin'
REMOTE_FS_WRITE_CHUNK_METHOD = 'fs.write_chunk'
REMOTE_FS_WRITE_COMMIT_METHOD = 'fs.write_commit'
REMOTE_FS_WRITE_ABORT_METHOD = 'fs.write_abort'

# No piece of file content on the wire exceeds this, so that no frame approaches the rpc's limit once base64 encoded.
# The agent refuses larger ones.
REMOTE_FS_MAX_CHUNK_BYTES = 8 * 1024 * 1024


##
# Paths


@dc.dataclass(frozen=True)
class RemoteFsPathParams:
    path: str


@dc.dataclass(frozen=True)
class RemoteFsEntry:
    path: str
    resolved_path: str

    is_dir: bool
    is_file: bool
    is_symlink: bool

    mode: int
    ino: int
    dev: int
    nlink: int
    uid: int
    gid: int
    size: int

    atime_ns: int
    mtime_ns: int
    ctime_ns: int

    blksize: int
    blocks: int
    rdev: int

    flags: ta.Optional[int]
    gen: ta.Optional[int]
    birthtime_ns: ta.Optional[int]

    def __post_init__(self) -> None:
        check.arg(self.size >= 0)


@dc.dataclass(frozen=True)
class RemoteFsGlobParams:
    pattern: str
    max_results: ta.Optional[int]

    def __post_init__(self) -> None:
        if self.max_results is not None:
            check.arg(self.max_results >= 0)


@dc.dataclass(frozen=True)
class RemoteFsGlobResult:
    entries: ta.List[RemoteFsEntry]
    has_more: bool


##
# Handles


@dc.dataclass(frozen=True)
class RemoteFsHandleParams:
    handle: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)


@dc.dataclass(frozen=True)
class RemoteFsHandleResult:
    handle: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)


##
# Reads


@dc.dataclass(frozen=True)
class RemoteFsReadFileParams:
    path: str
    max_bytes: int

    def __post_init__(self) -> None:
        check.arg(0 < self.max_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsReadFileResult:
    """The file's first `max_bytes`: all of it, with its digest, or else the rest follows through `handle`."""

    data: bytes
    digest: ta.Optional[str]
    handle: ta.Optional[str]

    def __post_init__(self) -> None:
        check.arg((self.digest is None) != (self.handle is None))
        if self.digest is not None:
            check.non_empty_str(self.digest)
        if self.handle is not None:
            check.non_empty_str(self.handle)


@dc.dataclass(frozen=True)
class RemoteFsReadChunkParams:
    handle: str
    max_bytes: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)
        check.arg(0 < self.max_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsReadChunkResult:
    """More of the file. A digest means that was the last of it, and its handle is gone."""

    data: bytes
    digest: ta.Optional[str]

    def __post_init__(self) -> None:
        if self.digest is not None:
            check.non_empty_str(self.digest)


##
# Writes


@dc.dataclass(frozen=True)
class RemoteFsWriteFileParams:
    path: str
    content: bytes
    overwrite: bool
    expected_digest: ta.Optional[str]

    def __post_init__(self) -> None:
        check.arg(len(self.content) <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsWriteFileResult:
    created: bool


@dc.dataclass(frozen=True)
class RemoteFsWriteChunkParams:
    handle: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)
        check.arg(len(self.data) <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsWriteCommitParams:
    handle: str
    overwrite: bool
    expected_digest: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)


########################################
# ../../../core/processes/remote/protocol.py
"""
The wire shapes of remote process management: the requests the host's `RemoteProcessManager` makes of the agent's
`RemoteProcessService`, their results, and the notifications the agent sends back unprompted. Lite: shared with the
remote agent amalgam, so Python 3.8 compatible and marshaled with the lite marshaler.
"""


##


REMOTE_PROCESS_SPAWN_METHOD = 'process.spawn'
REMOTE_PROCESS_SIGNAL_METHOD = 'process.signal'
REMOTE_PROCESS_CLOSE_METHOD = 'process.close'
REMOTE_PROCESS_WRITE_METHOD = 'process.write'
REMOTE_PROCESS_WRITE_EOF_METHOD = 'process.write_eof'
REMOTE_PROCESS_RESIZE_METHOD = 'process.resize'

REMOTE_PROCESS_OUTPUT_METHOD = 'process.output'
REMOTE_PROCESS_OUTPUT_END_METHOD = 'process.output_end'
REMOTE_PROCESS_EXITED_METHOD = 'process.exited'

# The agent's unprompted notifications, which the host applies inline, in wire order.
REMOTE_PROCESS_EVENT_METHODS = frozenset([
    REMOTE_PROCESS_OUTPUT_METHOD,
    REMOTE_PROCESS_OUTPUT_END_METHOD,
    REMOTE_PROCESS_EXITED_METHOD,
])


##
# Requests


@dc.dataclass(frozen=True)
class RemoteProcessStdioSpec:
    kind: str
    stdin: ta.Optional[str] = None
    stdout: ta.Optional[str] = None
    stderr: ta.Optional[str] = None
    rows: ta.Optional[int] = None
    cols: ta.Optional[int] = None
    term: ta.Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind == 'pipes':
            check.non_empty_str(self.stdin)
            check.non_empty_str(self.stdout)
            check.non_empty_str(self.stderr)
        elif self.kind == 'pty':
            check.arg(self.rows is not None and self.rows >= 1)
            check.arg(self.cols is not None and self.cols >= 1)
        else:
            raise ValueError(f'Invalid remote stdio kind: {self.kind!r}')


@dc.dataclass(frozen=True)
class RemoteProcessSpawnParams:
    argv: ta.List[str]
    cwd: ta.Optional[str]
    env: ta.Optional[ta.Dict[str, str]]
    stdio: RemoteProcessStdioSpec
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.not_empty(self.argv)


@dc.dataclass(frozen=True)
class RemoteProcessSpawnResult:
    id: str
    pid: int
    created_at: float
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.pid >= 1)
        check.arg(self.created_at >= 0.)


@dc.dataclass(frozen=True)
class RemoteProcessSignalParams:
    id: str
    signal: int
    process_group: bool

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.signal >= 1)


@dc.dataclass(frozen=True)
class RemoteProcessClosePolicySpec:
    signal: int
    grace_s: float
    kill_s: float
    close_stdin: bool
    process_group: bool
    drain_s: float

    def __post_init__(self) -> None:
        check.arg(self.signal >= 1)
        check.arg(self.grace_s >= 0.)
        check.arg(self.kill_s >= 0.)
        check.arg(self.drain_s >= 0.)


@dc.dataclass(frozen=True)
class RemoteProcessCloseParams:
    id: str
    policy: RemoteProcessClosePolicySpec

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessCloseResult:
    returncode: int
    state: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.state)


@dc.dataclass(frozen=True)
class RemoteProcessWriteParams:
    id: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessRefParams:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessResizeParams:
    id: str
    rows: int
    cols: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.rows >= 1)
        check.arg(self.cols >= 1)


##
# Notifications (agent -> host)


@dc.dataclass(frozen=True)
class RemoteProcessOutputEvent:
    id: str
    fd: int
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.fd >= 1)


@dc.dataclass(frozen=True)
class RemoteProcessOutputEndEvent:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessExitedEvent:
    id: str
    returncode: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


########################################
# ../../../../omcore/asyncs/asyncio/timeouts.py


##


def asyncio_maybe_timeout(
        fut: AwaitableT,
        timeout: TimeoutLike = None,
) -> AwaitableT:
    if timeout is not None:
        try:
            seconds = Timeout.of(timeout)()
        except BaseException:
            asyncio.ensure_future(fut).cancel()
            raise
        fut = asyncio.wait_for(fut, seconds)  # type: ignore
    return fut


########################################
# ../../../../omcore/asyncs/asynclite/asyncio/base.py


##


class AsyncioAsyncliteBase(Abstract):
    @classmethod
    @contextlib.contextmanager
    def _translate_exceptions(cls) -> ta.Generator[None, None, None]:
        try:
            yield

        except asyncio.TimeoutError as e:
            raise TimeoutError from e

        except asyncio.QueueEmpty as e:
            raise queue.Empty from e

        except asyncio.QueueFull as e:
            raise queue.Full from e

    @classmethod
    async def _wait_for(cls, aw: ta.Awaitable[T], *, timeout: ta.Optional[float] = None) -> T:
        if timeout is not None:
            with cls._translate_exceptions():
                return await asyncio.wait_for(aw, timeout)

        else:
            return await aw


class AsyncioAsyncliteObject(AsyncliteObject, AsyncioAsyncliteBase, Abstract):
    pass


class AsyncioAsyncliteApi(AsyncliteApi, AsyncioAsyncliteBase, Abstract):
    pass


########################################
# ../../../../omcore/asyncs/asynclite/events.py


##


class AsyncliteEvent(AsyncliteObject, Abstract):
    @abc.abstractmethod
    def set(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def is_set(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, *, timeout: ta.Optional[float] = None) -> ta.Awaitable[None]:
        raise NotImplementedError


class AsyncliteEvents(AsyncliteApi, Abstract):
    @abc.abstractmethod
    def make_event(self) -> AsyncliteEvent:
        raise NotImplementedError


########################################
# ../../../../omcore/asyncs/asynclite/promises.py


##


class AsynclitePromiseError(Exception):
    pass


class AsynclitePromiseAlreadySetError(AsynclitePromiseError):
    pass


class AsynclitePromiseWaitTimeoutError(AsynclitePromiseError, TimeoutError):
    pass


class AsynclitePromise(AsyncliteObject, Abstract, ta.Generic[T]):
    """
    A one-shot, write-once result cell - one producer, any number of waiters. Waiter-side timeouts and cancellation
    only ever affect that waiter - never the promise itself or any other waiter.
    """

    @abc.abstractmethod
    def is_done(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def poll(self) -> Maybe[T]:
        """Never blocks - empty while pending, otherwise the value, raising if the promise was set to an error."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_value(self, v: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def set_error(self, e: BaseException) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, *, timeout: ta.Optional[float] = None) -> ta.Awaitable[T]:
        raise NotImplementedError


class AsynclitePromises(AsyncliteApi, Abstract):
    @abc.abstractmethod
    def make_promise(self) -> AsynclitePromise:
        raise NotImplementedError


########################################
# ../../../../omcore/io/pipelines/asyncs.py


##


class AsyncIoPipelineMessages(NamespaceClass):
    @ta.final
    @dc.dataclass(frozen=True)
    class Await(
        IoPipelineMessages.Completable[T],
        IoPipelineMessages.NeverInbound,
        IoPipelineMessages.AfterShutdownOutput,
        ta.Generic[T],
    ):
        obj: ta.Awaitable[T]


########################################
# ../../../../omcore/io/pipelines/bytes/buffering.py


##


class InboundBytesBufferingIoPipelineHandler(IoPipelineHandler, Abstract):
    @abc.abstractmethod
    def inbound_buffered_bytes(self) -> ta.Optional[int]:
        """Returning `None` denotes currently unknown/unanswerable."""

        raise NotImplementedError


class OutboundBytesBufferingIoPipelineHandler(IoPipelineHandler, Abstract):
    @abc.abstractmethod
    def outbound_buffered_bytes(self) -> ta.Optional[int]:
        """Returning `None` denotes currently unknown/unanswerable."""

        raise NotImplementedError


########################################
# ../../../../omcore/io/pipelines/drivers/metadata.py


##


class DriverIoPipelineMetadata(IoPipelineMetadata):
    def __init__(self, driver: ta.Any) -> None:
        super().__init__()

        self.__driver_ref = weakref.ref(driver)

    @property
    def driver(self) -> ta.Any:
        return check.not_none(self.__driver_ref())


########################################
# ../../../../omcore/io/pipelines/flow/types.py


##


class IoPipelineFlowMessages(NamespaceClass):
    """
    Note: these inbound messages will never be sent without a `IoPipelineFlow` instance in `channel.services` -
    thus it's safe to refer to `ctx.services[IoPipelineFlow]` when handling these.
    """

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class FlushInput(  # ~ Netty `ChannelInboundInvoker::fireChannelReadComplete`  # noqa
        IoPipelineMessages.MayPropagate,
        IoPipelineMessages.NeverOutbound,
    ):
        pass

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class FlushOutput(  # ~ Netty 'ChannelOutboundInvoker::flush'
        IoPipelineMessages.MayPropagate,
        IoPipelineMessages.NeverInbound,
        IoPipelineMessages.AfterShutdownOutput,
        IoPipelineMessages.Completable[None],
    ):
        """
        Ordered transport-flush fence.

        Success means all preceding output has left pipeline-owned buffering and crossed the driver's transport
        boundary; it does not mean that the peer received or acknowledged the data.
        """

    @ta.final
    @dc.dataclass(frozen=True)
    class ReadyForInput(  # ~ Netty `ChannelOutboundInvoker::read`
        IoPipelineMessages.MayPropagate,
        IoPipelineMessages.NeverInbound,
        IoPipelineMessages.AfterShutdownOutput,
    ):
        pass

    ##
    # Output writability contract:
    #  - Level-triggered writability, edge-notified: emitters send one message per *transition*, never repeats.
    #    ReadyForOutput means 'output may flow'; PauseOutput means 'stop producing output'.
    #  - They flow INBOUND (transport -> app), originated by the transport head (or a dedicated watermark handler
    #    watching an OutboundBytesBufferingIoPipelineHandler) from its unflushed backlog vs high/low watermarks.
    #  - Handlers that buffer outbound data (ssl, compression, ...) do not forward these blindly: they combine the
    #    transport-side signal with their own buffer level and re-announce the COMBINED value inbound, again only on
    #    change. Pass-through handlers just propagate.
    #  - The implied initial state is writable; a pipeline that never sends either message behaves as if ReadyForOutput
    #    were always in effect. As with the other flow messages, these are only ever sent when an IoPipelineFlow service
    #    is present.

    #

    @ta.final
    @dc.dataclass(frozen=True)
    class ReadyForOutput(  # ~ Netty `ChannelInboundInvoker::fireChannelWritabilityChanged` # noqa
        IoPipelineMessages.MayPropagate,
        IoPipelineMessages.NeverOutbound,
        IoPipelineMessages.AfterFinalInput,
    ):
        pass

    @ta.final
    @dc.dataclass(frozen=True)
    class PauseOutput(  # ~ Netty `ChannelInboundInvoker::fireChannelWritabilityChanged` # noqa
        IoPipelineMessages.MayPropagate,
        IoPipelineMessages.NeverOutbound,
        IoPipelineMessages.AfterFinalInput,
    ):
        pass


##


class IoPipelineFlow(Abstract):
    def _get_instance(
            self: ta.Union[
                'IoPipelineFlow',
                IoPipeline,
                IoPipelineHandlerContext,
                None,
            ],
    ) -> ta.Optional['IoPipelineFlow']:
        # This strange construct grants the ability to do things like `IoPipelineFlow.is_auto_read(opt_flow)`, which are
        # becoming increasingly frequently useful in real code.
        if self is None:
            return None

        if isinstance(self, IoPipelineFlow):
            return self

        if isinstance(self, IoPipelineHandlerContext):
            self = self._pipeline  # noqa

        if isinstance(self, IoPipeline):
            return self.services.find(IoPipelineFlow)

        raise TypeError(self)

    #

    @abc.abstractmethod
    def is_auto_read(
            self: ta.Union[
                'IoPipelineFlow',
                IoPipeline,
                IoPipelineHandlerContext,
                None,
            ],
    ) -> bool:
        return (fc := IoPipelineFlow._get_instance(self)) is None or fc.is_auto_read()

    #

    @ta.final
    @classmethod
    def maybe_flush_output(cls, ctx: IoPipelineHandlerContext) -> None:
        if cls._get_instance(ctx) is not None:
            ctx.feed_out(IoPipelineFlowMessages.FlushOutput())

    @ta.final
    @classmethod
    def maybe_ready_for_input(cls, ctx: IoPipelineHandlerContext) -> None:
        if (fc := cls._get_instance(ctx)) is not None and not fc.is_auto_read():
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())


########################################
# ../../../../omcore/io/pipelines/posting/types.py
"""
Posting: running work inside a pipeline's execution boundary from outside its driver's current turn - from application
code between driver steps, from another pipeline's turn on the same thread, or from the pipeline's own turn.

A post is queued at the driver's boundary like an enqueued message: it runs after the boundary input queued before it
and before that queued after it, when the driver next processes its queue, and so never nested inside a turn already in
progress. A driver which is idle is woken by it. Nothing here is thread-safe: posts are made on the driver's thread.
"""


##


class ClosedIoPipelinePostingError(StateIoPipelineError):
    """The driver has closed or failed, or the stream has ended, so nothing can be posted into the pipeline any more."""


@ta.final
@dc.dataclass(frozen=True, eq=False)
class IoPipelinePost(IoPipelineMessages.Completable[T], ta.Generic[T]):
    """
    Work posted into a pipeline. Completes with the callable's result once it has run; fails with the exception it
    raised, with AbortedIoPipelineError if the driver closed before it ran, or with ContextInvalidatedIoPipelineError
    if the handler it was posted for was removed first. As for any completable, the outcome is observable only from a
    listener.
    """

    fn: ta.Union[
        ta.Callable[[], T],
        ta.Callable[[IoPipelineHandlerContext], T],
    ]

    _ctx_ref: ta.Optional[ta.Callable[[], ta.Optional[IoPipelineHandlerContext]]] = dc.field(default=None, repr=False)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}({self.fn!r})'

    def run(self, pipeline: IoPipeline) -> None:
        """
        Runs the post inside the pipeline's execution boundary, if it is still pending: for drivers. An exception from
        the callable fails the post and nothing else; one from a completion listener, or a propagation failure on
        leaving the boundary, is the driver's to handle as it handles any other.
        """

        if self.is_done():
            return

        with pipeline.enter():
            try:
                if (ctx_ref := self._ctx_ref) is not None:
                    if (ctx := ctx_ref()) is None or ctx.invalidated:
                        raise ContextInvalidatedIoPipelineError
                    res = self.fn(ctx)  # type: ignore[call-arg]
                else:
                    res = self.fn()  # type: ignore[call-arg]

            except Exception as e:  # noqa
                self.set_failed(e)

            else:
                self.set_succeeded(res)


def fail_io_pipeline_posts(posts: ta.Iterable[IoPipelinePost], exc: BaseException) -> None:
    """Fails every pending post given, raising the first listener error once all have been failed. For drivers."""

    first_listener_exc: ta.Optional[BaseException] = None

    for post in posts:
        if post.is_done():
            continue
        try:
            post.set_failed(exc)
        except BaseException as listener_exc:  # noqa
            if first_listener_exc is None:
                first_listener_exc = listener_exc

    if first_listener_exc is not None:
        raise first_listener_exc


##


class IoPipelinePosting(Abstract):
    """
    Posts work into one pipeline.

    Every driver installs one as a service, as every driver installs scheduling, and it is looked up from
    `ctx.services` by this interface; a pipeline without a driver has none, since nothing would wake for it. A handler
    requiring it validates its presence when added. A multiplexed stream's pipeline has one when its parent does, which
    reaches the stream through the parent's.
    """

    @abc.abstractmethod
    def post(self, fn: ta.Callable[[], T]) -> IoPipelinePost[T]:
        """Queues `fn` to run in the pipeline. Raises ClosedIoPipelinePostingError if nothing can run it any more."""

        raise NotImplementedError

    @abc.abstractmethod
    def post_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            fn: ta.Callable[[IoPipelineHandlerContext], T],
    ) -> IoPipelinePost[T]:
        """
        Queues `fn` to run with the handler's context, which is held only weakly until then - the submitter need not
        retain the ref - failing the post if the handler has been removed by the time it runs.
        """

        raise NotImplementedError


class IoPipelinePostingTarget(Abstract):
    """What a posting service hands posts to: a driver, or something which routes them to one."""

    @abc.abstractmethod
    def accept_post(self, post: IoPipelinePost) -> None:
        """
        Queues the post at the pipeline's boundary and arranges for it to run promptly. Raises
        ClosedIoPipelinePostingError if nothing can run it any more.
        """

        raise NotImplementedError


@ta.final
class TargetIoPipelinePostingService(IoPipelinePosting, IoPipelineService):
    """The posting service a driver installs: it forwards to its target, which it holds only weakly."""

    def __init__(self, target: IoPipelinePostingTarget) -> None:
        super().__init__()

        self.__target_ref = weakref.ref(target)
        self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

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
            self.__pipeline_ref = None

    def _target(self) -> IoPipelinePostingTarget:
        if (target := self.__target_ref()) is None:
            raise ClosedIoPipelinePostingError('posting target is gone')
        return target

    def post(self, fn: ta.Callable[[], T]) -> IoPipelinePost[T]:
        post: IoPipelinePost[T] = IoPipelinePost(fn)
        self._target().accept_post(post)
        return post

    def post_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            fn: ta.Callable[[IoPipelineHandlerContext], T],
    ) -> IoPipelinePost[T]:
        if (pipeline := self._pipeline) is None:
            raise ClosedIoPipelinePostingError('pipeline is gone')
        check.is_(handler_ref.pipeline, pipeline)
        check.state(not handler_ref.invalidated)

        post: IoPipelinePost[T] = IoPipelinePost(fn, _ctx_ref=weakref.ref(handler_ref._context))  # noqa
        self._target().accept_post(post)
        return post


########################################
# ../../../../omcore/io/pipelines/sched/types.py


##


class IoPipelineScheduling(Abstract):
    class Handle(Abstract):
        @abc.abstractmethod
        def cancel(self) -> None:
            """Idempotently cancel the callback if it has not begun running."""

            raise NotImplementedError

    @abc.abstractmethod
    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> Handle:
        """
        Schedule a callback owned by an active handler ref.

        The callback must not run after its owning handler ref is invalidated.
        Callers that need the owning context should use schedule_context instead of closing over it.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> Handle:
        """
        Schedule a callback receiving its owning handler context.

        Unlike a closure over the context, this lets scheduler implementations retain it non-owningly and avoids a
        reference cycle when the handler retains the returned handle. The callback should likewise avoid closing over
        the handler, context, or handler ref.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        """Cancel callbacks owned by an exact handler ref, or all callbacks when omitted."""

        raise NotImplementedError


########################################
# ../../../../omcore/io/streambufs/base.py


##


class BaseByteStreamBufferLike(ByteStreamBufferLike, Abstract):
    def _norm_slice(self, start: int, end: ta.Optional[int]) -> ta.Tuple[int, int]:
        if start == 0 and end is None:
            # The overwhelmingly common case - skip slice.indices().
            return 0, len(self)
        s, e, _ = slice(start, end, 1).indices(len(self))
        return (s, s) if e < s else (s, e)


########################################
# ../../../../omcore/io/streambufs/utils.py


##


class ByteStreamBuffers(NamespaceClass):
    _CAN_CONVERT_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        *BYTES_LIKE_TYPES,
        ByteStreamBufferLike,
    )

    #

    @classmethod
    def can_bytes(cls, obj: ta.Any, /) -> bool:
        return type(obj) in (cts := cls._CAN_CONVERT_TYPES) or isinstance(obj, cts)

    #

    @classmethod
    @ta.overload
    def to_bytes(
            cls,
            obj: ta.Any,
            /, *,
            strict: ta.Literal[True],
            or_none: ta.Literal[True],
    ) -> ta.Optional[bytes]:
        ...

    @classmethod
    @ta.overload
    def to_bytes(
            cls,
            obj: ta.Any,
            /, *,
            strict: ta.Literal[True],
            or_none: ta.Literal[False] = False,
    ) -> bytes:
        ...

    @classmethod
    @ta.overload
    def to_bytes(
            cls,
            obj: ta.Any,
            /, *,
            strict: ta.Literal[False] = False,
            or_none: ta.Literal[True],
    ) -> ta.Optional[Bytes]:
        ...

    @classmethod
    @ta.overload
    def to_bytes(
            cls,
            obj: ta.Any,
            /, *,
            strict: ta.Literal[False] = False,
            or_none: ta.Literal[False] = False,
    ) -> Bytes:
        ...

    @classmethod
    def to_bytes(
            cls,
            obj,
            /, *,
            strict=False,
            or_none=False,
    ):
        """
        Returns a non-shared version of the given object. If a possibly shared memoryview is acceptable, use
        `iter_segments`.
        """

        if strict:
            if (ot := type(obj)) is bytes or isinstance(obj, bytes):
                return obj

            elif ot is bytearray:
                return bytes(obj)

            elif isinstance(obj, memoryview):
                return memoryview_to_bytes_strict(obj)

        else:
            if (ot := type(obj)) is bytes or ot is bytearray or isinstance(obj, BYTES_TYPES):
                return obj

            elif isinstance(obj, memoryview):
                return memoryview_to_bytes(obj)

        if isinstance(obj, ByteStreamBufferView):
            return obj.tobytes()

        elif isinstance(obj, ByteStreamBufferLike):
            return b''.join(bytes(mv) for mv in obj.segments())

        elif or_none:
            return None

        else:
            raise TypeError(obj)

    #

    @classmethod
    @ta.overload
    def bytes_len(cls, obj: ta.Any, or_none: ta.Literal[True], /) -> ta.Optional[int]: ...

    @classmethod
    @ta.overload
    def bytes_len(cls, obj: ta.Any, or_none: ta.Literal[False] = False, /) -> int: ...

    @classmethod
    def bytes_len(cls, obj, or_none=False):
        if cls.can_bytes(obj):
            return len(obj)

        elif or_none:
            return None

        else:
            raise TypeError(obj)

    #

    @staticmethod
    def iter_segments(obj: ta.Any, /) -> ta.Iterator[memoryview]:
        if (ot := type(obj)) is memoryview:
            yield obj
        elif ot is bytes or ot is bytearray:
            yield memoryview(obj)

        elif isinstance(obj, memoryview):
            yield obj
        elif isinstance(obj, (bytes, bytearray)):
            yield memoryview(obj)

        elif isinstance(obj, ByteStreamBufferLike):
            yield from obj.segments()

        else:
            raise TypeError(obj)

    #

    @staticmethod
    def split(buf: ByteStreamBuffer, sep: bytes, /, *, final: bool = False) -> ta.List[ByteStreamBufferView]:
        """
        Split off a keep-ends frame (separator included) for each occurrence of `sep`, consuming them from `buf` and
        leaving any separator-less remainder buffered. If `final` is true, the remainder is appended as a last frame.
        """

        out: ta.List[ByteStreamBufferView] = []
        while (i := buf.find(sep)) >= 0:
            out.append(buf.split_to(i + len(sep)))
        if final and len(buf):
            out.append(buf.split_to(len(buf)))
        return out


########################################
# ../../../../omcore/logs/contexts.py


##


class LoggingContext(Abstract):
    @abc.abstractmethod
    def get_info(self, ty: ta.Type[LoggingContextInfoT]) -> ta.Optional[LoggingContextInfoT]:
        raise NotImplementedError

    @ta.final
    def __getitem__(self, ty: ta.Type[LoggingContextInfoT]) -> ta.Optional[LoggingContextInfoT]:
        return self.get_info(ty)

    @ta.final
    def must_get_info(self, ty: ta.Type[LoggingContextInfoT]) -> LoggingContextInfoT:
        if (info := self.get_info(ty)) is None:
            raise TypeError(f'LoggingContextInfo absent: {ty}')
        return info


@ta.final
class SimpleLoggingContext(LoggingContext):
    def __init__(self, *infos: LoggingContextInfo) -> None:
        self._infos: ta.Dict[ta.Type[LoggingContextInfo], LoggingContextInfo] = {type(i): i for i in infos}

    def get_info(self, ty: ta.Type[LoggingContextInfoT]) -> ta.Optional[LoggingContextInfoT]:
        return self._infos.get(ty)


##


class CaptureLoggingContext(LoggingContext, Abstract):
    @abc.abstractmethod
    def set_basic(
            self,
            name: str,

            msg: ta.Union[str, tuple, LoggingMsgFn],
            args: tuple,
    ) -> 'CaptureLoggingContext':
        raise NotImplementedError

    #

    class AlreadyCapturedError(Exception):
        pass

    class NotCapturedError(Exception):
        pass

    @abc.abstractmethod
    def capture(self) -> None:
        """Must be cooperatively called only from the expected locations."""

        raise NotImplementedError


@ta.final
class CaptureLoggingContextImpl(CaptureLoggingContext):
    @ta.final
    class NOT_SET:  # noqa
        def __new__(cls, *args, **kwargs):  # noqa
            raise TypeError

    #

    def __init__(
            self,
            level: LogLevel,
            *,
            time_ns: ta.Optional[int] = None,

            exc_info: LoggingExcInfoArg = False,

            caller: ta.Union[LoggingContextInfos.Caller, ta.Type[NOT_SET], None] = NOT_SET,
            stack_offset: int = 0,
            stack_info: bool = False,
    ) -> None:
        if time_ns is None:
            time_ns = time.time_ns()

        # Done early to not trample on sys.exc_info()
        exc = LoggingContextInfos.Exc.build(exc_info)

        self._infos: ta.Dict[ta.Type[LoggingContextInfo], LoggingContextInfo] = {}
        self._set_info(
            LoggingContextInfos.Level.build(level),
            exc,
            LoggingContextInfos.Time.build(time_ns),
        )

        if caller is not CaptureLoggingContextImpl.NOT_SET:
            self._infos[LoggingContextInfos.Caller] = caller
        else:
            self._stack_offset = stack_offset
            self._stack_info = stack_info

    def _set_info(self, *infos: ta.Optional[LoggingContextInfo]) -> 'CaptureLoggingContextImpl':
        for info in infos:
            if info is not None:
                self._infos[type(info)] = info
        return self

    def get_infos(self) -> ta.Mapping[ta.Type[LoggingContextInfo], LoggingContextInfo]:
        return self._infos

    def get_info(self, ty: ta.Type[LoggingContextInfoT]) -> ta.Optional[LoggingContextInfoT]:
        return self._infos.get(ty)

    ##

    def set_basic(
            self,
            name: str,

            msg: ta.Union[str, tuple, LoggingMsgFn],
            args: tuple,
    ) -> 'CaptureLoggingContextImpl':
        return self._set_info(
            LoggingContextInfos.Name(name),
            LoggingContextInfos.Msg.build(msg, *args),
        )

    ##

    _stack_offset: int
    _stack_info: bool

    def inc_stack_offset(self, ofs: int = 1) -> 'CaptureLoggingContextImpl':
        if hasattr(self, '_stack_offset'):
            self._stack_offset += ofs
        return self

    _has_captured: bool = False

    def capture(self) -> None:
        if self._has_captured:
            raise CaptureLoggingContextImpl.AlreadyCapturedError
        self._has_captured = True

        if LoggingContextInfos.Caller not in self._infos:
            self._set_info(LoggingContextInfos.Caller.build(
                self._stack_offset + 1,
                stack_info=self._stack_info,
            ))

        if (caller := self[LoggingContextInfos.Caller]) is not None:
            self._set_info(LoggingContextInfos.SourceFile.build(
                caller.file_path,
            ))

        self._set_info(
            LoggingContextInfos.Thread.build(),
            LoggingContextInfos.Process.build(),
            LoggingContextInfos.Multiprocessing.build(),
            LoggingContextInfos.AsyncioTask.build(),
        )


########################################
# ../../../../omcore/logs/utils.py


##


def exception_logging(log, exc_cls=Exception):  # noqa
    def outer(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except exc_cls as e:  # noqa
                log.exception('Error in %r', fn)
                raise

        return inner

    return outer


def async_exception_logging(alog, exc_cls=Exception):  # noqa
    def outer(fn):
        @functools.wraps(fn)
        async def inner(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except exc_cls as e:  # noqa
                await alog.exception('Error in %r', fn)
                raise

        return inner

    return outer


##


class LogTimingContext:
    DEFAULT_LOG: ta.ClassVar[ta.Optional[LoggerLike]] = None

    class _NOT_SPECIFIED:  # noqa
        def __new__(cls, *args, **kwargs):  # noqa
            raise TypeError

    def __init__(
            self,
            description: str,
            *,
            log: ta.Union[LoggerLike, ta.Type[_NOT_SPECIFIED], None] = _NOT_SPECIFIED,  # noqa
            level: int = logging.DEBUG,
    ) -> None:
        super().__init__()

        self._description = description
        if log is self._NOT_SPECIFIED:
            log = self.DEFAULT_LOG  # noqa
        self._log: ta.Optional[LoggerLike] = log  # type: ignore
        self._level = level

    def set_description(self, description: str) -> 'LogTimingContext':
        self._description = description
        return self

    _begin_time: float
    _end_time: float

    def __enter__(self) -> 'LogTimingContext':
        self._begin_time = time.time()

        if self._log is not None:
            self._log.log(self._level, f'Begin : {self._description}')  # noqa

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = time.time()

        if self._log is not None:
            self._log.log(
                self._level,
                f'End : {self._description} - {self._end_time - self._begin_time:0.2f} s elapsed',
            )


log_timing_context = LogTimingContext


########################################
# ../../../../omcore/rpc/errors.py
"""
The rpc error vocabulary.

Local errors are raised to callers. `RpcRemoteErrorData` is the wire shape of an error: a stable string code, the
remote exception type's name, a message, and optionally a traceback, which the receiving side raises as an
`RpcRemoteError`. Codes are plain strings so that both ends can be any mixture of versions and dialects; the ones the
toolbox itself emits are collected in `RpcErrorCodes`.
"""


##


class RpcError(Exception):
    """Base class for all rpc errors."""


class RpcProtocolError(RpcError):
    """
    The peer violated the protocol in a way the connection cannot recover from: framing desync, malformed envelopes.
    """  # noqa


class RpcConnectionClosedError(RpcError, ConnectionError):
    """The connection closed, or was already closed, before an operation could complete."""


class RpcTimeoutError(RpcError, TimeoutError):
    """An operation did not complete within its configured timeout."""


class RpcMessageTooLargeError(RpcError, ValueError):
    """
    A message exceeded the configured maximum frame size. Sending one fails just that message, like any other value
    which cannot be encoded; receiving one is fatal to the connection, as the stream cannot be resynchronized past it.
    """


class RpcTooManyRequestsError(RpcError):
    """The local limit on concurrently pending outbound requests was reached."""


class RpcCancelledError(RpcError):
    """An in-flight request was cancelled: by the peer, by a timeout, or by the connection closing."""


class RpcMethodNotFoundError(RpcError):
    """Raised by a handler for a method it does not implement; answered on the wire as `method_not_found`."""

    def __init__(self, method: str) -> None:
        super().__init__(f'RPC method not found: {method!r}')

        self.method = method


class RpcUnexpectedMessageError(RpcProtocolError):
    """A message of an unexpected kind was received, such as a response to a request this side never issued."""


class RpcHandlerError(RpcError):
    """
    Raised by a handler to answer the request with exactly this error data - a code of its own, say, or an answer kept
    from an earlier attempt. Any other exception is answered as code `remote`.
    """

    def __init__(self, data: 'RpcRemoteErrorData') -> None:
        super().__init__(data.message)

        self.data = data


##


class RpcErrorCodes(NamespaceClass):
    """The error codes the toolbox itself emits. Handlers are free to use any other string."""

    # A handler raised an ordinary exception; `type` names it.
    REMOTE = 'remote'

    # The handler was cancelled before producing a result.
    CANCELLED = 'cancelled'

    METHOD_NOT_FOUND = 'method_not_found'

    # The result could not be encoded for the wire.
    RESULT_ENCODING = 'result_encoding'

    # The receiving session is at its in-flight limit.
    BUSY = 'busy'

    # The receiving session is closing.
    SHUTTING_DOWN = 'shutting_down'

    # Handling exceeded the receiving session's handling timeout.
    HANDLING_TIMEOUT = 'handling_timeout'

    # The result exceeded the frame limit.
    RESULT_TOO_LARGE = 'result_too_large'


##


@dc.dataclass(frozen=True)
class RpcRemoteErrorData:
    """The wire shape of an error. `remote_type` is spelled `type` on the wire."""

    code: str
    remote_type: str = dc.field(metadata={OBJ_MARSHALER_FIELD_KEY: 'type'})
    message: str
    traceback: ta.Optional[str] = None


class RpcRemoteError(RpcError):
    """The peer answered a request with an error."""

    def __init__(self, data: RpcRemoteErrorData) -> None:
        super().__init__(data.message)

        self.data = data

    def __str__(self) -> str:
        d = self.data
        return f'[{d.code}] {d.remote_type}: {d.message}'

    @property
    def code(self) -> str:
        return self.data.code

    @property
    def remote_type(self) -> str:
        return self.data.remote_type

    @property
    def remote_message(self) -> str:
        return self.data.message

    @property
    def remote_traceback(self) -> ta.Optional[str]:
        return self.data.traceback


class RpcRemoteCancelledError(RpcRemoteError):
    """The peer reported that handling of the request was cancelled."""


class RpcRemoteMethodNotFoundError(RpcRemoteError):
    """The peer does not implement the method."""


class RpcRemoteShuttingDownError(RpcRemoteError, RpcConnectionClosedError):
    """
    The peer answered that it is closing and will not handle the request. Also an `RpcConnectionClosedError`, since that
    is what it means for the caller: code which handles a lost connection handles this too.
    """


def rpc_exception_type_name(obj: ta.Union[BaseException, ta.Type[BaseException]]) -> str:
    """The qualified name error data carries for an exception's type, such as `builtins.FileNotFoundError`."""

    cls = obj if isinstance(obj, type) else type(obj)
    return f'{cls.__module__}.{cls.__qualname__}'


def rpc_remote_error_for_data(data: RpcRemoteErrorData) -> RpcRemoteError:
    """Builds the local exception a remote error is raised as, with subclasses for the codes callers tend to catch."""

    if data.code == RpcErrorCodes.CANCELLED:
        return RpcRemoteCancelledError(data)
    if data.code == RpcErrorCodes.METHOD_NOT_FOUND:
        return RpcRemoteMethodNotFoundError(data)
    if data.code == RpcErrorCodes.SHUTTING_DOWN:
        return RpcRemoteShuttingDownError(data)
    return RpcRemoteError(data)


########################################
# ../../environment/local.py


##


def environment_resolve_cwd(path: ta.Optional[str]) -> str:
    """The absolute, symlink-resolved form of a working directory, which must exist and be one."""

    cwd = os.path.abspath(os.path.realpath(path if path is not None else os.getcwd()))

    if not os.path.exists(cwd):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), cwd)
    if not os.path.isdir(cwd):
        raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), cwd)

    return cwd


def environment_detect_container() -> ta.Optional[str]:
    """The container runtime this process is running under, as far as the usual marker files say. Best effort."""

    if os.path.exists('/.dockerenv'):
        return 'docker'
    if os.path.exists('/run/.containerenv'):
        return 'podman'
    return None


class LocalEnvironmentOps(EnvironmentOps):
    """The environment this process is in. On the host that is the user's own machine; in the remote agent, its own."""

    @staticmethod
    def _user() -> EnvironmentInfo.User:
        pw_name: ta.Optional[str] = None
        pw_dir: ta.Optional[str] = None
        pw_shell: ta.Optional[str] = None
        try:
            import pwd  # noqa: PLC0415
        except ImportError:  # pragma: no cover
            pass
        else:
            try:
                pw = pwd.getpwuid(os.getuid())
            except KeyError:
                pass
            else:
                pw_name, pw_dir, pw_shell = pw.pw_name, pw.pw_dir, pw.pw_shell

        # The account is authoritative for who; the session's own variables for where it lives and what it runs, as
        # they are what a shell started here would see.
        name = pw_name or os.environ.get('USER') or os.environ.get('LOGNAME') or None
        home = os.environ.get('HOME') or pw_dir or None
        shell = os.environ.get('SHELL') or pw_shell or None

        return EnvironmentInfo.User(
            name=name,
            home=home,
            shell=shell,
        )

    async def inspect_environment(
            self,
            *,
            cwd: ta.Optional[str] = None,
    ) -> EnvironmentInfo:
        user = self._user()

        return EnvironmentInfo(
            cwd=environment_resolve_cwd(cwd),

            system=platform.system(),
            release=platform.release(),
            machine=platform.machine(),

            hostname=socket.gethostname(),

            user=user,

            container=environment_detect_container(),
        )


########################################
# ../../fs/local.py


##


class LocalFsOps(FsOps):
    @staticmethod
    def _entry(path: str, *, dangling_ok: bool = False) -> FsEntry:
        lst = os.lstat(path)
        if stat_.S_ISLNK(lst.st_mode):
            try:
                st = os.stat(path)
            except OSError:
                if not dangling_ok:
                    raise
                st = lst
        else:
            st = lst

        birthtime_ns: ta.Optional[int] = getattr(st, 'st_birthtime_ns', None)
        if birthtime_ns is None and (birthtime := getattr(st, 'st_birthtime', None)) is not None:
            birthtime_ns = int(birthtime * 1_000_000_000)

        return FsEntry(
            path=path,
            resolved_path=fs_resolve_path(path),

            is_dir=stat_.S_ISDIR(st.st_mode),
            is_file=stat_.S_ISREG(st.st_mode),
            is_symlink=stat_.S_ISLNK(lst.st_mode),

            mode=st.st_mode,
            ino=st.st_ino,
            dev=st.st_dev,
            nlink=st.st_nlink,
            uid=st.st_uid,
            gid=st.st_gid,
            size=st.st_size,

            atime_ns=st.st_atime_ns,
            mtime_ns=st.st_mtime_ns,
            ctime_ns=st.st_ctime_ns,

            blksize=st.st_blksize,
            blocks=st.st_blocks,
            rdev=st.st_rdev,

            flags=getattr(st, 'st_flags', None),
            gen=getattr(st, 'st_gen', None),
            birthtime_ns=birthtime_ns,
        )

    async def resolve_path(self, path: str) -> str:
        return fs_resolve_path(path)

    async def stat(self, path: str) -> FsEntry:
        return self._entry(path)

    async def read_file(self, path: str) -> FsFile:
        with open(path, 'rb') as f:  # noqa
            data = f.read()
        return FsFile(
            data=data,
            digest=fs_file_digest(data),
        )

    async def write_file(
            self,
            path: str,
            content: BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> FsWriteResult:
        return FsWriteResult(created=fs_write_file(
            path,
            content,
            overwrite=overwrite,
            expected_digest=expected_digest,
        ))

    async def list_dir(self, path: str) -> ta.Sequence[FsEntry]:
        entries: ta.List[FsEntry] = []
        with os.scandir(path) as it:
            for e in it:
                try:
                    entries.append(self._entry(e.path, dangling_ok=True))
                except FileNotFoundError:
                    # Gone since the directory was read.
                    continue
        return entries

    async def glob(
            self,
            pattern: str,
            *,
            max_results: ta.Optional[int] = None,
    ) -> FsGlobResult:
        paths, has_more = fs_glob_paths(
            pattern,
            max_results=max_results,
        )

        entries: ta.List[FsEntry] = []
        for p in paths:
            try:
                entries.append(self._entry(p, dangling_ok=True))
            except FileNotFoundError:
                # Gone since the glob saw it.
                continue

        return FsGlobResult(
            entries=entries,
            has_more=has_more,
        )


########################################
# ../../../../omcore/asyncs/asynclite/asyncio/events.py


##


class AsyncioAsyncliteEvent(AsyncliteEvent, AsyncioAsyncliteObject):
    def __init__(self, u: asyncio.Event) -> None:
        super().__init__()

        self._u = u

    def set(self) -> None:
        return self._u.set()

    def is_set(self) -> bool:
        return self._u.is_set()

    async def wait(self, *, timeout: ta.Optional[float] = None) -> None:
        await self._wait_for(self._u.wait(), timeout=timeout)


class AsyncioAsyncliteEvents(AsyncliteEvents, AsyncioAsyncliteApi):
    def make_event(self) -> AsyncliteEvent:
        return AsyncioAsyncliteEvent(asyncio.Event())


########################################
# ../../../../omcore/asyncs/asynclite/eventpromises.py


##


class EventAsynclitePromise(AsynclitePromise[T]):
    """
    Generic implementation backed by any AsyncliteEvent - waiting inherits the event's backend semantics, including
    which contexts may legally wait on it.

    Once completed the promise sheds its internal synchronization machinery: the set-once lock and the backing event
    are released, leaving only the outcome. This makes long-lived done promises (such as once-per-key caches) cost
    little more than the value itself.

    Maintainer invariants:
     - The outcome slots are written strictly before `_has_out`, which is the unlocked publication point - `_has_out`
       must always be the last write under the lock.
     - `_ev` and `_mtx` are None once done, and are nulled only after the outcome is published (and, for `_ev`, after
       it is set). All paths must operate on locally-captured refs, never re-read the attributes.
    """

    def __init__(self, ev: AsyncliteEvent) -> None:
        super().__init__()

        self._ev: ta.Optional[AsyncliteEvent] = ev
        self._mtx: ta.Optional[threading.Lock] = threading.Lock()
        self._has_out = False
        self._val: ta.Optional[T] = None
        self._exc: ta.Optional[BaseException] = None

    def is_done(self) -> bool:
        return self._has_out

    def _result(self) -> T:
        # Only valid once _has_out is set - _val / _exc are written (under _mtx) strictly before it.
        if (e := self._exc) is not None:
            raise e
        return ta.cast(T, self._val)

    def poll(self) -> Maybe[T]:
        if not self._has_out:
            return Maybe.nothing()
        return Maybe.just(self._result())

    def _set(self, val: ta.Optional[T], exc: ta.Optional[BaseException]) -> None:
        if (mtx := self._mtx) is None:
            raise AsynclitePromiseAlreadySetError(self)

        with mtx:
            if self._has_out:
                raise AsynclitePromiseAlreadySetError(self)
            self._val = val
            self._exc = exc
            self._has_out = True  # must be the last write - the unlocked publication point for _val / _exc

        if (ev := self._ev) is not None:  # always the case for the sole arbitrated completer
            ev.set()

        self._ev = None
        self._mtx = None

    def set_value(self, v: T) -> None:
        self._set(v, None)

    def set_error(self, e: BaseException) -> None:
        if not isinstance(e, BaseException):
            raise TypeError(e)
        self._set(None, e)

    async def wait(self, *, timeout: ta.Optional[float] = None) -> T:
        # The local ref is grabbed before the done check: the completer nulls _ev only after publishing the outcome,
        # so observing a live event and a not-done flag guarantees the event will still be set.
        ev = self._ev
        if ev is not None and not self._has_out:
            try:
                await ev.wait(timeout=timeout)
            except TimeoutError as te:
                # A timeout racing completion is completion.
                if not self._has_out:
                    raise AsynclitePromiseWaitTimeoutError(self) from te

        return self._result()


class EventAsynclitePromises(
    AsyncliteEvents,
    AsynclitePromises,
    AsyncliteApi,
    Abstract,
):
    def make_promise(self) -> AsynclitePromise:
        return EventAsynclitePromise(self.make_event())


########################################
# ../../../../omcore/io/pipelines/flow/stub.py


##


@ta.final
class StubIoPipelineFlowService(IoPipelineFlow, IoPipelineService):
    def __init__(self, *, auto_read: bool = True) -> None:
        super().__init__()

        self._auto_read = auto_read

    def is_auto_read(self) -> bool:
        return self._auto_read


########################################
# ../../../../omcore/io/pipelines/sched/heap.py


##


@ta.final
class HeapIoPipelineSchedulingService(IoPipelineScheduling, IoPipelineService):
    """
    Tickless heap scheduling for select-, poll-, and generator-style pipeline drivers.

    `next_deadline()` returns an absolute deadline in the configured clock's time base, while `next_delay()` returns
    the corresponding relative delay. The default clock is `time.monotonic()`; deterministic drivers may inject one.
    Drivers call `run_due()` after waiting. Callbacks execute inside their pipeline and are automatically cancelled
    when their owning handler is removed or the pipeline is destroyed.

    A driver which waits on something other than this scheduler's delay - an asyncio queue, say - may supply
    `on_earliest_change`, called whenever a newly scheduled callback becomes the earliest, to re-arm whatever wakes it.
    Cancellations are not reported: a wake at a since cancelled deadline runs nothing and is harmless.
    """

    def __init__(
            self,
            clock: ta.Callable[[], float] = time.monotonic,
            *,
            on_earliest_change: ta.Optional[ta.Callable[[], None]] = None,
    ) -> None:
        super().__init__()

        self._clock = clock
        self._on_earliest_change = on_earliest_change

        self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None

        self._seq = 0
        self._pending: ta.List[ta.Tuple[float, int, HeapIoPipelineSchedulingService._Handle]] = []
        self._live: ta.Set[HeapIoPipelineSchedulingService._Handle] = set()

    @property
    def _pipeline(self) -> ta.Optional[IoPipeline]:
        if self.__pipeline_ref is None:
            return None
        return self.__pipeline_ref()

    @_pipeline.setter
    def _pipeline(self, pipeline: ta.Optional[IoPipeline]) -> None:
        self.__pipeline_ref = None if pipeline is None else weakref.ref(pipeline)

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'added':
            check.none(self._pipeline)
            self._pipeline = pipeline

        elif kind == 'removed':
            if self._pipeline is None:
                return

            check.is_(pipeline, self._pipeline)
            self.cancel_all()
            self._pipeline = None

    def handler_update(self, handler_ref: IoPipelineHandlerRef, kind: IoPipelineHandlerUpdate) -> None:
        if kind == 'removing':
            self.cancel_all(handler_ref)

    def _clear_cancelled(self) -> None:
        while self._pending and self._pending[0][2]._cancelled:  # noqa
            heapq.heappop(self._pending)

    def next_deadline(self) -> ta.Optional[float]:
        """Return the earliest absolute `time.monotonic()` deadline, or none when no callback is pending."""

        self._clear_cancelled()
        if not self._pending:
            return None
        return self._pending[0][0]

    def next_delay(self) -> ta.Optional[float]:
        """Return the non-negative delay until the earliest callback, or none when no callback is pending."""

        if (deadline := self.next_deadline()) is None:
            return None
        return max(0., deadline - self._clock())

    def run_due(self) -> int:
        """Run the callbacks due at entry and return the number that ran."""

        self._clear_cancelled()

        now = self._clock()
        due: ta.List[HeapIoPipelineSchedulingService._Handle] = []

        while self._pending and self._pending[0][0] <= now:
            _, _, handle = heapq.heappop(self._pending)
            if not handle._cancelled:  # noqa
                due.append(handle)
            self._clear_cancelled()

        ran = 0
        for i, handle in enumerate(due):
            if handle._cancelled:  # noqa
                continue

            handle._done = True  # noqa
            self._live.remove(handle)

            try:
                with check.not_none(self._pipeline).enter():
                    handle._run()  # noqa

            except BaseException:
                for remaining_handle in due[i + 1:]:
                    if not remaining_handle._cancelled:  # noqa
                        heapq.heappush(self._pending, (  # noqa
                            remaining_handle._deadline,  # noqa
                            remaining_handle._seq,  # noqa
                            remaining_handle,
                        ))
                raise

            ran += 1

        return ran

    @ta.final
    class _Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                sched: 'HeapIoPipelineSchedulingService',
                handler_ref: IoPipelineHandlerRef,
                fn: ta.Callable[..., None],
                with_context: bool,
                deadline: float,
                seq: int,
        ) -> None:
            self.__sched_ref = weakref.ref(sched)
            self._deadline = deadline
            self._seq = seq
            self.__handler_context_ref = weakref.ref(handler_ref._context)  # noqa
            self._fn: ta.Optional[ta.Callable[..., None]] = fn
            self._with_context = with_context

            self._cancelled = False
            self._done = False

        @property
        def _handler_context(self) -> IoPipelineHandlerContext:
            return check.not_none(self.__handler_context_ref())

        def _run(self) -> None:
            fn = check.not_none(self._fn)
            self._fn = None
            if self._with_context:
                fn(self._handler_context)
            else:
                fn()

        def cancel(self) -> None:
            if self._cancelled or self._done:
                return

            # A cancelled handle may linger in the heap until it surfaces, so release whatever its callback holds now.
            self._cancelled = True
            self._fn = None
            if (sched := self.__sched_ref()) is not None:
                sched._live.discard(self)  # noqa

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

        handle = self._Handle(
            self,
            handler_ref,
            fn,
            with_context,
            self._clock() + max(0., delay_s),
            self._seq,
        )
        self._seq += 1
        heapq.heappush(self._pending, (handle._deadline, handle._seq, handle))  # noqa
        self._live.add(handle)

        if (cb := self._on_earliest_change) is not None and self._pending[0][2] is handle:
            cb()

        return handle

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
        for handle in tuple(self._live):
            if handler_ref is None or handle._handler_context is handler_ref._context:  # noqa
                handle.cancel()

        self._pending = [entry for entry in self._pending if not entry[2]._cancelled]  # noqa
        heapq.heapify(self._pending)


########################################
# ../../../../omcore/io/pipelines/sched/timeouts.py


##


class IoPipelineIdleState(enum.Enum):
    READ_IDLE = 'read_idle'
    WRITE_IDLE = 'write_idle'
    ALL_IDLE = 'all_idle'


@ta.final
@dc.dataclass(frozen=True)
class IdleStateIoPipelineEvent(
    IoPipelineMessages.MayPropagate,
    IoPipelineMessages.NeverOutbound,
):
    """Signals that a configured pipeline inactivity interval elapsed."""

    state: IoPipelineIdleState
    first: bool


##


class IdleStateIoPipelineHandler(IoPipelineHandler):
    """
    Emits inbound idle-state events for configured read, write, and combined inactivity intervals.

    Each configured state uses an exact, independently reset scheduler deadline. Unconfigured states schedule nothing;
    when all intervals are omitted, this handler does not require an IoPipelineScheduling service and remains tickless.

    Read and write activity include ordinary messages crossing this handler in their respective directions. A
    successfully completed FlushOutput or ShutdownOutput additionally records write activity at the transport boundary;
    emitting the fence itself is not activity. Other flow-control, lifecycle, error, and idle-event messages are not
    activity. FinalInput ends read idleness and ShutdownOutput ends write idleness, each half-close leaving the other
    direction (and the combined state) running.
    """

    _STATES: ta.ClassVar[ta.Tuple[IoPipelineIdleState, ...]] = (
        IoPipelineIdleState.READ_IDLE,
        IoPipelineIdleState.WRITE_IDLE,
        IoPipelineIdleState.ALL_IDLE,
    )

    _WRITE_ACTIVITY_STATES: ta.ClassVar[ta.Tuple[IoPipelineIdleState, ...]] = (
        IoPipelineIdleState.WRITE_IDLE,
        IoPipelineIdleState.ALL_IDLE,
    )

    def __init__(
            self,
            read_idle_timeout_s: ta.Optional[float] = None,
            write_idle_timeout_s: ta.Optional[float] = None,
            all_idle_timeout_s: ta.Optional[float] = None,
    ) -> None:
        super().__init__()

        self._timeouts: ta.Dict[IoPipelineIdleState, ta.Optional[float]] = {
            IoPipelineIdleState.READ_IDLE: read_idle_timeout_s,
            IoPipelineIdleState.WRITE_IDLE: write_idle_timeout_s,
            IoPipelineIdleState.ALL_IDLE: all_idle_timeout_s,
        }
        for timeout_s in self._timeouts.values():
            if timeout_s is not None and (not math.isfinite(timeout_s) or timeout_s <= 0.):
                raise ValueError(timeout_s)

        self._handles: ta.Dict[IoPipelineIdleState, IoPipelineScheduling.Handle] = {}
        self._first: ta.Dict[IoPipelineIdleState, bool] = {state: True for state in self._STATES}

        self._started = False
        self._read_open = False
        self._write_open = False

    #

    def _is_active(self, state: IoPipelineIdleState) -> bool:
        return (
            self._started and
            (state is not IoPipelineIdleState.READ_IDLE or self._read_open) and
            (state is not IoPipelineIdleState.WRITE_IDLE or self._write_open)
        )

    def _cancel(self, state: ta.Optional[IoPipelineIdleState] = None) -> None:
        if state is not None:
            if (handle := self._handles.pop(state, None)) is not None:
                handle.cancel()
            return

        handles = tuple(self._handles.values())
        self._handles.clear()
        for handle in handles:
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext, state: IoPipelineIdleState) -> None:
        self._cancel(state)

        if not self._is_active(state) or (timeout_s := self._timeouts[state]) is None:
            return

        self._handles[state] = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, IdleStateIoPipelineHandler)._on_idle(ctx2, state),  # noqa
        )

    def _record_activity(
            self,
            ctx: IoPipelineHandlerContext,
            states: ta.Iterable[IoPipelineIdleState],
    ) -> None:
        for state in states:
            if self._timeouts[state] is None or not self._is_active(state):
                continue

            self._first[state] = True
            self._arm(ctx, state)

    @staticmethod
    def _on_flush_output_done(
            context_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            msg: IoPipelineMessages.Completable[None],
    ) -> None:
        if not msg.is_succeeded() or (ctx := context_ref()) is None or ctx.invalidated:
            return

        handler = check.isinstance(ctx.handler, IdleStateIoPipelineHandler)
        handler._record_activity(ctx, handler._WRITE_ACTIVITY_STATES)  # noqa

    def _track_flush_output(
            self,
            ctx: IoPipelineHandlerContext,
            msg: IoPipelineMessages.Completable[None],
    ) -> None:
        if not self._started or not any(self._timeouts[state] is not None for state in self._WRITE_ACTIVITY_STATES):
            return

        msg.add_listener(functools.partial(self._on_flush_output_done, weakref.ref(ctx)))

    def _on_idle(self, ctx: IoPipelineHandlerContext, state: IoPipelineIdleState) -> None:
        self._handles.pop(state, None)
        if not self._is_active(state):
            return

        first = self._first[state]
        self._first[state] = False
        ctx.feed_in(IdleStateIoPipelineEvent(state, first))

        # Delivering the event can synchronously cause activity, closure, or handler removal. Only re-arm if none of
        # those paths already replaced this state's deadline.
        if state not in self._handles:
            self._arm(ctx, state)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if any(timeout_s is not None for timeout_s in self._timeouts.values()):
                check.not_none(ctx.services.find(IoPipelineScheduling))

            self._cancel()
            self._first = {state: True for state in self._STATES}
            self._started = False
            self._read_open = False
            self._write_open = False

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._started = False
            self._read_open = False
            self._write_open = False
            self._cancel()

    #

    _NON_READ_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.Error,
        IdleStateIoPipelineEvent,
        IoPipelineFlowMessages.FlushInput,
        IoPipelineFlowMessages.ReadyForOutput,
        IoPipelineFlowMessages.PauseOutput,
    )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._cancel()
            self._first = {state: True for state in self._STATES}
            self._started = True
            self._read_open = True
            self._write_open = True
            for state in self._STATES:
                self._arm(ctx, state)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._read_open = False
            self._cancel(IoPipelineIdleState.READ_IDLE)

        elif not isinstance(msg, self._NON_READ_ACTIVITY_TYPES):
            self._record_activity(ctx, (
                IoPipelineIdleState.READ_IDLE,
                IoPipelineIdleState.ALL_IDLE,
            ))

        ctx.feed_in(msg)

    _NON_WRITE_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineFlowMessages.FlushOutput,
        IoPipelineFlowMessages.ReadyForInput,
    )

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._started = False
            self._read_open = False
            self._write_open = False
            self._cancel()

        elif isinstance(msg, IoPipelineMessages.ShutdownOutput):
            self._write_open = False
            self._cancel(IoPipelineIdleState.WRITE_IDLE)
            self._track_flush_output(ctx, msg)

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            self._track_flush_output(ctx, msg)

        elif not isinstance(msg, self._NON_WRITE_ACTIVITY_TYPES):
            self._record_activity(ctx, (
                IoPipelineIdleState.WRITE_IDLE,
                IoPipelineIdleState.ALL_IDLE,
            ))

        ctx.feed_out(msg)


##


class ReadTimeoutIoPipelineHandler(IoPipelineHandler):
    """
    Emits an inbound timeout error when no ordinary inbound message is observed within the configured interval.

    Flow-control and error messages do not count as read activity. The handler is placement-sensitive: installed near
    the transport it observes raw input, while above decoders or transforms it observes their output.
    """

    def __init__(self, timeout_s: float) -> None:
        super().__init__()

        if not math.isfinite(timeout_s) or timeout_s <= 0.:
            raise ValueError(timeout_s)
        self._timeout_s = timeout_s

        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._active = False
        self._timed_out = False

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext) -> None:
        self._cancel()
        self._handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            self._timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, ReadTimeoutIoPipelineHandler)._on_timeout(ctx2),  # noqa
        )

    def _on_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Read timed out after {self._timeout_s:g} seconds'),
            direction='inbound',
            handler=ctx.ref,
        ))

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            check.not_none(ctx.services.find(IoPipelineScheduling))

            self._active = False
            self._timed_out = False
            self._cancel()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._active = False
            self._cancel()

    #

    _NON_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.Error,
        IdleStateIoPipelineEvent,
        IoPipelineFlowMessages.FlushInput,
        IoPipelineFlowMessages.ReadyForOutput,
        IoPipelineFlowMessages.PauseOutput,
    )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._active = True
            self._timed_out = False
            self._arm(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._active = False
            self._cancel()

        elif self._active and not self._timed_out and not isinstance(msg, self._NON_ACTIVITY_TYPES):
            self._arm(ctx)

        ctx.feed_in(msg)


##


class WriteTimeoutIoPipelineHandler(IoPipelineHandler):
    """
    Emits one inbound timeout error when an explicit outbound completion fence remains pending for too long.

    FlushOutput, ShutdownOutput, and FinalOutput are ordered fences whose completion means all preceding output crossed
    the transport boundary. Each fence gets an independent deadline, making the oldest outstanding fence the effective
    deadline.
    Ordinary outbound messages do not implicitly flush or schedule anything, so the handler remains tickless whenever
    no fence is outstanding.

    Timeout only reports the stalled write. Error policy remains responsible for deciding whether to close the
    pipeline, and a later fence completion remains valid.
    """

    def __init__(self, timeout_s: float) -> None:
        super().__init__()

        if not math.isfinite(timeout_s) or timeout_s <= 0.:
            raise ValueError(timeout_s)
        self._timeout_s = timeout_s

        self._handles: ta.Dict[int, IoPipelineScheduling.Handle] = {}
        self._active = False
        self._timed_out = False

    #

    def _cancel(self) -> None:
        handles = tuple(self._handles.values())
        self._handles.clear()
        for handle in handles:
            handle.cancel()

    def _on_timeout(self, ctx: IoPipelineHandlerContext, token: int) -> None:
        if self._handles.pop(token, None) is None or not self._active or self._timed_out:
            return

        self._timed_out = True
        self._cancel()
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Write timed out after {self._timeout_s:g} seconds'),
            direction='outbound',
            handler=ctx.ref,
        ))

    @staticmethod
    def _on_fence_done(
            handler_ref: ta.Callable[[], ta.Optional['WriteTimeoutIoPipelineHandler']],
            token: int,
            final_output: bool,
            _msg: IoPipelineMessages.Completable[None],
    ) -> None:
        if (handler := handler_ref()) is None:
            return

        if (handle := handler._handles.pop(token, None)) is not None:  # noqa
            handle.cancel()

        if final_output:
            handler._active = False  # noqa
            handler._cancel()  # noqa

    def _track_fence(
            self,
            ctx: IoPipelineHandlerContext,
            msg: IoPipelineMessages.Completable[None],
            *,
            final_output: bool,
    ) -> None:
        token = id(msg)
        check.not_in(token, self._handles)

        handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            self._timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, WriteTimeoutIoPipelineHandler)._on_timeout(ctx2, token),  # noqa
        )
        self._handles[token] = handle
        msg.add_listener(functools.partial(
            self._on_fence_done,
            weakref.ref(self),
            token,
            final_output,
        ))

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            check.not_none(ctx.services.find(IoPipelineScheduling))

            self._active = False
            self._timed_out = False
            self._cancel()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._active = False
            self._cancel()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._cancel()
            self._active = True
            self._timed_out = False

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if (
                self._active and
                not self._timed_out and
                isinstance(msg, (
                    IoPipelineFlowMessages.FlushOutput,
                    IoPipelineMessages.ShutdownOutput,
                    IoPipelineMessages.FinalOutput,
                ))
        ):
            self._track_fence(
                ctx,
                msg,
                final_output=isinstance(msg, IoPipelineMessages.FinalOutput),
            )

        ctx.feed_out(msg)


########################################
# ../../../../omcore/io/streambufs/direct.py


##


class BaseDirectByteStreamBufferLike(BaseByteStreamBufferLike, Abstract):
    def __init__(self, data: BytesLike) -> None:
        super().__init__()

        self._data = data
        if isinstance(data, memoryview):
            self._mv_ = data
        else:
            self._b_ = data

    _mv_: memoryview
    _b_: ta.Union[bytes, bytearray]

    def _mv(self) -> memoryview:
        try:
            return self._mv_
        except AttributeError:
            pass

        self._mv_ = mv = memoryview(self._b_)
        return mv

    def _b(self) -> ta.Union[bytes, bytearray]:
        try:
            return self._b_
        except AttributeError:
            pass

        self._b_ = b = memoryview_to_bytes(self._mv_)  # noqa
        return b


class DirectByteStreamBufferView(BaseDirectByteStreamBufferLike, ByteStreamBufferView):
    def __len__(self) -> int:
        return len(self._data)

    def peek(self) -> memoryview:
        return self._mv()

    def segments(self) -> ta.Sequence[memoryview]:
        return (self._mv(),) if len(self._data) else ()

    def tobytes(self) -> Bytes:
        if type(b := self._b()) is bytes:
            return b
        return bytes(b)


class DirectByteStreamBuffer(BaseDirectByteStreamBufferLike, ByteStreamBuffer):
    """
    A read-only ByteStreamBuffer that wraps existing bytes without copying.

    This is a lightweight, zero-copy wrapper around bytes/bytearray/memoryview that provides the full
    ByteStreamBuffer interface (find, rfind, find_all_in_prefix, split_to, advance, coalesce) without mutation
    capabilities.

    Strengths:
      - Zero-copy construction from existing data
      - Always contiguous (coalesce is trivial)
      - Fast find/rfind delegating to optimized bytes methods
      - Simple implementation with minimal overhead

    Use cases:
      - Parsing fixed/immutable data (HTTP requests, protocol messages)
      - Using framers/codecs on data already in memory
      - Avoiding buffer allocation/copying overhead when mutation isn't needed

    Important notes:
      - If constructed from a bytearray, the underlying data could still be mutated externally. This is by design -
        we're wrapping directly, not defensively copying.
      - This is a read-only buffer - it does not implement MutableByteStreamBuffer (no write/reserve/commit).
      - All views returned from split_to() remain valid as they reference the original underlying data.

    Example:
        >>> data = b'GET /path HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n'
        >>> buf = DirectByteStreamBuffer(data)
        >>> pos = buf.find(b'\\r\\n\\r\\n')
        >>> headers = buf.split_to(pos)
        >>> print(headers.tobytes())
        b'GET /path HTTP/1.1\\r\\nHost: example.com'
    """

    def __init__(self, data: BytesLike) -> None:
        super().__init__(data)

        self._rpos = 0

    def __len__(self) -> int:
        return len(self._data) - self._rpos

    def peek(self) -> memoryview:
        mv = self._mv()
        if self._rpos >= len(mv):
            return memoryview(b'')
        return mv[self._rpos:]

    def segments(self) -> ta.Sequence[memoryview]:
        mv = self.peek()
        return (mv,) if len(mv) else ()

    def advance(self, n: int, /) -> None:
        if n < 0 or n > len(self):
            raise ValueError(n)
        self._rpos += n

    def split_to(self, n: int, /) -> ByteStreamBufferView:
        if n < 0 or n > len(self):
            raise ValueError(n)
        if not n:
            return _EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW

        if not self._rpos and n == len(self._data):
            self._rpos += n
            return DirectByteStreamBufferView(self._data)

        mv = self._mv()
        view = mv[self._rpos:self._rpos + n]
        self._rpos += n
        return DirectByteStreamBufferView(view)

    def find(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        start, end = self._norm_slice(start, end)

        if not sub:
            return start

        b = self._b()
        idx = b.find(sub, self._rpos + start, self._rpos + end)
        return (idx - self._rpos) if idx >= 0 else -1

    def rfind(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        start, end = self._norm_slice(start, end)

        if not sub:
            return end

        b = self._b()
        idx = b.rfind(sub, self._rpos + start, self._rpos + end)
        return (idx - self._rpos) if idx >= 0 else -1

    def find_all_in_prefix(self, sub: bytes, start: int = 0) -> ta.Sequence[int]:
        if not sub:
            raise ValueError('empty sub')
        if start < 0:
            raise ValueError(start)

        out: ta.List[int] = []
        append = out.append
        find = self._b().find
        rp = self._rpos
        end = len(self._data)
        m = len(sub)
        pos = rp + start
        while (i := find(sub, pos, end)) >= 0:
            append(i - rp)
            pos = i + m
        return out

    def coalesce(self, n: int, /) -> memoryview:
        if n < 0 or n > len(self):
            raise ValueError(n)
        if not n:
            return memoryview(b'')

        # Always contiguous - just return the requested slice
        mv = self._mv()
        return mv[self._rpos:self._rpos + n]


##


_EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW = DirectByteStreamBufferView(b'')


def empty_byte_stream_buffer_view() -> ByteStreamBufferView:
    return _EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW


########################################
# ../../../../omcore/io/streambufs/scanning.py


##


class ScanningByteStreamBuffer(BaseByteStreamBufferLike, MutableByteStreamBuffer):
    """
    A MutableByteStreamBuffer wrapper that caches negative-find progress to avoid repeated rescans in trickle scenarios.

    It is intentionally conservative:
      - It only caches progress for the default find range (start==0, end is None).
      - It only caches *negative* results (i.e., "-1"): once a match is found, caching is not updated, to preserve the
        property that repeated `find(sub)` on an unchanged buffer yields the same answer.
      - The same cache accelerates the bulk `find_all_in_prefix` primitive, keeping batch framing linear under trickle
        input (an empty bulk scan records the prefix length as negative progress).

    This is designed to help framing-style code that repeatedly does:
      - buf.write(...small...)
      - buf.find(delim) (or a batch-decoding framer's find_all_in_prefix(delim))
      - (not found) repeat

    Pairs well with `LongestMatchDelimiterByteStreamFrameDecoder`.
    """

    def __init__(self, buf) -> None:
        super().__init__()

        self._buf = buf
        self._scan_from_by_sub: ta.Dict[bytes, int] = {}

    @property
    def max_size(self) -> ta.Optional[int]:
        return self._buf.max_size

    #

    def __len__(self) -> int:
        return len(self._buf)

    def peek(self) -> memoryview:
        return self._buf.peek()

    def segments(self) -> ta.Sequence[memoryview]:
        return self._buf.segments()

    #

    def advance(self, n: int, /) -> None:
        self._buf.advance(n)
        self._adjust_for_consume(n)

    def split_to(self, n: int, /) -> ByteStreamBufferView:
        v = self._buf.split_to(n)
        self._adjust_for_consume(n)
        return v

    def coalesce(self, n: int, /) -> memoryview:
        return self._buf.coalesce(n)

    def find(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        if start != 0 or end is not None:
            return self._buf.find(sub, start, end)

        sub_len = len(sub)
        if sub_len <= 0:
            return self._buf.find(sub, start, end)

        scan_from = self._scan_from_by_sub.get(sub, 0)

        # Allow overlap so a match spanning old/new boundary is discoverable.
        overlap = sub_len - 1
        eff_start = scan_from - overlap
        if eff_start < 0:
            eff_start = 0

        i = self._buf.find(sub, eff_start, None)
        if i < 0:
            self._scan_from_by_sub[sub] = len(self._buf)

        return i

    def rfind(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        # rfind isn't the typical trickle hot-path; delegate.
        return self._buf.rfind(sub, start, end)

    def find_all_in_prefix(self, sub: bytes, start: int = 0) -> ta.Sequence[int]:
        if start != 0 or not (m := len(sub)):
            return self._buf.find_all_in_prefix(sub, start)

        scan_from = self._scan_from_by_sub.get(sub, 0)

        # Allow overlap so a match spanning old/new boundary is discoverable.
        eff_start = scan_from - (m - 1)
        if eff_start < 0:
            eff_start = 0

        hits = self._buf.find_all_in_prefix(sub, eff_start)
        if not hits:
            # A miss only proves no match *starts* early enough to lie entirely within the contiguous prefix - one
            # starting in its last m-1 bytes may still complete across the segment boundary or after future writes.
            # The stored value's read-side overlap rewind accounts for exactly that, so the prefix length itself is
            # the correct cache value (mirroring find()'s use of the full buffer length).
            pl = len(self._buf.peek())
            if pl > scan_from:
                self._scan_from_by_sub[sub] = pl

        return hits

    #

    def write(self, data: BytesLike, /) -> None:
        self._buf.write(data)

    def reserve(self, n: int, /) -> memoryview:
        return self._buf.reserve(n)

    def commit(self, n: int, /) -> None:
        self._buf.commit(n)

    #

    def _adjust_for_consume(self, n: int) -> None:
        if not self._scan_from_by_sub:
            return

        if n <= 0:
            return

        # Only front-consumption exists in this buffer model.
        for k, v in list(self._scan_from_by_sub.items()):
            nv = v - n
            if nv <= 0:
                self._scan_from_by_sub.pop(k, None)
            else:
                self._scan_from_by_sub[k] = nv


########################################
# ../../../../omcore/logs/base.py


##


class AnyLogger(AnyLoggerMetricCollector[T], Abstract, ta.Generic[T]):
    def is_enabled_for(self, level: LogLevel) -> bool:
        return level >= self.get_effective_level()

    @abc.abstractmethod
    def get_effective_level(self) -> LogLevel:
        raise NotImplementedError

    #

    @ta.final
    def isEnabledFor(self, level: LogLevel) -> bool:  # noqa
        return self.is_enabled_for(level)

    @ta.final
    def getEffectiveLevel(self) -> LogLevel:  # noqa
        return self.get_effective_level()

    ##

    # This will be 1 for [Sync]Logger and 0 for AsyncLogger - in sync loggers these methods remain present on the stack,
    # in async loggers they return a coroutine to be awaited and thus aren't actually present when said coroutine is
    # awaited.
    _level_proxy_method_stack_offset: int

    @ta.overload
    def log(self, level: LogLevel, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def log(self, level: LogLevel, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def log(self, level: LogLevel, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def log(self, level: LogLevel, *args, **kwargs):
        b, t = self._do_not_log_(level)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def debug(self, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def debug(self, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def debug(self, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def debug(self, *args, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.DEBUG)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def info(self, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def info(self, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def info(self, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def info(self, *args, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.INFO)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def warning(self, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def warning(self, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def warning(self, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def warning(self, *args, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.WARNING)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def error(self, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def error(self, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def error(self, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def error(self, *args, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.ERROR)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def exception(self, exc: BaseException, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def exception(self, *, exc_info: LoggingExcInfoArg = True, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def exception(self, msg: str, *args: ta.Any, exc_info: LoggingExcInfoArg = True, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def exception(self, msg: ta.Tuple[ta.Any, ...], *, exc_info: LoggingExcInfoArg = True, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def exception(self, msg_fn: LoggingMsgFn, *, exc_info: LoggingExcInfoArg = True, **kwargs: ta.Any) -> T: ...

    @ta.final
    def exception(self, *args, exc_info=True, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.ERROR)
        if b:
            return t

        if not args:
            if not exc_info:
                raise TypeError('exc_info=False is not allowed when no args are passed')
            args = ((),)
        elif len(args) == 1:
            if isinstance(arg0 := args[0], BaseException):
                if exc_info is not True:  # noqa
                    raise TypeError(f'exc_info={exc_info!r} is not allowed when exc={arg0!r} is passed')
                args, exc_info = ((),), arg0

        return self._log(
            CaptureLoggingContextImpl(
                level,
                exc_info=exc_info,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @ta.overload
    def critical(self, msg: str, *args: ta.Any, **kwargs: ta.Any) -> T: ...

    @ta.overload
    def critical(self, msg: ta.Tuple[ta.Any, ...], **kwargs: ta.Any) -> T: ...

    @ta.overload
    def critical(self, msg_fn: LoggingMsgFn, **kwargs: ta.Any) -> T: ...

    @ta.final
    def critical(self, *args, **kwargs):
        b, t = self._do_not_log_(level := NamedLogLevel.CRITICAL)
        if b:
            return t

        return self._log(
            CaptureLoggingContextImpl(
                level,
                stack_offset=self._level_proxy_method_stack_offset,
            ),
            *args,
            **kwargs,
        )

    #

    @abc.abstractmethod
    def _do_not_log_(self, level: LogLevel) -> ta.Tuple[bool, T]:
        raise NotImplementedError

    @abc.abstractmethod
    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> T:
        raise NotImplementedError


class Logger(LoggerMetricCollector, AnyLogger[None], Abstract):
    _level_proxy_method_stack_offset: int = 1

    @ta.final
    def _do_not_log_(self, level: LogLevel) -> ta.Tuple[bool, None]:
        return not self.is_enabled_for(level), None

    @abc.abstractmethod
    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def _metric(self, m: LoggerMetric) -> None:
        raise NotImplementedError


class AsyncLogger(AsyncLoggerMetricCollector, AnyLogger[ta.Awaitable[None]], Abstract):
    _level_proxy_method_stack_offset: int = 0

    @ta.final
    def _do_not_log_(self, level: LogLevel) -> ta.Tuple[bool, ta.Awaitable[None]]:
        if self.is_enabled_for(level):
            return False, None  # type: ignore

        async def nop():
            return None

        return True, nop()

    @abc.abstractmethod
    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> ta.Awaitable[None]:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def _metric(self, m: LoggerMetric) -> ta.Awaitable[None]:
        raise NotImplementedError


##


class AnyNopLogger(AnyNopLoggerMetricCollector[T], AnyLogger[T], Abstract):
    @ta.final
    def get_effective_level(self) -> LogLevel:
        return -999


class NopLogger(NopLoggerMetricCollector, AnyNopLogger[None], Logger):
    @ta.final
    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> None:
        pass


class AsyncNopLogger(AsyncNopLoggerMetricCollector, AnyNopLogger[ta.Awaitable[None]], AsyncLogger):
    @ta.final
    async def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> None:
        pass


########################################
# ../../../../omcore/logs/std/records.py
"""
TODO:
 - TypedDict?
"""


##


class LoggingContextInfoRecordAdapters:
    # Ref:
    #  - https://docs.python.org/3/library/logging.html#logrecord-attributes
    #
    # LogRecord:
    #  - https://github.com/python/cpython/blob/39b2f82717a69dde7212bc39b673b0f55c99e6a3/Lib/logging/__init__.py#L276 (3.8)  # noqa
    #  - https://github.com/python/cpython/blob/f070f54c5f4a42c7c61d1d5d3b8f3b7203b4a0fb/Lib/logging/__init__.py#L286 (~3.14)  # noqa
    #

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    class Adapter(Abstract, ta.Generic[T]):
        @property
        @abc.abstractmethod
        def info_cls(self) -> ta.Type[LoggingContextInfo]:
            raise NotImplementedError

        #

        @ta.final
        class NOT_SET:  # noqa
            def __new__(cls, *args, **kwargs):  # noqa
                raise TypeError

        class RecordAttr(ta.NamedTuple):
            name: str
            type: ta.Any
            default: ta.Any

        # @abc.abstractmethod
        record_attrs: ta.ClassVar[ta.Mapping[str, RecordAttr]]

        @property
        @abc.abstractmethod
        def _record_attrs(self) -> ta.Union[
            ta.Mapping[str, ta.Any],
            ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]],
        ]:
            raise NotImplementedError

        #

        @abc.abstractmethod
        def context_to_record(self, ctx: LoggingContext) -> ta.Mapping[str, ta.Any]:
            raise NotImplementedError

        #

        @abc.abstractmethod
        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[T]:
            raise NotImplementedError

        #

        def __init_subclass__(cls, **kwargs: ta.Any) -> None:
            super().__init_subclass__(**kwargs)

            if Abstract in cls.__bases__:
                return

            if 'record_attrs' in cls.__dict__:
                raise TypeError(cls)
            if not isinstance(ra := cls.__dict__['_record_attrs'], collections.abc.Mapping):
                raise TypeError(ra)

            rd: ta.Dict[str, LoggingContextInfoRecordAdapters.Adapter.RecordAttr] = {}
            for n, v in ra.items():
                if not n or not isinstance(n, str) or n in rd:
                    raise AttributeError(n)
                if isinstance(v, tuple):
                    t, d = v
                else:
                    t, d = v, cls.NOT_SET
                rd[n] = cls.RecordAttr(
                    name=n,
                    type=t,
                    default=d,
                )
            cls.record_attrs = rd

    class RequiredAdapter(Adapter[T], Abstract):
        @property
        @abc.abstractmethod
        def _record_attrs(self) -> ta.Mapping[str, ta.Any]:
            raise NotImplementedError

        #

        @ta.final
        def context_to_record(self, ctx: LoggingContext) -> ta.Mapping[str, ta.Any]:
            if (info := ctx.get_info(self.info_cls)) is not None:
                return self._info_to_record(info)
            else:
                raise TypeError  # FIXME: fallback?

        @abc.abstractmethod
        def _info_to_record(self, info: T) -> ta.Mapping[str, ta.Any]:
            raise NotImplementedError

        #

        @abc.abstractmethod
        def record_to_info(self, rec: logging.LogRecord) -> T:
            raise NotImplementedError

        #

        def __init_subclass__(cls, **kwargs: ta.Any) -> None:
            super().__init_subclass__(**kwargs)

            if any(a.default is not cls.NOT_SET for a in cls.record_attrs.values()):
                raise TypeError(cls.record_attrs)

    class OptionalAdapter(Adapter[T], Abstract, ta.Generic[T]):
        @property
        @abc.abstractmethod
        def _record_attrs(self) -> ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]:
            raise NotImplementedError

        record_defaults: ta.ClassVar[ta.Mapping[str, ta.Any]]

        #

        @ta.final
        def context_to_record(self, ctx: LoggingContext) -> ta.Mapping[str, ta.Any]:
            if (info := ctx.get_info(self.info_cls)) is not None:
                return self._info_to_record(info)
            else:
                return self.record_defaults

        @abc.abstractmethod
        def _info_to_record(self, info: T) -> ta.Mapping[str, ta.Any]:
            raise NotImplementedError

        #

        def __init_subclass__(cls, **kwargs: ta.Any) -> None:
            super().__init_subclass__(**kwargs)

            dd: ta.Dict[str, ta.Any] = {a.name: a.default for a in cls.record_attrs.values()}
            if any(d is cls.NOT_SET for d in dd.values()):
                raise TypeError(cls.record_attrs)
            cls.record_defaults = dd

    #

    class Name(RequiredAdapter[LoggingContextInfos.Name]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Name]] = LoggingContextInfos.Name

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Any]] = dict(
            # Name of the logger used to log the call. Unmodified by ctor.
            name=str,
        )

        def _info_to_record(self, info: LoggingContextInfos.Name) -> ta.Mapping[str, ta.Any]:
            return dict(
                name=info.name,
            )

        def record_to_info(self, rec: logging.LogRecord) -> LoggingContextInfos.Name:
            return LoggingContextInfos.Name(
                name=rec.name,
            )

    class Level(RequiredAdapter[LoggingContextInfos.Level]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Level]] = LoggingContextInfos.Level

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Any]] = dict(
            # Text logging level for the message ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'). Set to
            # `getLevelName(level)`.
            levelname=str,

            # Numeric logging level for the message (DEBUG, INFO, WARNING, ERROR, CRITICAL). Unmodified by ctor.
            levelno=int,
        )

        def _info_to_record(self, info: LoggingContextInfos.Level) -> ta.Mapping[str, ta.Any]:
            return dict(
                levelname=info.name,
                levelno=int(info.level),
            )

        def record_to_info(self, rec: logging.LogRecord) -> LoggingContextInfos.Level:
            return LoggingContextInfos.Level.build(rec.levelno)

    class Msg(RequiredAdapter[LoggingContextInfos.Msg]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Msg]] = LoggingContextInfos.Msg

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Any]] = dict(
            # The format string passed in the original logging call. Merged with args to produce message, or an
            # arbitrary object (see Using arbitrary objects as messages). Unmodified by ctor.
            msg=str,

            # The tuple of arguments merged into msg to produce message, or a dict whose values are used for the merge
            # (when there is only one argument, and it is a dictionary). Ctor will transform a 1-tuple containing a
            # Mapping into just the mapping, but is otherwise unmodified.
            args=ta.Union[tuple, dict, None],
        )

        def _info_to_record(self, info: LoggingContextInfos.Msg) -> ta.Mapping[str, ta.Any]:
            return dict(
                msg=info.msg,
                args=info.args,
            )

        def record_to_info(self, rec: logging.LogRecord) -> LoggingContextInfos.Msg:
            return LoggingContextInfos.Msg(
                msg=rec.msg,
                args=rec.args,
            )

    class Time(RequiredAdapter[LoggingContextInfos.Time]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Time]] = LoggingContextInfos.Time

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Any]] = dict(
            # Time when the LogRecord was created. Set to `time.time_ns() / 1e9` for >=3.13.0b1, otherwise simply
            # `time.time()`.
            #
            # See:
            #  - https://github.com/python/cpython/commit/1316692e8c7c1e1f3b6639e51804f9db5ed892ea
            #  - https://github.com/python/cpython/commit/1500a23f33f5a6d052ff1ef6383d9839928b8ff1
            #
            created=float,

            # Millisecond portion of the time when the LogRecord was created.
            msecs=float,

            # Time in milliseconds when the LogRecord was created, relative to the time the logging module was loaded.
            relativeCreated=float,
        )

        def _info_to_record(self, info: LoggingContextInfos.Time) -> ta.Mapping[str, ta.Any]:
            return dict(
                created=info.secs,
                msecs=info.msecs,
                relativeCreated=info.relative_secs,
            )

        def record_to_info(self, rec: logging.LogRecord) -> LoggingContextInfos.Time:
            return LoggingContextInfos.Time.build(
                int(rec.created * 1e9),
            )

    class Exc(OptionalAdapter[LoggingContextInfos.Exc]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Exc]] = LoggingContextInfos.Exc

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]] = dict(
            # Exception tuple (à la sys.exc_info) or, if no exception has occurred, None. Unmodified by ctor.
            exc_info=(ta.Optional[LoggingExcInfoTuple], None),

            # Used to cache the traceback text. Simply set to None by ctor, later set by Formatter.format.
            exc_text=(ta.Optional[str], None),
        )

        def _info_to_record(self, info: LoggingContextInfos.Exc) -> ta.Mapping[str, ta.Any]:
            return dict(
                exc_info=info.info_tuple,
                exc_text=None,
            )

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.Exc]:
            # FIXME:
            # error: Argument 1 to "build" of "Exc" has incompatible type
            # "tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None] | None"; expected  # noqa
            # "BaseException | tuple[type[BaseException], BaseException, TracebackType | None] | bool | None"  [arg-type]  # noqa
            return LoggingContextInfos.Exc.build(rec.exc_info)  # type: ignore[arg-type]

    class Caller(OptionalAdapter[LoggingContextInfos.Caller]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Caller]] = LoggingContextInfos.Caller

        _UNKNOWN_PATH_NAME: ta.ClassVar[str] = '(unknown file)'
        _UNKNOWN_FUNC_NAME: ta.ClassVar[str] = '(unknown function)'

        _STACK_INFO_PREFIX: ta.ClassVar[str] = 'Stack (most recent call last):\n'

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]] = dict(
            # Full pathname of the source file where the logging call was issued (if available). Unmodified by ctor. May
            # default to "(unknown file)" by Logger.findCaller / Logger._log.
            pathname=(str, _UNKNOWN_PATH_NAME),

            # Source line number where the logging call was issued (if available). Unmodified by ctor. May default to 0
            # by Logger.findCaller / Logger._log.
            lineno=(int, 0),

            # Name of function containing the logging call. Set by ctor to `func` arg, unmodified. May default to
            # "(unknown function)" by Logger.findCaller / Logger._log.
            funcName=(str, _UNKNOWN_FUNC_NAME),

            # Stack frame information (where available) from the bottom of the stack in the current thread, up to and
            # including the stack frame of the logging call which resulted in the creation of this record. Set by ctor
            # to `sinfo` arg, unmodified. Mostly set, if requested, by `Logger.findCaller`, to
            # `traceback.print_stack(f)`, but prepended with the literal "Stack (most recent call last):\n", and
            # stripped of exactly one trailing `\n` if present.
            stack_info=(ta.Optional[str], None),
        )

        def _info_to_record(self, caller: LoggingContextInfos.Caller) -> ta.Mapping[str, ta.Any]:
            if (sinfo := caller.stack_info) is not None:
                stack_info: ta.Optional[str] = '\n'.join([
                    self._STACK_INFO_PREFIX,
                    sinfo[1:] if sinfo.endswith('\n') else sinfo,
                ])
            else:
                stack_info = None

            return dict(
                pathname=caller.file_path,

                lineno=caller.line_no,
                funcName=caller.func_name,

                stack_info=stack_info,
            )

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.Caller]:
            # FIXME: piecemeal?
            if (
                    rec.pathname != self._UNKNOWN_PATH_NAME and
                    rec.lineno != 0 and
                    rec.funcName != self._UNKNOWN_FUNC_NAME
            ):
                if (sinfo := rec.stack_info) is not None and sinfo.startswith(self._STACK_INFO_PREFIX):
                    sinfo = sinfo[len(self._STACK_INFO_PREFIX):]
                return LoggingContextInfos.Caller(
                    file_path=rec.pathname,

                    line_no=rec.lineno,
                    func_name=rec.funcName,

                    stack_info=sinfo,
                )

            return None

    class SourceFile(Adapter[LoggingContextInfos.SourceFile]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.SourceFile]] = LoggingContextInfos.SourceFile

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Any]] = dict(
            # Filename portion of pathname. Set to `os.path.basename(pathname)` if successful, otherwise defaults to
            # pathname.
            filename=str,

            # Module (name portion of filename). Set to `os.path.splitext(filename)[0]`, otherwise defaults to
            # "Unknown module".
            module=str,
        )

        _UNKNOWN_MODULE: ta.ClassVar[str] = 'Unknown module'

        def context_to_record(self, ctx: LoggingContext) -> ta.Mapping[str, ta.Any]:
            if (info := ctx.get_info(LoggingContextInfos.SourceFile)) is not None:
                return dict(
                    filename=info.file_name,
                    module=info.module,
                )

            if (caller := ctx.get_info(LoggingContextInfos.Caller)) is not None:
                return dict(
                    filename=caller.file_path,
                    module=self._UNKNOWN_MODULE,
                )

            return dict(
                filename=LoggingContextInfoRecordAdapters.Caller._UNKNOWN_PATH_NAME,  # noqa
                module=self._UNKNOWN_MODULE,
            )

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.SourceFile]:
            if (
                    rec.module is not None and
                    rec.module != self._UNKNOWN_MODULE
            ):
                return LoggingContextInfos.SourceFile(
                    file_name=rec.filename,
                    module=rec.module,  # FIXME: piecemeal?
                )

            return None

    class Thread(OptionalAdapter[LoggingContextInfos.Thread]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Thread]] = LoggingContextInfos.Thread

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]] = dict(
            # Thread ID if available, and `logging.logThreads` is truthy.
            thread=(ta.Optional[int], None),

            # Thread name if available, and `logging.logThreads` is truthy.
            threadName=(ta.Optional[str], None),
        )

        def _info_to_record(self, info: LoggingContextInfos.Thread) -> ta.Mapping[str, ta.Any]:
            if logging.logThreads:
                return dict(
                    thread=info.ident,
                    threadName=info.name,
                )

            return self.record_defaults

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.Thread]:
            if (
                    (ident := rec.thread) is not None and
                    (name := rec.threadName) is not None
            ):
                return LoggingContextInfos.Thread(
                    ident=ident,
                    native_id=None,
                    name=name,
                )

            return None

    class Process(OptionalAdapter[LoggingContextInfos.Process]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Process]] = LoggingContextInfos.Process

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]] = dict(
            # Process ID if available - that is, if `hasattr(os, 'getpid')` - and `logging.logProcesses` is truthy,
            # otherwise None.
            process=(ta.Optional[int], None),
        )

        def _info_to_record(self, info: LoggingContextInfos.Process) -> ta.Mapping[str, ta.Any]:
            if logging.logProcesses:
                return dict(
                    process=info.pid,
                )

            return self.record_defaults

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.Process]:
            if (
                    (pid := rec.process) is not None
            ):
                return LoggingContextInfos.Process(
                    pid=pid,
                )

            return None

    class Multiprocessing(OptionalAdapter[LoggingContextInfos.Multiprocessing]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.Multiprocessing]] = LoggingContextInfos.Multiprocessing

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Tuple[ta.Any, ta.Any]]] = dict(
            # Process name if available. Set to None if `logging.logMultiprocessing` is not truthy. Otherwise, set to
            # 'MainProcess', then `sys.modules.get('multiprocessing').current_process().name` if that works, otherwise
            # remains as 'MainProcess'.
            #
            # As noted by stdlib:
            #
            #   Errors may occur if multiprocessing has not finished loading yet - e.g. if a custom import hook causes
            #   third-party code to run when multiprocessing calls import. See issue 8200 for an example
            #
            processName=(ta.Optional[str], None),
        )

        def _info_to_record(self, info: LoggingContextInfos.Multiprocessing) -> ta.Mapping[str, ta.Any]:
            if logging.logMultiprocessing:
                return dict(
                    processName=info.process_name,
                )

            return self.record_defaults

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.Multiprocessing]:
            if (
                    (process_name := rec.processName) is not None
            ):
                return LoggingContextInfos.Multiprocessing(
                    process_name=process_name,
                )

            return None

    class AsyncioTask(OptionalAdapter[LoggingContextInfos.AsyncioTask]):
        info_cls: ta.ClassVar[ta.Type[LoggingContextInfos.AsyncioTask]] = LoggingContextInfos.AsyncioTask

        _record_attrs: ta.ClassVar[ta.Mapping[str, ta.Union[ta.Any, ta.Tuple[ta.Any, ta.Any]]]] = dict(
            # Absent <3.12, otherwise asyncio.Task name if available, and `logging.logAsyncioTasks` is truthy. Set to
            # `sys.modules.get('asyncio').current_task().get_name()`, otherwise None.
            taskName=(ta.Optional[str], None),
        )

        def _info_to_record(self, info: LoggingContextInfos.AsyncioTask) -> ta.Mapping[str, ta.Any]:
            if getattr(logging, 'logAsyncioTasks', None):  # Absent <3.12
                return dict(
                    taskName=info.name,
                )

            return self.record_defaults

        def record_to_info(self, rec: logging.LogRecord) -> ta.Optional[LoggingContextInfos.AsyncioTask]:
            if (
                    (name := getattr(rec, 'taskName', None)) is not None
            ):
                return LoggingContextInfos.AsyncioTask(
                    name=name,
                )

            return None


_LOGGING_CONTEXT_INFO_RECORD_ADAPTERS_: ta.Sequence[LoggingContextInfoRecordAdapters.Adapter] = [  # noqa
    LoggingContextInfoRecordAdapters.Name(),
    LoggingContextInfoRecordAdapters.Level(),
    LoggingContextInfoRecordAdapters.Msg(),
    LoggingContextInfoRecordAdapters.Time(),
    LoggingContextInfoRecordAdapters.Exc(),
    LoggingContextInfoRecordAdapters.Caller(),
    LoggingContextInfoRecordAdapters.SourceFile(),
    LoggingContextInfoRecordAdapters.Thread(),
    LoggingContextInfoRecordAdapters.Process(),
    LoggingContextInfoRecordAdapters.Multiprocessing(),
    LoggingContextInfoRecordAdapters.AsyncioTask(),
]

_LOGGING_CONTEXT_INFO_RECORD_ADAPTERS: ta.Mapping[ta.Type[LoggingContextInfo], LoggingContextInfoRecordAdapters.Adapter] = {  # noqa
    ad.info_cls: ad for ad in _LOGGING_CONTEXT_INFO_RECORD_ADAPTERS_
}


##


# Formatter:
#  - https://github.com/python/cpython/blob/39b2f82717a69dde7212bc39b673b0f55c99e6a3/Lib/logging/__init__.py#L514 (3.8)
#  - https://github.com/python/cpython/blob/f070f54c5f4a42c7c61d1d5d3b8f3b7203b4a0fb/Lib/logging/__init__.py#L554 (~3.14)  # noqa
#
_KNOWN_STD_LOGGING_FORMATTER_RECORD_ATTRS: ta.Dict[str, ta.Any] = dict(
    # The logged message, computed as msg % args. Set to `record.getMessage()`.
    message=str,

    # Human-readable time when the LogRecord was created. By default this is of the form '2003-07-08 16:49:45,896' (the
    # numbers after the comma are millisecond portion of the time). Set to `self.formatTime(record, self.datefmt)` if
    # `self.usesTime()`, otherwise unset.
    asctime=str,

    # Used to cache the traceback text. If unset (falsey) on the record and `exc_info` is truthy, set to
    # `self.formatException(record.exc_info)` - otherwise unmodified.
    exc_text=ta.Optional[str],
)


##


_KNOWN_STD_LOGGING_RECORD_ATTR_SET: ta.FrozenSet[str] = frozenset(
    a for ad in _LOGGING_CONTEXT_INFO_RECORD_ADAPTERS.values() for a in ad.record_attrs
)

_KNOWN_STD_LOGGING_FORMATTER_RECORD_ATTR_SET: ta.FrozenSet[str] = frozenset(_KNOWN_STD_LOGGING_FORMATTER_RECORD_ATTRS)


class UnknownStdLoggingRecordAttrsWarning(LoggingSetupWarning):
    pass


def _check_std_logging_record_attrs() -> None:
    if (
            len([a for ad in _LOGGING_CONTEXT_INFO_RECORD_ADAPTERS.values() for a in ad.record_attrs]) !=
            len(_KNOWN_STD_LOGGING_RECORD_ATTR_SET)
    ):
        raise RuntimeError('Duplicate LoggingContextInfoRecordAdapter record attrs')

    rec_dct = dict(logging.makeLogRecord({}).__dict__)

    if (unk_rec_fields := frozenset(rec_dct) - _KNOWN_STD_LOGGING_RECORD_ATTR_SET):
        import warnings  # noqa

        warnings.warn(
            f'Unknown log record attrs detected: {sorted(unk_rec_fields)!r}',
            UnknownStdLoggingRecordAttrsWarning,
        )


_check_std_logging_record_attrs()


##


class LoggingContextLogRecord(logging.LogRecord):
    # LogRecord.__init__ args:
    #  - name: str
    #  - level: int
    #  - pathname: str - Confusingly referred to as `fn` before the LogRecord ctor. May be empty or "(unknown file)".
    #  - lineno: int - May be 0.
    #  - msg: str
    #  - args: tuple | dict | 1-tuple[dict]
    #  - exc_info: LoggingExcInfoTuple | None
    #  - func: str | None = None -> funcName
    #  - sinfo: str | None = None -> stack_info
    #

    def __init__(self, *, _logging_context: LoggingContext) -> None:  # noqa
        self.__dict__.update(_logging_context=_logging_context)

        for ad in _LOGGING_CONTEXT_INFO_RECORD_ADAPTERS_:
            self.__dict__.update(ad.context_to_record(_logging_context))

    _logging_context: LoggingContext

    # FIXME: track extra
    # def __setattr__(self, key, value):
    #     super().__setattr__(key, value)


##


@ta.final
class LogRecordLoggingContext(LoggingContext):
    def __init__(self, rec: logging.LogRecord) -> None:
        if isinstance(rec, LoggingContextLogRecord):
            raise TypeError(rec)

        self._rec = rec

        infos: ta.List[LoggingContextInfo] = [
            info
            for ad in _LOGGING_CONTEXT_INFO_RECORD_ADAPTERS_
            if (info := ad.record_to_info(rec)) is not None
        ]

        # FIXME:
        # if extra is not None:
        #     for key in extra:
        #         if (key in ["message", "asctime"]) or (key in rv.__dict__):
        #             raise KeyError("Attempt to overwrite %r in LogRecord" % key)
        #         rv.__dict__[key] = extra[key]

        if (extra := {
            a: v
            for a, v in rec.__dict__.items()
            if a not in _KNOWN_STD_LOGGING_RECORD_ATTR_SET
        }):
            infos.append(LoggingContextInfos.Extra(extra))

        self._infos: ta.Dict[ta.Type[LoggingContextInfo], LoggingContextInfo] = {
            type(info): info
            for info in infos
        }

    def get_info(self, ty: ta.Type[LoggingContextInfoT]) -> ta.Optional[LoggingContextInfoT]:
        return self._infos.get(ty)


########################################
# ../../../../omcore/rpc/messages.py
"""
The two message vocabularies of the toolbox.

Envelopes are what crosses the wire: seven frozen dataclasses, symmetric between the two ends of a connection. Request
ids are opaque values scoped to the direction they were issued in, so the same id may be in flight independently in
both directions. Params and results are opaque: the envelope codec hands them to the wire value codec untouched, so they
must be whatever that codec can represent, which is what a serde sitting above the connection guarantees.

Session messages are the vocabulary between a connection (the code driving a pipeline driver) and the session handler
sitting innermost in its pipeline. Commands are fed inbound at the pipeline boundary via a driver's `enqueue`, pass
untouched through the byte-level handlers, and are consumed by the session. Events are fed outbound by the session and,
being unhandled by any driver, are returned to the connection from the driver's `next`.

Commands are marked `AfterFinalInput` so that responses to in-flight inbound requests may still be sent after the peer
half-closes its side of the transport.
"""


##


class RpcUnspecified:
    """A sentinel type - the class itself is the value - for 'use the configured default', as distinct from None."""

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError


##


class RpcEnvelope(Abstract):
    """Base class of everything which crosses the wire."""

    @staticmethod
    def _check_id(id: ta.Any) -> None:  # noqa
        # Ids key the sessions' bookkeeping, so one off the wire must be hashable: a list or mapping is a protocol
        # violation, not a crash.
        if id is None:
            raise RpcProtocolError('message id must not be None')
        try:
            hash(id)
        except TypeError:
            raise RpcProtocolError(f'message id must be hashable: {id!r}') from None


@dc.dataclass(frozen=True)
class RpcRequestMessage(RpcEnvelope):
    id: ta.Any
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        self._check_id(self.id)
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcResultMessage(RpcEnvelope):
    id: ta.Any
    result: ta.Any = None

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcErrorMessage(RpcEnvelope):
    id: ta.Any
    error: RpcRemoteErrorData

    def __post_init__(self) -> None:
        self._check_id(self.id)
        check.isinstance(self.error, RpcRemoteErrorData, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcCancelMessage(RpcEnvelope):
    """Tells the peer this side no longer wants the response to one of its requests. Advisory: the peer need not act."""

    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcNotificationMessage(RpcEnvelope):
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPingMessage(RpcEnvelope):
    """Answered with a pong carrying the same id by the receiving session itself, without involving its host."""

    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcPongMessage(RpcEnvelope):
    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcHelloMessage(RpcEnvelope):
    """
    A handshake greeting: opaque fields agreed between the peers, such as a protocol name, version, or instance id.
    Never sent by the session; only by an `RpcHandshakeIoPipelineHandler`, which also consumes the peer's.
    """

    fields: ta.Mapping[str, ta.Any]

    def __post_init__(self) -> None:
        if not isinstance(self.fields, ta.Mapping) or not all(isinstance(k, str) for k in self.fields):
            raise RpcProtocolError(f'hello fields must be a string-keyed mapping: {self.fields!r}')


##


class RpcInfoEvent(Abstract):
    """
    Marks an event an optional handler emits toward the host for whoever cares, such as a completed handshake. A
    connection which does not consume one passes it by quietly; any other event it does not recognize is a mistake, and
    warned of.
    """


##


class RpcSessionMessages(NamespaceClass):
    ##
    # commands: connection -> session

    class Command(
        IoPipelineMessages.NeverOutbound,
        IoPipelineMessages.AfterFinalInput,
        Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class SendRequest(Command):
        """
        Send a request and track its response. The request must already carry an id unique among this side's pending
        requests.

        A timeout of RpcUnspecified uses the session's default; None disables the timeout for this request.
        """

        request: RpcRequestMessage

        timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]] = RpcUnspecified

    @dc.dataclass(frozen=True)
    class SendNotification(Command):
        notification: RpcNotificationMessage

    @dc.dataclass(frozen=True)
    class SendResponse(Command):
        """Answer an in-flight inbound request. Exactly one response per inbound request is accepted."""

        response: RpcResponseMessage

    @dc.dataclass(frozen=True)
    class CancelRequest(Command):
        """
        Stop waiting for the response to a previously sent request. A late response is silently dropped.

        With `notify_peer` a cancel envelope is also sent, so the peer may stop handling it.
        """

        id: ta.Any

        notify_peer: bool = True

    @dc.dataclass(frozen=True)
    class SendPing(Command):
        """Send a ping and track its pong. The ping must carry an id unique among this side's pending pings."""

        ping: RpcPingMessage

        timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]] = RpcUnspecified

    @dc.dataclass(frozen=True)
    class Close(Command):
        """
        Close the session.

        A graceful close stops accepting new outbound requests, waits for pending outbound requests to be answered and
        for in-flight inbound requests to be answered by the host (up to the configured drain timeout), and then
        completes output. An abortive close fails and aborts everything immediately.
        """

        graceful: bool = True

    ##
    # events: session -> connection

    class Event(
        IoPipelineMessages.NeverInbound,
        IoPipelineMessages.AfterShutdownOutput,  # for the connection, not the peer: deliverable after an output half-close  # noqa
        Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class RequestReceived(Event):
        """The peer sent a request which must eventually be answered with a SendResponse."""

        request: RpcRequestMessage

    @dc.dataclass(frozen=True)
    class NotificationReceived(Event):
        notification: RpcNotificationMessage

    @dc.dataclass(frozen=True)
    class ResponseReceived(Event):
        """The peer answered a request sent with SendRequest."""

        request: RpcRequestMessage
        response: RpcResponseMessage

    @dc.dataclass(frozen=True)
    class RequestFailed(Event):
        """
        A sent request will never receive a response: it timed out, could not be encoded, exceeded a limit, or the
        session closed. Exactly one of ResponseReceived or RequestFailed is emitted per accepted SendRequest, unless the
        request was cancelled first.
        """

        request: RpcRequestMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class RequestHandlingAborted(Event):
        """
        The session stopped waiting for the host to answer an inbound request: the peer cancelled it, handling timed
        out, or the session is closing. Any SendResponse for it will be ignored, and the host should cancel its
        handler.
        """

        request: RpcRequestMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class PongReceived(Event):
        ping: RpcPingMessage
        pong: RpcPongMessage

    @dc.dataclass(frozen=True)
    class PingFailed(Event):
        """A sent ping will never be answered: it timed out, could not be encoded, or the session closed."""

        ping: RpcPingMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class Sent(Event):
        """
        A SendRequest, SendNotification, or SendPing has been fully handled and its bytes, if any, have crossed the
        transport boundary (the flush fence following it completed). Connections block sends on this, which is what
        makes backpressure real: a peer which stops reading stalls the sender rather than growing its buffers without
        bound.

        Not emitted for a command handled after the session closed; closure fails such sends instead.
        """

        command: 'RpcSessionMessages.Command'

    @dc.dataclass(frozen=True)
    class OutputPaused(Event):
        """The transport's write buffer is over its high watermark; the host should stop producing output."""

    @dc.dataclass(frozen=True)
    class OutputResumed(Event):
        """The transport's write buffer drained below its low watermark."""

    @dc.dataclass(frozen=True)
    class Closed(Event):
        """
        The session reached its terminal state. Emitted exactly once, after every pending request has been failed and
        every in-flight inbound request aborted, and before the session completes pipeline output. The exception, if
        any, is why the connection failed; a clean close carries None, and a graceful close which had to give up on
        in-flight work carries an RpcTimeoutError.
        """

        exc: ta.Optional[BaseException] = None

    ##
    # internal: codec -> session

    @dc.dataclass(frozen=True)
    class OutboundEncodeFailed(IoPipelineMessages.NeverOutbound):
        """
        The codec could not encode an outbound envelope, most often because its payload is not representable or it
        exceeded the maximum frame size.

        Rather than raising, which the pipeline would turn into a connection-fatal error, the codec drops the envelope
        and feeds this inward so the session can fail only the affected request or substitute an error response.
        """

        envelope: RpcEnvelope
        exc: Exception


########################################
# ../../../../omcore/rpc/runtime.py
"""
The runtime seam: the one place the sync and asyncio connections differ.

A connection is written once, async-colored, against this interface. Everything whose mechanics depend on how the
process waits and runs things is behind it: making a promise and waiting on it, starting the pump which steps the
pipeline driver and feeds its events back, running a handler, and cancelling one.

The sync runtime holds a sync-stepped driver. Waiting on one of its promises pumps the driver in the caller's thread
until the promise is done, and never actually suspends, so `sync_await` drives the whole stack. Handlers run inline,
one at a time, as the events which caused them are delivered. The asyncio runtime holds an asyncio driver, runs one
pump task, backs promises with futures, and runs handlers as tracked tasks. A future runtime for another loop - or a
callback-only one for a reactor which cannot wait - is a third implementation of this interface and nothing else.
"""


##


class RpcRuntimeSink(Abstract):
    """What a runtime feeds: the connection."""

    @abc.abstractmethod
    async def on_event(self, event: ta.Any) -> None:
        """
        An unhandled output of the pipeline driver, which for an rpc pipeline is a session event. Awaited on the pump,
        so inline work here holds up everything behind it in wire order.

        A raw exception output - which the session surfaces on a failing close, so it reaches the host even past a
        stalled transport flush - is not delivered here: the runtime takes it as the driver's failure, aborts the
        driver, and reports it through `on_driver_done`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def on_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        """
        The driver stopped running, cleanly or with the given failure. Called exactly once per started runtime: by the
        pump when the driver stops, or by `close` when the runtime is closed before that.
        """

        raise NotImplementedError


class RpcRuntime(Abstract):
    @property
    @abc.abstractmethod
    def is_started(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_driver_done(self) -> bool:
        """Whether the driver has stopped running; nothing enqueued after this will be processed."""

        raise NotImplementedError

    @abc.abstractmethod
    async def start(self, sink: RpcRuntimeSink) -> None:
        """Binds the sink and, where pumping is a background activity, starts it."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def make_promise(self) -> AsynclitePromise:
        """
        A promise whose `wait` behaves as the runtime does: by pumping the driver until it is done under a sync runtime,
        by suspending under an asyncio one. A wait timeout raises `AsynclitePromiseWaitTimeoutError`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def is_cancelled_exception(self, exc: BaseException) -> bool:
        """Whether an exception raised out of a handler means the handler's task was cancelled, not that it failed."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def enqueue(self, *commands: ta.Any) -> bool:
        """Hands commands to the driver, returning False if it is no longer accepting them."""

        raise NotImplementedError

    @abc.abstractmethod
    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        """
        Runs `fn` as a handler: inline, to completion, under a sync runtime; as a tracked task under asyncio, where
        `key` (if not None) identifies it to `cancel`. A handler's exceptions are its own business - `fn` is expected to
        report them to the peer itself - but a runtime observes and logs whatever escapes.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def cancel(self, key: ta.Any) -> None:
        """Cancels the handler spawned under `key`, if any and if still running. A no-op under a sync runtime."""

        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all(self) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    async def close(self) -> None:
        """Aborts the driver and cancels every spawned handler. Idempotent."""

        raise NotImplementedError

    @abc.abstractmethod
    async def wait_closed(self) -> None:
        """Waits until the pump and every spawned handler have finished. Only meaningful once the driver is done."""

        raise NotImplementedError


########################################
# ../../../../omcore/io/streambufs/framing.py


##


class LongestMatchDelimiterByteStreamFrameDecoder:
    """
    A delimiter-based framing codec that supports *overlapping* delimiters with longest-match semantics.

    This is intentionally decoupled from any I/O model: it operates purely on a `ByteStreamBuffer`-like object
    (providing `__len__`, `find`, `find_all_in_prefix`, `split_to`, `advance`, and `segments`/`peek`).

    Key property:
      Given overlapping delimiters like [b'\\r', b'\\r\\n'], this codec will *not* emit a frame ending at '\\r' unless
      it can prove the next byte is not '\\n' (or the stream is finalized).

    Implementation note:
      This codec relies on `ByteStreamBuffer.find(...)` being stream-correct and C-accelerated over the buffer's
      underlying contiguous segments. In pure Python it is usually better to keep searching near the storage layer than
      to re-implement scanning byte-by-byte in higher-level codecs. With a single delimiter (where no same-position
      ambiguity or mid-buffer deferral is possible) it batch-decodes all complete frames in the buffer's contiguous
      prefix via `find_all_in_prefix`, amortizing per-frame call overhead; cross-segment matches and the buffered tail
      go through the careful per-frame path.

    Pairs well with `ScanningByteStreamBuffer`.
    """

    def __init__(
            self,
            delims: ta.Sequence[bytes],
            *,
            keep_ends: bool = False,
            max_size: ta.Optional[int] = None,
    ) -> None:
        super().__init__()

        dl = list(delims)
        if not dl:
            raise ValueError('no delimiters')
        if any(not isinstance(d, (bytes, bytearray)) for d in dl):
            raise TypeError(delims)
        if any(not d for d in dl):
            raise ValueError('empty delimiter')

        self._delims = tuple(bytes(d) for d in dl)
        self._keep_ends = keep_ends
        self._max_size = max_size

        # Sort by length descending for "choose longest at same start".
        self._delims_by_len = tuple(sorted(self._delims, key=len, reverse=True))

        # Build prefix relationships for overlap deferral. For each short delimiter, store longer delimiters that start
        # with it.
        pref: ta.Dict[bytes, ta.List[bytes]] = {}
        for d in self._delims:
            for e in self._delims:
                if d is e:
                    continue
                if len(e) > len(d) and e.startswith(d):
                    pref.setdefault(d, []).append(e)
        for k, vs in list(pref.items()):
            pref[k] = sorted(vs, key=len, reverse=True)
        self._prefix_longer = pref

        self._max_delim_len = max(len(d) for d in self._delims)

    @ta.overload
    def decode(
            self,
            buf: ByteStreamBuffer,
            *,
            final: bool = False,
            include_delims: ta.Literal[True],
    ) -> ta.List[ta.Tuple[ByteStreamBufferView, bytes]]:
        ...

    @ta.overload
    def decode(
            self,
            buf: ByteStreamBuffer,
            *,
            final: bool = False,
            include_delims: ta.Literal[False] = False,
    ) -> ta.List[ByteStreamBufferView]:
        ...

    def decode(
            self,
            buf,
            *,
            final=False,
            include_delims=False,
    ):
        """
        Consume as many complete frames as possible from `buf` and return them as views.

        - Frames are produced without copying (via `buf.split_to(...)`) when possible.
        - The delimiter is consumed from the buffer; it may be retained on the frame if `keep_ends=True`.
        - If `final=True`, the codec will not defer on overlapping delimiter prefixes at the end of the buffer.

        Raises:
          - BufferTooLargeByteStreamBufferError if no delimiter is present and the buffered prefix exceeds max_size.
          - FrameTooLargeByteStreamBufferError if the next frame payload (bytes before delimiter) exceeds max_size.

        Note on `max_size`:
          `max_size` is enforced as a limit on the *current* frame (bytes before the next delimiter). If the buffer
          contains bytes for a subsequent frame that already exceed `max_size`, this codec will only raise when it would
          otherwise need to make progress on that oversized frame. Concretely: if this call already emitted at least one
          frame, it will return those frames rather than raising - frames already consumed from the buffer must never
          be lost to an exception. The error is then raised by the next call, when the offending frame is first in
          line and nothing has been consumed yet.
        """

        out: ta.List[ta.Any] = []

        # With a single delimiter there is no same-position ambiguity and no mid-buffer deferral, so all complete
        # frames within the buffer's contiguous prefix can be batch-decoded in a handful of bulk calls. Cross-segment
        # matches and the buffered tail still go through the careful per-frame path below.
        batch = len(self._delims) == 1

        while True:
            if batch:
                self._decode_prefix_batch(buf, out, include_delims=include_delims)

            hit = self._find_next_delim(buf)
            if hit is None:
                if self._max_size is not None and len(buf) > self._max_size and not out:
                    raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size without delimiter')
                return out

            pos, delim = hit

            if self._max_size is not None and pos > self._max_size:
                # Never lose already-consumed frames to an exception - return them, and raise on the next call.
                if out:
                    return out
                raise FrameTooLargeByteStreamBufferError('frame exceeded max_size')

            if not final and self._should_defer(buf, pos, delim):
                return out

            if self._keep_ends:
                frame = buf.split_to(pos + len(delim))
            else:
                frame = buf.split_to(pos)
                buf.advance(len(delim))

            if include_delims:
                out.append((frame, delim))
            else:
                out.append(frame)

    def _decode_prefix_batch(
            self,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            include_delims: bool,
    ) -> None:
        """
        Batch-decode all complete single-delimiter frames lying within the buffer's contiguous readable prefix.

        Per round, one `find_all_in_prefix` scan yields every delimiter hit, one `split_to` consumes through the last
        hit, and the frames are sliced as stable views out of that single split. This amortizes the per-frame call
        overhead of the general loop across all frames in the prefix.

        Stops (leaving the buffer positioned for the caller's per-frame path to take over) at: a frame exceeding
        max_size, a possible cross-segment match, or the incomplete buffered tail.
        """

        d = self._delims[0]
        dl = len(d)
        ms = self._max_size
        ke = self._keep_ends

        while True:
            hits = buf.find_all_in_prefix(d)
            if not hits:
                return

            # Stop before any frame exceeding max_size - the caller's per-frame path re-discovers it and applies the
            # error contract (return already-decoded frames first, raise on the next call).
            stopped = False
            if ms is not None:
                prev = 0
                for k, h in enumerate(hits):
                    if h - prev > ms:
                        hits = hits[:k]
                        stopped = True
                        break
                    prev = h + dl
                if not hits:
                    return

            consumed = hits[-1] + dl
            v = buf.split_to(consumed)
            mv = v.peek()
            if len(mv) < consumed:
                # Defensive: a split of a contiguous run should itself be contiguous for all in-repo buffers.
                mv = memoryview(v.tobytes())

            prev = 0
            for h in hits:
                fe = (h + dl) if ke else h
                fv: ByteStreamBufferView
                if fe > prev:
                    fv = DirectByteStreamBufferView(mv[prev:fe])
                else:
                    fv = _EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW
                out.append((fv, d) if include_delims else fv)
                prev = h + dl

            if stopped:
                return

            # Consuming through the last hit may have exposed a new contiguous prefix (the run ended exactly at a
            # segment boundary) - loop to rescan; otherwise the next scan comes up empty and returns.

    def _find_next_delim(self, buf: ByteStreamBuffer) -> ta.Optional[ta.Tuple[int, bytes]]:
        """
        Return (pos, delim) for the earliest delimiter occurrence. If multiple delimiters occur at the same position,
        choose the longest matching delimiter.
        """

        ln = len(buf)
        if not ln:
            return None

        # Single delimiter: no same-position ambiguity is possible.
        if len(self._delims) == 1:
            d = self._delims[0]
            if (i := buf.find(d, 0, None)) == -1:
                return None
            return i, d

        best_pos = None  # type: ta.Optional[int]
        best_delim = None  # type: ta.Optional[bytes]

        # First pass: find the earliest position of any delimiter (cheap, uses buf.find).
        for d in self._delims:
            i = buf.find(d, 0, None)
            if i == -1:
                continue
            if best_pos is None or i < best_pos:
                best_pos = i
                best_delim = d
                if not best_pos:
                    # Can't beat position 0; still need to choose longest at this position.
                    pass
            elif i == best_pos and best_delim is not None and len(d) > len(best_delim):
                best_delim = d

        if best_pos is None or best_delim is None:
            return None

        # Any two delimiters matching at the same position necessarily match the same bytes there, so one must be a
        # prefix of the other - and the first pass already tie-breaks same-position matches by length. So when no
        # prefix relationships exist among the delimiters at all, the first-pass winner is exact.
        if not self._prefix_longer:
            return best_pos, best_delim

        # Second pass: at that position, choose the longest delimiter that actually matches there. (We can't just rely
        # on "which delimiter found it first" when overlaps exist.)
        pos = best_pos
        for d in self._delims_by_len:
            if pos + len(d) > ln:
                continue
            if buf.find(d, pos, pos + len(d)) == pos:
                return pos, d

        # Shouldn't happen: best_pos came from some delimiter occurrence.
        return pos, best_delim

    def _should_defer(self, buf: ByteStreamBuffer, pos: int, matched: bytes) -> bool:
        """
        Return True if we must defer because a longer delimiter could still match starting at `pos` but we don't yet
        have enough bytes to decide.

        We only defer when:
          - there exists some longer delimiter that has `matched` as a prefix, and
          - not all of that longer delimiter's bytes are buffered from `pos` (had they been, `_find_next_delim` would
            have already decided), and
          - the buffered bytes from `pos` match the available prefix of that longer delimiter.

        Note that the current match ending *before* the end of the buffered bytes does not preclude deferral: a longer
        delimiter may extend more than one byte past the current match, with only part of that extension buffered
        (e.g. matched=b'\\r' with b'\\r\\n' buffered and a longer delimiter of b'\\r\\n\\r\\n').
        """

        longer = self._prefix_longer.get(matched)
        if not longer:
            return False

        avail = len(buf) - pos
        for d2 in longer:
            if avail >= len(d2):
                # If we had enough bytes, we'd have matched d2 in _find_next_delim.
                continue
            # Check whether buffered bytes match the prefix of d2 that we have available.
            # Use stream-correct find on the prefix.
            prefix = d2[:avail]
            if buf.find(prefix, pos, pos + avail) == pos:
                return True

        return False


##


class LengthFieldByteStreamFrameDecoder:
    """
    Decode length-prefixed frames from a BytesBuffer/MutableBytesBuffer.

    This is modeled after the common Netty pattern:
      total_frame_length = length_field_value + length_adjustment + length_field_end_offset
    where:
      length_field_end_offset = length_field_offset + length_field_length

    Parameters:
      - length_field_offset: byte offset of the length field from the start of the frame
      - length_field_length: length of the length field in bytes (1, 2, 4, or 8)
      - byteorder: 'big' or 'little'
      - length_adjustment: adjustment added to computed frame length (may be negative)
      - initial_bytes_to_strip: number of leading bytes to drop from the emitted frame (typically used to strip the
        length field and/or header from the delivered payload)
      - max_frame_length: maximum allowed total frame length (before stripping)

    Notes:
      - This decoder operates directly on the provided buffer and consumes bytes as frames are produced.
      - It relies on `buf.coalesce(n)` for efficient header parsing in pure Python.
      - It does not require async/await and is suitable for pipeline-style codecs.
    """

    def __init__(
            self,
            *,
            length_field_offset: int = 0,
            length_field_length: int = 4,
            byteorder: ta.Literal['little', 'big'] = 'big',
            length_adjustment: int = 0,
            initial_bytes_to_strip: int = 0,
            max_frame_length: ta.Optional[int] = None,
    ) -> None:
        super().__init__()

        if length_field_offset < 0:
            raise ValueError(length_field_offset)
        if length_field_length not in (1, 2, 4, 8):
            raise ValueError(length_field_length)
        if byteorder not in ('big', 'little'):
            raise ValueError(byteorder)
        if initial_bytes_to_strip < 0:
            raise ValueError(initial_bytes_to_strip)
        if max_frame_length is not None and max_frame_length < 0:
            raise ValueError(max_frame_length)

        self._off = int(length_field_offset)
        self._llen = int(length_field_length)
        self._byteorder = byteorder
        self._adj = int(length_adjustment)
        self._strip = int(initial_bytes_to_strip)
        self._max = None if max_frame_length is None else int(max_frame_length)

        self._end_off = self._off + self._llen

    def decode(self, buf: ByteStreamBuffer) -> ta.List[ByteStreamBufferView]:
        """
        Consume as many complete frames as possible from `buf` and return them as views.

        Returns:
          - list of BytesView-like objects (from `split_to`) representing each decoded frame

        Raises:
          - FrameTooLarge if a frame exceeds max_frame_length
          - BufferTooLarge if max_frame_length is set and the buffered unread prefix grows beyond it without making
            progress (defensive; rarely hit if upstream caps buffer growth)
          - ValueError on frames whose computed total length is negative, smaller than the length field end offset, or
            smaller than initial_bytes_to_strip (a corrupt stream - decoding cannot resynchronize)

        If frames were already decoded by the current call, they are returned instead of raising - frames already
        consumed from the buffer must never be lost to an exception. The error is then raised by the next call, when
        the offending frame is first in line and nothing has been consumed yet.
        """

        out: ta.List[ta.Any] = []

        while True:
            # Need at least enough bytes to read the length field.
            if len(buf) < self._end_off:
                return out

            # Read header up through the length field contiguously.
            # IMPORTANT: don't keep exported memoryviews alive across buffer mutation.
            mv = buf.coalesce(self._end_off)
            if len(mv) < self._end_off:
                # Defensive: coalesce contract.
                return out

            # Copy just the length field bytes (1/2/4/8) so we can safely mutate the buffer afterward.
            lf_bytes = bytes(mv[self._off:self._end_off])
            # del mv

            length_val = int.from_bytes(lf_bytes, self._byteorder, signed=False)

            total_len = length_val + self._adj + self._end_off
            if total_len < 0:
                if out:
                    return out
                raise ValueError('negative frame length')

            # A frame shorter than its own header would leave part of the header unconsumed and permanently desync
            # the stream (Netty rejects this as a corrupted frame too).
            if total_len < self._end_off:
                if out:
                    return out
                raise ValueError('frame length less than length field end offset')

            if self._max is not None and total_len > self._max:
                if out:
                    return out
                raise FrameTooLargeByteStreamBufferError('frame exceeded max_frame_length')

            # If we don't have the full frame yet, either wait or (optionally) fail fast if buffering is clearly out of
            # control.
            if len(buf) < total_len:
                if self._max is not None and len(buf) > self._max:
                    if out:
                        return out
                    raise BufferTooLargeByteStreamBufferError(
                        'buffer exceeded max_frame_length without completing a frame',
                    )
                return out

            # We have a complete frame available.
            if self._strip:
                if self._strip > total_len:
                    if out:
                        return out
                    raise ValueError('initial_bytes_to_strip > frame length')
                buf.advance(self._strip)
                total_len -= self._strip

            out.append(buf.split_to(total_len))

            # Loop for additional frames


########################################
# ../../../../omcore/io/streambufs/segmented.py


##


class SegmentedByteStreamBufferView(BaseByteStreamBufferLike, ByteStreamBufferView):
    """
    A read-only, possibly non-contiguous view over a sequence of byte segments.

    This is intended to be produced by `SegmentedByteStreamBuffer.split_to()` without copying.
    """

    def __init__(self, segs: ta.Sequence[memoryview]) -> None:
        super().__init__()

        self._segs = tuple(segs)
        for mv in self._segs:
            if (mvl := len(mv)) < 1:
                raise ValueError('Empty segment')
            self._len += mvl

    @classmethod
    def of_opt(cls, segs: ta.Sequence[memoryview]) -> ta.Optional['SegmentedByteStreamBufferView']:
        if not segs:
            return None
        return cls(segs)

    @classmethod
    def or_else(cls, segs: ta.Sequence[memoryview], default: T) -> ta.Union['SegmentedByteStreamBufferView', T]:
        if not segs:
            return default
        return cls(segs)

    _len = 0

    def __len__(self) -> int:
        return self._len

    def peek(self) -> memoryview:
        if not self._segs:
            return memoryview(b'')
        return self._segs[0]

    def segments(self) -> ta.Sequence[memoryview]:
        return self._segs

    def tobytes(self) -> Bytes:
        if not self._segs:
            return b''
        if len(self._segs) == 1:
            return memoryview_to_bytes(self._segs[0])
        return b''.join(memoryview_to_bytes(mv) for mv in self._segs)


class SegmentedByteStreamBuffer(BaseByteStreamBufferLike, MutableByteStreamBuffer):
    """
    A segmented, consumption-oriented bytes buffer.

    Internally stores a list of `bytes`/`bytearray` segments plus a head offset. Exposes readable data as `memoryview`
    segments without copying.

    Optional "chunked writes":
      - If chunk_size > 0, small writes are accumulated into a lazily-allocated active bytearray "chunk" up to
        chunk_size.
      - Writes >= chunk_size are stored as their own segments (after flushing any active chunk).
      - On flush, the active chunk is kept as a bytearray segment iff it is at least `chunk_compact_threshold` full;
        otherwise it is materialized as bytes to avoid pinning a large capacity for tiny content.

    Reserve/commit:
      - If chunk_size > 0 and reserve(n) fits in the active chunk, the reservation is carved from the active chunk.
        Reserved bytes are not readable until commit().
      - If reserve(n) does not fit, the active chunk is flushed first.
      - If n <= chunk_size after flushing, the reservation is served from a new active chunk (so the remainder becomes
        the next active chunk).
      - If n > chunk_size, reserve allocates a dedicated buffer and on commit it is "closed" (it does not become the
        next active chunk).
      - While a reservation is outstanding, write/prepend-into-active/advance/split_to/coalesce raise
        OutstandingReserveByteStreamBufferError; commit() (possibly commit(0) to abandon) releases it. Non-mutating
        reads (peek/segments/find/etc.) remain valid and observe only readable bytes.

    Important exported-view caveat:
      - reserve() returns a memoryview. As long as any exported memoryview exists, the underlying bytearray must not be
        resized, or Python will raise BufferError. Therefore the active chunk bytearray is *fixed capacity*
        (len==chunk_size) and we track "used" bytes separately, writing via slice assignment rather than extend().
    """

    def __init__(
            self,
            *,
            max_size: ta.Optional[int] = None,
            chunk_size: int = 0,
            chunk_compact_threshold: float = .25,
    ) -> None:
        super().__init__()

        self._segs: ta.List[Bytes] = []

        self._max_size = None if max_size is None else int(max_size)

        if chunk_size < 0:
            raise ValueError(chunk_size)
        self._chunk_size = chunk_size

        if not (0.0 <= chunk_compact_threshold <= 1.0):
            raise ValueError(chunk_compact_threshold)
        self._chunk_compact_threshold = chunk_compact_threshold

    _active: ta.Optional[bytearray] = None
    _active_used = 0

    @property
    def max_size(self) -> ta.Optional[int]:
        return self._max_size

    _head_off = 0
    _len = 0

    _reserved: ta.Optional[bytearray] = None
    _reserved_len = 0
    _reserved_in_active = False

    #

    def __len__(self) -> int:
        return self._len

    def _active_readable_len(self) -> int:
        if self._active is None:
            return 0
        # An in-active reservation is carved *beyond* _active_used and only becomes readable at commit() (which then
        # advances _active_used), so readable bytes are always exactly _active_used.
        return self._active_used

    def peek(self) -> memoryview:
        if not self._segs:
            return memoryview(b'')

        s0 = self._segs[0]
        mv = memoryview(s0)
        if self._head_off:
            mv = mv[self._head_off:]

        if s0 is self._active:
            # Active is only meaningful by _active_used, not len(bytearray).
            rl = self._active_readable_len()
            if self._head_off >= rl:
                return memoryview(b'')
            mv = memoryview(self._active)[self._head_off:rl]
            return mv

        return mv

    def segments(self) -> ta.Sequence[memoryview]:
        if not self._segs:
            return ()

        out: ta.List[memoryview] = []

        last_i = len(self._segs) - 1
        for i, s in enumerate(self._segs):
            if s is self._active and i == last_i:
                # Active chunk: create fresh view with readable length.
                rl = self._active_readable_len()
                if not i:
                    # Active is also first segment; apply head_off.
                    if self._head_off >= rl:
                        continue
                    mv = memoryview(self._active)[self._head_off:rl]
                else:
                    if rl <= 0:
                        continue
                    mv = memoryview(self._active)[:rl]
            else:
                # Non-active segment.
                mv = memoryview(s)
                if not i and self._head_off:
                    mv = mv[self._head_off:]

            if len(mv):
                out.append(mv)

        return out

    #

    def _check_no_reserve(self) -> None:
        if self._reserved is not None:
            raise OutstandingReserveByteStreamBufferError('outstanding reserve')

    def _ensure_active(self) -> bytearray:
        if self._chunk_size <= 0:
            raise RuntimeError('no active chunk without chunk_size')

        a = self._active
        if a is None:
            a = bytearray(self._chunk_size)  # fixed capacity
            self._segs.append(a)
            self._active = a
            self._active_used = 0

        return a

    def _flush_active(self) -> None:
        if (a := self._active) is None:
            return

        if self._reserved_in_active:
            raise OutstandingReserveByteStreamBufferError('outstanding reserve')

        if (used := self._active_used) <= 0:
            if self._segs and self._segs[-1] is a:
                self._segs.pop()
            self._active = None
            self._active_used = 0
            return

        # If under threshold, always bytes() to avoid pinning.
        if self._chunk_size and (float(used) / float(self._chunk_size)) < self._chunk_compact_threshold:
            if not self._segs or self._segs[-1] is not a:
                raise RuntimeError('active not at tail')
            self._segs[-1] = memoryview_to_bytes(memoryview(a)[:used])

        else:
            # Try to shrink in-place to used bytes. If exported views exist, this can BufferError; fall back to bytes()
            # in that case.
            if not self._segs or self._segs[-1] is not a:
                raise RuntimeError('active not at tail')
            try:
                del a[used:]  # may raise BufferError if any exports exist
            except BufferError:
                self._segs[-1] = memoryview_to_bytes(memoryview(a)[:used])

        self._active = None
        self._active_used = 0

    def write(self, data: BytesLike, /) -> None:
        self._check_no_reserve()
        if not data:
            return
        if isinstance(data, memoryview):
            data = memoryview_to_bytes(data)  # noqa
        # elif isinstance(data, bytearray):
        #     pass
        # else:
        #     pass

        dl = len(data)

        if self._max_size is not None and self._len + dl > self._max_size:
            raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size')

        if self._chunk_size <= 0:
            self._segs.append(data)
            self._len += dl
            return

        if dl >= self._chunk_size:
            self._flush_active()
            self._segs.append(data)
            self._len += dl
            return

        a = self._ensure_active()
        if self._active_used + dl > self._chunk_size:
            self._flush_active()
            a = self._ensure_active()

        # Copy into fixed-capacity buffer; do not resize.
        memoryview(a)[self._active_used:self._active_used + dl] = data
        self._active_used += dl
        self._len += dl

    def prepend(self, data: BytesLike, /) -> None:
        # Note: unlike write/advance/split_to, prepend is safe with an outstanding reserve as long as it does not need
        # to reshape the active chunk - it only inserts a segment at the front.
        if not data:
            return
        if isinstance(data, memoryview):
            data = memoryview_to_bytes(data)  # noqa

        dl = len(data)

        if self._max_size is not None and self._len + dl > self._max_size:
            raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size')

        if self._head_off:
            s0 = self._segs[0]
            if s0 is self._active:
                if self._reserved_in_active:
                    raise OutstandingReserveByteStreamBufferError('outstanding reserve')
                rl = self._active_readable_len()
                if self._head_off < rl:
                    self._segs[0] = memoryview_to_bytes(memoryview(self._active)[self._head_off:rl])
                else:
                    self._segs.pop(0)
                self._active = None
                self._active_used = 0
            else:
                self._segs[0] = s0[self._head_off:]
            self._head_off = 0

        self._segs.insert(0, data)
        self._len += dl

    def reserve(self, n: int, /) -> memoryview:
        if n < 0:
            raise ValueError(n)
        if self._reserved is not None:
            raise OutstandingReserveByteStreamBufferError('outstanding reserve')

        if self._chunk_size <= 0:
            b = bytearray(n)
            self._reserved = b
            self._reserved_len = n
            self._reserved_in_active = False
            return memoryview(b)

        if n > self._chunk_size:
            self._flush_active()
            b = bytearray(n)
            self._reserved = b
            self._reserved_len = n
            self._reserved_in_active = False
            return memoryview(b)

        # Ensure reservation fits in active; otherwise flush then create a new one.
        if self._active is not None and (self._active_used + n > self._chunk_size):
            self._flush_active()

        a = self._ensure_active()

        start = self._active_used
        # Reservation does not change _active_used (not readable until commit).
        self._reserved = a
        self._reserved_len = n
        self._reserved_in_active = True
        return memoryview(a)[start:start + n]

    def commit(self, n: int, /) -> None:
        if self._reserved is None:
            raise NoOutstandingReserveByteStreamBufferError('no outstanding reserve')
        if n < 0 or n > self._reserved_len:
            raise ValueError(n)

        if self._reserved_in_active:
            a = self._reserved
            self._reserved = None
            self._reserved_len = 0
            self._reserved_in_active = False

            if self._max_size is not None and self._len + n > self._max_size:
                raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size')

            if n:
                self._active_used += n
                self._len += n

            # Keep active for reuse.
            self._active = a
            return

        b = self._reserved
        self._reserved = None
        self._reserved_len = 0
        self._reserved_in_active = False

        if self._max_size is not None and self._len + n > self._max_size:
            raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size')

        if not n:
            return

        if n == len(b):
            self._segs.append(b)
            self._len += n
        else:
            bb = memoryview_to_bytes(memoryview(b)[:n])
            self._segs.append(bb)
            self._len += n

    #

    def advance(self, n: int, /) -> None:
        self._check_no_reserve()
        if n < 0 or n > self._len:
            raise ValueError(n)
        if not n:
            return

        self._len -= n

        while n and self._segs:
            s0 = self._segs[0]

            if s0 is self._active:
                avail0 = self._active_readable_len() - self._head_off
            else:
                avail0 = len(s0) - self._head_off

            if avail0 <= 0:
                popped = self._segs.pop(0)
                if popped is self._active:
                    self._active = None
                    self._active_used = 0
                self._head_off = 0
                continue

            if n < avail0:
                self._head_off += n
                return

            n -= avail0
            popped = self._segs.pop(0)
            if popped is self._active:
                self._active = None
                self._active_used = 0
            self._head_off = 0

        if n:
            raise RuntimeError(n)

    def split_to(self, n: int, /) -> ByteStreamBufferView:
        self._check_no_reserve()
        if n < 0 or n > self._len:
            raise ValueError(n)
        if not n:
            return _EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW

        # Fast path: the split lies strictly within the first segment - no segment list manipulation needed.
        s0 = self._segs[0]
        if s0 is self._active:
            avail0 = self._active_readable_len() - self._head_off
        else:
            avail0 = len(s0) - self._head_off
        if n < avail0:
            mv = memoryview(s0)[self._head_off:self._head_off + n]
            self._head_off += n
            self._len -= n
            return DirectByteStreamBufferView(mv)

        out: ta.List[memoryview] = []
        rem = n

        while rem:
            if not self._segs:
                raise RuntimeError(rem)

            s0 = self._segs[0]

            if s0 is self._active:
                rl = self._active_readable_len()
                if self._head_off >= rl:
                    raise RuntimeError(rem)
                mv0 = memoryview(s0)[self._head_off:rl]
            else:
                mv0 = memoryview(s0)
                if self._head_off:
                    mv0 = mv0[self._head_off:]

            if rem < len(mv0):
                out.append(mv0[:rem])
                self._head_off += rem
                self._len -= n
                return byte_stream_buffer_view_from_segments(out)

            out.append(mv0)
            rem -= len(mv0)
            popped = self._segs.pop(0)
            if popped is self._active:
                self._active = None
                self._active_used = 0
            self._head_off = 0

        self._len -= n
        return byte_stream_buffer_view_from_segments(out)

    def coalesce(self, n: int, /) -> memoryview:
        if n < 0:
            raise ValueError(n)
        if n > self._len:
            raise ValueError(n)
        if not n:
            return memoryview(b'')

        self._check_no_reserve()

        mv0 = self.peek()
        if len(mv0) >= n:
            return mv0[:n]

        out = bytearray(n)
        w = 0

        new_segs: ta.List[Bytes] = []
        active_touched = False

        seg_i = 0
        while w < n and seg_i < len(self._segs):
            s = self._segs[seg_i]
            off = self._head_off if not seg_i else 0

            seg_len = len(s) - off
            if s is self._active and seg_i == (len(self._segs) - 1):
                seg_len = self._active_readable_len() - off

            if seg_len <= 0:
                seg_i += 1
                continue

            take = n - w
            if take > seg_len:
                take = seg_len

            if s is self._active:
                # Once bytes are pulled out of the active chunk it can no longer serve as the write tail: a partial
                # remainder is copied below, so the original fixed-capacity bytearray must not be reused.
                active_touched = True

            out[w:w + take] = memoryview(s)[off:off + take]
            w += take

            if take < seg_len:
                rem = s[off + take:off + seg_len]
                if rem:
                    new_segs.append(rem)
                seg_i += 1
                break

            seg_i += 1

        if seg_i < len(self._segs):
            # Untouched trailing segments carry over as-is - including the active chunk, whose fixed-capacity
            # bytearray must NOT be demoted to a plain segment (its unused capacity would become 'readable').
            new_segs.extend(self._segs[seg_i:])

        self._segs = [bytes(out), *new_segs]
        self._head_off = 0

        if active_touched:
            self._active = None
            self._active_used = 0

        return memoryview(self._segs[0])[:n]

    def _seg_readable_slice(
            self,
            si: int,
            s: Bytes,
            last_i: int,
    ) -> ta.Tuple[int, int]:
        """
        Compute the readable offset and length for segment at index si.

        Returns (offset, readable_len) where:
          - offset: byte offset into segment (head_off for si==0, else 0)
          - readable_len: number of readable bytes from offset (0 if segment empty/consumed)

        Handles head offset for first segment and active chunk readable length for last segment.
        """

        off = self._head_off if not si else 0
        seg_len = len(s) - off
        if s is self._active and si == last_i:
            seg_len = self._active_readable_len() - off
        return off, max(0, seg_len)

    def _seg_search_range(
            self,
            start: int,
            limit: int,
            m: int,
            seg_gs: int,
            seg_ge: int,
            seg_len: int,
    ) -> ta.Optional[ta.Tuple[int, int]]:
        """
        Compute local search range within a segment.

        Args:
            start: global start position (user-provided)
            limit: global limit (end - m, last valid position where match can start)
            m: pattern length
            seg_gs: segment global start position
            seg_ge: segment global end position
            seg_len: segment readable length

        Returns (local_start, local_end) if segment overlaps search range, else None.
          - local_start: offset within segment to start searching
          - local_end: offset within segment to end searching (exclusive)
        """

        # Check if segment overlaps search range
        if limit < seg_gs or start >= seg_ge:
            return None

        # Compute local start within segment
        ls = max(0, start - seg_gs)

        # Compute local end: can start match anywhere up to limit, need m bytes
        max_start_in_seg = limit - seg_gs
        end_search = min(max_start_in_seg + m, seg_len)

        # Validate range
        if ls >= end_search:
            return None

        return ls, end_search

    def find_all_in_prefix(self, sub: bytes, start: int = 0) -> ta.Sequence[int]:
        if not sub:
            raise ValueError('empty sub')
        if start < 0:
            raise ValueError(start)

        if not self._segs:
            return ()

        s0 = self._segs[0]
        off = self._head_off
        if s0 is self._active:
            rl = self._active_readable_len()
        else:
            rl = len(s0)

        out: ta.List[int] = []
        append = out.append
        find = s0.find
        m = len(sub)
        pos = off + start
        while (i := find(sub, pos, rl)) >= 0:
            append(i - off)
            pos = i + m
        return out

    def find(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        start, end = self._norm_slice(start, end)

        m = len(sub)
        if m == 0:
            return start
        if end - start < m:
            return -1

        limit = end - m

        # Fast path: with zero or one segment there is no cross-boundary logic to run. This is the common case in
        # chunked mode, where trickle writes accumulate into a single active chunk.
        if not self._segs:
            return -1
        if len(self._segs) == 1:
            s = self._segs[0]
            off, seg_len = self._seg_readable_slice(0, s, 0)
            if seg_len <= 0:
                return -1
            end_search = min(limit + m, seg_len)
            if start >= end_search:
                return -1
            idx = s.find(sub, off + start, off + end_search)
            return (idx - off) if idx >= 0 else -1

        tail: Bytes = b''
        tail_gstart = 0

        gpos = 0

        last_i = len(self._segs) - 1

        for si, s in enumerate(self._segs):
            off, seg_len = self._seg_readable_slice(si, s, last_i)
            if seg_len <= 0:
                continue

            seg_gs = gpos
            seg_ge = gpos + seg_len

            # Cross-boundary check first: matches spanning into this segment start in the previous one, so they come
            # before any within-segment match.
            if m > 1 and tail:
                head_need = m - 1
                # Only read as many bytes as are actually available in this segment to avoid reading uninitialized data
                # from active chunks.
                head_avail = min(head_need, seg_len)
                if head_avail > 0:
                    head = s[off:off + head_avail]
                    comb = tail + head
                    # Walk *all* candidates in the stitched window: an early candidate may be rejected by the
                    # start/limit bounds (or lie entirely within the head) while a later one is still valid.
                    j = comb.find(sub)
                    while j != -1:
                        if j < len(tail) < j + m:
                            cand = tail_gstart + j
                            if start <= cand <= limit:
                                return cand
                        j = comb.find(sub, j + 1)

            # Within-segment search
            search_range = self._seg_search_range(start, limit, m, seg_gs, seg_ge, seg_len)
            if search_range is not None:
                ls, end_search = search_range
                idx = s.find(sub, off + ls, off + end_search)
                if idx != -1:
                    return seg_gs + (idx - off)

            if m > 1:
                take = m - 1
                if seg_len >= take:
                    tail = s[off + seg_len - take:off + seg_len]
                    tail_gstart = seg_ge - take
                else:
                    tail = (tail + s[off:off + seg_len])[-(m - 1):]
                    tail_gstart = seg_ge - len(tail)

            gpos = seg_ge

        return -1

    def rfind(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        start, end = self._norm_slice(start, end)

        m = len(sub)
        if m == 0:
            return end
        if end - start < m:
            return -1

        limit = end - m

        if not self._segs:
            return -1

        # Fast path: with one segment there is no cross-boundary logic to run.
        if len(self._segs) == 1:
            s = self._segs[0]
            off, seg_len = self._seg_readable_slice(0, s, 0)
            if seg_len <= 0:
                return -1
            end_search = min(limit + m, seg_len)
            if start >= end_search:
                return -1
            idx = s.rfind(sub, off + start, off + end_search)
            return (idx - off) if idx >= 0 else -1

        best = -1

        seg_ge = self._len
        prev_s: ta.Optional[Bytes] = None
        prev_off = 0
        prev_seg_len = 0

        last_i = len(self._segs) - 1

        for si in range(len(self._segs) - 1, -1, -1):
            s = self._segs[si]
            off, seg_len = self._seg_readable_slice(si, s, last_i)
            if seg_len <= 0:
                continue

            seg_gs = seg_ge - seg_len

            # Within-segment search
            search_range = self._seg_search_range(start, limit, m, seg_gs, seg_ge, seg_len)
            if search_range is not None:
                ls, end_search = search_range
                idx = s.rfind(sub, off + ls, off + end_search)
                if idx != -1:
                    cand = seg_gs + (idx - off)
                    if cand > best:
                        best = cand

            if m > 1 and prev_s is not None:
                tail_need = m - 1
                if seg_len >= tail_need:
                    tail = s[off + seg_len - tail_need:off + seg_len]
                    tail_gstart = seg_ge - tail_need

                else:
                    tail_parts = [s[off:off + seg_len]]
                    tail_len = seg_len
                    for sj in range(si - 1, -1, -1):
                        if tail_len >= tail_need:
                            break

                        sj_s = self._segs[sj]
                        sj_off, sj_len = self._seg_readable_slice(sj, sj_s, last_i)
                        if sj_len <= 0:
                            continue

                        take = min(tail_need - tail_len, sj_len)
                        tail_parts.insert(0, sj_s[sj_off + sj_len - take:sj_off + sj_len])
                        tail_len += take

                    tail_combined = b''.join(tail_parts)
                    tail = tail_combined[-(m - 1):] if len(tail_combined) >= m - 1 else tail_combined
                    tail_gstart = seg_ge - len(tail)

                head_need = m - 1
                # Only read as many bytes as are actually available in prev segment to avoid reading uninitialized data
                # from active chunks.
                head_avail = min(head_need, prev_seg_len)
                if head_avail > 0:
                    head = prev_s[prev_off:prev_off + head_avail]
                else:
                    head = b''

                comb = tail + head
                # Walk candidates in descending order: the last candidate may be rejected by the start/limit bounds
                # (or lie entirely within the head) while an earlier one is still valid.
                j = comb.rfind(sub)
                while j != -1:
                    if j < len(tail) < j + m:
                        cand = tail_gstart + j
                        if start <= cand <= limit:
                            if cand > best:
                                best = cand
                            break
                    j = comb.rfind(sub, 0, j + m - 1)

            if best >= seg_gs:
                return best

            prev_s = s
            prev_off = off
            prev_seg_len = seg_len
            seg_ge = seg_gs

        return best


##


def byte_stream_buffer_view_from_segments(mvs: ta.Sequence[memoryview]) -> ByteStreamBufferView:
    if not mvs:
        return _EMPTY_DIRECT_BYTE_STREAM_BUFFER_VIEW
    elif len(mvs) == 1:
        return DirectByteStreamBufferView(mvs[0])
    else:
        return SegmentedByteStreamBufferView(mvs)


########################################
# ../../../../omcore/logs/asyncs.py


##


class AsyncLoggerToLogger(Logger):
    def __init__(self, u: AsyncLogger) -> None:
        super().__init__()

        self._u = u

    def get_effective_level(self) -> LogLevel:
        return self._u.get_effective_level()

    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> None:
        # Nope out early to avoid sync_await if possible - don't bother in the LoggerToAsyncLogger.
        if not self.is_enabled_for(ctx.must_get_info(LoggingContextInfos.Level).level):
            return

        # Note: we hardcode the stack offset of sync_await (which is 2 - sync_await + sync_await.thunk). In non-lite
        # code, lang.sync_await uses a cext if present to avoid being on the py stack, which would obviously complicate
        # this, but this is lite code so we will always have the non-c version.
        sync_await(
            self._u._log(  # noqa
                check.isinstance(ctx, CaptureLoggingContextImpl).inc_stack_offset(3),
                msg,
                *args,
                **kwargs,
            ),
        )

    def _metric(self, m: LoggerMetric) -> None:
        sync_await(self._u._metric(m))  # noqa


class LoggerToAsyncLogger(AsyncLogger):
    def __init__(self, u: Logger) -> None:
        super().__init__()

        self._u = u

    def get_effective_level(self) -> LogLevel:
        return self._u.get_effective_level()

    async def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
            **kwargs: ta.Any,
    ) -> None:
        self._u._log(  # noqa
            check.isinstance(ctx, CaptureLoggingContextImpl).inc_stack_offset(),
            msg,
            *args,
            **kwargs,
        )

    async def _metric(self, m: LoggerMetric) -> None:
        self._u._metric(m)  # noqa


########################################
# ../../../../omcore/logs/std/loggers.py


##


class StdLogger(Logger):
    def __init__(self, std: logging.Logger) -> None:
        super().__init__()

        self._std = std

    @property
    def std(self) -> logging.Logger:
        return self._std

    def is_enabled_for(self, level: LogLevel) -> bool:
        return self._std.isEnabledFor(level)

    def get_effective_level(self) -> LogLevel:
        return self._std.getEffectiveLevel()

    def _log(
            self,
            ctx: CaptureLoggingContext,
            msg: ta.Union[str, tuple, LoggingMsgFn],
            *args: ta.Any,
    ) -> None:
        if not self.is_enabled_for(ctx.must_get_info(LoggingContextInfos.Level).level):
            return

        ctx.set_basic(
            name=self._std.name,

            msg=msg,
            args=args,
        )

        ctx.capture()

        rec = LoggingContextLogRecord(_logging_context=ctx)

        self._std.handle(rec)

    def _metric(self, m: LoggerMetric) -> None:
        pass


########################################
# ../../../../omcore/rpc/keepalive.py
"""
An optional keepalive handler, installed between the envelope codec and the session only when configured.

After `interval_s` without receiving any envelope it sends a ping; if nothing at all is received within `timeout_s` of
that, it fails the connection with a timeout error, which the session treats as fatal. Any received envelope counts as
liveness, so an actively used connection never pings. Pongs answering this handler's own pings are consumed here and
never reach the session; the session answers the peer's pings itself.

Ping ids are drawn from a private string space so they never collide with the ids the connection issues for its own
explicit pings.
"""


##


class RpcKeepaliveIoPipelineHandler(IoPipelineHandler):
    ID_PREFIX: ta.ClassVar[str] = 'rpc-keepalive:'

    def __init__(
            self,
            *,
            interval_s: float,
            timeout_s: float,
    ) -> None:
        super().__init__()

        for t in (interval_s, timeout_s):
            if not math.isfinite(t) or t <= 0.:
                raise ValueError(t)
        self._interval_s = interval_s
        self._timeout_s = timeout_s

        self._ids = itertools.count(1)
        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._outstanding: ta.Optional[str] = None
        self._active = False
        self._failed = False

    @property
    def outstanding_ping_id(self) -> ta.Optional[str]:
        return self._outstanding

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext, delay_s: float) -> None:
        self._cancel()
        self._handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            delay_s,
            lambda ctx2: check.isinstance(ctx2.handler, RpcKeepaliveIoPipelineHandler)._on_timer(ctx2),  # noqa
        )

    def _on_activity(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._active or self._failed:
            return
        self._outstanding = None
        self._arm(ctx, self._interval_s)

    def _on_timer(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._active or self._failed:
            return

        if self._outstanding is not None:
            self._failed = True
            ctx.feed_in(IoPipelineMessages.Error(
                RpcTimeoutError(f'keepalive timed out: no traffic within {self._timeout_s:g}s of ping'),
                direction='inbound',
                handler=ctx.ref,
            ))
            return

        pid = f'{self.ID_PREFIX}{next(self._ids)}'
        self._outstanding = pid
        ctx.feed_out(RpcPingMessage(pid))
        if not self._is_live(ctx):
            return
        IoPipelineFlow.maybe_flush_output(ctx)
        if not self._is_live(ctx):
            return
        self._arm(ctx, self._timeout_s)

    def _is_live(self, ctx: IoPipelineHandlerContext) -> bool:
        # Feeding output can reentrantly close the pipeline or remove this handler.
        return not ctx.invalidated and self._active and not self._failed

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            check.not_none(ctx.services.find(IoPipelineScheduling))
            self._cancel()
            self._active = False
            self._failed = False
            self._outstanding = None

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._active = False
            self._cancel()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._active = True
            self._failed = False
            self._outstanding = None
            self._arm(ctx, self._interval_s)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._active = False
            self._cancel()

        elif isinstance(msg, RpcEnvelope):
            if isinstance(msg, RpcPongMessage) and isinstance(msg.id, str) and msg.id.startswith(self.ID_PREFIX):
                self._on_activity(ctx)
                return

            self._on_activity(ctx)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._active = False
            self._cancel()

        ctx.feed_out(msg)


########################################
# ../../../../omcore/io/pipelines/bytes/buffers.py


##


@ta.final
class OutboundBytesBufferIoPipelineHandler(OutboundBytesBufferingIoPipelineHandler):
    @ta.final
    @dc.dataclass(frozen=True)
    class Config:
        flush_threshold: ta.Optional[int] = 8 * 1024
        max_buffer_size: ta.Optional[int] = None
        buffer_chunk_size: int = 64 * 1024

        write_high_watermark: int = 64 * 1024
        write_low_watermark: int = 16 * 1024

        DEFAULT: ta.ClassVar['OutboundBytesBufferIoPipelineHandler.Config']

        def __post_init__(self) -> None:
            """Validate output writability watermarks."""

            if not (0 <= self.write_low_watermark <= self.write_high_watermark):
                raise ValueError((self.write_low_watermark, self.write_high_watermark))

    Config.DEFAULT = Config()

    def __init__(self, config: ta.Optional[Config] = None) -> None:
        super().__init__()

        if config is None:
            config = self.Config.DEFAULT
        self._config = config

        self._downstream_writable = True
        self._self_writable = True
        self._announced_writable = True

    #

    _buf: ta.Optional[MutableByteStreamBuffer] = None

    def _new_buf(self) -> MutableByteStreamBuffer:
        return SegmentedByteStreamBuffer(
            max_size=self._config.max_buffer_size,
            chunk_size=self._config.buffer_chunk_size,
        )

    def outbound_buffered_bytes(self) -> ta.Optional[int]:
        if (buf := self._buf) is None:
            return 0
        return len(buf)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            # This handler *requires* flow
            check.not_none(no.ctx.services.find(IoPipelineFlow))

    #

    def _update_writability(self, ctx: IoPipelineHandlerContext) -> None:
        size = check.not_none(self.outbound_buffered_bytes())
        if self._self_writable:
            if size > self._config.write_high_watermark:
                self._self_writable = False

        elif size <= self._config.write_low_watermark:
            self._self_writable = True

        effective = self._downstream_writable and self._self_writable
        if effective != self._announced_writable:
            self._announced_writable = effective
            ctx.feed_in(
                IoPipelineFlowMessages.ReadyForOutput() if effective
                else IoPipelineFlowMessages.PauseOutput(),
            )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._downstream_writable = True
            self._update_writability(ctx)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._downstream_writable = False
            self._update_writability(ctx)

        else:
            ctx.feed_in(msg)

    #

    def _flush(self, ctx: IoPipelineHandlerContext, *, no_announce_writability: bool = False) -> None:
        if (buf := self._buf) is None or len(buf) == 0:
            return

        # The bytes no longer belong to this handler before any downstream call. This matters when an outer handler
        # synchronously re-announces writability while receiving a segment.
        self._buf = None

        ctx.feed_out(buf.split_to(len(buf)))

        if not no_announce_writability:
            self._update_writability(ctx)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineMessages.FinalOutput, IoPipelineMessages.ShutdownOutput)):
            # Draining here can leave us writable again, but announcing that would invite a reentrant write which
            # could only land after the fence - and be rejected, since no ordinary output may follow either.
            self._flush(ctx, no_announce_writability=True)
            ctx.feed_out(msg)

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            self._flush(ctx)
            ctx.feed_out(msg)

        elif ByteStreamBuffers.can_bytes(msg):
            # Buffer the bytes
            if (buf := self._buf) is None:
                buf = self._buf = self._new_buf()

            for seg in ByteStreamBuffers.iter_segments(msg):
                if seg:
                    buf.write(seg)

            # Check if we should flush based on threshold
            if (
                (threshold := self._config.flush_threshold) is not None and
                len(buf) >= threshold
            ):
                self._flush(ctx)
            else:
                self._update_writability(ctx)

        else:
            ctx.feed_out(msg)


########################################
# ../../../../omcore/io/pipelines/bytes/decoders.py
"""
TODO: Dynamic decoder removal / Netty pending-removal semantics.

The recirculation in ``BytesToMessageDecoderIoPipelineHandler._call_decode`` does not implement Netty's
``STATE_HANDLER_REMOVED_PENDING`` trick. It solves a different ordering problem: reentrant ``FlushInput`` and
``FinalInput`` messages are queued until the active decode and its output delivery finish. Reentrant byte input is not
queued; it either uses the explicitly enabled reentrant-decode path or raises ``RuntimeError``.

Netty's ``ByteToMessageDecoder`` has separate protection for removal during ``decode()``. If removal is requested while
the decoder is on the stack, it marks removal pending. After ``decode()`` returns, it first forwards any messages that
were already decoded, then runs removal cleanup and forwards the remaining undecoded cumulation as raw bytes. Netty's
reentrant ``channelRead`` input queue is the mechanism analogous to the recirculation here, not its pending-removal
state.

This cannot be fixed entirely inside this decoder. ``IoPipeline._remove`` currently unlinks and invalidates a context,
and deletes its neighbor links, before notifying the handler that it was removed. Consequently the old context cannot be
used to finish delivering decoded output or to drain residual bytes. In particular:

 - A decoder which removes itself from ``_decode`` can fail in ``ctx.feed_in`` because ``_next_in`` was deleted.
 - If a downstream handler removes the decoder while consuming the first of multiple decoded messages, the first can be
   delivered while delivery of the rest fails.
 - Removing a buffered decoder with unread cumulation silently strands those bytes in the removed handler.
 - The eventual ``Removed`` notification is too late to drain through the handler's former pipeline position.

The topology-mutation contract should be decided in the core before implementing a decoder-local removal state. The
recommended contract is:

 1. Removal requested during a handler invocation becomes pending rather than immediately destroying its routing
    context.
 2. Already-produced messages retain their order and are forwarded before removal cleanup. 3. A pre-unlink removal phase
    has a stable successor route through which handler-owned state can be drained or transferred. Ordinary handler
    callbacks must not resume after the handler has entered removal.
 4. A buffered byte decoder forwards its remaining undecoded cumulation as raw bytes, matching Netty and supporting
    protocol-upgrade boundaries such as STARTTLS.
 5. Stateful protocol transforms such as compression and TLS either define safe drainage/completion semantics or reject
    removal outside a quiescent state.
 6. Outbound buffers likewise need an explicit drain, failure, or rejection policy; removal must not silently lose
    bytes, pending flush/final fences, or a previously announced paused state.

Dynamic addition also needs a flow-state contract. Output writability is currently communicated as edges, while a newly
inserted buffering handler initializes its downstream as writable. If it is inserted while downstream is already paused,
it misses that edge and can later announce a false ``ReadyForOutput`` when its local buffer drains (and can emit a
duplicate ``PauseOutput`` while filling). Either current downstream writability must be queryable/replayed on addition,
or live mutation must be constrained to a defined quiescent point with a known writable baseline.

Coverage associated with this work should include:

 - Core add/remove/replace during both inbound and outbound handler calls, including self-removal, downstream-triggered
   removal during multi-message delivery, notification ordering, exception behavior, stable successor routing, and
   reference release with cyclic GC disabled.
 - Decoder removal while idle, with unread cumulation, from inside ``_decode`` after producing zero/one/multiple
   messages, from downstream while consuming the first decoded message, and with reentrant flush/final messages queued.
 - Decoder replacement across a byte-split protocol-upgrade boundary.
 - Outbound-buffer removal while empty, nonempty, locally paused, and downstream-paused; addition while downstream is
   paused; replacement of one buffering handler by another; and pending ``FlushOutput``/``FinalOutput`` completion.
 - The corresponding pending-state cases for chunking, compression, decompression, and TLS, with tests documenting which
   transforms permit live removal and which require quiescence.

Existing tests cover ordinary topology changes and steady-state buffering/watermark behavior, but do not exercise these
interactions. Do not remove this to-do merely because input recirculation exists; it represents a broader, currently
undefined topology-mutation and buffered-state contract.
"""


##


class UnicodeDecoderIoPipelineHandler(IoPipelineHandler):
    """bytes/view -> str (UTF-8, replacement)."""

    def __init__(
            self,
            encoding: str = 'utf-8',
            *,
            errors: ta.Literal['strict', 'ignore', 'replace'] = 'strict',
    ) -> None:
        super().__init__()

        self._encoding = encoding
        self._errors = errors

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if ByteStreamBuffers.can_bytes(msg):
            b = ByteStreamBuffers.to_bytes(msg)

            msg = b.decode(self._encoding, errors=self._errors)

        ctx.feed_in(msg)


##


class DelimiterFrameDecoderIoPipelineHandler(InboundBytesBufferingIoPipelineHandler):
    """
    bytes-like -> frames using longest-match delimiter semantics.

    In manual-read mode a read which completes no frame leaves the reader's request unsatisfied, so the decoder asks
    the transport for more itself (as the buffered decoders do).

    TODO:
     - replace with BytesToMessageDecoderIoPipelineHandler
    """

    _decoded_since_flush = False   # bytes arrived since the last FlushInput ...
    _produced_since_flush = False  # ... and at least one frame was produced from them

    def __init__(
            self,
            delims: ta.Sequence[bytes],
            *,
            keep_ends: bool = False,
            max_size: ta.Optional[int] = None,
            max_buffer: ta.Optional[int] = None,
            buffer_chunk_size: int = 64 * 1024,
            on_incomplete_final: ta.Literal['allow', 'raise'] = 'allow',
    ) -> None:
        super().__init__()

        self._on_incomplete_final = on_incomplete_final

        self._buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(
            max_size=max_buffer,
            chunk_size=buffer_chunk_size,
        ))

        self._fr = LongestMatchDelimiterByteStreamFrameDecoder(
            delims,
            keep_ends=keep_ends,
            max_size=max_size,
        )

    def inbound_buffered_bytes(self) -> int:
        return len(self._buf)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._produce_frames(ctx, final=True)
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            decoded, produced = self._decoded_since_flush, self._produced_since_flush
            self._decoded_since_flush = self._produced_since_flush = False
            if decoded and not produced:
                # The read completed no frame: whoever asked for one is still waiting on it.
                IoPipelineFlow.maybe_ready_for_input(ctx)
            ctx.feed_in(msg)
            return

        if not ByteStreamBuffers.can_bytes(msg):
            ctx.feed_in(msg)
            return

        for mv in ByteStreamBuffers.iter_segments(msg):
            if mv:
                self._buf.write(mv)

        self._decoded_since_flush = True
        self._produce_frames(ctx)

    def _produce_frames(self, ctx: IoPipelineHandlerContext, *, final: bool = False) -> None:
        frames = self._fr.decode(self._buf, final=final)
        if frames:
            self._produced_since_flush = True

        if final and len(self._buf):
            if (oif := self._on_incomplete_final) == 'allow':
                frames.append(self._buf.split_to(len(self._buf)))
            elif oif == 'raise':
                raise IncompleteDecodingIoPipelineError
            else:
                raise RuntimeError(f'unexpected on_incomplete_final: {oif!r}')

        for fr in frames:
            ctx.feed_in(fr)


##


class BytesToMessageDecoderIoPipelineHandler(IoPipelineHandler, Abstract):
    @abc.abstractmethod
    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        raise NotImplementedError

    #

    _decode_state: ta.Literal['ready', 'decoding'] = 'ready'

    _allow_decode_reentrance: bool = False
    _decode_output: ta.Optional['collections.deque[ta.Any]'] = None
    _decode_pending_input: ta.Optional['collections.deque[ta.Any]'] = None

    _called_decode: bool = False  # ~ `selfFiredChannelRead`
    _produced_messages: bool = False  # ~ `firedChannelRead`

    def _call_decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            *,
            final: bool = False,
    ) -> None:
        if self._decode_state == 'ready':
            check.none(self._decode_output)
            check.none(self._decode_pending_input)

            self._decode_state = 'decoding'
            doq: 'collections.deque[ta.Any]' = collections.deque()
            diq: 'collections.deque[ta.Any]' = collections.deque()
            self._decode_output = doq
            self._decode_pending_input = diq

            self._called_decode = True

            try:
                out: ta.List[ta.Any] = []
                self._decode(ctx, data, out, final=final)
                doq.extend(out)

                if doq:
                    self._produced_messages = True

                    while doq:
                        out_msg = doq.popleft()
                        ctx.feed_in(out_msg)

            finally:
                self._decode_output = None
                self._decode_pending_input = None
                self._decode_state = 'ready'

            # Replay only on success: running flush / final processing mid-unwind would drive the decoder against a
            # pipeline already handling the error, and any exception it raised would replace the original one.
            while diq:
                in_msg = diq.popleft()
                self.inbound(ctx, in_msg)

        elif self._decode_state == 'decoding':
            if not self._allow_decode_reentrance:
                raise RuntimeError('already decoding')

            doq = check.not_none(self._decode_output)

            out = []
            self._decode(ctx, data, out, final=final)
            doq.extend(out)

        else:
            raise RuntimeError(f'unexpected decode state: {self._decode_state!r}')

    #

    def _on_bytes_input(self, ctx: IoPipelineHandlerContext, data: CanByteStreamBuffer) -> None:
        check.arg(len(data) > 0)

        self._call_decode(ctx, data)

    def _on_flush_input(self, ctx: IoPipelineHandlerContext) -> None:
        if (
                self._called_decode and
                not self._produced_messages and
                not ctx.services[IoPipelineFlow].is_auto_read()
        ):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

        self._called_decode = False
        self._produced_messages = False

        ctx.feed_in(IoPipelineFlowMessages.FlushInput())

    def _on_final_input(self, ctx: IoPipelineHandlerContext, msg: IoPipelineMessages.FinalInput) -> None:
        self._call_decode(ctx, DirectByteStreamBuffer(b''), final=True)

        ctx.feed_in(msg)

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            if (diq := self._decode_pending_input) is not None:
                diq.append(msg)
            else:
                self._on_flush_input(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            if (diq := self._decode_pending_input) is not None:
                diq.append(msg)
            else:
                self._on_final_input(ctx, msg)

        elif ByteStreamBuffers.can_bytes(msg):
            self._on_bytes_input(ctx, msg)

        else:
            ctx.feed_in(msg)


#


@ta.final
class FnBytesToMessageDecoderIoPipelineHandler(BytesToMessageDecoderIoPipelineHandler):
    class DecodeFn(ta.Protocol):
        def __call__(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> None:
            ...

    def __init__(
            self,
            decode_fn: DecodeFn,
    ) -> None:
        super().__init__()

        self._decode_fn = decode_fn

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            buf: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        self._decode_fn(ctx, buf, out, final=final)


##


class BufferedBytesToMessageDecoderIoPipelineHandler(
    InboundBytesBufferingIoPipelineHandler,
    BytesToMessageDecoderIoPipelineHandler,
    Abstract,
):
    def __init__(
            self,
            *,
            max_buffer_size: ta.Optional[int] = None,
            buffer_chunk_size: int = 64 * 1024,
            scanning_buffer: bool = False,
    ) -> None:
        super().__init__()

        self._max_buffer_size = max_buffer_size
        self._buffer_chunk_size = buffer_chunk_size
        self._scanning_buffer = scanning_buffer

    #

    def inbound_buffered_bytes(self) -> int:
        if (buf := self._buf) is None:
            return 0
        return len(buf)

    _buf: ta.Optional[MutableByteStreamBuffer] = None

    def _new_buf(self) -> MutableByteStreamBuffer:
        buf: MutableByteStreamBuffer = SegmentedByteStreamBuffer(
            max_size=self._max_buffer_size,
            chunk_size=self._buffer_chunk_size,
        )

        if self._scanning_buffer:
            buf = ScanningByteStreamBuffer(buf)

        return buf

    #

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        if final:
            check.arg(len(data) == 0)

            # ~ Netty `decodeLast`: the cumulation is presented, not an empty sentinel, so subclasses can flush or
            # reject a truncated trailing frame. Anything left afterwards is stranded by definition.
            final_buf: ByteStreamBuffer
            if (cum := self._buf) is not None:
                final_buf = cum
            elif isinstance(data, ByteStreamBuffer):
                final_buf = data
            else:
                final_buf = DirectByteStreamBuffer(b'')

            self._decode_buffer(ctx, final_buf, out, final=final)

            if cum is not None and not len(cum):
                self._buf = None

            return

        check.arg(len(data) > 0)

        if (max_size := self._max_buffer_size) is not None:
            buffered = len(self._buf) if self._buf is not None else 0
            if buffered + len(data) > max_size:
                raise BufferTooLargeByteStreamBufferError('buffer exceeded max_size')

        write_data = True
        if (buf := self._buf) is None and isinstance(data, ByteStreamBuffer):
            if isinstance(data, MutableByteStreamBuffer):
                buf = data
                if self._scanning_buffer and not isinstance(buf, ScanningByteStreamBuffer):
                    buf = ScanningByteStreamBuffer(buf)
                self._buf = buf
                write_data = False

            else:
                self._decode_buffer(ctx, data, out)
                if not len(data):
                    return

                buf = self._buf = self._new_buf()
                for seg in data.segments():
                    buf.write(seg)

                return

        elif buf is None:
            buf = self._buf = self._new_buf()

        if write_data:
            for seg in ByteStreamBuffers.iter_segments(data):
                buf.write(seg)

        self._decode_buffer(ctx, buf, out, final=final)
        if not len(buf):
            self._buf = None

    #

    @abc.abstractmethod
    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        raise NotImplementedError


########################################
# ../../../../omcore/logs/modules.py


##


def _get_module_std_logger(mod_globals: ta.Mapping[str, ta.Any]) -> logging.Logger:
    return logging.getLogger(mod_globals.get('__name__'))


def get_module_logger(mod_globals: ta.Mapping[str, ta.Any]) -> Logger:
    return StdLogger(_get_module_std_logger(mod_globals))


def get_module_async_logger(mod_globals: ta.Mapping[str, ta.Any]) -> AsyncLogger:
    return LoggerToAsyncLogger(get_module_logger(mod_globals))


def get_module_loggers(mod_globals: ta.Mapping[str, ta.Any]) -> ta.Tuple[Logger, AsyncLogger]:
    return (
        log := get_module_logger(mod_globals),
        LoggerToAsyncLogger(log),
    )


########################################
# ../../../../omcore/io/pipelines/drivers/asyncio/streams.py


log, alog = get_module_loggers(globals())  # noqa


##


class PollAsyncioStreamIoPipelineDriver(IoPipelinePostingTarget):
    """
    An asyncio pipeline driver with a poll-based interface mirroring the sync driver's API. Unlike
    LoopAsyncioStreamIoPipelineDriver which runs its own internal event loop via run(), this driver exposes next() and
    loop_until_done() methods that let the caller control stepping. Unhandled pipeline output messages are returned from
    next(), enabling streaming use cases.

    ShutdownOutput calls the writer's `write_eof()`, which the transport performs after the bytes already written, and
    completes after the following drain - the same transport-boundary guarantee FlushOutput receives. A writer which
    cannot write EOF fails the message with UnsupportedIoPipelineError and is left intact. Reading continues afterwards.

    The driver is task-stable: besides whatever task steps it, it runs one task reading the transport and one draining
    it (which also performs the graceful close), both for its whole life. Timers use the heap scheduler the other
    drivers use, with one loop timer handle armed for the earliest deadline, which wakes the command loop with a
    command. Only an Await supplied as a coroutine becomes a task of its own, since it must run concurrently.

    Enqueued messages, posted work, and completed reads are commands on one queue, processed in order; a post wakes a
    driver waiting on it.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['PollAsyncioStreamIoPipelineDriver.Config']

        read_chunk_size: int = 64 * 1024
        read_batch_max_bytes: int = 1024 * 1024
        read_batch_max_reads: int = 16
        write_chunk_max: ta.Optional[int] = None

        strict_input_flow: bool = False

        write_high_watermark: int = 64 * 1024
        write_low_watermark: int = 16 * 1024

        def __post_init__(self) -> None:
            """Validate I/O chunk sizes and output writability watermarks."""

            if self.read_chunk_size < 1:
                raise ValueError(self.read_chunk_size)
            if self.read_batch_max_bytes < 1:
                raise ValueError(self.read_batch_max_bytes)
            if self.read_batch_max_reads < 1:
                raise ValueError(self.read_batch_max_reads)
            if self.write_chunk_max is not None and self.write_chunk_max < 1:
                raise ValueError(self.write_chunk_max)
            if not (0 <= self.write_low_watermark <= self.write_high_watermark):
                raise ValueError((self.write_low_watermark, self.write_high_watermark))

    Config.DEFAULT = Config()

    #

    def __init__(
            self,
            spec: IoPipeline.Spec,
            reader: asyncio.StreamReader,
            writer: ta.Optional[asyncio.StreamWriter] = None,
            config: ta.Optional[Config] = None,
            *,
            _pipeline_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        super().__init__()

        self._spec = spec
        self._reader = reader
        self._writer = writer
        self._closing_writer: ta.Optional[asyncio.StreamWriter] = None
        if config is None:
            config = PollAsyncioStreamIoPipelineDriver.Config.DEFAULT
        self._config = config
        self._pipeline_kwargs = _pipeline_kwargs

        #

        self._shutdown_event = asyncio.Event()
        self._command_queue: asyncio.Queue = asyncio.Queue()

        self._state = IoPipelineDriverState.NEW
        self._has_init = False
        self._loop: ta.Optional[asyncio.AbstractEventLoop] = None

        # The one task which calls the writer's drain(), and performs the graceful close, woken through an event. A
        # drain is requested with a flag; the fences (FlushOutput and ShutdownOutput) requested before it is called are
        # the ones it completes. A drain is outstanding from its start until its completion command has been handled.
        # The idle event is set while the drainer has nothing requested or running.
        self._drainer_task: ta.Optional[asyncio.Task] = None
        self._drainer_event = asyncio.Event()
        self._drain_requested = False
        self._drains_outstanding = 0
        self._drain_idle_event = asyncio.Event()
        self._drain_idle_event.set()
        self._pending_drain_fences: ta.List[IoPipelineMessages.Completable] = []
        self._post_drain_output_q: collections.deque[ta.Any] = collections.deque()
        # Output bytes held behind a pending drain count toward writability as much as the transport's own buffer.
        self._post_drain_output_bytes = 0

        # Pending awaits, each marked whether the driver created its task (from a coroutine) and so owns it.
        self._pending_awaits: ta.Dict[asyncio.Future, bool] = {}

        # The graceful close is performed by the drainer task once FinalOutput reached the terminal, so commands -
        # timers, awaits, reads to discard - are serviced while the transport flushes.
        self._close_requested = False
        self._close_in_progress = False
        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None
        self._saved_write_limits: ta.Optional[ta.Tuple[int, int]] = None

        # The loop timer armed for the scheduler's earliest deadline: a timer handle, not a task.
        self._timer_handle: ta.Optional[asyncio.TimerHandle] = None
        self._timer_deadline: ta.Optional[float] = None

        self._read_task: ta.Optional[asyncio.Task] = None
        self._want_read = False
        self._want_read_event = asyncio.Event()
        self._has_read_eof: bool = False

        self._output_writable = True
        self._output_shutdown = False

        self._command_handlers: ta.Mapping[ta.Type['PollAsyncioStreamIoPipelineDriver._Command'], ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]]]  # noqa
        self._output_handlers: ta.Mapping[type, ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]]]

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand([
            IoPipelineMessages.InitialInput(),
        ]))

        # Usable before the pipeline exists: a post made then runs once it does.
        self._posting = TargetIoPipelinePostingService(self)

    _sched: HeapIoPipelineSchedulingService

    _pipeline: IoPipeline

    _flow: ta.Optional[IoPipelineFlow]

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> Config:
        return self._config

    @property
    def state(self) -> IoPipelineDriverState:
        return self._state

    @property
    def pipeline(self) -> IoPipeline:
        return self._pipeline

    @property
    def posting(self) -> TargetIoPipelinePostingService:
        """The pipeline's posting service, usable from construction on."""

        return self._posting

    @property
    def is_running(self) -> bool:
        return (
            self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
            hasattr(self, '_pipeline') and
            self._pipeline.is_ready
        )

    @property
    def output_shutdown(self) -> bool:
        """Whether a ShutdownOutput has shut down the writer's output half."""

        return self._output_shutdown

    ##
    # init

    async def _ensure_init(self) -> IoPipeline:
        if self._has_init:
            return self._pipeline
        check.state(self._state is IoPipelineDriverState.NEW)
        self._has_init = True

        try:
            return self._init()

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            self._shutdown_event.set()

            try:
                if self._pipeline.is_ready:
                    self._pipeline.destroy()
            except AttributeError:
                pass

            await self._abort_writer()
            raise

    def _init(self) -> IoPipeline:
        self._loop = loop = asyncio.get_running_loop()
        self._sched = HeapIoPipelineSchedulingService(
            loop.time,
            on_earliest_change=functools.partial(
                PollAsyncioStreamIoPipelineDriver._on_sched_earliest_change,
                weakref.ref(self),
            ),
        )

        services = IoPipelineServices.of(self._spec.services)
        self._flow = services.find(IoPipelineFlow)

        self._command_handlers = self._build_command_handlers()
        self._output_handlers = self._build_output_handlers()

        #

        self._pipeline = IoPipeline(
            dc.replace(
                self._spec,
                metadata=(*self._spec.metadata, DriverIoPipelineMetadata(self)),
                services=(*self._spec.services, self._sched, self._posting),
            ),
            **(self._pipeline_kwargs or {}),
        )

        if self._flow is not None and self._writer is not None:
            self._writer.transport.set_write_buffer_limits(
                high=self._config.write_high_watermark,
                low=self._config.write_low_watermark,
            )

        #

        self._read_task = asyncio.create_task(self._read_task_main())
        if self._writer is not None:
            self._drainer_task = asyncio.create_task(self._drainer_task_main())

        if self._is_auto_read():
            self._want_read = True
            self._want_read_event.set()

        self._state = IoPipelineDriverState.RUNNING

        return self._pipeline

    def _is_auto_read(self) -> bool:
        return (flow := self._flow) is None or flow.is_auto_read()

    ##
    # async utils

    def _own_loop_running(self) -> bool:
        """
        Whether the driver's own loop is the one running here - the only case in which `close()` may wait for what it
        cancels. Closed from anywhere else - a coroutine closed by garbage collection once its loop is gone, say, or a
        caller on another loop - it does its bookkeeping without suspending, and without touching a closed loop.
        """

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            return False
        if (loop := self._loop) is None:
            return True  # Not yet initialized: whichever loop runs here is as good as any.
        return running is loop and not loop.is_closed()

    def _loop_closed(self) -> bool:
        return (loop := self._loop) is not None and loop.is_closed()

    def _cancel_tasks_now(self, *tasks: ta.Optional[asyncio.Future]) -> ta.List[asyncio.Future]:
        """Cancels the tasks without awaiting them, returning those cancelled so they may be waited for."""

        if self._loop_closed():
            return []  # Nothing can run any more, and a closed loop refuses the cancellation's callbacks.

        cts: ta.List[asyncio.Future] = []
        try:
            # A driver-owned Await's task may be the one closing the driver: it is not cancelled from under itself.
            current: ta.Optional[asyncio.Future] = asyncio.current_task()
        except RuntimeError:
            current = None

        for t in tasks:
            if t is not None and t is not current and not t.done():
                t.cancel()
                cts.append(t)

        return cts

    @staticmethod
    async def _wait_cancelled(tasks: ta.Sequence[asyncio.Future]) -> None:
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _cancel_tasks(
            self,
            *tasks: ta.Optional[asyncio.Future],
            wait: bool = True,
    ) -> None:
        cts = self._cancel_tasks_now(*tasks)
        if wait:
            await self._wait_cancelled(cts)

    #

    async def _gracefully_close_writer(self) -> None:
        """
        Flushes everything written, then closes the transport. Closing it first would stop it reading at once, and a
        peer which has yet to read this side's output may be waiting for its own to be read first.
        """

        if self._writer is None:
            return

        writer = self._writer
        self._writer = None
        self._closing_writer = writer

        try:
            buffered = writer.transport.get_write_buffer_size()
        except AttributeError:
            # An SSL transport whose underlying transport is already gone (3.8): nothing is left to flush, and the
            # close reports what became of the connection.
            buffered = 0

        if buffered > 0:
            # Zero watermarks make the drain return once the buffer is empty rather than at the low watermark.
            self._set_write_limits(writer, high=0, low=0)
            await writer.drain()

        writer.close()
        # Cancelling a wait on the transport's close cancels the transport's own close waiter, which every later wait
        # would then raise from: the wait itself is shielded, and an abort completes it.
        await asyncio.shield(writer.wait_closed())
        if self._closing_writer is writer:
            self._closing_writer = None

    @staticmethod
    def _set_write_limits(writer: asyncio.StreamWriter, *, high: int, low: int) -> None:
        try:
            writer.transport.set_write_buffer_limits(high=high, low=low)
        except (AttributeError, NotImplementedError):
            pass

    def _abort_writer_now(self) -> ta.Optional[asyncio.StreamWriter]:
        """Aborts the transport without awaiting its close, returning the writer so the close may be waited for."""

        writer = self._writer
        if writer is None:
            writer = self._closing_writer
        if writer is None:
            return None

        self._writer = None
        self._closing_writer = None

        try:
            try:
                writer.transport.abort()
            except (AttributeError, NotImplementedError):
                writer.close()

        except Exception:  # noqa
            pass

        return writer

    @staticmethod
    async def _wait_writer_closed(writer: ta.Optional[asyncio.StreamWriter]) -> None:
        if writer is None:
            return

        try:
            await writer.wait_closed()
        except Exception:  # noqa
            pass

    async def _abort_writer(self, *, wait: bool = True) -> None:
        writer = self._abort_writer_now()
        if wait:
            await self._wait_writer_closed(writer)

    ##

    class _Command(Abstract):
        pass

    ##
    # feed in

    @dc.dataclass(frozen=True)
    class _FeedInCommand(_Command):
        msgs: ta.Sequence[ta.Any]

        fut: ta.Optional['asyncio.Future[None]'] = None

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}([{", ".join(map(repr, self.msgs))}])'

    async def _handle_command_feed_in(self, cmd: _FeedInCommand) -> None:
        try:
            self._pipeline.feed_in(*cmd.msgs)

        except BaseException as e:
            # The waiter may have been cancelled meanwhile; the queued input is still processed.
            if (fut := cmd.fut) is not None and not fut.done():
                fut.set_exception(e)
            raise

        else:
            if (fut := cmd.fut) is not None and not fut.done():
                fut.set_result(None)

    def enqueue_waitable(self, *msgs: ta.Any) -> 'asyncio.Future[None]':
        check.state(self._state in (IoPipelineDriverState.NEW, IoPipelineDriverState.RUNNING))

        fut: asyncio.Future[None] = asyncio.Future()
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs, fut=fut))
        return fut

    def enqueue(self, *msgs: ta.Any) -> None:
        check.state(self._state in (IoPipelineDriverState.NEW, IoPipelineDriverState.RUNNING))

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs))

    ##
    # posting

    @dc.dataclass(frozen=True)
    class _PostCommand(_Command):
        post: IoPipelinePost

    def accept_post(self, post: IoPipelinePost) -> None:
        if self._state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED):
            raise ClosedIoPipelinePostingError(f'{self!r} is {self._state.name}')
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._PostCommand(post))

    async def _handle_command_post(self, cmd: _PostCommand) -> None:
        cmd.post.run(self._pipeline)

    ##
    # read task

    async def _read_task_main(self) -> None:
        try:
            while not self._shutdown_event.is_set():
                # In manual flow mode, wait for ReadyForInput to signal via _want_read_event.
                if not self._is_auto_read():
                    await self._want_read_event.wait()

                    if self._shutdown_event.is_set():
                        break

                    self._want_read_event.clear()

                try:
                    data = await self._reader.read(min(
                        self._config.read_batch_max_bytes,
                        self._config.read_chunk_size * self._config.read_batch_max_reads,
                    ))
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa
                    if not self._shutdown_event.is_set():
                        self._command_queue.put_nowait(
                            PollAsyncioStreamIoPipelineDriver._ReadFailedCommand(e),
                        )
                    break

                if self._shutdown_event.is_set():
                    break

                self._command_queue.put_nowait(
                    PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand(data),
                )

                if not data:  # EOF
                    break

        except asyncio.CancelledError:
            pass

    ##
    # read completed

    class _ReadCompletedCommand(_Command):
        def __init__(self, data: ta.Union[bytes, ta.List[bytes]]) -> None:
            self._data = data

        def __repr__(self) -> str:
            return (
                f'{self.__class__.__name__}@{id(self):x}'
                f'({"[...]" if isinstance(self._data, list) else "..." if self._data else ""})'
            )

        def data(self) -> ta.Sequence[bytes]:
            if isinstance(self._data, bytes):
                return [self._data]
            elif isinstance(self._data, list):
                return self._data
            else:
                raise TypeError(self._data)

    @dc.dataclass(frozen=True)
    class _ReadFailedCommand(_Command):
        exc: BaseException

    async def _handle_command_read_completed(self, cmd: _ReadCompletedCommand) -> None:
        if self._state is IoPipelineDriverState.DRAINING:
            # Nothing consumes input any more, but it is still taken off the transport (and dropped) so a peer blocked
            # on this side reading can proceed to read this side's remaining output.
            if self._flow is not None and not self._is_auto_read():
                self._want_read_event.set()
            return

        eof = False
        data: ta.List[bytes] = []

        in_msgs: ta.List[ta.Any] = []

        for b in cmd.data():
            check.state(not eof)
            if not b:
                eof = True
            else:
                data.append(b)

        if data:
            if len(data) == 1:
                in_msgs.append(DirectByteStreamBuffer(data[0]))
            else:
                buf = SegmentedByteStreamBuffer()
                for b in data:
                    buf.write(b)
                in_msgs.append(buf)

        if data and self._flow is not None:
            in_msgs.append(IoPipelineFlowMessages.FlushInput())

        if self._flow is not None:
            self._want_read = False

        if eof:
            self._has_read_eof = True

            in_msgs.append(IoPipelineMessages.FinalInput())

        #

        self._pipeline.feed_in(*in_msgs)

        #

    async def _handle_command_read_failed(self, cmd: _ReadFailedCommand) -> None:
        raise cmd.exc

    ##
    # scheduling

    def _arm_timer(self) -> None:
        """
        Arms one loop timer for the scheduler's earliest deadline, which wakes the command loop with a command, unless
        one is already armed for it. A wake at a since cancelled deadline runs nothing and is harmless.
        """

        if (loop := self._loop) is None or loop.is_closed():
            return

        deadline = self._sched.next_deadline()
        if deadline == self._timer_deadline:
            return

        if (th := self._timer_handle) is not None:
            self._timer_handle = None
            th.cancel()

        self._timer_deadline = deadline
        if deadline is not None and not self._shutdown_event.is_set():
            self._timer_handle = loop.call_at(
                deadline,
                PollAsyncioStreamIoPipelineDriver._on_timer,
                weakref.ref(self),
            )

    def _disarm_timer(self) -> None:
        self._timer_deadline = None
        if (th := self._timer_handle) is not None:
            self._timer_handle = None
            th.cancel()

    @staticmethod
    def _on_sched_earliest_change(
            d_ref: ta.Callable[[], ta.Optional['PollAsyncioStreamIoPipelineDriver']],
    ) -> None:
        if (d := d_ref()) is not None:
            d._arm_timer()  # noqa

    @staticmethod
    def _on_timer(
            d_ref: ta.Callable[[], ta.Optional['PollAsyncioStreamIoPipelineDriver']],
    ) -> None:
        if (d := d_ref()) is None:
            return

        d._timer_handle = None  # noqa
        d._timer_deadline = None  # noqa
        if not d._shutdown_event.is_set():  # noqa
            d._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._TimerCommand())  # noqa

    class _TimerCommand(_Command):
        pass

    async def _handle_command_timer(self, cmd: _TimerCommand) -> None:
        self._sched.run_due()

    ##
    # shutdown

    class _ShutdownCommand(_Command):
        pass

    ##
    # deferred continuations

    @dc.dataclass(frozen=True)
    class _DeferCommand(_Command):
        msg: IoPipelineMessages.Defer

    async def _handle_command_defer(self, cmd: _DeferCommand) -> None:
        # A deferred continuation is a fairness yield: the timers due go first.
        self._sched.run_due()
        if self._pipeline.is_ready:
            self._pipeline.run_deferred(cmd.msg)

    ##
    # graceful close

    @dc.dataclass(frozen=True)
    class _CloseCompletedCommand(_Command):
        exc: ta.Optional[BaseException] = None

    @property
    def _close_pending(self) -> bool:
        return self._close_requested or self._close_in_progress

    def _request_close(self) -> None:
        """Asks the drainer task to perform the graceful close, after any drain it has pending."""

        self._close_requested = True
        self._drainer_event.set()

    def _fail_graceful_close(self, exc: BaseException) -> None:
        self._finish_flush_outputs(
            self._take_pending_drain_fences(),
            exc,
            raise_listener_errors=False,
        )
        if (msg := self._transport_final_output) is not None:
            self._transport_final_output = None
            self._finish_final_output(msg, exc, raise_listener_errors=False)

    async def _complete_graceful_close(self) -> None:
        msg = check.not_none(self._transport_final_output)
        self._transport_final_output = None

        try:
            self._finish_flush_outputs(self._take_pending_drain_fences())
        finally:
            self._finish_final_output(msg)

        self._shutdown_event.set()
        self._want_read_event.set()
        await self._cancel_tasks(self._read_task)
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ShutdownCommand())

    async def _handle_command_close_completed(self, cmd: _CloseCompletedCommand) -> None:
        if self._transport_final_output is None:
            return  # Closed or failed meanwhile.

        if (exc := cmd.exc) is not None:
            # The peer reset the connection while it was being flushed, say.
            self._fail_graceful_close(exc)
            await self._fail()
            raise exc

        await self._complete_graceful_close()

    ##
    # output drain

    @dc.dataclass(frozen=True)
    class _DrainCompletedCommand(_Command):
        fences: ta.Sequence[IoPipelineMessages.Completable]
        exc: ta.Optional[BaseException] = None

    def _finish_flush_outputs(
            self,
            flush_outputs: ta.Iterable[IoPipelineMessages.Completable],
            exc: ta.Optional[BaseException] = None,
            *,
            raise_listener_errors: bool = True,
    ) -> None:
        flush_outputs = list(flush_outputs)
        if not flush_outputs:
            return

        first_listener_exc: ta.Optional[BaseException] = None

        with self._pipeline.enter():
            for flush_output in flush_outputs:
                if flush_output.is_done():
                    continue
                try:
                    if exc is None:
                        flush_output.set_succeeded(None)
                    else:
                        flush_output.set_failed(exc)
                except BaseException as listener_exc:  # noqa
                    if first_listener_exc is None:
                        first_listener_exc = listener_exc

        if first_listener_exc is not None and raise_listener_errors:
            raise first_listener_exc

    def _take_pending_drain_fences(self) -> ta.List[IoPipelineMessages.Completable]:
        fences = self._pending_drain_fences
        self._pending_drain_fences = []
        return fences

    def _finish_final_output(
            self,
            msg: IoPipelineMessages.FinalOutput,
            exc: ta.Optional[BaseException] = None,
            *,
            raise_listener_errors: bool = True,
    ) -> None:
        if msg.is_done():
            return

        try:
            with self._pipeline.enter():
                if exc is None:
                    msg.set_succeeded(None)
                else:
                    msg.set_failed(exc)
        except BaseException:  # noqa
            if raise_listener_errors:
                raise

    def _set_shutdown_drain_limits(self) -> None:
        """
        `write_eof()` half-closes the transport only once its buffer has emptied, whereas `drain()` returns once the
        buffer reaches the low watermark. For the shutdown's drain to complete at the half-close - success means the
        transport's output half was shut down - the watermarks are zero until it has completed. Nothing may produce
        ordinary output once ShutdownOutput reached the terminal, so the zero limits announce nothing.
        """

        if (writer := self._writer) is None or self._saved_write_limits is not None:
            return
        try:
            self._saved_write_limits = writer.transport.get_write_buffer_limits()  # (low, high)
        except (AttributeError, NotImplementedError):
            self._saved_write_limits = None
        self._set_write_limits(writer, high=0, low=0)

    def _restore_write_limits(self) -> None:
        if (writer := self._writer) is None:
            return
        if (saved := self._saved_write_limits) is not None:
            self._saved_write_limits = None
            self._set_write_limits(writer, high=saved[1], low=saved[0])
        elif self._flow is not None:
            self._set_write_limits(
                writer,
                high=self._config.write_high_watermark,
                low=self._config.write_low_watermark,
            )

    @property
    def _drain_pending(self) -> bool:
        return self._drain_requested or self._drains_outstanding > 0

    def _request_drain(self, fence: ta.Optional[IoPipelineMessages.Completable] = None) -> None:
        """
        Asks the drainer task for a drain, completing `fence` with it. A fence requested before the drain is called is
        completed by that drain; one requested while a drain runs - possible only through direct output handling, as
        the command loop holds fences behind a pending drain - is completed by the drain which follows it.
        """

        if self._writer is None:
            if fence is not None:
                self._finish_flush_outputs([fence])
            return

        if fence is not None:
            self._pending_drain_fences.append(fence)

        if not self._drain_requested:
            self._drain_requested = True
            self._drain_idle_event.clear()
            self._drainer_event.set()

    async def _drainer_task_main(self) -> None:
        """
        The one task which calls the writer's `drain()`, and performs the graceful close after FinalOutput, woken
        through an event as the work arises. Drains never overlap, as the stream API requires: a drain requested while
        one runs follows it. Completions are reported to the command loop as commands.
        """

        try:
            while True:
                if self._drain_requested:
                    self._drain_requested = False
                    fences = self._take_pending_drain_fences()
                    self._drains_outstanding += 1
                    exc: ta.Optional[BaseException] = None
                    try:
                        await self._drain_writer()
                    except asyncio.CancelledError:
                        raise
                    except BaseException as e:  # noqa
                        exc = e
                    finally:
                        if not self._drain_requested:
                            self._drain_idle_event.set()
                    self._command_queue.put_nowait(
                        PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand(fences, exc),
                    )
                    if exc is not None:
                        return  # The driver fails on it: nothing more can be drained or closed.
                    continue

                if self._close_requested:
                    self._close_requested = False
                    self._close_in_progress = True
                    exc = None
                    try:
                        await self._gracefully_close_writer()
                    except asyncio.CancelledError:
                        raise
                    except BaseException as e:  # noqa
                        exc = e
                    finally:
                        self._close_in_progress = False
                    self._command_queue.put_nowait(
                        PollAsyncioStreamIoPipelineDriver._CloseCompletedCommand(exc),
                    )
                    return

                await self._drainer_event.wait()
                self._drainer_event.clear()

        except asyncio.CancelledError:
            pass

    async def _drain_writer(self) -> None:
        if (writer := self._writer) is None:
            return
        if self._output_shutdown:
            self._set_shutdown_drain_limits()
        await writer.drain()

    async def _handle_command_drain_completed(self, cmd: _DrainCompletedCommand) -> None:
        if self._drains_outstanding:
            self._drains_outstanding -= 1

        if self._state not in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
            return

        if (exc := cmd.exc) is not None:
            self._finish_flush_outputs(
                [*cmd.fences, *self._take_pending_drain_fences()],
                exc,
                raise_listener_errors=False,
            )
            await self._fail()
            raise exc

        if self._output_shutdown and not self._drains_outstanding:
            self._restore_write_limits()

        self._finish_flush_outputs(cmd.fences)

        if self._state is IoPipelineDriverState.RUNNING:
            self._update_output_writability(drained=True)

    ##
    # awaits

    @dc.dataclass(frozen=True)
    class _AwaitCompletedCommand(_Command):
        msg: AsyncIoPipelineMessages.Await
        fut: asyncio.Future

    @dc.dataclass(frozen=True)
    class _AwaitFailedCommand(_Command):
        msg: AsyncIoPipelineMessages.Await
        exc: BaseException

    async def _handle_command_await_completed(self, cmd: _AwaitCompletedCommand) -> None:
        fut = cmd.fut
        self._pending_awaits.pop(fut, None)

        if cmd.msg.is_done():
            # Failed meanwhile by its producer - a multiplexed stream which ended, say - which cancelled the work.
            return

        try:
            result = fut.result()
        except BaseException as e:  # noqa
            with self._pipeline.enter():
                cmd.msg.set_failed(e)
        else:
            with self._pipeline.enter():
                cmd.msg.set_succeeded(result)

    async def _handle_command_await_failed(self, cmd: _AwaitFailedCommand) -> None:
        with self._pipeline.enter():
            cmd.msg.set_failed(cmd.exc)

    async def _handle_output_await(
            self,
            msg: AsyncIoPipelineMessages.Await,
    ) -> ta.Optional[str]:
        loop = asyncio.get_running_loop()

        # A coroutine becomes a task the driver creates, and so owns: it is cancelled if the Await is failed by its
        # producer before it completes, and when the driver closes. A task or future supplied is the caller's.
        created = asyncio.iscoroutine(msg.obj)

        try:
            fut = asyncio.ensure_future(msg.obj)
        except BaseException as e:  # noqa
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand(msg, e),
            )
            return None

        try:
            fut_loop = fut.get_loop()
        except AttributeError:
            fut_loop = loop

        if fut_loop is not loop:
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand(
                    msg,
                    RuntimeError(f'awaitable {fut!r} is attached to a different event loop'),
                ),
            )
            return None

        self._pending_awaits[fut] = created

        def done_callback(f: asyncio.Future) -> None:
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitCompletedCommand(msg, f),
            )

        fut.add_done_callback(done_callback)  # noqa

        if created:
            def msg_done(m: IoPipelineMessages.Completable) -> None:
                try:
                    current = asyncio.current_task()
                except RuntimeError:
                    current = None
                if not fut.done() and fut is not current:
                    fut.cancel()

            msg.add_listener(msg_done)

        return None

    def _cancel_created_awaits_now(self) -> ta.List[asyncio.Future]:
        tasks = [fut for fut, created in self._pending_awaits.items() if created]
        self._pending_awaits.clear()
        return self._cancel_tasks_now(*tasks)

    ##
    # command handling

    def _build_command_handlers(self) -> ta.Mapping[
        ta.Type[_Command],
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]],
    ]:
        cls = type(self)
        return {
            PollAsyncioStreamIoPipelineDriver._FeedInCommand: cls._handle_command_feed_in,
            PollAsyncioStreamIoPipelineDriver._PostCommand: cls._handle_command_post,
            PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand: cls._handle_command_read_completed,
            PollAsyncioStreamIoPipelineDriver._ReadFailedCommand: cls._handle_command_read_failed,
            PollAsyncioStreamIoPipelineDriver._TimerCommand: cls._handle_command_timer,
            PollAsyncioStreamIoPipelineDriver._DeferCommand: cls._handle_command_defer,
            PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand: cls._handle_command_drain_completed,
            PollAsyncioStreamIoPipelineDriver._CloseCompletedCommand: cls._handle_command_close_completed,
            PollAsyncioStreamIoPipelineDriver._AwaitCompletedCommand: cls._handle_command_await_completed,
            PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand: cls._handle_command_await_failed,
        }

    async def _handle_command(self, cmd: _Command) -> None:
        log.debug(lambda: f'Handling command: {cmd!r}')

        try:
            fn = self._command_handlers[cmd.__class__]
        except KeyError:
            raise TypeError(f'Unknown command type: {cmd.__class__}') from None

        try:
            await fn(self, cmd)
        except BaseException:
            if self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
                await self._fail()
            raise

        if (
                self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
                not self._pipeline.is_ready
        ):
            # Destroyed from under the driver - by an application policy in a timer callback, say: an explicit close.
            await self.close()

    ##
    # output handling

    async def _handle_output_final_output(self, msg: IoPipelineMessages.FinalOutput) -> ta.Optional[str]:
        """
        The graceful close - flushing everything written, then closing the transport - is performed by the drainer
        task, so that while a peer which has yet to read keeps it from completing, the driver still runs timers,
        completes awaits, and keeps taking the peer's output off the transport (and dropping it) so the peer can
        proceed to read this side's.
        """

        self._state = IoPipelineDriverState.DRAINING
        self._transport_final_output = msg

        # Input is taken but not consumed from now on: let a manual-mode read task read regardless.
        self._want_read_event.set()

        if self._writer is None or self._drainer_task is None:
            await self._complete_graceful_close()
            return None

        # A drain still pending completes first, on its own; the drainer task then performs the close.
        self._request_close()
        return None

    async def _handle_output_defer(self, msg: IoPipelineMessages.Defer) -> ta.Optional[str]:
        # A deferred continuation is a fairness yield: the commands already queued - reads, awaits, drain completions -
        # and then the timers due go first.
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._DeferCommand(msg))
        return None

    async def _handle_output_bytes(self, msg: ta.Any) -> None:
        for mv in ByteStreamBuffers.iter_segments(msg):
            if self._writer is not None and mv:
                if (wcm := self._config.write_chunk_max) is None:
                    self._writer.write(mv)
                else:
                    for pos in range(0, len(mv), wcm):
                        self._writer.write(mv[pos:pos + wcm])

        self._update_output_writability()

    async def _handle_output_flush_output(self, msg: IoPipelineFlowMessages.FlushOutput) -> ta.Optional[str]:
        self._request_drain(msg)
        return None

    async def _handle_output_shutdown_output(self, msg: IoPipelineMessages.ShutdownOutput) -> ta.Optional[str]:
        if (writer := self._writer) is not None:
            if not writer.can_write_eof():
                with self._pipeline.enter():
                    if not msg.is_done():
                        msg.set_failed(UnsupportedIoPipelineError(f'{writer!r} cannot write eof'))
                return None

            writer.write_eof()

        self._output_shutdown = True
        self._request_drain(msg)
        return None

    async def _handle_output_ready_for_input(self, msg: IoPipelineFlowMessages.ReadyForInput) -> ta.Optional[str]:
        check.state(self._flow is not None)
        if self._config.strict_input_flow:
            check.state(not self._want_read)
        self._want_read = True
        self._want_read_event.set()
        return None

    def _hold_post_drain_output(self, msg: ta.Any) -> None:
        self._post_drain_output_q.append(msg)
        if ByteStreamBuffers.can_bytes(msg):
            self._post_drain_output_bytes += ByteStreamBuffers.bytes_len(msg)
            # Without this a producer continuing through Defers - which are not held - would never be paused.
            self._update_output_writability()

    def _take_post_drain_output(self) -> ta.Any:
        msg = self._post_drain_output_q.popleft()
        if ByteStreamBuffers.can_bytes(msg):
            self._post_drain_output_bytes -= ByteStreamBuffers.bytes_len(msg)
        return msg

    def _update_output_writability(self, *, drained: bool = False) -> None:
        """
        The transport's own write buffer limits are the watermarks, so it pauses and resumes with the same hysteresis.
        A completed drain means it resumed - its buffer reached the low watermark - so unless the buffer has since grown
        past the high watermark, output is writable again.
        """

        if (
                self._state is not IoPipelineDriverState.RUNNING or
                self._flow is None or
                self._writer is None or
                self._output_shutdown
        ):
            return

        size = self._writer.transport.get_write_buffer_size() + self._post_drain_output_bytes
        if self._output_writable:
            if size > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif (
                (
                    size <= self._config.write_low_watermark or
                    (drained and size <= self._config.write_high_watermark)
                ) and
                # Never announced once ShutdownOutput reached the terminal - not just once the transport performed it -
                # since from then on nothing may produce ordinary output.
                not self._pipeline.saw_shutdown_output
        ):
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

    def _ensure_paused_output_drain(self) -> None:
        """
        The transport writes in the background, and nothing else observes it catching up: while output is paused, a
        drain must be pending, or a producer which honors writability without flushing would wait forever. Started only
        once no runnable output remains, so it never delays fences already queued behind the paused output.
        """

        if (
                not self._output_writable and
                not self._drain_pending and
                self._state is IoPipelineDriverState.RUNNING and
                self._writer is not None and
                not self._output_shutdown
        ):
            self._request_drain()

    def _build_output_handlers(self) -> ta.Mapping[
        type,
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]],
    ]:
        cls = type(self)
        return {
            IoPipelineMessages.FinalOutput: cls._handle_output_final_output,
            IoPipelineMessages.Defer: cls._handle_output_defer,
            IoPipelineFlowMessages.FlushOutput: cls._handle_output_flush_output,
            IoPipelineMessages.ShutdownOutput: cls._handle_output_shutdown_output,
            IoPipelineFlowMessages.ReadyForInput: cls._handle_output_ready_for_input,
            AsyncIoPipelineMessages.Await: cls._handle_output_await,
        }

    async def _handle_output(self, msg: ta.Any) -> str:
        log.debug(lambda: f'Handling output: {msg!r}')

        try:
            if ByteStreamBuffers.can_bytes(msg):
                await self._handle_output_bytes(msg)
                return 'handled'

            try:
                fn = self._output_handlers[msg.__class__]
            except KeyError:
                return 'unhandled'

            ret = await fn(self, msg)
            return ret if ret is not None else 'handled'

        except BaseException:
            if self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
                await self._fail()
            raise

    ##
    # core loop

    @staticmethod
    def _is_drain_ordered_output(msg: ta.Any) -> bool:
        return ByteStreamBuffers.can_bytes(msg) or isinstance(msg, (
            IoPipelineFlowMessages.FlushOutput,
            IoPipelineMessages.ShutdownOutput,
            IoPipelineMessages.FinalOutput,
        ))

    def _has_pending_work(self) -> bool:
        if self._pending_awaits:
            return True

        if self._drain_pending or self._close_pending:
            return True

        if self._read_task is not None and not self._read_task.done():
            return True

        if hasattr(self, '_sched') and self._sched.next_deadline() is not None:
            return True

        return False

    async def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        """
        Advance until an unhandled output or no work remains.

        When read is false, process only immediately available work without waiting for transport input or future
        timers. In this mode, raise_on_stall is ignored.
        """

        pipeline = await self._ensure_init()

        try:
            self._sched.run_due()
        except BaseException:
            await self._fail()
            raise

        while True:
            if not pipeline.is_ready:
                # Destroyed from under the driver - by an application policy in a callback, say: an explicit close.
                await self.close()
                return None

            if self._drain_pending:
                while (blocked_msg := pipeline.output.poll()) is not None:
                    # Only output bytes and output fences are ordered against a pending drain. Everything else - read
                    # requests, deferred work, awaits, unhandled messages for the caller - is not, and must not wait
                    # behind a drain stalled on the peer: a read request held here would stop input while output waits
                    # for the peer to read, deadlocking two such peers.
                    if self._is_drain_ordered_output(blocked_msg):
                        self._hold_post_drain_output(blocked_msg)
                        continue

                    handled = await self._handle_output(blocked_msg)

                    if handled == 'handled':
                        continue

                    elif handled == 'unhandled':
                        return blocked_msg

                    else:
                        raise RuntimeError(f'Unexpected handled value for {blocked_msg!r}: {handled!r}')

            else:
                if self._post_drain_output_q:
                    out_msg = self._take_post_drain_output()
                else:
                    out_msg = pipeline.output.poll()

                if out_msg is not None:
                    handled = await self._handle_output(out_msg)

                    if handled == 'handled':
                        continue

                    elif handled == 'unhandled':
                        return out_msg

                    elif handled == 'stop':
                        break

                    else:
                        raise RuntimeError(f'Unknown handled value: {handled!r}')

            self._ensure_paused_output_drain()

            # Handling pipeline output (notably a Defer) can schedule timers just as handling a command can, so the
            # loop timer is (re)armed for the earliest deadline before any wait.
            self._arm_timer()

            try:
                cmd = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                if self._shutdown_event.is_set():
                    break

                if not read:
                    if not self._close_pending:
                        return None
                    # The graceful close is the driver's own work in flight, not input: it is waited for as it always
                    # was, but with what arrives meanwhile - timers, awaits, reads to discard - serviced.

                elif raise_on_stall and not self._has_pending_work():
                    raise RuntimeError('Pipeline stalled') from None

                cmd = await self._command_queue.get()

            if isinstance(cmd, PollAsyncioStreamIoPipelineDriver._ShutdownCommand):
                break

            await self._handle_command(cmd)

        try:
            pipeline.destroy()
        except BaseException:
            await self._fail()
            raise

        self._state = IoPipelineDriverState.CLOSED
        return None

    @async_exception_logging(alog)
    async def loop_until_done(self) -> None:
        try:
            while True:
                if (out := await self.next()) is not None:
                    raise TypeError(out)

                if not self._pipeline.is_ready:
                    break

        finally:
            await self.close()

    ##
    # lifecycle

    def _drain_command_queue(self, exc: BaseException) -> None:
        posts: ta.List[IoPipelinePost] = []
        while True:
            try:
                cmd = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if (
                    isinstance(cmd, PollAsyncioStreamIoPipelineDriver._FeedInCommand) and
                    (fut := cmd.fut) is not None and
                    not fut.done()
            ):
                fut.set_exception(exc)
            elif isinstance(cmd, PollAsyncioStreamIoPipelineDriver._PostCommand):
                posts.append(cmd.post)

        fail_io_pipeline_posts(posts, exc)

    async def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        await self.close()

    async def close(self) -> None:
        """
        Abort the driver without waiting for graceful pipeline output completion.

        Everything is released - the tasks cancelled, the transport aborted, the pipeline destroyed - before anything is
        awaited. The task closing the driver may itself be cancelled while the driver waits for what it cancelled, as
        when a connection closes on its own just as its owner closes it: the wait is interrupted, but nothing is left
        open.
        """

        if self._state is IoPipelineDriverState.CLOSED:
            return

        failed = self._state is IoPipelineDriverState.FAILED

        # Only on its own running loop may the driver wait for what it cancels.
        wait = self._own_loop_running()

        cancelled: ta.List[asyncio.Future] = []
        aborted_writer: ta.Optional[asyncio.StreamWriter] = None

        try:
            try:
                self._shutdown_event.set()

                self._want_read_event.set()

                self._disarm_timer()

                self._drain_requested = False
                self._drains_outstanding = 0
                self._close_requested = False
                cancelled.extend(self._cancel_tasks_now(self._drainer_task))
                self._drainer_task = None
                self._drain_idle_event.set()
                self._fail_graceful_close(AbortedIoPipelineError('Driver closed before transport flush completion'))
                self._post_drain_output_q.clear()
                self._post_drain_output_bytes = 0

                cancelled.extend(self._cancel_tasks_now(self._read_task))
                cancelled.extend(self._cancel_created_awaits_now())

                aborted_writer = self._abort_writer_now()

                if hasattr(self, '_sched'):
                    self._sched.cancel_all()

                # Closed from here on: nothing more is accepted, by a listener run below or by anyone else.
                self._state = IoPipelineDriverState.FAILED if failed else IoPipelineDriverState.CLOSED

                # Only now, with the transport released, does anything run which may raise: handlers' Removed
                # callbacks as the pipeline is destroyed, then completion listeners as the input never processed is
                # failed. Each step runs whatever the other did, so that nothing is left undone, and the first
                # exception raised is the one re-raised once everything has been released - the rule the pipeline's
                # own destroy() applies to its handlers - and any later one is dropped. An exception group would carry
                # them all, but there is none on Python 3.8, and a close is not the place to invent one.
                first_exc: ta.Optional[BaseException] = None

                if (pipeline := getattr(self, '_pipeline', None)) is not None and pipeline.is_ready:
                    try:
                        pipeline.destroy()
                    except BaseException as e:  # noqa
                        first_exc = e

                # Input never processed is released, and anyone waiting on it is told.
                try:
                    self._drain_command_queue(AbortedIoPipelineError('Driver closed before the input was processed'))
                except BaseException as e:  # noqa
                    if first_exc is None:
                        first_exc = e
                self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ShutdownCommand())

                if first_exc is not None:
                    raise first_exc

            except BaseException:
                self._state = IoPipelineDriverState.FAILED
                raise

        finally:
            # Waited for even when a handler's removal failed: the close is still the close of the transport.
            if wait:
                await self._wait_cancelled(cancelled)
                await self._wait_writer_closed(aborted_writer)

    async def __aenter__(self) -> 'PollAsyncioStreamIoPipelineDriver':  # noqa
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


########################################
# ../../../../omcore/rpc/dispatch.py
"""
What a connection dispatches inbound requests and notifications to.

Handlers are async-colored like everything above the pipeline: a sync runtime drives them with `sync_await`, so a
handler used under one must never actually suspend. `rpc_async_method` wraps a plain callable for use in a method
table.

The table handler is deliberately a plain mapping from method name to callable - no reflection, no signature binding,
no object facades. Concerns compose by merging their tables, with duplicate names rejected at composition time.
"""


log = get_module_logger(globals())  # noqa


##


class RpcHandler(Abstract):
    """
    Requests are answered by `handle_request`; its result is sent back as-is and any exception it raises is sent back
    as an error. Raise `RpcMethodNotFoundError` for an unknown method, and an `RpcHandlerError` to answer with exactly
    the error data it carries.

    Notifications are first offered to `handle_notification_inline`, which runs synchronously on the connection's pump
    in wire order: anything the peer sent after the notification, such as the reply to a later request, is seen only
    once it has been applied. This is how ordered streams are pushed. Returning False hands the notification to
    `handle_notification`, which the connection runs however it runs request handlers.
    """

    @abc.abstractmethod
    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        raise NotImplementedError

    def handle_request_message(self, request: RpcRequestMessage) -> ta.Awaitable[ta.Any]:
        """
        What the connection actually calls. Handlers which need more than the method and params - the request's id, as
        a replay registry keyed on client-chosen ids does - override this instead.
        """

        return self.handle_request(request.method, request.params)

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        return False

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        log.debug('Dropping unhandled notification: %r', method)


##


def rpc_merge_method_tables(*tables: ta.Mapping[str, T]) -> ta.Dict[str, T]:
    """Merges method tables, rejecting a name present in more than one."""

    out: ta.Dict[str, T] = {}
    for table in tables:
        for name, fn in table.items():
            if name in out:
                raise ValueError(f'duplicate rpc method: {name!r}')
            out[name] = fn
    return out


def rpc_async_method(fn: ta.Callable[[ta.Any], ta.Any]) -> RpcMethodFn:
    """Wraps a plain callable as an async method table entry."""

    @functools.wraps(fn)
    async def inner(params: ta.Any) -> ta.Any:
        return fn(params)

    return inner


class RpcMethodTableHandler(RpcHandler):
    def __init__(
            self,
            methods: ta.Optional[ta.Mapping[str, RpcMethodFn]] = None,
            *,
            notifications: ta.Optional[ta.Mapping[str, RpcMethodFn]] = None,
            inline_notifications: ta.Optional[ta.Mapping[str, RpcInlineNotificationFn]] = None,
    ) -> None:
        super().__init__()

        self._methods: ta.Dict[str, RpcMethodFn] = dict(methods or {})
        self._notifications: ta.Dict[str, RpcMethodFn] = dict(notifications or {})
        self._inline_notifications: ta.Dict[str, RpcInlineNotificationFn] = dict(inline_notifications or {})

        if dup := set(self._notifications) & set(self._inline_notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._methods)} methods>'

    @property
    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return self._methods

    @property
    def notifications(self) -> ta.Mapping[str, RpcMethodFn]:
        return self._notifications

    @property
    def inline_notifications(self) -> ta.Mapping[str, RpcInlineNotificationFn]:
        return self._inline_notifications

    #

    def add_methods(self, methods: ta.Mapping[str, RpcMethodFn]) -> None:
        self._methods = rpc_merge_method_tables(self._methods, methods)

    def add_notifications(self, notifications: ta.Mapping[str, RpcMethodFn]) -> None:
        if dup := set(notifications) & set(self._inline_notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')
        self._notifications = rpc_merge_method_tables(self._notifications, notifications)

    def add_inline_notifications(self, notifications: ta.Mapping[str, RpcInlineNotificationFn]) -> None:
        if dup := set(notifications) & set(self._notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')
        self._inline_notifications = rpc_merge_method_tables(self._inline_notifications, notifications)

    #

    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None

        return await fn(params)

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        if (fn := self._inline_notifications.get(method)) is None:
            return False

        fn(params)
        return True

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        if (fn := self._notifications.get(method)) is None:
            log.debug('Dropping unhandled notification: %r', method)
            return

        await fn(params)


########################################
# ../../../../omcore/rpc/framing.py
"""
Wire framing: bytes <-> RpcFrame.

The toolbox's own framing is a fixed-width unsigned length prefix, network order by default, followed by that many
payload bytes. Both directions enforce a maximum frame size; a received frame exceeding it is fatal, as the byte stream
cannot be resynchronized past it.

Written in the pipelines idiom as a `BufferedBytesToMessageDecoderIoPipelineHandler`, but kept in this package rather
than in `omcore.io.pipelines`: it is the rpc wire format, and lives with it for the foreseeable future.
"""


##


@dc.dataclass(frozen=True)
class RpcFrame:
    """One complete wire payload, before envelope decoding or after envelope encoding."""

    data: bytes


##


class RpcLengthPrefixedFramingIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """
    bytes <-> RpcFrame with a length prefix of `length_field_length` bytes in `byteorder`.

    The limit applies to the payload, excluding the prefix. Outbound frames are sized by the envelope codec before they
    get here, so an oversized outbound frame is a programming error and raises.
    """

    def __init__(
            self,
            *,
            max_frame_bytes: int,
            length_field_length: int = 4,
            byteorder: ta.Literal['big', 'little'] = 'big',
            buffer_chunk_size: int = 64 * 1024,
    ) -> None:
        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        if length_field_length not in (1, 2, 4, 8):
            raise ValueError(length_field_length)
        if max_frame_bytes >= (1 << (8 * length_field_length)):
            raise ValueError(f'max_frame_bytes {max_frame_bytes} is not representable in {length_field_length} bytes')

        super().__init__(
            # The decoder checks frame sizes precisely itself; the buffer limit is a backstop bounding memory by what
            # one driver read batch can overshoot.
            max_buffer_size=None,
            buffer_chunk_size=buffer_chunk_size,
        )

        self._max_frame_bytes = max_frame_bytes
        self._length_field_length = length_field_length
        self._byteorder = byteorder

        self._fr = LengthFieldByteStreamFrameDecoder(
            length_field_length=length_field_length,
            byteorder=byteorder,
            initial_bytes_to_strip=length_field_length,
            max_frame_length=max_frame_bytes + length_field_length,
        )

    @property
    def max_frame_bytes(self) -> int:
        return self._max_frame_bytes

    #

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        try:
            frames = self._fr.decode(buf)
        except FrameTooLargeByteStreamBufferError as e:
            raise RpcMessageTooLargeError(f'received frame exceeds limit of {self._max_frame_bytes} bytes') from e
        except LimitByteStreamBufferError as e:
            raise RpcMessageTooLargeError(str(e)) from e
        except ValueError as e:
            raise RpcProtocolError(f'corrupt frame: {e}') from e

        for fr in frames:
            out.append(RpcFrame(ByteStreamBuffers.to_bytes(fr, strict=True)))

        if final and len(buf):
            # Raising during final input would strand FinalInput's propagation, so report the error as a message.
            buf.advance(len(buf))
            out.append(IoPipelineMessages.Error(
                RpcProtocolError('stream ended within a frame'),
                direction='inbound',
                handler=ctx.ref,
            ))

    def _encode_frame(self, frame: RpcFrame) -> bytes:
        return len(frame.data).to_bytes(self._length_field_length, self._byteorder) + frame.data

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            if len(msg.data) > self._max_frame_bytes:
                raise RpcMessageTooLargeError(
                    f'outbound frame is {len(msg.data)} bytes, exceeding limit {self._max_frame_bytes}',
                )

            msg = self._encode_frame(msg)

        ctx.feed_out(msg)


########################################
# ../../../../omcore/rpc/session.py
"""
The sans-io rpc session: the innermost pipeline handler, owning all protocol state for one connection.

The protocol is symmetric - either peer may send requests, notifications, cancels, and pings at any time - so one
session handler serves both ends. It correlates responses to the requests this side sent, surfaces the requests the peer
sent for the host to answer, answers pings itself, and enforces every timeout and limit which can be expressed without
touching a transport. Timers come from the driver's IoPipelineScheduling service, so they behave identically under every
driver and can be exercised deterministically with the pure driver's manual clock.

Everything the host needs to know arrives as an event fed outbound (see `messages.py`); everything the host wants done
arrives as a command fed inbound. The session never executes anything: a received request becomes a RequestReceived
event, and how and where the host runs its handler is the host's business. Peer misbehavior which can be tolerated is
tolerated by policy; the rest closes the connection with a protocol error.

Reentrancy: feeding a message outbound can synchronously deliver an Error back into this handler and change its state (a
failed write, an unencodable envelope reported by the codec). Every method therefore re-checks state after any
`feed_out`, and the terminal `_finish_close` is idempotent.
"""


log = get_module_logger(globals())  # noqa


##


class RpcSessionIoPipelineHandler(IoPipelineHandler):
    @dc.dataclass()
    class _PendingOut:
        request: RpcRequestMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    @dc.dataclass()
    class _PendingPing:
        ping: RpcPingMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    @dc.dataclass()
    class _InflightIn:
        request: RpcRequestMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    def __init__(self, config: RpcConfig = RpcConfig.DEFAULT) -> None:
        super().__init__()

        self._config = config

        self._state: RpcSessionState = 'new'

        self._pending_out: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._PendingOut] = {}
        self._pending_pings: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._PendingPing] = {}
        self._inflight_in: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._InflightIn] = {}

        self._output_paused = False
        self._ready_for_input_issued = False

        self._close_handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._close_exc: ta.Optional[BaseException] = None
        self._sent_final_output = False

        self._sending_substitute = False

        # The flush fence issued while handling the current send command, if any, so completion can be reported.
        self._current_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None

        # Under consolidate_flushes: the fence fed last and not yet completed, if any, and the fence the sends made
        # meanwhile share, fed once that one completes.
        self._inflight_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None
        self._pending_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}@{id(self):x}'
            f'<{self._state}, pending_out={len(self._pending_out)}, inflight_in={len(self._inflight_in)}>'
        )

    @property
    def config(self) -> RpcConfig:
        return self._config

    @property
    def state(self) -> RpcSessionState:
        return self._state

    @property
    def pending_outbound_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._pending_out.keys()

    @property
    def pending_ping_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._pending_pings.keys()

    @property
    def inflight_inbound_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._inflight_in.keys()

    @property
    def output_paused(self) -> bool:
        return self._output_paused

    def _is_closed(self) -> bool:
        # A method rather than a direct comparison so re-checks after reentrant calls are not narrowed away.
        return self._state == 'closed'

    ##
    # utilities

    def _needs_scheduling(self) -> bool:
        c = self._config
        return any(t is not None for t in (
            c.default_request_timeout_s,
            c.default_ping_timeout_s,
            c.inbound_handling_timeout_s,
            c.close_drain_timeout_s,
        ))

    def _schedule(
            self,
            ctx: IoPipelineHandlerContext,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        if (sched := ctx.services.find(IoPipelineScheduling)) is None:
            raise RuntimeError('rpc session timeouts require an IoPipelineScheduling service')
        return sched.schedule_context(ctx.ref, delay_s, fn)

    @staticmethod
    def _cancel_handle(entry: ta.Union[_PendingOut, _PendingPing, _InflightIn]) -> None:
        if (handle := entry.handle) is not None:
            entry.handle = None
            handle.cancel()

    def _emit(self, ctx: IoPipelineHandlerContext, event: RpcSessionMessages.Event) -> None:
        ctx.feed_out(event)

    def _send(self, ctx: IoPipelineHandlerContext, envelope: RpcEnvelope) -> bool:
        """Feed an envelope toward the wire and flush. Returns False if the session closed reentrantly meanwhile."""

        if self._sent_final_output:
            return False

        ctx.feed_out(envelope)
        if self._is_closed():
            return False

        if ctx.services.find(IoPipelineFlow) is not None:
            if not self._config.consolidate_flushes:
                fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = fence
                ctx.feed_out(fence)

            elif self._inflight_fence is not None:
                # A flush is under way: this send joins the one which follows it.
                if self._pending_fence is None:
                    self._pending_fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = self._pending_fence

            else:
                fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = fence
                self._feed_consolidated_fence(ctx, fence)

        return not self._is_closed()

    def _feed_consolidated_fence(
            self,
            ctx: IoPipelineHandlerContext,
            fence: IoPipelineFlowMessages.FlushOutput,
    ) -> None:
        self._inflight_fence = fence
        fence.add_listener(functools.partial(self._on_consolidated_fence_done, weakref.ref(ctx)))
        ctx.feed_out(fence)

    @staticmethod
    def _on_consolidated_fence_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            fence: IoPipelineMessages.Completable[None],
    ) -> None:
        if (ctx := ctx_ref()) is None or ctx.invalidated:
            return
        h = ta.cast('RpcSessionIoPipelineHandler', ctx.handler)
        if h._inflight_fence is fence:  # noqa
            h._inflight_fence = None  # noqa
        if fence.is_succeeded():
            h._flush_pending_fence(ctx)  # noqa

    def _flush_pending_fence(self, ctx: IoPipelineHandlerContext) -> None:
        if (fence := self._pending_fence) is None or self._inflight_fence is not None:
            return
        self._pending_fence = None
        if ctx.invalidated or self._sent_final_output or ctx.pipeline.saw_final_output:
            # Closed meanwhile: the fence is never fed, and closure has failed whatever waited on it.
            return
        self._feed_consolidated_fence(ctx, fence)

    @staticmethod
    def _on_send_fence_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            cmd: RpcSessionMessages.Command,
            fence: IoPipelineMessages.Completable[None],
    ) -> None:
        # Failure means the driver is closing, which the host learns of from Closed; only success is worth reporting.
        # Output after FinalOutput reached the terminal is rejected by the pipeline, so check for that too.
        if not fence.is_succeeded():
            return
        if (ctx := ctx_ref()) is None or ctx.invalidated or ctx.pipeline.saw_final_output:
            return
        ctx.feed_out(RpcSessionMessages.Sent(cmd))

    def _report_sent(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.Command) -> None:
        """Emit Sent for a send command, now if nothing needed flushing, else once its fence completes."""

        fence = self._current_fence
        self._current_fence = None

        if self._is_closed():
            return

        if fence is not None and not fence.is_done():
            fence.add_listener(functools.partial(self._on_send_fence_done, weakref.ref(ctx), cmd))
        elif fence is None or fence.is_succeeded():
            self._emit(ctx, RpcSessionMessages.Sent(cmd))

    def _closed_error(self) -> RpcConnectionClosedError:
        if (exc := self._close_exc) is not None:
            err = RpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return RpcConnectionClosedError('connection closed')

    def _effective_timeout(
            self,
            timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]],
            default: ta.Optional[float],
    ) -> ta.Optional[float]:
        if timeout_s is RpcUnspecified:
            return default
        return ta.cast(ta.Optional[float], timeout_s)

    ##
    # session-generated errors

    @staticmethod
    def _error_data(code: str, exc_type: ta.Type[BaseException], message: str) -> RpcRemoteErrorData:
        return RpcRemoteErrorData(code=code, remote_type=rpc_exception_type_name(exc_type), message=message)

    def _busy_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.BUSY,
            RpcTooManyRequestsError,
            'Too many concurrent requests',
        ))

    def _shutting_down_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.SHUTTING_DOWN,
            RpcConnectionClosedError,
            'Connection shutting down',
        ))

    def _handling_timeout_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.HANDLING_TIMEOUT,
            RpcTimeoutError,
            'Request handling timed out',
        ))

    ##
    # outbound requests

    def _track_pending_out(
            self,
            ctx: IoPipelineHandlerContext,
            request: RpcRequestMessage,
    ) -> ta.Optional[_PendingOut]:
        """Register an outbound request, or emit RequestFailed and return None if it cannot be sent."""

        if (rid := request.id) in self._pending_out:
            self._emit(ctx, RpcSessionMessages.RequestFailed(
                request,
                ValueError(f'duplicate outbound request id: {rid!r}'),
            ))
            return None

        if (mx := self._config.max_pending_outbound) is not None and len(self._pending_out) >= mx:
            self._emit(ctx, RpcSessionMessages.RequestFailed(request, RpcTooManyRequestsError(
                f'too many pending outbound requests: {mx}',
            )))
            return None

        entry = self._PendingOut(request)
        self._pending_out[rid] = entry
        return entry

    def _on_send_request(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendRequest) -> None:
        if (entry := self._track_pending_out(ctx, cmd.request)) is None:
            return

        if not self._send(ctx, cmd.request):
            return

        rid = entry.request.id
        if self._pending_out.get(rid) is not entry:
            # Failed reentrantly while being sent.
            return

        if (t := self._effective_timeout(cmd.timeout_s, self._config.default_request_timeout_s)) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_request_timeout(ctx2, rid),  # noqa
            )

    def _on_send_notification(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendNotification) -> None:
        self._send(ctx, cmd.notification)

    def _send_cancel(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if self._state != 'open':
            return
        self._send(ctx, RpcCancelMessage(rid))

    def _on_request_timeout(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if (entry := self._pending_out.pop(rid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, RpcTimeoutError(
            f'request {rid!r} ({entry.request.method}) timed out',
        )))
        if self._is_closed():
            return

        if self._config.cancel_abandoned_requests:
            self._send_cancel(ctx, rid)
            if self._is_closed():
                return

        self._after_pending_out_completed(ctx)

    def _on_cancel_request(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.CancelRequest) -> None:
        if (entry := self._pending_out.pop(cmd.id, None)) is None:
            return
        self._cancel_handle(entry)

        if cmd.notify_peer:
            self._send_cancel(ctx, cmd.id)
            if self._is_closed():
                return

        self._after_pending_out_completed(ctx)

    def _fail_pending_out(self, ctx: IoPipelineHandlerContext, exc: Exception) -> None:
        entries = list(self._pending_out.values())
        self._pending_out.clear()
        for entry in entries:
            self._cancel_handle(entry)
            self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, exc))

        pings = list(self._pending_pings.values())
        self._pending_pings.clear()
        for ping in pings:
            self._cancel_handle(ping)
            self._emit(ctx, RpcSessionMessages.PingFailed(ping.ping, exc))

    def _after_pending_out_completed(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closing' and not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)

    ##
    # pings

    def _on_send_ping(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendPing) -> None:
        ping = cmd.ping
        if (pid := ping.id) in self._pending_pings:
            self._emit(ctx, RpcSessionMessages.PingFailed(ping, ValueError(f'duplicate outbound ping id: {pid!r}')))
            return

        entry = self._PendingPing(ping)
        self._pending_pings[pid] = entry

        if not self._send(ctx, ping):
            return

        if self._pending_pings.get(pid) is not entry:
            return

        if (t := self._effective_timeout(cmd.timeout_s, self._config.default_ping_timeout_s)) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_ping_timeout(ctx2, pid),  # noqa
            )

    def _on_ping_timeout(self, ctx: IoPipelineHandlerContext, pid: ta.Any) -> None:
        if (entry := self._pending_pings.pop(pid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, RpcSessionMessages.PingFailed(entry.ping, RpcTimeoutError(f'ping {pid!r} timed out')))

    def _on_inbound_ping(self, ctx: IoPipelineHandlerContext, ping: RpcPingMessage) -> None:
        if self._state == 'closed':
            return

        self._send(ctx, RpcPongMessage(ping.id))

    def _on_inbound_pong(self, ctx: IoPipelineHandlerContext, pong: RpcPongMessage) -> None:
        if (entry := self._pending_pings.pop(pong.id, None)) is None:
            log.debug('Dropping unmatched pong: %r', pong)
            return

        self._cancel_handle(entry)
        self._emit(ctx, RpcSessionMessages.PongReceived(entry.ping, pong))

    ##
    # inbound responses

    def _on_inbound_response(self, ctx: IoPipelineHandlerContext, response: RpcResponseMessage) -> None:
        if (entry := self._pending_out.pop(response.id, None)) is None:
            if self._config.on_unmatched_response == 'close':
                self._finish_close(ctx, RpcProtocolError(f'unmatched response id: {response.id!r}'))
            else:
                log.debug('Dropping unmatched response: %r', response)
            return

        self._cancel_handle(entry)
        self._emit(ctx, RpcSessionMessages.ResponseReceived(entry.request, response))

        self._after_pending_out_completed(ctx)

    ##
    # inbound requests

    def _at_inflight_limit(self) -> bool:
        return (mx := self._config.max_inflight_inbound) is not None and len(self._inflight_in) >= mx

    def _on_inbound_request(self, ctx: IoPipelineHandlerContext, request: RpcRequestMessage) -> None:
        rid = request.id

        if self._state != 'open':
            self._send(ctx, self._shutting_down_response(rid))
            return

        if rid in self._inflight_in:
            self._finish_close(ctx, RpcProtocolError(f'duplicate inbound request id: {rid!r}'))
            return

        if self._at_inflight_limit() and self._config.inflight_limit_policy == 'reject':
            self._send(ctx, self._busy_response(rid))
            return

        entry = self._InflightIn(request)
        self._inflight_in[rid] = entry

        if (t := self._config.inbound_handling_timeout_s) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_inbound_handling_timeout(ctx2, rid),  # noqa
            )

        self._emit(ctx, RpcSessionMessages.RequestReceived(request))

    def _on_send_response(self, ctx: IoPipelineHandlerContext, response: RpcResponseMessage) -> None:
        if (entry := self._inflight_in.pop(response.id, None)) is None:
            log.debug('Dropping response to unknown or aborted inbound request: %r', response)
            return
        self._cancel_handle(entry)

        if not self._send(ctx, response):
            return

        self._after_inflight_in_completed(ctx)

    def _on_inbound_handling_timeout(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if (entry := self._inflight_in.pop(rid, None)) is None:
            return
        entry.handle = None

        if self._config.respond_to_aborted_inbound:
            if not self._send(ctx, self._handling_timeout_response(rid)):
                return

        self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, RpcTimeoutError(
            f'handling of inbound request {rid!r} ({entry.request.method}) timed out',
        )))

        self._after_inflight_in_completed(ctx)

    def _on_inbound_cancel(self, ctx: IoPipelineHandlerContext, cancel: RpcCancelMessage) -> None:
        if (entry := self._inflight_in.pop(cancel.id, None)) is None:
            # Already answered, or never seen: cancels race with responses by nature.
            return
        self._cancel_handle(entry)

        self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, RpcCancelledError(
            f'inbound request {cancel.id!r} ({entry.request.method}) cancelled by peer',
        )))

        self._after_inflight_in_completed(ctx)

    def _after_inflight_in_completed(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closing':
            if not self._pending_out and not self._inflight_in:
                self._finish_close(ctx, None)
            return

        self._maybe_ready_for_input(ctx)

    ##
    # encoding failures

    def _on_encode_failed(self, ctx: IoPipelineHandlerContext, msg: RpcSessionMessages.OutboundEncodeFailed) -> None:
        envelope = msg.envelope
        exc = msg.exc

        if self._sending_substitute:
            # Even the minimal error response would not fit: the frame limit is misconfigured. Dropping the response is
            # the least bad option - the peer times out and the connection stays usable for smaller messages.
            log.error('Cannot send even a substitute error response, dropping: %r', exc)
            return

        if isinstance(envelope, RpcRequestMessage):
            if (entry := self._pending_out.pop(envelope.id, None)) is not None:
                self._cancel_handle(entry)
                fexc: Exception
                if isinstance(exc, RpcMessageTooLargeError):
                    fexc = exc
                else:
                    fexc = ValueError(f'request could not be encoded: {exc!r}')
                    fexc.__cause__ = exc
                self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, fexc))

            self._after_pending_out_completed(ctx)
            return

        if isinstance(envelope, RpcPingMessage):
            if (ping := self._pending_pings.pop(envelope.id, None)) is not None:
                self._cancel_handle(ping)
                self._emit(ctx, RpcSessionMessages.PingFailed(ping.ping, exc))
            return

        if isinstance(envelope, (RpcResultMessage, RpcErrorMessage)):
            log.warning('Substituting error for unencodable response %r: %r', envelope.id, exc)
            substitute: RpcErrorMessage
            if isinstance(exc, RpcMessageTooLargeError):
                substitute = RpcErrorMessage(envelope.id, self._error_data(
                    RpcErrorCodes.RESULT_TOO_LARGE,
                    RpcMessageTooLargeError,
                    'Response too large',
                ))
            else:
                substitute = RpcErrorMessage(envelope.id, self._error_data(
                    RpcErrorCodes.RESULT_ENCODING,
                    type(exc),
                    f'Response could not be encoded: {exc}',
                ))

            self._sending_substitute = True
            try:
                self._send(ctx, substitute)
            finally:
                self._sending_substitute = False
            return

        if isinstance(envelope, RpcNotificationMessage):
            log.warning('Dropping unencodable notification %r: %r', envelope.method, exc)
            return

        # Cancels and pongs carry only an id: if one is unencodable the peer will not miss it much.
        log.debug('Dropping unencodable envelope %r: %r', envelope, exc)

    ##
    # flow control

    def _maybe_ready_for_input(self, ctx: IoPipelineHandlerContext) -> None:
        """Under the 'pause' policy, lets the driver read again once there is room for more inbound requests."""

        if (flow := ctx.services.find(IoPipelineFlow)) is None or flow.is_auto_read():
            return
        if self._state == 'closed' or self._ready_for_input_issued or self._at_inflight_limit():
            return

        self._ready_for_input_issued = True
        ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _on_flush_input(self, ctx: IoPipelineHandlerContext) -> None:
        # The driver has consumed its current read batch; it reads again only when told to.
        self._ready_for_input_issued = False

        if self._state != 'closed':
            ctx.defer(lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._maybe_ready_for_input(ctx2))  # noqa

    ##
    # lifecycle

    def _arm_close_drain(self, ctx: IoPipelineHandlerContext) -> None:
        if self._close_handle is not None:
            return
        if (t := self._config.close_drain_timeout_s) is None:
            return

        self._close_handle = self._schedule(
            ctx,
            t,
            lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_close_drain_timeout(ctx2),  # noqa
        )

    def _on_close_drain_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._close_handle = None
        if self._state != 'closing':
            return

        self._finish_close(ctx, RpcTimeoutError('close drain timed out with work still in flight'))

    def _on_close(self, ctx: IoPipelineHandlerContext, graceful: bool) -> None:
        if self._state == 'closed':
            return

        if not graceful:
            self._finish_close(ctx, None)
            return

        if self._state == 'closing':
            return
        self._state = 'closing'

        if not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)
            return

        self._arm_close_drain(ctx)

    def _on_peer_eof(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closed':
            return

        # No further responses can arrive.
        self._fail_pending_out(ctx, RpcConnectionClosedError('peer closed the connection'))
        if self._is_closed():
            return

        if self._config.on_peer_eof == 'drain' and self._inflight_in:
            # Keep answering what is already in flight; the peer may only have half-closed.
            self._state = 'closing'
            self._arm_close_drain(ctx)
            return

        self._finish_close(ctx, None)

    def _finish_close(
            self,
            ctx: IoPipelineHandlerContext,
            exc: ta.Optional[BaseException],
            *,
            transport_ok: bool = True,
    ) -> None:
        """
        Enter the terminal state exactly once: fail everything pending, abort everything in flight, announce Closed, and
        complete pipeline output.
        """

        if self._state == 'closed':
            return
        self._state = 'closed'
        self._close_exc = exc

        if (h := self._close_handle) is not None:
            self._close_handle = None
            h.cancel()

        closed_exc = self._closed_error()

        self._fail_pending_out(ctx, closed_exc)

        inflight = list(self._inflight_in.values())
        self._inflight_in.clear()
        for entry in inflight:
            self._cancel_handle(entry)
            if transport_ok and self._config.respond_to_aborted_inbound and not self._sent_final_output:
                ctx.feed_out(self._shutting_down_response(entry.request.id))
            self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, closed_exc))

        self._emit(ctx, RpcSessionMessages.Closed(exc))

        if exc is not None and not transport_ok:
            # The transport itself is in trouble - it failed, stalled, or the peer stopped answering or sent garbage -
            # so flushing what is left is unlikely to complete. Surfacing the failure as a raw exception output tells
            # the host to abort rather than wait on the final flush. A failure with a healthy transport (a drain or idle
            # timeout, a peer protocol violation caught by policy) instead flushes normally, so the answers just queued
            # for the requests in flight still reach the peer.
            ctx.feed_out(exc)

        if not self._sent_final_output and not ctx.pipeline.saw_final_output:
            if transport_ok and (fence := self._pending_fence) is not None:
                # Sends awaiting a flush are reported sent once their bytes are out, as ever.
                self._pending_fence = None
                ctx.feed_out(fence)
            self._sent_final_output = True
            ctx.feed_final_output()

    ##
    # handler interface

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._needs_scheduling():
                check.not_none(ctx.services.find(IoPipelineScheduling))

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            for po in self._pending_out.values():
                self._cancel_handle(po)
            for pp in self._pending_pings.values():
                self._cancel_handle(pp)
            for ii in self._inflight_in.values():
                self._cancel_handle(ii)
            if (h := self._close_handle) is not None:
                self._close_handle = None
                h.cancel()

    def _on_command(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.Command) -> None:
        check.state(self._state != 'new', 'command received before initial input')

        if isinstance(cmd, RpcSessionMessages.Close):
            self._on_close(ctx, cmd.graceful)
            return

        if isinstance(cmd, RpcSessionMessages.CancelRequest):
            self._on_cancel_request(ctx, cmd)
            return

        if isinstance(cmd, RpcSessionMessages.SendResponse):
            self._on_send_response(ctx, cmd.response)
            return

        if self._state != 'open':
            closed_exc = self._closed_error()
            if isinstance(cmd, RpcSessionMessages.SendRequest):
                self._emit(ctx, RpcSessionMessages.RequestFailed(cmd.request, closed_exc))
            elif isinstance(cmd, RpcSessionMessages.SendPing):
                self._emit(ctx, RpcSessionMessages.PingFailed(cmd.ping, closed_exc))
            elif isinstance(cmd, RpcSessionMessages.SendNotification):
                log.debug('Dropping notification sent while %s: %r', self._state, cmd.notification)
            else:
                raise TypeError(cmd)
            return

        self._current_fence = None
        try:
            if isinstance(cmd, RpcSessionMessages.SendRequest):
                self._on_send_request(ctx, cmd)
            elif isinstance(cmd, RpcSessionMessages.SendNotification):
                self._on_send_notification(ctx, cmd)
            elif isinstance(cmd, RpcSessionMessages.SendPing):
                self._on_send_ping(ctx, cmd)
            else:
                raise TypeError(cmd)
        finally:
            self._report_sent(ctx, cmd)

    def _on_envelope(self, ctx: IoPipelineHandlerContext, msg: RpcEnvelope) -> None:
        if isinstance(msg, RpcRequestMessage):
            self._on_inbound_request(ctx, msg)

        elif isinstance(msg, (RpcResultMessage, RpcErrorMessage)):
            self._on_inbound_response(ctx, msg)

        elif isinstance(msg, RpcNotificationMessage):
            self._emit(ctx, RpcSessionMessages.NotificationReceived(msg))

        elif isinstance(msg, RpcCancelMessage):
            self._on_inbound_cancel(ctx, msg)

        elif isinstance(msg, RpcPingMessage):
            self._on_inbound_ping(ctx, msg)

        elif isinstance(msg, RpcPongMessage):
            self._on_inbound_pong(ctx, msg)

        else:
            raise TypeError(msg)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcSessionMessages.Command):
            self._on_command(ctx, msg)

        elif isinstance(msg, RpcEnvelope):
            if self._state == 'closed':
                log.debug('Dropping envelope received after close: %r', msg)
                return
            self._on_envelope(ctx, msg)

        elif isinstance(msg, RpcSessionMessages.OutboundEncodeFailed):
            self._on_encode_failed(ctx, msg)

        elif isinstance(msg, IoPipelineMessages.InitialInput):
            check.state(self._state == 'new', 'duplicate initial input')
            self._state = 'open'
            ctx.feed_in(msg)
            self._maybe_ready_for_input(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._on_peer_eof(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.Error):
            if self._state == 'closed':
                # A failure after closing - the final flush timed out, say. Nothing may be output after FinalOutput, and
                # there is nothing left to do but abort, so the error is let past: unhandled, it fails the driver, which
                # is the abort.
                ctx.feed_in(msg)
                return
            self._finish_close(ctx, msg.exc, transport_ok=False)

        elif isinstance(msg, IdleStateIoPipelineEvent):
            # Idle means no messages *and* nothing in flight: a long-running handler or a slow peer answering a request
            # is covered by the per-request timeouts, not this one.
            if (
                    msg.state is IoPipelineIdleState.ALL_IDLE and
                    not self._pending_out and
                    not self._pending_pings and
                    not self._inflight_in
            ):
                self._finish_close(ctx, RpcTimeoutError('connection idle timed out'))

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._on_flush_input(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            if not self._output_paused:
                self._output_paused = True
                self._emit(ctx, RpcSessionMessages.OutputPaused())

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            if self._output_paused:
                self._output_paused = False
                self._emit(ctx, RpcSessionMessages.OutputResumed())

        else:
            ctx.feed_in(msg)


########################################
# ../../../../omcore/rpc/codecs.py
"""
RpcFrame <-> RpcEnvelope, in two pluggable halves.

A value codec turns bytes into an opaque value tree and back - JSON by default, but nothing in the toolbox depends on
JSON: anything which can carry string-keyed mappings, strings, and whatever the serde above the connection produces as
params and results (CBOR, say) plugs in here. An envelope codec maps the seven envelope kinds onto such a tree; the
default spells each as a mapping tagged by kind. This is the one place a differently-shaped wire dialect differs.

Decoding failures are protocol errors and fatal to the connection. Encoding never raises: an envelope which cannot be
encoded, or which encodes larger than the frame limit, is dropped and reported inward as an OutboundEncodeFailed so the
session can fail just that message rather than the connection.
"""


##


class RpcValueCodec(Abstract):
    """bytes <-> an opaque value tree. Both methods raise on input they cannot handle."""

    @abc.abstractmethod
    def encode(self, value: ta.Any) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> ta.Any:
        raise NotImplementedError


class JsonRpcValueCodec(RpcValueCodec):
    """
    Compact UTF-8 JSON. NaN and infinities are rejected rather than emitted as the non-standard tokens json allows.
    """  # noqa

    def __init__(
            self,
            *,
            ensure_ascii: bool = False,
            sort_keys: bool = False,
    ) -> None:
        super().__init__()

        self._ensure_ascii = ensure_ascii
        self._sort_keys = sort_keys

    def encode(self, value: ta.Any) -> bytes:
        return json.dumps(
            value,
            separators=(',', ':'),
            ensure_ascii=self._ensure_ascii,
            sort_keys=self._sort_keys,
            allow_nan=False,
        ).encode('utf-8')

    def decode(self, data: bytes) -> ta.Any:
        return json.loads(data.decode('utf-8'))


##


class RpcEnvelopeCodec(Abstract):
    @abc.abstractmethod
    def encode(self, envelope: RpcEnvelope) -> bytes:
        """Raises on an unencodable envelope; the pipeline handler reports that inward as an OutboundEncodeFailed."""

        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> RpcEnvelope:
        """Raises RpcProtocolError on data which is not a well-formed envelope."""

        raise NotImplementedError


class RpcValueEnvelopeCodec(RpcEnvelopeCodec):
    """
    Envelopes as tagged mappings over a value codec: `{"type": <kind>, ...fields}`. Error data is spelled
    `{"code", "type", "message", "traceback"?}`. Unknown keys are ignored on decode, for forward compatibility.
    """

    TYPE_KEY: ta.ClassVar[str] = 'type'

    REQUEST_TYPE: ta.ClassVar[str] = 'request'
    RESULT_TYPE: ta.ClassVar[str] = 'result'
    ERROR_TYPE: ta.ClassVar[str] = 'error'
    CANCEL_TYPE: ta.ClassVar[str] = 'cancel'
    NOTIFICATION_TYPE: ta.ClassVar[str] = 'notification'
    PING_TYPE: ta.ClassVar[str] = 'ping'
    PONG_TYPE: ta.ClassVar[str] = 'pong'
    HELLO_TYPE: ta.ClassVar[str] = 'hello'

    def __init__(
            self,
            value_codec: ta.Optional[RpcValueCodec] = None,
    ) -> None:
        super().__init__()

        if value_codec is None:
            value_codec = JsonRpcValueCodec()
        self._value_codec = value_codec

    @property
    def value_codec(self) -> RpcValueCodec:
        return self._value_codec

    #

    def _error_data_to_value(self, e: RpcRemoteErrorData) -> ta.Any:
        dct: ta.Dict[str, ta.Any] = {
            'code': e.code,
            'type': e.remote_type,
            'message': e.message,
        }
        if e.traceback is not None:
            dct['traceback'] = e.traceback
        return dct

    def envelope_to_value(self, envelope: RpcEnvelope) -> ta.Any:
        tk = self.TYPE_KEY

        if isinstance(envelope, RpcRequestMessage):
            return {tk: self.REQUEST_TYPE, 'id': envelope.id, 'method': envelope.method, 'params': envelope.params}

        elif isinstance(envelope, RpcResultMessage):
            return {tk: self.RESULT_TYPE, 'id': envelope.id, 'result': envelope.result}

        elif isinstance(envelope, RpcErrorMessage):
            return {tk: self.ERROR_TYPE, 'id': envelope.id, 'error': self._error_data_to_value(envelope.error)}

        elif isinstance(envelope, RpcCancelMessage):
            return {tk: self.CANCEL_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcNotificationMessage):
            return {tk: self.NOTIFICATION_TYPE, 'method': envelope.method, 'params': envelope.params}

        elif isinstance(envelope, RpcPingMessage):
            return {tk: self.PING_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcPongMessage):
            return {tk: self.PONG_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcHelloMessage):
            if tk in envelope.fields:
                raise ValueError(f'hello fields may not use the {tk!r} key')
            return {tk: self.HELLO_TYPE, **envelope.fields}

        else:
            raise TypeError(envelope)

    #

    @staticmethod
    def _require(dct: ta.Mapping[str, ta.Any], key: str) -> ta.Any:
        try:
            return dct[key]
        except KeyError:
            raise RpcProtocolError(f'envelope missing {key!r}') from None

    @staticmethod
    def _require_str(dct: ta.Mapping[str, ta.Any], key: str) -> str:
        v = RpcValueEnvelopeCodec._require(dct, key)
        if not isinstance(v, str):
            raise RpcProtocolError(f'envelope {key!r} is not a string: {v!r}')
        return v

    def _error_data_from_value(self, v: ta.Any) -> RpcRemoteErrorData:
        if not isinstance(v, ta.Mapping):
            raise RpcProtocolError(f'error is not a mapping: {v!r}')

        tb = v.get('traceback')
        if tb is not None and not isinstance(tb, str):
            raise RpcProtocolError(f'error traceback is not a string: {tb!r}')

        return RpcRemoteErrorData(
            code=self._require_str(v, 'code'),
            remote_type=self._require_str(v, 'type'),
            message=self._require_str(v, 'message'),
            traceback=tb,
        )

    def envelope_from_value(self, value: ta.Any) -> RpcEnvelope:
        if not isinstance(value, ta.Mapping):
            raise RpcProtocolError(f'envelope is not a mapping: {type(value).__name__}')

        ty = self._require_str(value, self.TYPE_KEY)

        try:
            if ty == self.REQUEST_TYPE:
                return RpcRequestMessage(
                    self._require(value, 'id'),
                    self._require_str(value, 'method'),
                    value.get('params'),
                )

            elif ty == self.RESULT_TYPE:
                return RpcResultMessage(self._require(value, 'id'), value.get('result'))

            elif ty == self.ERROR_TYPE:
                return RpcErrorMessage(
                    self._require(value, 'id'),
                    self._error_data_from_value(self._require(value, 'error')),
                )

            elif ty == self.CANCEL_TYPE:
                return RpcCancelMessage(self._require(value, 'id'))

            elif ty == self.NOTIFICATION_TYPE:
                return RpcNotificationMessage(self._require_str(value, 'method'), value.get('params'))

            elif ty == self.PING_TYPE:
                return RpcPingMessage(self._require(value, 'id'))

            elif ty == self.PONG_TYPE:
                return RpcPongMessage(self._require(value, 'id'))

            elif ty == self.HELLO_TYPE:
                return RpcHelloMessage({k: v for k, v in value.items() if k != self.TYPE_KEY})

            else:
                raise RpcProtocolError(f'unknown envelope type: {ty!r}')

        except RpcProtocolError:
            raise

        except (TypeError, ValueError) as e:
            raise RpcProtocolError(f'malformed {ty} envelope: {e}') from e

    #

    def encode(self, envelope: RpcEnvelope) -> bytes:
        return self._value_codec.encode(self.envelope_to_value(envelope))

    def decode(self, data: bytes) -> RpcEnvelope:
        try:
            value = self._value_codec.decode(data)
        except RpcProtocolError:
            raise
        except Exception as e:  # noqa
            raise RpcProtocolError(f'undecodable envelope: {e}') from e

        return self.envelope_from_value(value)


##


class RpcEnvelopeCodecIoPipelineHandler(IoPipelineHandler):
    """RpcFrame <-> RpcEnvelope. Sits between the framing handler and the session (or any handlers between them)."""

    def __init__(
            self,
            codec: ta.Optional[RpcEnvelopeCodec] = None,
            *,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        if codec is None:
            codec = RpcValueEnvelopeCodec()
        self._codec = codec

        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        self._max_frame_bytes = max_frame_bytes

    @property
    def codec(self) -> RpcEnvelopeCodec:
        return self._codec

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            msg = self._codec.decode(msg.data)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcEnvelope):
            try:
                data = self._codec.encode(msg)
            except Exception as e:  # noqa
                ctx.feed_in(RpcSessionMessages.OutboundEncodeFailed(msg, e))
                return

            if len(data) > self._max_frame_bytes:
                ctx.feed_in(RpcSessionMessages.OutboundEncodeFailed(msg, RpcMessageTooLargeError(
                    f'outbound envelope is {len(data)} bytes, exceeding limit {self._max_frame_bytes}',
                )))
                return

            msg = RpcFrame(data)

        ctx.feed_out(msg)


########################################
# ../../../../omcore/rpc/connection.py
"""
The connection: everything a host does with a session other than pumping its driver, written once, async-colored.

A connection sits on a runtime (see `runtime.py`), which owns the driver and decides how waiting, pumping, and handler
execution happen. The connection owns the rest: id assignment, the waiters callers block on, send fences, demultiplexing
session events, running handlers and turning their outcomes into responses, error conversion, and close sequencing.

Under a sync runtime nothing in here ever actually suspends, so `SyncRpcConnection` drives it with `sync_await`. Under
an asyncio runtime it is used directly. Handlers are likewise written once, as coroutines; under a sync runtime they run
inline on the pump and must never actually suspend.

The split:
 - `BaseRpcConnection` is protocol-agnostic: lifecycle, waiters and send fences keyed by opaque keys, the request /
   abandon pattern, close sequencing, and close callbacks. It knows nothing of envelopes, events, or handlers, so a
   connection for another session vocabulary - JSON-RPC's, say - is a subclass which demultiplexes its own events onto
   these helpers.
 - `RpcConnection` is this toolbox's protocol: its envelopes, its session events, `RpcHandler`, and its error mapping.

The connection speaks wire values: params and results are whatever the envelope codec's value codec carries. Typed
calls and typed handlers sit above it, in `serde.py`.
"""


log = get_module_logger(globals())  # noqa


##


class BaseRpcConnection(RpcRuntimeSink, Abstract):
    """
    Must be started (via `start` or `async with`) before use. Closing is graceful by default: new outbound requests are
    refused, in-flight work on both sides is given the session's drain time to finish, and output is flushed.

    A handler which wants to close its own connection should not await a graceful close from within a request handler:
    the close waits for in-flight requests - that one included - to be answered, so it would wait out the drain
    timeout. Respond first, and close from elsewhere.

    Subclasses implement `on_event`, demultiplexing their session's events onto the helpers here, and the hooks naming
    their session's close and cancel commands.
    """

    def __init__(
            self,
            runtime: RpcRuntime,
            *,
            send_timeout_s: ta.Optional[float] = None,
    ) -> None:
        """
        `send_timeout_s` bounds how long a send waits for its bytes to reach the transport when the peer is not keeping
        up; None waits indefinitely, in which case the session's write timeout still bounds a stalled transport.
        """

        super().__init__()

        self._runtime = runtime
        self._send_timeout_s = send_timeout_s

        self._started = False
        self._closing = False
        self._closed = False
        self._close_exc: ta.Optional[BaseException] = None
        self._driver_done = False
        self._finished = False
        self._output_paused = False

        # Created on start, so that under asyncio it is made on the loop which will use it.
        self._done: ta.Optional[AsynclitePromise] = None

        self._waiters: ta.Dict[ta.Any, AsynclitePromise] = {}
        self._send_fences: ta.Dict[ta.Any, AsynclitePromise] = {}

        self._close_callbacks: ta.List[RpcConnectionCloseCallback] = []

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._runtime!r}>'

    ##
    # hooks

    @abc.abstractmethod
    def _make_close_command(self, graceful: bool) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def _default_close_timeout_s(self, graceful: bool) -> ta.Optional[float]:
        """
        How long `close` waits by default before aborting the transport. The session bounds draining and the write
        timeout handler bounds flushing, but the driver's final transport flush happens outside the pipeline's reach,
        so closing needs its own bound: a peer which stops reading would otherwise hang a close forever.
        """

        raise NotImplementedError

    ##
    # properties

    @property
    def runtime(self) -> RpcRuntime:
        return self._runtime

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def close_exception(self) -> ta.Optional[BaseException]:
        """Why the connection failed, if it did. A clean close leaves this None."""

        return self._close_exc

    @property
    def output_paused(self) -> bool:
        """Whether the transport's write buffer is over its high watermark. Advisory: sends block on their own."""

        return self._output_paused

    ##
    # lifecycle

    def add_close_callback(self, callback: RpcConnectionCloseCallback) -> None:
        """
        Registers a callback, given the connection, run synchronously as the last step of teardown: after every pending
        call has been failed and before `wait_closed` returns. Runs right away if the connection has already finished.
        """

        if self._finished:
            callback(self)
            return
        self._close_callbacks.append(callback)

    async def start(self) -> None:
        check.state(not self._started, 'already started')
        check.state(not self._closed, 'already closed')

        self._started = True
        self._done = self._runtime.make_promise()
        await self._runtime.start(self)

    async def __aenter__(self: BaseRpcConnectionT) -> BaseRpcConnectionT:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close(graceful=exc_type is None)

    async def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> None:
        """
        Closes the connection and waits for it to finish, gracefully by default.

        The wait is bounded: by `timeout_s` if given, else by `_default_close_timeout_s`. On expiry the transport is
        aborted. Never raises for a connection which failed earlier - the failure is available as `close_exception`.
        """

        if timeout_s is RpcUnspecified:
            timeout_s = self._default_close_timeout_s(graceful)

        self._closing = True

        if not self._started:
            self._mark_closed(None)
            await self._runtime.close()
            self._finish()
            return

        done = check.not_none(self._done)
        if not done.is_done():
            if not self._closed:
                self._runtime.enqueue(self._make_close_command(graceful))

            try:
                await done.wait(timeout=ta.cast(ta.Optional[float], timeout_s))

            except AsynclitePromiseWaitTimeoutError:
                log.warning('Close did not complete within %r seconds, aborting transport', timeout_s)

            except BaseException:
                # Interrupted - cancelled, say: nothing may be left open.
                await self._runtime.close()
                raise

        await self._runtime.close()
        await self.wait_closed()

    async def wait_closed(self) -> None:
        """
        Waits until the connection has closed for any reason and its runtime has finished: under asyncio the pump and
        every handler task. Under a sync runtime this pumps the connection until the peer goes away, which makes it the
        serving loop of a sync server - see `serve`.
        """

        if not self._started:
            check.state(self._closed, 'connection neither started nor closed')
            return

        await check.not_none(self._done).wait()
        await self._runtime.wait_closed()

    async def serve(self) -> None:
        """Serves until the connection closes. Equivalent to `wait_closed`; reads better at the end of a server."""

        await self.wait_closed()

    ##
    # closure

    def _closed_error(self) -> BaseException:
        """The error closure fails things with. A subclass for another vocabulary may raise its own closed error."""

        if (exc := self._close_exc) is not None:
            err = RpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return RpcConnectionClosedError('connection closed')

    def _send_timeout_error(self) -> BaseException:
        return RpcTimeoutError(f'send timed out after {self._send_timeout_s!r} seconds waiting for the transport')

    def _check_usable(self) -> None:
        check.state(self._started, 'connection not started')
        if self._closed or self._closing:
            raise self._closed_error()

    def _mark_closed(self, exc: ta.Optional[BaseException]) -> None:
        """Records closure and fails everything still waiting. Idempotent: the first reason wins."""

        if self._closed:
            return
        self._closed = True
        self._close_exc = exc

        for dct in (self._waiters, self._send_fences):
            ps = list(dct.values())
            dct.clear()
            for p in ps:
                if not p.is_done():
                    # A fresh error each: raising one instance from many places tangles its traceback.
                    p.set_error(self._closed_error())

        self._runtime.cancel_all()

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True

        callbacks, self._close_callbacks = self._close_callbacks, []
        for cb in callbacks:
            try:
                cb(self)
            except Exception:  # noqa
                # A close callback is a courtesy to its registrant; its failure is not the connection's, and nothing
                # here may prevent the connection from finishing.
                log.exception('Error in rpc connection close callback %r', cb)

        if (done := self._done) is not None and not done.is_done():
            done.set_value(None)

    def on_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        self._driver_done = True
        self._mark_closed(exc)
        self._finish()

    ##
    # sending and waiting

    def _enqueue(self, *commands: ta.Any) -> bool:
        """Hands commands to the driver without waiting, returning False if it is no longer accepting them."""

        if self._driver_done:
            return False
        return self._runtime.enqueue(*commands)

    async def _send(self, cmd: ta.Any, key: ta.Any) -> None:
        """
        Hands a send command to the driver and waits until its fence, registered under `key`, is resolved - by the
        session reporting the command sent - or failed - by the command failing before it could be.

        Waiting is what makes backpressure real: sent means the bytes crossed into the transport, so a peer which stops
        reading stalls the sender here rather than growing buffers without bound. The wait is bounded by
        `send_timeout_s`.
        """

        self._check_usable()

        check.not_in(key, self._send_fences)
        fence = self._runtime.make_promise()
        self._send_fences[key] = fence
        try:
            if not self._enqueue(cmd):
                raise self._closed_error()

            try:
                await fence.wait(timeout=self._send_timeout_s)
            except AsynclitePromiseWaitTimeoutError as e:
                raise self._send_timeout_error() from e

        finally:
            if self._send_fences.get(key) is fence:
                del self._send_fences[key]

    def _add_waiter(self, key: ta.Any) -> AsynclitePromise:
        check.not_in(key, self._waiters, 'duplicate waiter key')
        waiter = self._runtime.make_promise()
        self._waiters[key] = waiter
        return waiter

    def _discard_waiter(self, key: ta.Any, waiter: AsynclitePromise) -> bool:
        """Drops a waiter if still registered. Returns whether it was abandoned: dropped with no outcome."""

        if self._waiters.get(key) is not waiter:
            return False
        del self._waiters[key]
        return not waiter.is_done()

    async def _send_and_wait(
            self,
            cmd: ta.Any,
            send_key: ta.Any,
            waiter_key: ta.Any,
            abandon_command: ta.Optional[ta.Callable[[], ta.Any]] = None,
    ) -> ta.Any:
        """
        Sends a command and waits for the outcome resolved under `waiter_key`. A caller which gives up first -
        cancelled, or its send timed out - abandons it, and `abandon_command`, if given, makes the command telling the
        session so.
        """

        waiter = self._add_waiter(waiter_key)
        try:
            await self._send(cmd, send_key)
            return await waiter.wait()

        except BaseException:
            if self._discard_waiter(waiter_key, waiter) and abandon_command is not None:
                self._enqueue(abandon_command())
            raise

        finally:
            self._discard_waiter(waiter_key, waiter)

    #

    @staticmethod
    def _resolve(dct: ta.Dict[ta.Any, AsynclitePromise], key: ta.Any, value: ta.Any) -> None:
        if (p := dct.pop(key, None)) is not None and not p.is_done():
            p.set_value(value)

    @staticmethod
    def _fail(dct: ta.Dict[ta.Any, AsynclitePromise], key: ta.Any, exc: BaseException) -> None:
        if (p := dct.pop(key, None)) is not None and not p.is_done():
            p.set_error(exc)

    def _resolve_waiter(self, key: ta.Any, value: ta.Any) -> None:
        self._resolve(self._waiters, key, value)

    def _fail_waiter(self, key: ta.Any, exc: BaseException) -> None:
        self._fail(self._waiters, key, exc)

    def _resolve_fence(self, key: ta.Any) -> None:
        self._resolve(self._send_fences, key, None)

    def _fail_fence(self, key: ta.Any, exc: BaseException) -> None:
        self._fail(self._send_fences, key, exc)

    def _set_output_paused(self, paused: bool) -> None:
        self._output_paused = paused

    ##
    # handlers

    async def _spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        await self._runtime.spawn(key, fn)

    def _cancel_handler(self, key: ta.Any) -> None:
        self._runtime.cancel(key)

    def _is_cancelled_exception(self, exc: BaseException) -> bool:
        return self._runtime.is_cancelled_exception(exc)


##


class RpcConnection(BaseRpcConnection):
    """A connection speaking this toolbox's protocol, to a session built by `rpc_build_pipeline_spec`."""

    def __init__(
            self,
            runtime: RpcRuntime,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            handler: ta.Optional[RpcHandler] = None,
            id_creator: ta.Optional[RpcIdCreatorLike] = None,
            send_timeout_s: ta.Optional[float] = None,
            notification_error_handler: ta.Optional[RpcNotificationErrorHandler] = None,
    ) -> None:
        super().__init__(
            runtime,
            send_timeout_s=send_timeout_s,
        )

        self._config = config
        self._handler = handler
        self._id_creator = rpc_id_creator_of(id_creator)
        self._notification_error_handler = notification_error_handler

    @property
    def config(self) -> RpcConfig:
        return self._config

    @property
    def handler(self) -> ta.Optional[RpcHandler]:
        return self._handler

    def set_handler(self, handler: ta.Optional[RpcHandler]) -> None:
        """May be called at any time; requests already being handled keep the handler they started with."""

        self._handler = handler

    ##
    # hooks

    def _make_close_command(self, graceful: bool) -> ta.Any:
        return RpcSessionMessages.Close(graceful=graceful)

    def _default_close_timeout_s(self, graceful: bool) -> ta.Optional[float]:
        c = self._config
        parts = [t for t in ((c.close_drain_timeout_s if graceful else None), c.write_timeout_s) if t is not None]
        return sum(parts) if parts else None

    ##
    # outbound

    async def send_request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> RpcResponseMessage:
        """
        Sends a request and waits for its raw response envelope.

        A timeout of RpcUnspecified uses the configured default; None waits indefinitely. A caller which gives up -
        cancelled, or its send timed out - abandons the request, which also tells the peer if so configured.
        """

        self._check_usable()

        rid = self._id_creator()
        request = RpcRequestMessage(rid, method, params)

        return await self._send_and_wait(
            RpcSessionMessages.SendRequest(request, timeout_s),
            ('request', rid),
            ('request', rid),
            lambda: RpcSessionMessages.CancelRequest(rid, notify_peer=self._config.cancel_abandoned_requests),
        )

    @staticmethod
    def result_of(response: RpcResponseMessage) -> ta.Any:
        """The result a response carries, or its error raised as an RpcRemoteError."""

        if isinstance(response, RpcResultMessage):
            return response.result
        elif isinstance(response, RpcErrorMessage):
            raise rpc_remote_error_for_data(response.error)
        else:
            raise TypeError(response)

    async def request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> ta.Any:
        return self.result_of(await self.send_request(method, params, timeout_s=timeout_s))

    async def notify(self, method: str, params: ta.Any = None) -> None:
        cmd = RpcSessionMessages.SendNotification(RpcNotificationMessage(method, params))
        await self._send(cmd, ('command', id(cmd)))

    def notify_nowait(self, method: str, params: ta.Any = None) -> None:
        """
        Sends a notification without waiting for its bytes to reach the transport: no backpressure, but usable where
        nothing may wait, as in an fdio callback. Notifications sent either way keep their order.
        """

        self._check_usable()
        if not self._enqueue(RpcSessionMessages.SendNotification(RpcNotificationMessage(method, params))):
            raise self._closed_error()

    async def ping(self, *, timeout_s: RpcTimeoutArg = RpcUnspecified) -> None:
        """Round-trips a ping, which the peer's session answers without involving its handler."""

        self._check_usable()

        pid = self._id_creator()
        await self._send_and_wait(
            RpcSessionMessages.SendPing(RpcPingMessage(pid), timeout_s),
            ('ping', pid),
            ('ping', pid),
        )

    ##
    # inbound

    def _error_data_for(self, exc: BaseException, code: ta.Optional[str] = None) -> RpcRemoteErrorData:
        if code is None:
            code = RpcErrorCodes.METHOD_NOT_FOUND if isinstance(exc, RpcMethodNotFoundError) else RpcErrorCodes.REMOTE

        tb: ta.Optional[str] = None
        if self._config.include_tracebacks and (mx := self._config.max_traceback_chars):
            tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if len(tb) > mx:
                tb = tb[-mx:]

        return RpcRemoteErrorData(
            code=code,
            remote_type=rpc_exception_type_name(exc),
            message=str(exc),
            traceback=tb,
        )

    async def _run_request_handler(self, request: RpcRequestMessage) -> None:
        response: RpcResponseMessage
        try:
            if (h := self._handler) is None:
                raise RpcMethodNotFoundError(request.method)

            result = await h.handle_request_message(request)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e):
                # The session drops this if it already gave up on the request - the peer cancelled it, or it timed out
                # - but a handler cancelled from elsewhere leaves a peer still waiting, which deserves an answer.
                self._enqueue(RpcSessionMessages.SendResponse(RpcErrorMessage(
                    request.id,
                    self._error_data_for(e, RpcErrorCodes.CANCELLED),
                )))
                raise

            if not isinstance(e, Exception):
                raise

            if isinstance(e, RpcHandlerError):
                # An answer the handler chose: sent exactly as it is.
                response = RpcErrorMessage(request.id, e.data)
            else:
                response = RpcErrorMessage(request.id, self._error_data_for(e))

        else:
            response = RpcResultMessage(request.id, result)

        self._enqueue(RpcSessionMessages.SendResponse(response))

    def _report_notification_error(self, notification: RpcNotificationMessage, exc: BaseException) -> None:
        if (neh := self._notification_error_handler) is None:
            log.error('Unhandled error handling rpc notification %r', notification.method, exc_info=exc)
            return

        try:
            neh(notification, exc)
        except Exception:  # noqa
            log.exception('Error in rpc notification error handler')

    async def _run_notification_handler(self, h: RpcHandler, notification: RpcNotificationMessage) -> None:
        try:
            await h.handle_notification(notification.method, notification.params)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e) or not isinstance(e, Exception):
                raise

            self._report_notification_error(notification, e)

    async def _on_notification_received(self, notification: RpcNotificationMessage) -> None:
        if (h := self._handler) is None:
            log.debug('Dropping rpc notification with no handler: %r', notification.method)
            return

        try:
            if h.handle_notification_inline(notification.method, notification.params):
                return
        except Exception as e:  # noqa
            self._report_notification_error(notification, e)
            return

        await self._spawn(None, functools.partial(self._run_notification_handler, h, notification))

    ##
    # RpcRuntimeSink

    @staticmethod
    def _send_key(cmd: RpcSessionMessages.Command) -> ta.Any:
        if isinstance(cmd, RpcSessionMessages.SendRequest):
            return ('request', cmd.request.id)
        if isinstance(cmd, RpcSessionMessages.SendPing):
            return ('ping', cmd.ping.id)
        return ('command', id(cmd))

    async def on_event(self, event: ta.Any) -> None:
        if isinstance(event, RpcSessionMessages.RequestReceived):
            await self._spawn(event.request.id, functools.partial(self._run_request_handler, event.request))

        elif isinstance(event, RpcSessionMessages.ResponseReceived):
            self._resolve_waiter(('request', event.request.id), event.response)

        elif isinstance(event, RpcSessionMessages.NotificationReceived):
            await self._on_notification_received(event.notification)

        elif isinstance(event, RpcSessionMessages.Sent):
            self._resolve_fence(self._send_key(event.command))

        elif isinstance(event, RpcSessionMessages.RequestFailed):
            key = ('request', event.request.id)
            self._fail_fence(key, event.exc)
            self._fail_waiter(key, event.exc)

        elif isinstance(event, RpcSessionMessages.RequestHandlingAborted):
            self._cancel_handler(event.request.id)

        elif isinstance(event, RpcSessionMessages.PongReceived):
            self._resolve_waiter(('ping', event.ping.id), None)

        elif isinstance(event, RpcSessionMessages.PingFailed):
            key = ('ping', event.ping.id)
            self._fail_fence(key, event.exc)
            self._fail_waiter(key, event.exc)

        elif isinstance(event, RpcSessionMessages.OutputPaused):
            self._set_output_paused(True)

        elif isinstance(event, RpcSessionMessages.OutputResumed):
            self._set_output_paused(False)

        elif isinstance(event, RpcSessionMessages.Closed):
            self._mark_closed(event.exc)

        else:
            await self._on_other_event(event)

    async def _on_other_event(self, event: ta.Any) -> None:
        """
        An output which is not a session event: one from an optional handler, such as a completed handshake. Subclasses
        which install such handlers handle their events here.
        """

        if isinstance(event, RpcInfoEvent):
            log.debug('Unconsumed rpc connection event: %r', event)
        else:
            log.warning('Unexpected rpc connection event: %r', event)


##


class BaseSyncRpcConnection(Abstract):
    """
    The sync facade over a connection on a sync-pumping runtime: every method drives the async connection with
    `sync_await`, and pumps the driver in the calling thread while it waits.

    Not thread-safe. Nested use from the thread already using it - a handler calling back out to the peer while running
    inline on the pump - is permitted; use from a second thread at the same time raises.
    """

    def __init__(self, connection: BaseRpcConnection) -> None:
        super().__init__()

        self._c = connection
        self._lock = threading.RLock()

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._c!r}>'

    def run(self, aw: ta.Awaitable[T]) -> T:
        """
        Drives an awaitable written against the async connection - a typed caller's call, say - to completion in this
        thread, pumping the connection while it waits. The awaitable must await nothing but this connection.
        """

        if not self._lock.acquire(blocking=False):
            if hasattr(aw, 'close'):
                aw.close()
            raise RuntimeError(f'{type(self).__name__} is in use by another thread')
        try:
            return sync_await(aw)
        finally:
            self._lock.release()

    #

    @property
    def is_started(self) -> bool:
        return self._c.is_started

    @property
    def is_closed(self) -> bool:
        return self._c.is_closed

    @property
    def close_exception(self) -> ta.Optional[BaseException]:
        return self._c.close_exception

    def add_close_callback(self, callback: RpcConnectionCloseCallback) -> None:
        self._c.add_close_callback(callback)

    #

    def start(self) -> None:
        self.run(self._c.start())

    def __enter__(self: BaseSyncRpcConnectionT) -> BaseSyncRpcConnectionT:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close(graceful=exc_type is None)

    def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> None:
        self.run(self._c.close(graceful=graceful, timeout_s=timeout_s))

    def wait_closed(self) -> None:
        self.run(self._c.wait_closed())

    def serve(self) -> None:
        self.run(self._c.serve())


class SyncRpcConnection(BaseSyncRpcConnection):
    def __init__(self, connection: RpcConnection) -> None:
        super().__init__(connection)

        self._rc = connection

    @property
    def connection(self) -> RpcConnection:
        return self._rc

    @property
    def config(self) -> RpcConfig:
        return self._rc.config

    def set_handler(self, handler: ta.Optional[RpcHandler]) -> None:
        self._rc.set_handler(handler)

    #

    def send_request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> RpcResponseMessage:
        return self.run(self._rc.send_request(method, params, timeout_s=timeout_s))

    def request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> ta.Any:
        return self.run(self._rc.request(method, params, timeout_s=timeout_s))

    def notify(self, method: str, params: ta.Any = None) -> None:
        self.run(self._rc.notify(method, params))

    def ping(self, *, timeout_s: RpcTimeoutArg = RpcUnspecified) -> None:
        self.run(self._rc.ping(timeout_s=timeout_s))


########################################
# ../../environment/remote/server.py
"""
The target side of the remote environment: `RemoteEnvironmentService` answers for the environment the remote agent runs
in, through a `LocalEnvironmentOps` there. Lite: this runs inside the remote agent amalgam under Python 3.8+.
"""


##


class RemoteEnvironmentService:
    def __init__(
            self,
            *,
            local_ops: ta.Optional[LocalEnvironmentOps] = None,
    ) -> None:
        super().__init__()

        if local_ops is None:
            local_ops = LocalEnvironmentOps()

        self._local_ops = local_ops

    async def info(self, params: ta.Any) -> ta.Any:
        p: RemoteEnvironmentInfoParams = unmarshal_obj(params, RemoteEnvironmentInfoParams)
        i = await self._local_ops.inspect_environment(cwd=p.cwd)
        return marshal_obj(RemoteEnvironmentInfo(
            cwd=i.cwd,

            system=i.system,
            release=i.release,
            machine=i.machine,

            hostname=i.hostname,

            user=RemoteEnvironmentInfo.User(
                name=i.user.name,
                home=i.user.home,
                shell=i.user.shell,
            ) if i.user is not None else None,

            container=i.container,
        ))

    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return {
            REMOTE_ENVIRONMENT_INFO_METHOD: self.info,
        }


########################################
# ../../fs/remote/server.py
"""
The target side of the remote filesystem: `RemoteFsService` serves the `FsOps` operations on behalf of a host's
`RemoteFsOps`, including the chunked reads and staged writes through which content larger than one chunk crosses the
connection (see `protocol.py`). The operations which are the same call on either side - paths, metadata, and a write
that fits one chunk - are a `LocalFsOps`'s; the handle-based reads and staged writes are the service's own, so that
content streams through it rather than being held whole. Lite: this runs inside the remote agent amalgam under Python
3.8+, and imports nothing but the standard library, `omcore.lite`, the rpc package, and the shared lite filesystem
helpers and ops.
"""


##


class _RemoteFsOpenRead:
    """
    A file held open across the chunks of one read. The size seen at the open bounds what is served, so the whole read
    is of the file as it was then: a writer replacing it atomically leaves this inode untouched.
    """

    def __init__(self, file: ta.BinaryIO) -> None:
        super().__init__()

        self.file = file
        self.size = os.fstat(file.fileno()).st_size
        self.hasher = hashlib.sha256()

    def read(self, max_bytes: int) -> ta.Tuple[bytes, bool]:
        """The next piece, and whether it was the last."""

        data = self.file.read(max_bytes)
        self.hasher.update(data)
        done = not data or self.file.tell() >= self.size
        return data, done

    def close(self) -> None:
        self.file.close()


class RemoteFsService:
    def __init__(
            self,
            *,
            local_ops: ta.Optional[LocalFsOps] = None,
            max_chunk_bytes: int = REMOTE_FS_MAX_CHUNK_BYTES,
            max_open_handles: int = 64,
    ) -> None:
        super().__init__()

        check.arg(0 < max_chunk_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)
        check.arg(max_open_handles > 0)

        if local_ops is None:
            local_ops = LocalFsOps()

        self._local_ops = local_ops
        self._max_chunk_bytes = max_chunk_bytes
        self._max_open_handles = max_open_handles

        self._reads: ta.Dict[str, _RemoteFsOpenRead] = {}
        self._writes: ta.Dict[str, FsStagedWrite] = {}
        self._next_handle = 1
        self._closed = False

    @property
    def num_open_handles(self) -> int:
        return len(self._reads) + len(self._writes)

    def _new_handle(self, prefix: str) -> str:
        if self._closed:
            raise RuntimeError('remote filesystem service is closed')
        if self.num_open_handles >= self._max_open_handles:
            raise RuntimeError(f'too many open remote filesystem handles: {self._max_open_handles}')
        handle = f'{prefix}{self._next_handle}'
        self._next_handle += 1
        return handle

    def _chunk_bytes(self, requested: int) -> int:
        return min(requested, self._max_chunk_bytes)

    @staticmethod
    def _entry(e: FsEntry) -> RemoteFsEntry:
        return RemoteFsEntry(
            path=e.path,
            resolved_path=e.resolved_path,

            is_dir=e.is_dir,
            is_file=e.is_file,
            is_symlink=e.is_symlink,

            mode=e.mode,
            ino=e.ino,
            dev=e.dev,
            nlink=e.nlink,
            uid=e.uid,
            gid=e.gid,
            size=e.size,

            atime_ns=e.atime_ns,
            mtime_ns=e.mtime_ns,
            ctime_ns=e.ctime_ns,

            blksize=e.blksize,
            blocks=e.blocks,
            rdev=e.rdev,

            flags=e.flags,
            gen=e.gen,
            birthtime_ns=e.birthtime_ns,
        )

    #

    async def resolve_path(self, params: ta.Any) -> str:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return await self._local_ops.resolve_path(p.path)

    async def stat(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return marshal_obj(self._entry(await self._local_ops.stat(p.path)))

    async def list_dir(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return marshal_obj(
            [self._entry(e) for e in await self._local_ops.list_dir(p.path)],
            ta.List[RemoteFsEntry],
        )

    async def glob(self, params: ta.Any) -> ta.Any:
        p: RemoteFsGlobParams = unmarshal_obj(params, RemoteFsGlobParams)
        r = await self._local_ops.glob(
            p.pattern,
            max_results=p.max_results,
        )
        return marshal_obj(RemoteFsGlobResult(
            entries=[self._entry(e) for e in r.entries],
            has_more=r.has_more,
        ))

    #

    def _lookup_read(self, handle: str) -> _RemoteFsOpenRead:
        try:
            return self._reads[handle]
        except KeyError:
            raise ValueError(f'No such remote filesystem read: {handle!r}') from None

    async def read_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsReadFileParams = unmarshal_obj(params, RemoteFsReadFileParams)
        if self._closed:
            raise RuntimeError('remote filesystem service is closed')

        rd = _RemoteFsOpenRead(open(p.path, 'rb'))  # noqa
        try:
            data, done = rd.read(self._chunk_bytes(p.max_bytes))
            if done:
                return marshal_obj(RemoteFsReadFileResult(
                    data=data,
                    digest=rd.hasher.hexdigest(),
                    handle=None,
                ))

            handle = self._new_handle('r')

        except BaseException:
            rd.close()
            raise

        self._reads[handle] = rd
        return marshal_obj(RemoteFsReadFileResult(
            data=data,
            digest=None,
            handle=handle,
        ))

    async def read_chunk(self, params: ta.Any) -> ta.Any:
        p: RemoteFsReadChunkParams = unmarshal_obj(params, RemoteFsReadChunkParams)
        rd = self._lookup_read(p.handle)

        try:
            data, done = rd.read(self._chunk_bytes(p.max_bytes))
        except BaseException:
            self._reads.pop(p.handle, None)
            rd.close()
            raise

        if not done:
            return marshal_obj(RemoteFsReadChunkResult(
                data=data,
                digest=None,
            ))

        self._reads.pop(p.handle, None)
        rd.close()
        return marshal_obj(RemoteFsReadChunkResult(
            data=data,
            digest=rd.hasher.hexdigest(),
        ))

    async def read_abort(self, params: ta.Any) -> None:
        # Idempotent: the handle may already have gone with its last chunk.
        p: RemoteFsHandleParams = unmarshal_obj(params, RemoteFsHandleParams)
        if (rd := self._reads.pop(p.handle, None)) is not None:
            rd.close()

    #

    def _lookup_write(self, handle: str) -> FsStagedWrite:
        try:
            return self._writes[handle]
        except KeyError:
            raise ValueError(f'No such remote filesystem write: {handle!r}') from None

    async def write_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsWriteFileParams = unmarshal_obj(params, RemoteFsWriteFileParams)
        check.arg(len(p.content) <= self._max_chunk_bytes)
        r = await self._local_ops.write_file(
            p.path,
            p.content,
            overwrite=p.overwrite,
            expected_digest=p.expected_digest,
        )
        return marshal_obj(RemoteFsWriteFileResult(
            created=r.created,
        ))

    async def write_begin(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        handle = self._new_handle('w')
        self._writes[handle] = FsStagedWrite(p.path)
        return marshal_obj(RemoteFsHandleResult(
            handle=handle,
        ))

    async def write_chunk(self, params: ta.Any) -> None:
        p: RemoteFsWriteChunkParams = unmarshal_obj(params, RemoteFsWriteChunkParams)
        stage = self._lookup_write(p.handle)
        try:
            check.arg(len(p.data) <= self._max_chunk_bytes)
            stage.write(p.data)
        except BaseException:
            # A stage that failed to take a piece cannot be completed: it is discarded, and the commit will say so.
            self._writes.pop(p.handle, None)
            stage.abort()
            raise

    async def write_commit(self, params: ta.Any) -> ta.Any:
        p: RemoteFsWriteCommitParams = unmarshal_obj(params, RemoteFsWriteCommitParams)
        stage = self._lookup_write(p.handle)
        self._writes.pop(p.handle, None)
        # Finishes the stage either way, cleaning up after a failure.
        created = stage.commit(
            overwrite=p.overwrite,
            expected_digest=p.expected_digest,
        )
        return marshal_obj(RemoteFsWriteFileResult(
            created=created,
        ))

    async def write_abort(self, params: ta.Any) -> None:
        # Idempotent: the handle may already have gone with a failed chunk or commit.
        p: RemoteFsHandleParams = unmarshal_obj(params, RemoteFsHandleParams)
        if (stage := self._writes.pop(p.handle, None)) is not None:
            stage.abort()

    #

    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return {
            REMOTE_FS_RESOLVE_PATH_METHOD: self.resolve_path,
            REMOTE_FS_STAT_METHOD: self.stat,
            REMOTE_FS_LIST_DIR_METHOD: self.list_dir,
            REMOTE_FS_GLOB_METHOD: self.glob,

            REMOTE_FS_READ_FILE_METHOD: self.read_file,
            REMOTE_FS_READ_CHUNK_METHOD: self.read_chunk,
            REMOTE_FS_READ_ABORT_METHOD: self.read_abort,

            REMOTE_FS_WRITE_FILE_METHOD: self.write_file,
            REMOTE_FS_WRITE_BEGIN_METHOD: self.write_begin,
            REMOTE_FS_WRITE_CHUNK_METHOD: self.write_chunk,
            REMOTE_FS_WRITE_COMMIT_METHOD: self.write_commit,
            REMOTE_FS_WRITE_ABORT_METHOD: self.write_abort,
        }

    async def aclose(self) -> None:
        """Releases every open read and discards every unfinished write - a host that has gone cannot finish them."""

        self._closed = True

        reads, self._reads = self._reads, {}
        for rd in reads.values():
            rd.close()

        writes, self._writes = self._writes, {}
        for stage in writes.values():
            stage.abort()


########################################
# ../../../../omcore/rpc/specs.py


##


def rpc_build_pipeline_spec(
        config: RpcConfig = RpcConfig.DEFAULT,
        *,
        outermost_handlers: ta.Sequence[IoPipelineHandler] = (),
        transport_handlers: ta.Sequence[IoPipelineHandler] = (),
        innermost_handlers: ta.Sequence[IoPipelineHandler] = (),

        framing_handler: ta.Optional[IoPipelineHandler] = None,
        envelope_codec: ta.Optional[RpcEnvelopeCodec] = None,
        envelope_codec_handler: ta.Optional[IoPipelineHandler] = None,
        handshake_handler: ta.Optional[IoPipelineHandler] = None,
        between_handlers: ta.Sequence[IoPipelineHandler] = (),
        session_handler: ta.Optional[RpcSessionIoPipelineHandler] = None,

        without_flow: bool = False,

        raise_immediately: bool = False,

        metadata: ta.Sequence[IoPipelineMetadata] = (),
        services: ta.Sequence[IoPipelineService] = (),
) -> IoPipeline.Spec:
    """
    Assemble the full pipeline for one rpc connection, outermost (transport side) first.

    The session handler is innermost so that everything a connection enqueues reaches it untouched and everything it
    emits reaches the connection untouched. Framing and the envelope codec sit outside it; the optional handshake,
    keepalive, and idle handlers, and any `between_handlers`, sit between codec and session so they see complete
    envelopes, which makes a slow trickle of bytes that never completes an envelope count as idle. The handshake sits
    nearest the codec, so nothing - keepalive pings included - crosses before the greetings have.

    Optional handlers are passed in as instances rather than switched on by flags, so that this module imports none of
    them and an amalgam carries only those its callers construct: `transport_handlers` sit just inside the outbound
    buffering, where a TLS handler goes (`SslIoPipelineHandler`), and `outermost_handlers` outside everything, where a
    `LoggingIoPipelineHandler` goes.
    """

    if without_flow:
        check.arg(config.inflight_limit_policy != 'pause', "the 'pause' policy requires flow control")

    if framing_handler is None:
        framing_handler = RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=config.max_frame_bytes)

    if envelope_codec_handler is None:
        envelope_codec_handler = RpcEnvelopeCodecIoPipelineHandler(
            envelope_codec,
            max_frame_bytes=config.max_frame_bytes,
        )
    else:
        check.none(envelope_codec, 'envelope_codec is ignored when envelope_codec_handler is given')

    if session_handler is None:
        session_handler = RpcSessionIoPipelineHandler(config)

    keepalive_handlers: ta.List[IoPipelineHandler] = []
    if (ki := config.keepalive_interval_s) is not None:
        keepalive_handlers.append(RpcKeepaliveIoPipelineHandler(
            interval_s=ki,
            timeout_s=check.not_none(config.keepalive_timeout_s),
        ))

    return IoPipeline.Spec(
        [
            *outermost_handlers,

            *([OutboundBytesBufferIoPipelineHandler()] if not without_flow else []),

            *transport_handlers,

            *([WriteTimeoutIoPipelineHandler(t)] if (t := config.write_timeout_s) is not None else []),

            framing_handler,

            envelope_codec_handler,

            *([handshake_handler] if handshake_handler is not None else []),

            *keepalive_handlers,

            *([IdleStateIoPipelineHandler(all_idle_timeout_s=t)] if (t := config.idle_timeout_s) is not None else []),

            *between_handlers,

            session_handler,

            *innermost_handlers,
        ],

        config=IoPipeline.Config.DEFAULT.update(
            raise_immediately=raise_immediately,
        ),

        metadata=metadata,

        services=[
            *([StubIoPipelineFlowService(auto_read=config.inflight_limit_policy != 'pause')] if not without_flow else []),  # noqa
            *services,
        ],
    )


########################################
# ../../../core/processes/remote/server.py
"""
The target side of remote process management: `RemoteProcessService` spawns, streams, signals, and reaps children on
behalf of a host's `RemoteProcessManager`, over the rpc connection it is given. Lite: this runs inside the remote agent
amalgam under Python 3.8+, and imports nothing but the standard library, `omcore.lite`, and `omcore.rpc`.

Children run in owned process groups and keep an unreaped leader until `close` deliberately reaps them, so their pid
and pgid stay ours to signal. Exits are observed by one SIGCHLD handler probing every unexited child with a
non-blocking, non-reaping `waitid`, which requires the event loop to run in the main thread. Output chunks, end of
output, and exits reach the host as notifications in wire order, and the reply to a `close` is therefore an ordering
barrier for everything sent before it.
"""


##


_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE = 64 * 1024

_REMOTE_CLD_EXITED = getattr(os, 'CLD_EXITED', 1)
_REMOTE_CLD_KILLED = getattr(os, 'CLD_KILLED', 2)
_REMOTE_CLD_DUMPED = getattr(os, 'CLD_DUMPED', 3)

_REMOTE_DARWIN_P_PID = 1
_REMOTE_DARWIN_WEXITED = 0x04
_REMOTE_DARWIN_WNOWAIT = 0x20

_REMOTE_PTY_CHILD_CODE = """\
import fcntl
import json
import os
import signal
import sys
import termios


if __name__ == '__main__':
    argv = json.loads(sys.argv[1])
    # This interpreter ignored these at its own startup, and an ignored disposition survives exec: the target would
    # never see a SIGPIPE. Popen's restore_signals undid that for this process only as far as its exec of this
    # interpreter.
    for name in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, signal.SIG_DFL)

    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    os.tcsetpgrp(0, os.getpgrp())

    os.execvpe(argv[0], argv, os.environ)
"""  # noqa


def _remote_process_returncode(si_code: int, si_status: int) -> int:
    if si_code == _REMOTE_CLD_EXITED:
        return si_status
    if si_code in (_REMOTE_CLD_KILLED, _REMOTE_CLD_DUMPED):
        return -si_status
    raise RuntimeError(f'Unexpected waitid result: si_code={si_code!r}, si_status={si_status!r}')


class _RemoteDarwinProcessWaiter(ta.Protocol):
    def __call__(self, pid: int, *, nohang: bool = False) -> ta.Optional[int]: ...


@cached_nullary
def _remote_darwin_process_waiter() -> _RemoteDarwinProcessWaiter:
    # CPython did not expose os.waitid on macOS until 3.13, although libc and the kernel have long provided it. Keep the
    # child waitable so its pid/pgid remain ours until close deliberately reaps it. The first six siginfo_t fields are
    # fixed-width scalars on Darwin; the tail only reserves enough space for libc to fill the complete structure.

    import ctypes as ct

    class Siginfo(ct.Structure):
        _fields_ = [
            ('si_signo', ct.c_int),
            ('si_errno', ct.c_int),
            ('si_code', ct.c_int),
            ('si_pid', ct.c_int),
            ('si_uid', ct.c_uint),
            ('si_status', ct.c_int),
            ('_tail', ct.c_ubyte * 104),
        ]

    _waitid = ct.CDLL(None, use_errno=True).waitid
    _waitid.argtypes = (ct.c_int, ct.c_uint, ct.c_void_p, ct.c_int)
    _waitid.restype = ct.c_int

    def waitpid(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
        info = Siginfo()
        options = _REMOTE_DARWIN_WEXITED | _REMOTE_DARWIN_WNOWAIT
        if nohang:
            options |= os.WNOHANG
        ct.set_errno(0)
        if _waitid(_REMOTE_DARWIN_P_PID, pid, ct.byref(info), options):
            errno = ct.get_errno()
            raise OSError(errno, os.strerror(errno))
        if nohang and not info.si_pid:
            return None
        return _remote_process_returncode(info.si_code, info.si_status)

    return waitpid


def _remote_darwin_process_wait(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
    return _remote_darwin_process_waiter()(pid, nohang=nohang)


def _remote_process_wait(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
    waitid: ta.Any = getattr(os, 'waitid', None)
    if waitid is None:
        platform: ta.Any = sys.platform
        if platform != 'darwin':
            raise RuntimeError('waitid is unavailable')
        return _remote_darwin_process_wait(pid, nohang=nohang)

    options = os.WEXITED | os.WNOWAIT
    if nohang:
        options |= os.WNOHANG
    info = waitid(os.P_PID, pid, options)
    if info is None:
        return None
    return _remote_process_returncode(info.si_code, info.si_status)


##


def _remote_waitstatus_to_exitcode(status: int) -> int:
    # os.waitstatus_to_exitcode is 3.9+.
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    raise ValueError(f'Unexpected wait status: {status!r}')


def _remote_log(msg: str, *, exc: ta.Optional[BaseException] = None) -> None:
    """Writes a line of agent diagnostics - with a traceback, given `exc` - to stderr, which the host captures."""

    try:
        parts = [f'omllm remote agent: {msg}\n']
        if exc is not None:
            parts.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
        sys.stderr.write(''.join(parts))
        sys.stderr.flush()
    except Exception:  # noqa
        pass


class _RemoteServerProcess:
    def __init__(
            self,
            service: 'RemoteProcessService',  # noqa: UP037
            process_id: str,
            popen: subprocess.Popen,
            *,
            created_at: float,
            pty_master_fd: ta.Optional[int],
            pty_slave_fd: ta.Optional[int],
            pty_winsize: ta.Optional[ta.Tuple[int, int]],
    ) -> None:
        super().__init__()

        self._service = service
        self.id = process_id
        self.popen = popen
        self.created_at = created_at

        self._pty_master_fd = pty_master_fd
        self._pty_slave_fd = pty_slave_fd
        self._pty_read_fd: ta.Optional[int] = None
        self._pty_reader_task: ta.Optional[asyncio.Task] = None
        self._pty_readable: ta.Optional[asyncio.Future] = None
        self._pty_winsize = pty_winsize

        self._stdin: ta.Optional[asyncio.StreamWriter] = None
        self._read_transports: ta.List[asyncio.BaseTransport] = []
        self._reader_tasks: ta.List[asyncio.Task] = []
        self._open_readers = 0
        self._close_task: ta.Optional[asyncio.Task] = None

        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._returncode: ta.Optional[int] = None
        self._reaped = False

    @property
    def returncode(self) -> ta.Optional[int]:
        return self._returncode

    @property
    def exited(self) -> bool:
        return self._exited.is_set()

    #

    def _add_reader(self, read: ta.Callable[[], ta.Coroutine[ta.Any, ta.Any, None]]) -> asyncio.Task:
        self._open_readers += 1
        task = asyncio.create_task(
            self._run_reader(read),
            name=f'remote-read-{self.id}',
        )
        self._reader_tasks.append(task)
        return task

    async def _run_reader(self, read: ta.Callable[[], ta.Coroutine[ta.Any, ta.Any, None]]) -> None:
        try:
            await read()
        finally:
            # The last reader to finish - at EOF, or torn down - is what ends the output. Announcing that from here,
            # before the task completes, is what lets `_run_close` order its reply after every last byte.
            self._open_readers -= 1
            if self._open_readers == 0 and not self._output_ended.is_set():
                self._output_ended.set()
                await self._service.notify(
                    REMOTE_PROCESS_OUTPUT_END_METHOD,
                    marshal_obj(RemoteProcessOutputEndEvent(
                        id=self.id,
                    )),
                )

    async def _connect_reader(self, file: ta.IO, fd: int) -> None:
        reader = await asyncio_open_stream_reader(file)
        transport = reader._transport  # type: ignore[attr-defined]  # noqa
        if transport is not None:
            self._read_transports.append(transport)
        self._add_reader(lambda: self._read_output(reader, fd))

    async def start(self) -> None:
        if self._pty_master_fd is not None:
            read_fd = os.dup(self._pty_master_fd)
            os.set_blocking(read_fd, False)
            self._pty_read_fd = read_fd
            self._pty_reader_task = self._add_reader(lambda: self._read_pty_output(read_fd, 1))

            write_file = os.fdopen(os.dup(self._pty_master_fd), 'wb', 0)
            self._stdin = await asyncio_open_stream_writer(write_file)
        else:
            if self.popen.stdout is not None:
                await self._connect_reader(self.popen.stdout, 1)
            if self.popen.stderr is not None:
                await self._connect_reader(self.popen.stderr, 2)
            if self.popen.stdin is not None:
                self._stdin = await asyncio_open_stream_writer(self.popen.stdin)

        if not self._reader_tasks:
            # Nothing to read: the output is over before it began.
            self._output_ended.set()
            self._service.queue_event(
                REMOTE_PROCESS_OUTPUT_END_METHOD,
                marshal_obj(RemoteProcessOutputEndEvent(
                    id=self.id,
                )),
            )

    #

    async def _drain_pty_output(self, fd: int, output_fd: int) -> bool:
        """Forwards whatever is queued on the master; False once the pty is finished (its last slave closed)."""

        while True:
            try:
                data = os.read(fd, _REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except (BlockingIOError, InterruptedError):
                return True
            except OSError:
                # Linux pty masters report EIO when the last slave closes; BSDs return EOF.
                return False
            if not data:
                return False
            await self._service.notify(
                REMOTE_PROCESS_OUTPUT_METHOD,
                marshal_obj(RemoteProcessOutputEvent(
                    id=self.id,
                    fd=output_fd,
                    data=data,
                )),
            )

    def _close_pty_slave(self) -> None:
        if self._pty_slave_fd is not None:
            os.close(self._pty_slave_fd)
            self._pty_slave_fd = None

    async def _read_pty_output(self, fd: int, output_fd: int) -> None:
        loop = asyncio.get_running_loop()
        try:
            while True:
                if not await self._drain_pty_output(fd, output_fd):
                    return

                if self.exited and self._pty_slave_fd is not None:
                    # Keep one slave descriptor open until the leader has exited and every byte already queued on the
                    # master has been consumed. Closing the final slave first can discard trailing pty output.
                    self._close_pty_slave()
                    continue

                # Wait for output - or for the exit, which `_poll_exit` announces by resolving this same future.
                readable = self._pty_readable = loop.create_future()

                def on_readable() -> None:
                    if not readable.done():
                        readable.set_result(None)

                loop.add_reader(fd, on_readable)
                try:
                    await readable
                finally:
                    self._pty_readable = None
                    if self._pty_read_fd == fd:
                        loop.remove_reader(fd)

        finally:
            if self._pty_read_fd == fd:
                self._pty_read_fd = None
                os.close(fd)

    async def _read_output(self, reader: asyncio.StreamReader, fd: int) -> None:
        while True:
            try:
                data = await reader.read(_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except OSError:
                return
            if not data:
                return
            await self._service.notify(
                REMOTE_PROCESS_OUTPUT_METHOD,
                marshal_obj(RemoteProcessOutputEvent(
                    id=self.id,
                    fd=fd,
                    data=data,
                )),
            )

    #

    def _poll_exit(self) -> None:
        """
        A non-blocking, non-reaping probe of the child, run from the service's SIGCHLD handler: the first to see the
        exit records and announces it. The leader stays a zombie - its pid and pgid ours to signal - until `close` reaps
        it.
        """

        if self._exited.is_set() or self._reaped:
            return
        try:
            returncode = _remote_process_wait(self.popen.pid, nohang=True)
        except ChildProcessError:
            # Reaped behind our back: there is no exit status to be had, and nothing more to observe.
            return
        if returncode is None:
            return
        self._returncode = returncode
        self._exited.set()
        if (readable := self._pty_readable) is not None and not readable.done():
            readable.set_result(None)
        self._service.queue_event(
            REMOTE_PROCESS_EXITED_METHOD,
            marshal_obj(RemoteProcessExitedEvent(
                id=self.id,
                returncode=returncode,
            )),
        )

    def _signal(self, sig: int, process_group: bool) -> None:
        if self._reaped:
            raise ProcessLookupError(self.popen.pid)
        if self.exited:
            # The unreaped leader keeps its pid, and therefore its process-group id, from being reused.
            if process_group:
                try:
                    os.killpg(self.popen.pid, sig)
                except (PermissionError, ProcessLookupError):
                    pass
            return

        if not process_group:
            self._kill_leader(sig)
        elif not self._kill_group(sig):
            # No such group yet: the pty bootstrap creates its session right after exec, and a signal can race that
            # setup. Hit the owned pid so it cannot escape, then sweep the group once more in case it came to exist in
            # between - and already has members. The leader may by then be dead of the first signal, leaving the group
            # nothing but its zombie, which that sweep tolerates like any other.
            self._kill_leader(sig)
            self._kill_group(sig)

    def _kill_leader(self, sig: int) -> None:
        """
        Delivers `sig` to the owned leader pid directly: for a signal to the leader alone, or when its group does not
        exist yet. ESRCH is benign (already gone). EPERM means a leader we may not signal, a genuine error - unless a
        probe finds it has in fact exited.
        """

        try:
            os.kill(self.popen.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            if not self._is_exited_nowait():
                raise

    def _kill_group(self, sig: int) -> bool:
        """
        Delivers `sig` to the owned leader's process group, or returns False if no such group exists. EPERM means a
        group we may not signal, a genuine error - unless a probe finds the leader has exited: Darwin fails a group
        signal with EPERM rather than ESRCH when every member of the group is a zombie, as it is once the unreaped
        leader has exited and nothing else in it lives.
        """

        try:
            os.killpg(self.popen.pid, sig)
        except ProcessLookupError:
            return False
        except PermissionError:
            if not self._is_exited_nowait():
                raise
        return True

    def _is_exited_nowait(self) -> bool:
        try:
            return _remote_process_wait(self.popen.pid, nohang=True) is not None
        except ChildProcessError:
            return True
        except OSError:
            return False

    async def signal(self, sig: int, process_group: bool) -> None:
        self._signal(sig, process_group)

    async def write(self, data: bytes) -> None:
        if self._stdin is None or self._stdin.is_closing():
            raise BrokenPipeError('process has no open stdin')
        self._stdin.write(data)
        await self._stdin.drain()

    async def write_eof(self) -> None:
        if self._stdin is None or self._stdin.is_closing():
            return
        try:
            self._stdin.write_eof()
        except (AttributeError, NotImplementedError):
            self._stdin.close()

    async def resize(self, rows: int, cols: int) -> None:
        if self._pty_master_fd is None:
            raise RuntimeError('process does not have a pty')

        import fcntl
        import struct
        import termios

        fcntl.ioctl(self._pty_master_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        self._pty_winsize = (rows, cols)
        if not self.exited:
            self._kill_group(signal.SIGWINCH)

    #

    async def _wait_exited(self, timeout: ta.Optional[float]) -> bool:
        if self.exited:
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._exited.wait(), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self.exited
        return True

    async def _wait_output_ended(self, timeout: ta.Optional[float]) -> bool:
        if self._output_ended.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._output_ended.wait(), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self._output_ended.is_set()
        return True

    def _close_streams(self) -> None:
        if self._stdin is not None:
            self._stdin.close()
        for transport in self._read_transports:
            transport.close()
        self._read_transports.clear()
        self._close_pty_slave()
        if (task := self._pty_reader_task) is not None and not task.done():
            task.cancel()
        if (fd := self._pty_read_fd) is not None:
            # Taken out from under the reader: unregister it here too, before the fd number can be reused.
            self._pty_read_fd = None
            asyncio.get_running_loop().remove_reader(fd)
            try:
                os.close(fd)
            except OSError:
                pass
        if self._pty_master_fd is not None:
            try:
                os.close(self._pty_master_fd)
            except OSError:
                pass
            self._pty_master_fd = None

    def _reap(self) -> None:
        if self._reaped:
            return
        _, status = os.waitpid(self.popen.pid, 0)
        self._reaped = True
        if self._returncode is None:
            self._returncode = _remote_waitstatus_to_exitcode(status)
            self._exited.set()
        self.popen.returncode = self._returncode

    async def _run_close(self, policy: RemoteProcessClosePolicySpec) -> RemoteProcessCloseResult:
        close_stdin = policy.close_stdin
        first_signal = policy.signal
        grace_s = policy.grace_s
        kill_s = policy.kill_s
        process_group = policy.process_group
        drain_s = policy.drain_s

        if not self.exited:
            if close_stdin:
                try:
                    await self.write_eof()
                except Exception:  # noqa
                    pass
            self._signal(first_signal, process_group)
            if not await self._wait_exited(grace_s):
                self._signal(signal.SIGKILL, process_group)
                if not await self._wait_exited(kill_s):
                    self._close_streams()
                    raise RuntimeError(f'process {self.id!r} survived SIGKILL for {kill_s}s')

        # Sweep descendants while the unreaped leader still makes its process-group id safe to address.
        if process_group:
            self._signal(first_signal, True)
        if not self._output_ended.is_set():
            await self._wait_output_ended(drain_s)
        if process_group:
            self._signal(signal.SIGKILL, True)

        self._close_streams()
        if self._reader_tasks:
            # Every byte, and the end of output, has been sent once these are done - so the reply below comes after.
            await asyncio.gather(*self._reader_tasks, return_exceptions=True)
        self._reap()
        self._service.finished(self)
        return RemoteProcessCloseResult(returncode=check.not_none(self._returncode), state='reaped')

    async def close(self, policy: RemoteProcessClosePolicySpec) -> RemoteProcessCloseResult:
        if self._reaped:
            return RemoteProcessCloseResult(returncode=check.not_none(self._returncode), state='reaped')
        if self._close_task is None:
            self._close_task = asyncio.create_task(
                self._run_close(policy),
                name=f'remote-close-{self.id}',
            )
        return await asyncio.shield(self._close_task)

    async def _hard_kill(self, timeout: float) -> ta.Optional[int]:
        """
        Last resort once a graceful close has failed: SIGKILLs the group and the leader, closes our ends of its streams,
        and reaps it within `timeout`, so nothing it started outlives the agent. Returns the reaped returncode, or None
        if it could not be reaped in time.
        """

        pid = self.popen.pid
        if not self._reaped:
            # Only while unreaped: the pid, and so its process-group id, is still ours to signal.
            for kill in (os.killpg, os.kill):
                try:
                    kill(pid, signal.SIGKILL)
                except (PermissionError, ProcessLookupError):
                    pass
        self._close_streams()

        deadline = time.monotonic() + timeout
        while not self._reaped:
            try:
                reaped_pid, status = os.waitpid(pid, os.WNOHANG)  # noqa: ASYNC222  # WNOHANG: never blocks
            except ChildProcessError:
                # Reaped behind our back: there is no status left to collect.
                self._reaped = True
                break
            if reaped_pid:
                self._reaped = True
                self._returncode = _remote_waitstatus_to_exitcode(status)
                self._exited.set()
                self.popen.returncode = self._returncode
                break
            if time.monotonic() >= deadline:
                return None
            await asyncio.sleep(.01)

        self._service.finished(self)
        return self._returncode


class RemoteProcessService:
    _DEFAULT_CLOSE_POLICY: ta.ClassVar[RemoteProcessClosePolicySpec] = RemoteProcessClosePolicySpec(
        signal=int(signal.SIGTERM),
        grace_s=5.,
        kill_s=5.,
        close_stdin=True,
        process_group=True,
        drain_s=1.,
    )

    def __init__(self) -> None:
        super().__init__()

        self._connection: ta.Optional[RpcConnection] = None
        self._processes: ta.Dict[str, _RemoteServerProcess] = {}
        self._next_id = 1
        self._closed = False

        self._sigchld_loop: ta.Optional[asyncio.AbstractEventLoop] = None

        # Exit and end-of-output announcements. They originate in sync code that cannot await a send, so they are queued
        # and sent, in order, by at most one short-lived task.
        self._events: ta.Deque[ta.Tuple[str, ta.Any]] = collections.deque()
        self._event_task: ta.Optional[asyncio.Task] = None

    def set_connection(self, connection: RpcConnection) -> None:
        if self._connection is not None:
            raise RuntimeError('connection already set')
        self._connection = connection

    async def notify(self, method: str, params: ta.Any) -> None:
        if (connection := self._connection) is None or connection.is_closed:
            return
        try:
            # Fire-and-forget on an ordered stream that the host applies inline, in its receive loop: wire order is
            # delivery order. Awaiting the write is what makes process.close's reply - sent after it - an ordering
            # barrier: by the time the host sees that reply, every preceding output chunk is in its spool.
            await connection.notify(method, params)
        except Exception:  # noqa
            # The connection owns its failure. Keep draining child pipes until server teardown reaches us.
            pass

    def queue_event(self, method: str, params: ta.Any) -> None:
        self._events.append((method, params))
        if self._event_task is None or self._event_task.done():
            self._event_task = asyncio.create_task(
                self._send_events(),
                name='remote-events',
            )

    async def _send_events(self) -> None:
        while self._events:
            method, params = self._events.popleft()
            await self.notify(method, params)

    #

    def _ensure_sigchld(self) -> None:
        """
        Exits are observed by one SIGCHLD handler probing every unexited child with a non-blocking, non-reaping waitid:
        no thread and no task per child, so nothing to saturate. It is installed before the first child exists, so no
        exit can slip by unnoticed.
        """

        if self._sigchld_loop is not None:
            return
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGCHLD, self._on_sigchld)
        self._sigchld_loop = loop

    def _remove_sigchld(self) -> None:
        if (loop := self._sigchld_loop) is None:
            return
        self._sigchld_loop = None
        try:
            loop.remove_signal_handler(signal.SIGCHLD)
        except (RuntimeError, ValueError):
            pass

    def _on_sigchld(self) -> None:
        # One signal may stand for any number of exits.
        for process in list(self._processes.values()):
            process._poll_exit()  # noqa: SLF001

    #

    def _lookup(self, process_id: str) -> _RemoteServerProcess:
        try:
            return self._processes[process_id]
        except KeyError:
            raise ValueError(f'No such remote process: {process_id!r}') from None

    def finished(self, process: _RemoteServerProcess) -> None:
        if self._processes.get(process.id) is process:
            self._processes.pop(process.id, None)

    @staticmethod
    def _stdio_value(value: str, *, stderr: bool = False) -> ta.Any:
        if value == 'pipe':
            return subprocess.PIPE
        if value == 'devnull':
            return subprocess.DEVNULL
        if stderr and value == 'stdout':
            return subprocess.STDOUT
        raise ValueError(f'Unsupported remote stdio channel: {value!r}')

    @staticmethod
    def _set_pty_winsize(fd: int, rows: int, cols: int) -> None:
        import fcntl
        import struct
        import termios

        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))

    async def spawn(self, params: ta.Any) -> ta.Any:
        if self._closed:
            raise RuntimeError('remote process service is closed')
        p: RemoteProcessSpawnParams = unmarshal_obj(params, RemoteProcessSpawnParams)
        argv = list(p.argv)
        cwd = p.cwd
        env = dict(p.env) if p.env is not None else None
        name = p.name
        stdio = p.stdio
        kind = stdio.kind

        process_id = f'p{self._next_id}'
        self._next_id += 1

        self._ensure_sigchld()

        master: ta.Optional[int] = None
        slave: ta.Optional[int] = None
        pty_slave_fd: ta.Optional[int] = None
        pty_winsize: ta.Optional[ta.Tuple[int, int]] = None
        try:
            try:
                if kind == 'pipes':
                    stdin = self._stdio_value(check.not_none(stdio.stdin))
                    stdout = self._stdio_value(check.not_none(stdio.stdout))
                    stderr = self._stdio_value(check.not_none(stdio.stderr), stderr=True)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        argv,
                        cwd=cwd,
                        env=env,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                        bufsize=0,
                        start_new_session=True,
                    )

                elif kind == 'pty':
                    rows = check.not_none(stdio.rows)
                    cols = check.not_none(stdio.cols)
                    term = stdio.term
                    if term is not None and (env is None or 'TERM' not in env):
                        env = dict(os.environ if env is None else env)
                        env['TERM'] = term

                    master, slave = os.openpty()
                    self._set_pty_winsize(slave, rows, cols)
                    pty_winsize = (rows, cols)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        [sys.executable, '-c', _REMOTE_PTY_CHILD_CODE, json.dumps(argv)],
                        cwd=cwd,
                        env=env,
                        stdin=slave,
                        stdout=slave,
                        stderr=slave,
                        close_fds=True,
                    )
                    pty_slave_fd = slave
                    slave = None

                else:
                    raise ValueError(f'Invalid remote stdio kind: {kind!r}')

            except BaseException:
                if master is not None:
                    os.close(master)
                raise

        finally:
            if slave is not None:
                os.close(slave)

        process = _RemoteServerProcess(
            self,
            process_id,
            popen,
            created_at=time.time(),
            pty_master_fd=master,
            pty_slave_fd=pty_slave_fd,
            pty_winsize=pty_winsize,
        )
        # Registered before start()'s first suspension point. The SIGCHLD handler is already installed and there is no
        # await between the fork above and here, so a fast exit's signal cannot arrive before the process is findable -
        # no speculative waitid probe is needed to catch it.
        self._processes[process_id] = process
        try:
            await process.start()
        except BaseException:
            self._processes.pop(process_id, None)
            try:
                os.kill(popen.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(popen.pid, 0)  # noqa: ASYNC222
            popen.returncode = -signal.SIGKILL
            process._close_streams()  # noqa: SLF001
            raise

        return marshal_obj(RemoteProcessSpawnResult(
            id=process.id,
            pid=process.popen.pid,
            created_at=process.created_at,
            name=name,
        ))

    async def signal(self, params: ta.Any) -> None:
        p: RemoteProcessSignalParams = unmarshal_obj(params, RemoteProcessSignalParams)
        await self._lookup(p.id).signal(p.signal, p.process_group)

    async def close(self, params: ta.Any) -> ta.Any:
        p: RemoteProcessCloseParams = unmarshal_obj(params, RemoteProcessCloseParams)
        return marshal_obj(await self._lookup(p.id).close(p.policy))

    async def write(self, params: ta.Any) -> None:
        p: RemoteProcessWriteParams = unmarshal_obj(params, RemoteProcessWriteParams)
        await self._lookup(p.id).write(p.data)

    async def write_eof(self, params: ta.Any) -> None:
        p: RemoteProcessRefParams = unmarshal_obj(params, RemoteProcessRefParams)
        await self._lookup(p.id).write_eof()

    async def resize(self, params: ta.Any) -> None:
        p: RemoteProcessResizeParams = unmarshal_obj(params, RemoteProcessResizeParams)
        await self._lookup(p.id).resize(p.rows, p.cols)

    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return {
            REMOTE_PROCESS_SPAWN_METHOD: self.spawn,
            REMOTE_PROCESS_SIGNAL_METHOD: self.signal,
            REMOTE_PROCESS_CLOSE_METHOD: self.close,
            REMOTE_PROCESS_WRITE_METHOD: self.write,
            REMOTE_PROCESS_WRITE_EOF_METHOD: self.write_eof,
            REMOTE_PROCESS_RESIZE_METHOD: self.resize,
        }

    async def _close_at_shutdown(self, process: _RemoteServerProcess) -> None:
        """
        Closes one process as part of agent shutdown, reporting how it went on stderr - nothing else will ever observe
        it. A process whose graceful close fails is not left running past the agent: it is killed outright.
        """

        pid = process.popen.pid
        exited_before = process.exited
        start = time.monotonic()
        try:
            result = await process.close(self._DEFAULT_CLOSE_POLICY)

        except BaseException as e:  # noqa
            _remote_log(
                f'process {process.id} (pid {pid}): close failed after {time.monotonic() - start:.3f}s '
                f'(exited before close: {exited_before}), killing it: {e!r}',
                exc=e,
            )
            returncode = await process._hard_kill(self._DEFAULT_CLOSE_POLICY.kill_s)  # noqa: SLF001
            outcome = f'returncode={returncode}' if returncode is not None else 'NOT reaped'
            _remote_log(f'process {process.id} (pid {pid}): killed, {outcome}')
            if not isinstance(e, Exception):
                raise

        else:
            _remote_log(
                f'process {process.id} (pid {pid}): closed in {time.monotonic() - start:.3f}s '
                f'(exited before close: {exited_before}), returncode={result.returncode}',
            )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._processes:
                await asyncio.gather(*[
                    self._close_at_shutdown(process)
                    for process in list(self._processes.values())
                ], return_exceptions=True)
        finally:
            self._remove_sigchld()
            if (task := self._event_task) is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)


########################################
# ../../../../omcore/rpc/asyncio.py
"""
The asyncio runtime: one pump task steps the driver and delivers events; every handler runs as a tracked task.

Promises are asynclite event promises over asyncio events, so waiting suspends the waiting task. Request handlers are
keyed by request id, so a peer's cancel, a handling timeout, or the connection closing cancels exactly the right task.
Every task the runtime creates is tracked from creation to completion: `close` cancels them, `wait_closed` waits for
them (save the task calling it), and their exceptions are observed.

Cancellation, the asyncio reality:
 - A caller cancelled while awaiting a response abandons the request: its waiter is dropped and, if so configured, the
   peer is sent a cancel.
 - A peer's cancel, or the session giving up on an inbound request, cancels that request's handler task.
 - A handler task cancelled from anywhere else answers the peer with a `cancelled` error, if the request is still in
   flight, and then lets the cancellation propagate.
 - The pump task being cancelled fails the connection: every waiter fails, every handler is cancelled, the driver is
   aborted.
Handlers should let CancelledError propagate. One which swallows it delays `wait_closed` for as long as it keeps
running.
"""


log = get_module_logger(globals())  # noqa


##


class AsyncioRpcRuntime(RpcRuntime):
    """Must be started on the loop which will run it; the driver's streams must belong to that loop too."""

    def __init__(
            self,
            driver: PollAsyncioStreamIoPipelineDriver,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        super().__init__()

        self._driver = driver
        self._closers = list(closers)

        self._sink: ta.Optional[RpcRuntimeSink] = None
        self._pump_task: ta.Optional[asyncio.Task] = None
        self._closed_event: ta.Optional[asyncio.Event] = None
        self._driver_done = False
        self._closed = False

        self._keyed_tasks: ta.Dict[ta.Any, asyncio.Task] = {}
        self._unkeyed_tasks: ta.Set[asyncio.Task] = set()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> PollAsyncioStreamIoPipelineDriver:
        return self._driver

    @property
    def is_started(self) -> bool:
        return self._sink is not None

    @property
    def is_driver_done(self) -> bool:
        return self._driver_done

    @property
    def num_tasks(self) -> int:
        """Handler tasks currently tracked, excluding the pump."""

        return len(self._keyed_tasks) + len(self._unkeyed_tasks)

    #

    def make_promise(self) -> AsynclitePromise:
        return EventAsynclitePromise(AsyncioAsyncliteEvent(asyncio.Event()))

    def is_cancelled_exception(self, exc: BaseException) -> bool:
        return isinstance(exc, asyncio.CancelledError)

    def enqueue(self, *commands: ta.Any) -> bool:
        if self._driver_done or self._closed:
            return False
        try:
            self._driver.enqueue(*commands)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    #

    async def start(self, sink: RpcRuntimeSink) -> None:
        check.none(self._sink, 'already started')
        check.state(not self._closed, 'already closed')

        self._sink = sink
        self._closed_event = asyncio.Event()
        self._pump_task = asyncio.create_task(self._pump(sink), name=f'{type(self).__name__}._pump')

    async def _pump(self, sink: RpcRuntimeSink) -> None:
        exc: ta.Optional[BaseException] = None
        try:
            while True:
                try:
                    out = await self._driver.next()
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa
                    exc = e
                    break

                if out is None:
                    if not self._driver.is_running:
                        break
                    continue

                if isinstance(out, BaseException):
                    # A failing close the session surfaced: the driver may be stuck flushing to a stalled peer, so do
                    # not wait for its orderly shutdown.
                    exc = out
                    break

                await sink.on_event(out)

        except asyncio.CancelledError:
            if exc is None:
                exc = RpcConnectionClosedError('rpc pump cancelled')
            raise

        except Exception as e:  # noqa
            log.exception('Rpc pump failed delivering an event')
            exc = e

        finally:
            self._driver_done = True
            try:
                sink.on_driver_done(exc)
            except Exception:  # noqa
                log.exception('Error reporting rpc driver done')

            try:
                await self._driver.close()
            except Exception:  # noqa
                log.debug('Error closing rpc driver', exc_info=True)

            self._run_closers()

            check.not_none(self._closed_event).set()

    #

    @staticmethod
    def _observe(task: asyncio.Task) -> None:
        if not task.cancelled() and (e := task.exception()) is not None:
            log.error('Rpc handler task failed', exc_info=e)

    def _on_keyed_done(self, key: ta.Any, task: asyncio.Task) -> None:
        if self._keyed_tasks.get(key) is task:
            del self._keyed_tasks[key]
        self._observe(task)

    def _on_unkeyed_done(self, task: asyncio.Task) -> None:
        self._unkeyed_tasks.discard(task)
        self._observe(task)

    @staticmethod
    async def _run_spawned(fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        try:
            await fn()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa
            log.exception('Unhandled error in rpc handler')

    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        if self._closed or self._driver_done:
            return

        task = asyncio.create_task(self._run_spawned(fn))

        if key is not None:
            if (prev := self._keyed_tasks.get(key)) is not None and not prev.done():
                # The session never lets an id be in flight twice, so this is a bug; keep tracking the old task anyway.
                log.warning('Rpc handler key %r spawned while still running', key)
                self._unkeyed_tasks.add(prev)
                prev.add_done_callback(self._unkeyed_tasks.discard)
            self._keyed_tasks[key] = task
            task.add_done_callback(functools.partial(self._on_keyed_done, key))

        else:
            self._unkeyed_tasks.add(task)
            task.add_done_callback(self._on_unkeyed_done)

    def cancel(self, key: ta.Any) -> None:
        if (task := self._keyed_tasks.get(key)) is not None and not task.done():
            task.cancel()

    def _all_tasks_but_current(self) -> ta.List[asyncio.Task]:
        try:
            cur = asyncio.current_task()
        except RuntimeError:
            cur = None
        return [t for t in (*self._keyed_tasks.values(), *self._unkeyed_tasks) if t is not cur]

    def cancel_all(self) -> None:
        for task in self._all_tasks_but_current():
            if not task.done():
                task.cancel()

    #

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        self.cancel_all()

        try:
            await self._driver.close()

        except Exception:  # noqa
            log.debug('Error closing rpc driver', exc_info=True)

        finally:
            if self._pump_task is None:
                # Never started: no pump will run them.
                self._run_closers()

    def _run_closers(self) -> None:
        """Run once the driver is done, however that came about. Idempotent: the closers run once."""

        closers, self._closers = self._closers, []
        for c in closers:
            try:
                c()
            except Exception:  # noqa
                log.exception('Error in rpc runtime closer %r', c)

    async def wait_closed(self) -> None:
        if (ev := self._closed_event) is not None:
            await ev.wait()

        try:
            cur = asyncio.current_task()
        except RuntimeError:
            cur = None

        while True:
            tasks = [
                t
                for t in (self._pump_task, *self._keyed_tasks.values(), *self._unkeyed_tasks)
                if t is not None and t is not cur and not t.done()
            ]
            if tasks:
                # asyncio.wait, unlike gather, does not cancel what it waits for when the waiter itself is cancelled.
                await asyncio.wait(tasks)
                continue

            if any(t is not cur for t in (*self._keyed_tasks.values(), *self._unkeyed_tasks)):
                # Finished, but with their done callbacks - which observe and untrack them - not yet run: they run on
                # the next loop iteration, so yield one.
                await asyncio.sleep(0)
                continue

            return


##


class AsyncioSerializingRpcHandler(RpcHandler):
    """
    Runs the wrapped handler's requests and spawned notifications one at a time, in arrival order, for a backend which
    is not safe to call concurrently. Inline notifications are untouched: they already run one at a time on the pump.
    """

    def __init__(self, handler: RpcHandler) -> None:
        super().__init__()

        self._handler = handler
        self._lock: ta.Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if (lock := self._lock) is None:
            lock = self._lock = asyncio.Lock()
        return lock

    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        async with self._get_lock():
            return await self._handler.handle_request(method, params)

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        return self._handler.handle_notification_inline(method, params)

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        async with self._get_lock():
            await self._handler.handle_notification(method, params)


##


def _rpc_asyncio_try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class AsyncioRpcConnections:
    """
    Factories taping an asyncio connection onto the transports in use: sockets, a subprocess's stdio, or our own.
    Connection keyword arguments (`handler`, `id_creator`, ...) pass through. The connections are not started.
    """

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    @staticmethod
    def of_streams(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            driver_config: ta.Optional[PollAsyncioStreamIoPipelineDriver.Config] = None,
            spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """TLS is a transport handler: `spec_kwargs=dict(transport_handlers=[SslIoPipelineHandler(...)])`."""

        spec = rpc_build_pipeline_spec(
            config,
            **(spec_kwargs or {}),
        )
        driver = PollAsyncioStreamIoPipelineDriver(spec, reader, writer, driver_config)
        return RpcConnection(AsyncioRpcRuntime(driver, closers=closers), config, **kwargs)

    @classmethod
    async def connect_tcp(
            cls,
            host: str,
            port: int,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_connection(host, port),
            connect_timeout_s,
        )

        try:
            if (sock := writer.get_extra_info('socket')) is not None:
                _rpc_asyncio_try_set_nodelay(sock)

            return cls.of_streams(reader, writer, config, **kwargs)

        except BaseException:
            writer.close()
            raise

    @classmethod
    async def connect_unix(
            cls,
            path: str,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_unix_connection(path),
            connect_timeout_s,
        )

        try:
            return cls.of_streams(reader, writer, config, **kwargs)
        except BaseException:
            writer.close()
            raise

    @classmethod
    def of_subprocess(
            cls,
            proc: asyncio.subprocess.Process,
            config: RpcConfig = RpcConfig.DEFAULT,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """Talks to a child process over its stdio. The process must have been created with piped stdin and stdout."""

        return cls.of_streams(
            check.not_none(proc.stdout),
            check.not_none(proc.stdin),
            config,
            **kwargs,
        )

    @classmethod
    async def of_stdio(
            cls,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            stdin: ta.Optional[ta.IO] = None,
            stdout: ta.Optional[ta.IO] = None,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """Serves or talks over this process's own stdio, as a remotely bootstrapped process does."""

        reader = await asyncio_open_stream_reader(stdin if stdin is not None else sys.stdin.buffer)
        writer = await asyncio_open_stream_writer(stdout if stdout is not None else sys.stdout.buffer)

        return cls.of_streams(reader, writer, config, **kwargs)


########################################
# ../server.py
"""
The remote agent payload's request handler: the method tables of each remotable concern's target-side service, merged
into one table over the one rpc connection. Lite: this is the amalgam's composition root beneath `_main.py`. A new
remotable concern plugs in here, and its host-side client into `client.py`; nothing below either knows the others exist.
"""


##


class RemoteAgentRpcHandler(RpcMethodTableHandler):
    def __init__(self) -> None:
        super().__init__()

        self._environment = RemoteEnvironmentService()
        self._fs = RemoteFsService()
        self._processes = RemoteProcessService()

        self.add_methods(rpc_merge_method_tables(
            self._environment.methods(),
            self._fs.methods(),
            self._processes.methods(),
        ))

    def set_connection(self, connection: RpcConnection) -> None:
        # Only the process service speaks unprompted - its output and exit notifications - so only it needs the
        # connection.
        self._processes.set_connection(connection)

    async def aclose(self) -> None:
        try:
            await self._fs.aclose()
        finally:
            await self._processes.aclose()


########################################
# _main.py


##


async def serve_remote_agent(input: ta.BinaryIO, output: ta.BinaryIO) -> None:  # noqa
    reader = await asyncio_open_stream_reader(input)
    writer = await asyncio_open_stream_writer(output)

    handler = RemoteAgentRpcHandler()
    connection = AsyncioRpcConnections.of_streams(reader, writer, handler=handler)
    handler.set_connection(connection)
    try:
        await connection.start()
        try:
            await connection.serve()
        finally:
            await connection.close()
    finally:
        await handler.aclose()


def remote_agent_main() -> None:
    runtime = pyremote_bootstrap_finalize()
    asyncio.run(serve_remote_agent(runtime.input, runtime.output))
