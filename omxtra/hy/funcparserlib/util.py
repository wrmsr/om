# Copyright © 2009/2023 Andrey Vlasovskikh
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
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import typing as ta


T = ta.TypeVar('T')


##


def pretty_tree(
        x: T,
        kids: ta.Callable[[T], ta.Sequence[T]],
        show: ta.Callable[[T], str],
) -> str:
    """
    Return a pseudo-graphic tree representation of the object `x`, similar to the output of the Unix `tree` command.
    The text of each object is given by `show`, and its children by `kids`.

    >>> print(pretty_tree(
    ...     ["foo", ["bar", "baz"], "quux"],
    ...     lambda obj: obj if isinstance(obj, list) else [],
    ...     lambda obj: "[]" if isinstance(obj, list) else str(obj),
    ... ))
    []
    |-- foo
    |-- []
    |   |-- bar
    |   `-- baz
    `-- quux
    """

    mid, end, continuation, last, root = '|-- ', '`-- ', '|   ', '    ', ''

    def rec(obj: T, indent: str, sym: str) -> str:
        line = indent + sym + show(obj)

        obj_kids = kids(obj)
        if len(obj_kids) == 0:
            return line

        if sym == mid:
            next_indent = indent + continuation
        elif sym == root:
            next_indent = indent + root
        else:
            next_indent = indent + last

        kid_syms = [mid] * (len(obj_kids) - 1) + [end]
        lines = [rec(kid, next_indent, kid_sym) for kid, kid_sym in zip(obj_kids, kid_syms)]
        return '\n'.join([line, *lines])

    return rec(x, '', root)
