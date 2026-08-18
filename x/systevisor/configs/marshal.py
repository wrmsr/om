# ruff: noqa: UP006 UP007 UP045
import enum
import typing as ta

from omcore.lite.marshal import ObjMarshalContext
from omcore.lite.marshal import ObjMarshaler
from omcore.lite.marshal import ObjMarshalerManager
from omcore.lite.marshal import new_obj_marshaler_manager

from .models import SystevisorDependencyCondition
from .models import SystevisorHealthProbeKind
from .models import SystevisorHealthRecovery
from .models import SystevisorHealthRole
from .models import SystevisorOutputMode
from .models import SystevisorRestartMode
from .models import SystevisorScheduleActionKind
from .models import SystevisorScheduleConcurrencyPolicy
from .models import SystevisorScheduleMissedPolicy
from .models import SystevisorScheduleTargetKind
from .models import SystevisorSignalScope
from .models import SystevisorStdinMode
from .models import SystevisorUnitKind


SystevisorConfigEnum = ta.TypeVar('SystevisorConfigEnum', bound=enum.Enum)


class SystevisorConfigEnumObjMarshaler(ObjMarshaler):
    def __init__(self, enum_type: ta.Type[SystevisorConfigEnum]) -> None:
        super().__init__()

        self._enum_type = enum_type

    def marshal(self, value: ta.Any, context: ObjMarshalContext) -> ta.Any:
        return value.value

    def unmarshal(self, value: ta.Any, context: ObjMarshalContext) -> ta.Any:
        if not isinstance(value, str):
            raise TypeError(value)
        try:
            return self._enum_type(value)
        except ValueError:
            try:
                return self._enum_type.__members__[value.upper()]
            except KeyError as exc:
                raise ValueError(f'invalid {self._enum_type.__name__}: {value!r}') from exc


_SYSTEVISOR_CONFIG_ENUM_TYPES = (
    SystevisorDependencyCondition,
    SystevisorHealthProbeKind,
    SystevisorHealthRecovery,
    SystevisorHealthRole,
    SystevisorOutputMode,
    SystevisorRestartMode,
    SystevisorScheduleActionKind,
    SystevisorScheduleConcurrencyPolicy,
    SystevisorScheduleMissedPolicy,
    SystevisorScheduleTargetKind,
    SystevisorSignalScope,
    SystevisorStdinMode,
    SystevisorUnitKind,
)

_SYSTEVISOR_CONFIG_OBJ_MARSHALER_MANAGER: ObjMarshalerManager = new_obj_marshaler_manager()
for _systevisor_config_marshal_enum_type in _SYSTEVISOR_CONFIG_ENUM_TYPES:
    _SYSTEVISOR_CONFIG_OBJ_MARSHALER_MANAGER.set_obj_marshaler(
        _systevisor_config_marshal_enum_type,
        SystevisorConfigEnumObjMarshaler(_systevisor_config_marshal_enum_type),
    )


def systevisor_marshal_config_obj(value: ta.Any, value_type: ta.Any = None) -> ta.Any:
    return _SYSTEVISOR_CONFIG_OBJ_MARSHALER_MANAGER.marshal_obj(value, value_type)


def systevisor_unmarshal_config_obj(value: ta.Any, value_type: ta.Type[SystevisorConfigEnum]) -> SystevisorConfigEnum:
    return _SYSTEVISOR_CONFIG_OBJ_MARSHALER_MANAGER.unmarshal_obj(value, value_type)


def systevisor_unmarshal_config(value: ta.Any, value_type: ta.Type[ta.Any]) -> ta.Any:
    return _SYSTEVISOR_CONFIG_OBJ_MARSHALER_MANAGER.unmarshal_obj(value, value_type)
