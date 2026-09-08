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
import collections
import itertools
import operator
import sys  # noqa
import typing as ta

from omcore import check

from . import consts
from .segments import prepare_data_segments
from .utils import Buffer
from .utils import get_version_name
from .utils import version_range


##


def boost_error_level(
        version,
        error,
        segments,
        eci,
        is_sa=False,
):
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


#


def get_eci_assignment_number(encoding):
    try:
        return consts.ECI_ASSIGNMENT_NUM[codecs.lookup(encoding).name]
    except KeyError:
        raise ValueError(f'Unknown ECI assignment number for encoding "{encoding}".') from None


def write_segment(
        buff,
        segment,
        ver,
        ver_range,
        eci=False,
):
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


#


def write_terminator(
        buff,
        capacity,
        length,
):
    # ISO/IEC 18004:2015 -- 7.4.9 Terminator (page 32)
    buff.extend([0] * min(capacity - length, consts.TERMINATOR_LENGTH))


#


def write_padding_bits(buff, length):
    # ISO/IEC 18004:2015(E) - 7.4.10 Bit stream to codeword conversion -- page 32
    # [...] All codewords are 8 bits in length, except for the final data symbol character in Micro QR Code versions M1
    # and M3 symbols, which is 4 bits in length. If the bit stream length is such that it does not end at a codeword
    # boundary, padding bits with binary value 0 shall be added after the final bit (least significant bit) of the data
    # stream to extend it to the codeword boundary. [...]
    buff.extend([0] * (8 - (length % 8)))


#


def write_pad_codewords(buff, capacity, length):
    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 32) The message bit stream shall then be
    # extended to fill the data capacity of the symbol corresponding to the Version and Error Correction Level, as
    # defined in Table 8, by adding the Pad Codewords 11101100 and 00010001 alternately. For Micro QR Code versions M1
    # and M3 symbols, the final data codeword is 4 bits long. The Pad Codeword used in the final data symbol character
    # position in Micro QR Code versions M1 and M3 symbols shall be represented as 0000.
    write = buff.extend
    pad_codewords = ((1, 1, 1, 0, 1, 1, 0, 0), (0, 0, 0, 1, 0, 0, 0, 1))
    for i in range(capacity // 8 - length // 8):
        write(pad_codewords[i % 2])


#


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
    corners: tuple[tuple[int, int], ...] = ((0, 0), (0, len(matrix) - 8), (-8, 0))  # Upper left, upper right, bottom left  # noqa
    if is_square and width < 21:
        corners = ((0, 0),)
    finder_range = range(8)
    for i, j in corners:
        offset = 1 if i == 0 else 0
        sepoffset = 0 if j != 0 else 1
        for r in finder_range:
            matrix[i + r][j:j + 8] = _FINDER_PATTERN[offset + r][sepoffset:sepoffset + 8]


#


def add_timing_pattern(matrix):
    j, stop = (6, len(matrix) - 8)
    col = matrix[j]
    bit = 0x1
    for i in range(8, stop):
        matrix[i][j] = bit
        col[i] = bit
        bit ^= 0x1


#


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


#


def add_codewords(matrix, codewords):
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


#


def make_blocks(ec_infos, buff):
    codewords = buff.toints()
    data_blocks: list
    error_blocks: list
    data_blocks, error_blocks = [], []
    append_data_block = data_blocks.append
    append_error_block = error_blocks.append
    gen_log = consts.GALIOS_LOG
    gen_exp = consts.GALIOS_EXP
    for ec_info in ec_infos:
        num_error_words = ec_info.num_total - ec_info.num_data
        gen = consts.GEN_POLY[num_error_words]
        range_error_words = range(num_error_words)
        for _ in range(ec_info.num_blocks):
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

    ec_infos = consts.ECC[version][error]  # type: ignore[index]
    data_blocks, error_blocks = make_blocks(ec_infos, buff)
    res = Buffer()
    # Write codewords
    res.extend(itertools.chain(*map(
        to_binary,
        (x for x in itertools.chain.from_iterable(itertools.zip_longest(*data_blocks)) if x is not None),
    )))
    # Write error codewords
    res.extend(itertools.chain(*map(
        to_binary,
        (x for x in itertools.chain.from_iterable(itertools.zip_longest(*error_blocks)) if x is not None),
    )))
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


#


def calc_matrix_size(ver):
    return ver * 4 + 17 if ver > 0 else (ver + 4) * 2 + 9


def make_matrix(
        width,
        height,
        reserve_regions=True,
        add_timing=True,
):
    is_square = width == height
    is_micro = is_square and width < 21
    if is_micro:
        raise RuntimeError
    row: ta.Any = [0x2] * width
    matrix = tuple(bytearray(row) for _ in range(height))
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


#


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


_MAX_PENALTY_SCORE = sys.maxsize


def find_and_apply_best_mask(
        matrix,
        width,
        height,
        proposed_mask=None,
):
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


def apply_mask(
        matrix,
        mask_pattern,
        width,
        height,
        is_encoding_region,
):
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
    check.state(width == height)
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


#


def calc_format_info(error, mask_pattern):
    fmt = mask_pattern
    if error == consts.ERROR_LEVEL_L:
        fmt += 0x08
    elif error == consts.ERROR_LEVEL_H:
        fmt += 0x10
    elif error == consts.ERROR_LEVEL_Q:
        fmt += 0x18
    format_info = consts.FORMAT_INFO[fmt]
    return format_info


def add_format_info(
        matrix,
        version,
        error,
        mask_pattern,
):
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
    format_info = calc_format_info(error, mask_pattern)
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


#


def add_version_info(matrix, version):
    #
    # module  0 = least significant bit
    # module 17 = most significant bit
    #
    # Figure 27 - Version information positioning (page 58)
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


#


Code = collections.namedtuple('Code', [  # noqa
    'matrix',
    'version',
    'error',
    'mask',
    'segments',
])


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
        error = boost_error_level(
            version,
            error,
            segments,
            eci,
            is_sa=sa_mode,
        )

    if sa_mode:
        # ISO/IEC 18004:2015(E) -- 8 Structured Append (page 59)
        for i in sa_info[:3]:
            buff.append_bits(i, 4)
        buff.append_bits(sa_info.parity, 8)

    # ISO/IEC 18004:2015(E) -- 7.4 Data encoding (page 22)
    for segment in segments:
        write_segment(
            buff,
            segment,
            ver,
            ver_range,
            eci,
        )
    capacity = consts.SYMBOL_CAPACITY[version][error]

    # ISO/IEC 18004:2015(E) -- 7.4.9 Terminator (page 32)
    write_terminator(buff, capacity, len(buff))

    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 34)
    write_padding_bits(buff, len(buff))

    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 34)
    write_pad_codewords(buff, capacity, len(buff))

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
    add_codewords(matrix, buff)

    # ISO/IEC 18004:2015(E) -- 7.8.2 Data mask patterns (page 50)
    # ISO/IEC 18004:2015(E) -- 7.8.3 Evaluation of data masking results (page 53)
    mask, matrix = find_and_apply_best_mask(
        matrix,
        width,
        height,
        mask,
    )

    # ISO/IEC 18004:2015(E) -- 7.9 Format information (page 55)
    add_format_info(
        matrix,
        version,
        error,
        mask,
    )

    # ISO/IEC 18004:2015(E) -- 7.10 Version information (page 58)
    add_version_info(matrix, version)

    return Code(
        matrix,
        version,
        error,
        mask,
        segments,
    )


##


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


def encode(
        content,
        *,
        error=None,
        mode=None,
        eci=False,
        version=None,
        boost_error=True,
):
    segments = prepare_data_segments(content, mode)
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
    return _encode(
        segments,
        error,
        version,
        eci,
        boost_error,
    )


##


class QrCode:
    __slots__ = (
        '_error',
        'matrix_size',
        '_mode',
        '_version',
        'mask',
        'matrix',
    )

    def __init__(self, code):
        matrix = code.matrix
        self.matrix = matrix
        self.mask = code.mask
        self.matrix_size = len(matrix[0]), len(matrix)
        self._version = code.version
        self._error = code.error
        self._mode = code.segments[0].mode if len(code.segments) == 1 else None


def make(content):
    return QrCode(encode(content))


##


def _main() -> None:
    # import segno  # noqa
    # qr = segno.make_qr('Your text or URL here')
    qr = make('Your text or URL here')

    # qr.terminal()
    # qr.terminal(compact=True)

    from .writers import write_terminal
    from .writers import write_terminal_compact

    write_terminal(qr.matrix, qr.matrix_size, sys.stdout)
    write_terminal_compact(qr.matrix, qr.matrix_size, sys.stdout)


if __name__ == '__main__':
    _main()
