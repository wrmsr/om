from omcore import inject as inj

from ... import agent as agn
from ...core import ui
from ..agent.inject.events import bind_on_agent_event_subscriber
from ..inject.inject import bind_ui
from ..paths import AgentCwdDisplayPathResolver
from .config import WebConfig
from .feed.feed import Feed
from .info import WebInfoBuilder
from .output.agents import AgentEventFeeder
from .output.agents import VerboseAgentEventFeeder
from .output.display import FeedTextDisplayer
from .permissions import FeedPermissionAsker
from .quit import WebQuitSignal
from .server.inject import bind_server
from .submissions import Submitter
from .texts import WebTextRenderer


##


def _provide_text_rendering_options(paths: AgentCwdDisplayPathResolver) -> ui.TextRenderingOptions:
    return ui.TextRenderingOptions(paths=paths)


def _provide_web_text_renderer(options: ui.TextRenderingOptions) -> WebTextRenderer:
    return WebTextRenderer(options)


def bind_output(config: WebConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(AgentCwdDisplayPathResolver, singleton=True),
        inj.bind(ui.TextRenderingOptions, singleton=True, to_fn=_provide_text_rendering_options),
        inj.bind(_provide_web_text_renderer, singleton=True),

        inj.bind(FeedTextDisplayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=FeedTextDisplayer),

        inj.bind(AgentEventFeeder, singleton=True),
        bind_on_agent_event_subscriber(AgentEventFeeder),
    ]

    if config.verbose:
        lst.extend([
            inj.bind(VerboseAgentEventFeeder, singleton=True),
            bind_on_agent_event_subscriber(VerboseAgentEventFeeder),
        ])

    return inj.as_elements(*lst)


def bind_input(config: WebConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(FeedPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=FeedPermissionAsker),

        inj.bind(Submitter, singleton=True),
    )


##


def bind_web(config: WebConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(WebConfig, to_const=config),

        bind_ui(config),

        inj.bind(Feed, singleton=True),

        bind_output(config),
        bind_input(config),

        inj.bind(WebQuitSignal, singleton=True),
        inj.bind(ui.QuitSignal, to_key=WebQuitSignal),

        inj.bind(WebInfoBuilder, singleton=True),

        bind_server(config),
    ]

    return inj.as_elements(*lst)
