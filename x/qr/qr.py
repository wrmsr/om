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
#
# https://github.com/heuer/segno/tree/1.6.6
import codecs
import collections
import contextlib
import itertools
import operator
import re
import sys  # noqa

import segno  # noqa

from . import consts


##


def get_mode_name(mode_const):
    for name, val in consts.MODE_MAPPING.items():
        if val == mode_const:
            return name
    raise ValueError(f'Unknown mode "{mode_const}"')


def version_range(version):
    # ISO/IEC 18004:2015(E)
    # Table 3 — Number of bits in character count indicator for QR Code (page 23)
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


class _Segment(tuple):
    __slots__ = ()

    def __new__(cls, bits, char_count, mode, encoding=None):
        return tuple.__new__(cls, (bits, char_count, mode, encoding))

    bits = property(operator.itemgetter(0))
    char_count = property(operator.itemgetter(1))
    mode = property(operator.itemgetter(2))
    encoding = property(operator.itemgetter(3))


class Segments:
    __slots__ = ('bit_length', 'modes', 'segments')

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

    def bit_length_with_overhead(self, version, eci, is_sa=False):
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


def prepare_data(content, mode):
    segments = Segments()
    add_segment = segments.add_segment
    if not isinstance(content, (str, bytes, int)):
        raise TypeError(content)
    add_segment(make_segment(content, mode))
    return segments


def boost_error_level(version, error, segments, eci, is_sa=False):
    if error not in (consts.ERROR_LEVEL_H, None) and len(segments) == 1:
        levels = [consts.ERROR_LEVEL_L, consts.ERROR_LEVEL_M, consts.ERROR_LEVEL_Q, consts.ERROR_LEVEL_H]
        if version < 1:
            raise RuntimeError
        data_length = segments.bit_length_with_overhead(version, eci, is_sa=is_sa)
        for error_level in levels[levels.index(error) + 1:]:
            if consts.SYMBOL_CAPACITY[version][error_level] >= data_length:
                error = error_level
            else:
                break
    return error


def get_eci_assignment_number(encoding):
    try:
        return consts.ECI_ASSIGNMENT_NUM[codecs.lookup(encoding).name]
    except KeyError:
        raise ValueError(f'Unknown ECI assignment number for encoding "{encoding}".')


def write_segment(buff, segment, ver, ver_range, eci=False):
    mode = segment.mode
    append_bits = buff.append_bits
    # Write ECI header if requested
    if (
            eci and
            mode == consts.MODE_BYTE and
            segment.encoding != consts.DEFAULT_BYTE_ENCODING
    ):
        append_bits(consts.MODE_ECI, 4)
        append_bits(get_eci_assignment_number(segment.encoding), 8)
    if ver is None:  # QR Code
        append_bits(mode, 4)
    elif ver > consts.VERSION_M1:  # Micro QR Code (M1 has no mode indicator)
        raise RuntimeError
    # Character count indicator
    append_bits(segment.char_count, consts.CHAR_COUNT_INDICATOR_LENGTH[mode][ver_range])
    buff.extend(segment.bits)


# ISO/IEC 18004:2015(E) -- Table 2 — Mode indicators for QR Code (page 23)
TERMINATOR_LENGTH = {
    None: 4,  # QR Codes, all versions
}


def write_terminator(buff, capacity, ver, length):
    # ISO/IEC 18004:2015 -- 7.4.9 Terminator (page 32)
    buff.extend([0] * min(capacity - length, TERMINATOR_LENGTH[ver]))


def write_padding_bits(buff, version, length):
    # ISO/IEC 18004:2015(E) - 7.4.10 Bit stream to codeword conversion -- page 32
    # [...] All codewords are 8 bits in length, except for the final data symbol character in Micro QR Code versions M1
    # and M3 symbols, which is 4 bits in length. If the bit stream length is such that it does not end at a codeword
    # boundary, padding bits with binary value 0 shall be added after the final bit (least significant bit) of the data
    # stream to extend it to the codeword boundary. [...]
    buff.extend([0] * (8 - (length % 8)))


def write_pad_codewords(buff, version, capacity, length):
    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 32) The message bit stream shall then be
    # extended to fill the data capacity of the symbol corresponding to the Version and Error Correction Level, as
    # defined in Table 8, by adding the Pad Codewords 11101100 and 00010001 alternately. For Micro QR Code versions M1
    # and M3 symbols, the final data codeword is 4 bits long. The Pad Codeword used in the final data symbol character
    # position in Micro QR Code versions M1 and M3 symbols shall be represented as 0000.
    write = buff.extend
    pad_codewords = ((1, 1, 1, 0, 1, 1, 0, 0), (0, 0, 0, 1, 0, 0, 0, 1))
    for i in range(capacity // 8 - length // 8):
        write(pad_codewords[i % 2])


# Finder pattern (includes separator around each side!)
_FINDER_PATTERN = (
    (0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0),
    (0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0),
    (0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1, 0x0),
    (0x0, 0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0),
    (0x0, 0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0),
    (0x0, 0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0),
    (0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1, 0x0),
    (0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0),
    (0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0),
)


def add_finder_patterns(matrix, width, height):
    is_square = width == height
    corners = ((0, 0), (0, len(matrix) - 8), (-8, 0))  # Upper left, upper right, bottom left
    if is_square and width < 21:
        corners = ((0, 0),)
    finder_range = range(8)
    for i, j in corners:
        offset = 1 if i == 0 else 0
        sepoffset = 0 if j != 0 else 1
        for r in finder_range:
            matrix[i + r][j:j + 8] = _FINDER_PATTERN[offset + r][sepoffset:sepoffset + 8]


def add_timing_pattern(matrix):
    j, stop = (6, len(matrix) - 8)
    col = matrix[j]
    bit = 0x1
    for i in range(8, stop):
        matrix[i][j] = bit
        col[i] = bit
        bit ^= 0x1



def add_alignment_patterns(matrix, width, height):
    is_square = width == height
    version = (width - 17) // 4  # QR Codes: version * 4 +  17 == width / height of the matrix w/o border
    if is_square and version < 2:  # QR Codes version < 2 don't have alignment patterns
        return
    pattern = (
        0x1, 0x1, 0x1, 0x1, 0x1,
        0x1, 0x0, 0x0, 0x0, 0x1,
        0x1, 0x0, 0x1, 0x0, 0x1,
        0x1, 0x0, 0x0, 0x0, 0x1,
        0x1, 0x1, 0x1, 0x1, 0x1,
    )
    positions = consts.ALIGNMENT_POS[version - 2]
    alignment_range = range(5)
    min_pos = positions[0]
    max_pos = positions[-1]
    finder_positions = ((min_pos, min_pos), (min_pos, max_pos), (max_pos, min_pos))
    for x, y in itertools.product(positions, repeat=2):
        if (x, y) in finder_positions:
            continue
        # The x and y values represent the center of the alignment pattern
        i, j = x - 2, y - 2
        for r in alignment_range:
            matrix[i + r][j:j + 5] = pattern[r * 5:r * 5 + 5]


def add_codewords(matrix, codewords, version):
    matrix_size = len(matrix)
    # Necessary for M1 and M3: The algorithm would start at the upper right corner, see
    # <https://github.com/heuer/segno/issues/36>
    inc = 0
    idx = 0  # Pointer to the current codeword
    # ISO/IEC 18004:2015(E) - page 48
    # [...] An alternative method for placement in the symbol [...] is to regard the interleaved codeword sequence as a
    # single bit stream, which is placed (starting with the most significant bit) in the two-module wide columns
    # alternately upwards and downwards from the right to left of the symbol. [...]
    codeword_length = len(codewords)
    range_two = range(2)
    for right in range(matrix_size - 1, 0, -2):
        if right <= 6:
            right -= 1
        for vertical in range(matrix_size):
            for z in range_two:
                j = right - z
                upwards = ((right + inc) & 2) == 0
                upwards ^= j < 6
                i = (matrix_size - 1 - vertical) if upwards else vertical
                row = matrix[i]
                if row[j] == 0x2 and idx < codeword_length:
                    row[j] = codewords[idx]
                    idx += 1
    if idx != len(codewords):  # pragma: no cover
        raise ValueError(
            f'Internal error: Adding codewords to matrix failed. Added {idx} of {len(codewords)} codewords',
        )


def make_blocks(ec_infos, buff):
    codewords = buff.toints()
    data_blocks, error_blocks = [], []
    append_data_block = data_blocks.append
    append_error_block = error_blocks.append
    gen_log = consts.GALIOS_LOG
    gen_exp = consts.GALIOS_EXP
    for ec_info in ec_infos:
        num_error_words = ec_info.num_total - ec_info.num_data
        gen = consts.GEN_POLY[num_error_words]
        range_error_words = range(num_error_words)
        for i in range(ec_info.num_blocks):
            block = bytearray(itertools.islice(codewords, ec_info.num_data))
            append_data_block(block)
            len_data = len(block)
            error_block = bytearray(block)
            error_block.extend([0] * num_error_words)
            # Extended synthetic division, see http://research.swtch.com/field
            for k in range(len_data):
                coef = error_block[k]
                if coef != 0:  # log(0) is undefined
                    lcoef = gen_log[coef]
                    for n in range_error_words:
                        error_block[k + n + 1] ^= gen_exp[lcoef + gen[n]]
            append_error_block(error_block[len_data:])
    return data_blocks, error_blocks


def make_final_message(version, error, buff):
    def to_binary(val, length=8):
        return ((val >> i) & 1 for i in reversed(range(length)))

    ec_infos = consts.ECC[version][error]
    data_blocks, error_blocks = make_blocks(ec_infos, buff)
    cw_four = None
    res = Buffer()
    # Write codewords
    res.extend(itertools.chain(*map(to_binary, (x for x in itertools.chain.from_iterable(itertools.zip_longest(*data_blocks)) if x is not None))))
    if cw_four is not None:
        res.extend(cw_four)
    # Write error codewords
    res.extend(itertools.chain(*map(to_binary, (x for x in itertools.chain.from_iterable(itertools.zip_longest(*error_blocks)) if x is not None))))
    # ISO/IEC 18004:2015(E) -- 7.6 Constructing the final message codeword sequence
    # [...] In certain QR Code versions, however, where the number of modules available for data and error correction
    # codewords is not an exact multiple of 8, there may be a need for 3, 4 or 7 Remainder Bits to be appended to the
    # final message bit stream in order to fill exactly the number of modules in the encoding region
    remainder = 0
    if version in (2, 3, 4, 5, 6):
        remainder = 7
    elif version in (14, 15, 16, 17, 18, 19, 20, 28, 29, 30, 31, 32, 33, 34):
        remainder = 3
    elif version in (21, 22, 23, 24, 25, 26, 27):
        remainder = 4
    res.extend(b'\0' * remainder)
    return res


def calc_matrix_size(ver):
    return ver * 4 + 17 if ver > 0 else (ver + 4) * 2 + 9


_MAX_PENALTY_SCORE = sys.maxsize


def make_matrix(width, height, reserve_regions=True, add_timing=True):
    is_square = width == height
    is_micro = is_square and width < 21
    if is_micro:
        raise RuntimeError
    row = [0x2] * width
    matrix = tuple(bytearray(row) for i in range(height))
    if reserve_regions:
        if is_square and width > 41:  # QR Codes < version 7 don't have a version pattern
            # Reserve version pattern areas
            for i in range(6):
                row = matrix[i]
                # Upper right
                row[-11] = 0x0
                row[-10] = 0x0
                row[-9] = 0x0
                # Lower left
                matrix[-11][i] = 0x0
                matrix[-10][i] = 0x0
                matrix[-9][i] = 0x0
        # Reserve format pattern areas
        row_eight = matrix[8]
        for i in range(9):
            matrix[i][8] = 0x0  # Upper left
            row_eight[i] = 0x0  # Upper bottom
            matrix[-i][8] = 0x0  # Bottom left
            row_eight[-i] = 0x0  # Upper right
    if add_timing:
        # ISO/IEC 18004:2015 -- 6.3.5 Timing pattern (page 17)
        add_timing_pattern(matrix)
    return matrix


def get_data_mask_functions():
    # i = row position, j = col position; (i, j) = (0, 0) = upper left corner
    def fn0(i, j):
        return (i + j) & 0x1 == 0

    def fn1(i, j):
        return i & 0x1 == 0

    def fn2(i, j):
        return j % 3 == 0

    def fn3(i, j):
        return (i + j) % 3 == 0

    def fn4(i, j):
        return (i // 2 + j // 3) & 0x1 == 0

    def fn5(i, j):
        tmp = i * j
        return (tmp & 0x1) + (tmp % 3) == 0

    def fn6(i, j):
        tmp = i * j
        return ((tmp & 0x1) + (tmp % 3)) & 0x1 == 0

    def fn7(i, j):
        return (((i + j) & 0x1) + (i * j) % 3) & 0x1 == 0

    return fn0, fn1, fn2, fn3, fn4, fn5, fn6, fn7


def find_and_apply_best_mask(matrix, width, height, proposed_mask=None):
    # ISO/IEC 18004:2015 -- 7.8.3.1 Evaluation of QR Code symbols (page 53/54)
    # The data mask pattern which results in the lowest penalty score shall be selected for the symbol.
    is_better = operator.lt
    best_score = _MAX_PENALTY_SCORE
    eval_mask = evaluate_mask
    is_micro = width == height and width < 21
    if is_micro:
        raise RuntimeError
    # Matrix to check if a module belongs to the encoding region or to the function patterns
    function_matrix = make_matrix(width, height)
    add_finder_patterns(function_matrix, width, height)
    add_alignment_patterns(function_matrix, width, height)
    function_matrix[-8][8] = 0x1

    def is_encoding_region(i, j):
        return function_matrix[i][j] > 0x1

    mask_patterns = get_data_mask_functions()
    # If the user supplied a mask pattern, the evaluation step is skipped
    if proposed_mask is not None:
        apply_mask(matrix, mask_patterns[proposed_mask], width, height,
                   is_encoding_region)
        return proposed_mask, matrix

    best_matrix = None
    for mask_number, mask_pattern in enumerate(mask_patterns):
        m = [ba[:] for ba in matrix]
        apply_mask(m, mask_pattern, width, height, is_encoding_region)
        # NOTE: DO NOT add format / version info in advance of evaluation
        # See ISO/IEC 18004:2015(E) -- 7.8. Data masking (page 50)
        score = eval_mask(m, width, height)
        if is_better(score, best_score):
            best_score = score
            best_pattern = mask_number
            best_matrix = tuple(m)
    return best_pattern, best_matrix


def apply_mask(matrix, mask_pattern, width, height, is_encoding_region):
    width_range = range(width)
    for i in range(height):
        row = matrix[i]
        for j in width_range:
            if is_encoding_region(i, j):
                row[j] ^= mask_pattern(i, j)


def evaluate_mask(matrix, width, height):
    return sum(mask_scores(matrix, width, height))


def mask_scores(matrix, width, height):
    n3_pattern = bytearray((0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1))

    def n3_pattern_occurrences(seq):
        count = 0
        idx = seq.find(n3_pattern)
        while idx != -1:
            offset = idx + 7
            if (
                    idx in (0, qr_size - 7) or
                    not any(seq[max(idx - 4, 0):min(idx, qr_size)]) or
                    not any(seq[max(offset, 0):min(offset + 4, qr_size)])
            ):
                count += 40  # N3 = 40
            else:
                # Found no / not enough light modules, start at next possible match:
                #                   v
                # dark light dark dark dark light dark
                #                   ^
                offset = idx + 4
            idx = seq.find(n3_pattern, offset)
        return count

    score_n1 = 0
    score_n2 = 0
    score_n3 = 0
    assert width == height
    qr_size = width
    qr_module_range = range(qr_size)
    dark_module_counter = 0
    last_row = None
    # Collects the bytes column-wise (required to calculate score N3)
    n3_column = bytearray(qr_size)
    for i in qr_module_range:
        row = matrix[i]
        row_prev_bit = -1
        col_prev_bit = -1
        # N1
        n1_row_counter = 0
        n1_col_counter = 0
        for j in qr_module_range:
            row_current_bit = row[j]
            col_current_bit = matrix[j][i]
            n3_column[j] = col_current_bit
            dark_module_counter += row_current_bit
            # N1 -- row-wise
            if row_current_bit == row_prev_bit:
                n1_row_counter += 1
            else:
                if n1_row_counter >= 5:
                    score_n1 += n1_row_counter - 2
                n1_row_counter = 1
            # N1 -- col-wise
            if col_current_bit == col_prev_bit:
                n1_col_counter += 1
            else:
                if n1_col_counter >= 5:
                    score_n1 += n1_col_counter - 2
                n1_col_counter = 1
            # N2
            if last_row and j and row_current_bit == row_prev_bit == last_row[j] == last_row[j - 1]:
                score_n2 += 3
            row_prev_bit = row_current_bit
            col_prev_bit = col_current_bit
        last_row = row
        # N3
        score_n3 += n3_pattern_occurrences(row)
        score_n3 += n3_pattern_occurrences(n3_column)
        # N1
        if n1_row_counter >= 5:
            score_n1 += n1_row_counter - 2
        if n1_col_counter >= 5:
            score_n1 += n1_col_counter - 2
    # N4
    percent = float(dark_module_counter) / (qr_size ** 2)
    score_n4 = 10 * int(abs(percent * 100 - 50) / 5)  # N4 = 10
    return score_n1, score_n2, score_n3, score_n4


def calc_format_info(version, error, mask_pattern):
    fmt = mask_pattern
    if error == consts.ERROR_LEVEL_L:
        fmt += 0x08
    elif error == consts.ERROR_LEVEL_H:
        fmt += 0x10
    elif error == consts.ERROR_LEVEL_Q:
        fmt += 0x18
    format_info = consts.FORMAT_INFO[fmt]
    return format_info


def add_format_info(matrix, version, error, mask_pattern):
    # 14: most significant bit
    #  0: least significant bit
    #
    # QR Code format info:                                          Micro QR format info
    # col 0                col 7              col matrix[-1]      col 1
    #                        0                       |               |                [ ]
    #                        1                                                         0
    #                        2                                                         1
    #                        3                                                         2
    #                        4                                                         3
    #                        5                                                         4
    #                       [ ]                                                        5
    #                        6                                                         6
    # 14 13 12 11 10 9 [ ] 8 7    ...  7 6 5 4 3 2 1 0              14 13 12 11 10 9 8 7
    #
    # ...
    #                       [ ] (dark module)
    #                        8
    #                        9
    #                       10
    #                       11
    #                       12
    #                       13
    #                       14
    is_micro = version < 1
    format_info = calc_format_info(version, error, mask_pattern)
    voffset = int(is_micro)
    hoffset = voffset
    row_eight = matrix[8]
    for i in range(8):
        vbit = (format_info >> i) & 0x01
        hbit = (format_info >> (14 - i)) & 0x01
        if i == 6 and not is_micro:  # Timing pattern
            voffset += 1
            hoffset = 1
        # vertical row, upper left corner
        matrix[i + voffset][8] = vbit
        # horizontal row, upper left corner
        row_eight[i + hoffset] = hbit
        if not is_micro:
            # horizontal row, upper right corner
            row_eight[-1 - i] = vbit
            # vertical row, bottom left corner
            matrix[-1 - i][8] = hbit
    if not is_micro:
        # Dark module
        matrix[-8][8] = 0x1


def add_version_info(matrix, version):
    #
    # module  0 = least significant bit
    # module 17 = most significant bit
    #
    # Figure 27 — Version information positioning (page 58)
    #
    # Lower left                    Upper right
    # ----------                    -----------
    #  0  3  6  9 12 15               0  1  2
    #  1  4  7 10 13 16               3  4  5
    #  2  5  8 11 14 17               6  7  8
    #                                 9 10 11
    #                                12 13 14
    #                                15 16 17
    #
    if version < 7:
        return
    version_info = consts.VERSION_INFO[version - 7]
    for i in range(6):
        bit1 = (version_info >> (i * 3)) & 0x01
        bit2 = (version_info >> ((i * 3) + 1)) & 0x01
        bit3 = (version_info >> ((i * 3) + 2)) & 0x01
        # Lower left
        matrix[-11][i] = bit1
        matrix[-10][i] = bit2
        matrix[-9][i] = bit3
        # Upper right
        row = matrix[i]
        row[-11] = bit1
        row[-10] = bit2
        row[-9] = bit3


Code = collections.namedtuple('Code', 'matrix version error mask segments')


def _encode(
        segments,
        error,
        version,
        eci,
        boost_error,
        sa_info=None,
):
    mask = None
    sa_mode = sa_info is not None
    buff = Buffer()
    ver = None
    ver_range = version_range(version)
    if boost_error:
        error = boost_error_level(version, error, segments, eci, is_sa=sa_mode)
    if sa_mode:
        # ISO/IEC 18004:2015(E) -- 8 Structured Append (page 59)
        for i in sa_info[:3]:
            buff.append_bits(i, 4)
        buff.append_bits(sa_info.parity, 8)
    # ISO/IEC 18004:2015(E) -- 7.4 Data encoding (page 22)
    for segment in segments:
        write_segment(buff, segment, ver, ver_range, eci)
    capacity = consts.SYMBOL_CAPACITY[version][error]
    # ISO/IEC 18004:2015(E) -- 7.4.9 Terminator (page 32)
    write_terminator(buff, capacity, ver, len(buff))
    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 34)
    write_padding_bits(buff, version, len(buff))
    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 34)
    write_pad_codewords(buff, version, capacity, len(buff))
    # ISO/IEC 18004:2015(E) -- 7.6 Constructing the final message codeword sequence (page 45)
    buff = make_final_message(version, error, buff)
    # Matrix with timing pattern and reserved format / version regions
    width = calc_matrix_size(version)
    height = width
    matrix = make_matrix(width, height)
    # ISO/IEC 18004:2015 -- 6.3.3 Finder pattern (page 16)
    add_finder_patterns(matrix, width, height)
    # ISO/IEC 18004:2015 -- 6.3.6 Alignment patterns (page 17)
    add_alignment_patterns(matrix, width, height)
    # ISO/IEC 18004:2015 -- 7.7 Codeword placement in matrix (page 46)
    add_codewords(matrix, buff, version)
    # ISO/IEC 18004:2015(E) -- 7.8.2 Data mask patterns (page 50)
    # ISO/IEC 18004:2015(E) -- 7.8.3 Evaluation of data masking results (page 53)
    mask, matrix = find_and_apply_best_mask(matrix, width, height, mask)
    # ISO/IEC 18004:2015(E) -- 7.9 Format information (page 55)
    add_format_info(matrix, version, error, mask)
    # ISO/IEC 18004:2015(E) -- 7.10 Version information (page 58)
    add_version_info(matrix, version)
    return Code(matrix, version, error, mask, segments)


class DataOverflowError(ValueError):
    pass


def find_version(
        segments,
        error,
        eci,
        is_sa=False,
):
    min_version = 1
    max_version = 40
    if min_version < 1:
        raise RuntimeError
    for version in range(min_version, max_version + 1):
        if error is None:
            error = consts.ERROR_LEVEL_L
        try:
            if consts.SYMBOL_CAPACITY[version][error] >= segments.bit_length_with_overhead(version, eci, is_sa):
                return version
        except KeyError:
            pass
    raise DataOverflowError(f'Data too large. No QR Code can handle the provided data')


def encode(content):
    error = None
    mode = None
    encoding = None
    eci = False
    version = None
    boost_error = True

    segments = prepare_data(content, mode)
    guessed_version = find_version(segments, error, eci)
    if version is None:
        version = guessed_version
    elif guessed_version > version:
        raise DataOverflowError(
            f'The provided data does not fit into version "{get_version_name(version)}"'
            f'Proposal: version {get_version_name(guessed_version)}',
        )
    if error is None:
        error = consts.ERROR_LEVEL_L
    return _encode(segments, error, version, eci, boost_error)


##


class QRCode:
    __slots__ = ('_error', '_matrix_size', '_mode', '_version', 'mask', 'matrix')

    def __init__(self, code):
        matrix = code.matrix
        self.matrix = matrix
        self.mask = code.mask
        self._matrix_size = len(matrix[0]), len(matrix)
        self._version = code.version
        self._error = code.error
        self._mode = code.segments[0].mode if len(code.segments) == 1 else None


def make(content):
    return QRCode(encode(content))


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


def matrix_iter(matrix, matrix_size, scale=1, border=None):
    check_valid_border(border)
    scale = int(scale)
    check_valid_scale(scale)
    border = get_border(matrix_size, border)
    width, height = matrix_size
    border_row = [0x0] * width
    width_range, height_range = range(-border, width + border), range(-border, height + border)
    for i in height_range:
        r = matrix[i] if 0 <= i < height else border_row
        row = tuple(itertools.chain.from_iterable(itertools.repeat(r[j] if 0 <= j < width else 0x0, scale) for j in width_range))
        for s in itertools.repeat(None, scale):
            yield row


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


def write_terminal_compact(matrix, matrix_size, out, border=None):
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


def write_terminal(matrix, matrix_size, out, border=None):
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


##


def _main() -> None:
    # qr = segno.make_qr('Your text or URL here')
    qr = make('Your text or URL here')

    # qr.terminal()
    # qr.terminal(compact=True)

    write_terminal(qr.matrix, qr._matrix_size, sys.stdout)
    write_terminal_compact(qr.matrix, qr._matrix_size, sys.stdout)


if __name__ == '__main__':
    _main()
