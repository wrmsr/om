import os.path
import uuid

from omcore import inject as inj
from omdev.home.paths import get_home_paths

from ... import harness as har
from .config import Config


##


def bind_sessions(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    session_id = uuid.uuid7()  # noqa

    state_dir_path = os.path.join(get_home_paths().state_dir, 'llm', 'sessions')
    os.makedirs(state_dir_path, exist_ok=True)

    if config.jsonl_storage:
        lst.extend([
            inj.bind(har.JsonlSessionStorage(
                file_path=os.path.join(state_dir_path, f'{session_id.hex}.jsonl'),
            )),
            inj.bind(har.SessionStorage, to_key=har.JsonlSessionStorage),
        ])

    else:
        lst.extend([
            inj.bind(har.InMemorySessionStorage()),
            inj.bind(har.SessionStorage, to_key=har.InMemorySessionStorage),
        ])

    lst.extend([
        inj.bind(har.Session, singleton=True),
    ])

    return inj.as_elements(*lst)
