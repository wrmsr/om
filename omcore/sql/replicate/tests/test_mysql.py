from ...tests.harness import HarnessSandboxes
from .models import build_schema
from .nodes import mysql_node
from .scenarios import check_capture
from .scenarios import check_capture_with_kept_columns
from .scenarios import check_install
from .scenarios import check_install_triggers_only


def test_install(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_install(mysql_node('a', sb), build_schema())


def test_install_triggers_only(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_install_triggers_only(mysql_node('a', sb), build_schema())


def test_capture(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_capture(mysql_node('a', sb), build_schema())


def test_capture_with_kept_columns(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_capture_with_kept_columns(mysql_node('a', sb), build_schema())
