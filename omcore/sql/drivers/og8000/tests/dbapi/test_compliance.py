import typing as ta

import pytest

from .....dbapi.compliance.bindings import DbapiComplianceBinding
from .....dbapi.compliance.suites import DbapiComplianceSuite
from ... import dbapi


class TestDbapiCompliance(DbapiComplianceSuite):
    _binding: ta.ClassVar[DbapiComplianceBinding]

    def binding(self) -> DbapiComplianceBinding:
        return self._binding

    @pytest.fixture(scope='class', autouse=True)
    @classmethod
    def _setup_binding(cls, _database):
        cls._binding = DbapiComplianceBinding(
            module=dbapi,
            connect=lambda: dbapi.connect(**_database),
        )
