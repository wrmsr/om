# @om-lite
import typing as ta
import weakref

from ....lite.check import check
from ..core import IoPipelineMetadata


##


class DriverIoPipelineMetadata(IoPipelineMetadata):
    def __init__(self, driver: ta.Any) -> None:
        super().__init__()

        self.__driver_ref = weakref.ref(driver)

    @property
    def driver(self) -> ta.Any:
        return check.not_none(self.__driver_ref())
