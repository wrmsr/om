import os.path

from omcore import lang

from ... import agent as agn
from ...core import ui
from ..commands.base import Commands
from ..commands.manager import CommandsManager
from ..commands.permissions import PermissionsCommand
from ..commands.simple import EchoCommand
from ..config import UiConfig
from ..yolo import yolo_autoexec


##


# Every one a directory a user may be in, and each something to one of the layers its name passes through on its way
# into a rule: the command line, the json, the glob.
_AWKWARD_CWDS = [
    '/w/plain',
    '/w/a b',
    "/w/it's",
    '/w/say "hi"',
    '/w/back\\slash',
    '/w/a[b]',
    '/w/a*b',
    '/w/a?b',
    '/',
]


def _run_autoexec(config, cwd):
    """The rules the config's autoexec leaves behind, each line run as the frontends run them."""

    permissions = agn.StandardPermissionsManager()

    commands = CommandsManager(
        commands=Commands([PermissionsCommand(permissions), EchoCommand()]),
        text_displayer=ui.NopTextDisplayer(),
    )

    for line in yolo_autoexec(config, cwd):
        assert line.startswith('/')
        lang.sync_await(commands.parse(line[1:]).run())

    return permissions


def _fs_state(permissions, path, mode):
    rule = permissions.match(agn.PermissionMatchContext(agn.FsPermissionTarget(path, mode)))
    return rule.result if rule is not None else None


def _paths_within(cwd):
    return [cwd, os.path.join(cwd, 'a.py'), os.path.join(cwd, 'a', 'b.py')]


##


def test_yolo_grants_the_working_directory_whatever_it_is_named():
    for cwd in _AWKWARD_CWDS:
        permissions = _run_autoexec(UiConfig(yolo=True), cwd)

        for path in _paths_within(cwd):
            for mode in ('r', 'w'):
                assert _fs_state(permissions, path, mode) is agn.PermissionState.ALLOW, (cwd, path, mode)


def test_diet_yolo_reads_the_working_directory_and_asks_to_write_it():
    for cwd in _AWKWARD_CWDS:
        permissions = _run_autoexec(UiConfig(diet_yolo=True), cwd)

        for path in _paths_within(cwd):
            assert _fs_state(permissions, path, 'r') is agn.PermissionState.ALLOW, (cwd, path)
            assert _fs_state(permissions, path, 'w') is agn.PermissionState.ASK, (cwd, path)


def test_yolo_grants_nothing_beside_the_working_directory():
    # A directory's name is not a pattern: one which reads as a glob still names only itself.
    for cwd, sibling in [
        ('/w/plain', '/w/plainer'),
        ('/w/a*b', '/w/aXb'),
        ('/w/a?b', '/w/aXb'),
        ('/w/a[b]', '/w/ab'),
    ]:
        for config in [UiConfig(yolo=True), UiConfig(diet_yolo=True)]:
            permissions = _run_autoexec(config, cwd)

            for mode in ('r', 'w'):
                assert _fs_state(permissions, os.path.join(sibling, 'a.py'), mode) is None, (cwd, sibling, mode)
