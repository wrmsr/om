from omcore import inject as inj

from .... import agent as agn
from ...types import TargetCwd
from ..config import AgentConfig


##


def _provide_permissions_manager(config: AgentConfig, cwd: TargetCwd) -> agn.StandardPermissionsManager:
    permission_rules: list[agn.PermissionRule] = []

    return agn.StandardPermissionsManager(permission_rules)


def bind_permissions(config: AgentConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(agn.StandardPermissionsManager, singleton=True, to_fn=_provide_permissions_manager),
        inj.bind(agn.PermissionsManager, to_key=agn.StandardPermissionsManager),

        inj.bind(agn.StandardPermissionDecider, singleton=True),
        inj.bind(agn.PermissionDecider, to_key=agn.StandardPermissionDecider),
    ])

    return inj.as_elements(*lst)
