# ruff: noqa: UP006 UP007 UP045
import abc
import dataclasses as dc
import enum
import os
import tempfile
import typing as ta

from omcore.lite.abstract import Abstract

from ..configs.compiling import SystevisorConfigCompiler
from ..configs.compiling import SystevisorConfigCompileResult
from ..configs.diagnostics import SystevisorConfigDiagnostic
from ..configs.diagnostics import SystevisorConfigDiagnosticSeverity
from ..configs.diagnostics import SystevisorConfigDiagnosticStage
from ..configs.snapshots import SystevisorConfigSnapshot
from ..core.inputs import SystevisorApplySnapshotCommand
from ..runtime.clocks import SystevisorClock
from ..runtime.coordinator import SystevisorRuntimeCoordinator
from ..runtime.events import SystevisorBusEvent
from ..runtime.events import SystevisorEventSubscription
from .jsoncodec import SystevisorJsonCodec


class SystevisorConfigPreparedChange(Abstract):
    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class SystevisorConfigParticipant(Abstract):
    @abc.abstractmethod
    def prepare(self, snapshot: SystevisorConfigSnapshot) -> SystevisorConfigPreparedChange:
        raise NotImplementedError


class SystevisorConfigAttemptKind(enum.Enum):
    CHECK = 'check'
    RELOAD = 'reload'
    INITIAL = 'initial'


@dc.dataclass(frozen=True)
class SystevisorConfigAttempt:
    sequence: int
    kind: SystevisorConfigAttemptKind
    request_id: ta.Optional[str]
    at: float
    valid: bool
    applied: bool
    digest: ta.Optional[str]
    discovered_paths: ta.Sequence[str]
    diagnostics: ta.Sequence[SystevisorConfigDiagnostic]


@dc.dataclass(frozen=True)
class SystevisorConfigControllerResult:
    attempt: SystevisorConfigAttempt
    snapshot: ta.Optional[SystevisorConfigSnapshot]


class SystevisorConfigController:
    def __init__(
            self,
            compiler: SystevisorConfigCompiler,
            coordinator: SystevisorRuntimeCoordinator,
            clock: SystevisorClock,
            json_codec: SystevisorJsonCodec,
            paths: ta.Iterable[str],
            *,
            recursive: bool = False,
            state_directory: ta.Optional[str] = None,
    ) -> None:
        self._compiler = compiler
        self._coordinator = coordinator
        self._clock = clock
        self._json_codec = json_codec
        self._paths = tuple(paths)
        self._recursive = recursive
        self._state_directory = state_directory
        self._attempt_sequence = 0
        self._last_attempt: ta.Optional[SystevisorConfigAttempt] = None
        self._signal_subscription: ta.Optional[SystevisorEventSubscription] = None
        self._participants: ta.List[SystevisorConfigParticipant] = []

    @property
    def paths(self) -> ta.Sequence[str]:
        return self._paths

    @property
    def recursive(self) -> bool:
        return self._recursive

    @property
    def state_directory(self) -> ta.Optional[str]:
        return self._state_directory

    @property
    def last_attempt(self) -> ta.Optional[SystevisorConfigAttempt]:
        return self._last_attempt

    @property
    def active_snapshot(self) -> ta.Optional[SystevisorConfigSnapshot]:
        return self._coordinator.engine.state.snapshot

    def install_signal_reload(self) -> None:
        if self._signal_subscription is not None:
            raise RuntimeError('signal reload is already installed')

        def on_event(event: SystevisorBusEvent) -> None:
            if event.topic == 'runtime.reload_requested':
                self.reload()

        self._signal_subscription = self._coordinator.event_bus.subscribe_callback(on_event)

    def add_participant(self, participant: SystevisorConfigParticipant) -> None:
        if participant in self._participants:
            raise ValueError('configuration participant is already registered')
        self._participants.append(participant)

    def _compile(self) -> SystevisorConfigCompileResult:
        return self._compiler.compile(self._paths, recursive=self._recursive)

    def _record(
            self,
            kind: SystevisorConfigAttemptKind,
            request_id: ta.Optional[str],
            result: SystevisorConfigCompileResult,
            applied: bool,
    ) -> SystevisorConfigControllerResult:
        self._attempt_sequence += 1
        attempt = SystevisorConfigAttempt(
            sequence=self._attempt_sequence,
            kind=kind,
            request_id=request_id,
            at=self._clock.monotonic(),
            valid=result.is_valid,
            applied=applied,
            digest=result.snapshot.digest if result.snapshot is not None else None,
            discovered_paths=result.discovered_paths,
            diagnostics=result.diagnostics,
        )
        self._last_attempt = attempt
        topic = (
            'config.checked' if kind is SystevisorConfigAttemptKind.CHECK else
            'config.applied' if applied else
            'config.rejected'
        )
        self._coordinator.event_bus.publish(topic, attempt, self._clock.monotonic())
        try:
            self._persist_attempt(attempt, result.snapshot)
        except OSError as exc:
            self._coordinator.event_bus.publish('config.status_persist_failed', {
                'attempt_sequence': attempt.sequence,
                'message': str(exc),
            }, self._clock.monotonic())
        return SystevisorConfigControllerResult(attempt=attempt, snapshot=result.snapshot)

    def check(self, request_id: ta.Optional[str] = None) -> SystevisorConfigControllerResult:
        result = self._compile()
        return self._record(SystevisorConfigAttemptKind.CHECK, request_id, result, False)

    def reload(
            self,
            request_id: ta.Optional[str] = None,
            *,
            initial: bool = False,
    ) -> SystevisorConfigControllerResult:
        return self.apply_compiled(self._compile(), request_id, initial=initial)

    def apply_compiled(
            self,
            result: SystevisorConfigCompileResult,
            request_id: ta.Optional[str] = None,
            *,
            initial: bool = False,
    ) -> SystevisorConfigControllerResult:
        prepared: ta.List[SystevisorConfigPreparedChange] = []
        if result.snapshot is not None:
            try:
                for participant in self._participants:
                    prepared.append(participant.prepare(result.snapshot))
            except Exception as exc:  # noqa: BLE001
                for change in reversed(prepared):
                    change.rollback()
                result = SystevisorConfigCompileResult(
                    snapshot=None,
                    diagnostics=(SystevisorConfigDiagnostic(
                        severity=SystevisorConfigDiagnosticSeverity.ERROR,
                        stage=SystevisorConfigDiagnosticStage.PREPARE,
                        code='prepare_failed',
                        message=f'{type(exc).__name__}: {exc}',
                    ),),
                    discovered_paths=result.discovered_paths,
                )

        applied = result.snapshot is not None
        if result.snapshot is not None:
            try:
                self._coordinator.submit(SystevisorApplySnapshotCommand(result.snapshot, request_id))
            except BaseException:
                for change in reversed(prepared):
                    change.rollback()
                raise
            for change in prepared:
                change.commit()
        return self._record(
            SystevisorConfigAttemptKind.INITIAL if initial else SystevisorConfigAttemptKind.RELOAD,
            request_id,
            result,
            applied,
        )

    def rehydrate(self, snapshot: SystevisorConfigSnapshot) -> None:
        active = self._coordinator.engine.state.snapshot
        if active is None or active.digest != snapshot.digest:
            raise RuntimeError('engine and controller handoff snapshots do not match')
        prepared: ta.List[SystevisorConfigPreparedChange] = []
        try:
            for participant in self._participants:
                prepared.append(participant.prepare(snapshot))
        except BaseException:
            for change in reversed(prepared):
                change.rollback()
            raise
        try:
            for change in prepared:
                change.commit()
        except BaseException:
            for change in reversed(prepared):
                change.rollback()
            raise
        self._coordinator.configure_snapshot_runtime(snapshot)

    def _effective_state_directory(self, snapshot: ta.Optional[SystevisorConfigSnapshot]) -> ta.Optional[str]:
        if self._state_directory is not None:
            return self._state_directory
        if snapshot is not None and snapshot.config.manager.state_directory is not None:
            return snapshot.config.manager.state_directory
        active = self.active_snapshot
        if active is not None:
            return active.config.manager.state_directory
        return None

    def _persist_attempt(
            self,
            attempt: SystevisorConfigAttempt,
            snapshot: ta.Optional[SystevisorConfigSnapshot],
    ) -> None:
        state_directory = self._effective_state_directory(snapshot)
        if state_directory is None:
            return
        os.makedirs(state_directory, mode=0o700, exist_ok=True)
        target_path = os.path.join(state_directory, 'config-status.json')
        fd, temporary_path = tempfile.mkstemp(prefix='.config-status.', dir=state_directory)
        try:
            data = self._json_codec.dumps(attempt, pretty=True)
            offset = 0
            while offset < len(data):
                offset += os.write(fd, data[offset:])
            os.fsync(fd)
            os.close(fd)
            fd = -1
            os.replace(temporary_path, target_path)
            directory_fd = os.open(state_directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

    def close(self) -> None:
        if self._signal_subscription is not None:
            self._signal_subscription.close()
            self._signal_subscription = None
