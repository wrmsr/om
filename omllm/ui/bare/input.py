import asyncio
import functools
import sys

from omcore import inject as inj

from ... import agent as agn
from .config import Config


##


class InputManager:
    def __init__(self) -> None:
        super().__init__()

        self._mtx = asyncio.Lock()

    #

    _has_init = False

    async def _do_init(self) -> None:
        if sys.stdin.isatty():
            try:
                import readline  # noqa
            except ImportError:
                pass

    async def _maybe_init(self) -> None:
        if not self._has_init:
            await self._do_init()
            self._has_init = True

    #

    async def input(self, prompt: str | None = None) -> str:
        async with self._mtx:
            await self._maybe_init()

            return await asyncio.to_thread(
                functools.partial(
                    input,
                    *([prompt] if prompt is not None else []),
                ),
            )


##


class InputPermissionAsker(agn.PermissionAsker):
    def __init__(self, *, input_manager: InputManager) -> None:
        super().__init__()

        self._input_manager = input_manager

    async def ask(
            self,
            requestor: agn.PermissionRequestor,
            target: agn.PermissionTarget,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        while True:
            out = await self._input_manager.input(f'{requestor!r} :: {target!r} (y/n) ')
            if out == 'y':
                return agn.PermissionState.ALLOW
            elif out == 'n':
                return agn.PermissionState.DENY


##


def bind_input(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.append(inj.bind(InputManager, singleton=True))

    lst.extend([
        inj.bind(InputPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=InputPermissionAsker),
    ])

    return inj.as_elements(*lst)
