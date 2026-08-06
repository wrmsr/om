import typing as ta


##


class MarshalError(Exception):
    pass


class UnhandledTypeError(MarshalError):
    @property
    def spec(self) -> ta.Any:
        return self.args[0]


class ForbiddenError(MarshalError):
    pass


class ForbiddenTypeError(MarshalError):
    @property
    def spec(self) -> ta.Any:
        return self.args[0]
