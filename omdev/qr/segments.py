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
import operator
import re

from . import consts
from .utils import Buffer
from .utils import get_mode_name
from .utils import version_range


##


class _Segment(tuple):
    __slots__ = ()

    def __new__(
            cls,
            bits,
            char_count,
            mode,
            encoding=None,
    ):
        return tuple.__new__(cls, (
            bits,
            char_count,
            mode,
            encoding,
        ))

    bits = property(operator.itemgetter(0))
    char_count = property(operator.itemgetter(1))
    mode = property(operator.itemgetter(2))
    encoding = property(operator.itemgetter(3))


class Segments:
    __slots__ = (
        'bit_length',
        'modes',
        'segments',
    )

    def __init__(self):
        self.segments = []
        self.bit_length = 0
        self.modes = []

    def add_segment(self, segment):
        if self.segments:
            prev_seg = self.segments[-1]
            if prev_seg.mode == segment.mode and prev_seg.encoding == segment.encoding:
                # Merge segment with previous segment
                segment = _Segment(
                    prev_seg.bits + segment.bits,
                    prev_seg.char_count + segment.char_count,
                    segment.mode,
                    segment.encoding,
                )
                self.bit_length -= len(prev_seg.bits)
                del self.segments[-1]
                del self.modes[-1]
        self.segments.append(segment)
        self.bit_length += len(segment.bits)
        self.modes.append(segment.mode)

    def __len__(self):
        return len(self.segments)

    def __getitem__(self, item):
        return self.segments[item]

    def __iter__(self):
        return iter(self.segments)

    def bit_length_with_overhead(
            self,
            version,
            eci,
            is_sa=False,
    ):
        overhead = 0
        # ECI overhead
        if eci:
            no_eci_indicators = sum(
                1
                for segment in self.segments
                if segment.mode == consts.MODE_BYTE
                and segment.encoding != consts.DEFAULT_BYTE_ENCODING
            )
            overhead += no_eci_indicators * 4  # ECI indicator
            overhead += no_eci_indicators * 8  # ECI assignment no
        if is_sa:
            # 4 bit for mode, 4 bit for the position, 4 bit for total number of symbols
            # 8 bit for parity data
            overhead += 5 * 4
        # Mode indicator overhead
        if version > 0:  # QR Code
            overhead += len(self.modes) * 4
        elif version > consts.VERSION_M1:  # Micro QR Code (M1 has no mode indicator)
            overhead += len(self.modes) * (version + 3)
        # Char count indicator overhead
        ver_range = version_range(version) if version > 0 else version
        overhead += sum(consts.CHAR_COUNT_INDICATOR_LENGTH[mode][ver_range] for mode in self.modes)
        return overhead + self.bit_length


##


def data_to_bytes(data):
    if not isinstance(data, str):
        raise TypeError(data)
    encoding = consts.DEFAULT_BYTE_ENCODING
    data_ = data.encode(encoding)
    return data_, len(data_), consts.DEFAULT_BYTE_ENCODING


_ALPHANUMERIC_PATTERN = re.compile(br'^[' + re.escape(consts.ALPHANUMERIC_CHARS) + br']+\Z')


def is_alphanumeric(data):
    return _ALPHANUMERIC_PATTERN.match(data)


def find_mode(data):
    if data.isdigit():
        return consts.MODE_NUMERIC
    if is_alphanumeric(data):
        return consts.MODE_ALPHANUMERIC
    return consts.MODE_BYTE


def make_segment(data, mode):
    segment_data, segment_length, segment_encoding = data_to_bytes(data)
    segment_mode = mode

    # If the user prefers BYTE, use BYTE and do not try to find a better mode Necessary since BYTE < KANJI and find_mode
    # may return KANJI as (more) appropriate mode and the encoder throws an exception if "user provided mode" < "found
    # mode"
    guessed_mode = find_mode(segment_data) if segment_mode != consts.MODE_BYTE else consts.MODE_BYTE
    if segment_mode is not None:
        # Check if user provided mode is applicable for the given segment_data
        if segment_mode < guessed_mode:
            raise ValueError(
                f'The provided mode "{get_mode_name(segment_mode)}" '
                f'is not applicable for {segment_data!r}. '
                f'Proposal: {get_mode_name(guessed_mode)}',
            )
    else:
        segment_mode = guessed_mode
    if segment_mode != consts.MODE_BYTE:
        segment_encoding = None
    char_count = segment_length
    buff = Buffer()
    append_bits = buff.append_bits

    if segment_mode == consts.MODE_NUMERIC:
        # ISO/IEC 18004:2015(E) -- 7.4.3 Numeric mode (page 25) The input data string is divided into groups of three
        # digits, and each group is converted to its 10-bit binary equivalent. If the number of input digits is not an
        # exact multiple of three, the final one or two digits are converted to 4 or 7 bits respectively.
        for i in range(0, segment_length, 3):
            chunk = segment_data[i:i + 3]
            append_bits(int(chunk), len(chunk) * 3 + 1)

    elif segment_mode == consts.MODE_ALPHANUMERIC:
        # ISO/IEC 18004:2015(E) -- 7.4.4 Alphanumeric mode (page 26)
        to_byte = consts.ALPHANUMERIC_CHARS.find
        for i in range(0, segment_length, 2):
            chunk = segment_data[i:i + 2]
            # Input data characters are divided into groups of two characters which are encoded as 11-bit binary codes.
            # The character value of the first character is multiplied by 45 and the character value of the second digit
            # is added to the product. The sum is then converted to an 11-bit binary number.
            if len(chunk) > 1:
                append_bits(to_byte(chunk[0]) * 45 + to_byte(chunk[1]), 11)
            else:
                # If the number of input data characters is not a multiple of two, the character value of the final
                # character is encoded as a 6-bit binary number.
                append_bits(to_byte(chunk), 6)

    elif segment_mode == consts.MODE_BYTE:
        # ISO/IEC 18004:2015(E) -- 7.4.5 Byte mode (page 27)
        for b in segment_data:
            append_bits(b, 8)

    else:
        # ISO/IEC 18004:2015(E) -- 7.4.6 Kanji mode (page 29)
        for i in range(0, segment_length, 2):
            code = (segment_data[i] << 8) | segment_data[i + 1]
            if 0x8140 <= code <= 0x9ffc:
                # 1. a) For characters with Shift JIS values from 8140HEX to 9FFCHEX:
                # Subtract 8140HEX from Shift JIS value;
                diff = code - 0x8140
            elif 0xe040 <= code <= 0xebbf:
                # 2. a) For characters with Shift JIS values from E040HEX to EBBFHEX:
                # Subtract C140HEX from Shift JIS value;
                diff = code - 0xc140
            else:  # pragma: no cover
                raise ValueError(f'Invalid Kanji bytes: {code}')
            # b) Multiply most significant byte of result by C0HEX;
            # c) Add least significant byte to product from b);
            # d) Convert result to a 13-bit binary string.
            append_bits(((diff >> 8) * 0xc0) + (diff & 0xff), 13)

    return _Segment(buff.getbits(), char_count, segment_mode, segment_encoding)


def prepare_data_segments(content, mode):
    segments = Segments()
    add_segment = segments.add_segment
    if not isinstance(content, (str, bytes, int)):
        raise TypeError(content)
    add_segment(make_segment(content, mode))
    return segments
