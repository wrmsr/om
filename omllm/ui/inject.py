import uuid

from omcore import inject as inj

from .types import UiId


##


def bind_ui() -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.append(inj.bind(UiId(uuid.uuid7())))

    return inj.as_elements(*lst)
