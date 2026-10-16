from omcore import marshal as msh

from ....core import fieldhash as fh
from ...permissions.types import PermissionMatchContext
from ...permissions.types import PermissionMatcher
from ...permissions.types import PermissionTarget
from ..permissions import SubagentPermissionMatcher
from ..permissions import SubagentPermissionTarget


##


def test_matcher_matches_any_profile_or_the_one_named():
    any_ = SubagentPermissionMatcher()
    explore = SubagentPermissionMatcher(profile='explore')

    assert any_.match(PermissionMatchContext(SubagentPermissionTarget('general')))
    assert any_.match(PermissionMatchContext(SubagentPermissionTarget('explore')))
    assert explore.match(PermissionMatchContext(SubagentPermissionTarget('explore')))
    assert not explore.match(PermissionMatchContext(SubagentPermissionTarget('general')))


def test_matcher_ignores_other_targets():
    from ...exec.permissions import ExecPermissionTarget  # noqa

    assert not SubagentPermissionMatcher().match(PermissionMatchContext(ExecPermissionTarget(['ls'])))


def test_marshal_is_what_the_permissions_command_takes():
    # `/permissions add allow subagent {}` and `/permissions add allow subagent {"profile": "explore"}`.
    assert msh.unmarshal({'subagent': {}}, PermissionMatcher) == SubagentPermissionMatcher()
    assert msh.unmarshal({'subagent': {'profile': 'explore'}}, PermissionMatcher) == SubagentPermissionMatcher(
        profile='explore',
    )

    assert msh.marshal(SubagentPermissionMatcher(), PermissionMatcher) == {'subagent': {}}
    assert msh.marshal(SubagentPermissionMatcher(profile='explore'), PermissionMatcher) == {
        'subagent': {'profile': 'explore'},
    }

    assert msh.unmarshal(msh.marshal(SubagentPermissionTarget('general'), PermissionTarget), PermissionTarget) == (
        SubagentPermissionTarget('general')
    )


def test_field_hashes_differ_by_profile():
    assert fh.render_field_hash(SubagentPermissionMatcher()) == '{"subagent":{"profile":null}}'
    assert fh.render_field_hash(SubagentPermissionMatcher(profile='explore')) == '{"subagent":{"profile":"explore"}}'
    assert fh.digest_field_hash(SubagentPermissionTarget('a')) != fh.digest_field_hash(SubagentPermissionTarget('b'))
