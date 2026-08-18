# ruff: noqa: UP006 UP007 UP045
import typing as ta

from omcore.io.fdio.kqueue import KqueueFdioPoller
from omcore.io.fdio.manager import FdioManager
from omcore.io.fdio.pollers import FdioPoller
from omcore.io.fdio.pollers import PollFdioPoller
from omcore.io.fdio.pollers import SelectFdioPoller
from omcore.lite.inject import InjectorBindingOrBindings
from omcore.lite.inject import InjectorBindings
from omcore.lite.inject import inj

from ..core.engine import SystevisorEngine
from .clocks import SystevisorClock
from .clocks import SystevisorSystemClock
from .coordinator import SystevisorRuntimeCoordinator
from .events import SystevisorEventBus
from .health import SystevisorFdioHealthProbeRunner
from .health import SystevisorHealthProbeRunner
from .logs import SystevisorLogManager
from .processes import SystevisorProcessManager


def _systevisor_runtime_inject_provide_engine() -> SystevisorEngine:
    return SystevisorEngine()


def _systevisor_runtime_inject_provide_process_manager() -> SystevisorProcessManager:
    return SystevisorProcessManager()


def _systevisor_runtime_inject_provide_event_bus() -> SystevisorEventBus:
    return SystevisorEventBus()


def _systevisor_runtime_inject_provide_log_manager(
        event_bus: SystevisorEventBus,
        clock: SystevisorClock,
) -> SystevisorLogManager:
    return SystevisorLogManager(event_bus, clock)


def systevisor_bind_runtime() -> InjectorBindings:
    poller_type = ta.cast(ta.Type[FdioPoller], next(filter(None, (
        KqueueFdioPoller,
        PollFdioPoller,
        SelectFdioPoller,
    ))))
    bindings: ta.List[InjectorBindingOrBindings] = [
        inj.bind(poller_type, key=FdioPoller, singleton=True),
        inj.bind(FdioManager, singleton=True),

        inj.bind(SystevisorSystemClock, singleton=True),
        inj.bind(SystevisorClock, to_key=SystevisorSystemClock),

        inj.bind(_systevisor_runtime_inject_provide_engine, singleton=True),
        inj.bind(_systevisor_runtime_inject_provide_process_manager, singleton=True),
        inj.bind(_systevisor_runtime_inject_provide_event_bus, singleton=True),
        inj.bind(_systevisor_runtime_inject_provide_log_manager, singleton=True),
        inj.bind(SystevisorFdioHealthProbeRunner, singleton=True),
        inj.bind(SystevisorHealthProbeRunner, to_key=SystevisorFdioHealthProbeRunner),
        inj.bind(SystevisorRuntimeCoordinator, singleton=True),
    ]
    return inj.as_bindings(*bindings)
