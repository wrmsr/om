from ....sqldrivers.dbapi.compliance.bindings import DbapiComplianceBinding
from ....sqldrivers.dbapi.compliance.suites import DbapiComplianceSuite
from ... import dbapi
from ..dbs import DB_KWARGS


class TestDbapiCompliance(DbapiComplianceSuite):
    BINDING = DbapiComplianceBinding(
        module=dbapi,
        connect=lambda: dbapi.connect(**DB_KWARGS),
    )
