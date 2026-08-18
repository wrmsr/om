# ruff: noqa: DTZ001 PTH100 PTH118 PTH123 PT009 UP006 UP007 UP017 UP045
import datetime
import os.path
import tempfile
import typing as ta
import unittest

from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorManagerConfig
from x.systevisor.configs.models import SystevisorScheduleActionConfig
from x.systevisor.configs.models import SystevisorScheduleActionKind
from x.systevisor.configs.models import SystevisorScheduleConcurrencyPolicy
from x.systevisor.configs.models import SystevisorScheduleConfig
from x.systevisor.configs.models import SystevisorScheduleMissedPolicy
from x.systevisor.configs.models import SystevisorScheduleTargetKind
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.control.operations import SystevisorOperation
from x.systevisor.control.operations import SystevisorOperationStore
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.scheduling.cron import SystevisorCronError
from x.systevisor.scheduling.cron import systevisor_parse_cron
from x.systevisor.scheduling.runtime import SystevisorJsonScheduleStateStore
from x.systevisor.scheduling.runtime import SystevisorSchedulePersistentState
from x.systevisor.scheduling.runtime import SystevisorScheduler
from x.systevisor.scheduling.runtime import SystevisorScheduleStateStore
from x.systevisor.tests.fakes import SystevisorFakeClock


_SYSTEVISOR_TEST_SCHEDULE_EPOCH = datetime.datetime(
    2024,
    1,
    1,
    tzinfo=datetime.timezone.utc,
).timestamp()


class SystevisorTestScheduleConfigController:
    def __init__(self) -> None:
        self.participants: ta.List[ta.Any] = []

    def add_participant(self, participant: ta.Any) -> None:
        self.participants.append(participant)


class SystevisorTestScheduleFdioManager:
    def __init__(self) -> None:
        self.handlers: ta.List[ta.Any] = []

    def register(self, handler: ta.Any) -> None:
        self.handlers.append(handler)


class SystevisorTestScheduleStateStore(SystevisorScheduleStateStore):
    def __init__(self) -> None:
        self.states: ta.Mapping[str, SystevisorSchedulePersistentState] = {}

    def load(self, path: str) -> ta.Mapping[str, SystevisorSchedulePersistentState]:
        return self.states

    def save(self, path: str, states: ta.Mapping[str, SystevisorSchedulePersistentState]) -> None:
        self.states = dict(states)


class SystevisorTestScheduleControl:
    def __init__(self, event_bus: SystevisorEventBus, clock: SystevisorFakeClock) -> None:
        self.operations = SystevisorOperationStore(event_bus, clock)
        self.calls: ta.List[ta.Tuple[str, ta.Optional[str], ta.Optional[bool]]] = []

    def _operation(self, kind: str, target: ta.Optional[str] = None) -> SystevisorOperation:
        self.calls.append((kind, target, None))
        return self.operations.create(kind, target)

    def set_unit(self, target: str, active: bool) -> SystevisorOperation:
        self.calls.append(('unit', target, active))
        return self.operations.create('unit.start' if active else 'unit.stop', target)

    def set_collection(self, target: str, active: bool) -> SystevisorOperation:
        self.calls.append(('collection', target, active))
        return self.operations.create('collection.start' if active else 'collection.stop', target)

    def set_instance(self, target: str, active: bool) -> SystevisorOperation:
        self.calls.append(('instance', target, active))
        return self.operations.create('instance.start' if active else 'instance.stop', target)

    def restart_unit(self, target: str) -> SystevisorOperation:
        return self._operation('unit.restart', target)

    def restart_instance(self, target: str) -> SystevisorOperation:
        return self._operation('instance.restart', target)

    def shutdown(self) -> SystevisorOperation:
        return self._operation('manager.shutdown')


def _systevisor_test_schedule_snapshot(
        *,
        missed: SystevisorScheduleMissedPolicy = SystevisorScheduleMissedPolicy.SKIP,
        concurrency: SystevisorScheduleConcurrencyPolicy = SystevisorScheduleConcurrencyPolicy.SKIP,
        state_directory: ta.Optional[str] = '/state',
) -> ta.Any:
    return systevisor_build_config_snapshot(SystevisorConfig(
        manager=SystevisorManagerConfig(state_directory=state_directory),
        units={'job': SystevisorUnitConfig(exec=SystevisorExecConfig(argv=('/bin/true',)))},
        schedules={
            'job-every-minute': SystevisorScheduleConfig(
                cron='* * * * *',
                action=SystevisorScheduleActionConfig(
                    kind=SystevisorScheduleActionKind.RESTART,
                    target_kind=SystevisorScheduleTargetKind.UNIT,
                    target='job',
                ),
                missed=missed,
                max_catch_up=2,
                concurrency=concurrency,
            ),
        },
    ), (), ())


def _systevisor_test_scheduler(
        clock: SystevisorFakeClock,
        store: ta.Optional[SystevisorScheduleStateStore] = None,
) -> ta.Tuple[SystevisorScheduler, SystevisorTestScheduleControl, SystevisorEventBus]:
    event_bus = SystevisorEventBus()
    control = SystevisorTestScheduleControl(event_bus, clock)
    scheduler = SystevisorScheduler(
        ta.cast(ta.Any, SystevisorTestScheduleConfigController()),
        ta.cast(ta.Any, control),
        clock,
        ta.cast(ta.Any, SystevisorTestScheduleFdioManager()),
        event_bus,
        store or SystevisorTestScheduleStateStore(),
    )
    return scheduler, control, event_bus


class TestSystevisorCron(unittest.TestCase):
    def test_steps_ranges_and_sunday_alias(self) -> None:
        cron = systevisor_parse_cron('*/15 9-17 * * 1-5')
        self.assertTrue(cron.matches_datetime(datetime.datetime(2024, 1, 1, 9, 30)))
        self.assertFalse(cron.matches_datetime(datetime.datetime(2024, 1, 1, 18, 0)))
        sunday = systevisor_parse_cron('0 0 * * 7')
        self.assertTrue(sunday.matches_datetime(datetime.datetime(2024, 1, 7, 0, 0)))

    def test_day_fields_use_classic_or_semantics(self) -> None:
        cron = systevisor_parse_cron('0 0 1 * 1')
        self.assertTrue(cron.matches_datetime(datetime.datetime(2024, 1, 8, 0, 0)))
        self.assertTrue(cron.matches_datetime(datetime.datetime(2024, 2, 1, 0, 0)))

    def test_invalid_expression_is_rejected(self) -> None:
        with self.assertRaises(SystevisorCronError):
            systevisor_parse_cron('61 * * * *')


class TestSystevisorScheduler(unittest.TestCase):
    def test_monotonic_deadline_fires_normal_control_operation(self) -> None:
        clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        scheduler, control, event_bus = _systevisor_test_scheduler(clock)
        scheduler.prepare(_systevisor_test_schedule_snapshot(state_directory=None)).commit()

        self.assertEqual(scheduler.next_deadline(), 60.)
        clock.advance(60.)
        scheduler.on_timeout()

        self.assertEqual(control.calls, [('unit.restart', 'job', None)])
        state = scheduler.states['job-every-minute']
        self.assertEqual(state.fire_count, 1)
        self.assertEqual(state.next_due_wall_time, _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 120.)
        self.assertTrue(any(event.topic == 'schedule' for event in event_bus.journal()))

    def test_latest_missed_policy_coalesces_and_concurrency_skips(self) -> None:
        clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        scheduler, control, _ = _systevisor_test_scheduler(clock)
        scheduler.prepare(_systevisor_test_schedule_snapshot(
            missed=SystevisorScheduleMissedPolicy.LATEST,
            state_directory=None,
        )).commit()
        clock.advance(180.)
        scheduler.on_timeout()

        state = scheduler.states['job-every-minute']
        self.assertEqual(state.fire_count, 1)
        self.assertEqual(state.skip_count, 2)
        clock.advance(60.)
        scheduler.on_timeout()
        self.assertEqual(state.fire_count, 1)
        self.assertEqual(state.skip_count, 3)
        self.assertEqual(len(control.calls), 1)

    def test_persistent_state_drives_restart_catch_up(self) -> None:
        store = SystevisorTestScheduleStateStore()
        first_clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        first, _, _ = _systevisor_test_scheduler(first_clock, store)
        snapshot = _systevisor_test_schedule_snapshot(missed=SystevisorScheduleMissedPolicy.LATEST)
        first.prepare(snapshot).commit()
        first_clock.advance(60.)
        first.on_timeout()

        second_clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH + 240.)
        second, second_control, _ = _systevisor_test_scheduler(second_clock, store)
        second.prepare(snapshot).commit()
        second.on_timeout()

        self.assertEqual(len(second_control.calls), 1)
        self.assertEqual(second.states['job-every-minute'].last_due_wall_time, _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 240.)

    def test_all_policy_obeys_catch_up_bound(self) -> None:
        clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        scheduler, control, _ = _systevisor_test_scheduler(clock)
        scheduler.prepare(_systevisor_test_schedule_snapshot(
            missed=SystevisorScheduleMissedPolicy.ALL,
            concurrency=SystevisorScheduleConcurrencyPolicy.ALLOW,
            state_directory=None,
        )).commit()
        clock.advance(300.)

        scheduler.on_timeout()

        state = scheduler.states['job-every-minute']
        self.assertEqual(len(control.calls), 2)
        self.assertEqual(state.fire_count, 2)
        self.assertEqual(state.skip_count, 3)

    def test_json_store_atomically_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, 'schedules.json')
            store = SystevisorJsonScheduleStateStore()
            states = {
                'job': SystevisorSchedulePersistentState(
                    fingerprint='abc',
                    last_due_wall_time=123.,
                    last_fired_wall_time=120.,
                    fire_count=2,
                    skip_count=3,
                ),
            }

            store.save(path, states)

            self.assertEqual(store.load(path), states)
