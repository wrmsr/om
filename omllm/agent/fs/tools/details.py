import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...types.tools import ToolResultDetails


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class EditToolResultDetails(ToolResultDetails, lang.Final):
    path: str

    # A unified diff of the change.
    diff: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class GlobToolResultDetails(ToolResultDetails, lang.Final):
    pattern: str

    root_path: str
    num_matches: int

    has_more: bool = False


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ReadToolResultDetails(ToolResultDetails, lang.Final):
    path: str

    line_offset: int
    num_lines: int

    has_more: bool = False


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class WriteToolResultDetails(ToolResultDetails, lang.Final):
    path: str

    num_bytes: int

    created: bool = False
