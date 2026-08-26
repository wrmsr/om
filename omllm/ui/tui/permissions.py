import os.path

from omcore import check
from omcore import inject as inj

from ... import agent as agn
from .config import Config


##


def bind_permissions(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    permission_rules: list[agn.PermissionRule] = []

    if config.eval:
        permission_rules.extend([
            agn.PermissionRule(
                agn.EvalPermissionMatcher(),
                agn.PermissionState.ASK,
            ),
        ])

    if config.allow_ripgrep_execs:
        permission_rules.append(
            agn.PermissionRule(
                agn.ToolPermissionMatcher(
                    tool='ripgrep',
                    child=agn.ExecPermissionMatcher(),
                ),
                agn.PermissionState.ALLOW,
            ),
        )

    if config.exec:
        permission_rules.extend([
            agn.PermissionRule(
                agn.ExecPermissionMatcher(),
                agn.PermissionState.ASK,
            ),
        ])

    if config.fs:
        if config.allow_fs_reads:
            permission_rules.extend([
                agn.PermissionRule(
                    agn.GlobFsPermissionMatcher(os.path.join(check.non_empty_str(config.cwd), '**'), ['r']),
                    agn.PermissionState.ALLOW,
                ),
                agn.PermissionRule(
                    agn.GlobFsPermissionMatcher(os.path.join(check.non_empty_str(config.cwd), '**'), ['w']),
                    agn.PermissionState.ASK,
                ),
            ])
        else:
            permission_rules.extend([
                agn.PermissionRule(
                    agn.GlobFsPermissionMatcher(os.path.join(check.non_empty_str(config.cwd), '**'), ['r', 'w']),
                    agn.PermissionState.ASK,
                ),
            ])

    lst.append(inj.bind(
        agn.PermissionsManager,
        to_const=agn.StandardPermissionsManager(permission_rules),
    ))

    lst.extend([
        inj.bind(agn.StandardPermissionDecider, singleton=True),
        inj.bind(agn.PermissionDecider, to_key=agn.StandardPermissionDecider),
    ])

    return inj.as_elements(*lst)
