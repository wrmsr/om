import uuid

from omcore import marshal as msh

from .... import llm
from ..entries import MessageSessionEntry
from ..entries import SessionEntry


def test_marshal():
    se: SessionEntry = MessageSessionEntry(
        llm.UserMessage('hi!'),
        id=(se_id := uuid.uuid7()),
    )

    mv = msh.marshal(se, SessionEntry)
    assert mv == {'message': {'id': str(se_id), 'message': {'user': {'content': 'hi!'}}}}

    se2 = msh.unmarshal(mv, SessionEntry)
    assert se2 == se
