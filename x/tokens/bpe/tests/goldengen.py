"""
Writes golden.py, which is what rustbpe - the original, and no part of this codebase - makes of the texts here:

    pip install rustbpe
    python -m omllm.tokens.bpe.tests.goldengen
"""
import importlib.metadata
import os.path
import textwrap
import typing as ta

from omcore import lang

from .texts import SAMPLES


rustbpe: ta.Any = lang.proxy_import('rustbpe')


##


GOLDEN_FILE = os.path.join(os.path.dirname(__file__), 'golden.py')

VOCAB_SIZE = 256 + 96

# Other patterns, and in particular ones which can match nothing - where how a search goes on from one match to the
# next is not something every regex engine agrees on.
PATTERN_CASES = [
    (r'a*', 'baaac'),
    (r'|a', 'aa'),
    (r'a|', 'aab'),
    (r'a??', 'aaa'),
    (r'x*|a', 'aaxa'),
    (r'(?=a)|a', 'aab'),
    (r'(?<=a)b|', 'abab'),
    (r'\b', 'ab cd'),
    (r'\b\w*', 'ab cd  ef'),
    (r'\w*', 'ab, cd'),
    ('\u00e9*|b', '\u00e9\u00e9b\u00e9'),
    ('(?:)|\u4e2d', '\u4e2d\u4e2d'),
    (r'\w+|\s+', "it's 12 o'clock,  na\u00efve \u4e2d\u6587!"),
    (r'\S+', ' leading and  trailing '),
    (r'(?i)[a-c]+', 'abcABCdabC'),
    (r'\d{2}', '12345 6 78'),
    (r'(?s).', 'a\n\u4e2d'),
    (r'.', 'a\n\u4e2d'),
]


def split(text, pattern=None):
    # Trained on one text until there is nothing left to merge, every chunk of it is a token of its own.
    tok = rustbpe.Tokenizer()
    tok.train_from_iterator([text], 256 + 100_000, pattern=pattern)
    vocab = [bytes(token_bytes) for token_bytes, _ in tok.get_mergeable_ranks()]
    return [vocab[token].decode() for token in tok.encode(text)]


def wrap(items, indent, width=120):
    lines = []
    line = indent
    for item in items:
        piece = item + ','
        if len(indent) + len(piece) > width:
            if line.strip():
                lines.append(line.rstrip())
            lines.append(indent + piece + '  # noqa')
            line = indent
            continue
        if len(line) + len(piece) + (1 if line.strip() else 0) > width:
            lines.append(line.rstrip())
            line = indent
        line += (' ' if line.strip() else '') + piece
    if line.strip():
        lines.append(line.rstrip())
    return lines


def wrap_lists(lists, render):
    lines = []
    for items in lists:
        if not items:
            lines.append('    [],')
        else:
            lines.extend(['    [', *wrap([render(item) for item in items], ' ' * 8), '    ],'])
    return lines


def generate():
    tok = rustbpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, VOCAB_SIZE)
    ranks = [(bytes(token_bytes), token) for token_bytes, token in tok.get_mergeable_ranks()]
    if [token for _, token in ranks] != list(range(VOCAB_SIZE)):
        raise RuntimeError('the samples do not have that many merges in them')

    pattern_lines = []
    for pattern, text in PATTERN_CASES:
        line = f'    ({pattern!a}, {text!a}, {split(text, pattern)!a}),'
        pattern_lines.append(line + ('  # noqa' if len(line) > 120 else ''))

    doc = [
        (
            f'What rustbpe {importlib.metadata.version("rustbpe")} makes of the sample texts, to hold the extension '
            f'to: the pattern it defaults to, the merges it learns from them, what it encodes each of them to with '
            f'those, and the chunks it splits each of them into - and then the chunks it splits a few other texts into '
            f'by other patterns.'
        ),
        (
            'This is not written by hand: it is written by goldengen, from the output of the rustbpe wheel, and is '
            'only to be replaced by more of the same.'
        ),
    ]

    return '\n'.join([
        '"""',
        '\n\n'.join(textwrap.fill(paragraph, 120) for paragraph in doc),
        '"""',
        '',
        '',
        '##',
        '',
        '',
        f'PATTERN = {tok.get_pattern()!a}  # noqa',
        '',
        f'VOCAB_SIZE = {VOCAB_SIZE}',
        '',
        'MERGES = [',
        *wrap([ascii(token_bytes) for token_bytes, _ in ranks[256:]], ' ' * 4),
        ']',
        '',
        'ENCODED = [',
        *wrap_lists([tok.encode(text) for text in SAMPLES], str),
        ']',
        '',
        'CHUNKS = [',
        *wrap_lists([split(text) for text in SAMPLES], ascii),
        ']',
        '',
        'PATTERN_CHUNKS = [',
        *pattern_lines,
        ']',
        '',
    ])


def _main() -> None:
    src = generate()
    with open(GOLDEN_FILE, 'w') as f:
        f.write(src)


if __name__ == '__main__':
    _main()
