import re
import typing as ta


SystevisorUnitName = ta.NewType('SystevisorUnitName', str)
SystevisorCollectionName = ta.NewType('SystevisorCollectionName', str)
SystevisorInstanceId = ta.NewType('SystevisorInstanceId', str)
SystevisorRunId = ta.NewType('SystevisorRunId', int)
SystevisorHealthCheckId = ta.NewType('SystevisorHealthCheckId', int)


_SYSTEVISOR_IDENTITIES_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


def systevisor_is_valid_name(value: str) -> bool:
    return bool(_SYSTEVISOR_IDENTITIES_NAME_RE.fullmatch(value))


def systevisor_make_instance_id(unit_name: str, slot: int) -> SystevisorInstanceId:
    if not systevisor_is_valid_name(unit_name):
        raise ValueError(unit_name)
    if slot < 0:
        raise ValueError(slot)
    return SystevisorInstanceId(f'{unit_name}:{slot}')
