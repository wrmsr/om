import copy
import dataclasses as dc
import inspect
import typing as ta

import pytest

from ....errors import FieldFnValidationError
from ....errors import FnValidationError
from ...api import field
from ...api import init
from ...api import validate
from ...concerns.frozen import unchecked_frozen_base
from .harness import AotHarness


T = ta.TypeVar('T')


##


class Opaque:
    def __repr__(self):
        raise AssertionError('opaque repr')

    def __eq__(self, other):
        raise AssertionError('opaque equality')

    def __hash__(self):
        raise AssertionError('opaque hash')


def test_opaque_bindings_skip_generation():
    def make(annotation, default):
        class C:
            x: annotation = default  # type: ignore[valid-type]

        return C

    with AotHarness() as aot:
        aot.decorate(make(Opaque(), Opaque()), train=True)
        ann, default = Opaque(), Opaque()
        cls = aot.decorate(make(ann, default))
        assert aot.generated_calls == [True, False]
        assert cls().x is default
        assert cls.__init__.__annotations__['x'] is ann


def test_factory_and_callable_bindings():
    def make(offset):
        class C:
            x: int = field(default_factory=lambda: 10, coerce=lambda v: v + offset, validate=lambda v: v > offset)

        return C

    with AotHarness() as aot:
        aot.decorate(make(1), train=True)
        cls = aot.decorate(make(2))
        assert not aot.generated_calls[-1]
        assert cls().x == 12
        with pytest.raises(FieldFnValidationError):
            cls(-1)


def test_bindings_use_spec_indexes_after_filtering_and_sorting():
    def make(marker):
        class Base:
            @property
            def x(self):
                raise NotImplementedError

        class C(Base):
            cv: ta.ClassVar[int] = 7
            x: int = field(default=1, override=True, repr_priority=20, repr_fn=lambda v: f'{marker}{v}')
            y: int = field(default=2, repr_priority=10, repr_fn=lambda v: f'{marker}{v}')

        return C

    with AotHarness() as aot:
        aot.decorate(make('old'), train=True)
        cls = aot.decorate(make('new'))
        assert not aot.generated_calls[-1]
        obj = cls()
        assert repr(obj).endswith('(y=new2, x=new1)')
        assert obj.x == 1
        obj.x = 4
        assert obj.x == 4
        assert cls.x.fget.__annotations__['return'] is int


@pytest.mark.parametrize('change', ['factory', 'field', 'keyword', 'repr', 'compare', 'coerce', 'validate'])
def test_spec_changes_miss(change):
    def make(changed):
        class C:
            x: int = field(
                **({'default_factory': lambda: 3} if changed and change == 'factory' else {'default': 3}),
                kw_only=changed and change == 'keyword',
                repr=not (changed and change == 'repr'),
                compare=not (changed and change == 'compare'),
                coerce=int if changed and change == 'coerce' else None,
                validate=(lambda v: v > 0) if changed and change == 'validate' else None,
            )

        if changed and change == 'field':
            C.__annotations__ = {**C.__annotations__, 'y': int}
            setattr(C, 'y', 4)
        return C

    with AotHarness() as aot:
        aot.decorate(make(False), train=True)
        cls = aot.decorate(make(True))
        assert aot.generated_calls[-1]
        assert cls().x == 3


@pytest.mark.parametrize('name', ['__init__', '__repr__', '__eq__', '__hash__', '__copy__', '__post_init__'])
@pytest.mark.parametrize('remove', [False, True])
def test_class_observations_include_inactive_generators(name, remove):
    def make(custom):
        class C:
            x: int = 3

        if custom:
            setattr(C, name, lambda *args: None)
        return C

    with AotHarness() as aot:
        aot.decorate(make(remove), train=True)
        cls = aot.decorate(make(not remove))
        assert aot.generated_calls[-1]
        assert cls().x == 3


def test_inherited_post_init():
    class Base:
        pass

    def make():
        class C(Base):
            x: int = 3

        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True)
        setattr(Base, '__post_init__', lambda self: setattr(self, 'x', self.x + 1))
        cls = aot.decorate(make())
        assert aot.generated_calls[-1]
        assert cls().x == 4


def test_order_conflict_still_raises():
    def make():
        class C:
            x: int = 1

        return C

    with AotHarness() as aot:
        aot.decorate(make(), order=True, train=True)
        cls = make()
        setattr(cls, '__lt__', lambda self, other: False)
        with pytest.raises(TypeError, match='__lt__'):
            aot.decorate(cls, order=True)
        assert '__copy__' not in vars(cls)


def test_newly_invalid_field_order_still_raises():
    def make(default):
        class C:
            x: int = field(default=1 if default else dc.MISSING)
            y: int

        return C

    with AotHarness() as aot:
        aot.decorate(make(False), train=True)
        with pytest.raises(TypeError, match='non-default argument'):
            aot.decorate(make(True))


def test_property_init_bindings():
    def make(marker):
        class C:
            events: list = field(default_factory=list)

            @init  # type: ignore[prop-decorator]
            @property
            def first(self):
                self.events.append((marker, 'first'))

            @property
            @init
            def second(self):
                self.events.append((marker, 'second'))

        return C

    with AotHarness() as aot:
        aot.decorate(make('old'), train=True)
        cls = aot.decorate(make('new'))
        assert not aot.generated_calls[-1]
        assert cls().events == [('new', 'first'), ('new', 'second')]


def test_property_init_class_observation():
    def make(as_property):
        class C:
            x: int = 0

            @init
            def bump(self):
                self.x += 1

        if as_property:
            setattr(C, 'bump', property(C.bump))
        return C

    with AotHarness() as aot:
        aot.decorate(make(False), train=True)
        cls = aot.decorate(make(True))
        assert aot.generated_calls[-1]
        assert cls().x == 1


def test_generic_bindings():
    @dc.dataclass()
    class Base(ta.Generic[T]):
        x: T

    def make(annotation):
        class C(Base[annotation]):  # type: ignore[valid-type]
            pass

        return C

    with AotHarness() as aot:
        aot.decorate(make(int), generic_init=True, train=True)
        cls = aot.decorate(make(str), generic_init=True)
        assert not aot.generated_calls[-1]
        assert inspect.signature(cls).parameters['x'].annotation is str
        assert cls('new').x == 'new'


def test_binding_recipes_distinguish_generic_init():
    def make():
        class C:
            x: int

        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True)
        aot.decorate(make(), generic_init=True, train=True)
        plain, generic = [p for p, _ in aot.captured]
        assert plain.ops == generic.ops
        assert plain.bindings != generic.bindings


def test_check_type_binding_validation_precedes_mutation():
    def make(check_type):
        class C:
            x: ta.Any = field(check_type=check_type)

        return C

    with AotHarness() as aot:
        aot.decorate(make((int, None)), train=True)
        cls = aot.decorate(make((str, None)))
        assert not aot.generated_calls[-1]
        assert cls(None).x is None
        assert cls('s').x == 's'
        with pytest.raises(TypeError):
            cls(1)

        invalid = make((str, 'not a type'))
        with pytest.raises(TypeError):
            aot.decorate(invalid)
        assert '__init__' not in vars(invalid)
        assert '__copy__' not in vars(invalid)


def test_class_validation_params():
    def make(other):
        class C:
            x: int
            y: int

            if other:
                @validate
                @staticmethod
                def check(y):
                    return y > 0
            else:
                @validate
                @staticmethod
                def check(x):
                    return x > 0

        return C

    with AotHarness() as aot:
        aot.decorate(make(False), train=True)
        cls = aot.decorate(make(True))
        assert aot.generated_calls[-1]
        assert cls(-1, 1).x == -1
        with pytest.raises(FnValidationError):
            cls(1, -1)


def test_frozen_base_validation_is_live():
    @dc.dataclass()
    class Base:
        x: int = 3

    def make():
        class C(Base):
            pass

        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True)
        getattr(Base, '__dataclass_params__').frozen = True
        with pytest.raises(TypeError, match='non-frozen dataclass from a frozen'):
            aot.decorate(make())
        unchecked_frozen_base(Base)
        cls = aot.decorate(make())
        assert not aot.generated_calls[-1]
        assert cls().x == 3


def test_frozen_slots_and_closure_cells():
    def make():
        class C:
            x: int = 3

        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True, slots=True, frozen=True)
        cls = aot.decorate(make(), slots=True, frozen=True)
        assert not aot.generated_calls[-1]
        obj = cls()
        assert copy.copy(obj) == obj
        with pytest.raises(dc.FrozenInstanceError):
            obj.x = 4
        with pytest.raises(AttributeError):
            obj.extra = 5


def test_incompatible_artifact_falls_back():
    def make():
        class C:
            x: int = 3

        return C

    with AotHarness() as aot:
        aot.decorate(make(), train=True)
        aot.generated.IMPLEMENTATION_KEY = 'old format'
        cls = aot.decorate(make())
        assert aot.generated_calls[-1]
        assert cls().x == 3


@pytest.mark.parametrize('trusted', [False, True])
def test_plan_keyed_artifact_falls_back(trusted):
    def make():
        class C:
            x: int = 3

        return C

    with AotHarness() as aot:
        del aot.generated.IMPLEMENTATION_KEY
        aot.generated.REGISTRY_BY_PLAN_REPR = {}
        cls = aot.decorate(make(), trusted=trusted)
        assert aot.generated_calls == [True]
        assert cls().x == 3


def test_prepare_only_validates_without_installing():
    with AotHarness() as aot:
        class C:
            x: int

        aot.decorate(C, _plan_only=True)
        assert aot.generated_calls == [True]
        assert '__init__' not in vars(C)
        assert '__eq__' not in vars(C)
        assert '__copy__' not in vars(C)

        class Invalid:
            x: int = 1
            y: int

        with pytest.raises(TypeError, match='non-default argument'):
            aot.decorate(Invalid, _plan_only=True)
        assert '__copy__' not in vars(Invalid)


def test_trusted_lookup_uses_names_and_still_binds_values():
    def make(default):
        class C:
            x: int = default

        return C

    with AotHarness() as aot:
        aot.decorate(make(1), train=True)
        aot.generated.REGISTRY_BY_SPEC_KEY.clear()
        cls = aot.decorate(make(2), trusted=True)
        assert not aot.generated_calls[-1]
        assert cls().x == 2

        other = make(3)
        other.__qualname__ = 'Other'
        cls = aot.decorate(other, trusted=True)
        assert aot.generated_calls[-1]
        assert cls().x == 3
