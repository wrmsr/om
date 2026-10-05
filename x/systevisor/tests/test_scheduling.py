# ruff: noqa: DTZ001 PTH100 PTH118 PTH123 PT009 UP006 UP007 UP017 UP045
import dataclasses as dc
import datetime
import os.path
import tempfile
import typing as ta
import unittest

from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorExecConfig
from ..configs.models import SystevisorManagerConfig
from ..configs.models import SystevisorScheduleActionConfig
from ..configs.models import SystevisorScheduleActionKind
from ..configs.models import SystevisorScheduleConcurrencyPolicy
from ..configs.models import SystevisorScheduleConfig
from ..configs.models import SystevisorScheduleMissedPolicy
from ..configs.models import SystevisorScheduleTargetKind
from ..configs.models import SystevisorUnitConfig
from ..configs.snapshots import systevisor_build_config_snapshot
from ..control.operations import SystevisorOperation
from ..control.operations import SystevisorOperationStore
from ..runtime.events import SystevisorEventBus
from ..scheduling.cron import SystevisorCronError
from ..scheduling.cron import systevisor_parse_cron
from ..scheduling.runtime import SystevisorJsonScheduleStateStore
from ..scheduling.runtime import SystevisorScheduleEventKind
from ..scheduling.runtime import SystevisorSchedulePersistentState
from ..scheduling.runtime import SystevisorScheduler
from ..scheduling.runtime import SystevisorScheduleStateStore
from .fakes import SystevisorFakeClock
from .utils import true_bin


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
        self.save_count = 0

    def load(self, path: str) -> ta.Mapping[str, SystevisorSchedulePersistentState]:
        return self.states

    def save(self, path: str, states: ta.Mapping[str, SystevisorSchedulePersistentState]) -> None:
        self.states = dict(states)
        self.save_count += 1


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
        units={'job': SystevisorUnitConfig(exec=SystevisorExecConfig(argv=(true_bin(),)))},
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


    def test_impossible_date_is_rejected_quickly_rather_than_searched_for(self) -> None:
        cron = systevisor_parse_cron('0 0 31 2 *')
        with self.assertRaises(SystevisorCronError):
            cron.next_after(_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        with self.assertRaises(SystevisorCronError):
            cron.previous_at_or_before(_SYSTEVISOR_TEST_SCHEDULE_EPOCH)

    def test_sparse_expressions_resolve_across_long_gaps(self) -> None:
        def at(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> float:
            return datetime.datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                tzinfo=datetime.timezone.utc,
            ).timestamp()

        leap_day = systevisor_parse_cron('17 4 29 2 *')
        self.assertEqual(leap_day.next_after(at(2024, 2, 29, 4, 17)), at(2028, 2, 29, 4, 17))
        self.assertEqual(leap_day.next_after(at(2096, 3, 1)), at(2104, 2, 29, 4, 17))
        self.assertEqual(leap_day.previous_at_or_before(at(2028, 2, 29, 4, 16, 59)), at(2024, 2, 29, 4, 17))
        self.assertEqual(leap_day.previous_at_or_before(at(2028, 2, 29, 4, 17, 30)), at(2028, 2, 29, 4, 17))

        yearly = systevisor_parse_cron('0 0 1 1 *')
        self.assertEqual(yearly.next_after(at(2024, 1, 1)), at(2025, 1, 1))
        self.assertEqual(yearly.previous_at_or_before(at(2024, 12, 31, 23, 59)), at(2024, 1, 1))

    def test_searches_agree_with_scanning_every_minute(self) -> None:
        minute = datetime.timedelta(minutes=1)
        for source in (
                '* * * * *',
                '*/15 9-17 * * 1-5',
                '0 0 1 * 1',
                '5,35 0,12 1-7 */3 *',
                '0 12 28-31 * 5',
        ):
            cron = systevisor_parse_cron(source)
            for day_offset in range(0, 800, 37):
                start = datetime.datetime.fromtimestamp(
                    _SYSTEVISOR_TEST_SCHEDULE_EPOCH + day_offset * 86400. + day_offset * 617.,
                    datetime.timezone.utc,
                )
                later = start.replace(second=0, microsecond=0) + minute
                while not cron.matches_datetime(later):
                    later += minute
                earlier = start.replace(second=0, microsecond=0)
                while not cron.matches_datetime(earlier):
                    earlier -= minute
                self.assertEqual(cron.next_after(start.timestamp()), later.timestamp(), (source, start))
                self.assertEqual(cron.previous_at_or_before(start.timestamp()), earlier.timestamp(), (source, start))


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

    def test_unreadable_state_is_set_aside_and_schedules_start_from_now(self) -> None:
        for damaged in (b'', b'{"schema_version": 1, "sched', b'\xff\xfe\x00', b'{"schema_version": 99}', b'[]'):
            with self.subTest(damaged=damaged), tempfile.TemporaryDirectory() as temp_dir:
                path = os.path.join(temp_dir, 'schedules.json')
                with open(path, 'wb') as state_file:
                    state_file.write(damaged)
                clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
                store = SystevisorJsonScheduleStateStore()
                scheduler, control, event_bus = _systevisor_test_scheduler(clock, store)

                scheduler.prepare(_systevisor_test_schedule_snapshot(state_directory=temp_dir)).commit()

                self.assertEqual(
                    scheduler.states['job-every-minute'].next_due_wall_time,
                    _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 60.,
                )
                with open(f'{path}.damaged', 'rb') as discarded_file:
                    self.assertEqual(discarded_file.read(), damaged)
                self.assertEqual(set(store.load(path)), {'job-every-minute'})
                [discarded] = [event for event in event_bus.journal() if event.topic == 'schedule.state_discarded']
                self.assertEqual(discarded.payload['discarded_path'], f'{path}.damaged')

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

    def _stepped_forward(
            self,
            missed: SystevisorScheduleMissedPolicy,
    ) -> ta.Tuple[SystevisorScheduler, SystevisorTestScheduleControl, SystevisorEventBus, float]:
        # A manager started before its clock was set: half a century of every-minute occurrences are suddenly overdue.
        clock = SystevisorFakeClock(wall_time=0.)
        scheduler, control, event_bus = _systevisor_test_scheduler(clock)
        scheduler.prepare(_systevisor_test_schedule_snapshot(
            missed=missed,
            concurrency=SystevisorScheduleConcurrencyPolicy.ALLOW,
            state_directory=None,
        )).commit()
        now = _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 30.
        clock.advance(now)
        scheduler.on_timeout()
        self.assertEqual(scheduler.states['job-every-minute'].next_due_wall_time, _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 60.)
        return scheduler, control, event_bus, now

    def _fired_at(self, event_bus: SystevisorEventBus) -> ta.Sequence[float]:
        return [
            event.payload.scheduled_wall_time
            for event in event_bus.journal()
            if event.topic == 'schedule' and event.payload.kind is SystevisorScheduleEventKind.FIRED
        ]

    def test_large_forward_clock_step_is_bounded_work_under_every_policy(self) -> None:
        scheduler, control, event_bus, _ = self._stepped_forward(SystevisorScheduleMissedPolicy.SKIP)
        self.assertEqual(self._fired_at(event_bus), [_SYSTEVISOR_TEST_SCHEDULE_EPOCH])
        self.assertEqual(scheduler.states['job-every-minute'].skip_count, 999)

        scheduler, control, event_bus, _ = self._stepped_forward(SystevisorScheduleMissedPolicy.LATEST)
        self.assertEqual(self._fired_at(event_bus), [_SYSTEVISOR_TEST_SCHEDULE_EPOCH])

        # Bounded catch-up replays the most recent occurrences, ending with the one that is due now.
        scheduler, control, event_bus, _ = self._stepped_forward(SystevisorScheduleMissedPolicy.ALL)
        self.assertEqual(self._fired_at(event_bus), [
            _SYSTEVISOR_TEST_SCHEDULE_EPOCH - 60.,
            _SYSTEVISOR_TEST_SCHEDULE_EPOCH,
        ])
        self.assertEqual(len(control.calls), 2)
        skipped = [
            event.payload.reason
            for event in event_bus.journal()
            if event.topic == 'schedule' and event.payload.kind is SystevisorScheduleEventKind.SKIPPED
        ]
        self.assertEqual(skipped, ['missed-run policy skipped at least 998 occurrence(s)'])

    def test_small_backward_clock_step_is_waited_out_without_firing_twice(self) -> None:
        clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        store = SystevisorTestScheduleStateStore()
        scheduler, control, _ = _systevisor_test_scheduler(clock, store)
        scheduler.prepare(_systevisor_test_schedule_snapshot(
            concurrency=SystevisorScheduleConcurrencyPolicy.ALLOW,
        )).commit()
        clock.advance(60.)
        scheduler.on_timeout()
        self.assertEqual(len(control.calls), 1)
        save_count = store.save_count

        clock.set_wall_time(_SYSTEVISOR_TEST_SCHEDULE_EPOCH - 3600.)
        for _ in range(61):
            scheduler.on_timeout()
            clock.advance(60.)
        self.assertEqual(len(control.calls), 1)
        # Waking with nothing to do is not a reason to rewrite the state file.
        self.assertEqual(store.save_count, save_count)

        clock.advance(60.)
        scheduler.on_timeout()
        self.assertEqual(len(control.calls), 2)
        self.assertEqual(
            scheduler.states['job-every-minute'].last_fired_wall_time,
            _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 120.,
        )

    def test_large_backward_clock_step_carries_on_from_the_new_time(self) -> None:
        clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
        scheduler, control, event_bus = _systevisor_test_scheduler(clock)
        scheduler.prepare(_systevisor_test_schedule_snapshot(
            concurrency=SystevisorScheduleConcurrencyPolicy.ALLOW,
            state_directory=None,
        )).commit()
        clock.advance(60.)
        scheduler.on_timeout()

        corrected = _SYSTEVISOR_TEST_SCHEDULE_EPOCH - 86400.
        clock.set_wall_time(corrected)
        scheduler.on_timeout()
        self.assertEqual(len(control.calls), 1)
        self.assertEqual(scheduler.states['job-every-minute'].next_due_wall_time, corrected + 60.)
        self.assertIn('schedule.clock_stepped', {event.topic for event in event_bus.journal()})

        clock.advance(60.)
        scheduler.on_timeout()
        self.assertEqual(len(control.calls), 2)

    def test_state_persisted_under_a_fast_clock_does_not_silence_a_restart(self) -> None:
        for recorded in (_SYSTEVISOR_TEST_SCHEDULE_EPOCH + 86400., float('nan')):
            store = SystevisorTestScheduleStateStore()
            first, _, _ = _systevisor_test_scheduler(
                SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH),
                store,
            )
            snapshot = _systevisor_test_schedule_snapshot()
            first.prepare(snapshot).commit()
            store.states = {
                name: dc.replace(state, last_due_wall_time=recorded, fire_count=7)
                for name, state in store.states.items()
            }

            clock = SystevisorFakeClock(wall_time=_SYSTEVISOR_TEST_SCHEDULE_EPOCH)
            second, control, _ = _systevisor_test_scheduler(clock, store)
            second.prepare(snapshot).commit()
            state = second.states['job-every-minute']
            self.assertEqual(state.next_due_wall_time, _SYSTEVISOR_TEST_SCHEDULE_EPOCH + 60.)
            self.assertEqual(state.fire_count, 7)

            clock.advance(60.)
            second.on_timeout()
            self.assertEqual(len(control.calls), 1)
