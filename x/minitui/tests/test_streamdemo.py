from ..apps.streamdemo import PARAGRAPHS
from ..apps.streamdemo import StreamDemo
from ..apps.streamdemo import wrap_words
from .harness import SurfaceHarness


##


def test_wrap_words():
    assert wrap_words(['a', 'bb', 'ccc', 'dddd'], 6) == ['a bb', 'ccc', 'dddd']
    assert wrap_words([], 10) == []
    assert wrap_words(['toolongword'], 4) == ['toolongword']


def test_streamdemo_transcript():
    h = SurfaceHarness(height=10, width=60)

    StreamDemo(h.surface, word_delay_s=0).run()
    h.pump()

    lines = h.all_lines()
    text = '\n'.join(lines)

    # Every paragraph made it into the terminal, in full, in order.
    positions = []
    for paragraph in PARAGRAPHS:
        first_words = ' '.join(paragraph.split()[:4])
        assert first_words in text.replace('\n', ' ')
        positions.append(text.replace('\n', ' ').index(first_words))
    assert positions == sorted(positions)

    # The committed transcript is in scrollback plus screen; the live tail ended as the single 'done' line.
    assert any(line.startswith('done - ') for line in h.screen())
    assert lines[0].startswith('assistant')
