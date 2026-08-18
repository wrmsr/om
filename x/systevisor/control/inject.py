# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from omcore.lite.inject import InjectorBindingOrBindings
from omcore.lite.inject import InjectorBindings
from omcore.lite.inject import inj

from ..configs.compiling import SystevisorConfigCompiler
from ..runtime.clocks import SystevisorClock
from ..runtime.coordinator import SystevisorRuntimeCoordinator
from .api import SystevisorApiApplication
from .configs import SystevisorConfigController
from .http import SystevisorHttpServer
from .jsoncodec import SystevisorJsonCodec
from .operations import SystevisorOperationStore
from .plane import SystevisorControlPlane
from .service import SystevisorControlService


@dc.dataclass(frozen=True)
class SystevisorControlBootstrapConfig:
    paths: ta.Sequence[str]
    recursive: bool = False
    state_directory: ta.Optional[str] = None


def _systevisor_control_inject_provide_config_controller(
        compiler: SystevisorConfigCompiler,
        coordinator: SystevisorRuntimeCoordinator,
        clock: SystevisorClock,
        json_codec: SystevisorJsonCodec,
        bootstrap: SystevisorControlBootstrapConfig,
) -> SystevisorConfigController:
    return SystevisorConfigController(
        compiler,
        coordinator,
        clock,
        json_codec,
        bootstrap.paths,
        recursive=bootstrap.recursive,
        state_directory=bootstrap.state_directory,
    )


def systevisor_bind_control(bootstrap: SystevisorControlBootstrapConfig) -> InjectorBindings:
    bindings: ta.List[InjectorBindingOrBindings] = [
        inj.bind(bootstrap),
        inj.bind(SystevisorConfigCompiler, singleton=True),
        inj.bind(SystevisorJsonCodec, singleton=True),
        inj.bind(_systevisor_control_inject_provide_config_controller, singleton=True),
        inj.bind(SystevisorOperationStore, singleton=True),
        inj.bind(SystevisorControlService, singleton=True),
        inj.bind(SystevisorApiApplication, singleton=True),
        inj.bind(SystevisorHttpServer, singleton=True),
        inj.bind(SystevisorControlPlane, singleton=True),
    ]
    return inj.as_bindings(*bindings)
