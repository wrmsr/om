import sys

from ..encoding import make
from ..writers import write_terminal
from ..writers import write_terminal_compact


def test_qr():
    qr = make('Your text or URL here ' * 3)

    print()
    write_terminal(qr.matrix, qr.matrix_size, sys.stdout)
    write_terminal_compact(qr.matrix, qr.matrix_size, sys.stdout)
