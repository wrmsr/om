import os.path
import subprocess
import sys


##


def _run(*args, src=''):
    return subprocess.run(
        [sys.executable, '-m', 'omdev.tools.json', *args],
        input=src.encode('utf-8'),
        capture_output=True,
        timeout=60,
        check=False,
    )


def _out(*args, src=''):
    p = _run(*args, src=src)
    assert p.returncode == 0, p.stderr.decode()
    return p.stdout.decode()


##


def test_eager():
    doc = '{"b": 2, "a": [1, null, true]}'
    assert _out(src=doc) == '{"b": 2, "a": [1, null, true]}\n'
    assert _out('-z', src=doc) == '{"b":2,"a":[1,null,true]}\n'
    assert _out('-s', src='{"b": 2, "a": 1}') == '{"a": 1, "b": 2}\n'
    assert _out('-p', src='{"b": 2, "a": [1]}') == '{\n  "b": 2,\n  "a": [\n    1\n  ]\n}\n'


def test_eager_file_input(tmp_path):
    fp = os.path.join(str(tmp_path), 'doc.json')
    with open(fp, 'w') as f:
        f.write('{"a": 1}')

    assert _out(fp) == '{"a": 1}\n'


##


def test_stream():
    assert _out('-S', src='{"a": [1, 2]} "x" 3') == '{"a": [1, 2]}\n"x"\n3\n'


def test_stream_build():
    assert _out('-S', '-B', src='{"a": [1, 2]} "x" 3') == '{"a": [1, 2]}\n"x"\n3\n'


def test_stream_trailing_scalar():
    # A bare trailing value with no terminator must be flushed at EOF
    assert _out('-S', src='123') == '123\n'
    assert _out('-S', '-B', src='123') == '123\n'


def test_stream_small_read_buffer():
    # Single-byte reads force chunk-straddling tokens and split multibyte utf-8 sequences through the whole pipeline
    src = '{"a": [1, 2], "k\u00e9y": "\u00fcn\u00efcod\u00e9"} "x" 3'
    expected = '{"a": [1, 2], "k\\u00e9y": "\\u00fcn\\u00efcod\\u00e9"}\n"x"\n3\n'

    for args in [('-S',), ('-S', '-B')]:
        assert _out(*args, '--read-buffer-size', '1', src=src) == expected


def test_stream_partial_output_before_error():
    p = _run('-S', src='[1, ')
    assert p.returncode != 0
    assert p.stdout.decode() == '[1\n'


##


def test_lines():
    assert _out('-l', src='{"a": 1}\n{"b": 2}\n') == '{"a": 1}\n{"b": 2}\n'


def test_json5_input():
    assert _out('-f', 'json5', src="{a: 'x', b: [true,] /* c */}") == '{"a": "x", "b": [true]}\n'


def test_invalid_input_fails():
    for args in [(), ('-S',), ('-S', '-B'), ('-l',)]:
        p = _run(*args, src='not json')
        assert p.returncode != 0
