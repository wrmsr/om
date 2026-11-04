"""The serde adapter over the standard `omcore.marshal`, for standard code. Not lite."""
import typing as ta

from .. import marshal as msh
from .serde import RpcSerde


##


class MarshalRpcSerde(RpcSerde):
    """Over `omcore.marshal`: the global marshaling by default, or a given one."""

    def __init__(self, marshaling: msh.Marshaling | None = None) -> None:
        super().__init__()

        self._marshaling = marshaling

    def _get_marshaling(self) -> msh.Marshaling:
        if (m := self._marshaling) is not None:
            return m
        return msh.global_marshaling()

    def marshal(self, obj: ta.Any, ty: ta.Any = None) -> ta.Any:
        return self._get_marshaling().marshal(obj, ty)

    def unmarshal(self, value: ta.Any, ty: ta.Any) -> ta.Any:
        return self._get_marshaling().unmarshal(value, ty)
