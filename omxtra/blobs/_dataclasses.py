# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa
import dataclasses
import reprlib
import types


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
    installer_sha1='69dbf2c452a7b8afc34a5a1be81149dd36987731',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('region', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('virtual_hosted', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.endpoints', 'S3Endpoint'),
    ),
)
def _process_dataclass__69dbf2c452a7b8afc34a5a1be81149dd36987731():
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
                url=self.url,
                region=self.region,
                virtual_hosted=self.virtual_hosted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.region == other.region and
                self.virtual_hosted == other.virtual_hosted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'region',
            'virtual_hosted',
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
                self.url,
                self.region,
                self.virtual_hosted,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url: __dataclass__init__fields__0__annotation,
            region: __dataclass__init__fields__1__annotation,
            virtual_hosted: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'region', region)
            __dataclass__object_setattr(self, 'virtual_hosted', virtual_hosted)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"url={self.url!r}")
            parts.append(f"region={self.region!r}")
            parts.append(f"virtual_hosted={self.virtual_hosted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='87dd8f095d75206942daee08e9e70428e590d027',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('infos', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('prefixes', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('next_token', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.ops', 'ListPage'),
    ),
)
def _process_dataclass__87dd8f095d75206942daee08e9e70428e590d027():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                infos=self.infos,
                prefixes=self.prefixes,
                next_token=self.next_token,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.infos == other.infos and
                self.prefixes == other.prefixes and
                self.next_token == other.next_token
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'infos',
            'prefixes',
            'next_token',
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
                self.infos,
                self.prefixes,
                self.next_token,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            infos: __dataclass__init__fields__0__annotation,
            prefixes: __dataclass__init__fields__1__annotation,
            next_token: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'infos', infos)
            __dataclass__object_setattr(self, 'prefixes', prefixes)
            __dataclass__object_setattr(self, 'next_token', next_token)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"infos={self.infos!r}")
            parts.append(f"prefixes={self.prefixes!r}")
            parts.append(f"next_token={self.next_token!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='abac065e42759dd7f2ce6dd6be24800f6d64fcc5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('status', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('code', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('request_id', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('host_id', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('raw', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.restxml', 'RestXmlError'),
    ),
)
def _process_dataclass__abac065e42759dd7f2ce6dd6be24800f6d64fcc5():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                status=self.status,
                code=self.code,
                message=self.message,
                request_id=self.request_id,
                host_id=self.host_id,
                raw=self.raw,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status == other.status and
                self.code == other.code and
                self.message == other.message and
                self.request_id == other.request_id and
                self.host_id == other.host_id and
                self.raw == other.raw
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'status',
            'code',
            'message',
            'request_id',
            'host_id',
            'raw',
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
                self.status,
                self.code,
                self.message,
                self.request_id,
                self.host_id,
                self.raw,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            status: __dataclass__init__fields__0__annotation,
            code: __dataclass__init__fields__1__annotation,
            message: __dataclass__init__fields__2__annotation,
            request_id: __dataclass__init__fields__3__annotation,
            host_id: __dataclass__init__fields__4__annotation,
            raw: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'code', code)
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'request_id', request_id)
            __dataclass__object_setattr(self, 'host_id', host_id)
            __dataclass__object_setattr(self, 'raw', raw)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status={self.status!r}")
            parts.append(f"code={self.code!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"request_id={self.request_id!r}")
            parts.append(f"host_id={self.host_id!r}")
            parts.append(f"raw={self.raw!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6af8e55c1f478ba5983cb8520f22cf4868073f94',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('member_name', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('wire_name', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('location', True, True, None, True, True, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('xml_namespace', True, True, None, True, True, False, None), 'insta"
            "nce', 'missing', None, False, False, False), (('xml_flattened', True, True, None, True, True, False, None)"
            ", 'instance', 'missing', None, False, False, False), (('xml_attribute', True, True, None, True, True, Fals"
            "e, None), 'instance', 'missing', None, False, False, False), (('list_member_name', True, True, None, True,"
            " True, False, None), 'instance', 'missing', None, False, False, False), (('required', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (Fal"
            "se,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.restxml', 'RestXmlField'),
    ),
)
def _process_dataclass__6af8e55c1f478ba5983cb8520f22cf4868073f94():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                member_name=self.member_name,
                wire_name=self.wire_name,
                type=self.type,
                location=self.location,
                xml_namespace=self.xml_namespace,
                xml_flattened=self.xml_flattened,
                xml_attribute=self.xml_attribute,
                list_member_name=self.list_member_name,
                required=self.required,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.member_name == other.member_name and
                self.wire_name == other.wire_name and
                self.type == other.type and
                self.location == other.location and
                self.xml_namespace == other.xml_namespace and
                self.xml_flattened == other.xml_flattened and
                self.xml_attribute == other.xml_attribute and
                self.list_member_name == other.list_member_name and
                self.required == other.required
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'member_name',
            'wire_name',
            'type',
            'location',
            'xml_namespace',
            'xml_flattened',
            'xml_attribute',
            'list_member_name',
            'required',
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
                self.name,
                self.member_name,
                self.wire_name,
                self.type,
                self.location,
                self.xml_namespace,
                self.xml_flattened,
                self.xml_attribute,
                self.list_member_name,
                self.required,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__00__annotation,
            member_name: __dataclass__init__fields__01__annotation,
            wire_name: __dataclass__init__fields__02__annotation,
            type: __dataclass__init__fields__03__annotation,
            location: __dataclass__init__fields__04__annotation,
            xml_namespace: __dataclass__init__fields__05__annotation,
            xml_flattened: __dataclass__init__fields__06__annotation,
            xml_attribute: __dataclass__init__fields__07__annotation,
            list_member_name: __dataclass__init__fields__08__annotation,
            required: __dataclass__init__fields__09__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'member_name', member_name)
            __dataclass__object_setattr(self, 'wire_name', wire_name)
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'location', location)
            __dataclass__object_setattr(self, 'xml_namespace', xml_namespace)
            __dataclass__object_setattr(self, 'xml_flattened', xml_flattened)
            __dataclass__object_setattr(self, 'xml_attribute', xml_attribute)
            __dataclass__object_setattr(self, 'list_member_name', list_member_name)
            __dataclass__object_setattr(self, 'required', required)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"member_name={self.member_name!r}")
            parts.append(f"wire_name={self.wire_name!r}")
            parts.append(f"type={self.type!r}")
            parts.append(f"location={self.location!r}")
            parts.append(f"xml_namespace={self.xml_namespace!r}")
            parts.append(f"xml_flattened={self.xml_flattened!r}")
            parts.append(f"xml_attribute={self.xml_attribute!r}")
            parts.append(f"list_member_name={self.list_member_name!r}")
            parts.append(f"required={self.required!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8dbb5defbfb244ee469f3de1cbce9250b127d5c5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('method', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('path', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('query', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('headers', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('body', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.restxml', 'RestXmlRequest'),
    ),
)
def _process_dataclass__8dbb5defbfb244ee469f3de1cbce9250b127d5c5():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                method=self.method,
                path=self.path,
                query=self.query,
                headers=self.headers,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.method == other.method and
                self.path == other.path and
                self.query == other.query and
                self.headers == other.headers and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'method',
            'path',
            'query',
            'headers',
            'body',
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
                self.method,
                self.path,
                self.query,
                self.headers,
                self.body,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            method: __dataclass__init__fields__0__annotation,
            path: __dataclass__init__fields__1__annotation,
            query: __dataclass__init__fields__2__annotation,
            headers: __dataclass__init__fields__3__annotation,
            body: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'method', method)
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'query', query)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'body', body)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"method={self.method!r}")
            parts.append(f"path={self.path!r}")
            parts.append(f"query={self.query!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4036a40a19a1198d613aad3bdb47fefea7500f73',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('kind', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('cls', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('elem', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value', None, False, F"
            "alse, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.restxml', 'RestXmlType'),
    ),
)
def _process_dataclass__4036a40a19a1198d613aad3bdb47fefea7500f73():
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
                kind=self.kind,
                cls=self.cls,
                elem=self.elem,
                key=self.key,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.cls == other.cls and
                self.elem == other.elem and
                self.key == other.key
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
            'cls',
            'elem',
            'key',
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
                self.kind,
                self.cls,
                self.elem,
                self.key,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            kind: __dataclass__init__fields__0__annotation,
            cls: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            elem: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            key: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'cls', cls)
            __dataclass__object_setattr(self, 'elem', elem)
            __dataclass__object_setattr(self, 'key', key)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
            parts.append(f"cls={self.cls!r}")
            parts.append(f"elem={self.elem!r}")
            parts.append(f"key={self.key!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cda2587084dfda9d59a341d92cb0f65a06e5d775',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('op', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('attempt', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('kind', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('conditional', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('status', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('code', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('cause', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.retries', 'S3Failure'),
    ),
)
def _process_dataclass__cda2587084dfda9d59a341d92cb0f65a06e5d775():
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
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op=self.op,
                attempt=self.attempt,
                kind=self.kind,
                conditional=self.conditional,
                status=self.status,
                code=self.code,
                cause=self.cause,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op == other.op and
                self.attempt == other.attempt and
                self.kind == other.kind and
                self.conditional == other.conditional and
                self.status == other.status and
                self.code == other.code and
                self.cause == other.cause
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'op',
            'attempt',
            'kind',
            'conditional',
            'status',
            'code',
            'cause',
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
                self.op,
                self.attempt,
                self.kind,
                self.conditional,
                self.status,
                self.code,
                self.cause,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            op: __dataclass__init__fields__0__annotation,
            attempt: __dataclass__init__fields__1__annotation,
            kind: __dataclass__init__fields__2__annotation,
            conditional: __dataclass__init__fields__3__annotation,
            status: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            code: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            cause: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'op', op)
            __dataclass__object_setattr(self, 'attempt', attempt)
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'conditional', conditional)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'code', code)
            __dataclass__object_setattr(self, 'cause', cause)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op={self.op!r}")
            parts.append(f"attempt={self.attempt!r}")
            parts.append(f"kind={self.kind!r}")
            parts.append(f"conditional={self.conditional!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"code={self.code!r}")
            parts.append(f"cause={self.cause!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7e600164f721bb906ccfb5da5f27d9ba8de60b14',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('capabilities', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('copy_dst_if_none_match_header', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('copy_dst_if_match_header', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False), (('no_list_url_encoding', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('unsigned_payload', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('streamed_up"
            "loads', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('pa"
            "rt_size', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "streaming_chunk_size', True, True, None, True, True, False, None), 'instance', 'value', None, False, False"
            ", False), (('list_page_size', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False), (('delete_batch_size', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('request_timeout_s', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.stores', 'S3BlobStore.Config'),
    ),
)
def _process_dataclass__7e600164f721bb906ccfb5da5f27d9ba8de60b14():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
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
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                capabilities=self.capabilities,
                copy_dst_if_none_match_header=self.copy_dst_if_none_match_header,
                copy_dst_if_match_header=self.copy_dst_if_match_header,
                no_list_url_encoding=self.no_list_url_encoding,
                unsigned_payload=self.unsigned_payload,
                streamed_uploads=self.streamed_uploads,
                part_size=self.part_size,
                streaming_chunk_size=self.streaming_chunk_size,
                list_page_size=self.list_page_size,
                delete_batch_size=self.delete_batch_size,
                request_timeout_s=self.request_timeout_s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.capabilities == other.capabilities and
                self.copy_dst_if_none_match_header == other.copy_dst_if_none_match_header and
                self.copy_dst_if_match_header == other.copy_dst_if_match_header and
                self.no_list_url_encoding == other.no_list_url_encoding and
                self.unsigned_payload == other.unsigned_payload and
                self.streamed_uploads == other.streamed_uploads and
                self.part_size == other.part_size and
                self.streaming_chunk_size == other.streaming_chunk_size and
                self.list_page_size == other.list_page_size and
                self.delete_batch_size == other.delete_batch_size and
                self.request_timeout_s == other.request_timeout_s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'capabilities',
            'copy_dst_if_none_match_header',
            'copy_dst_if_match_header',
            'no_list_url_encoding',
            'unsigned_payload',
            'streamed_uploads',
            'part_size',
            'streaming_chunk_size',
            'list_page_size',
            'delete_batch_size',
            'request_timeout_s',
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
                self.capabilities,
                self.copy_dst_if_none_match_header,
                self.copy_dst_if_match_header,
                self.no_list_url_encoding,
                self.unsigned_payload,
                self.streamed_uploads,
                self.part_size,
                self.streaming_chunk_size,
                self.list_page_size,
                self.delete_batch_size,
                self.request_timeout_s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            capabilities: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            copy_dst_if_none_match_header: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            copy_dst_if_match_header: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            no_list_url_encoding: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            unsigned_payload: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            streamed_uploads: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            part_size: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            streaming_chunk_size: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            list_page_size: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            delete_batch_size: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            request_timeout_s: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'capabilities', capabilities)
            __dataclass__object_setattr(self, 'copy_dst_if_none_match_header', copy_dst_if_none_match_header)
            __dataclass__object_setattr(self, 'copy_dst_if_match_header', copy_dst_if_match_header)
            __dataclass__object_setattr(self, 'no_list_url_encoding', no_list_url_encoding)
            __dataclass__object_setattr(self, 'unsigned_payload', unsigned_payload)
            __dataclass__object_setattr(self, 'streamed_uploads', streamed_uploads)
            __dataclass__object_setattr(self, 'part_size', part_size)
            __dataclass__object_setattr(self, 'streaming_chunk_size', streaming_chunk_size)
            __dataclass__object_setattr(self, 'list_page_size', list_page_size)
            __dataclass__object_setattr(self, 'delete_batch_size', delete_batch_size)
            __dataclass__object_setattr(self, 'request_timeout_s', request_timeout_s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"capabilities={self.capabilities!r}")
            parts.append(f"copy_dst_if_none_match_header={self.copy_dst_if_none_match_header!r}")
            parts.append(f"copy_dst_if_match_header={self.copy_dst_if_match_header!r}")
            parts.append(f"no_list_url_encoding={self.no_list_url_encoding!r}")
            parts.append(f"unsigned_payload={self.unsigned_payload!r}")
            parts.append(f"streamed_uploads={self.streamed_uploads!r}")
            parts.append(f"part_size={self.part_size!r}")
            parts.append(f"streaming_chunk_size={self.streaming_chunk_size!r}")
            parts.append(f"list_page_size={self.list_page_size!r}")
            parts.append(f"delete_batch_size={self.delete_batch_size!r}")
            parts.append(f"request_timeout_s={self.request_timeout_s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e73a710c3d1100b2054cc89de7c65eb055eb2994',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('source', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('length', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.streaming', 'S3StreamBody'),
    ),
)
def _process_dataclass__e73a710c3d1100b2054cc89de7c65eb055eb2994():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                source=self.source,
                length=self.length,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.length == other.length
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'length',
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
                self.source,
                self.length,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            source: __dataclass__init__fields__0__annotation,
            length: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'length', length)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"length={self.length!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6f30ac3149c2b5a7f8c1e509093a1d845a295167',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('status', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('headers', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('body', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.transport', 'S3Response'),
    ),
)
def _process_dataclass__6f30ac3149c2b5a7f8c1e509093a1d845a295167():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                status=self.status,
                headers=self.headers,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status == other.status and
                self.headers == other.headers and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'status',
            'headers',
            'body',
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
                self.status,
                self.headers,
                self.body,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            status: __dataclass__init__fields__0__annotation,
            headers: __dataclass__init__fields__1__annotation,
            body: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'body', body)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status={self.status!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='480cba9b2f32bf6ed651bece6a31c893f10bc48d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('key', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('size', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('cond', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('parts', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.uploads', 'S3ParallelUploadPlan'),
    ),
)
def _process_dataclass__480cba9b2f32bf6ed651bece6a31c893f10bc48d():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                size=self.size,
                upload_id=self.upload_id,
                cond=self.cond,
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.size == other.size and
                self.upload_id == other.upload_id and
                self.cond == other.cond and
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'size',
            'upload_id',
            'cond',
            'parts',
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
                self.key,
                self.size,
                self.upload_id,
                self.cond,
                self.parts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__0__annotation,
            size: __dataclass__init__fields__1__annotation,
            upload_id: __dataclass__init__fields__2__annotation,
            cond: __dataclass__init__fields__3__annotation,
            parts: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'cond', cond)
            __dataclass__object_setattr(self, 'parts', parts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"size={self.size!r}")
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"cond={self.cond!r}")
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='eae358fac14218361d4a601bed92683e81608f19',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('number', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('start', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('stop', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.uploads', 'S3UploadPart'),
    ),
)
def _process_dataclass__eae358fac14218361d4a601bed92683e81608f19():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                number=self.number,
                start=self.start,
                stop=self.stop,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.number == other.number and
                self.start == other.start and
                self.stop == other.stop
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'number',
            'start',
            'stop',
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
                self.number,
                self.start,
                self.stop,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            number: __dataclass__init__fields__0__annotation,
            start: __dataclass__init__fields__1__annotation,
            stop: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'number', number)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'stop', stop)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"number={self.number!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"stop={self.stop!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f8864cbb117579ef542939507a7215a72a57b5a7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('number', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('data', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.aws.uploads', 'S3UploadedPart'),
    ),
)
def _process_dataclass__f8864cbb117579ef542939507a7215a72a57b5a7():
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
                number=self.number,
                etag=self.etag,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.number == other.number and
                self.etag == other.etag and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'number',
            'etag',
            'data',
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
                self.number,
                self.etag,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            number: __dataclass__init__fields__0__annotation,
            etag: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            data: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'number', number)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"number={self.number!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='dd674dcb5e9a0be515b525d159d200f68a84291d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('key', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('path', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('is_dir', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('stat', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.local.listings', 'LocalEntry'),
    ),
)
def _process_dataclass__dd674dcb5e9a0be515b525d159d200f68a84291d():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                path=self.path,
                is_dir=self.is_dir,
                stat=self.stat,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.path == other.path and
                self.is_dir == other.is_dir and
                self.stat == other.stat
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'path',
            'is_dir',
            'stat',
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
                self.key,
                self.path,
                self.is_dir,
                self.stat,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            key: __dataclass__init__fields__0__annotation,
            path: __dataclass__init__fields__1__annotation,
            is_dir: __dataclass__init__fields__2__annotation,
            stat: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'is_dir', is_dir)
            __dataclass__object_setattr(self, 'stat', stat)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"path={self.path!r}")
            parts.append(f"is_dir={self.is_dir!r}")
            parts.append(f"stat={self.stat!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e17a6ae6c0b95b019ca5c6a697eb2cf82245c860',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('no_fsync', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('full_fsync', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('lock_stripes', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.local.stores', 'LocalBlobStore.Config'),
    ),
)
def _process_dataclass__e17a6ae6c0b95b019ca5c6a697eb2cf82245c860():
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
                no_fsync=self.no_fsync,
                full_fsync=self.full_fsync,
                lock_stripes=self.lock_stripes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.no_fsync == other.no_fsync and
                self.full_fsync == other.full_fsync and
                self.lock_stripes == other.lock_stripes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'no_fsync',
            'full_fsync',
            'lock_stripes',
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
                self.no_fsync,
                self.full_fsync,
                self.lock_stripes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            no_fsync: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            full_fsync: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            lock_stripes: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'no_fsync', no_fsync)
            __dataclass__object_setattr(self, 'full_fsync', full_fsync)
            __dataclass__object_setattr(self, 'lock_stripes', lock_stripes)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"no_fsync={self.no_fsync!r}")
            parts.append(f"full_fsync={self.full_fsync!r}")
            parts.append(f"lock_stripes={self.lock_stripes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='086011a7c86d52265c3e8e5b43fd12424d86ffe3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('index', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('byte_range', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.plans', 'ParallelGetPart'),
    ),
)
def _process_dataclass__086011a7c86d52265c3e8e5b43fd12424d86ffe3():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                index=self.index,
                byte_range=self.byte_range,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.index == other.index and
                self.byte_range == other.byte_range
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'index',
            'byte_range',
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
                self.index,
                self.byte_range,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            index: __dataclass__init__fields__0__annotation,
            byte_range: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'index', index)
            __dataclass__object_setattr(self, 'byte_range', byte_range)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"index={self.index!r}")
            parts.append(f"byte_range={self.byte_range!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fcfc7fe9d1770cb688d3602bf097014e3a09c032',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('key', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('version', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('size', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('parts', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.plans', 'ParallelGetPlan'),
    ),
)
def _process_dataclass__fcfc7fe9d1770cb688d3602bf097014e3a09c032():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                version=self.version,
                size=self.size,
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.version == other.version and
                self.size == other.size and
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'version',
            'size',
            'parts',
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
                self.key,
                self.version,
                self.size,
                self.parts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
            size: __dataclass__init__fields__2__annotation,
            parts: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'parts', parts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"size={self.size!r}")
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='24564bd93152888a807bce66461cea600860be3b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('info', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('data', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'Blob'),
    ),
)
def _process_dataclass__24564bd93152888a807bce66461cea600860be3b():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                info=self.info,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.info == other.info and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'info',
            'data',
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
                self.info,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            info: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'info', info)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"info={self.info!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f9cb9d0f61348e9539df020e60349303aed1f250',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('key', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('size', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('version', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('last_modified', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'BlobInfo'),
    ),
)
def _process_dataclass__f9cb9d0f61348e9539df020e60349303aed1f250():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                size=self.size,
                version=self.version,
                last_modified=self.last_modified,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.size == other.size and
                self.version == other.version and
                self.last_modified == other.last_modified
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'size',
            'version',
            'last_modified',
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
                self.key,
                self.size,
                self.version,
                self.last_modified,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__0__annotation,
            size: __dataclass__init__fields__1__annotation,
            version: __dataclass__init__fields__2__annotation,
            last_modified: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'last_modified', last_modified)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"size={self.size!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2d8d469949908a8999051dfb18c6cf21d2f85259',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('prefix', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'BlobPrefix'),
    ),
)
def _process_dataclass__2d8d469949908a8999051dfb18c6cf21d2f85259():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                prefix=self.prefix,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.prefix == other.prefix
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'prefix',
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
                self.prefix,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            prefix: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'prefix', prefix)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"prefix={self.prefix!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='327ed39089b927a67d229d0da0f9bc5937b6df3c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('etag', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'BlobVersion'),
    ),
)
def _process_dataclass__327ed39089b927a67d229d0da0f9bc5937b6df3c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                etag=self.etag,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.etag == other.etag
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'etag',
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
                self.etag,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            etag: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'etag', etag)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"etag={self.etag!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b437895e997b1cc68c4e36257f02a65e2a894180',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'IfAbsent'),
    ),
)
def _process_dataclass__b437895e997b1cc68c4e36257f02a65e2a894180():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__()  # noqa

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return True

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash(())

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
        ) -> __dataclass__None:
            pass

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            return f"{self.__class__.__qualname__}()"

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c3829b3cc1b675cf64c5e7ea8640583edeaacfa2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('version', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'IfMatch'),
        ('omxtra.blobs.types', 'IfNoneMatch'),
    ),
)
def _process_dataclass__c3829b3cc1b675cf64c5e7ea8640583edeaacfa2():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                version=self.version,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.version == other.version
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'version',
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
                self.version,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            version: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'version', version)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"version={self.version!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='38ade81e17aa2495f775cb37610cbc8ff1edee19',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('start', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('stop', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'OffsetBlobRange'),
    ),
)
def _process_dataclass__38ade81e17aa2495f775cb37610cbc8ff1edee19():
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
                start=self.start,
                stop=self.stop,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.start == other.start and
                self.stop == other.stop
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'start',
            'stop',
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
                self.start,
                self.stop,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            start: __dataclass__init__fields__0__annotation,
            stop: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'stop', stop)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"start={self.start!r}")
            parts.append(f"stop={self.stop!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7b2527b6f49ae0bc1cf64f11e25ed722c984f8da',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('length', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.blobs.types', 'SuffixBlobRange'),
    ),
)
def _process_dataclass__7b2527b6f49ae0bc1cf64f11e25ed722c984f8da():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                length=self.length,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.length == other.length
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'length',
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
                self.length,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            length: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'length', length)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"length={self.length!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
