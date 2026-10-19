# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa


##


REGISTRY_BY_SPEC_KEY = {}
REGISTRY_BY_CLS_NAME = {}


def _register(**kwargs):
    def inner(fn):
        for key in kwargs['spec_keys']:
            if key in REGISTRY_BY_SPEC_KEY:
                raise RuntimeError('Conflicting dataclass cache key')
            REGISTRY_BY_SPEC_KEY[key] = (kwargs, fn)
        REGISTRY_BY_CLS_NAME.update({cn: (kwargs, fn) for cn in kwargs['cls_names']})
        return fn
    return inner


##


IMPLEMENTATION_KEY = 'ec0d825a77daf2010440f2135dbf8d063599428f1d09d40e22d60773f9be3250'


@_register(
    installer_sha1='6248f41581623360303edcbd9a6847690167e599',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('input_audio', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('output_audio', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('x', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('context_over_200k', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('tiers', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'AuthoredCost'),
        ('omllm.modeldb.types', 'OutputCost'),
    ),
)
def _process_dataclass__6248f41581623360303edcbd9a6847690167e599():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
                input_audio=self.input_audio,
                output_audio=self.output_audio,
                x=self.x,
                context_over_200k=self.context_over_200k,
                tiers=self.tiers,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write and
                self.input_audio == other.input_audio and
                self.output_audio == other.output_audio and
                self.x == other.x and
                self.context_over_200k == other.context_over_200k and
                self.tiers == other.tiers
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
            'input_audio',
            'output_audio',
            'x',
            'context_over_200k',
            'tiers',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.input,
                self.output,
                self.reasoning,
                self.cache_read,
                self.cache_write,
                self.input_audio,
                self.output_audio,
                self.x,
                self.context_over_200k,
                self.tiers,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__00__annotation,
            output: __dataclass__init__fields__01__annotation,
            reasoning: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            cache_read: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            cache_write: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            input_audio: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            output_audio: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            x: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            context_over_200k: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            tiers: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)
            __dataclass__object_setattr(self, 'input_audio', input_audio)
            __dataclass__object_setattr(self, 'output_audio', output_audio)
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__object_setattr(self, 'context_over_200k', context_over_200k)
            __dataclass__object_setattr(self, 'tiers', tiers)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"cache_read={self.cache_read!r}")
            parts.append(f"cache_write={self.cache_write!r}")
            parts.append(f"input_audio={self.input_audio!r}")
            parts.append(f"output_audio={self.output_audio!r}")
            parts.append(f"x={self.x!r}")
            parts.append(f"context_over_200k={self.context_over_200k!r}")
            parts.append(f"tiers={self.tiers!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='302fe50504a14b9ccd83c12b9a642cd78bf84d39',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('id', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'missing', None, "
            "False, False, False), (('attachment', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('tool_call', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('release_date', True, True, None, True, True, False, None), 'instance"
            "', 'missing', None, False, False, False), (('last_updated', True, True, None, True, True, False, None), 'i"
            "nstance', 'missing', None, False, False, False), (('modalities', True, True, None, True, True, False, None"
            "), 'instance', 'missing', None, False, False, False), (('open_weights', True, True, None, True, True, Fals"
            "e, None), 'instance', 'missing', None, False, False, False), (('limit', True, True, None, True, True, Fals"
            "e, None), 'instance', 'missing', None, False, False, False), (('family', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('interleaved', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('structured_output', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('temperature', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('knowledge', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('status', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('experimental', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('provider', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('cost', True, True,"
            " None, True, True, False, None), 'instance', 'value', None, False, False, False), (('x', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (Fa"
            "lse,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'AuthoredModel'),
        ('omllm.modeldb.types', 'Model'),
    ),
)
def _process_dataclass__302fe50504a14b9ccd83c12b9a642cd78bf84d39():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                name=self.name,
                attachment=self.attachment,
                reasoning=self.reasoning,
                tool_call=self.tool_call,
                release_date=self.release_date,
                last_updated=self.last_updated,
                modalities=self.modalities,
                open_weights=self.open_weights,
                limit=self.limit,
                family=self.family,
                interleaved=self.interleaved,
                structured_output=self.structured_output,
                temperature=self.temperature,
                knowledge=self.knowledge,
                status=self.status,
                experimental=self.experimental,
                provider=self.provider,
                cost=self.cost,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.name == other.name and
                self.attachment == other.attachment and
                self.reasoning == other.reasoning and
                self.tool_call == other.tool_call and
                self.release_date == other.release_date and
                self.last_updated == other.last_updated and
                self.modalities == other.modalities and
                self.open_weights == other.open_weights and
                self.limit == other.limit and
                self.family == other.family and
                self.interleaved == other.interleaved and
                self.structured_output == other.structured_output and
                self.temperature == other.temperature and
                self.knowledge == other.knowledge and
                self.status == other.status and
                self.experimental == other.experimental and
                self.provider == other.provider and
                self.cost == other.cost and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'name',
            'attachment',
            'reasoning',
            'tool_call',
            'release_date',
            'last_updated',
            'modalities',
            'open_weights',
            'limit',
            'family',
            'interleaved',
            'structured_output',
            'temperature',
            'knowledge',
            'status',
            'experimental',
            'provider',
            'cost',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.id,
                self.name,
                self.attachment,
                self.reasoning,
                self.tool_call,
                self.release_date,
                self.last_updated,
                self.modalities,
                self.open_weights,
                self.limit,
                self.family,
                self.interleaved,
                self.structured_output,
                self.temperature,
                self.knowledge,
                self.status,
                self.experimental,
                self.provider,
                self.cost,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            id: __dataclass__init__fields__00__annotation,
            name: __dataclass__init__fields__01__annotation,
            attachment: __dataclass__init__fields__02__annotation,
            reasoning: __dataclass__init__fields__03__annotation,
            tool_call: __dataclass__init__fields__04__annotation,
            release_date: __dataclass__init__fields__05__annotation,
            last_updated: __dataclass__init__fields__06__annotation,
            modalities: __dataclass__init__fields__07__annotation,
            open_weights: __dataclass__init__fields__08__annotation,
            limit: __dataclass__init__fields__09__annotation,
            family: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            interleaved: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            structured_output: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            temperature: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            knowledge: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            status: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            experimental: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            provider: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            cost: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            x: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'attachment', attachment)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'tool_call', tool_call)
            __dataclass__object_setattr(self, 'release_date', release_date)
            __dataclass__object_setattr(self, 'last_updated', last_updated)
            __dataclass__object_setattr(self, 'modalities', modalities)
            __dataclass__object_setattr(self, 'open_weights', open_weights)
            __dataclass__object_setattr(self, 'limit', limit)
            __dataclass__object_setattr(self, 'family', family)
            __dataclass__object_setattr(self, 'interleaved', interleaved)
            __dataclass__object_setattr(self, 'structured_output', structured_output)
            __dataclass__object_setattr(self, 'temperature', temperature)
            __dataclass__object_setattr(self, 'knowledge', knowledge)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'experimental', experimental)
            __dataclass__object_setattr(self, 'provider', provider)
            __dataclass__object_setattr(self, 'cost', cost)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"attachment={self.attachment!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"tool_call={self.tool_call!r}")
            parts.append(f"release_date={self.release_date!r}")
            parts.append(f"last_updated={self.last_updated!r}")
            parts.append(f"modalities={self.modalities!r}")
            parts.append(f"open_weights={self.open_weights!r}")
            parts.append(f"limit={self.limit!r}")
            parts.append(f"family={self.family!r}")
            parts.append(f"interleaved={self.interleaved!r}")
            parts.append(f"structured_output={self.structured_output!r}")
            parts.append(f"temperature={self.temperature!r}")
            parts.append(f"knowledge={self.knowledge!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"experimental={self.experimental!r}")
            parts.append(f"provider={self.provider!r}")
            parts.append(f"cost={self.cost!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='65d7a2fd272b958b79eb4dedbdb70554e7346355',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('input_audio', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('output_audio', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('x', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Cost'),
    ),
)
def _process_dataclass__65d7a2fd272b958b79eb4dedbdb70554e7346355():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
                input_audio=self.input_audio,
                output_audio=self.output_audio,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write and
                self.input_audio == other.input_audio and
                self.output_audio == other.output_audio and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
            'input_audio',
            'output_audio',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.input,
                self.output,
                self.reasoning,
                self.cache_read,
                self.cache_write,
                self.input_audio,
                self.output_audio,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation,
            output: __dataclass__init__fields__1__annotation,
            reasoning: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_read: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_write: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            input_audio: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            output_audio: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            x: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)
            __dataclass__object_setattr(self, 'input_audio', input_audio)
            __dataclass__object_setattr(self, 'output_audio', output_audio)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"cache_read={self.cache_read!r}")
            parts.append(f"cache_write={self.cache_write!r}")
            parts.append(f"input_audio={self.input_audio!r}")
            parts.append(f"output_audio={self.output_audio!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1948800f1d0c472cf3fbf3e7143e76a1c14f96d1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('input_audio', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('output_audio', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('x', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('tier', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'CostTier'),
    ),
)
def _process_dataclass__1948800f1d0c472cf3fbf3e7143e76a1c14f96d1():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
                input_audio=self.input_audio,
                output_audio=self.output_audio,
                x=self.x,
                tier=self.tier,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write and
                self.input_audio == other.input_audio and
                self.output_audio == other.output_audio and
                self.x == other.x and
                self.tier == other.tier
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
            'input_audio',
            'output_audio',
            'x',
            'tier',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.input,
                self.output,
                self.reasoning,
                self.cache_read,
                self.cache_write,
                self.input_audio,
                self.output_audio,
                self.x,
                self.tier,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation,
            output: __dataclass__init__fields__1__annotation,
            reasoning: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_read: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_write: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            input_audio: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            output_audio: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            x: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            tier: __dataclass__init__fields__8__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)
            __dataclass__object_setattr(self, 'input_audio', input_audio)
            __dataclass__object_setattr(self, 'output_audio', output_audio)
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__object_setattr(self, 'tier', tier)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"cache_read={self.cache_read!r}")
            parts.append(f"cache_write={self.cache_write!r}")
            parts.append(f"input_audio={self.input_audio!r}")
            parts.append(f"output_audio={self.output_audio!r}")
            parts.append(f"x={self.x!r}")
            parts.append(f"tier={self.tier!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7cd6c943c3cb8d84b8ebb60f09746f337d165f6c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('size', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)"
            "))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'CostTierTier'),
    ),
)
def _process_dataclass__7cd6c943c3cb8d84b8ebb60f09746f337d165f6c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                size=self.size,
                type=self.type,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.size == other.size and
                self.type == other.type and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'size',
            'type',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.size,
                self.type,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            size: __dataclass__init__fields__0__annotation,
            type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"size={self.size!r}")
            parts.append(f"type={self.type!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='13bcc298d288bf0eabc36f5aba6f8fd7b8c763e9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('modes', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False"
            ",)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Experimental'),
    ),
)
def _process_dataclass__13bcc298d288bf0eabc36f5aba6f8fd7b8c763e9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                modes=self.modes,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.modes == other.modes and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'modes',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.modes,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            modes: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            x: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'modes', modes)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"modes={self.modes!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4ecd42b82372df1e0a44f4ecc7c8375850af3660',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('cost', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('provider', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False"
            ",)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'ExperimentalMode'),
    ),
)
def _process_dataclass__4ecd42b82372df1e0a44f4ecc7c8375850af3660():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                cost=self.cost,
                provider=self.provider,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.cost == other.cost and
                self.provider == other.provider and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'cost',
            'provider',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.cost,
                self.provider,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            cost: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            provider: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'cost', cost)
            __dataclass__object_setattr(self, 'provider', provider)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"cost={self.cost!r}")
            parts.append(f"provider={self.provider!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e1c36d30449e5c22454e290133c86f9565af7d48',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('body', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('headers', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,"
            ")))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'ExperimentalModeProvider'),
    ),
)
def _process_dataclass__e1c36d30449e5c22454e290133c86f9565af7d48():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                body=self.body,
                headers=self.headers,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.headers == other.headers and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'body',
            'headers',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.body,
                self.headers,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            body: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            headers: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9deae73afb718fd7cf555ad8d1e152b38efe63d9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('field', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fal"
            "se,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Interleaved'),
    ),
)
def _process_dataclass__9deae73afb718fd7cf555ad8d1e152b38efe63d9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                field=self.field,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.field == other.field and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'field',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.field,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            field: __dataclass__init__fields__0__annotation,
            x: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'field', field)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"field={self.field!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='86d9629c6b5dcdf1cecc80123b98ec40fe0df0a7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('input', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Limit'),
    ),
)
def _process_dataclass__86d9629c6b5dcdf1cecc80123b98ec40fe0df0a7():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                context=self.context,
                output=self.output,
                input=self.input,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context == other.context and
                self.output == other.output and
                self.input == other.input and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context',
            'output',
            'input',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.context,
                self.output,
                self.input,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context: __dataclass__init__fields__0__annotation,
            output: __dataclass__init__fields__1__annotation,
            input: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            x: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"context={self.context!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"input={self.input!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ead5d0f6a51b72e11f573f469649448aa883eb57',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Modalities'),
    ),
)
def _process_dataclass__ead5d0f6a51b72e11f573f469649448aa883eb57():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.input,
                self.output,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation,
            output: __dataclass__init__fields__1__annotation,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d5d9d427fef74d0879e392ecfdebbe9ab75185e9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('id', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'missing', None, "
            "False, False, False), (('attachment', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('tool_call', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('release_date', True, True, None, True, True, False, None), 'instance"
            "', 'missing', None, False, False, False), (('last_updated', True, True, None, True, True, False, None), 'i"
            "nstance', 'missing', None, False, False, False), (('modalities', True, True, None, True, True, False, None"
            "), 'instance', 'missing', None, False, False, False), (('open_weights', True, True, None, True, True, Fals"
            "e, None), 'instance', 'missing', None, False, False, False), (('limit', True, True, None, True, True, Fals"
            "e, None), 'instance', 'missing', None, False, False, False), (('family', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('interleaved', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('structured_output', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('temperature', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('knowledge', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('status', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('experimental', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('provider', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((Fal"
            "se,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'ModelBase'),
    ),
)
def _process_dataclass__d5d9d427fef74d0879e392ecfdebbe9ab75185e9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                name=self.name,
                attachment=self.attachment,
                reasoning=self.reasoning,
                tool_call=self.tool_call,
                release_date=self.release_date,
                last_updated=self.last_updated,
                modalities=self.modalities,
                open_weights=self.open_weights,
                limit=self.limit,
                family=self.family,
                interleaved=self.interleaved,
                structured_output=self.structured_output,
                temperature=self.temperature,
                knowledge=self.knowledge,
                status=self.status,
                experimental=self.experimental,
                provider=self.provider,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.name == other.name and
                self.attachment == other.attachment and
                self.reasoning == other.reasoning and
                self.tool_call == other.tool_call and
                self.release_date == other.release_date and
                self.last_updated == other.last_updated and
                self.modalities == other.modalities and
                self.open_weights == other.open_weights and
                self.limit == other.limit and
                self.family == other.family and
                self.interleaved == other.interleaved and
                self.structured_output == other.structured_output and
                self.temperature == other.temperature and
                self.knowledge == other.knowledge and
                self.status == other.status and
                self.experimental == other.experimental and
                self.provider == other.provider
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'name',
            'attachment',
            'reasoning',
            'tool_call',
            'release_date',
            'last_updated',
            'modalities',
            'open_weights',
            'limit',
            'family',
            'interleaved',
            'structured_output',
            'temperature',
            'knowledge',
            'status',
            'experimental',
            'provider',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.id,
                self.name,
                self.attachment,
                self.reasoning,
                self.tool_call,
                self.release_date,
                self.last_updated,
                self.modalities,
                self.open_weights,
                self.limit,
                self.family,
                self.interleaved,
                self.structured_output,
                self.temperature,
                self.knowledge,
                self.status,
                self.experimental,
                self.provider,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            id: __dataclass__init__fields__00__annotation,
            name: __dataclass__init__fields__01__annotation,
            attachment: __dataclass__init__fields__02__annotation,
            reasoning: __dataclass__init__fields__03__annotation,
            tool_call: __dataclass__init__fields__04__annotation,
            release_date: __dataclass__init__fields__05__annotation,
            last_updated: __dataclass__init__fields__06__annotation,
            modalities: __dataclass__init__fields__07__annotation,
            open_weights: __dataclass__init__fields__08__annotation,
            limit: __dataclass__init__fields__09__annotation,
            family: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            interleaved: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            structured_output: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            temperature: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            knowledge: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            status: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            experimental: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            provider: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'attachment', attachment)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'tool_call', tool_call)
            __dataclass__object_setattr(self, 'release_date', release_date)
            __dataclass__object_setattr(self, 'last_updated', last_updated)
            __dataclass__object_setattr(self, 'modalities', modalities)
            __dataclass__object_setattr(self, 'open_weights', open_weights)
            __dataclass__object_setattr(self, 'limit', limit)
            __dataclass__object_setattr(self, 'family', family)
            __dataclass__object_setattr(self, 'interleaved', interleaved)
            __dataclass__object_setattr(self, 'structured_output', structured_output)
            __dataclass__object_setattr(self, 'temperature', temperature)
            __dataclass__object_setattr(self, 'knowledge', knowledge)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'experimental', experimental)
            __dataclass__object_setattr(self, 'provider', provider)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"attachment={self.attachment!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"tool_call={self.tool_call!r}")
            parts.append(f"release_date={self.release_date!r}")
            parts.append(f"last_updated={self.last_updated!r}")
            parts.append(f"modalities={self.modalities!r}")
            parts.append(f"open_weights={self.open_weights!r}")
            parts.append(f"limit={self.limit!r}")
            parts.append(f"family={self.family!r}")
            parts.append(f"interleaved={self.interleaved!r}")
            parts.append(f"structured_output={self.structured_output!r}")
            parts.append(f"temperature={self.temperature!r}")
            parts.append(f"knowledge={self.knowledge!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"experimental={self.experimental!r}")
            parts.append(f"provider={self.provider!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5f9d4bc37357ecc4c34760dfd4edfba3b1116aa0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('npm', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('api', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('shape', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('body', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('headers', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'ModelProvider'),
    ),
)
def _process_dataclass__5f9d4bc37357ecc4c34760dfd4edfba3b1116aa0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                npm=self.npm,
                api=self.api,
                shape=self.shape,
                body=self.body,
                headers=self.headers,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.npm == other.npm and
                self.api == other.api and
                self.shape == other.shape and
                self.body == other.body and
                self.headers == other.headers and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'npm',
            'api',
            'shape',
            'body',
            'headers',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.npm,
                self.api,
                self.shape,
                self.body,
                self.headers,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            npm: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            api: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            shape: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            body: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            headers: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            x: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'npm', npm)
            __dataclass__object_setattr(self, 'api', api)
            __dataclass__object_setattr(self, 'shape', shape)
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"npm={self.npm!r}")
            parts.append(f"api={self.api!r}")
            parts.append(f"shape={self.shape!r}")
            parts.append(f"body={self.body!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c488cd8989ca2e2be9740ccea22948aab4ed68ae',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('id', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'missing', None, F"
            "alse, False, False), (('npm', True, True, None, True, True, False, None), 'instance', 'missing', None, Fal"
            "se, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'missing', None, Fals"
            "e, False, False), (('doc', True, True, None, True, True, False, None), 'instance', 'missing', None, False,"
            " False, False), (('models', True, True, None, True, True, False, None), 'instance', 'missing', None, False"
            ", False, False), (('api', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('x', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.modeldb.types', 'Provider'),
    ),
)
def _process_dataclass__c488cd8989ca2e2be9740ccea22948aab4ed68ae():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                env=self.env,
                npm=self.npm,
                name=self.name,
                doc=self.doc,
                models=self.models,
                api=self.api,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.env == other.env and
                self.npm == other.npm and
                self.name == other.name and
                self.doc == other.doc and
                self.models == other.models and
                self.api == other.api and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'env',
            'npm',
            'name',
            'doc',
            'models',
            'api',
            'x',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.id,
                self.env,
                self.npm,
                self.name,
                self.doc,
                self.models,
                self.api,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            id: __dataclass__init__fields__0__annotation,
            env: __dataclass__init__fields__1__annotation,
            npm: __dataclass__init__fields__2__annotation,
            name: __dataclass__init__fields__3__annotation,
            doc: __dataclass__init__fields__4__annotation,
            models: __dataclass__init__fields__5__annotation,
            api: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            x: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'env', env)
            __dataclass__object_setattr(self, 'npm', npm)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'doc', doc)
            __dataclass__object_setattr(self, 'models', models)
            __dataclass__object_setattr(self, 'api', api)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"env={self.env!r}")
            parts.append(f"npm={self.npm!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"doc={self.doc!r}")
            parts.append(f"models={self.models!r}")
            parts.append(f"api={self.api!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
