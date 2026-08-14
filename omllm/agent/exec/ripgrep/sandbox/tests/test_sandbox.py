import sys

import pytest

from ..sandbox import sandboxed_rg


@pytest.mark.skipif(sys.platform != 'darwin', reason='darwin only')
def test_sandboxed_rg():
    out = sandboxed_rg(
        roots=['omcore'],
        args=['foo'],
    )

    print(out)
