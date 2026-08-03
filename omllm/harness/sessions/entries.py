from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class SessionEntry(lang.Abstract, lang.Sealed):
    pass
