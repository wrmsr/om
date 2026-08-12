import abc
import argparse
import asyncio
import functools
import os.path
import sys
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
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
from ...core.eventbus import EventSubscriber
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


class AgentEventDisplayer(lang.Abstract):
    def __init__(self, text_displayer: ui.TextDisplayer) -> None:
        super().__init__()

        self._text_displayer = text_displayer

    @abc.abstractmethod
    def on_event(self, ev: agn.Event) -> ta.Awaitable[None]:
        raise NotImplementedError


class VerbosePrinter(AgentEventDisplayer):
    async def on_event(self, ev: agn.Event) -> None:
        print(ev)


class ImmediateResponsePrinter(AgentEventDisplayer):
    async def on_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.TurnEndEvent):
            if isinstance(msg := ev.message, llm.AiMessage):
                for c in msg.content:
                    if isinstance(c, llm.TextContent):
                        if (s := c.text.strip()):
                            await self._text_displayer.display_text(ui.MarkdownText(s))


class StreamResponsePrinter(AgentEventDisplayer):
    async def on_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.LlmAiStreamEvent):
            lev = ev.event

            if isinstance(lev, llm.TextDeltaAiStreamEvent):
                await self._text_displayer.display_text(lev.text)

            elif isinstance(lev, llm.TextEndAiStreamEvent):
                await self._text_displayer.display_text('\n')


##


AgentEventSubscribers = ta.NewType('AgentEventSubscribers', ta.Sequence[EventSubscriber[agn.Event]])


@lang.cached_function
def agent_event_subscribers() -> inj.ItemsBinderHelper[EventSubscriber[agn.Event]]:
    return inj.items_binder_helper[EventSubscriber[agn.Event]](AgentEventSubscribers)


AgentTools = ta.NewType('AgentTools', ta.Sequence[agn.Tool])


@lang.cached_function
def agent_tools() -> inj.ItemsBinderHelper[agn.Tool]:
    return inj.items_binder_helper[agn.Tool](AgentTools)


@lang.cached_function
def harness_commands() -> inj.ItemsBinderHelper[har.Command]:
    return inj.items_binder_helper[har.Command](har.Commands)


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

    bindings: list[inj.Elemental] = []

    bindings.append(inj.bind(InputManager, singleton=True))

    #

    backend = backend_cls(
        llm.default_model_catalog()[model_key],  # noqa
        **(dict(api_key=load_secrets().get(api_key_name)) if api_key_name is not None else {}),  # type: ignore  # noqa
    )

    bindings.extend([
        inj.bind(build_rich_text_displayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=ui.RichTextDisplayer),
    ])

    if args.verbose:
        bindings.extend([
            inj.bind(VerbosePrinter, singleton=True),
            agent_event_subscribers().bind_item(to_fn=inj.target(o=VerbosePrinter)(lambda o: o.on_event)),
        ])

    if args.stream:
        bindings.extend([
            inj.bind(StreamResponsePrinter, singleton=True),
            agent_event_subscribers().bind_item(to_fn=inj.target(o=StreamResponsePrinter)(lambda o: o.on_event)),
        ])

    else:
        bindings.extend([
            inj.bind(ImmediateResponsePrinter, singleton=True),
            agent_event_subscribers().bind_item(to_fn=inj.target(o=ImmediateResponsePrinter)(lambda o: o.on_event)),
        ])

    bindings.append(inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        }),
    ))

    bindings.extend([
        agent_event_subscribers().bind_items_provider(singleton=True),

        inj.bind(agn.Agent, singleton=True),
    ])

    permission_rules = [  # noqa
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
    ]

    bindings.append(inj.bind(
        agn.PermissionsManager,
        to_const=agn.StandardPermissionsManager(permission_rules),
    ))

    bindings.extend([
        inj.bind(InputPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=InputPermissionAsker),

        inj.bind(agn.StandardPermissionDecider, singleton=True),
        inj.bind(agn.PermissionDecider, to_key=agn.StandardPermissionDecider),
    ])

    if args.bash:
        bindings.extend([
            inj.bind(agn.LocalShellOps, singleton=True),
            inj.bind(agn.ShellOps, to_key=agn.LocalShellOps),

            inj.bind(BashTool, singleton=True),
            agent_tools().bind_item(to_fn=inj.target(o=BashTool)(lambda o: o.tool())),
        ])

    if args.fs:
        bindings.extend([
            inj.bind(agn.LocalFsOps, singleton=True),
            inj.bind(agn.FsOps, to_key=agn.LocalFsOps),

            inj.bind(EditTool, singleton=True),
            agent_tools().bind_item(to_fn=inj.target(o=EditTool)(lambda o: o.tool())),

            inj.bind(LsTool, singleton=True),
            agent_tools().bind_item(to_fn=inj.target(o=LsTool)(lambda o: o.tool())),

            inj.bind(ReadTool, singleton=True),
            agent_tools().bind_item(to_fn=inj.target(o=ReadTool)(lambda o: o.tool())),

            inj.bind(WriteTool, singleton=True),
            agent_tools().bind_item(to_fn=inj.target(o=WriteTool)(lambda o: o.tool())),

        ])

    bindings.extend([
        agent_tools().bind_items_provider(singleton=True),

        inj.bind(
            agn.ToolSet,
            to_fn=inj.target(ats=AgentTools)(lambda ats: agn.ToolSet(ats)),
            singleton=True,
        ),
    ])

    #

    bindings.extend([
        inj.bind(ui.RaiseQuitSignal(KeyboardInterrupt)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
    ])

    bindings.extend([
        inj.bind(EchoCommand, singleton=True),
        harness_commands().bind_item(to_key=EchoCommand),

        inj.bind(QuitCommand, singleton=True),
        harness_commands().bind_item(to_key=QuitCommand),

        inj.bind(PermissionsCommand, singleton=True),
        harness_commands().bind_item(to_key=PermissionsCommand),
    ])

    bindings.extend([
        harness_commands().bind_items_provider(singleton=True),

        inj.bind(har.CommandsManager, singleton=True),
    ])

    #

    session_id = uuid.uuid7()  # noqa

    state_dir_path = os.path.join(get_home_paths().state_dir, 'llm', 'sessions')
    os.makedirs(state_dir_path, exist_ok=True)

    if args.jsonl_storage:
        bindings.extend([
            inj.bind(har.JsonlSessionStorage(
                file_path=os.path.join(state_dir_path, f'{session_id.hex}.jsonl'),
            )),
            inj.bind(har.SessionStorage, to_key=har.JsonlSessionStorage),
        ])

    else:
        bindings.extend([
            inj.bind(har.InMemorySessionStorage()),
            inj.bind(har.SessionStorage, to_key=har.InMemorySessionStorage),
        ])

    bindings.extend([
        inj.bind(har.Session, singleton=True),
    ])

    #

    async with inj.create_async_managed_injector(
        *bindings,
        factory=inj.create_asyncio_injector,
    ) as injector:
        agent = await injector[agn.Agent]
        tool_set = await injector[agn.ToolSet]
        session = await injector[har.Session]
        input_manager = await injector[InputManager]

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await agent.update_state(
            lambda state: dc.replace(
                state,
                context=dc.replace(
                    state.context,
                    system_prompt='\n\n'.join([
                        f'Current working directory: {cwd}',
                    ]),
                    tools=tool_set,
                ),
                tool_env=agn.ToolEnvironment(
                    cwd=cwd,
                ),
            ),
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
