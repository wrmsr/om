# ruff: noqa: UP006 UP007 UP045
# @om-lite
import os
import tempfile
import typing as ta
import uuid

from .paths import get_home_dir


##


HOME_ID_FILE_NAME = 'id'


def get_home_id(
        *,
        no_create: bool = False,

        _file_path: ta.Optional[str] = None,
        home_path: ta.Optional[str] = None,
) -> uuid.UUID:
    if _file_path is not None:
        path = _file_path
    else:
        if home_path is None:
            home_path = get_home_dir()
        path = os.path.join(home_path, HOME_ID_FILE_NAME)
    path = os.path.abspath(path)

    #

    if not os.path.exists(path) and not no_create:
        new_id = getattr(uuid, 'uuid7', uuid.uuid4)()

        fd, tmp = tempfile.mkstemp(prefix='.' + HOME_ID_FILE_NAME + '.', suffix='.tmp', dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(str(new_id) + '\n')
                f.flush()
                os.fsync(f.fileno())

            try:
                os.link(tmp, path)
            except FileExistsError:
                pass
            else:
                return new_id

        finally:
            os.unlink(tmp)

    #

    with open(path, encoding='utf-8') as f:
        id_str = f.read().strip()

    read_id = uuid.UUID(id_str)
    if str(read_id) != id_str.lower():
        raise ValueError(read_id)

    return read_id
