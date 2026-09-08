# Copyright (c) 2016 - 2025, Lars Heuer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#    disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import codecs
import contextlib
import itertools

from .utils import matrix_iter


##


@contextlib.contextmanager
def writable(file_or_path, mode, encoding=None):
    f = file_or_path
    must_close = False
    try:
        file_or_path.write  # noqa
        if encoding is not None:
            f = codecs.getwriter(encoding)(file_or_path)
    except AttributeError:
        f = open(file_or_path, mode, encoding=encoding)
        must_close = True
    try:
        yield f
    finally:
        if must_close:
            f.close()


##


def write_terminal_compact(
        matrix,
        matrix_size,
        out,
        border=None,
):
    blocks = {
        (1, 1): ' ',
        (0, 1): '\u2580',  # Upper half block
        (1, 0): '\u2584',  # Lower half block
        (0, 0): '\u2588',  # Full block
    }
    it = [matrix_iter(matrix, matrix_size, scale=1, border=border)] * 2
    with writable(out, 'wt') as f:
        write = f.write
        for top_row, bottom_row in itertools.zip_longest(*it, fillvalue=itertools.repeat(1)):
            write(''.join(blocks[pair] for pair in zip(top_row, bottom_row)))
            write('\n')


def write_terminal(
        matrix,
        matrix_size,
        out,
        border=None,
):
    with writable(out, 'wt') as f:
        write = f.write
        colours = [f'\033[{i}m' for i in (7, 49)]
        for row in matrix_iter(matrix, matrix_size, scale=1, border=border):
            prev_bit = -1
            cnt = 0
            for bit in row:
                if bit == prev_bit:
                    cnt += 1
                else:
                    if cnt:
                        write(colours[prev_bit])
                        write('  ' * cnt)
                        write('\033[0m')  # reset color
                    prev_bit = bit
                    cnt = 1
            if cnt:
                write(colours[prev_bit])
                write('  ' * cnt)
                write('\033[0m')  # reset color
            write('\n')
