from ...tests.harness import HarnessSandboxes
from .models import build_schema
from .nodes import sqlite_node
from .scenarios import check_capture
from .scenarios import check_install
from .scenarios import check_install_triggers_only


def test_install(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        check_install(sqlite_node('a', sb), build_schema())


def test_install_triggers_only(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        check_install_triggers_only(sqlite_node('a', sb), build_schema())


def test_capture(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        check_capture(sqlite_node('a', sb), build_schema())
