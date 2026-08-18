# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import json
import typing as ta

from omcore.lite.marshal import ObjMarshalerManager
from omcore.lite.marshal import new_obj_marshaler_manager


def _systevisor_json_normalize_marshaled(value: ta.Any, marshaled: ta.Any) -> ta.Any:
    if isinstance(value, enum.Enum):
        return value.value
    if dc.is_dataclass(value) and isinstance(marshaled, dict):
        return {
            field.name: _systevisor_json_normalize_marshaled(getattr(value, field.name), marshaled[field.name])
            for field in dc.fields(value)
            if field.init and field.name in marshaled
        }
    if isinstance(value, ta.Mapping) and isinstance(marshaled, dict):
        return {
            str(marshaled_key): _systevisor_json_normalize_marshaled(item, marshaled_item)
            for (_, item), (marshaled_key, marshaled_item) in zip(value.items(), marshaled.items())
        }
    if isinstance(value, (tuple, list)) and isinstance(marshaled, list):
        return [
            _systevisor_json_normalize_marshaled(item, marshaled_item)
            for item, marshaled_item in zip(value, marshaled)
        ]
    return marshaled


class SystevisorJsonCodec:
    def __init__(self, marshaler_manager: ta.Optional[ObjMarshalerManager] = None) -> None:
        self._marshaler_manager = (
            marshaler_manager if marshaler_manager is not None else new_obj_marshaler_manager()
        )

    def to_obj(self, value: ta.Any, value_type: ta.Any = None) -> ta.Any:
        marshaled = self._marshaler_manager.marshal_obj(
            value,
            type(value) if value_type is None else value_type,
        )
        return _systevisor_json_normalize_marshaled(value, marshaled)

    def dumps(self, value: ta.Any, value_type: ta.Any = None, *, pretty: bool = False) -> bytes:
        obj = self.to_obj(value, value_type)
        if pretty:
            text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        else:
            text = json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        return text.encode('utf-8')

    def dump_line(self, value: ta.Any, value_type: ta.Any = None) -> bytes:
        return self.dumps(value, value_type) + b'\n'

    def loads(self, data: bytes) -> ta.Any:
        if not data:
            return None
        return json.loads(data.decode('utf-8'))
