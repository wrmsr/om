import os.path

from omcore import check
from omcore import inject as inj

from ... import agent as agn
from .config import Config


##


def bind_permissions(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    permission_rules = [  # noqa
        *([
            agn.PermissionRule(
                agn.GlobFsPermissionMatcher(os.path.join(check.non_empty_str(config.cwd), '**'), ['r', 'w']),
                agn.PermissionState.ASK,
            ),
        ] if config.fs else []),

        *([
            agn.PermissionRule(
                agn.ExecPermissionMatcher(),
                agn.PermissionState.ASK,
            ),
        ] if config.exec else []),
    ]

    lst.append(inj.bind(
        agn.PermissionsManager,
        to_const=agn.StandardPermissionsManager(permission_rules),
    ))

    lst.extend([
        inj.bind(agn.StandardPermissionDecider, singleton=True),
        inj.bind(agn.PermissionDecider, to_key=agn.StandardPermissionDecider),
    ])

    return inj.as_elements(*lst)
