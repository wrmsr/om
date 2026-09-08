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
import itertools

from . import consts


##


class Buffer:
    __slots__ = ('_data',)

    def __init__(self, iterable=()):
        self._data = bytearray(iterable)

    def extend(self, iterable):
        self._data.extend(iterable)

    def append_bits(self, val, length):
        self._data.extend((val >> i) & 1 for i in reversed(range(length)))

    def getbits(self):
        return self._data

    def toints(self):
        return (int(''.join(map(str, g)), 2) for g in itertools.zip_longest(*[iter(self._data)] * 8, fillvalue=0))

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]


##


def get_mode_name(mode_const):
    for name, val in consts.MODE_MAPPING.items():
        if val == mode_const:
            return name
    raise ValueError(f'Unknown mode "{mode_const}"')


def version_range(version):
    # ISO/IEC 18004:2015(E)
    # Table 3 - Number of bits in character count indicator for QR Code (page 23)
    if 0 < version < 10:
        return consts.VERSION_RANGE_01_09
    elif 9 < version < 27:
        return consts.VERSION_RANGE_10_26
    elif 26 < version < 41:
        return consts.VERSION_RANGE_27_40
    raise ValueError(f'Unknown version "{version}"')


def get_version_name(version_const):
    if 0 < version_const < 41:
        return version_const
    raise ValueError(f'Unknown version constant "{version_const}"')


##


def get_default_border_size(matrix_size):
    width, height = matrix_size
    return 4 if width > 17 and width == height else 2


def get_border(matrix_size, border):
    return border if border is not None else get_default_border_size(matrix_size)


def check_valid_scale(scale):
    if scale <= 0:
        raise ValueError(f'The scale must not be negative or zero. Got: "{scale}"')


def check_valid_border(border):
    if border is not None and (int(border) != border or border < 0):
        raise ValueError(f'The border must not a non-negative integer value. Got: "{border}"')


##


def matrix_iter(
        matrix,
        matrix_size,
        scale=1,
        border=None,
):
    check_valid_border(border)
    scale = int(scale)
    check_valid_scale(scale)
    border = get_border(matrix_size, border)
    width, height = matrix_size
    border_row = [0x0] * width
    width_range, height_range = range(-border, width + border), range(-border, height + border)
    for i in height_range:
        r = matrix[i] if 0 <= i < height else border_row
        row = tuple(itertools.chain.from_iterable(
            itertools.repeat(r[j] if 0 <= j < width else 0x0, scale)
            for j in width_range
        ))
        for _ in itertools.repeat(None, scale):
            yield row
