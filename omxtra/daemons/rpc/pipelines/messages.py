"""
The daemons protocol's response records: what the replay registry keeps and the dispatchers produce, kept apart from
the wire envelopes so a stored answer is independent of how it travels.
"""
import typing as ta

from omcore import dataclasses as dc

from ..protocol import RpcRequest


##


@dc.dataclass(frozen=True, kw_only=True)
class RpcWireRequest:
    request: RpcRequest


@dc.dataclass(frozen=True, kw_only=True)
class RpcWireResult:
    client_id: str
    request_id: str
    result: ta.Any


@dc.dataclass(frozen=True, kw_only=True)
class RpcWireError:
    client_id: str
    request_id: str
    code: str
    remote_type: str
    message: str


RpcWireResponse: ta.TypeAlias = ta.Union[  # noqa: UP007
    RpcWireResult,
    RpcWireError,
]
