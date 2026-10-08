import contextlib
import pathlib
import shutil
import tempfile
import typing as ta

import pytest


##


@pytest.fixture
def exit_stack():
    with contextlib.ExitStack() as es:
        yield es


@pytest.fixture
async def async_exit_stack():
    async with contextlib.AsyncExitStack() as aes:
        yield aes


##


@pytest.fixture
def temp_path() -> ta.Generator[pathlib.Path]:
    """pytest's builtin `tmp_path` by default produces paths too long for certain usecases (like unix sockets)."""

    path = tempfile.mkdtemp()

    yield pathlib.Path(path)

    shutil.rmtree(path)
