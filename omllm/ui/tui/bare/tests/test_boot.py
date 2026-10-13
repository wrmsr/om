"""
The boot commands on the bare frontend: each shown as typed and set off by a blank line, its output - where it has any -
likewise, so the yolo boot reads as a run of commands ending in its echo, the prompt on its own line beneath.
"""
import io
import os.path

import pytest

from omcore import inject as inj

from .....core import ui
from ...config import Config
from ...rendering import TerminalTextDisplayer
from ...rendering import TerminalTextRenderer
from ...tests.headless import bind_scripted_backend
from ...tests.headless import headless_tui
from ...yolo import yolo_autoexec
from ...yolo import yolo_process_config
from ..inject import bind_bare
from ..prompting import Prompter


##


@pytest.mark.asyncs('asyncio')
async def test_bare_boot_commands_read_as_blocks(tmp_path):
    root = os.path.realpath(tmp_path)
    out = io.StringIO()

    def build_text_displayer(options: ui.TextRenderingOptions) -> TerminalTextDisplayer:
        return TerminalTextDisplayer(file=out, renderer=TerminalTextRenderer(options, width=200, color_depth=None))

    config = yolo_process_config(Config(
        model='scripted',
        in_memory=True,
        cwd=root,
        yolo=True,
    ))
    async with headless_tui(inj.override(
        bind_bare(config),
        inj.bind(TerminalTextDisplayer, singleton=True, to_fn=build_text_displayer),
        bind_scripted_backend(),
    )) as tui:
        prompter = await tui.injector[Prompter]
        for ax in yolo_autoexec(config, root):
            await prompter.prompt(ax, echo=True)

    text = out.getvalue()
    assert text.endswith('YOLO\n\n')

    # One blank line after each line shown: nothing run together, nothing doubled.
    lines = text[:-1].split('\n')
    assert lines[1::2] == [''] * (len(lines) // 2)
    content = lines[::2]
    assert all(content)

    # Each command as given, each add's rule beneath it, the echo and its word last.
    clear, *adds, echo = yolo_autoexec(config, root)
    assert content[0] == clear
    for i, add in enumerate(adds):
        assert content[1 + i * 2] == add
        rule = content[2 + i * 2]
        assert rule.startswith(f'#{i} ') and ' allow ' in rule
    assert content[-2:] == [echo, 'YOLO']
    assert len(content) == 3 + 2 * len(adds)


@pytest.mark.asyncs('asyncio')
async def test_bare_shows_a_typed_commands_output_as_a_block_without_echoing_it(tmp_path):
    out = io.StringIO()

    def build_text_displayer(options: ui.TextRenderingOptions) -> TerminalTextDisplayer:
        return TerminalTextDisplayer(file=out, renderer=TerminalTextRenderer(options, color_depth=None))

    async with headless_tui(inj.override(
        bind_bare(Config(
            model='scripted',
            in_memory=True,
            cwd=os.path.realpath(tmp_path),
        )),
        inj.bind(TerminalTextDisplayer, singleton=True, to_fn=build_text_displayer),
        bind_scripted_backend(),
    )) as tui:
        prompter = await tui.injector[Prompter]
        await prompter.prompt('/echo hi')
        await prompter.prompt('/nope')
        await prompter.prompt('/permissions clear')

    # The typed line is on the terminal already; what follows it is the output, ended and set off - or nothing.
    assert out.getvalue() == 'hi\n\nUnknown command: nope\n\n'
