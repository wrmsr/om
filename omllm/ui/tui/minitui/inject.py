from omcore import inject as inj
from omdev.tui import minitui as mt

from .... import agent as agn
from ....core import ui
from ..config import Config
from ..inject import bind_on_agent_event_subscriber
from ..inject import bind_tui
from .app import AppQuitSignal
from .app import MinituiChatApp
from .input import CardPermissionAsker
from .output import AgentEventRenderer
from .output import MinituiTextDisplayer
from .output import VerboseEventRenderer


##


def _provide_driver(surface: mt.InlineSurface) -> mt.AsyncioDriver:
    # EOF goes through the app's quit funnel, like every other way out, rather than stopping the driver on the spot.
    return mt.AsyncioDriver(surface, app_handles_eof=True)


def bind_app(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(mt.InlineSurface(kitty_keys=True)),
        inj.bind(_provide_driver, singleton=True),
        inj.bind(MinituiChatApp, singleton=True),
    )


##


def bind_input(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(CardPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=CardPermissionAsker),
    )


##


def bind_output(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(MinituiTextDisplayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=MinituiTextDisplayer),

        inj.bind(AgentEventRenderer, singleton=True),
        bind_on_agent_event_subscriber(AgentEventRenderer),
    ]

    if config.verbose:
        lst.extend([
            inj.bind(VerboseEventRenderer, singleton=True),
            bind_on_agent_event_subscriber(VerboseEventRenderer),
        ])

    return inj.as_elements(*lst)


##


def bind_minitui(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(config),

        bind_tui(config),

        bind_app(config),
        bind_input(config),
        bind_output(config),

        inj.bind(AppQuitSignal, singleton=True),
        inj.bind(ui.QuitSignal, to_key=AppQuitSignal),
    ]

    return inj.as_elements(*lst)
