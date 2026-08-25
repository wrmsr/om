import typing as ta

import pytest

from ....dbapi.compliance.bindings import DbapiComplianceBinding
from ....dbapi.compliance.suites import DbapiComplianceSuite
from ... import omysql


@pytest.fixture(autouse=True)
def _bootstrap(mysql_bootstrap):
    """The binding below connects outside of the fixture system, so the database bootstrap must be forced here."""


class TestDbapiCompliance(DbapiComplianceSuite):
    _binding: ta.ClassVar[DbapiComplianceBinding]

    def binding(self) -> DbapiComplianceBinding:
        return self._binding

    @pytest.fixture(scope='class', autouse=True)
    @classmethod
    def _setup_binding(cls, _databases):
        def _connect():
            params = {k: v for k, v in _databases[0].items() if k not in ('use_unicode', 'local_infile')}
            return omysql.connect(**params)

        cls._binding = DbapiComplianceBinding(
            module=omysql,
            connect=_connect,
            float_type='double',
            # A varbinary column shares varchar's type code, so a blob is used where the description must read as
            # BINARY.
            binary_type='blob',
            timestamp_type='datetime',
            strict_fetch_without_result=False,
            time_is_timedelta=True,
        )
