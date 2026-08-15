from ... import dataclasses as dc
from ..runtime import ServiceRuntime
from ..services import RuntimeService
from .configs import ChildProcessConfig
from .configs import ChildTerminationConfig
from .processes import DEFAULT_CHILD_PROCESS_FACTORY
from .processes import ChildProcessFactory
from .supervisors import ChildProcessSupervisor
from .supervisors import ChildProcessSupervisorConfig


##


class ChildProcessService(RuntimeService['ChildProcessService.Config']):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        process: ChildProcessConfig
        termination: ChildTerminationConfig = ChildTerminationConfig()

        def supervisor_config(self) -> ChildProcessSupervisorConfig:
            return ChildProcessSupervisorConfig(
                process=self.process,
                termination=self.termination,
            )

        def __post_init__(self) -> None:
            self.supervisor_config()

    def __init__(
            self,
            config: Config,
            *,
            process_factory: ChildProcessFactory = DEFAULT_CHILD_PROCESS_FACTORY,
    ) -> None:
        super().__init__(config)

        self._process_factory = process_factory

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        ChildProcessSupervisor(
            self.config.supervisor_config(),
            process_factory=self._process_factory,
        ).run(runtime)
