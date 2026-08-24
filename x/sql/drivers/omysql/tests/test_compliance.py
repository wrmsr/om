from ....dbapi.compliance.bindings import DbapiComplianceBinding
from ....dbapi.compliance.suites import DbapiComplianceSuite
from ... import omysql
from .dbs import DATABASES


def _connect():
    params = {k: v for k, v in DATABASES[0].items() if k not in ('use_unicode', 'local_infile')}
    return omysql.connect(**params)


class TestDbapiCompliance(DbapiComplianceSuite):
    BINDING = DbapiComplianceBinding(
        module=omysql,
        connect=_connect,
        float_type='double',
        # A varbinary column shares varchar's type code, so a blob is used where the description must read as BINARY.
        binary_type='blob',
        timestamp_type='datetime',
        strict_fetch_without_result=False,
        time_is_timedelta=True,
    )
