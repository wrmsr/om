import dataclasses as dc
import datetime
import decimal
import enum
import fractions
import typing as ta

from ...api.configs import ConfigRegistry
from ...api.contexts import MarshalContext
from ...api.contexts import MarshalFactoryContext
from ...api.contexts import UnmarshalContext
from ...api.contexts import UnmarshalFactoryContext
from ...api.runtime import Runtime
from ...tests.foox import Foox
from ..factories import StandardMarshalerFactory
from ..factories import StandardUnmarshalerFactory


class E(enum.Enum):
    X = enum.auto()
    Y = enum.auto()
    Z = enum.auto()


@dc.dataclass(frozen=True)
class Foo(Foox):
    s: str
    f: Foo | None = None
    e: E | None = None
    frac: fractions.Fraction = fractions.Fraction(1, 9)
    dec: decimal.Decimal = decimal.Decimal('3.140000000000000124344978758017532527446746826171875')
    dt: datetime.datetime = dc.field(default_factory=datetime.datetime.now)
    d: datetime.date = dc.field(default_factory=lambda: datetime.datetime.now().date())  # noqa
    t: datetime.time = dc.field(default_factory=lambda: datetime.datetime.now().time())  # noqa


def test_marshal():
    # reg = Registry()
    # reg.register(spec_of(int), SetType(marshaler=PrimitiveMarshaler()))

    reg = ConfigRegistry()

    for _ in range(3):
        rt = Runtime(
            config_registry=reg,
            marshaler_factory=StandardMarshalerFactory(),
            unmarshaler_factory=StandardUnmarshalerFactory(),
        )

        print()

        obj = Foo([420, 421], 'barf', Foo([1, 2], 'xxx', e=E.Y))
        print(obj)
        print()

        mfc = MarshalFactoryContext(runtime=rt)
        mc = MarshalContext(runtime=rt)
        for _ in range(2):
            mobj = mfc.make_marshaler(type(obj)).marshal(mc, obj)
            print(mobj)
        print()

        ufc = UnmarshalFactoryContext(runtime=rt)
        uc = UnmarshalContext(runtime=rt)
        for _ in range(2):
            uobj = ufc.make_unmarshaler(type(obj)).unmarshal(uc, mobj)  # noqa
            print(uobj)
        print()

        print(ufc.make_unmarshaler(ta.Any).unmarshal(uc, 420))
