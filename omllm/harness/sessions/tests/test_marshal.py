from omcore import marshal as msh

from .... import llm
from ..entries import MessageSessionEntry
from ..entries import SessionEntry


def test_marshal():
    se: SessionEntry = MessageSessionEntry(
        llm.UserMessage('hi!'),
    )

    mv = msh.marshal(se, SessionEntry)
    assert mv == {'message': {'message': {'user': {'content': 'hi!'}}}}

    se2 = msh.unmarshal(mv, SessionEntry)
    assert se2 == se
