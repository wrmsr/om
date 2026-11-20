from .bootstrap import SpaceBootstrap
from .collections import SpaceCollections
from .conversions import SpaceConversions
from .objects import SpaceObjects
from .operators import SpaceOperators


##


class ObjectSpace(
    SpaceBootstrap,
    SpaceObjects,
    SpaceCollections,
    SpaceOperators,
    SpaceConversions,
):
    pass
