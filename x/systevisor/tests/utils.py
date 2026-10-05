# ruff: noqa: PTH100 PTH118 PTH123 UP033 UP036
import functools
import os.path
import shutil
import sys

from omcore.lite.check import check


_SYSTEVISOR_TEST_UTILS_ROOT = os.path.dirname(os.path.dirname(__file__))
_SYSTEVISOR_TEST_UTILS_REPO_ROOT = os.path.abspath(os.path.join(_SYSTEVISOR_TEST_UTILS_ROOT, '..', '..'))

SYSTEVISOR_TEST_ARTIFACT_MAIN = os.path.join(_SYSTEVISOR_TEST_UTILS_ROOT, '__main__.py')
SYSTEVISOR_TEST_ARTIFACT_PATH = os.path.join(_SYSTEVISOR_TEST_UTILS_ROOT, '_bin', 'systevisor.py')


def true_bin() -> str:
    return check.not_none(shutil.which('true'))


@functools.lru_cache(maxsize=None)
def systevisor_test_artifact_source() -> str:
    """
    The single-file artifact for the source tree as it stands: generated afresh where the development amalgamator can
    run, so a test of the artifact is never a test of a stale one, and read from the checked-in copy elsewhere.
    """

    if sys.version_info >= (3, 9):
        from omdev.amalg.gen.gen import AmalgGenerator

        return AmalgGenerator(
            SYSTEVISOR_TEST_ARTIFACT_MAIN,
            mounts={'omcore': os.path.join(_SYSTEVISOR_TEST_UTILS_REPO_ROOT, 'omcore')},
            output_dir=os.path.dirname(SYSTEVISOR_TEST_ARTIFACT_PATH),
        ).gen_amalg()
    else:
        with open(SYSTEVISOR_TEST_ARTIFACT_PATH) as artifact_file:
            return artifact_file.read()
