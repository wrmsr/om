# ruff: noqa: PT009 UP006 UP007 UP045
import unittest

from omcore.lite.marshal import OBJ_MARSHALER_MANAGER
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorDependenciesConfig
from x.systevisor.configs.models import SystevisorDependencyCondition
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorHealthProbeConfig
from x.systevisor.configs.models import SystevisorHealthRecovery
from x.systevisor.configs.models import SystevisorHealthRole
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorRunHealthProbeEffect
from x.systevisor.core.effects import SystevisorSignalProcessEffect
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.events import SystevisorEventKind
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.state import SystevisorEngineState
from x.systevisor.core.states import SystevisorHealthStatus
from x.systevisor.core.states import SystevisorProcessState
from x.systevisor.core.states import SystevisorSignalReason
from x.systevisor.tests.fakes import SystevisorEngineHarness


def _systevisor_test_health_unit(
        argv: str,
        *,
        health: tuple = (),
        start_secs: float = 0.,
        dependencies: SystevisorDependenciesConfig = SystevisorDependenciesConfig(),
) -> SystevisorUnitConfig:
    return SystevisorUnitConfig(
        exec=SystevisorExecConfig(argv=(argv,)),
        restart=SystevisorRestartConfig(start_secs=start_secs),
        dependencies=dependencies,
        health=health,
    )


def _systevisor_test_health_apply(
        harness: SystevisorEngineHarness,
        **units: SystevisorUnitConfig,
) -> object:
    snapshot = systevisor_build_config_snapshot(SystevisorConfig(units=units), (), ())
    return harness.submit(SystevisorApplySnapshotCommand(snapshot))


def _systevisor_test_health_effects(output: object, effect_type: object) -> list:
    return [effect for effect in output.effects if isinstance(effect, effect_type)]  # type: ignore[attr-defined,arg-type]


class TestSystevisorHealthEngine(unittest.TestCase):
    def test_startup_requires_stability_and_all_probes(self) -> None:
        harness = SystevisorEngineHarness()
        output = _systevisor_test_health_apply(
            harness,
            worker=_systevisor_test_health_unit(
                'worker',
                start_secs=2.,
                health=(SystevisorHealthProbeConfig(
                    name='boot',
                    role=SystevisorHealthRole.STARTUP,
                ),),
            ),
        )
        spawn = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.advance_to(0.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        harness.health_result(check, True)
        instance = harness.engine.state.instances[SystevisorInstanceId('worker:0')]
        self.assertEqual(instance.process_state, SystevisorProcessState.STARTING)

        harness.advance_to(2.)
        self.assertEqual(instance.process_state, SystevisorProcessState.RUNNING)
        self.assertTrue(instance.ready)

    def test_readiness_thresholds_drive_dependency_without_sleep(self) -> None:
        harness = SystevisorEngineHarness()
        output = _systevisor_test_health_apply(
            harness,
            database=_systevisor_test_health_unit(
                'database',
                health=(SystevisorHealthProbeConfig(
                    name='accepting',
                    role=SystevisorHealthRole.READINESS,
                    interval_secs=5.,
                    success_threshold=2,
                    failure_threshold=2,
                ),),
            ),
            web=_systevisor_test_health_unit(
                'web',
                dependencies=SystevisorDependenciesConfig(
                    requires={'database': SystevisorDependencyCondition.READY},
                ),
            ),
        )
        database_spawn = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(database_spawn)
        instance = harness.engine.state.instances[SystevisorInstanceId('database:0')]
        self.assertFalse(instance.ready)

        output = harness.advance_to(0.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        harness.health_result(check, True)
        self.assertFalse(instance.ready)

        output = harness.advance_to(5.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        output = harness.health_result(check, True)
        self.assertTrue(instance.ready)
        web_spawns = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)
        self.assertEqual([effect.instance_id for effect in web_spawns], [SystevisorInstanceId('web:0')])

        output = harness.advance_to(10.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        harness.health_result(check, False)
        self.assertTrue(instance.ready)
        output = harness.advance_to(15.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        output = harness.health_result(check, False)
        self.assertFalse(instance.ready)
        self.assertIn(SystevisorEventKind.READINESS_CHANGED, {event.kind for event in output.events})

    def test_liveness_recovery_requests_owned_restart(self) -> None:
        harness = SystevisorEngineHarness()
        output = _systevisor_test_health_apply(
            harness,
            worker=_systevisor_test_health_unit(
                'worker',
                health=(SystevisorHealthProbeConfig(
                    name='alive',
                    role=SystevisorHealthRole.LIVENESS,
                    interval_secs=1.,
                    failure_threshold=2,
                    recovery=SystevisorHealthRecovery.RESTART,
                ),),
            ),
        )
        spawn = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.advance_to(0.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        output = harness.health_result(check, False)
        self.assertEqual(_systevisor_test_health_effects(output, SystevisorSignalProcessEffect), [])

        output = harness.advance_to(1.)[0]
        check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]
        output = harness.health_result(check, False)
        signals = _systevisor_test_health_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].reason, SystevisorSignalReason.RESTART)

    def test_live_probe_change_rejects_old_result(self) -> None:
        harness = SystevisorEngineHarness()
        first_probe = SystevisorHealthProbeConfig(
            name='ready',
            role=SystevisorHealthRole.READINESS,
        )
        output = _systevisor_test_health_apply(
            harness,
            worker=_systevisor_test_health_unit('worker', health=(first_probe,)),
        )
        spawn = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)
        output = harness.advance_to(0.)[0]
        old_check = _systevisor_test_health_effects(output, SystevisorRunHealthProbeEffect)[0]

        _systevisor_test_health_apply(
            harness,
            worker=_systevisor_test_health_unit(
                'worker',
                health=(SystevisorHealthProbeConfig(
                    name='ready',
                    role=SystevisorHealthRole.READINESS,
                    interval_secs=20.,
                ),),
            ),
        )
        output = harness.health_result(old_check, True)

        instance = harness.engine.state.instances[SystevisorInstanceId('worker:0')]
        self.assertFalse(instance.ready)
        self.assertEqual(instance.health['ready'].status, SystevisorHealthStatus.UNKNOWN)
        self.assertEqual(output.events[-1].kind, SystevisorEventKind.STALE_FACT_IGNORED)

    def test_health_state_roundtrips_with_pending_probe(self) -> None:
        harness = SystevisorEngineHarness()
        output = _systevisor_test_health_apply(
            harness,
            worker=_systevisor_test_health_unit(
                'worker',
                health=(SystevisorHealthProbeConfig(
                    name='ready',
                    role=SystevisorHealthRole.READINESS,
                ),),
            ),
        )
        spawn = _systevisor_test_health_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)
        harness.advance_to(0.)

        restored: SystevisorEngineState = OBJ_MARSHALER_MANAGER.roundtrip_obj(
            harness.engine.state,
            SystevisorEngineState,
        )

        self.assertEqual(restored, harness.engine.state)
        self.assertIsNotNone(restored.instances[spawn.instance_id].health['ready'].in_flight_check_id)
