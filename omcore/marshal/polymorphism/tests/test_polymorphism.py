import dataclasses as dc

from ...api.contexts import MarshalContext
from ...api.contexts import MarshalFactoryContext
from ...api.contexts import UnmarshalContext
from ...api.contexts import UnmarshalFactoryContext
from ...api.runtime import Runtime
from ...factories.multi import MultiMarshalerFactory
from ...factories.multi import MultiUnmarshalerFactory
from ...objects.dataclasses import DataclassMarshalerFactory
from ...objects.dataclasses import DataclassUnmarshalerFactory
from ...objects.marshal import ObjectMarshalerFactory
from ...objects.unmarshal import ObjectUnmarshalerFactory
from ...singular.primitives import PRIMITIVE_MARSHALER_FACTORY
from ...singular.primitives import PRIMITIVE_UNMARSHALER_FACTORY
from ..api import FieldTypeTagging
from ..api import Impl
from ..api import Polymorphism
from ..api import WrapperTypeTagging
from ..marshal import PolymorphismMarshalerFactory
from ..unmarshal import PolymorphismUnmarshalerFactory


@dc.dataclass(frozen=True)
class PB:
    a: str


@dc.dataclass(frozen=True)
class PS0(PB):
    b: str


@dc.dataclass(frozen=True)
class PS1(PB):
    b: int


@dc.dataclass(frozen=True)
class PS2(PB):
    b: PB


P_POLYMORPHISM = Polymorphism(
    PB,
    [
        Impl(PS0, 's0'),
        Impl(PS1, 's1'),
        Impl(PS2, 's2'),
    ],
)


def _test_polymorphism(tt):
    rt = Runtime(
        marshaler_factory=MultiMarshalerFactory(
            PolymorphismMarshalerFactory(P_POLYMORPHISM, tt),
            ObjectMarshalerFactory(),
            DataclassMarshalerFactory(),
            PRIMITIVE_MARSHALER_FACTORY,
        ),
        unmarshaler_factory=MultiUnmarshalerFactory(
            PolymorphismUnmarshalerFactory(P_POLYMORPHISM, tt),
            ObjectUnmarshalerFactory(),
            DataclassUnmarshalerFactory(),
            PRIMITIVE_UNMARSHALER_FACTORY,
        ),
    )

    o = PS2('0', PS1('1', 420))

    mfc = MarshalFactoryContext(runtime=rt)
    mc = MarshalContext(runtime=rt)
    v = mfc.make_marshaler(PB).marshal(mc, o)
    print(v)

    ufc = UnmarshalFactoryContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    o2 = ufc.make_unmarshaler(PB).unmarshal(uc, v)
    print(o2)


def test_polymorphism_wrapper():
    _test_polymorphism(WrapperTypeTagging())


def test_polymorphism_field():
    _test_polymorphism(FieldTypeTagging('$type'))
