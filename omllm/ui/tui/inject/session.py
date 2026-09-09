import os.path
import uuid

from omcore import inject as inj
from omdev.home.paths import get_home_paths

from .... import harness as har
from ..config import Config


##


def bind_sessions(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    session_id = har.SessionId(uuid.uuid7())

    lst.extend([
        inj.bind(session_id),

        inj.bind(har.Session, singleton=True),
    ])

    #

    state_dir_path = os.path.join(get_home_paths().state_dir, 'llm', 'sessions')

    if config.jsonl_storage:
        lst.extend([
            inj.bind(har.JsonlSessionStorage(
                file_path=os.path.join(state_dir_path, f'{session_id.v!s}.jsonl'),
            )),
            inj.bind(har.SessionStorage, to_key=har.JsonlSessionStorage),
        ])

    else:
        lst.extend([
            inj.bind(har.InMemorySessionStorage()),
            inj.bind(har.SessionStorage, to_key=har.InMemorySessionStorage),
        ])

    #

    return inj.as_elements(*lst)
