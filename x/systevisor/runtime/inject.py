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
from ..resources.cgroups import SystevisorCgroupManager
from ..resources.namespaces import SystevisorNamespaceChildModifier
from ..resources.sockets import SystevisorInheritedSocketChildModifier
from .clocks import SystevisorClock
from .clocks import SystevisorSystemClock
from .coordinator import SystevisorRuntimeCoordinator
from .events import SystevisorEventBus
from .health import SystevisorFdioHealthProbeRunner
from .health import SystevisorHealthProbeRunner
from .logs import SystevisorChildSyslogWriter
from .logs import SystevisorLogManager
from .logs import SystevisorPosixChildSyslogWriter
from .processes import SystevisorChildPidProvider
from .processes import SystevisorProcessManager
from .processes import SystevisorSystemChildPidProvider


def _systevisor_runtime_inject_provide_engine() -> SystevisorEngine:
    return SystevisorEngine()


def _systevisor_runtime_inject_provide_process_manager(
        child_pid_provider: SystevisorChildPidProvider,
        cgroup_manager: SystevisorCgroupManager,
        namespace_modifier: SystevisorNamespaceChildModifier,
        socket_modifier: SystevisorInheritedSocketChildModifier,
) -> SystevisorProcessManager:
    return SystevisorProcessManager(
        child_pid_provider=child_pid_provider,
        child_modifiers=(cgroup_manager, socket_modifier, namespace_modifier),
    )


def _systevisor_runtime_inject_provide_event_bus() -> SystevisorEventBus:
    return SystevisorEventBus()


def _systevisor_runtime_inject_provide_log_manager(
        event_bus: SystevisorEventBus,
        clock: SystevisorClock,
        syslog_writer: SystevisorChildSyslogWriter,
) -> SystevisorLogManager:
    return SystevisorLogManager(event_bus, clock, syslog_writer)


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
        inj.bind(SystevisorSystemChildPidProvider, singleton=True),
        inj.bind(SystevisorChildPidProvider, to_key=SystevisorSystemChildPidProvider),
        inj.bind(_systevisor_runtime_inject_provide_process_manager, singleton=True),
        inj.bind(_systevisor_runtime_inject_provide_event_bus, singleton=True),
        inj.bind(SystevisorPosixChildSyslogWriter, singleton=True),
        inj.bind(SystevisorChildSyslogWriter, to_key=SystevisorPosixChildSyslogWriter),
        inj.bind(_systevisor_runtime_inject_provide_log_manager, singleton=True),
        inj.bind(SystevisorFdioHealthProbeRunner, singleton=True),
        inj.bind(SystevisorHealthProbeRunner, to_key=SystevisorFdioHealthProbeRunner),
        inj.bind(SystevisorRuntimeCoordinator, singleton=True),
    ]
    return inj.as_bindings(*bindings)
