import os.path

import pytest


@pytest.fixture(scope='session')
def pulldown_cmark_root() -> str:
    return os.path.join(os.path.dirname(__file__), 'pulldown-cmark')
