import typing as ta


##


class JqError(Exception):
    pass


class JqCompileError(JqError):
    pass


class JqLexError(JqCompileError):
    def __init__(self, message: str, *, offset: int | None = None) -> None:
        super().__init__(message)

        self.message = message
        self.offset = offset

    def __str__(self) -> str:
        if self.offset is None:
            return self.message
        return f'{self.message} at offset {self.offset}'


class JqParseError(JqCompileError):
    def __init__(self, message: str, *, offset: int | None = None) -> None:
        super().__init__(message)

        self.message = message
        self.offset = offset

    def __str__(self) -> str:
        if self.offset is None:
            return self.message
        return f'{self.message} at offset {self.offset}'


class JqNameError(JqCompileError):
    pass


class JqUnsupportedError(JqCompileError):
    pass


class JqRuntimeError(JqError):
    @property
    def payload(self) -> ta.Any:
        return str(self)


class JqTypeError(JqRuntimeError, TypeError):
    pass


class JqValueError(JqRuntimeError, ValueError):
    pass


class JqCycleError(JqValueError):
    pass


class JqPathError(JqRuntimeError):
    pass


class JqInputError(JqRuntimeError):
    pass


class JqInputEofError(JqInputError):
    @property
    def payload(self) -> str:
        return 'break'


class JqRegexError(JqRuntimeError):
    pass


class JqRegexUnavailableError(JqRegexError):
    pass


class JqRecursionError(JqRuntimeError, RecursionError):
    pass


class JqStructureError(JqRuntimeError):
    pass


class JqThrownError(JqRuntimeError):
    def __init__(self, value: ta.Any) -> None:
        super().__init__(value)

        self.value = value

    @property
    def payload(self) -> ta.Any:
        return self.value
