# ruff: noqa: UP006 UP007 UP045
import typing as ta

from ..core.effects import SystevisorEngineEffect
from ..core.effects import SystevisorRunHealthProbeEffect
from ..core.effects import SystevisorScheduleDeadlineEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.engine import SystevisorEngine
from ..core.events import SystevisorEngineOutput
from ..core.events import SystevisorEvent
from ..core.inputs import SystevisorDeadlineReachedFact
from ..core.inputs import SystevisorEngineInput
from ..core.inputs import SystevisorHealthProbeResultFact
from ..core.inputs import SystevisorProcessExitedFact
from ..core.inputs import SystevisorSpawnFailedFact
from ..core.inputs import SystevisorSpawnSucceededFact
from ..runtime.clocks import SystevisorClock


class SystevisorFakeClock(SystevisorClock):
    def __init__(self, monotonic: float = 0., wall_time: float = 0.) -> None:
        self._monotonic = monotonic
        self._wall_time = wall_time

    def monotonic(self) -> float:
        return self._monotonic

    def wall_time(self) -> float:
        return self._wall_time

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError(seconds)
        self._monotonic += seconds
        self._wall_time += seconds


class SystevisorEngineHarness:
    def __init__(self, engine: ta.Optional[SystevisorEngine] = None) -> None:
        self.engine = engine if engine is not None else SystevisorEngine()
        self.now = 0.
        self.effects: ta.List[SystevisorEngineEffect] = []
        self.events: ta.List[SystevisorEvent] = []
        self.deadlines: ta.Dict[int, SystevisorScheduleDeadlineEffect] = {}

    def submit(self, engine_input: SystevisorEngineInput) -> SystevisorEngineOutput:
        output = self.engine.step(engine_input, self.now)
        self.effects.extend(output.effects)
        self.events.extend(output.events)
        for effect in output.effects:
            if isinstance(effect, SystevisorScheduleDeadlineEffect):
                self.deadlines[effect.deadline_id] = effect
        return output

    def advance_to(self, now: float) -> ta.Sequence[SystevisorEngineOutput]:
        if now < self.now:
            raise ValueError(now)
        outputs: ta.List[SystevisorEngineOutput] = []
        while True:
            due = sorted(
                (effect for effect in self.deadlines.values() if effect.deadline_at <= now),
                key=lambda effect: (effect.deadline_at, effect.deadline_id),
            )
            if not due:
                break
            effect = due[0]
            del self.deadlines[effect.deadline_id]
            self.now = effect.deadline_at
            outputs.append(self.submit(SystevisorDeadlineReachedFact(effect.deadline_id)))
        self.now = now
        return tuple(outputs)

    def succeed_spawn(self, effect: SystevisorSpawnProcessEffect) -> SystevisorEngineOutput:
        return self.submit(SystevisorSpawnSucceededFact(effect.run_id))

    def fail_spawn(
            self,
            effect: SystevisorSpawnProcessEffect,
            message: str = 'injected failure',
    ) -> SystevisorEngineOutput:
        return self.submit(SystevisorSpawnFailedFact(effect.run_id, message))

    def exit_spawn(self, effect: SystevisorSpawnProcessEffect, return_code: int) -> SystevisorEngineOutput:
        return self.submit(SystevisorProcessExitedFact(effect.run_id, return_code))

    def health_result(
            self,
            effect: SystevisorRunHealthProbeEffect,
            success: bool,
            message: ta.Optional[str] = None,
    ) -> SystevisorEngineOutput:
        return self.submit(SystevisorHealthProbeResultFact(
            check_id=effect.check_id,
            run_id=effect.run_id,
            success=success,
            message=message,
        ))
