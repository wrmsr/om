"""
The trigger-rendering plugin seam. A backend's ddl `Renderer` knows nothing of any concrete trigger type's SQL: it
dispatches by trigger type to a registered `TriggerRenderer`, which is where the dialect-specific create and drop
statements live. Backends register renderers for the built-in trigger types; any other package registers renderers for
its own trigger types when it constructs the backend renderer. A drop is rendered from the trigger's name alone (that
is all reflection yields), so a plugin must be able to find every object it created from that name.
"""
import abc
import typing as ta

from ... import lang
from ..qualifiedname import QualifiedName
from .elements import Trigger
from .tabledefs import TableDef


if ta.TYPE_CHECKING:
    from .rendering import Renderer


TriggerT = ta.TypeVar('TriggerT', bound=Trigger)


##


class TriggerRenderer(lang.Abstract, ta.Generic[TriggerT]):
    @property
    @abc.abstractmethod
    def trigger_cls(self) -> type[TriggerT]:
        raise NotImplementedError

    @abc.abstractmethod
    def create_statements(
            self,
            r: Renderer,
            tbl: TableDef,
            t: TriggerT,
            opts: Renderer.CreateOptions,
    ) -> list[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def drop_statements(
            self,
            r: Renderer,
            table_name: QualifiedName,
            name: str,
    ) -> list[str]:
        raise NotImplementedError
