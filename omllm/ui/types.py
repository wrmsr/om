import uuid

from omcore import check
from omcore import lang
from omcore import typedvalues as tv

from .. import llm


with lang.auto_proxy_import(globals()):
    pass


##


class UiId(tv.UniqueScalarTypedValue[uuid.UUID], final=True):
    def __post_init__(self) -> None:
        check.isinstance(self.v, uuid.UUID)


class RequestedCwd(tv.UniqueScalarTypedValue[str], final=True):
    """
    The working directory as asked for - `--cwd` - spelled in the target's namespace and resolved there at the agent's
    setup, which is where the resolved one lives: on the agent's tool environment.
    """

    def __post_init__(self) -> None:
        check.non_empty_str(self.v)


class InitialLlmOptions(tv.UniqueScalarTypedValue[llm.Options], final=True):
    pass
