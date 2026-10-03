import os.path

from omcore import check
from omcore import typedvalues as tv

from ... import llm


##


class TargetCwd(tv.UniqueScalarTypedValue[str], final=True):
    def __post_init__(self) -> None:
        check.non_empty_str(self.v)
        check.arg(os.path.isabs(self.v))


class InitialLlmOptions(tv.UniqueScalarTypedValue[llm.Options], final=True):
    pass
