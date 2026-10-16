class SubinterpreterError(RuntimeError):
    pass


class SubinterpreterUnavailableError(SubinterpreterError):
    pass


class SubinterpreterSerializationError(SubinterpreterError):
    pass


class SubinterpreterCodeIdentityError(SubinterpreterError):
    def __init__(self, *, expected: str, actual: str) -> None:
        super().__init__(f'Subinterpreter code identity mismatch: expected {expected!r}, got {actual!r}')

        self._expected = expected
        self._actual = actual

    @property
    def expected(self) -> str:
        return self._expected

    @property
    def actual(self) -> str:
        return self._actual


class SubinterpreterGilError(SubinterpreterError):
    pass


class SubinterpreterRemoteError(SubinterpreterError):
    def __init__(
            self,
            *,
            remote_type: str,
            message: str,
            remote_traceback: str,
    ) -> None:
        super().__init__(f'{remote_type}: {message}')

        self._remote_type = remote_type
        self._message = message
        self._remote_traceback = remote_traceback

    @property
    def remote_type(self) -> str:
        return self._remote_type

    @property
    def message(self) -> str:
        return self._message

    @property
    def remote_traceback(self) -> str:
        return self._remote_traceback


class SubinterpreterExecutionError(SubinterpreterError):
    pass


class SubinterpreterCallTimeoutError(SubinterpreterError, TimeoutError):
    pass
