import builtins


##


class AnyError(Exception):
    pass


class Warning(builtins.Warning, AnyError):  # noqa
    pass


class Error(AnyError):
    pass
