import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import marshal as msh
from ... import typedvalues as tv
from ..qualifiedname import CanQualifiedName
from ..qualifiedname import QualifiedName
from .elements import Element
from .elements import Elements
from .options import TableOption
from .options import TableOptions


##


@dc.dataclass(frozen=True)
class TableDef(lang.Final):
    # The canonical form is always a QualifiedName - a bare name is a one-part name. The `table_def` helper coerces.
    name: QualifiedName
    elements: Elements

    def __post_init__(self) -> None:
        check.isinstance(self.name, QualifiedName)

    _: dc.KW_ONLY

    options: TableOptions = (
        dc.xfield(default_factory=tv.TypedValues, coerce=tv.as_collection) |
        msh.dc_field_options(no_marshal=True, no_unmarshal=True)
    )


def table_def(
        name: CanQualifiedName,
        *elements: Element,
        options: ta.Sequence[TableOption] = (),
) -> TableDef:
    return TableDef(
        QualifiedName.of(name),
        Elements(*elements),
        options=tv.collect(*options),
    )
