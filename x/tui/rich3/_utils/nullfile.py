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
import types
import typing as ta


##


class NullFile(ta.IO[str]):
    def close(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    def read(self, __n: int = 1) -> str:
        return ''

    def readable(self) -> bool:
        return False

    def readline(self, __limit: int = 1) -> str:
        return ''

    def readlines(self, __hint: int = 1) -> list[str]:
        return []

    def seek(self, __offset: int, __whence: int = 1) -> int:
        return 0

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        return 0

    def truncate(self, __size: int | None = 1) -> int:
        return 0

    def writable(self) -> bool:
        return False

    def writelines(self, __lines: ta.Iterable[str]) -> None:  # noqa
        pass

    def __next__(self) -> str:
        return ''

    def __iter__(self) -> ta.Iterator[str]:
        return iter([''])

    def __enter__(self) -> ta.IO[str]:
        return self

    def __exit__(
            self,
            __t: type[BaseException] | None,
            __value: BaseException | None,
            __traceback: types.TracebackType | None,
    ) -> None:
        pass

    def write(self, text: str) -> int:
        return 0

    def flush(self) -> None:
        pass

    def fileno(self) -> int:
        return -1


NULL_FILE = NullFile()
