import pytest

from .... import marshal as msh
from ..dtypes import DATETIME
from ..dtypes import INTEGER
from ..dtypes import STRING
from ..dtypes import UUID
from ..dtypes import Datetime
from ..dtypes import Dtype
from ..dtypes import Integer
from ..dtypes import String
from ..dtypes import Uuid


def test_defaults():
    assert INTEGER == Integer()
    assert STRING == String()
    assert DATETIME == Datetime()
    assert UUID == Uuid()

    assert Integer() == Integer(bits=None)
    assert Integer(bits=64) != Integer()
    assert Integer(bits=64) == Integer(bits=64)
    assert String(length=10) != STRING

    assert hash(Integer(bits=64)) == hash(Integer(bits=64))


def test_details_validated():
    with pytest.raises(Exception):  # noqa
        Integer(bits=24)
    with pytest.raises(Exception):  # noqa
        String(length=0)


def test_marshal_roundtrip():
    for dt in [INTEGER, Integer(bits=64), STRING, String(length=255), DATETIME, UUID]:
        v = msh.marshal(dt, Dtype)
        assert msh.unmarshal(v, Dtype) == dt
