import datetime
import typing as ta
import uuid

from omcore import dataclasses as dc


WorkerId = ta.NewType('WorkerId', uuid.UUID)

# Anything json-serializable. The bus never looks inside it - the rpc layer owns the shape.
Payload: ta.TypeAlias = ta.Any


##


@dc.dataclass(frozen=True)
class OutgoingMessage:
    dst_id: WorkerId
    payload: Payload


@dc.dataclass(frozen=True)
class Message:
    dst_id: WorkerId
    src_id: WorkerId
    seq: int
    payload: Payload

    # Server-assigned on insert; only populated on messages read back out of the store.
    created_at: datetime.datetime | None = None


@dc.dataclass(frozen=True)
class WorkerInfo:
    worker_id: WorkerId
    name: str
    started_at: datetime.datetime
    heartbeat_at: datetime.datetime


def new_worker_id() -> WorkerId:
    return WorkerId(uuid.uuid7())
