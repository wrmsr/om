# ruff: noqa: PT009 UP006 UP007 UP045
import unittest

from omcore.lite.marshal import OBJ_MARSHALER_MANAGER
from x.systevisor.configs.models import SystevisorCollectionConfig
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorDependenciesConfig
from x.systevisor.configs.models import SystevisorDependencyCondition
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorRestartMode
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.models import SystevisorUnitKind
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorSignalProcessEffect
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.engine import SystevisorEngine
from x.systevisor.core.identities import SystevisorCollectionName
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.inputs import SystevisorSetCollectionDesiredCommand
from x.systevisor.core.inputs import SystevisorSetUnitDesiredCommand
from x.systevisor.core.state import SystevisorEngineState
from x.systevisor.core.states import SystevisorCollectionStatus
from x.systevisor.core.states import SystevisorDesiredOrigin
from x.systevisor.core.states import SystevisorDesiredState
from x.systevisor.tests.fakes import SystevisorEngineHarness


def _systevisor_test_collection_unit(
        name: str,
        *,
        autostart: bool = False,
        restart_mode: SystevisorRestartMode = SystevisorRestartMode.NEVER,
) -> SystevisorUnitConfig:
    return SystevisorUnitConfig(
        exec=SystevisorExecConfig(argv=(name,)),
        autostart=autostart,
        restart=SystevisorRestartConfig(mode=restart_mode, start_secs=0.),
    )


def _systevisor_test_collection_snapshot(
        units: dict,
        collections: dict,
) -> object:
    return systevisor_build_config_snapshot(
        SystevisorConfig(units=units, collections=collections),
        (),
        (),
    )


def _systevisor_test_collection_effects(output: object, effect_type: object) -> list:
    return [effect for effect in output.effects if isinstance(effect, effect_type)]  # type: ignore[attr-defined,arg-type]


class TestSystevisorCollections(unittest.TestCase):
    def test_autostart_collection_claim_reaches_ready(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {'web': _systevisor_test_collection_unit('web')},
            {'stack': SystevisorCollectionConfig(units=('web',), autostart=True)},
        )

        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        collection = harness.engine.state.collections[SystevisorCollectionName('stack')]
        self.assertEqual(collection.status, SystevisorCollectionStatus.STARTING)
        self.assertEqual(
            harness.engine.state.instances[spawn.instance_id].desired_origin,
            SystevisorDesiredOrigin.COLLECTION,
        )

        harness.succeed_spawn(spawn)
        self.assertEqual(collection.status, SystevisorCollectionStatus.READY)

    def test_manual_stop_is_a_collection_veto_and_can_be_restarted(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {'web': _systevisor_test_collection_unit('web', autostart=True)},
            {'stack': SystevisorCollectionConfig(units=('web',))},
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(spawn)

        output = harness.submit(SystevisorSetCollectionDesiredCommand(
            SystevisorCollectionName('stack'),
            False,
        ))
        self.assertEqual(len(_systevisor_test_collection_effects(output, SystevisorSignalProcessEffect)), 1)
        instance = harness.engine.state.instances[spawn.instance_id]
        self.assertEqual(instance.desired_state, SystevisorDesiredState.INACTIVE)
        collection = harness.engine.state.collections[SystevisorCollectionName('stack')]
        self.assertEqual(collection.status, SystevisorCollectionStatus.STOPPING)

        harness.exit_spawn(spawn, 0)
        self.assertEqual(collection.status, SystevisorCollectionStatus.INACTIVE)
        output = harness.submit(SystevisorSetCollectionDesiredCommand(
            SystevisorCollectionName('stack'),
            True,
        ))
        self.assertEqual(len(_systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)), 1)

    def test_stop_together_latches_failure_and_stops_peers(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {
                'database': _systevisor_test_collection_unit('database'),
                'web': _systevisor_test_collection_unit('web'),
            },
            {'stack': SystevisorCollectionConfig(
                units=('database', 'web'),
                autostart=True,
                stop_together=True,
            )},
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        spawns = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)
        for spawn in spawns:
            harness.succeed_spawn(spawn)
        failed_spawn = next(spawn for spawn in spawns if spawn.instance_id == SystevisorInstanceId('database:0'))

        output = harness.exit_spawn(failed_spawn, 1)

        collection = harness.engine.state.collections[SystevisorCollectionName('stack')]
        self.assertEqual(collection.status, SystevisorCollectionStatus.FAILED)
        self.assertEqual(collection.failure_instance_id, SystevisorInstanceId('database:0'))
        self.assertFalse(collection.desired_active)
        signals = _systevisor_test_collection_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual([signal.run_id for signal in signals], [
            next(spawn.run_id for spawn in spawns if spawn.instance_id == SystevisorInstanceId('web:0')),
        ])
        self.assertTrue(all(
            instance.desired_state is SystevisorDesiredState.INACTIVE
            for instance in harness.engine.state.instances.values()
        ))

    def test_collection_without_stop_together_becomes_degraded(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {
                'database': _systevisor_test_collection_unit('database'),
                'web': _systevisor_test_collection_unit('web'),
            },
            {'stack': SystevisorCollectionConfig(
                units=('database', 'web'),
                autostart=True,
                stop_together=False,
            )},
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        spawns = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)
        for spawn in spawns:
            harness.succeed_spawn(spawn)
        failed_spawn = next(spawn for spawn in spawns if spawn.instance_id == SystevisorInstanceId('database:0'))

        output = harness.exit_spawn(failed_spawn, 1)

        collection = harness.engine.state.collections[SystevisorCollectionName('stack')]
        self.assertEqual(collection.status, SystevisorCollectionStatus.DEGRADED)
        self.assertTrue(collection.desired_active)
        self.assertEqual(_systevisor_test_collection_effects(output, SystevisorSignalProcessEffect), [])

    def test_startup_collection_suppresses_unselected_autostart(self) -> None:
        state = SystevisorEngineState(startup_collection=SystevisorCollectionName('selected'))
        harness = SystevisorEngineHarness(SystevisorEngine(state))
        snapshot = _systevisor_test_collection_snapshot(
            {
                'selected': _systevisor_test_collection_unit('selected'),
                'unrelated': _systevisor_test_collection_unit('unrelated', autostart=True),
            },
            {
                'selected': SystevisorCollectionConfig(units=('selected',)),
                'other': SystevisorCollectionConfig(units=('unrelated',), autostart=True),
            },
        )

        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]

        spawns = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)
        self.assertEqual([spawn.instance_id for spawn in spawns], [SystevisorInstanceId('selected:0')])
        self.assertTrue(harness.engine.state.collections[SystevisorCollectionName('selected')].desired_active)
        self.assertFalse(harness.engine.state.collections[SystevisorCollectionName('other')].desired_active)

    def test_explicit_unit_start_overrides_a_collection_stop_veto(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {'web': _systevisor_test_collection_unit('web')},
            {'stack': SystevisorCollectionConfig(units=('web',))},
        )
        harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        harness.submit(SystevisorSetCollectionDesiredCommand(SystevisorCollectionName('stack'), False))

        output = harness.submit(SystevisorSetUnitDesiredCommand('web', True))  # type: ignore[arg-type]

        self.assertEqual(len(_systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)), 1)

    def test_collection_stop_releases_transitive_dependency_claims(self) -> None:
        harness = SystevisorEngineHarness()
        database = _systevisor_test_collection_unit('database')
        web = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('web',)),
            autostart=False,
            restart=SystevisorRestartConfig(mode=SystevisorRestartMode.NEVER, start_secs=0.),
            dependencies=SystevisorDependenciesConfig(
                requires={'database': SystevisorDependencyCondition.RUNNING},
            ),
        )
        snapshot = _systevisor_test_collection_snapshot(
            {'database': database, 'web': web},
            {'stack': SystevisorCollectionConfig(units=('web',), autostart=True)},
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        database_spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        output = harness.succeed_spawn(database_spawn)
        web_spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(web_spawn)

        output = harness.submit(SystevisorSetCollectionDesiredCommand(
            SystevisorCollectionName('stack'),
            False,
        ))

        signals = _systevisor_test_collection_effects(output, SystevisorSignalProcessEffect)
        self.assertEqual({signal.run_id for signal in signals}, {database_spawn.run_id, web_spawn.run_id})
        self.assertEqual(
            harness.engine.state.instances[database_spawn.instance_id].desired_state,
            SystevisorDesiredState.INACTIVE,
        )

    def test_collection_state_roundtrips(self) -> None:
        harness = SystevisorEngineHarness()
        snapshot = _systevisor_test_collection_snapshot(
            {'web': _systevisor_test_collection_unit('web')},
            {'stack': SystevisorCollectionConfig(units=('web',), autostart=True)},
        )
        harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]

        restored: SystevisorEngineState = OBJ_MARSHALER_MANAGER.roundtrip_obj(
            harness.engine.state,
            SystevisorEngineState,
        )

        self.assertEqual(restored, harness.engine.state)

    def test_reactivating_collection_reruns_completed_oneshot(self) -> None:
        harness = SystevisorEngineHarness()
        oneshot = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('migrate',)),
            kind=SystevisorUnitKind.ONESHOT,
            autostart=False,
            restart=SystevisorRestartConfig(mode=SystevisorRestartMode.NEVER, start_secs=0.),
        )
        snapshot = _systevisor_test_collection_snapshot(
            {'migrate': oneshot},
            {'stack': SystevisorCollectionConfig(units=('migrate',), autostart=True)},
        )
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))  # type: ignore[arg-type]
        first_spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        harness.succeed_spawn(first_spawn)
        harness.exit_spawn(first_spawn, 0)
        harness.submit(SystevisorSetCollectionDesiredCommand(SystevisorCollectionName('stack'), False))

        output = harness.submit(SystevisorSetCollectionDesiredCommand(SystevisorCollectionName('stack'), True))

        second_spawn = _systevisor_test_collection_effects(output, SystevisorSpawnProcessEffect)[0]
        self.assertNotEqual(first_spawn.run_id, second_spawn.run_id)
