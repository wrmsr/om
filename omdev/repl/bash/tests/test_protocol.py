import re

import pytest

from ..protocol import BashPrompt
from ..protocol import BashProtocol


##


def mark(seq, returncode, cwd, *, nonce='n0nce'):
    return f'\x1b]7770;{nonce};{seq};{returncode};{cwd}\x07'.encode()


def decode_submission(data):
    """A submission read back the way bash reads it: the `$'...'` chunks of its block, unescaped and joined."""

    first, *block, last = data.decode('ascii').splitlines()
    assert first == '{'
    source = b''
    for i, line in enumerate(block):
        m = re.fullmatch(r"__om_s(\+?)=\$'(.*)'", line)
        assert m is not None
        assert bool(m.group(1)) == bool(i)
        source += re.sub(rb'\\x([0-9a-f]{2})', lambda x: bytes([int(x.group(1), 16)]), m.group(2).encode('ascii'))
    return source.decode('utf-8'), last


def test_scanner_splits_output_and_prompts():
    scanner = BashProtocol('n0nce').new_scanner()
    assert scanner.feed(b'one\r\n' + mark(3, 0, '/work') + b'two' + mark(4, 130, '/a b') + b'three') == [
        b'one\r\n',
        BashPrompt(seq=3, returncode=0, cwd='/work'),
        b'two',
        BashPrompt(seq=4, returncode=130, cwd='/a b'),
        b'three',
    ]
    assert scanner.feed(b'') == []


def test_scanner_holds_a_mark_split_anywhere():
    data = b'before' + mark(12, 1, '/work') + b'after'
    for i in range(len(data) + 1):
        scanner = BashProtocol('n0nce').new_scanner()
        events = scanner.feed(data[:i]) + scanner.feed(data[i:])
        assert b''.join(e for e in events if isinstance(e, bytes)) == b'beforeafter'
        assert [e for e in events if isinstance(e, BashPrompt)] == [BashPrompt(seq=12, returncode=1, cwd='/work')]


def test_scanner_is_not_taken_in():
    scanner = BashProtocol('n0nce').new_scanner()

    # Another conversation's mark, an escape which only begins like one, and one which is never finished.
    other = mark(1, 0, '/', nonce='other')
    assert scanner.feed(other + b'\x1b]7770;x') == [other + b'\x1b]7770;x']

    unfinished = b'\x1b]7770;n0nce;' + b'x' * 10_000
    assert scanner.feed(b'a' + unfinished[:100]) == [b'a']
    assert scanner.feed(unfinished[100:]) == [unfinished]


def test_init_is_one_short_line():
    protocol = BashProtocol()
    init = protocol.init()
    assert init.endswith(b'\n')
    assert init.count(b'\n') == 1
    assert len(init) < 768
    assert protocol.nonce.encode() in init
    init.decode('ascii')


@pytest.mark.parametrize('source', [
    'echo hi',
    "echo 'single' \"double\" \\ back`tick` $dollar",
    'line one\nline two\n\n\tindented',
    'control \x03\x04\x15\x16\x1a\x1b\x7f characters',
    'unicode: héllo → \u65e5\u672c 🙂',
    'x' * 5000,
    'é' * 3000,
    '',
])
def test_submissions_survive_a_terminal(source):
    data = BashProtocol('n0nce', max_line_bytes=256).submit(7, source)

    # Printable ascii in short lines: nothing a terminal's line discipline acts on, or cuts.
    text = data.decode('ascii')
    assert text.endswith('\n')
    assert all(0x20 <= ord(c) < 0x7f for c in text.replace('\n', ''))
    assert all(len(line) <= 256 for line in text.splitlines())

    decoded, last = decode_submission(data)
    assert decoded == source
    assert last == '}; __om_n=7; __om_rc "$__om_last"; eval "$__om_s" </dev/null'


def test_submissions_drop_nuls():
    assert decode_submission(BashProtocol('n0nce').submit(1, 'a\0b'))[0] == 'ab'


def test_commands():
    protocol = BashProtocol('n0nce')
    assert protocol.command(4, protocol.SYNC) == b' __om_n=4; :\n'
    assert protocol.command(5, protocol.KILL_STOPPED_JOBS).endswith(b'\n')
    with pytest.raises(RuntimeError):
        protocol.command(6, 'x' * 1000)


def test_versions():
    assert BashProtocol.parse_version('5.2\r\n') == (5, 2)
    assert BashProtocol.parse_version('3.2') == (3, 2)
    assert BashProtocol.parse_version('sh: 1: Bad substitution') is None
    assert BashProtocol.parse_version('.') is None
    assert BashProtocol.parse_version('') is None
