# ruff: noqa: PT009 UP006 UP007 UP045
import unittest

from omcore.lite.marshal import OBJ_MARSHALER_MANAGER
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorDependenciesConfig
from x.systevisor.configs.models import SystevisorDependencyCondition
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorRestartMode
from x.systevisor.configs.models import SystevisorSignalScope
from x.systevisor.configs.models import SystevisorStopConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import SystevisorConfigSnapshot
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorApplyLiveConfigEffect
from x.systevisor.core.effects import SystevisorScheduleDeadlineEffect
from x.systevisor.core.effects import SystevisorSignalProcessEffect
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.events import SystevisorEventKind
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.inputs import SystevisorProcessExitedFact
from x.systevisor.core.inputs import SystevisorRestartInstanceCommand
from x.systevisor.core.inputs import SystevisorSetInstanceDesiredCommand
from x.systevisor.core.inputs import SystevisorShutdownCommand
from x.systevisor.core.inputs import SystevisorSpawnSucceededFact
from x.systevisor.core.state import SystevisorEngineState
from x.systevisor.core.states import SystevisorDeadlineKind
from x.systevisor.core.states import SystevisorProcessState
from x.systevisor.core.states import SystevisorSignalReason
from x.systevisor.tests.fakes import SystevisorEngineHarness


def _systevisor_test_engine_snapshot(**units: SystevisorUnitConfig) -> SystevisorConfigSnapshot:
    return systevisor_build_config_snapshot(SystevisorConfig(units=units), (), ())


def _systevisor_test_engine_unit(
        argv: str,
        *,
        start_secs: float = 0.,
        start_retries: int = 3,
        restart_mode: SystevisorRestartMode = SystevisorRestartMode.UNEXPECTED,
        dependencies: SystevisorDependenciesConfig = SystevisorDependenciesConfig(),
        stop: SystevisorStopConfig = SystevisorStopConfig(),
        priority: int = 999,
) -> SystevisorUnitConfig:
    return SystevisorUnitConfig(
        exec=SystevisorExecConfig(argv=(argv,)),
        restart=SystevisorRestartConfig(
            mode=restart_mode,
            start_secs=start_secs,
            start_retries=start_retries,
            backoff_initial_secs=1.,
            backoff_multiplier=2.,
            backoff_max_secs=60.,
        ),
        dependencies=dependencies,
        stop=stop,
        priority=priority,
    )


def _systevisor_test_engine_effects(output: object, effect_type: object) -> list:
    return [effect for effect in output.effects if isinstance(effect, effect_type)]  # type: ignore[attr-defined,arg-type]


class TestSystevisorEngine(unittest.TestCase):
    def test_dependency_start_is_lock_step(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database', start_secs=2., priority=10),
            web=_systevisor_test_engine_unit(
                'web',
                dependencies=SystevisorDependenciesConfig(
                    requires={'database': SystevisorDependencyCondition.RUNNING},
                ),
                priority=20,
            ),
        )

        applied = harness.submit(SystevisorApplySnapshotCommand(snapshot))
        spawns = _systevisor_test_engine_effects(applied, SystevisorSpawnProcessEffect)
        self.assertEqual([effect.instance_id for effect in spawns], [SystevisorInstanceId('database:0')])
        self.assertEqual(
            harness.engine.state.instances[SystevisorInstanceId('web:0')].blocked_reason,
            'database:running',
        )

        spawned = harness.succeed_spawn(spawns[0])
        deadlines = _systevisor_test_engine_effects(spawned, SystevisorScheduleDeadlineEffect)
        self.assertEqual(len(deadlines), 1)
        self.assertEqual(deadlines[0].kind, SystevisorDeadlineKind.START_STABLE)
        self.assertEqual(_systevisor_test_engine_effects(spawned, SystevisorSpawnProcessEffect), [])

        outputs = harness.advance_to(2.)
        self.assertEqual(len(outputs), 1)
        web_spawns = _systevisor_test_engine_effects(outputs[0], SystevisorSpawnProcessEffect)
        self.assertEqual([effect.instance_id for effect in web_spawns], [SystevisorInstanceId('web:0')])
        self.assertEqual(
            harness.engine.state.instances[SystevisorInstanceId('database:0')].process_state,
            SystevisorProcessState.RUNNING,
        )

    def test_early_exit_backoff_reaches_fatal_without_sleep(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', start_secs=10., start_retries=2),
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))

        expected_deadlines = (1., 3.)
        for attempt, expected_deadline in enumerate(expected_deadlines):
            spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
            harness.succeed_spawn(spawn)
            output = harness.exit_spawn(spawn, 0)
            instance = harness.engine.state.instances[SystevisorInstanceId('worker:0')]
            self.assertEqual(instance.process_state, SystevisorProcessState.BACKOFF)
            backoff = next(
                effect
                for effect in _systevisor_test_engine_effects(output, SystevisorScheduleDeadlineEffect)
                if effect.kind is SystevisorDeadlineKind.BACKOFF
            )
            self.assertEqual(backoff.deadline_at, expected_deadline)
            output = harness.advance_to(expected_deadline)[0]
            self.assertEqual(attempt + 1, instance.start_failures)

        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)
        output = harness.exit_spawn(spawn, 0)
        self.assertEqual(
            harness.engine.state.instances[SystevisorInstanceId('worker:0')].process_state,
            SystevisorProcessState.FATAL,
        )
        self.assertEqual(_systevisor_test_engine_effects(output, SystevisorScheduleDeadlineEffect), [])

    def test_expected_running_exit_does_not_restart(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            oneshot=_systevisor_test_engine_unit('oneshot', restart_mode=SystevisorRestartMode.UNEXPECTED),
        )))
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.exit_spawn(spawn, 0)

        instance = harness.engine.state.instances[SystevisorInstanceId('oneshot:0')]
        self.assertEqual(instance.process_state, SystevisorProcessState.EXITED)
        self.assertTrue(instance.completed_successfully)
        self.assertEqual(_systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect), [])

    def test_live_change_does_not_restart_but_exec_change_does(self) -> None:
        harness = SystevisorEngineHarness()
        initial = _systevisor_test_engine_unit('worker')
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(worker=initial)))
        first_spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(first_spawn)

        live = SystevisorUnitConfig(
            exec=initial.exec,
            restart=initial.restart,
            priority=100,
        )
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(worker=live)))
        self.assertEqual(len(_systevisor_test_engine_effects(output, SystevisorApplyLiveConfigEffect)), 1)
        self.assertEqual(_systevisor_test_engine_effects(output, SystevisorSignalProcessEffect), [])

        replacement = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('replacement',)),
            restart=initial.restart,
            priority=100,
        )
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(worker=replacement)))
        signals = _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].run_id, first_spawn.run_id)
        self.assertEqual(signals[0].reason, SystevisorSignalReason.RESTART)

        output = harness.exit_spawn(first_spawn, 0)
        second_spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        self.assertNotEqual(first_spawn.run_id, second_spawn.run_id)
        self.assertEqual(second_spawn.spec.unit.exec.argv, ('replacement',))

    def test_removed_instance_is_stopped_then_forgotten(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker'),
        )))
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot()))
        self.assertEqual(len(_systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)), 1)
        self.assertIn(SystevisorInstanceId('worker:0'), harness.engine.state.instances)

        output = harness.exit_spawn(spawn, 0)
        self.assertNotIn(SystevisorInstanceId('worker:0'), harness.engine.state.instances)
        self.assertIn(SystevisorEventKind.INSTANCE_REMOVED, {event.kind for event in output.events})

    def test_stop_escalation_uses_run_identity_and_configured_scope(self) -> None:
        harness = SystevisorEngineHarness()
        stop = SystevisorStopConfig(
            signal='INT',
            timeout_secs=5.,
            kill_signal='KILL',
            scope=SystevisorSignalScope.SESSION,
        )
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', stop=stop),
        )))
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.submit(SystevisorSetInstanceDesiredCommand(spawn.instance_id, False))
        first_signal = _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)[0]
        self.assertEqual((first_signal.run_id, first_signal.signal, first_signal.scope), (
            spawn.run_id,
            'INT',
            SystevisorSignalScope.SESSION,
        ))

        outputs = harness.advance_to(5.)
        final_signal = _systevisor_test_engine_effects(outputs[0], SystevisorSignalProcessEffect)[0]
        self.assertEqual((final_signal.run_id, final_signal.signal, final_signal.reason), (
            spawn.run_id,
            'KILL',
            SystevisorSignalReason.ESCALATE,
        ))

    def test_stale_run_fact_cannot_mutate_replacement(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker'),
        )))
        first_spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(first_spawn)
        output = harness.submit(SystevisorRestartInstanceCommand(first_spawn.instance_id))
        self.assertEqual(len(_systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)), 1)
        output = harness.exit_spawn(first_spawn, 0)
        second_spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]

        output = harness.submit(SystevisorProcessExitedFact(first_spawn.run_id, 1))

        instance = harness.engine.state.instances[first_spawn.instance_id]
        self.assertEqual(instance.run_id, second_spawn.run_id)
        self.assertEqual(instance.process_state, SystevisorProcessState.STARTING)
        self.assertEqual(output.events[-1].kind, SystevisorEventKind.STALE_FACT_IGNORED)

    def test_shutdown_stops_in_reverse_priority_and_rejects_start(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            low=_systevisor_test_engine_unit('low', priority=10),
            high=_systevisor_test_engine_unit('high', priority=20),
        )))
        spawns = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)
        for spawn in spawns:
            harness.succeed_spawn(spawn)
        priorities_by_run = {
            instance.run_id: instance.desired_spec.unit.priority
            for instance in harness.engine.state.instances.values()
        }

        output = harness.submit(SystevisorShutdownCommand())
        signals = _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual(
            [priorities_by_run[signal.run_id] for signal in signals],
            [20, 10],
        )
        rejected = harness.submit(SystevisorSetInstanceDesiredCommand(SystevisorInstanceId('low:0'), True))
        self.assertEqual(rejected.events[-1].kind, SystevisorEventKind.COMMAND_REJECTED)

    def test_unknown_and_duplicate_facts_are_observable(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorSpawnSucceededFact(SystevisorRunId(999)))
        self.assertEqual(output.events[-1].kind, SystevisorEventKind.STALE_FACT_IGNORED)

    def test_identical_snapshot_is_process_noop(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_engine_snapshot(worker=_systevisor_test_engine_unit('worker'))
        harness.submit(SystevisorApplySnapshotCommand(snapshot))

        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))

        self.assertEqual(output.effects, ())
        self.assertEqual(output.events[-1].kind, SystevisorEventKind.CONFIG_UNCHANGED)
        self.assertEqual(harness.engine.state.config_generation, 1)

    def test_after_does_not_activate_or_wait_for_inactive_unit(self) -> None:
        harness = SystevisorEngineHarness()
        inactive = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('inactive',)),
            autostart=False,
            restart=SystevisorRestartConfig(start_secs=0.),
        )
        active = _systevisor_test_engine_unit(
            'active',
            dependencies=SystevisorDependenciesConfig(after=('inactive',)),
        )

        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            inactive=inactive,
            active=active,
        )))

        spawns = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)
        self.assertEqual([effect.instance_id for effect in spawns], [SystevisorInstanceId('active:0')])

    def test_engine_state_roundtrips_while_deadline_is_armed(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', start_secs=4.),
        )))
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        restored: SystevisorEngineState = OBJ_MARSHALER_MANAGER.roundtrip_obj(
            harness.engine.state,
            SystevisorEngineState,
        )

        self.assertEqual(restored, harness.engine.state)
        instance = restored.instances[SystevisorInstanceId('worker:0')]
        self.assertEqual(instance.deadline_at, 4.)

    def test_engine_rejects_monotonic_time_reversal(self) -> None:
        harness = SystevisorEngineHarness()
        harness.advance_to(2.)
        harness.submit(SystevisorSpawnSucceededFact(SystevisorRunId(999)))
        with self.assertRaises(ValueError):
            harness.engine.step(SystevisorSpawnSucceededFact(SystevisorRunId(1)), 1.)

    def test_completed_dependency_starts_after_successful_exit(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            migrate=_systevisor_test_engine_unit('migrate'),
            web=_systevisor_test_engine_unit(
                'web',
                dependencies=SystevisorDependenciesConfig(
                    requires={'migrate': SystevisorDependencyCondition.COMPLETED},
                ),
            ),
        )))
        migration = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(migration)

        output = harness.exit_spawn(migration, 0)

        spawns = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)
        self.assertEqual([effect.instance_id for effect in spawns], [SystevisorInstanceId('web:0')])

    def test_identical_input_trace_is_deterministic(self) -> None:
        snapshot = _systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', start_secs=1.),
        )

        def run_trace() -> tuple:
            harness = SystevisorEngineHarness()
            first = harness.submit(SystevisorApplySnapshotCommand(snapshot))
            spawn = _systevisor_test_engine_effects(first, SystevisorSpawnProcessEffect)[0]
            second = harness.succeed_spawn(spawn)
            third = harness.advance_to(1.)[0]
            return first, second, third, harness.engine.state

        self.assertEqual(run_trace(), run_trace())
