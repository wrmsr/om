from ...tests.harness import HarnessSandboxes
from .models import build_schema
from .nodes import mysql_node
from .scenarios import check_capture
from .scenarios import check_install


def test_install(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_install(mysql_node('a', sb), build_schema())


def test_capture(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        check_capture(mysql_node('a', sb), build_schema())
