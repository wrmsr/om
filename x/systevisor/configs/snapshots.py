# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import hashlib
import json
import typing as ta

from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorUnitName
from ..core.identities import systevisor_make_instance_id
from .marshal import systevisor_marshal_config_obj
from .models import SystevisorConfig
from .models import SystevisorUnitConfig
from .sources import SystevisorConfigProvenance


_SYSTEVISOR_CONFIG_SNAPSHOT_SCHEMA_VERSION = 1


@dc.dataclass(frozen=True)
class SystevisorDesiredInstanceSpec:
    instance_id: SystevisorInstanceId
    unit_name: SystevisorUnitName
    slot: int
    spec_digest: str
    unit: SystevisorUnitConfig


@dc.dataclass(frozen=True)
class SystevisorConfigSnapshot:
    snapshot_schema_version: int
    digest: str
    config: SystevisorConfig
    instances: ta.Mapping[SystevisorInstanceId, SystevisorDesiredInstanceSpec]
    source_paths: ta.Sequence[str]
    provenance: ta.Sequence[SystevisorConfigProvenance]


def systevisor_digest_config_object(value: ta.Any, value_type: ta.Any = None) -> str:
    marshaled = systevisor_marshal_config_obj(value, value_type)
    encoded = json.dumps(marshaled, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def systevisor_build_config_snapshot(
        config: SystevisorConfig,
        source_paths: ta.Sequence[str],
        provenance: ta.Sequence[SystevisorConfigProvenance],
) -> SystevisorConfigSnapshot:
    instances: ta.Dict[SystevisorInstanceId, SystevisorDesiredInstanceSpec] = {}
    for unit_name, unit in sorted(config.units.items()):
        spec_digest = systevisor_digest_config_object(unit, SystevisorUnitConfig)
        for slot in range(unit.replica_start, unit.replica_start + unit.replicas):
            instance_id = systevisor_make_instance_id(unit_name, slot)
            instances[instance_id] = SystevisorDesiredInstanceSpec(
                instance_id=instance_id,
                unit_name=SystevisorUnitName(unit_name),
                slot=slot,
                spec_digest=spec_digest,
                unit=unit,
            )

    return SystevisorConfigSnapshot(
        snapshot_schema_version=_SYSTEVISOR_CONFIG_SNAPSHOT_SCHEMA_VERSION,
        digest=systevisor_digest_config_object(config, SystevisorConfig),
        config=config,
        instances=instances,
        source_paths=tuple(source_paths),
        provenance=tuple(provenance),
    )
