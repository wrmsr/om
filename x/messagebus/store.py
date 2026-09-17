import abc
import json
import typing as ta
import uuid

from omcore import lang

from .sql import SqlConn
from .statements import Statements
from .types import Message
from .types import WorkerId
from .types import WorkerInfo


##


class MessageStore(lang.Abstract):
    @abc.abstractmethod
    def register_worker(self, worker_id: WorkerId, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def load_seqs(self, worker_id: WorkerId) -> ta.Mapping[WorkerId, int]:
        raise NotImplementedError

    @abc.abstractmethod
    def heartbeat(self, worker_id: WorkerId) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def list_workers(self) -> ta.Sequence[WorkerInfo]:
        raise NotImplementedError

    @abc.abstractmethod
    def insert_message(self, msg: Message) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def update_seqs(self, worker_id: WorkerId, seqs: ta.Mapping[WorkerId, int]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def select_messages(self, dst_id: WorkerId, *, limit: int) -> ta.Sequence[Message]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_message(self, msg: Message) -> None:
        raise NotImplementedError


##


def _load_json(v: ta.Any) -> ta.Any:
    # Drivers differ on whether json columns come back decoded.
    return json.loads(v) if isinstance(v, (str, bytes)) else v


def _worker_id(v: ta.Any) -> WorkerId:
    return WorkerId(v if isinstance(v, uuid.UUID) else uuid.UUID(str(v)))


class SqlMessageStore(MessageStore):
    def __init__(self, conn: SqlConn, stmts: Statements) -> None:
        super().__init__()

        self._conn = conn
        self._stmts = stmts

    def register_worker(self, worker_id: WorkerId, name: str) -> None:
        self._conn.execute(self._stmts.upsert_worker, [str(worker_id), name])

    def load_seqs(self, worker_id: WorkerId) -> ta.Mapping[WorkerId, int]:
        [[raw]] = self._conn.execute(self._stmts.select_worker_seqs, [str(worker_id)])
        return {_worker_id(k): int(v) for k, v in _load_json(raw).items()}

    def heartbeat(self, worker_id: WorkerId) -> None:
        self._conn.execute(self._stmts.update_heartbeat, [str(worker_id)])

    def list_workers(self) -> ta.Sequence[WorkerInfo]:
        return [
            WorkerInfo(_worker_id(wid), name, started_at, heartbeat_at)
            for wid, name, started_at, heartbeat_at in self._conn.execute(self._stmts.select_workers)
        ]

    def insert_message(self, msg: Message) -> None:
        self._conn.execute(
            self._stmts.insert_message,
            [str(msg.dst_id), str(msg.src_id), msg.seq, json.dumps(msg.payload)],
        )

    def update_seqs(self, worker_id: WorkerId, seqs: ta.Mapping[WorkerId, int]) -> None:
        self._conn.execute(
            self._stmts.update_seqs,
            [json.dumps({str(k): v for k, v in seqs.items()}), str(worker_id)],
        )

    def select_messages(self, dst_id: WorkerId, *, limit: int) -> ta.Sequence[Message]:
        return [
            Message(
                dst_id=dst_id,
                src_id=_worker_id(src_id),
                seq=int(seq),
                payload=_load_json(payload),
                created_at=created_at,
            )
            for src_id, seq, created_at, payload in self._conn.execute(self._stmts.select_messages, [str(dst_id), limit])
        ]

    def delete_message(self, msg: Message) -> None:
        self._conn.execute(self._stmts.delete_message, [str(msg.dst_id), str(msg.src_id), msg.seq])
