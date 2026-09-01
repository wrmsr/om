from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


MARKDOWN = (
    '# Skip Install If Command Already Exists\n'
    '\n'
    'The standard approach is a guard.\n'
    '\n'
    '- check first\n'
    '- then install\n'
    '\n'
    '```sh\n'
    'command -v foo || install foo\n'
    '```\n'
    '\n'
    'Done.\n'
)


def _stream(app, text, *, chunk=3):
    for i in range(0, len(text), chunk):
        app.stream_feed(text[i:i + chunk])


def test_streamed_markdown_renders_like_immediate():
    # Deltas settle a block at a time, each committed on its own - the blank rows between blocks must survive that, so
    # the scrollback matches immediate mode's one-shot rendering exactly.
    app, driver = make_app()
    app.display_markdown(MARKDOWN)
    immediate = '\n'.join(commit_texts(driver))
    assert '\n\n' in immediate

    app, driver = make_app()
    app.begin_ai_turn()
    driver.commits.clear()
    _stream(app, MARKDOWN)
    app.stream_break()
    assert len(driver.commits) > 2
    assert '\n'.join(commit_texts(driver)) == immediate


def test_live_tail_separates_from_committed_blocks():
    app, driver = make_app()
    app.begin_ai_turn()

    app.stream_feed('First paragraph.\n\nSecond')
    assert commit_texts(driver)[-1] == 'First paragraph.'
    lines = frame_lines(app)
    assert lines[0] == ''
    assert lines[1].startswith('Second')

    # A fresh cycle with nothing settled yet: the tail sits directly under whatever the app committed last.
    app.stream_break()
    app.stream_feed('Third')
    assert frame_lines(app)[0].startswith('Third')
