import typing as ta
import uuid

from .... import dataclasses as dc
from ..protocol import RpcRequest


##


@dc.dataclass(frozen=True)
class RpcFrame:
    data: bytes


##


@dc.dataclass(frozen=True, kw_only=True)
class RpcClientHello:
    version: int


@dc.dataclass(frozen=True, kw_only=True)
class RpcServerHello:
    version: int
    instance_id: uuid.UUID


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


RpcWireResponse: ta.TypeAlias = RpcWireResult | RpcWireError
RpcWireMessage: ta.TypeAlias = RpcClientHello | RpcServerHello | RpcWireRequest | RpcWireResponse


##


@dc.dataclass(frozen=True, kw_only=True)
class RpcClientConnected:
    instance_id: uuid.UUID


@dc.dataclass(frozen=True, kw_only=True)
class RpcClientSendRequest:
    request: RpcRequest


@dc.dataclass(frozen=True, kw_only=True)
class RpcClientRequestSent:
    request: RpcRequest


@dc.dataclass(frozen=True, kw_only=True)
class RpcClientResponse:
    response: RpcWireResponse


@dc.dataclass(frozen=True, kw_only=True)
class RpcPipelineFailure:
    exc: BaseException


@dc.dataclass(frozen=True, kw_only=True)
class RpcServerDispatch:
    request: RpcRequest


@dc.dataclass(frozen=True, kw_only=True)
class RpcServerSendResponse:
    response: RpcWireResponse
