"""
An offline demo of the web frontend: a scripted model, paced so that its streaming shows, working through a little
project in a temporary directory - looking around, reading a file, editing it (which asks), running it (which asks), and
saying what it did. Every prompt gets the same performance.

    python -m omllm.ui.web.tests.demo [--port N]
"""
import argparse
import asyncio
import functools
import os.path
import tempfile
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj

from .... import agent as agn
from .... import llm
from ..config import WebConfig
from ..main import configure_web_logging
from ..main import serve_web


##


DEMO_FILE_NAME = 'hello.py'

DEMO_FILE_CONTENTS = """\
def greet(name):
    print("hello " + name)


if __name__ == "__main__":
    greet("world")
"""

DEMO_FINAL_ANSWER = """\
Done - `greet` now uses an f-string and says a little more:

```python
def greet(name):
    print(f"hello, {name}!")
```

| step | tool | result |
|---|---|---|
| look around | `ls` | found `hello.py` |
| read it | `read` | 6 lines |
| edit it | `edit` | 1 line changed |
| run it | `bash` | `hello, world!` |

Anything else? A few things I *could* do next:

1. add a `--name` argument
2. add a test
3. leave it be
"""


def _text(text: str) -> llm.TextContent:
    return llm.TextContent(text)


def _call(name: str, **args: ta.Any) -> llm.ToolCall:
    return llm.ToolCall(f'demo-{name}', name, args)


def build_demo_script(cwd: str) -> llm.BackendScript:
    file_path = os.path.join(cwd, DEMO_FILE_NAME)

    turns = [
        llm.AiMessage(
            [
                llm.ThinkingContent(
                    'The user wants something done in this project, but I have not seen it yet. Best to look around '
                    'before touching anything.',
                ),
                _text("I'll start by looking around the project."),
                _call('ls', dir_path=cwd),
            ],
            stop_reason='tool_use',
        ),
        llm.AiMessage(
            [
                _text(f'There is just `{DEMO_FILE_NAME}` - let me read it.'),
                _call('read', file_path=file_path),
            ],
            stop_reason='tool_use',
        ),
        llm.AiMessage(
            [
                _text('The greeting could be friendlier. **Editing it now** - this one needs your permission.'),
                _call(
                    'edit',
                    file_path=file_path,
                    old_string='    print("hello " + name)',
                    new_string='    print(f"hello, {name}!")',
                ),
            ],
            stop_reason='tool_use',
        ),
        llm.AiMessage(
            [
                _text("Now let's make sure it still runs."),
                _call('bash', command=f'python3 {DEMO_FILE_NAME}'),
            ],
            stop_reason='tool_use',
        ),
        llm.AiMessage(
            [_text(DEMO_FINAL_ANSWER)],
            stop_reason='stop',
        ),
    ]

    return llm.BackendScript(
        [llm.BackendScriptTurn(t, chunk_size=6) for t in turns],
        on_exhausted='restart',
    )


class DemoBackendScriptCursor(llm.BackendScriptCursor):
    """
    Walks the script round and round, from the top again whenever told to - at each new prompt - and gives the calls of
    every turn ids of their own: a turn repeated on a later prompt must not repeat its ids.
    """

    def __init__(self, script: llm.BackendScript) -> None:
        super().__init__(script)

        self._pos = 0
        self._n = 0

    def restart(self) -> None:
        self._pos = 0

    def next_turn(self) -> llm.BackendScriptTurn:
        turns = self.script.turns
        turn = turns[self._pos % len(turns)]
        self._pos += 1
        self._n += 1

        if (msg := turn.message) is None:
            return turn

        return dc.replace(turn, message=dc.replace(msg, content=[
            dc.replace(c, id=f'{c.id}-{self._n}') if isinstance(c, llm.ToolCall) else c
            for c in msg.content
        ]))


class DemoScriptedStreamBackend(llm.ScriptedStreamBackend):
    """
    Starts its script over for every prompt, so that a run cut short does not leave the next one mid-script - and puts
    the project back as it was, so that the script's edit has something to do every time.
    """

    def __init__(
            self,
            model: llm.Model,
            cursor: DemoBackendScriptCursor,
            *,
            on_restart: ta.Callable[[], None] | None = None,
    ) -> None:
        super().__init__(model, cursor=cursor)

        self._demo_cursor = cursor
        self._on_restart = on_restart

    async def stream(self, context: llm.Context, options: llm.Options | None = None) -> llm.AiStream:
        if (msgs := context.messages) and isinstance(msgs[-1], llm.UserMessage):
            self._demo_cursor.restart()
            if self._on_restart is not None:
                self._on_restart()

        return await super().stream(context, options)


def build_demo_backend(cwd: str, *, pace_s: float = .02) -> llm.ScriptedStreamBackend:
    async def gate(point: llm.BackendScriptGatePoint) -> None:
        await asyncio.sleep(pace_s)

    script = dc.replace(build_demo_script(cwd), gate=gate if pace_s > 0 else None)

    return DemoScriptedStreamBackend(
        llm.Model(
            key=llm.ModelKey('scripted', 'demo'),
            backend='scripted',
            reasoning_efforts=frozenset(llm.ReasoningEffort),
        ),
        DemoBackendScriptCursor(script),
        on_restart=functools.partial(write_demo_project, cwd),
    )


def bind_demo_backend(cwd: str, *, pace_s: float = .02) -> inj.Elemental:
    return inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager.of(build_demo_backend(cwd, pace_s=pace_s)),
    )


def build_demo_config(cwd: str, **kwargs: ta.Any) -> WebConfig:
    return WebConfig(
        cwd=cwd,

        fs=True,
        exec=True,

        in_memory=True,

        autoexec=[
            f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r"]}}\'',
            f'/permissions add ask glob_fs \'{{"glob":"{cwd}/**","modes":["w"]}}\'',
            '/permissions add ask exec {}',
        ],

        **kwargs,
    )


def write_demo_project(cwd: str) -> None:
    with open(os.path.join(cwd, DEMO_FILE_NAME), 'w') as f:
        f.write(DEMO_FILE_CONTENTS)


##


async def _a_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('--pace', type=float, default=.02)
    args = parser.parse_args()

    configure_web_logging()

    with tempfile.TemporaryDirectory(prefix='omllm-web-demo-') as cwd:
        cwd = os.path.realpath(cwd)
        write_demo_project(cwd)

        await serve_web(
            build_demo_config(cwd, port=args.port),
            overrides=[bind_demo_backend(cwd, pace_s=args.pace)],
        )


if __name__ == '__main__':
    try:
        asyncio.run(_a_main())
    except KeyboardInterrupt:
        pass
