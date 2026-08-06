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
from ..api import set_polymorphic_from_subclasses
from ..metadata import make_polymorphism_metadata_factories


@set_polymorphic_from_subclasses()
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


def test_polymorphism_helper():
    for _ in range(3):
        pmf, puf = make_polymorphism_metadata_factories()

        rt = Runtime(
            marshaler_factory=MultiMarshalerFactory(
                pmf,
                ObjectMarshalerFactory(),
                DataclassMarshalerFactory(),
                PRIMITIVE_MARSHALER_FACTORY,
            ),
            unmarshaler_factory=MultiUnmarshalerFactory(
                puf,
                ObjectUnmarshalerFactory(),
                DataclassUnmarshalerFactory(),
                PRIMITIVE_UNMARSHALER_FACTORY,
            ),
        )

        o = PS2('0', PS1('1', 420))

        for _ in range(3):
            mfc = MarshalFactoryContext(runtime=rt)
            mc = MarshalContext(runtime=rt)
            v = mfc.make_marshaler(PB).marshal(mc, o)
            print(v)

            ufc = UnmarshalFactoryContext(runtime=rt)
            uc = UnmarshalContext(runtime=rt)
            o2 = ufc.make_unmarshaler(PB).unmarshal(uc, v)
            print(o2)

            assert o2 == o
