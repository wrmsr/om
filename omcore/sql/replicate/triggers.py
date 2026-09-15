import enum
import typing as ta

from ... import dataclasses as dc
from ... import lang
from ..qualifiedname import QualifiedName
from ..tabledefs.elements import Trigger
from .names import capture_trigger_prefix


##


CAPTURE_TRIGGER_VERSION: ta.Final[int] = 1


class CaptureEvent(enum.Enum):
    INSERT = 'insert'
    UPDATE = 'update'
    DELETE = 'delete'


@dc.dataclass(frozen=True)
class CaptureTrigger(Trigger, lang.Final):
    """
    The row trigger that keeps a table's shadow current: on any change it bumps the row's version, stamps the local node
    as origin, and records whether the row is gone. The body version is part of the name, so changing the body is a bump
    here and the differ does the rest.
    """

    event: CaptureEvent

    _: dc.KW_ONLY

    version: int = CAPTURE_TRIGGER_VERSION
    log: bool = False  # also append the change to the node's log; part of the name, since it changes the body

    @classmethod
    def trigger_name_prefix(cls, table_name: QualifiedName) -> str:
        return capture_trigger_prefix(table_name)

    def trigger_name_suffix(self) -> str:
        return f'{self.event.value}_v{self.version}' + ('_log' if self.log else '')


def capture_triggers(
        version: int = CAPTURE_TRIGGER_VERSION,
        *,
        log: bool = False,
) -> list[CaptureTrigger]:
    return [CaptureTrigger(e, version=version, log=log) for e in CaptureEvent]
