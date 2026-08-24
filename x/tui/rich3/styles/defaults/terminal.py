# Copyright (c) 2020 Will McGugan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from ..terminal import TerminalTheme


##


DEFAULT_TERMINAL_THEME = TerminalTheme(
    (255, 255, 255),
    (0, 0, 0),
    [
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
    ],
    [
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ],
)

MONOKAI = TerminalTheme(
    (12, 12, 12),
    (217, 217, 217),
    [
        (26, 26, 26),
        (244, 0, 95),
        (152, 224, 36),
        (253, 151, 31),
        (157, 101, 255),
        (244, 0, 95),
        (88, 209, 235),
        (196, 197, 181),
        (98, 94, 76),
    ],
    [
        (244, 0, 95),
        (152, 224, 36),
        (224, 213, 97),
        (157, 101, 255),
        (244, 0, 95),
        (88, 209, 235),
        (246, 246, 239),
    ],
)

DIMMED_MONOKAI = TerminalTheme(
    (25, 25, 25),
    (185, 188, 186),
    [
        (58, 61, 67),
        (190, 63, 72),
        (135, 154, 59),
        (197, 166, 53),
        (79, 118, 161),
        (133, 92, 141),
        (87, 143, 164),
        (185, 188, 186),
        (136, 137, 135),
    ],
    [
        (251, 0, 31),
        (15, 114, 47),
        (196, 112, 51),
        (24, 109, 227),
        (251, 0, 103),
        (46, 112, 109),
        (253, 255, 185),
    ],
)

NIGHT_OWLISH = TerminalTheme(
    (255, 255, 255),
    (64, 63, 83),
    [
        (1, 22, 39),
        (211, 66, 62),
        (42, 162, 152),
        (218, 170, 1),
        (72, 118, 214),
        (64, 63, 83),
        (8, 145, 106),
        (122, 129, 129),
        (122, 129, 129),
    ],
    [
        (247, 110, 110),
        (73, 208, 197),
        (218, 194, 107),
        (92, 167, 228),
        (105, 112, 152),
        (0, 201, 144),
        (152, 159, 177),
    ],
)

SVG_EXPORT_THEME = TerminalTheme(
    (41, 41, 41),
    (197, 200, 198),
    [
        (75, 78, 85),
        (204, 85, 90),
        (152, 168, 75),
        (208, 179, 68),
        (96, 138, 177),
        (152, 114, 159),
        (104, 160, 179),
        (197, 200, 198),
        (154, 155, 153),
    ],
    [
        (255, 38, 39),
        (0, 130, 61),
        (208, 132, 66),
        (25, 132, 233),
        (255, 44, 122),
        (57, 130, 128),
        (253, 253, 197),
    ],
)
