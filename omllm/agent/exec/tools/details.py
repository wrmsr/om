import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...types.tools import ToolResultDetails


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ExecToolResultDetails(ToolResultDetails, lang.Final):
    rc: int

    stdout: str
    stderr: str

    timed_out: bool = False
    truncated: bool = False
