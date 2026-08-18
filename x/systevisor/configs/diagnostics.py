# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta


class SystevisorConfigDiagnosticSeverity(enum.Enum):
    ERROR = 'error'
    WARNING = 'warning'


class SystevisorConfigDiagnosticStage(enum.Enum):
    DISCOVERY = 'discovery'
    PARSE = 'parse'
    MERGE = 'merge'
    UNMARSHAL = 'unmarshal'
    VALIDATE = 'validate'


@dc.dataclass(frozen=True)
class SystevisorConfigDiagnostic:
    severity: SystevisorConfigDiagnosticSeverity
    stage: SystevisorConfigDiagnosticStage
    code: str
    message: str
    source: ta.Optional[str] = None
    object_path: ta.Sequence[str] = ()


class SystevisorConfigCompileError(Exception):
    pass
