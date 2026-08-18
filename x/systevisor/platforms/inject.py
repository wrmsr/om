# ruff: noqa: UP006 UP007 UP045
import typing as ta

from omcore.lite.inject import InjectorBindingOrBindings
from omcore.lite.inject import InjectorBindings
from omcore.lite.inject import inj

from .runtime import SystevisorManagerLogging
from .runtime import SystevisorManagerRuntime
from .runtime import SystevisorPidFileManager
from .runtime import SystevisorPosixProcessBootstrap
from .runtime import SystevisorProcessBootstrap
from .runtime import SystevisorServiceNotifier
from .runtime import SystevisorSystemdServiceNotifier


def systevisor_bind_platforms() -> InjectorBindings:
    bindings: ta.List[InjectorBindingOrBindings] = [
        inj.bind(SystevisorPosixProcessBootstrap, singleton=True),
        inj.bind(SystevisorProcessBootstrap, to_key=SystevisorPosixProcessBootstrap),
        inj.bind(SystevisorManagerLogging, singleton=True),
        inj.bind(SystevisorPidFileManager, singleton=True),
        inj.bind(SystevisorSystemdServiceNotifier, singleton=True),
        inj.bind(SystevisorServiceNotifier, to_key=SystevisorSystemdServiceNotifier),
        inj.bind(SystevisorManagerRuntime, singleton=True),
    ]
    return inj.as_bindings(*bindings)
