# ruff: noqa: UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import typing as ta

from .ops import EnvironmentInfo
from .ops import EnvironmentOps


##


class StaticEnvironmentOps(EnvironmentOps):
    """An environment which says what it was given, for tests, demos, and anywhere nothing is to be looked at."""

    def __init__(self, info: EnvironmentInfo) -> None:
        super().__init__()

        self._info = info

    async def get_info(self, *, cwd: ta.Optional[str] = None) -> EnvironmentInfo:
        # Nothing to resolve against: a directory asked for is the one reported, as given.
        if cwd is None:
            return self._info

        return dc.replace(self._info, cwd=cwd)
