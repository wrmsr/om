"""
Entry point for the web frontend: `python -m omllm.ui.web`, or `om llm --web`.

Serves the one session this process runs to whoever opens its page - one browser tab or several, all seeing the same
feed. Logs go to stderr: the terminal is free, the page being the ui. Quitting (`/quit`, or ctrl+c in the terminal)
cancels whatever is running, tells the pages, and stops serving.
"""
import asyncio
import contextlib
import logging
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang
from omcore.io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from omcore.logs import all as logs

from ... import agent as agn
from ..agent.inject.events import AgentEventSubscribers
from ..agent.setup import AgentSetup
from ..paths import get_agent_cwd
from ..yolo import yolo_autoexec
from ..yolo import yolo_process_config
from .config import WebConfig
from .feed.feed import Feed
from .inject import bind_web
from .output.transcripts import feed_transcript
from .quit import WebQuitSignal
from .server.security import WebToken
from .server.serving import AsgiPipelineServer
from .server.serving import WebServerAddress
from .submissions import Submitter


log = logs.get_module_logger(globals())


##


@dc.dataclass(frozen=True, kw_only=True)
class RunningWeb:
    injector: inj.AsyncInjector

    address: WebServerAddress
    token: WebToken
    url: str

    session: agn.Session
    feed: Feed
    submitter: Submitter
    quit_signal: WebQuitSignal


@contextlib.asynccontextmanager
async def running_web(
        config: WebConfig,
        *,
        overrides: ta.Sequence[inj.Elemental] = (),
) -> ta.AsyncIterator[RunningWeb]:
    """The frontend, serving, until the context exits. Overrides replace any of its bindings - its backends, say."""

    els = bind_web(config)
    if overrides:
        els = inj.as_elements(inj.override(els, *overrides))

    async with inj.create_async_managed_injector(
        els,
        factory=inj.create_asyncio_injector,
    ) as injector:
        agent = await injector[agn.Agent]
        session = await injector[agn.Session]
        feed = await injector[Feed]
        submitter = await injector[Submitter]
        server = await injector[AsgiPipelineServer]

        #

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await (await injector[AgentSetup]).run()

        cwd = check.non_empty_str(get_agent_cwd(agent))

        if config.resume is not None:
            feed_transcript(feed, await session.resume())

        #

        quit_signal = await injector[WebQuitSignal]

        # Winds the session down as soon as quitting is asked for, however that is: what is running is cancelled,
        # its ends fed, and then the end of the session announced - the last thing the feed carries.
        async def wind_down() -> None:
            await quit_signal.wait()
            await submitter.aclose()
            quit_signal.announce()

        async with server:
            wind_down_task = asyncio.create_task(wind_down())

            try:
                # Run before anyone can be looking, their output waits in the feed for the first page to load.
                for ax in [
                    *yolo_autoexec(config, cwd),
                    *(config.autoexec or []),
                ]:
                    await (await submitter.submit(ax)).join()

                address = await injector[WebServerAddress]
                token = await injector[WebToken]

                yield RunningWeb(
                    injector=injector,

                    address=address,
                    token=token,
                    url=address.url if config.no_auth else f'{address.url}?token={token.v}',

                    session=session,
                    feed=feed,
                    submitter=submitter,
                    quit_signal=quit_signal,
                )

            finally:
                await quit_signal.quit()
                await wind_down_task


async def serve_web(
        config: WebConfig,
        *,
        overrides: ta.Sequence[inj.Elemental] = (),
) -> None:
    async with running_web(config, overrides=overrides) as rw:
        log.info('Serving session %s on %s', rw.session.id.v, rw.url)

        await rw.quit_signal.wait_announced()


class _PeerDisconnectLogFilter(logging.Filter):
    """
    Drops the pipeline drivers' error logs of a peer gone mid-response - a browser closing a stream, which it does on
    every reload - which are routine here. The server logs them itself, at debug.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.exc_info and isinstance(record.exc_info[1], ConnectionError))


def configure_web_logging() -> None:
    logs.configure_standard_logging('INFO')

    logging.getLogger(PollAsyncioStreamIoPipelineDriver.__module__).addFilter(_PeerDisconnectLogFilter())


async def _a_main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    config = WebConfig.parse_from_arguments(argv)
    config = yolo_process_config(config)

    configure_web_logging()

    await serve_web(config)


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    try:
        asyncio.run(_a_main(argv))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
