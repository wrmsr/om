# ruff: noqa: PT009 UP006 UP007 UP045
import typing as ta
import unittest

from omcore.lite.marshal import OBJ_MARSHALER_MANAGER

from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorDependenciesConfig
from ..configs.models import SystevisorDependencyCondition
from ..configs.models import SystevisorDependencyFollow
from ..configs.models import SystevisorExecConfig
from ..configs.models import SystevisorRequirementConfig
from ..configs.models import SystevisorRestartConfig
from ..configs.models import SystevisorRestartMode
from ..configs.models import SystevisorSignalScope
from ..configs.models import SystevisorStopConfig
from ..configs.models import SystevisorUnitConfig
from ..configs.models import SystevisorUnitSignalsConfig
from ..configs.snapshots import SystevisorConfigSnapshot
from ..configs.snapshots import systevisor_build_config_snapshot
from ..core.effects import SystevisorApplyLiveConfigEffect
from ..core.effects import SystevisorScheduleDeadlineEffect
from ..core.effects import SystevisorSignalProcessEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.events import SystevisorEventKind
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..core.identities import SystevisorUnitName
from ..core.inputs import SystevisorApplySnapshotCommand
from ..core.inputs import SystevisorForwardSignalCommand
from ..core.inputs import SystevisorProcessExitedFact
from ..core.inputs import SystevisorRestartInstanceCommand
from ..core.inputs import SystevisorSetInstanceDesiredCommand
from ..core.inputs import SystevisorSetUnitDesiredCommand
from ..core.inputs import SystevisorShutdownCommand
from ..core.inputs import SystevisorSpawnSucceededFact
from ..core.state import SystevisorEngineState
from ..core.states import SystevisorDeadlineKind
from ..core.states import SystevisorDesiredOrigin
from ..core.states import SystevisorDesiredState
from ..core.states import SystevisorProcessState
from ..core.states import SystevisorSignalReason
from .fakes import SystevisorEngineHarness


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
        signals: SystevisorUnitSignalsConfig = SystevisorUnitSignalsConfig(),
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
        signals=signals,
        priority=priority,
    )


def _systevisor_test_engine_effects(output: object, effect_type: object) -> list:
    return [effect for effect in output.effects if isinstance(effect, effect_type)]  # type: ignore[attr-defined,arg-type]


class TestSystevisorEngine(unittest.TestCase):
    def test_manager_signal_forwarding_is_rewritten_by_run_identity(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit(
                'worker',
                signals=SystevisorUnitSignalsConfig(
                    forward={'USR1': 'HUP'},
                    scope=SystevisorSignalScope.PROCESS,
                ),
            ),
        )))
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.submit(SystevisorForwardSignalCommand('SIGUSR1'))

        forwarded = _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual(len(forwarded), 1)
        self.assertEqual(
            (forwarded[0].run_id, forwarded[0].signal, forwarded[0].reason),
            (spawn.run_id, 'HUP', SystevisorSignalReason.FORWARD),
        )
        self.assertIn(SystevisorEventKind.SIGNAL_FORWARDED, {event.kind for event in output.events})

    def test_dependency_start_is_lock_step(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database', start_secs=2., priority=10),
            web=_systevisor_test_engine_unit(
                'web',
                dependencies=SystevisorDependenciesConfig(
                    requires={'database': SystevisorRequirementConfig(condition=SystevisorDependencyCondition.RUNNING)},
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

    def test_running_exits_are_restarted_on_a_backoff_which_a_stable_run_resets(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', restart_mode=SystevisorRestartMode.ALWAYS),
        )))
        instance = harness.engine.state.instances[SystevisorInstanceId('worker:0')]

        def run_for(uptime: float) -> ta.Optional[float]:
            # Returns how long the engine waits before respawning a run which exits after the given uptime.
            nonlocal output
            spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
            harness.succeed_spawn(spawn)
            self.assertEqual(instance.process_state, SystevisorProcessState.RUNNING)
            harness.advance_to(harness.now + uptime)
            exited_at = harness.now
            output = harness.exit_spawn(spawn, 1)
            if _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect):
                return 0.
            self.assertEqual(instance.process_state, SystevisorProcessState.BACKOFF)
            backoff = next(
                effect
                for effect in _systevisor_test_engine_effects(output, SystevisorScheduleDeadlineEffect)
                if effect.kind is SystevisorDeadlineKind.BACKOFF
            )
            output = harness.advance_to(backoff.deadline_at)[-1]
            return backoff.deadline_at - exited_at

        # The first exit restarts at once; a unit which keeps dying young then waits longer each time, up to the cap,
        # without ever being given up on.
        self.assertEqual(
            [run_for(.5) for _ in range(9)],
            [0., 1., 2., 4., 8., 16., 32., 60., 60.],
        )
        self.assertEqual(instance.start_failures, 0)

        # A run which lasted is forgiven its history.
        self.assertEqual(run_for(60.), 0.)
        self.assertEqual(run_for(.5), 1.)

        # So is one the operator restarts by hand.
        spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)
        harness.submit(SystevisorRestartInstanceCommand(instance.instance_id))
        output = harness.exit_spawn(spawn, -15)
        self.assertEqual(run_for(.5), 0.)

    def test_restart_backoff_is_cancelled_by_a_stop(self) -> None:
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            worker=_systevisor_test_engine_unit('worker', restart_mode=SystevisorRestartMode.ALWAYS),
        )))
        instance = harness.engine.state.instances[SystevisorInstanceId('worker:0')]
        for _ in range(2):
            spawn = _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)[0]
            harness.succeed_spawn(spawn)
            output = harness.exit_spawn(spawn, 1)
        self.assertEqual(instance.process_state, SystevisorProcessState.BACKOFF)

        harness.submit(SystevisorSetInstanceDesiredCommand(instance.instance_id, False))
        self.assertEqual(instance.process_state, SystevisorProcessState.STOPPED)
        self.assertEqual(
            [output for output in harness.advance_to(120.) if output.effects],
            [],
        )

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
            scope=SystevisorSignalScope.PROCESS,
            kill_scope=SystevisorSignalScope.SESSION,
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
            SystevisorSignalScope.PROCESS,
        ))

        outputs = harness.advance_to(5.)
        final_signal = _systevisor_test_engine_effects(outputs[0], SystevisorSignalProcessEffect)[0]
        self.assertEqual((final_signal.run_id, final_signal.signal, final_signal.reason), (
            spawn.run_id,
            'KILL',
            SystevisorSignalReason.ESCALATE,
        ))
        self.assertEqual(final_signal.scope, SystevisorSignalScope.SESSION)

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

    def _start_all(
            self,
            harness: SystevisorEngineHarness,
            snapshot: SystevisorConfigSnapshot,
    ) -> ta.Mapping[str, ta.Any]:
        spawns: ta.Dict[str, ta.Any] = {}
        outputs = [harness.submit(SystevisorApplySnapshotCommand(snapshot))]
        while outputs:
            for spawn in _systevisor_test_engine_effects(outputs.pop(), SystevisorSpawnProcessEffect):
                spawns[spawn.instance_id] = spawn
                outputs.append(harness.succeed_spawn(spawn))
        self.assertEqual(
            {instance.process_state for instance in harness.engine.state.instances.values()},
            {SystevisorProcessState.RUNNING},
        )
        return spawns

    def test_stops_are_ordered_as_the_reverse_of_starts(self) -> None:
        harness = SystevisorEngineHarness()
        spawns = self._start_all(harness, _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database'),
            cache=_systevisor_test_engine_unit('cache', dependencies=SystevisorDependenciesConfig(before=('web',))),
            web=SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('web',)),
                replicas=2,
                restart=SystevisorRestartConfig(start_secs=0.),
                dependencies=SystevisorDependenciesConfig(
                    requires={'database': SystevisorRequirementConfig(condition=SystevisorDependencyCondition.RUNNING)},
                ),
            ),
            worker=_systevisor_test_engine_unit('worker', dependencies=SystevisorDependenciesConfig(wants=('web',))),
            unrelated=_systevisor_test_engine_unit('unrelated'),
        ))
        instances = harness.engine.state.instances

        def signalled(output: ta.Any) -> ta.AbstractSet[str]:
            return {
                next(instance_id for instance_id, spawn in spawns.items() if spawn.run_id == effect.run_id)
                for effect in _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)
            }

        # Only what nothing else depends on goes first; everything else is still serving its dependents.
        output = harness.submit(SystevisorShutdownCommand())
        self.assertEqual(signalled(output), {'worker:0', 'unrelated:0'})
        self.assertEqual(instances[SystevisorInstanceId('web:0')].blocked_reason, 'worker:stopping')
        self.assertEqual(instances[SystevisorInstanceId('database:0')].blocked_reason, 'web:stopping')
        self.assertEqual(signalled(harness.exit_spawn(spawns['unrelated:0'], 0)), set())

        output = harness.exit_spawn(spawns['worker:0'], 0)
        self.assertEqual(signalled(output), {'web:0', 'web:1'})
        self.assertIsNone(instances[SystevisorInstanceId('web:0')].blocked_reason)

        # Every replica of a dependent has to be gone, and then both of its dependencies are free at once.
        self.assertEqual(signalled(harness.exit_spawn(spawns['web:1'], 0)), set())
        output = harness.exit_spawn(spawns['web:0'], 0)
        self.assertEqual(signalled(output), {'database:0', 'cache:0'})
        self.assertIsNone(instances[SystevisorInstanceId('database:0')].blocked_reason)

    def test_stopping_only_a_dependency_does_not_wait_on_dependents_that_stay_up(self) -> None:
        harness = SystevisorEngineHarness()
        spawns = self._start_all(harness, _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database'),
            web=_systevisor_test_engine_unit('web', dependencies=SystevisorDependenciesConfig(
                requires={'database': SystevisorRequirementConfig(condition=SystevisorDependencyCondition.RUNNING)},
            )),
        ))

        output = harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), False))

        self.assertEqual(
            [effect.run_id for effect in _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)],
            [spawns['database:0'].run_id],
        )
        web = harness.engine.state.instances[SystevisorInstanceId('web:0')]
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        self.assertIsNone(web.blocked_reason)

    def test_stop_ordering_loop_cannot_hang_a_shutdown(self) -> None:
        # Not reachable through validation, which the engine is not allowed to rely on to terminate.
        harness = SystevisorEngineHarness()
        self._start_all(harness, _systevisor_test_engine_snapshot(
            first=_systevisor_test_engine_unit('first'),
            second=_systevisor_test_engine_unit('second'),
            third=_systevisor_test_engine_unit('third'),
        ))
        harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            first=_systevisor_test_engine_unit('first', dependencies=SystevisorDependenciesConfig(wants=('second',))),
            second=_systevisor_test_engine_unit('second', dependencies=SystevisorDependenciesConfig(after=('first',))),
            third=_systevisor_test_engine_unit('third', dependencies=SystevisorDependenciesConfig(after=('first',))),
        )))

        output = harness.submit(SystevisorShutdownCommand())

        # The leaf goes first as usual; the two which only wait on each other go together once it has.
        self.assertEqual(len(_systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)), 1)
        third = harness.engine.state.instances[SystevisorInstanceId('third:0')]
        self.assertEqual(third.process_state, SystevisorProcessState.STOPPING)
        assert third.run_id is not None
        output = harness.submit(SystevisorProcessExitedFact(third.run_id, 0))
        self.assertEqual(len(_systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)), 2)

    def _signalled(self, spawns: ta.Mapping[str, ta.Any], output: ta.Any) -> ta.AbstractSet[str]:
        return {
            next(instance_id for instance_id, spawn in spawns.items() if spawn.run_id == effect.run_id)
            for effect in _systevisor_test_engine_effects(output, SystevisorSignalProcessEffect)
        }

    def _respawned(self, harness: SystevisorEngineHarness, spawns: ta.Dict[str, ta.Any], output: ta.Any) -> ta.Any:
        # Confirms whatever the engine just asked to have spawned, and returns the output of the last confirmation.
        for spawn in _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect):
            spawns[spawn.instance_id] = spawn
            output = self._respawned(harness, spawns, harness.succeed_spawn(spawn))
        return output

    def _following_snapshot(self, *follow: SystevisorDependencyFollow, **units: SystevisorUnitConfig) -> ta.Any:
        return _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database'),
            web=_systevisor_test_engine_unit('web', dependencies=SystevisorDependenciesConfig(requires={
                'database': SystevisorRequirementConfig(
                    condition=SystevisorDependencyCondition.RUNNING,
                    follow=follow,
                ),
            })),
            bystander=_systevisor_test_engine_unit('bystander', dependencies=SystevisorDependenciesConfig(requires={
                'database': SystevisorRequirementConfig(condition=SystevisorDependencyCondition.RUNNING),
            })),
            **units,
        )

    def test_follower_goes_down_with_a_requirement_stopped_on_purpose_and_returns_with_it(self) -> None:
        harness = SystevisorEngineHarness()
        spawns = dict(self._start_all(harness, self._following_snapshot(
            SystevisorDependencyFollow.STOP,
            frontend=_systevisor_test_engine_unit('frontend', dependencies=SystevisorDependenciesConfig(requires={
                'web': SystevisorRequirementConfig(
                    condition=SystevisorDependencyCondition.RUNNING,
                    follow=(SystevisorDependencyFollow.STOP,),
                ),
            })),
        )))
        instances = harness.engine.state.instances
        web = instances[SystevisorInstanceId('web:0')]
        frontend = instances[SystevisorInstanceId('frontend:0')]
        bystander = instances[SystevisorInstanceId('bystander:0')]
        bystander_run_id = bystander.run_id

        # The whole chain that follows is held, and stops from its far end; what merely requires it carries on.
        output = harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), False))
        self.assertEqual(self._signalled(spawns, output), {'frontend:0'})
        self.assertEqual(
            (web.desired_state, web.desired_origin, web.blocked_reason),
            (SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.FOLLOW, 'frontend:stopping'),
        )
        self.assertEqual(frontend.blocked_reason, 'web:stopped')
        self.assertEqual(self._signalled(spawns, harness.exit_spawn(spawns['frontend:0'], 0)), {'web:0'})
        self.assertEqual(web.blocked_reason, 'database:stopped')
        self.assertEqual(self._signalled(spawns, harness.exit_spawn(spawns['web:0'], 0)), {'database:0'})
        harness.exit_spawn(spawns['database:0'], 0)
        self.assertEqual(bystander.desired_state, SystevisorDesiredState.ACTIVE)
        self.assertEqual(bystander.process_state, SystevisorProcessState.RUNNING)

        # Wanting the requirement again is all it takes: the followers return to what they were configured to be.
        output = harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), True))
        self.assertEqual((web.desired_state, web.desired_origin), (
            SystevisorDesiredState.ACTIVE,
            SystevisorDesiredOrigin.CONFIG,
        ))
        self._respawned(harness, spawns, output)
        self.assertEqual(
            {instance.process_state for instance in instances.values()},
            {SystevisorProcessState.RUNNING},
        )
        self.assertIsNone(web.blocked_reason)
        self.assertEqual(bystander.run_id, bystander_run_id)

    def test_held_follower_keeps_what_the_operator_last_asked_of_it(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_engine_snapshot(
            database=_systevisor_test_engine_unit('database'),
            web=SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('web',)),
                autostart=False,
                restart=SystevisorRestartConfig(start_secs=0.),
                dependencies=SystevisorDependenciesConfig(requires={
                    'database': SystevisorRequirementConfig(
                        condition=SystevisorDependencyCondition.RUNNING,
                        follow=(SystevisorDependencyFollow.STOP,),
                    ),
                }),
            ),
        )
        spawns: ta.Dict[str, ta.Any] = {}
        self._respawned(harness, spawns, harness.submit(SystevisorApplySnapshotCommand(snapshot)))
        web = harness.engine.state.instances[SystevisorInstanceId('web:0')]
        self._respawned(harness, spawns, harness.submit(SystevisorSetInstanceDesiredCommand(web.instance_id, True)))
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)

        # Started by hand, and not by anything in the configuration: being held must not forget that.
        harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), False))
        harness.exit_spawn(spawns['web:0'], 0)
        harness.exit_spawn(spawns['database:0'], 0)
        self.assertEqual(web.desired_origin, SystevisorDesiredOrigin.FOLLOW)
        self._respawned(
            harness,
            spawns,
            harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), True)),
        )
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        self.assertEqual(web.desired_origin, SystevisorDesiredOrigin.MANUAL)

        # Stopped by hand while held, it stays stopped when the hold ends.
        harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), False))
        harness.exit_spawn(spawns['web:0'], 0)
        harness.exit_spawn(spawns['database:0'], 0)
        harness.submit(SystevisorSetInstanceDesiredCommand(web.instance_id, False))
        self._respawned(
            harness,
            spawns,
            harness.submit(SystevisorSetUnitDesiredCommand(SystevisorUnitName('database'), True)),
        )
        self.assertEqual(web.process_state, SystevisorProcessState.STOPPED)
        self.assertEqual(web.desired_origin, SystevisorDesiredOrigin.MANUAL)

    def test_follower_restarts_with_its_requirement(self) -> None:
        harness = SystevisorEngineHarness()
        spawns = dict(self._start_all(harness, self._following_snapshot(SystevisorDependencyFollow.RESTART)))
        instances = harness.engine.state.instances
        before = {instance_id: spawn.run_id for instance_id, spawn in spawns.items()}

        output = harness.submit(SystevisorRestartInstanceCommand(SystevisorInstanceId('database:0')))
        self.assertIn(SystevisorEventKind.RESTART_FOLLOWED, {event.kind for event in output.events})
        self.assertEqual(self._signalled(spawns, output), {'web:0'})
        output = harness.exit_spawn(spawns['web:0'], 0)
        self.assertEqual(self._signalled(spawns, output), {'database:0'})
        self.assertEqual(_systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect), [])
        self._respawned(harness, spawns, harness.exit_spawn(spawns['database:0'], 0))

        self.assertEqual(
            {instance.process_state for instance in instances.values()},
            {SystevisorProcessState.RUNNING},
        )
        after = {instance_id: spawn.run_id for instance_id, spawn in spawns.items()}
        self.assertNotEqual(after['database:0'], before['database:0'])
        self.assertNotEqual(after['web:0'], before['web:0'])
        self.assertEqual(after['bystander:0'], before['bystander:0'])

        # A restart-required change to the requirement's configuration is a restart like any other.
        changed = self._following_snapshot(SystevisorDependencyFollow.RESTART)
        changed = _systevisor_test_engine_snapshot(**{
            **changed.config.units,
            'database': _systevisor_test_engine_unit('database-v2'),
        })
        output = harness.submit(SystevisorApplySnapshotCommand(changed))
        self.assertEqual(self._signalled(spawns, output), {'web:0'})

    def test_rerun_of_a_completed_requirement_waits_for_its_follower_to_stop(self) -> None:
        harness = SystevisorEngineHarness()
        spawns: ta.Dict[str, ta.Any] = {}
        output = harness.submit(SystevisorApplySnapshotCommand(_systevisor_test_engine_snapshot(
            migrate=_systevisor_test_engine_unit('migrate'),
            web=_systevisor_test_engine_unit('web', dependencies=SystevisorDependenciesConfig(requires={
                'migrate': SystevisorRequirementConfig(
                    condition=SystevisorDependencyCondition.COMPLETED,
                    follow=(SystevisorDependencyFollow.RESTART,),
                ),
            })),
        )))
        self._respawned(harness, spawns, output)
        self._respawned(harness, spawns, harness.exit_spawn(spawns['migrate:0'], 0))
        migrate = harness.engine.state.instances[SystevisorInstanceId('migrate:0')]
        web = harness.engine.state.instances[SystevisorInstanceId('web:0')]
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        first_web_run_id = web.run_id

        # The requirement has nothing running to stop, so nothing would otherwise order it behind its follower.
        output = harness.submit(SystevisorRestartInstanceCommand(migrate.instance_id))
        self.assertEqual(self._signalled(spawns, output), {'web:0'})
        self.assertEqual(_systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect), [])
        self.assertEqual(migrate.blocked_reason, 'web:restarting')

        output = harness.exit_spawn(spawns['web:0'], 0)
        self.assertEqual(
            [spawn.instance_id for spawn in _systevisor_test_engine_effects(output, SystevisorSpawnProcessEffect)],
            ['migrate:0'],
        )
        self._respawned(harness, spawns, output)
        self.assertEqual(web.blocked_reason, 'migrate:completed')
        self._respawned(harness, spawns, harness.exit_spawn(spawns['migrate:0'], 0))
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        self.assertNotEqual(web.run_id, first_web_run_id)

    def test_follower_is_held_while_a_requirement_has_failed(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = self._following_snapshot(SystevisorDependencyFollow.FAILURE)
        snapshot = _systevisor_test_engine_snapshot(**{
            **snapshot.config.units,
            'database': _systevisor_test_engine_unit('database', restart_mode=SystevisorRestartMode.NEVER),
        })
        spawns = dict(self._start_all(harness, snapshot))
        instances = harness.engine.state.instances
        web = instances[SystevisorInstanceId('web:0')]
        bystander = instances[SystevisorInstanceId('bystander:0')]

        # Gone, and not coming back by itself.
        output = harness.exit_spawn(spawns['database:0'], 1)
        self.assertEqual(self._signalled(spawns, output), {'web:0'})
        self.assertEqual(
            (web.desired_state, web.desired_origin, web.blocked_reason),
            (SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.FOLLOW, 'database:failed'),
        )
        self.assertEqual(bystander.process_state, SystevisorProcessState.RUNNING)
        harness.exit_spawn(spawns['web:0'], 0)
        self.assertEqual(web.process_state, SystevisorProcessState.STOPPED)

        self._respawned(
            harness,
            spawns,
            harness.submit(SystevisorRestartInstanceCommand(SystevisorInstanceId('database:0'))),
        )
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        self.assertEqual(web.desired_origin, SystevisorDesiredOrigin.CONFIG)

    def test_requirement_that_restarts_itself_is_not_a_failure_and_is_not_followed(self) -> None:
        harness = SystevisorEngineHarness()
        spawns = dict(self._start_all(harness, self._following_snapshot(
            SystevisorDependencyFollow.STOP,
            SystevisorDependencyFollow.RESTART,
            SystevisorDependencyFollow.FAILURE,
        )))
        web = harness.engine.state.instances[SystevisorInstanceId('web:0')]

        # A crash its own restart policy recovers from is neither a stop, a restart on purpose, nor gone for good.
        output = harness.exit_spawn(spawns['database:0'], 1)
        self.assertEqual(self._signalled(spawns, output), set())
        self.assertEqual(web.process_state, SystevisorProcessState.RUNNING)
        self.assertEqual(web.desired_origin, SystevisorDesiredOrigin.CONFIG)
        self.assertFalse(web.restart_requested)

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
                    requires={
                        'migrate': SystevisorRequirementConfig(condition=SystevisorDependencyCondition.COMPLETED),
                    },
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
