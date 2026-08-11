import argparse
import asyncio
import functools
import os.path
import sys
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omdev.home.paths import get_home_paths
from omdev.home.secrets import load_secrets
from omdev.tui import rich
from omdev.tui.rich import textual as rich_tx

from ... import agent as agn
from ... import harness as har
from ... import llm
from ...agent.fs.tools.edit import EditTool
from ...agent.fs.tools.ls import LsTool
from ...agent.fs.tools.read import ReadTool
from ...agent.fs.tools.write import WriteTool
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
            out = await self._input_manager.input(f'{requestor!r} :: {target!r} (y/n) ')
            if out == 'y':
                return agn.PermissionState.ALLOW
            elif out == 'n':
                return agn.PermissionState.DENY


##


@dc.dataclass(frozen=True, kw_only=True)
class RichUiStyles:
    theme: ta.Any
    code_theme: ta.Any
    json_styles: ui.RichJsonStyles


@lang.cached_function
def rich_ui_styles() -> RichUiStyles:
    dtx = rich_tx.TEXTUAL_DARK

    ps = check.not_none(dtx.pygments_styles)

    return RichUiStyles(
        theme=rich_tx.build_theme(dtx),
        code_theme=rich_tx.build_pygments_theme(dtx),
        json_styles=ui.RichJsonStyles(
            # Match the theme's code-block highlighting of json source.
            key=ps['Token.Name.Tag'],
            string=ps['Token.Literal.String.Double'],
            number=ps['Token.Literal.Number'],
            literal=ps['Token.Keyword.Constant'],
        ),
    )


def build_rich_text_displayer() -> ui.RichTextDisplayer:
    rs = rich_ui_styles()

    return ui.RichTextDisplayer(
        console=rich.Console(theme=rs.theme),
        renderer=ui.RichTextRenderer(
            markdown_code_theme=rs.code_theme,
            json_styles=rs.json_styles,
        ),
    )


##


async def _a_main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('--fs', action='store_true')
    parser.add_argument('--bash', action='store_true')

    parser.add_argument('-J', '--jsonl-storage', action='store_true')

    parser.add_argument('-X', '--autoexec', action='append')

    parser.add_argument('-S', '--stream', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    #

    model_key: llm.ModelKey
    api_key_name: ta.Any

    model_key, api_key_name = (
        (llm.ModelKey('openai', 'gpt-5.4-mini'), 'openai_api_key')
        # (llm.ModelKey('groq', 'openai/gpt-oss-120b'), 'groq_api_key')
        # (llm.ModelKey('cerebras', 'gpt-oss-120b'), 'cerebras_api_key')
        # (llm.ModelKey('ollama', 'qwen3.6:27b'), None)
    )

    backend_cls = (
        # llm.OpenaiCompletionsImmediateBackend
        llm.OpenaiCompletionsStreamBackend
    )

    if args.stream:
        check.issubclass(backend_cls, llm.StreamBackend)

    cwd = os.path.abspath(os.path.realpath(os.getcwd()))

    #

    input_manager = InputManager()

    #

    backend = backend_cls(
        llm.default_model_catalog()[model_key],  # noqa
        **(dict(api_key=load_secrets().get(api_key_name)) if api_key_name is not None else {}),  # type: ignore  # noqa
    )

    text_displayer = build_rich_text_displayer()

    async def on_event(ev: agn.Event) -> None:
        if args.verbose:
            print(ev)

        if isinstance(ev, agn.LlmAiStreamEvent):
            lev = ev.event

            if isinstance(lev, llm.TextDeltaAiStreamEvent):
                if args.stream:
                    print(lev.text, end='')

            elif isinstance(lev, llm.TextEndAiStreamEvent):
                if args.stream:
                    print()

        if isinstance(ev, agn.TurnEndEvent):
            if isinstance(msg := ev.message, llm.AiMessage):
                if not args.stream:
                    for c in msg.content:
                        if isinstance(c, llm.TextContent):
                            if (s := c.text.strip()):
                                await text_displayer.display_text(ui.MarkdownText(s))

    agent = agn.Agent(
        backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore
    )

    agent.subscribe(on_event)

    permissions_manager = agn.StandardPermissionsManager([  # noqa
        *([
            agn.PermissionRule(
                agn.GlobFsPermissionMatcher(os.path.join(cwd, '**'), ['r', 'w']),
                agn.PermissionState.ASK,
            ),
        ] if args.fs else []),

        *([
            agn.PermissionRule(
                agn.ShellPermissionMatcher(),
                agn.PermissionState.ASK,

            ),
        ] if args.bash else []),
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
            EditTool(
                permissions=permission_decider,
            ).tool(),
            LsTool(
                permissions=permission_decider,
            ).tool(),
            ReadTool(
                permissions=permission_decider,
            ).tool(),
            WriteTool(
                permissions=permission_decider,
            ).tool(),
        ] if args.fs else []),

    ])

    await agent.update_state(
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

    #

    session_id = uuid.uuid7()  # noqa

    state_dir_path = os.path.join(get_home_paths().state_dir, 'llm', 'sessions')
    os.makedirs(state_dir_path, exist_ok=True)

    session_storage: har.SessionStorage
    if args.jsonl_storage:
        session_storage = har.JsonlSessionStorage(
            file_path=os.path.join(state_dir_path, f'{session_id.hex}.jsonl'),
        )
    else:
        session_storage = har.InMemorySessionStorage()

    session = har.Session(
        agent=agent,
        storage=session_storage,
        commands_manager=commands_manager,
    )

    #

    async def prompt(s: str) -> None:
        if s == '/quit':
            raise SystemExit(0)

        await session.prompt(s)

    for ax in args.autoexec or []:
        await prompt(ax)

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

        await prompt(entry)


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
