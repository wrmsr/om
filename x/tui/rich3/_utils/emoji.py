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
import re
import typing as ta


_ReStringMatch: ta.TypeAlias = re.Match[str]  # regex match object
_ReSubCallable: ta.TypeAlias = ta.Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EmojiSubMethod: ta.TypeAlias = ta.Callable[[_ReSubCallable, str], str]  # Sub method of a compiled re


##


def emoji_replace(
        text: str,
        default_variant: str | None = None,
        _emoji_sub: _EmojiSubMethod = re.compile(r'(:(\S*?)(?:(?:\-)(emoji|text))?:)').sub,
) -> str:
    """Replace emoji code in text."""

    from .._data.emoji import EMOJI

    get_emoji = EMOJI.__getitem__
    variants = {'text': '\ufe0e', 'emoji': '\ufe0f'}
    get_variant = variants.get
    default_variant_code = variants.get(default_variant, '') if default_variant else ''

    def do_replace(match: re.Match[str]) -> str:
        emoji_code, emoji_name, variant = match.groups()
        try:
            return (
                    get_emoji(emoji_name.lower()) +
                    get_variant(variant, default_variant_code)
            )
        except KeyError:
            return emoji_code

    return _emoji_sub(do_replace, text)
