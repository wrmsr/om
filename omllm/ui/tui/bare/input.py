import asyncio
import functools
import sys

from omcore import inject as inj

from .... import agent as agn
from ....core import ui
from ..config import Config
from .previews import ShownPreviews


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
    def __init__(
            self,
            *,
            input_manager: InputManager,
            text_displayer: ui.TextDisplayer,
            shown_previews: ShownPreviews,
    ) -> None:
        super().__init__()

        self._input_manager = input_manager
        self._text_displayer = text_displayer
        self._shown_previews = shown_previews

        # A preview and the prompt it belongs to go out together: another ask's preview must not land mid-prompt.
        self._mtx = asyncio.Lock()

    @staticmethod
    def _describe_requestor(requestor: agn.PermissionRequestor) -> str:
        if (context := requestor.tool_context) is not None and (tool := context.tool) is not None:
            return tool.name
        return repr(requestor)

    async def ask(
            self,
            request: agn.PermissionRequest,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        async with self._mtx:
            if preview := request.preview:
                await self._text_displayer.display_text(preview)
                self._shown_previews.add(request.requestor.tool_context, preview)

            prompt = f'{self._describe_requestor(request.requestor)} :: {request.target!r} (y/n) '
            while True:
                out = await self._input_manager.input(prompt)
                if out == 'y':
                    return agn.PermissionState.ALLOW
                elif out == 'n':
                    return agn.PermissionState.DENY


##


def bind_input(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(InputManager, singleton=True),
        inj.bind(ShownPreviews, singleton=True),
    ])

    lst.extend([
        inj.bind(InputPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=InputPermissionAsker),
    ])

    return inj.as_elements(*lst)
