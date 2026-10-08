import os
import subprocess
import sys

from .. import _bpe


##


def test_loads_before_the_binding():
    # Everything else here has long since imported _pcre2, one way or another, by the time it imports this - which
    # would hide its only loading if something else already had.
    script = '\n'.join([
        'import sys',
        f'from {_bpe.__name__.rpartition(".")[0]} import {_bpe.__name__.rpartition(".")[2]} as bpe',
        'assert "omcore.text.pcre2._pcre2" in sys.modules',
        'tok = bpe.Tokenizer()',
        'tok.train_from_iterator(["ab ab ab"], 300)',
        'assert tok.encode("ab ab") == [256, 257]',
    ])
    subprocess.run(
        [sys.executable, '-c', script],
        env={**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)},
        check=True,
        timeout=60,
    )
