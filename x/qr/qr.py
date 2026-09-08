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


##


ALPHANUMERIC_CHARS = br'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'

DEFAULT_BYTE_ENCODING = 'iso-8859-1'

MODE_NUMERIC = 0x1
MODE_ALPHANUMERIC = 0x2
MODE_BYTE = 0x4
MODE_ECI = 0x7


MODE_MAPPING = {
    'numeric': MODE_NUMERIC,
    'alphanumeric': MODE_ALPHANUMERIC,
    'byte': MODE_BYTE,
}


# Note: These versions must be comparable: Version 1 > M4 > M3 > M2 > M1
VERSION_M4 = 0
VERSION_M3 = -1
VERSION_M2 = -2
VERSION_M1 = -3


# ISO/IEC 18004:2015(E)
# Table 12 — Error correction level indicators for QR Code symbols (page 55)
ERROR_LEVEL_L = 1
ERROR_LEVEL_M = 0
ERROR_LEVEL_Q = 3
ERROR_LEVEL_H = 2


def get_mode_name(mode_const):
    for name, val in MODE_MAPPING.items():
        if val == mode_const:
            return name
    raise ValueError(f'Unknown mode "{mode_const}"')


VERSION_RANGE_01_09 = 1  # Version  1 ..  9
VERSION_RANGE_10_26 = 2  # Version 10 .. 26
VERSION_RANGE_27_40 = 3  # Version 27 .. 40


# ISO/IEC 18004:2015(E) -- Table 2 — Mode indicators for QR Code (page 23)
SUPPORTED_MODES = {
    MODE_NUMERIC: (None, VERSION_M1, VERSION_M2, VERSION_M3, VERSION_M4),
    MODE_ALPHANUMERIC: (None, VERSION_M2, VERSION_M3, VERSION_M4),
    MODE_BYTE: (None, VERSION_M3, VERSION_M4),
    MODE_ECI: (None,),
}

def is_mode_supported(mode, ver):
    ver = None if ver > 0 else ver
    try:
        return ver in SUPPORTED_MODES[mode]
    except KeyError:
        raise ValueError(f'Unknown mode "{mode}"')


def find_minimum_version_for_mode(mode):
    return 1


def version_range(version):
    # ISO/IEC 18004:2015(E)
    # Table 3 — Number of bits in character count indicator for QR Code (page 23)
    if 0 < version < 10:
        return VERSION_RANGE_01_09
    elif 9 < version < 27:
        return VERSION_RANGE_10_26
    elif 26 < version < 41:
        return VERSION_RANGE_27_40
    raise ValueError(f'Unknown version "{version}"')


# ISO/IEC 18004:2015(E)
# Table 3 — Number of bits in character count indicator for QR Code (page 23)
CHAR_COUNT_INDICATOR_LENGTH = {
    MODE_NUMERIC: {
        VERSION_RANGE_01_09: 10,
        VERSION_RANGE_10_26: 12,
        VERSION_RANGE_27_40: 14,
        VERSION_M1: 3,
        VERSION_M2: 4,
        VERSION_M3: 5,
        VERSION_M4: 6,
    },
    MODE_ALPHANUMERIC: {
        VERSION_RANGE_01_09: 9,
        VERSION_RANGE_10_26: 11,
        VERSION_RANGE_27_40: 13,
        VERSION_M2: 3,
        VERSION_M3: 4,
        VERSION_M4: 5,
    },
    MODE_BYTE: {
        VERSION_RANGE_01_09: 8,
        VERSION_RANGE_10_26: 16,
        VERSION_RANGE_27_40: 16,
        VERSION_M3: 4,
        VERSION_M4: 5,
    },
}


# ISO/IEC 18004:2015(E) - 6.4.10 Bit stream to codeword conversion (page 33)
# Table 7 — Number of symbol characters and input data capacity for QR Code
SYMBOL_CAPACITY = {
    VERSION_M1: {None:          20},
    VERSION_M2: {ERROR_LEVEL_L: 40,    ERROR_LEVEL_M: 32},
    VERSION_M3: {ERROR_LEVEL_L: 84,    ERROR_LEVEL_M: 68},
    VERSION_M4: {ERROR_LEVEL_L: 128,   ERROR_LEVEL_M: 112,   ERROR_LEVEL_Q: 80},
    1:    {ERROR_LEVEL_L: 152,   ERROR_LEVEL_M: 128,   ERROR_LEVEL_Q: 104,   ERROR_LEVEL_H: 72},
    2:    {ERROR_LEVEL_L: 272,   ERROR_LEVEL_M: 224,   ERROR_LEVEL_Q: 176,   ERROR_LEVEL_H: 128},
    3:    {ERROR_LEVEL_L: 440,   ERROR_LEVEL_M: 352,   ERROR_LEVEL_Q: 272,   ERROR_LEVEL_H: 208},
    4:    {ERROR_LEVEL_L: 640,   ERROR_LEVEL_M: 512,   ERROR_LEVEL_Q: 384,   ERROR_LEVEL_H: 288},
    5:    {ERROR_LEVEL_L: 864,   ERROR_LEVEL_M: 688,   ERROR_LEVEL_Q: 496,   ERROR_LEVEL_H: 368},
    6:    {ERROR_LEVEL_L: 1088,  ERROR_LEVEL_M: 864,   ERROR_LEVEL_Q: 608,   ERROR_LEVEL_H: 480},
    7:    {ERROR_LEVEL_L: 1248,  ERROR_LEVEL_M: 992,   ERROR_LEVEL_Q: 704,   ERROR_LEVEL_H: 528},
    8:    {ERROR_LEVEL_L: 1552,  ERROR_LEVEL_M: 1232,  ERROR_LEVEL_Q: 880,   ERROR_LEVEL_H: 688},
    9:    {ERROR_LEVEL_L: 1856,  ERROR_LEVEL_M: 1456,  ERROR_LEVEL_Q: 1056,  ERROR_LEVEL_H: 800},
    10:   {ERROR_LEVEL_L: 2192,  ERROR_LEVEL_M: 1728,  ERROR_LEVEL_Q: 1232,  ERROR_LEVEL_H: 976},
    11:   {ERROR_LEVEL_L: 2592,  ERROR_LEVEL_M: 2032,  ERROR_LEVEL_Q: 1440,  ERROR_LEVEL_H: 1120},
    12:   {ERROR_LEVEL_L: 2960,  ERROR_LEVEL_M: 2320,  ERROR_LEVEL_Q: 1648,  ERROR_LEVEL_H: 1264},
    13:   {ERROR_LEVEL_L: 3424,  ERROR_LEVEL_M: 2672,  ERROR_LEVEL_Q: 1952,  ERROR_LEVEL_H: 1440},
    14:   {ERROR_LEVEL_L: 3688,  ERROR_LEVEL_M: 2920,  ERROR_LEVEL_Q: 2088,  ERROR_LEVEL_H: 1576},
    15:   {ERROR_LEVEL_L: 4184,  ERROR_LEVEL_M: 3320,  ERROR_LEVEL_Q: 2360,  ERROR_LEVEL_H: 1784},
    16:   {ERROR_LEVEL_L: 4712,  ERROR_LEVEL_M: 3624,  ERROR_LEVEL_Q: 2600,  ERROR_LEVEL_H: 2024},
    17:   {ERROR_LEVEL_L: 5176,  ERROR_LEVEL_M: 4056,  ERROR_LEVEL_Q: 2936,  ERROR_LEVEL_H: 2264},
    18:   {ERROR_LEVEL_L: 5768,  ERROR_LEVEL_M: 4504,  ERROR_LEVEL_Q: 3176,  ERROR_LEVEL_H: 2504},
    19:   {ERROR_LEVEL_L: 6360,  ERROR_LEVEL_M: 5016,  ERROR_LEVEL_Q: 3560,  ERROR_LEVEL_H: 2728},
    20:   {ERROR_LEVEL_L: 6888,  ERROR_LEVEL_M: 5352,  ERROR_LEVEL_Q: 3880,  ERROR_LEVEL_H: 3080},
    21:   {ERROR_LEVEL_L: 7456,  ERROR_LEVEL_M: 5712,  ERROR_LEVEL_Q: 4096,  ERROR_LEVEL_H: 3248},
    22:   {ERROR_LEVEL_L: 8048,  ERROR_LEVEL_M: 6256,  ERROR_LEVEL_Q: 4544,  ERROR_LEVEL_H: 3536},
    23:   {ERROR_LEVEL_L: 8752,  ERROR_LEVEL_M: 6880,  ERROR_LEVEL_Q: 4912,  ERROR_LEVEL_H: 3712},
    24:   {ERROR_LEVEL_L: 9392,  ERROR_LEVEL_M: 7312,  ERROR_LEVEL_Q: 5312,  ERROR_LEVEL_H: 4112},
    25:   {ERROR_LEVEL_L: 10208, ERROR_LEVEL_M: 8000,  ERROR_LEVEL_Q: 5744,  ERROR_LEVEL_H: 4304},
    26:   {ERROR_LEVEL_L: 10960, ERROR_LEVEL_M: 8496,  ERROR_LEVEL_Q: 6032,  ERROR_LEVEL_H: 4768},
    27:   {ERROR_LEVEL_L: 11744, ERROR_LEVEL_M: 9024,  ERROR_LEVEL_Q: 6464,  ERROR_LEVEL_H: 5024},
    28:   {ERROR_LEVEL_L: 12248, ERROR_LEVEL_M: 9544,  ERROR_LEVEL_Q: 6968,  ERROR_LEVEL_H: 5288},
    29:   {ERROR_LEVEL_L: 13048, ERROR_LEVEL_M: 10136, ERROR_LEVEL_Q: 7288,  ERROR_LEVEL_H: 5608},
    30:   {ERROR_LEVEL_L: 13880, ERROR_LEVEL_M: 10984, ERROR_LEVEL_Q: 7880,  ERROR_LEVEL_H: 5960},
    31:   {ERROR_LEVEL_L: 14744, ERROR_LEVEL_M: 11640, ERROR_LEVEL_Q: 8264,  ERROR_LEVEL_H: 6344},
    32:   {ERROR_LEVEL_L: 15640, ERROR_LEVEL_M: 12328, ERROR_LEVEL_Q: 8920,  ERROR_LEVEL_H: 6760},
    33:   {ERROR_LEVEL_L: 16568, ERROR_LEVEL_M: 13048, ERROR_LEVEL_Q: 9368,  ERROR_LEVEL_H: 7208},
    34:   {ERROR_LEVEL_L: 17528, ERROR_LEVEL_M: 13800, ERROR_LEVEL_Q: 9848,  ERROR_LEVEL_H: 7688},
    35:   {ERROR_LEVEL_L: 18448, ERROR_LEVEL_M: 14496, ERROR_LEVEL_Q: 10288, ERROR_LEVEL_H: 7888},
    36:   {ERROR_LEVEL_L: 19472, ERROR_LEVEL_M: 15312, ERROR_LEVEL_Q: 10832, ERROR_LEVEL_H: 8432},
    37:   {ERROR_LEVEL_L: 20528, ERROR_LEVEL_M: 15936, ERROR_LEVEL_Q: 11408, ERROR_LEVEL_H: 8768},
    38:   {ERROR_LEVEL_L: 21616, ERROR_LEVEL_M: 16816, ERROR_LEVEL_Q: 12016, ERROR_LEVEL_H: 9136},
    39:   {ERROR_LEVEL_L: 22496, ERROR_LEVEL_M: 17728, ERROR_LEVEL_Q: 12656, ERROR_LEVEL_H: 9776},
    40:   {ERROR_LEVEL_L: 23648, ERROR_LEVEL_M: 18672, ERROR_LEVEL_Q: 13328, ERROR_LEVEL_H: 10208}
}


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
                if segment.mode == MODE_BYTE
                and segment.encoding != DEFAULT_BYTE_ENCODING
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
        elif version > VERSION_M1:  # Micro QR Code (M1 has no mode indicator)
            overhead += len(self.modes) * (version + 3)
        # Char count indicator overhead
        ver_range = version_range(version) if version > 0 else version
        overhead += sum(CHAR_COUNT_INDICATOR_LENGTH[mode][ver_range] for mode in self.modes)
        return overhead + self.bit_length


def data_to_bytes(data):
    if not isinstance(data, str):
        raise TypeError(data)
    encoding = DEFAULT_BYTE_ENCODING
    data_ = data.encode(encoding)
    return data_, len(data_), DEFAULT_BYTE_ENCODING


_ALPHANUMERIC_PATTERN = re.compile(br'^[' + re.escape(ALPHANUMERIC_CHARS) + br']+\Z')


def is_alphanumeric(data):
    return _ALPHANUMERIC_PATTERN.match(data)


def find_mode(data):
    if data.isdigit():
        return MODE_NUMERIC
    if is_alphanumeric(data):
        return MODE_ALPHANUMERIC
    return MODE_BYTE


def make_segment(data, mode):
    segment_data, segment_length, segment_encoding = data_to_bytes(data)
    segment_mode = mode

    # If the user prefers BYTE, use BYTE and do not try to find a better mode Necessary since BYTE < KANJI and find_mode
    # may return KANJI as (more) appropriate mode and the encoder throws an exception if "user provided mode" < "found
    # mode"
    guessed_mode = find_mode(segment_data) if segment_mode != MODE_BYTE else MODE_BYTE
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
    if segment_mode != MODE_BYTE:
        segment_encoding = None
    char_count = segment_length
    buff = Buffer()
    append_bits = buff.append_bits

    if segment_mode == MODE_NUMERIC:
        # ISO/IEC 18004:2015(E) -- 7.4.3 Numeric mode (page 25) The input data string is divided into groups of three
        # digits, and each group is converted to its 10-bit binary equivalent. If the number of input digits is not an
        # exact multiple of three, the final one or two digits are converted to 4 or 7 bits respectively.
        for i in range(0, segment_length, 3):
            chunk = segment_data[i:i + 3]
            append_bits(int(chunk), len(chunk) * 3 + 1)

    elif segment_mode == MODE_ALPHANUMERIC:
        # ISO/IEC 18004:2015(E) -- 7.4.4 Alphanumeric mode (page 26)
        to_byte = ALPHANUMERIC_CHARS.find
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

    elif segment_mode == MODE_BYTE:
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
    if error not in (ERROR_LEVEL_H, None) and len(segments) == 1:
        levels = [ERROR_LEVEL_L, ERROR_LEVEL_M, ERROR_LEVEL_Q, ERROR_LEVEL_H]
        if version < 1:
            levels.pop()  # H isn't support by Micro QR Codes
            if version < VERSION_M4:
                levels.pop()  # Error level Q isn't supported by M2 and M3
        data_length = segments.bit_length_with_overhead(version, eci, is_sa=is_sa)
        for error_level in levels[levels.index(error) + 1:]:
            if SYMBOL_CAPACITY[version][error_level] >= data_length:
                error = error_level
            else:
                break
    return error


#
# ISO/IEC 18004:2015(E) -- 7.3.2 Extended Channel Interpretation (ECI) mode (page 20)
#
# <https://strokescribe.com/en/ECI.html>
# ECI       Reference
# ------    ---------
# 000000    Represents the default encodation scheme
# 000001    Represents the GLI encodation scheme of a number of symbologies
#           with characters 0 to 127 being identical to those of
#           ISO/IEC 646 : 1991 IRV (equivalent to ANSI X3.4) and characters
#           128 to 255 being identical to those values of ISO 8859-1
# 000002    An equivalent code table to ECI 000000, without the return-to-GLI 0
#           logic. It is the default encodation scheme for encoders fully
#           compliant with this standard.
# 000003    ISO/IEC 8859-1 Latin alphabet No. 1
# 000004    ISO/IEC 8859-2 Latin alphabet No. 2
# 000005    ISO/IEC 8859-3 Latin alphabet No. 3
# 000006    ISO/IEC 8859-4 Latin alphabet No. 4
# 000007    ISO/IEC 8859-5 Latin/Cyrillic alphabet
# 000008    ISO/IEC 8859-6 Latin/Arabic alphabet
# 000009    ISO/IEC 8859-7 Latin/Greek alphabet
# 000010    ISO/IEC 8859-8 Latin/Hebrew alphabet
# 000011    ISO/IEC 8859-9 Latin alphabet No. 5
# 000012    ISO/IEC 8859-10 Latin alphabet No. 6
# 000013    ISO/IEC 8859-11 Latin/Thai alphabet
# 000014    Reserved
# 000015    ISO/IEC 8859-13 Latin alphabet No. 7 (Baltic Rim)
# 000016    ISO/IEC 8859-14 Latin alphabet No. 8 (Celtic)
# 000017    ISO/IEC 8859-15 Latin alphabet No. 9
# 000018    ISO/IEC 8859-16 Latin alphabet No. 10
# 000019    Reserved
# 000020    Shift JIS (JIS X 0208 Annex 1 + JIS X 0201)
# 000021    Windows 1250 Latin 2 (Central Europe)
# 000022    Windows 1251 Cyrillic
# 000023    Windows 1252 Latin 1
# 000024    Windows 1256 Arabic
# 000025    ISO/IEC 10646 UCS-2 (High order byte first)
# 000026    ISO/IEC 10646 UTF-8 (See information above)
# 000027    ISO/IEC 646:1991 International Reference Version of ISO 7-bit
#           coded character set
# 000028    Big 5 (Taiwan) Chinese Character Set
# 000029    GB (PRC) Chinese Character Set
# 000030    Korean Character Set
ECI_ASSIGNMENT_NUM = {
    # Codecs name (``codecs.lookup(some-charset).name``) -> ECI designator
    'cp437': 1,
    'iso8859-1': 3,
    'iso8859-2': 4,
    'iso8859-3': 5,
    'iso8859-4': 6,
    'iso8859-5': 7,
    'iso8859-6': 8,
    'iso8859-7': 9,
    'iso8859-8': 10,
    'iso8859-9': 11,
    'iso8859-10': 12,
    'iso8859-11': 13,
    'iso8859-13': 15,
    'iso8859-14': 16,
    'iso8859-15': 17,
    'iso8859-16': 18,
    'shift_jis': 20,
    'cp1250': 21,
    'cp1251': 22,
    'cp1252': 23,
    'cp1256': 24,
    'utf-16-be': 25,
    'utf-8': 26,
    'ascii': 27,
    'big5': 28,
    'gb18030': 29, 'gbk': 29,  # GBK is treated as GB-18030
    'euc_kr': 30,
}


def get_eci_assignment_number(encoding):
    try:
        return ECI_ASSIGNMENT_NUM[codecs.lookup(encoding).name]
    except KeyError:
        raise ValueError(f'Unknown ECI assignment number for encoding "{encoding}".')


def write_segment(buff, segment, ver, ver_range, eci=False):
    mode = segment.mode
    append_bits = buff.append_bits
    # Write ECI header if requested
    if eci and mode == MODE_BYTE \
            and segment.encoding != DEFAULT_BYTE_ENCODING:
        append_bits(MODE_ECI, 4)
        append_bits(get_eci_assignment_number(segment.encoding), 8)
    if ver is None:  # QR Code
        append_bits(mode, 4)
    elif ver > VERSION_M1:  # Micro QR Code (M1 has no mode indicator)
        raise RuntimeError
    # Character count indicator
    append_bits(segment.char_count, CHAR_COUNT_INDICATOR_LENGTH[mode][ver_range])
    buff.extend(segment.bits)


# ISO/IEC 18004:2015(E) -- Table 2 — Mode indicators for QR Code (page 23)
TERMINATOR_LENGTH = {
    None: 4,  # QR Codes, all versions
    VERSION_M1: 3,
    VERSION_M2: 5,
    VERSION_M3: 7,
    VERSION_M4: 9
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
    if version not in (VERSION_M1, VERSION_M3):
        buff.extend([0] * (8 - (length % 8)))


def write_pad_codewords(buff, version, capacity, length):
    # ISO/IEC 18004:2015(E) -- 7.4.10 Bit stream to codeword conversion (page 32) The message bit stream shall then be
    # extended to fill the data capacity of the symbol corresponding to the Version and Error Correction Level, as
    # defined in Table 8, by adding the Pad Codewords 11101100 and 00010001 alternately. For Micro QR Code versions M1
    # and M3 symbols, the final data codeword is 4 bits long. The Pad Codeword used in the final data symbol character
    # position in Micro QR Code versions M1 and M3 symbols shall be represented as 0000.
    write = buff.extend
    if version in (VERSION_M1, VERSION_M3):
        write([0] * (capacity - length))
    else:
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


# ISO/IEC 18004:2015 -- Annex E - Position of alignment patterns
# Table E.1 — Row/column coordinates of center module of alignment patterns (page 83)
ALIGNMENT_POS = (
    (6, 18),  # Version 2 (version 1 has no additional alignment patterns)
    (6, 22),  # Version 3
    (6, 26),  # ..
    (6, 30),
    (6, 34),
    (6, 22, 38),  # Version 7
    (6, 24, 42),
    (6, 26, 46),
    (6, 28, 50),
    (6, 30, 54),
    (6, 32, 58),
    (6, 34, 62),
    (6, 26, 46, 66),  # Version 14
    (6, 26, 48, 70),
    (6, 26, 50, 74),
    (6, 30, 54, 78),
    (6, 30, 56, 82),
    (6, 30, 58, 86),
    (6, 34, 62, 90),
    (6, 28, 50, 72, 94),  # Version 21
    (6, 26, 50, 74, 98),
    (6, 30, 54, 78, 102),
    (6, 28, 54, 80, 106),
    (6, 32, 58, 84, 110),
    (6, 30, 58, 86, 114),
    (6, 34, 62, 90, 118),
    (6, 26, 50, 74, 98, 122),  # Version 28
    (6, 30, 54, 78, 102, 126),
    (6, 26, 52, 78, 104, 130),
    (6, 30, 56, 82, 108, 134),
    (6, 34, 60, 86, 112, 138),
    (6, 30, 58, 86, 114, 142),
    (6, 34, 62, 90, 118, 146),
    (6, 30, 54, 78, 102, 126, 150),  # Version 35
    (6, 24, 50, 76, 102, 128, 154),
    (6, 28, 54, 80, 106, 132, 158),
    (6, 32, 58, 84, 110, 136, 162),
    (6, 26, 54, 82, 110, 138, 166),
    (6, 30, 58, 86, 114, 142, 170),  # Version 40
)


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
    positions = ALIGNMENT_POS[version - 2]
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
    inc = 0 if version not in (VERSION_M1, VERSION_M3) else 2
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


# ISO/IEC 18004:2015 -- Annex A - Error detection and correction generator polynomials
# Table A.1 — Generator polynomials for Reed-Solomon error correction codewords (page 73)
GEN_POLY = {
    2: (25, 1),
    5: (113, 164, 166, 119, 10),
    6: (166, 0, 134, 5, 176, 15),
    7: (87, 229, 146, 149, 238, 102, 21),
    8: (175, 238, 208, 249, 215, 252, 196, 28),
    10: (251, 67, 46, 61, 118, 70, 64, 94, 32, 45),
    13: (74, 152, 176, 100, 86, 100, 106, 104, 130, 218, 206, 140, 78),
    14: (199, 249, 155, 48, 190, 124, 218, 137, 216, 87, 207, 59, 22, 91),
    15: (8, 183, 61, 91, 202, 37, 51, 58, 58, 237, 140, 124, 5, 99, 105),
    16: (120, 104, 107, 109, 102, 161, 76, 3, 91, 191, 147, 169, 182, 194, 225, 120),
    17: (43, 139, 206, 78, 43, 239, 123, 206, 214, 147, 24, 99, 150, 39, 243, 163, 136),
    18: (215, 234, 158, 94, 184, 97, 118, 170, 79, 187, 152, 148, 252, 179, 5, 98, 96, 153),
    20: (17, 60, 79, 50, 61, 163, 26, 187, 202, 180, 221, 225, 83, 239, 156, 164, 212, 212, 188, 190),
    22: (210, 171, 247, 242, 93, 230, 14, 109, 221, 53, 200, 74, 8, 172, 98, 80, 219, 134, 160, 105, 165, 231),
    24: (229, 121, 135, 48, 211, 117, 251, 126, 159, 180, 169, 152, 192, 226, 228, 218, 111, 0, 117, 232, 87, 96, 227, 21),  # noqa: E501
    26: (173, 125, 158, 2, 103, 182, 118, 17, 145, 201, 111, 28, 165, 53, 161, 21, 245, 142, 13, 102, 48, 227, 153, 145, 218, 70),  # noqa: E501
    28: (168, 223, 200, 104, 224, 234, 108, 180, 110, 190, 195, 147, 205, 27, 232, 201, 21, 43, 245, 87, 42, 195, 212, 119, 242, 37, 9, 123),  # noqa: E501
    30: (41, 173, 145, 152, 216, 31, 179, 182, 50, 48, 110, 86, 239, 96, 222, 125, 42, 173, 226, 193, 224, 130, 156, 37, 251, 216, 238, 40, 192, 180)  # noqa: E501
}

# GF(256) log
GALIOS_LOG = (
    0, 0, 1, 25, 2, 50, 26, 198, 3, 223, 51, 238, 27, 104, 199, 75, 4, 100,
    224, 14, 52, 141, 239, 129, 28, 193, 105, 248, 200, 8, 76, 113, 5, 138,
    101, 47, 225, 36, 15, 33, 53, 147, 142, 218, 240, 18, 130, 69, 29, 181,
    194, 125, 106, 39, 249, 185, 201, 154, 9, 120, 77, 228, 114, 166, 6, 191,
    139, 98, 102, 221, 48, 253, 226, 152, 37, 179, 16, 145, 34, 136, 54, 208,
    148, 206, 143, 150, 219, 189, 241, 210, 19, 92, 131, 56, 70, 64, 30, 66,
    182, 163, 195, 72, 126, 110, 107, 58, 40, 84, 250, 133, 186, 61, 202, 94,
    155, 159, 10, 21, 121, 43, 78, 212, 229, 172, 115, 243, 167, 87, 7, 112,
    192, 247, 140, 128, 99, 13, 103, 74, 222, 237, 49, 197, 254, 24, 227, 165,
    153, 119, 38, 184, 180, 124, 17, 68, 146, 217, 35, 32, 137, 46, 55, 63,
    209, 91, 149, 188, 207, 205, 144, 135, 151, 178, 220, 252, 190, 97, 242,
    86, 211, 171, 20, 42, 93, 158, 132, 60, 57, 83, 71, 109, 65, 162, 31, 45,
    67, 216, 183, 123, 164, 118, 196, 23, 73, 236, 127, 12, 111, 246, 108,
    161, 59, 82, 41, 157, 85, 170, 251, 96, 134, 177, 187, 204, 62, 90, 203,
    89, 95, 176, 156, 169, 160, 81, 11, 245, 22, 235, 122, 117, 44, 215, 79,
    174, 213, 233, 230, 231, 173, 232, 116, 214, 244, 234, 168, 80, 88, 175
)

# GF(256) antilog
# Inverse of the logarithm table.  Maps integer logarithms to members of the field.
GALIOS_EXP = ([
    1, 2, 4, 8, 16, 32, 64, 128, 29, 58, 116, 232, 205, 135, 19, 38, 76, 152,
    45, 90, 180, 117, 234, 201, 143, 3, 6, 12, 24, 48, 96, 192, 157, 39, 78,
    156, 37, 74, 148, 53, 106, 212, 181, 119, 238, 193, 159, 35, 70, 140, 5,
    10, 20, 40, 80, 160, 93, 186, 105, 210, 185, 111, 222, 161, 95, 190, 97,
    194, 153, 47, 94, 188, 101, 202, 137, 15, 30, 60, 120, 240, 253, 231, 211,
    187, 107, 214, 177, 127, 254, 225, 223, 163, 91, 182, 113, 226, 217, 175,
    67, 134, 17, 34, 68, 136, 13, 26, 52, 104, 208, 189, 103, 206, 129, 31,
    62, 124, 248, 237, 199, 147, 59, 118, 236, 197, 151, 51, 102, 204, 133, 23,
    46, 92, 184, 109, 218, 169, 79, 158, 33, 66, 132, 21, 42, 84, 168, 77, 154,
    41, 82, 164, 85, 170, 73, 146, 57, 114, 228, 213, 183, 115, 230, 209, 191,
    99, 198, 145, 63, 126, 252, 229, 215, 179, 123, 246, 241, 255, 227, 219,
    171, 75, 150, 49, 98, 196, 149, 55, 110, 220, 165, 87, 174, 65, 130, 25,
    50, 100, 200, 141, 7, 14, 28, 56, 112, 224, 221, 167, 83, 166, 81, 162, 89,
    178, 121, 242, 249, 239, 195, 155, 43, 86, 172, 69, 138, 9, 18, 36, 72,
    144, 61, 122, 244, 245, 247, 243, 251, 235, 203, 139, 11, 22, 44, 88, 176,
    125, 250, 233, 207, 131, 27, 54, 108, 216, 173, 71, 142,
] * 2)


def make_blocks(ec_infos, buff):
    codewords = buff.toints()
    data_blocks, error_blocks = [], []
    append_data_block = data_blocks.append
    append_error_block = error_blocks.append
    gen_log = GALIOS_LOG
    gen_exp = GALIOS_EXP
    for ec_info in ec_infos:
        num_error_words = ec_info.num_total - ec_info.num_data
        gen = GEN_POLY[num_error_words]
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


# ISO/IEC 18004:2015(E) -- Table 9 — Error correction characteristics for QR Code (page 38)
# ISO/IEC 23941:2022(E) -- Table 8 — Error correction characteristics for rMQR (page 29)
EC = collections.namedtuple('EC', 'num_blocks num_total num_data')


ECC = {
    VERSION_M1: {None: (EC(1, 5, 3),)},
    VERSION_M2: {ERROR_LEVEL_L: (EC(1, 10, 5),), ERROR_LEVEL_M: (EC(1, 10, 4),)},
    VERSION_M3: {ERROR_LEVEL_L: (EC(1, 17, 11),), ERROR_LEVEL_M: (EC(1, 17, 9),)},
    VERSION_M4: {ERROR_LEVEL_L: (EC(1, 24, 16),), ERROR_LEVEL_M: (EC(1, 24, 14),),
                 ERROR_LEVEL_Q: (EC(1, 24, 10),)},
    1: {
        ERROR_LEVEL_L: (EC(1, 26, 19),), ERROR_LEVEL_M: (EC(1, 26, 16),),
        ERROR_LEVEL_Q: (EC(1, 26, 13),), ERROR_LEVEL_H: (EC(1, 26, 9),)},
    2: {
        ERROR_LEVEL_L: (EC(1, 44, 34),), ERROR_LEVEL_M: (EC(1, 44, 28),),
        ERROR_LEVEL_Q: (EC(1, 44, 22),), ERROR_LEVEL_H: (EC(1, 44, 16),)},
    3: {
        ERROR_LEVEL_L: (EC(1, 70, 55),), ERROR_LEVEL_M: (EC(1, 70, 44),),
        ERROR_LEVEL_Q: (EC(2, 35, 17),), ERROR_LEVEL_H: (EC(2, 35, 13),)},
    4: {
        ERROR_LEVEL_L: (EC(1, 100, 80),), ERROR_LEVEL_M: (EC(2, 50, 32),),
        ERROR_LEVEL_Q: (EC(2, 50, 24),),  ERROR_LEVEL_H: (EC(4, 25, 9),)},
    5: {
        ERROR_LEVEL_L: (EC(1, 134, 108),), ERROR_LEVEL_M: (EC(2, 67, 43),),
        ERROR_LEVEL_Q: (EC(2, 33, 15), EC(2, 34, 16)),
        ERROR_LEVEL_H: (EC(2, 33, 11), EC(2, 34, 12))},
    6: {
        ERROR_LEVEL_L: (EC(2, 86, 68),), ERROR_LEVEL_M: (EC(4, 43, 27),),
        ERROR_LEVEL_Q: (EC(4, 43, 19),), ERROR_LEVEL_H: (EC(4, 43, 15),)},
    7: {
        ERROR_LEVEL_L: (EC(2, 98, 78),), ERROR_LEVEL_M: (EC(4, 49, 31),),
        ERROR_LEVEL_Q: (EC(2, 32, 14), EC(4, 33, 15)),
        ERROR_LEVEL_H: (EC(4, 39, 13), EC(1, 40, 14))},
    8: {
        ERROR_LEVEL_L: (EC(2, 121, 97),),
        ERROR_LEVEL_M: (EC(2, 60, 38), EC(2, 61, 39)),
        ERROR_LEVEL_Q: (EC(4, 40, 18), EC(2, 41, 19)),
        ERROR_LEVEL_H: (EC(4, 40, 14), EC(2, 41, 15))},
    9: {
        ERROR_LEVEL_L: (EC(2, 146, 116),),
        ERROR_LEVEL_M: (EC(3, 58, 36), EC(2, 59, 37)),
        ERROR_LEVEL_Q: (EC(4, 36, 16), EC(4, 37, 17)),
        ERROR_LEVEL_H: (EC(4, 36, 12), EC(4, 37, 13))},
    10: {
        ERROR_LEVEL_L: (EC(2, 86, 68), EC(2, 87, 69)),
        ERROR_LEVEL_M: (EC(4, 69, 43), EC(1, 70, 44)),
        ERROR_LEVEL_Q: (EC(6, 43, 19), EC(2, 44, 20)),
        ERROR_LEVEL_H: (EC(6, 43, 15), EC(2, 44, 16))},
    11: {
        ERROR_LEVEL_L: (EC(4, 101, 81),),
        ERROR_LEVEL_M: (EC(1, 80, 50), EC(4, 81, 51)),
        ERROR_LEVEL_Q: (EC(4, 50, 22), EC(4, 51, 23)),
        ERROR_LEVEL_H: (EC(3, 36, 12), EC(8, 37, 13))},
    12: {
        ERROR_LEVEL_L: (EC(2, 116, 92), EC(2, 117, 93)),
        ERROR_LEVEL_M: (EC(6, 58, 36), EC(2, 59, 37)),
        ERROR_LEVEL_Q: (EC(4, 46, 20), EC(6, 47, 21)),
        ERROR_LEVEL_H: (EC(7, 42, 14), EC(4, 43, 15))},
    13: {
        ERROR_LEVEL_L: (EC(4, 133, 107),),
        ERROR_LEVEL_M: (EC(8, 59, 37), EC(1, 60, 38)),
        ERROR_LEVEL_Q: (EC(8, 44, 20), EC(4, 45, 21)),
        ERROR_LEVEL_H: (EC(12, 33, 11), EC(4, 34, 12))},
    14: {
        ERROR_LEVEL_L: (EC(3, 145, 115), EC(1, 146, 116)),
        ERROR_LEVEL_M: (EC(4, 64, 40), EC(5, 65, 41)),
        ERROR_LEVEL_Q: (EC(11, 36, 16), EC(5, 37, 17)),
        ERROR_LEVEL_H: (EC(11, 36, 12), EC(5, 37, 13))},
    15: {
        ERROR_LEVEL_L: (EC(5, 109, 87), EC(1, 110, 88)),
        ERROR_LEVEL_M: (EC(5, 65, 41), EC(5, 66, 42)),
        ERROR_LEVEL_Q: (EC(5, 54, 24), EC(7, 55, 25)),
        ERROR_LEVEL_H: (EC(11, 36, 12), EC(7, 37, 13))},
    16: {
        ERROR_LEVEL_L: (EC(5, 122, 98), EC(1, 123, 99)),
        ERROR_LEVEL_M: (EC(7, 73, 45), EC(3, 74, 46)),
        ERROR_LEVEL_Q: (EC(15, 43, 19), EC(2, 44, 20)),
        ERROR_LEVEL_H: (EC(3, 45, 15), EC(13, 46, 16))},
    17: {
        ERROR_LEVEL_L: (EC(1, 135, 107), EC(5, 136, 108)),
        ERROR_LEVEL_M: (EC(10, 74, 46), EC(1, 75, 47)),
        ERROR_LEVEL_Q: (EC(1, 50, 22), EC(15, 51, 23)),
        ERROR_LEVEL_H: (EC(2, 42, 14), EC(17, 43, 15))},
    18: {
        ERROR_LEVEL_L: (EC(5, 150, 120), EC(1, 151, 121)),
        ERROR_LEVEL_M: (EC(9, 69, 43), EC(4, 70, 44)),
        ERROR_LEVEL_Q: (EC(17, 50, 22), EC(1, 51, 23)),
        ERROR_LEVEL_H: (EC(2, 42, 14), EC(19, 43, 15))},
    19: {
        ERROR_LEVEL_L: (EC(3, 141, 113), EC(4, 142, 114)),
        ERROR_LEVEL_M: (EC(3, 70, 44), EC(11, 71, 45)),
        ERROR_LEVEL_Q: (EC(17, 47, 21), EC(4, 48, 22)),
        ERROR_LEVEL_H: (EC(9, 39, 13), EC(16, 40, 14))},
    20: {
        ERROR_LEVEL_L: (EC(3, 135, 107), EC(5, 136, 108)),
        ERROR_LEVEL_M: (EC(3, 67, 41), EC(13, 68, 42)),
        ERROR_LEVEL_Q: (EC(15, 54, 24), EC(5, 55, 25)),
        ERROR_LEVEL_H: (EC(15, 43, 15), EC(10, 44, 16))},
    21: {
        ERROR_LEVEL_L: (EC(4, 144, 116), EC(4, 145, 117)),
        ERROR_LEVEL_M: (EC(17, 68, 42),),
        ERROR_LEVEL_Q: (EC(17, 50, 22), EC(6, 51, 23)),
        ERROR_LEVEL_H: (EC(19, 46, 16), EC(6, 47, 17))},
    22: {
        ERROR_LEVEL_L: (EC(2, 139, 111), EC(7, 140, 112)),
        ERROR_LEVEL_M: (EC(17, 74, 46),),
        ERROR_LEVEL_Q: (EC(7, 54, 24), EC(16, 55, 25)),
        ERROR_LEVEL_H: (EC(34, 37, 13),)},
    23: {
        ERROR_LEVEL_L: (EC(4, 151, 121), EC(5, 152, 122)),
        ERROR_LEVEL_M: (EC(4, 75, 47), EC(14, 76, 48)),
        ERROR_LEVEL_Q: (EC(11, 54, 24), EC(14, 55, 25)),
        ERROR_LEVEL_H: (EC(16, 45, 15), EC(14, 46, 16))},
    24: {
        ERROR_LEVEL_L: (EC(6, 147, 117), EC(4, 148, 118)),
        ERROR_LEVEL_M: (EC(6, 73, 45), EC(14, 74, 46)),
        ERROR_LEVEL_Q: (EC(11, 54, 24), EC(16, 55, 25)),
        ERROR_LEVEL_H: (EC(30, 46, 16), EC(2, 47, 17))},
    25: {
        ERROR_LEVEL_L: (EC(8, 132, 106), EC(4, 133, 107)),
        ERROR_LEVEL_M: (EC(8, 75, 47), EC(13, 76, 48)),
        ERROR_LEVEL_Q: (EC(7, 54, 24), EC(22, 55, 25)),
        ERROR_LEVEL_H: (EC(22, 45, 15), EC(13, 46, 16))},
    26: {
        ERROR_LEVEL_L: (EC(10, 142, 114), EC(2, 143, 115)),
        ERROR_LEVEL_M: (EC(19, 74, 46), EC(4, 75, 47)),
        ERROR_LEVEL_Q: (EC(28, 50, 22), EC(6, 51, 23)),
        ERROR_LEVEL_H: (EC(33, 46, 16), EC(4, 47, 17))},
    27: {
        ERROR_LEVEL_L: (EC(8, 152, 122), EC(4, 153, 123)),
        ERROR_LEVEL_M: (EC(22, 73, 45), EC(3, 74, 46)),
        ERROR_LEVEL_Q: (EC(8, 53, 23), EC(26, 54, 24)),
        ERROR_LEVEL_H: (EC(12, 45, 15), EC(28, 46, 16))},
    28: {
        ERROR_LEVEL_L: (EC(3, 147, 117), EC(10, 148, 118)),
        ERROR_LEVEL_M: (EC(3, 73, 45), EC(23, 74, 46)),
        ERROR_LEVEL_Q: (EC(4, 54, 24), EC(31, 55, 25)),
        ERROR_LEVEL_H: (EC(11, 45, 15), EC(31, 46, 16))},
    29: {
        ERROR_LEVEL_L: (EC(7, 146, 116), EC(7, 147, 117)),
        ERROR_LEVEL_M: (EC(21, 73, 45), EC(7, 74, 46)),
        ERROR_LEVEL_Q: (EC(1, 53, 23), EC(37, 54, 24)),
        ERROR_LEVEL_H: (EC(19, 45, 15), EC(26, 46, 16))},
    30: {
        ERROR_LEVEL_L: (EC(5, 145, 115), EC(10, 146, 116)),
        ERROR_LEVEL_M: (EC(19, 75, 47), EC(10, 76, 48)),
        ERROR_LEVEL_Q: (EC(15, 54, 24), EC(25, 55, 25)),
        ERROR_LEVEL_H: (EC(23, 45, 15), EC(25, 46, 16))},
    31: {
        ERROR_LEVEL_L: (EC(13, 145, 115), EC(3, 146, 116)),
        ERROR_LEVEL_M: (EC(2, 74, 46), EC(29, 75, 47)),
        ERROR_LEVEL_Q: (EC(42, 54, 24), EC(1, 55, 25)),
        ERROR_LEVEL_H: (EC(23, 45, 15), EC(28, 46, 16))},
    32: {
        ERROR_LEVEL_L: (EC(17, 145, 115),),
        ERROR_LEVEL_M: (EC(10, 74, 46), EC(23, 75, 47)),
        ERROR_LEVEL_Q: (EC(10, 54, 24), EC(35, 55, 25)),
        ERROR_LEVEL_H: (EC(19, 45, 15), EC(35, 46, 16))},
    33: {
        ERROR_LEVEL_L: (EC(17, 145, 115), EC(1, 146, 116)),
        ERROR_LEVEL_M: (EC(14, 74, 46), EC(21, 75, 47)),
        ERROR_LEVEL_Q: (EC(29, 54, 24), EC(19, 55, 25)),
        ERROR_LEVEL_H: (EC(11, 45, 15), EC(46, 46, 16))},
    34: {
        ERROR_LEVEL_L: (EC(13, 145, 115), EC(6, 146, 116)),
        ERROR_LEVEL_M: (EC(14, 74, 46), EC(23, 75, 47)),
        ERROR_LEVEL_Q: (EC(44, 54, 24), EC(7, 55, 25)),
        ERROR_LEVEL_H: (EC(59, 46, 16), EC(1, 47, 17))},
    35: {
        ERROR_LEVEL_L: (EC(12, 151, 121), EC(7, 152, 122)),
        ERROR_LEVEL_M: (EC(12, 75, 47), EC(26, 76, 48)),
        ERROR_LEVEL_Q: (EC(39, 54, 24), EC(14, 55, 25)),
        ERROR_LEVEL_H: (EC(22, 45, 15), EC(41, 46, 16))},
    36: {
        ERROR_LEVEL_L: (EC(6, 151, 121), EC(14, 152, 122)),
        ERROR_LEVEL_M: (EC(6, 75, 47), EC(34, 76, 48)),
        ERROR_LEVEL_Q: (EC(46, 54, 24), EC(10, 55, 25)),
        ERROR_LEVEL_H: (EC(2, 45, 15), EC(64, 46, 16))},
    37: {
        ERROR_LEVEL_L: (EC(17, 152, 122), EC(4, 153, 123)),
        ERROR_LEVEL_M: (EC(29, 74, 46), EC(14, 75, 47)),
        ERROR_LEVEL_Q: (EC(49, 54, 24), EC(10, 55, 25)),
        ERROR_LEVEL_H: (EC(24, 45, 15), EC(46, 46, 16))},
    38: {
        ERROR_LEVEL_L: (EC(4, 152, 122), EC(18, 153, 123)),
        ERROR_LEVEL_M: (EC(13, 74, 46), EC(32, 75, 47)),
        ERROR_LEVEL_Q: (EC(48, 54, 24), EC(14, 55, 25)),
        ERROR_LEVEL_H: (EC(42, 45, 15), EC(32, 46, 16))},
    39: {
        ERROR_LEVEL_L: (EC(20, 147, 117), EC(4, 148, 118)),
        ERROR_LEVEL_M: (EC(40, 75, 47), EC(7, 76, 48)),
        ERROR_LEVEL_Q: (EC(43, 54, 24), EC(22, 55, 25)),
        ERROR_LEVEL_H: (EC(10, 45, 15), EC(67, 46, 16))},
    40: {
        ERROR_LEVEL_L: (EC(19, 148, 118), EC(6, 149, 119)),
        ERROR_LEVEL_M: (EC(18, 75, 47), EC(31, 76, 48)),
        ERROR_LEVEL_Q: (EC(34, 54, 24), EC(34, 55, 25)),
        ERROR_LEVEL_H: (EC(20, 45, 15), EC(61, 46, 16))},
    'R7x43': {ERROR_LEVEL_M: 48, ERROR_LEVEL_H: 24},
    'R7x59': {ERROR_LEVEL_M: 96, ERROR_LEVEL_H: 56},
    'R7x77': {ERROR_LEVEL_M: 160, ERROR_LEVEL_H: 80},
    'R7x99': {ERROR_LEVEL_M: 224, ERROR_LEVEL_H: 112},
    'R7x139': {ERROR_LEVEL_M: 352, ERROR_LEVEL_H: 192},
    'R9x43': {ERROR_LEVEL_M: 96, ERROR_LEVEL_H: 56},
    'R9x59': {ERROR_LEVEL_M: 168, ERROR_LEVEL_H: 88},
    'R9x77': {ERROR_LEVEL_M: 248, ERROR_LEVEL_H: 136},
    'R9x99': {ERROR_LEVEL_M: 336, ERROR_LEVEL_H: 176},
    'R9x139': {ERROR_LEVEL_M: 504, ERROR_LEVEL_H: 264},
    'R11x27': {ERROR_LEVEL_M: 56, ERROR_LEVEL_H: 40},
    'R11x43': {ERROR_LEVEL_M: 152, ERROR_LEVEL_H: 88},
    'R11x59': {ERROR_LEVEL_M: 248, ERROR_LEVEL_H: 120},
    'R11x77': {ERROR_LEVEL_M: 344, ERROR_LEVEL_H: 184},
    'R11x99': {ERROR_LEVEL_M: 456, ERROR_LEVEL_H: 232},
    'R11x139': {ERROR_LEVEL_M: 672, ERROR_LEVEL_H: 336},
    'R13x27': {ERROR_LEVEL_M: 96, ERROR_LEVEL_H: 56},
    'R13x43': {ERROR_LEVEL_M: 216, ERROR_LEVEL_H: 104},
    'R13x59': {ERROR_LEVEL_M: 304, ERROR_LEVEL_H: 160},
    'R13x77': {ERROR_LEVEL_M: 424, ERROR_LEVEL_H: 232},
    'R13x99': {ERROR_LEVEL_M: 584, ERROR_LEVEL_H: 280},
    'R13x139': {ERROR_LEVEL_M: 848, ERROR_LEVEL_H: 432},
    'R15x43': {ERROR_LEVEL_M: 264, ERROR_LEVEL_H: 120},
    'R15x59': {ERROR_LEVEL_M: 384, ERROR_LEVEL_H: 208},
    'R15x77': {ERROR_LEVEL_M: 536, ERROR_LEVEL_H: 248},
    'R15x99': {ERROR_LEVEL_M: 704, ERROR_LEVEL_H: 384},
    'R15x139': {ERROR_LEVEL_M: 1016, ERROR_LEVEL_H: 552},
    'R17x43': {ERROR_LEVEL_M: 312, ERROR_LEVEL_H: 168},
    'R17x59': {ERROR_LEVEL_M: 448, ERROR_LEVEL_H: 224},
    'R17x77': {ERROR_LEVEL_M: 624, ERROR_LEVEL_H: 304},
    'R17x99': {ERROR_LEVEL_M: 800, ERROR_LEVEL_H: 448},
    'R17x139': {ERROR_LEVEL_M: 1216, ERROR_LEVEL_H: 608},
}


def make_final_message(version, error, buff):
    def to_binary(val, length=8):
        return ((val >> i) & 1 for i in reversed(range(length)))

    ec_infos = ECC[version][error]
    data_blocks, error_blocks = make_blocks(ec_infos, buff)
    cw_four = None
    if version in (VERSION_M1, VERSION_M3):
        # All codewords are 8 bit by default, M1 and M3 symbols use 4 bits
        # to represent the last codeword.
        # datablocks[0] is save since Micro QR Codes use just one datablock and
        # one error block
        cw_four = to_binary(data_blocks[0].pop(-1) >> 4, 4)
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
    # The data mask pattern which results in the lowest penalty score shall
    # be selected for the symbol.
    is_better = operator.lt
    best_score = _MAX_PENALTY_SCORE
    eval_mask = evaluate_mask
    is_micro = width == height and width < 21
    if is_micro:
        raise RuntimeError
    # Matrix to check if a module belongs to the encoding region
    # or to the function patterns
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
            if idx in (0, qr_size - 7) \
                    or not any(seq[max(idx - 4, 0):min(idx, qr_size)]) \
                    or not any(seq[max(offset, 0):min(offset + 4, qr_size)]):
                count += 40  # N3 = 40
            else:
                # Found no / not enough light modules, start at next possible
                # match:
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


FORMAT_INFO = (
    # M: mask 0, mask 1 .. 7
    0x5412, 0x5125, 0x5e7c, 0x5b4b, 0x45f9, 0x40ce, 0x4f97, 0x4aa0,
    # L
    0x77c4, 0x72f3, 0x7daa, 0x789d, 0x662f, 0x6318, 0x6c41, 0x6976,
    # H
    0x1689, 0x13be, 0x1ce7, 0x19d0, 0x0762, 0x0255, 0x0d0c, 0x083b,
    # Q
    0x355f, 0x3068, 0x3f31, 0x3a06, 0x24b4, 0x2183, 0x2eda, 0x2bed,
)


def calc_format_info(version, error, mask_pattern):
    fmt = mask_pattern
    if error == ERROR_LEVEL_L:
        fmt += 0x08
    elif error == ERROR_LEVEL_H:
        fmt += 0x10
    elif error == ERROR_LEVEL_Q:
        fmt += 0x18
    format_info = FORMAT_INFO[fmt]
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


# ISO/IEC 18004:2015 -- Annex D - D.1 Error correction bit calculation
# Table D.1 — Version information bit stream for each version (page 82)
VERSION_INFO = (
    # Version 7, 8, 9 .. 40
    0x07c94, 0x085bc, 0x09a99, 0x0a4d3, 0x0bbf6, 0x0c762, 0x0d847, 0x0e60d,
    0x0f928, 0x10b78, 0x1145d, 0x12a17, 0x13532, 0x149a6, 0x15683, 0x168c9,
    0x177ec, 0x18ec4, 0x191e1, 0x1afab, 0x1b08e, 0x1cc1a, 0x1d33f, 0x1ed75,
    0x1f250, 0x209d5, 0x216f0, 0x228ba, 0x2379f, 0x24b0b, 0x2542e, 0x26a64,
    0x27541, 0x28c69,
)


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
    version_info = VERSION_INFO[version - 7]
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
    ver = version
    ver_range = version
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
    capacity = SYMBOL_CAPACITY[version][error]
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
        min_version = max([find_minimum_version_for_mode(mode) for mode in segments.modes])
    for version in range(min_version, max_version + 1):
        if error is None and version != VERSION_M1:
            error = ERROR_LEVEL_L
        try:
            if SYMBOL_CAPACITY[version][error] >= segments.bit_length_with_overhead(version, eci, is_sa):
                return version
        except KeyError:
            pass
    raise DataOverflowError(f'Data too large. No QR Code can handle the provided data')


def encode(
        content,
):
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
    if error is None and version != VERSION_M1:
        error = ERROR_LEVEL_L
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

    # write_terminal(qr.matrix, qr._matrix_size, sys.stdout)
    write_terminal_compact(qr.matrix, qr._matrix_size, sys.stdout)


if __name__ == '__main__':
    _main()
