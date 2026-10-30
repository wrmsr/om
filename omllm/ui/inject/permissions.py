from omcore import inject as inj

from ... import agent as agn
from ..config import UiConfig
from ..types import TargetCwd


##


def _provide_permissions_manager(config: UiConfig, cwd: TargetCwd) -> agn.StandardPermissionsManager:
    permission_rules: list[agn.PermissionRule] = []

    return agn.StandardPermissionsManager(permission_rules)


def bind_permissions(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(agn.StandardPermissionsManager, singleton=True, to_fn=_provide_permissions_manager),
        inj.bind(agn.PermissionsManager, to_key=agn.StandardPermissionsManager),

        inj.bind(agn.StandardPermissionDecider, singleton=True),
        inj.bind(agn.PermissionDecider, to_key=agn.StandardPermissionDecider),
    ])

    return inj.as_elements(*lst)
