import io
import os.path
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import marshal as msh
from omcore.formats.json import all as json

from ..entries import SessionEntry
from .types import SessionStorage


##


class FsSessionStorage(SessionStorage):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        dir_path: str

    def __init__(
            self,
            config: Config,
    ) -> None:
        super().__init__()

        self._config = config

        self._dir_path = check.non_empty_str(config.dir_path)

        self._entries_file_path = os.path.join(self._dir_path, self.ENTRIES_FILE_NAME)

    ENTRIES_FILE_NAME: ta.Final = 'entries.jsonl'

    #

    _is_initialized = False

    async def __aenter__(self) -> ta.Self:
        await super().__aenter__()

        if not os.path.exists(self._dir_path):
            os.makedirs(self._dir_path, exist_ok=True)

        self._is_initialized = True

        return self

    async def add_entry(self, *entries: SessionEntry) -> None:
        check.state(self._is_initialized)

        if not entries:
            return

        #

        mvs = [  # noqa
            msh.marshal(e, SessionEntry)
            for e in entries
        ]

        out = io.StringIO()
        for mv in mvs:
            out.write(json.dumps_compact(mv))
            out.write('\n')

        #

        with open(self._entries_file_path, 'a') as f:  # noqa
            f.write(out.getvalue())
