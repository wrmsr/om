# @om-lite
# ruff: noqa: UP006 UP007 UP045
from omcore.lite.inject import InjectorBindings
from omcore.lite.inject import inj

from .runtime import SystevisorPosixSelfUpdateExecBackend
from .runtime import SystevisorSelfUpdateExecBackend
from .runtime import SystevisorSelfUpdateManager


def systevisor_bind_self_update() -> InjectorBindings:
    return inj.as_bindings(
        inj.bind(SystevisorPosixSelfUpdateExecBackend, singleton=True),
        inj.bind(SystevisorSelfUpdateExecBackend, to_key=SystevisorPosixSelfUpdateExecBackend),
        inj.bind(SystevisorSelfUpdateManager, singleton=True),
    )
