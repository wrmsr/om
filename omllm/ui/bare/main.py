import argparse
import asyncio
import functools
import os
import sys
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omdev.home.secrets import load_secrets
from omdev.tui import rich
from omdev.tui.rich import textual as rich_tx

from ... import agent as agn
from ... import harness as har
from ... import llm
from ...agent.fs.tools.ls import LsTool
from ...agent.fs.tools.read import ReadTool
from ...agent.shell.tools.bash import BashTool
from ...core import ui
from ...harness.commands.permissions import PermissionsCommand
from ...harness.commands.simple import EchoCommand
from ...harness.commands.simple import QuitCommand


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
            out = await self._input_manager.input(repr(target) + ' (y/n) ')
            if out == 'y':
                return agn.PermissionState.ALLOW
            elif out == 'n':
                return agn.PermissionState.DENY


##


class RichMarkdown(ta.NamedTuple):
    theme: ta.Any
    code_theme: ta.Any


@lang.cached_function
def rich_markdown() -> RichMarkdown:
    return RichMarkdown(
        rich_tx.build_theme(rich_tx.TEXTUAL_DARK),
        rich_tx.build_pygments_theme(rich_tx.TEXTUAL_DARK),
    )


##


async def _a_main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('--fs', action='store_true')
    parser.add_argument('--bash', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    #

    model_key = llm.ModelKey('openai', 'gpt-5.4-mini')
    api_key_name = 'openai_api_key'
    backend_cls = (
        # llm.OpenaiCompletionsImmediateBackend
        llm.OpenaiCompletionsStreamBackend
    )

    cwd = os.path.abspath(os.path.realpath(os.getcwd()))

    #

    input_manager = InputManager()

    #

    backend = backend_cls(
        llm.default_model_catalog()[model_key],  # noqa
        api_key=load_secrets().get(api_key_name),
    )

    async def on_event(ev: agn.Event) -> None:
        if args.verbose:
            print(ev)

        if isinstance(ev, agn.TurnEndEvent):
            if isinstance(msg := ev.message, llm.AiMessage):
                for c in msg.content:
                    if isinstance(c, llm.TextContent):
                        if (s := c.text.strip()):
                            rm = rich_markdown()
                            rich.Console(theme=rm.theme).print(rich.Markdown(s, code_theme=rm.code_theme))

    agent = agn.Agent(
        backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore
        sink=on_event,
    )

    permissions_manager = agn.StandardPermissionsManager([  # noqa
        agn.PermissionRule(
            agn.GlobFsPermissionMatcher(os.path.join(cwd, '**/*'), ['r']),
            agn.PermissionState.ASK,
        ),
    ])

    permission_decider = agn.StandardPermissionDecider(
        manager=permissions_manager,
        asker=InputPermissionAsker(
            input_manager=input_manager,
        ),
    )

    tools = agn.ToolSet([

        *([
            BashTool(
                permissions=permission_decider,
            ).tool(),
        ] if args.bash else []),

        *([
            LsTool(
                permissions=permission_decider,
            ).tool(),
            ReadTool(
                permissions=permission_decider,
            ).tool(),
        ] if args.fs else []),

    ])

    await agent.modify_state(
        lambda state: dc.replace(
            state,
            context=dc.replace(
                state.context,
                system_prompt='\n\n'.join([
                    f'Current working directory: {cwd}',
                ]),
                tools=tools,
            ),
            tool_env=agn.ToolEnvironment(
                cwd=cwd,
            ),
        ),
    )

    #

    text_displayer = ui.PrintTextDisplayer()

    commands_manager = har.CommandsManager(
        commands=har.Commands([

            EchoCommand(),

            QuitCommand(
                quit_signal=ui.RaiseQuitSignal(KeyboardInterrupt),
            ),

            PermissionsCommand(
                permissions=permissions_manager,
            ),

        ]),
        text_displayer=text_displayer,
    )

    session = har.Session(
        agent=agent,
        commands_manager=commands_manager,
    )

    #

    if sys.stdin.isatty():
        try:
            import readline  # noqa
        except ImportError:
            pass

    while True:
        try:
            entry = await input_manager.input('> ')
        except EOFError:
            break

        if entry == '/quit':
            break

        await session.prompt(entry)


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
