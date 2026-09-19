"""
What an orm session storage must do whatever its orm is kept in, written once against an `Orm`. Driven from the top: a
scripted llm backend under a real agent under a real session, with the storage under test beneath that. Not a test
module.
"""
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import marshal as msh
from omcore import orm
from omcore.asyncs.asynclite import all as asl

from ...... import agent as agn
from ...... import llm
from ......agent.tests.scripted import scripted_backend
from ......agent.tests.scripted import text_message
from ......agent.tests.scripted import tool_call_message
from ......agent.tests.tools import EchoTool
from ......core import ui
from ......core.asyncs.asyncio import AsyncioGroupRunner
from .....commands.base import Commands
from .....commands.manager import CommandsManager
from ....entries import MessageSessionEntry
from ....session import Session
from ....types import SessionId
from ..models import OrmSession
from ..models import OrmSessionEntry
from ..storage import OrmSessionStorage
from ..types import Orm


##


async def scripted_session(
        orm_: Orm,
        *turns: ta.Any,
        tools: ta.Sequence[agn.Tool] = (),
) -> tuple[Session, agn.Agent, OrmSessionStorage]:
    agent = agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=agn.DictBackendManager({
                llm.ImmediateBackend: {None: scripted_backend(*turns)},  # type: ignore[type-abstract]
            }),
        ),
    )
    if tools:
        await agent.update_state(lambda s: dc.replace(s, context=agn.Context(tools=agn.ToolSet(list(tools)))))

    session_id = SessionId(uuid.uuid7())
    storage = OrmSessionStorage(session_id, orm_)
    session = Session(
        agent=agent,
        storage=storage,
        commands_manager=CommandsManager(commands=Commands([]), text_displayer=ui.NopTextDisplayer()),
        id=session_id,
    )

    return session, agent, storage


def transcript(agent: agn.Agent) -> list[agn.Message]:
    return list(agent.state.context.messages or [])


def marshal_messages(messages: ta.Iterable[agn.Message]) -> list[ta.Any]:
    # Compared as marshaled: what comes back from storage has been through it, and is equal to what went in up to the
    # likes of a list having become a tuple.
    return [msh.marshal(m, agn.Message) for m in messages]


async def check_stored_transcript(storage: OrmSessionStorage, agent: agn.Agent) -> None:
    entries = await storage.get_entries()
    assert all(isinstance(e, MessageSessionEntry) for e in entries)
    assert marshal_messages(e.message for e in entries) == marshal_messages(transcript(agent))  # type: ignore[attr-defined]  # noqa


##


async def check_orm_session_storage(orm_: Orm) -> None:
    echo = EchoTool()
    session, agent, storage = await scripted_session(
        orm_,
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'x'})),
        text_message('ok'),
        text_message('ok again'),
        RuntimeError('boom'),
        tools=[echo.tool()],
    )

    # Nothing is there for a session until something is stored for it.
    async with orm_.new_session():
        assert await orm.get(OrmSession, session.id.v) is None

    await session.prompt('hi')
    assert echo.calls == ['x']
    assert [type(m) for m in transcript(agent)] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.AiMessage,
    ]
    await check_stored_transcript(storage, agent)

    # A later run adds to what is there, and one which fails is stored as far as it got.
    await session.prompt('again')
    await session.prompt('and again')
    assert isinstance(transcript(agent)[-1], agn.InfoAgentMessage)
    await check_stored_transcript(storage, agent)

    # The rows are what they claim to be: a dense 1-based seq, counted on the session, each keyed by its entry's id.
    entries = await storage.get_entries()
    async with orm_.new_session():
        orm_session = await orm.get(OrmSession, session.id.v)
        assert orm_session is not None
        assert orm_session.num_entries == len(entries) == 8
        assert orm_session.created_at is not None

        orm_entries = await orm.query(orm.Query(
            OrmSessionEntry,
            orm.Where(
                orm.WhereItem.of('session', '=', orm.ref(orm_session)),
                orm.WhereItem.of('seq', '>=', 1),
            ),
            order_by=[orm.OrderByItem('seq', 'asc')],
        ))
        assert [oe.seq for oe in orm_entries] == list(range(1, len(entries) + 1))
        assert [oe.id.k for oe in orm_entries] == [e.id for e in entries]

    # Another session in the same orm keeps to itself.
    other_session, other_agent, other_storage = await scripted_session(orm_, text_message('hello'))
    await other_session.prompt('hi')
    await check_stored_transcript(other_storage, other_agent)
    assert len(await other_storage.get_entries()) == 2
    await check_stored_transcript(storage, agent)
