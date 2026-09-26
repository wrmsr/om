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
    installer_sha1='a92bafdb9ca5770e99c153e96160ca8464b64366',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('request_charged', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'AbortMultipartUploadOutput'),
    ),
)
def _process_dataclass__a92bafdb9ca5770e99c153e96160ca8464b64366():
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
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'request_charged',
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
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            request_charged: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fd018bef819564cd800065a63f1698bc821e1ea8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('request_payer', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('if_match_initiated_time', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,),"
            " (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'AbortMultipartUploadRequest'),
    ),
)
def _process_dataclass__fd018bef819564cd800065a63f1698bc821e1ea8():
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
                bucket=self.bucket,
                key=self.key,
                upload_id=self.upload_id,
                request_payer=self.request_payer,
                expected_bucket_owner=self.expected_bucket_owner,
                if_match_initiated_time=self.if_match_initiated_time,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.key == other.key and
                self.upload_id == other.upload_id and
                self.request_payer == other.request_payer and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.if_match_initiated_time == other.if_match_initiated_time
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'key',
            'upload_id',
            'request_payer',
            'expected_bucket_owner',
            'if_match_initiated_time',
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
                self.bucket,
                self.key,
                self.upload_id,
                self.request_payer,
                self.expected_bucket_owner,
                self.if_match_initiated_time,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__1__annotation,
            key: __dataclass__init__fields__2__annotation,
            upload_id: __dataclass__init__fields__3__annotation,
            request_payer: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            expected_bucket_owner: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            if_match_initiated_time: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'if_match_initiated_time', if_match_initiated_time)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"if_match_initiated_time={self.if_match_initiated_time!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7cb9c7535ada86244fa778228a8f0759842ec829',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('creation_date', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('bucket_region', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('bucket_arn', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fals"
            "e, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Bucket'),
    ),
)
def _process_dataclass__7cb9c7535ada86244fa778228a8f0759842ec829():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
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
                creation_date=self.creation_date,
                bucket_region=self.bucket_region,
                bucket_arn=self.bucket_arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.creation_date == other.creation_date and
                self.bucket_region == other.bucket_region and
                self.bucket_arn == other.bucket_arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'name',
            'creation_date',
            'bucket_region',
            'bucket_arn',
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
                self.creation_date,
                self.bucket_region,
                self.bucket_arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            creation_date: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            bucket_region: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            bucket_arn: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'creation_date', creation_date)
            __dataclass__object_setattr(self, 'bucket_region', bucket_region)
            __dataclass__object_setattr(self, 'bucket_arn', bucket_arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"creation_date={self.creation_date!r}")
            parts.append(f"bucket_region={self.bucket_region!r}")
            parts.append(f"bucket_arn={self.bucket_arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='23c41b5997eaa88ff7f1b9f5ca1b6c3fab2075c6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'BucketAlreadyExists'),
        ('ominfra.clouds.aws.models.services.s3', 'BucketAlreadyOwnedByYou'),
        ('ominfra.clouds.aws.models.services.s3', 'EncryptionTypeMismatch'),
        ('ominfra.clouds.aws.models.services.s3', 'InvalidRequest'),
        ('ominfra.clouds.aws.models.services.s3', 'InvalidWriteOffset'),
        ('ominfra.clouds.aws.models.services.s3', 'NoSuchBucket'),
        ('ominfra.clouds.aws.models.services.s3', 'NoSuchKey'),
        ('ominfra.clouds.aws.models.services.s3', 'NoSuchUpload'),
        ('ominfra.clouds.aws.models.services.s3', 'ObjectNotInActiveTierError'),
        ('ominfra.clouds.aws.models.services.s3', 'TooManyParts'),
    ),
)
def _process_dataclass__23c41b5997eaa88ff7f1b9f5ca1b6c3fab2075c6():
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

        __dataclass___frozen_fields = {
            '__shape__',
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
    installer_sha1='f9d89fdf672616bdbc1c7766d64f846134954a9a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('data_redundancy', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'BucketInfo'),
    ),
)
def _process_dataclass__f9d89fdf672616bdbc1c7766d64f846134954a9a():
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
                data_redundancy=self.data_redundancy,
                type=self.type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.data_redundancy == other.data_redundancy and
                self.type == other.type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'data_redundancy',
            'type',
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
                self.data_redundancy,
                self.type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            data_redundancy: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            type: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'data_redundancy', data_redundancy)
            __dataclass__object_setattr(self, 'type', type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"data_redundancy={self.data_redundancy!r}")
            parts.append(f"type={self.type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='225541fce628820ca9d5ba9bb35962e5f9422532',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CommonPrefix'),
    ),
)
def _process_dataclass__225541fce628820ca9d5ba9bb35962e5f9422532():
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
            '__shape__',
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
            *,
            prefix: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
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
    installer_sha1='13386828acf01e3a103f62bb791ff8a6805352d2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('location', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('expiration', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_xxhash64', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_xxha"
            "sh3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('chec"
            "ksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('checksum_type', True, True, None, True, True, False, None), 'instance', 'value', None, False, False"
            ", False), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('sse_kms_key_id', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('bucket_key_enabled', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('request_charged', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), ("
            "False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CompleteMultipartUploadOutput'),
    ),
)
def _process_dataclass__13386828acf01e3a103f62bb791ff8a6805352d2():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                location=self.location,
                bucket=self.bucket,
                key=self.key,
                expiration=self.expiration,
                etag=self.etag,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                checksum_type=self.checksum_type,
                server_side_encryption=self.server_side_encryption,
                version_id=self.version_id,
                sse_kms_key_id=self.sse_kms_key_id,
                bucket_key_enabled=self.bucket_key_enabled,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.location == other.location and
                self.bucket == other.bucket and
                self.key == other.key and
                self.expiration == other.expiration and
                self.etag == other.etag and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.checksum_type == other.checksum_type and
                self.server_side_encryption == other.server_side_encryption and
                self.version_id == other.version_id and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'location',
            'bucket',
            'key',
            'expiration',
            'etag',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'checksum_type',
            'server_side_encryption',
            'version_id',
            'sse_kms_key_id',
            'bucket_key_enabled',
            'request_charged',
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
                self.location,
                self.bucket,
                self.key,
                self.expiration,
                self.etag,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.checksum_type,
                self.server_side_encryption,
                self.version_id,
                self.sse_kms_key_id,
                self.bucket_key_enabled,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            location: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            bucket: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            key: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            expiration: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            etag: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_crc32: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_crc32c: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_crc64nvme: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_sha1: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_sha256: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_sha512: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_md5: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_xxhash64: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_xxhash3: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_xxhash128: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            checksum_type: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            server_side_encryption: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            version_id: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            sse_kms_key_id: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            bucket_key_enabled: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            request_charged: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'location', location)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'expiration', expiration)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"location={self.location!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"expiration={self.expiration!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9b7c21a0f760e396a801c466f22a65939bc4542c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('multipart_upload', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksu"
            "m_xxhash64', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('checksum_type', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('mpu_object_size', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('request_payer', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('if_match', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('if_none_match', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('sse_customer_algorithm', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_m"
            "d5', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, "
            "0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CompleteMultipartUploadRequest'),
    ),
)
def _process_dataclass__9b7c21a0f760e396a801c466f22a65939bc4542c():
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
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                bucket=self.bucket,
                key=self.key,
                multipart_upload=self.multipart_upload,
                upload_id=self.upload_id,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                checksum_type=self.checksum_type,
                mpu_object_size=self.mpu_object_size,
                request_payer=self.request_payer,
                expected_bucket_owner=self.expected_bucket_owner,
                if_match=self.if_match,
                if_none_match=self.if_none_match,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.key == other.key and
                self.multipart_upload == other.multipart_upload and
                self.upload_id == other.upload_id and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.checksum_type == other.checksum_type and
                self.mpu_object_size == other.mpu_object_size and
                self.request_payer == other.request_payer and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.if_match == other.if_match and
                self.if_none_match == other.if_none_match and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'key',
            'multipart_upload',
            'upload_id',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'checksum_type',
            'mpu_object_size',
            'request_payer',
            'expected_bucket_owner',
            'if_match',
            'if_none_match',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
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
                self.bucket,
                self.key,
                self.multipart_upload,
                self.upload_id,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.checksum_type,
                self.mpu_object_size,
                self.request_payer,
                self.expected_bucket_owner,
                self.if_match,
                self.if_none_match,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation,
            key: __dataclass__init__fields__02__annotation,
            multipart_upload: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            upload_id: __dataclass__init__fields__04__annotation,
            checksum_crc32: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_crc32c: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_crc64nvme: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_sha1: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_sha256: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_sha512: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_md5: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_xxhash64: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_xxhash3: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_xxhash128: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_type: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            mpu_object_size: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            request_payer: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            expected_bucket_owner: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            if_match: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            if_none_match: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            sse_customer_algorithm: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            sse_customer_key: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            sse_customer_key_md5: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'multipart_upload', multipart_upload)
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'mpu_object_size', mpu_object_size)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'if_match', if_match)
            __dataclass__object_setattr(self, 'if_none_match', if_none_match)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"multipart_upload={self.multipart_upload!r}")
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"mpu_object_size={self.mpu_object_size!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"if_match={self.if_match!r}")
            parts.append(f"if_none_match={self.if_none_match!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='496e7531b3aa54249e533e4b5533035bf9630922',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('parts', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CompletedMultipartUpload'),
    ),
)
def _process_dataclass__496e7531b3aa54249e533e4b5533035bf9630922():
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
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
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
                self.parts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            parts: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'parts', parts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3536287d98e8fe5ed3b13c4597b83b809a2c931c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_xxhash64', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_xxh"
            "ash3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('che"
            "cksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('part_number', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CompletedPart'),
    ),
)
def _process_dataclass__3536287d98e8fe5ed3b13c4597b83b809a2c931c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
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
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                part_number=self.part_number,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.etag == other.etag and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.part_number == other.part_number
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'etag',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'part_number',
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
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.part_number,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            etag: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            checksum_crc32: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            checksum_crc32c: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_crc64nvme: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_sha1: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_sha256: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_sha512: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_md5: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_xxhash64: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_xxhash3: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_xxhash128: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            part_number: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'part_number', part_number)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"part_number={self.part_number!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e48d17e86e601be02759d7bdcf07944a587c61cf',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('copy_object_result', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('expiration', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('copy_source_version_id', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('version_id', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('server_side_encryption', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_algorithm', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_custom"
            "er_key_md5', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('sse_kms_key_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse), (('sse_kms_encryption_context', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('bucket_key_enabled', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('request_charged', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fa"
            "lse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CopyObjectOutput'),
    ),
)
def _process_dataclass__e48d17e86e601be02759d7bdcf07944a587c61cf():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                copy_object_result=self.copy_object_result,
                expiration=self.expiration,
                copy_source_version_id=self.copy_source_version_id,
                version_id=self.version_id,
                server_side_encryption=self.server_side_encryption,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.copy_object_result == other.copy_object_result and
                self.expiration == other.expiration and
                self.copy_source_version_id == other.copy_source_version_id and
                self.version_id == other.version_id and
                self.server_side_encryption == other.server_side_encryption and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'copy_object_result',
            'expiration',
            'copy_source_version_id',
            'version_id',
            'server_side_encryption',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'request_charged',
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
                self.copy_object_result,
                self.expiration,
                self.copy_source_version_id,
                self.version_id,
                self.server_side_encryption,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            copy_object_result: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            expiration: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            copy_source_version_id: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            version_id: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            server_side_encryption: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            sse_customer_algorithm: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            sse_customer_key_md5: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            sse_kms_key_id: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            sse_kms_encryption_context: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            bucket_key_enabled: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            request_charged: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'copy_object_result', copy_object_result)
            __dataclass__object_setattr(self, 'expiration', expiration)
            __dataclass__object_setattr(self, 'copy_source_version_id', copy_source_version_id)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"copy_object_result={self.copy_object_result!r}")
            parts.append(f"expiration={self.expiration!r}")
            parts.append(f"copy_source_version_id={self.copy_source_version_id!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='24f186e35b4cabf4fada515e6913eee21e728968',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('acl', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('cache_control', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('checksum_algorithm', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('content_disposition', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('content_encoding', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('content_language', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('content_type', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('copy_source', True, Tru"
            "e, None, True, True, False, None), 'instance', 'missing', None, False, False, False), (('copy_source_if_ma"
            "tch', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('copy"
            "_source_if_modified_since', True, True, None, True, True, False, None), 'instance', 'value', None, False, "
            "False, False), (('copy_source_if_none_match', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('copy_source_if_unmodified_since', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('expires', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('grant_full_control', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('grant_read', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('grant_read_acp', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_write_acp', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('if_match', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('if_none_match', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('key', True"
            ", True, None, True, True, False, None), 'instance', 'missing', None, False, False, False), (('metadata', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('metadata_di"
            "rective', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "tagging_directive', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse), (('annotation_directive', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('storage_class', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('website_redirect_location', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('sse_customer_algorithm', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms"
            "_key_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "sse_kms_encryption_context', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('bucket_key_enabled', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('copy_source_sse_customer_algorithm', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('copy_source_sse_customer_key', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('copy_source_sse_customer_key"
            "_md5', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('req"
            "uest_payer', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('tagging', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('object_lock_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('object_lock_retain_until_date', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('object_lock_legal_hold_status', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('object_lock_event_hold', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold_duration_day"
            "s', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object"
            "_lock_event_hold_duration_years', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('expected_bucket_owner', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('expected_source_bucket_owner', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,),"
            " (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CopyObjectRequest'),
    ),
)
def _process_dataclass__24f186e35b4cabf4fada515e6913eee21e728968():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__29__default = __dataclass__spec.fields[29].default.must()
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default = __dataclass__spec.fields[33].default.must()
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__init__fields__35__annotation = __dataclass__spec.fields[35].annotation
        __dataclass__init__fields__35__default = __dataclass__spec.fields[35].default.must()
        __dataclass__init__fields__36__annotation = __dataclass__spec.fields[36].annotation
        __dataclass__init__fields__36__default = __dataclass__spec.fields[36].default.must()
        __dataclass__init__fields__37__annotation = __dataclass__spec.fields[37].annotation
        __dataclass__init__fields__37__default = __dataclass__spec.fields[37].default.must()
        __dataclass__init__fields__38__annotation = __dataclass__spec.fields[38].annotation
        __dataclass__init__fields__38__default = __dataclass__spec.fields[38].default.must()
        __dataclass__init__fields__39__annotation = __dataclass__spec.fields[39].annotation
        __dataclass__init__fields__39__default = __dataclass__spec.fields[39].default.must()
        __dataclass__init__fields__40__annotation = __dataclass__spec.fields[40].annotation
        __dataclass__init__fields__40__default = __dataclass__spec.fields[40].default.must()
        __dataclass__init__fields__41__annotation = __dataclass__spec.fields[41].annotation
        __dataclass__init__fields__41__default = __dataclass__spec.fields[41].default.must()
        __dataclass__init__fields__42__annotation = __dataclass__spec.fields[42].annotation
        __dataclass__init__fields__42__default = __dataclass__spec.fields[42].default.must()
        __dataclass__init__fields__43__annotation = __dataclass__spec.fields[43].annotation
        __dataclass__init__fields__43__default = __dataclass__spec.fields[43].default.must()
        __dataclass__init__fields__44__annotation = __dataclass__spec.fields[44].annotation
        __dataclass__init__fields__44__default = __dataclass__spec.fields[44].default.must()
        __dataclass__init__fields__45__annotation = __dataclass__spec.fields[45].annotation
        __dataclass__init__fields__45__default = __dataclass__spec.fields[45].default.must()
        __dataclass__init__fields__46__annotation = __dataclass__spec.fields[46].annotation
        __dataclass__init__fields__46__default = __dataclass__spec.fields[46].default.must()
        __dataclass__init__fields__47__annotation = __dataclass__spec.fields[47].annotation
        __dataclass__init__fields__47__default = __dataclass__spec.fields[47].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                acl=self.acl,
                bucket=self.bucket,
                cache_control=self.cache_control,
                checksum_algorithm=self.checksum_algorithm,
                content_disposition=self.content_disposition,
                content_encoding=self.content_encoding,
                content_language=self.content_language,
                content_type=self.content_type,
                copy_source=self.copy_source,
                copy_source_if_match=self.copy_source_if_match,
                copy_source_if_modified_since=self.copy_source_if_modified_since,
                copy_source_if_none_match=self.copy_source_if_none_match,
                copy_source_if_unmodified_since=self.copy_source_if_unmodified_since,
                expires=self.expires,
                grant_full_control=self.grant_full_control,
                grant_read=self.grant_read,
                grant_read_acp=self.grant_read_acp,
                grant_write_acp=self.grant_write_acp,
                if_match=self.if_match,
                if_none_match=self.if_none_match,
                key=self.key,
                metadata=self.metadata,
                metadata_directive=self.metadata_directive,
                tagging_directive=self.tagging_directive,
                annotation_directive=self.annotation_directive,
                server_side_encryption=self.server_side_encryption,
                storage_class=self.storage_class,
                website_redirect_location=self.website_redirect_location,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                copy_source_sse_customer_algorithm=self.copy_source_sse_customer_algorithm,
                copy_source_sse_customer_key=self.copy_source_sse_customer_key,
                copy_source_sse_customer_key_md5=self.copy_source_sse_customer_key_md5,
                request_payer=self.request_payer,
                tagging=self.tagging,
                object_lock_mode=self.object_lock_mode,
                object_lock_retain_until_date=self.object_lock_retain_until_date,
                object_lock_legal_hold_status=self.object_lock_legal_hold_status,
                object_lock_event_hold=self.object_lock_event_hold,
                object_lock_event_hold_duration_days=self.object_lock_event_hold_duration_days,
                object_lock_event_hold_duration_years=self.object_lock_event_hold_duration_years,
                expected_bucket_owner=self.expected_bucket_owner,
                expected_source_bucket_owner=self.expected_source_bucket_owner,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.acl == other.acl and
                self.bucket == other.bucket and
                self.cache_control == other.cache_control and
                self.checksum_algorithm == other.checksum_algorithm and
                self.content_disposition == other.content_disposition and
                self.content_encoding == other.content_encoding and
                self.content_language == other.content_language and
                self.content_type == other.content_type and
                self.copy_source == other.copy_source and
                self.copy_source_if_match == other.copy_source_if_match and
                self.copy_source_if_modified_since == other.copy_source_if_modified_since and
                self.copy_source_if_none_match == other.copy_source_if_none_match and
                self.copy_source_if_unmodified_since == other.copy_source_if_unmodified_since and
                self.expires == other.expires and
                self.grant_full_control == other.grant_full_control and
                self.grant_read == other.grant_read and
                self.grant_read_acp == other.grant_read_acp and
                self.grant_write_acp == other.grant_write_acp and
                self.if_match == other.if_match and
                self.if_none_match == other.if_none_match and
                self.key == other.key and
                self.metadata == other.metadata and
                self.metadata_directive == other.metadata_directive and
                self.tagging_directive == other.tagging_directive and
                self.annotation_directive == other.annotation_directive and
                self.server_side_encryption == other.server_side_encryption and
                self.storage_class == other.storage_class and
                self.website_redirect_location == other.website_redirect_location and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.copy_source_sse_customer_algorithm == other.copy_source_sse_customer_algorithm and
                self.copy_source_sse_customer_key == other.copy_source_sse_customer_key and
                self.copy_source_sse_customer_key_md5 == other.copy_source_sse_customer_key_md5 and
                self.request_payer == other.request_payer and
                self.tagging == other.tagging and
                self.object_lock_mode == other.object_lock_mode and
                self.object_lock_retain_until_date == other.object_lock_retain_until_date and
                self.object_lock_legal_hold_status == other.object_lock_legal_hold_status and
                self.object_lock_event_hold == other.object_lock_event_hold and
                self.object_lock_event_hold_duration_days == other.object_lock_event_hold_duration_days and
                self.object_lock_event_hold_duration_years == other.object_lock_event_hold_duration_years and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.expected_source_bucket_owner == other.expected_source_bucket_owner
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'acl',
            'bucket',
            'cache_control',
            'checksum_algorithm',
            'content_disposition',
            'content_encoding',
            'content_language',
            'content_type',
            'copy_source',
            'copy_source_if_match',
            'copy_source_if_modified_since',
            'copy_source_if_none_match',
            'copy_source_if_unmodified_since',
            'expires',
            'grant_full_control',
            'grant_read',
            'grant_read_acp',
            'grant_write_acp',
            'if_match',
            'if_none_match',
            'key',
            'metadata',
            'metadata_directive',
            'tagging_directive',
            'annotation_directive',
            'server_side_encryption',
            'storage_class',
            'website_redirect_location',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'copy_source_sse_customer_algorithm',
            'copy_source_sse_customer_key',
            'copy_source_sse_customer_key_md5',
            'request_payer',
            'tagging',
            'object_lock_mode',
            'object_lock_retain_until_date',
            'object_lock_legal_hold_status',
            'object_lock_event_hold',
            'object_lock_event_hold_duration_days',
            'object_lock_event_hold_duration_years',
            'expected_bucket_owner',
            'expected_source_bucket_owner',
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
                self.acl,
                self.bucket,
                self.cache_control,
                self.checksum_algorithm,
                self.content_disposition,
                self.content_encoding,
                self.content_language,
                self.content_type,
                self.copy_source,
                self.copy_source_if_match,
                self.copy_source_if_modified_since,
                self.copy_source_if_none_match,
                self.copy_source_if_unmodified_since,
                self.expires,
                self.grant_full_control,
                self.grant_read,
                self.grant_read_acp,
                self.grant_write_acp,
                self.if_match,
                self.if_none_match,
                self.key,
                self.metadata,
                self.metadata_directive,
                self.tagging_directive,
                self.annotation_directive,
                self.server_side_encryption,
                self.storage_class,
                self.website_redirect_location,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.copy_source_sse_customer_algorithm,
                self.copy_source_sse_customer_key,
                self.copy_source_sse_customer_key_md5,
                self.request_payer,
                self.tagging,
                self.object_lock_mode,
                self.object_lock_retain_until_date,
                self.object_lock_legal_hold_status,
                self.object_lock_event_hold,
                self.object_lock_event_hold_duration_days,
                self.object_lock_event_hold_duration_years,
                self.expected_bucket_owner,
                self.expected_source_bucket_owner,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            acl: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            bucket: __dataclass__init__fields__02__annotation,
            cache_control: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_algorithm: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            content_disposition: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            content_encoding: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            content_language: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            content_type: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            copy_source: __dataclass__init__fields__09__annotation,
            copy_source_if_match: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            copy_source_if_modified_since: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            copy_source_if_none_match: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            copy_source_if_unmodified_since: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            expires: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            grant_full_control: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            grant_read: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            grant_read_acp: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            grant_write_acp: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            if_match: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            if_none_match: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            key: __dataclass__init__fields__21__annotation,
            metadata: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            metadata_directive: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            tagging_directive: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            annotation_directive: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            server_side_encryption: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            storage_class: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            website_redirect_location: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            sse_customer_algorithm: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            sse_customer_key: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            sse_customer_key_md5: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            sse_kms_key_id: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            sse_kms_encryption_context: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            bucket_key_enabled: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            copy_source_sse_customer_algorithm: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            copy_source_sse_customer_key: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            copy_source_sse_customer_key_md5: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            request_payer: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            tagging: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            object_lock_mode: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            object_lock_retain_until_date: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            object_lock_legal_hold_status: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            object_lock_event_hold: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            object_lock_event_hold_duration_days: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            object_lock_event_hold_duration_years: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            expected_bucket_owner: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
            expected_source_bucket_owner: __dataclass__init__fields__47__annotation = __dataclass__init__fields__47__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'acl', acl)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'cache_control', cache_control)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'content_disposition', content_disposition)
            __dataclass__object_setattr(self, 'content_encoding', content_encoding)
            __dataclass__object_setattr(self, 'content_language', content_language)
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'copy_source', copy_source)
            __dataclass__object_setattr(self, 'copy_source_if_match', copy_source_if_match)
            __dataclass__object_setattr(self, 'copy_source_if_modified_since', copy_source_if_modified_since)
            __dataclass__object_setattr(self, 'copy_source_if_none_match', copy_source_if_none_match)
            __dataclass__object_setattr(self, 'copy_source_if_unmodified_since', copy_source_if_unmodified_since)
            __dataclass__object_setattr(self, 'expires', expires)
            __dataclass__object_setattr(self, 'grant_full_control', grant_full_control)
            __dataclass__object_setattr(self, 'grant_read', grant_read)
            __dataclass__object_setattr(self, 'grant_read_acp', grant_read_acp)
            __dataclass__object_setattr(self, 'grant_write_acp', grant_write_acp)
            __dataclass__object_setattr(self, 'if_match', if_match)
            __dataclass__object_setattr(self, 'if_none_match', if_none_match)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'metadata_directive', metadata_directive)
            __dataclass__object_setattr(self, 'tagging_directive', tagging_directive)
            __dataclass__object_setattr(self, 'annotation_directive', annotation_directive)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'website_redirect_location', website_redirect_location)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'copy_source_sse_customer_algorithm', copy_source_sse_customer_algorithm)
            __dataclass__object_setattr(self, 'copy_source_sse_customer_key', copy_source_sse_customer_key)
            __dataclass__object_setattr(self, 'copy_source_sse_customer_key_md5', copy_source_sse_customer_key_md5)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'tagging', tagging)
            __dataclass__object_setattr(self, 'object_lock_mode', object_lock_mode)
            __dataclass__object_setattr(self, 'object_lock_retain_until_date', object_lock_retain_until_date)
            __dataclass__object_setattr(self, 'object_lock_legal_hold_status', object_lock_legal_hold_status)
            __dataclass__object_setattr(self, 'object_lock_event_hold', object_lock_event_hold)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_days', object_lock_event_hold_duration_days)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_years', object_lock_event_hold_duration_years)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'expected_source_bucket_owner', expected_source_bucket_owner)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"acl={self.acl!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"cache_control={self.cache_control!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"content_disposition={self.content_disposition!r}")
            parts.append(f"content_encoding={self.content_encoding!r}")
            parts.append(f"content_language={self.content_language!r}")
            parts.append(f"content_type={self.content_type!r}")
            parts.append(f"copy_source={self.copy_source!r}")
            parts.append(f"copy_source_if_match={self.copy_source_if_match!r}")
            parts.append(f"copy_source_if_modified_since={self.copy_source_if_modified_since!r}")
            parts.append(f"copy_source_if_none_match={self.copy_source_if_none_match!r}")
            parts.append(f"copy_source_if_unmodified_since={self.copy_source_if_unmodified_since!r}")
            parts.append(f"expires={self.expires!r}")
            parts.append(f"grant_full_control={self.grant_full_control!r}")
            parts.append(f"grant_read={self.grant_read!r}")
            parts.append(f"grant_read_acp={self.grant_read_acp!r}")
            parts.append(f"grant_write_acp={self.grant_write_acp!r}")
            parts.append(f"if_match={self.if_match!r}")
            parts.append(f"if_none_match={self.if_none_match!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"metadata_directive={self.metadata_directive!r}")
            parts.append(f"tagging_directive={self.tagging_directive!r}")
            parts.append(f"annotation_directive={self.annotation_directive!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"website_redirect_location={self.website_redirect_location!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"copy_source_sse_customer_algorithm={self.copy_source_sse_customer_algorithm!r}")
            parts.append(f"copy_source_sse_customer_key={self.copy_source_sse_customer_key!r}")
            parts.append(f"copy_source_sse_customer_key_md5={self.copy_source_sse_customer_key_md5!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"tagging={self.tagging!r}")
            parts.append(f"object_lock_mode={self.object_lock_mode!r}")
            parts.append(f"object_lock_retain_until_date={self.object_lock_retain_until_date!r}")
            parts.append(f"object_lock_legal_hold_status={self.object_lock_legal_hold_status!r}")
            parts.append(f"object_lock_event_hold={self.object_lock_event_hold!r}")
            parts.append(f"object_lock_event_hold_duration_days={self.object_lock_event_hold_duration_days!r}")
            parts.append(f"object_lock_event_hold_duration_years={self.object_lock_event_hold_duration_years!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"expected_source_bucket_owner={self.expected_source_bucket_owner!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='58b46da8cc7bcdc791391bac8a58e6ec4d63dfb3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('last_modified', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('checksum_type', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_x"
            "xhash64', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fa"
            "lse), (('checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,"
            ")))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CopyObjectResult'),
    ),
)
def _process_dataclass__58b46da8cc7bcdc791391bac8a58e6ec4d63dfb3():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
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
                last_modified=self.last_modified,
                checksum_type=self.checksum_type,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.etag == other.etag and
                self.last_modified == other.last_modified and
                self.checksum_type == other.checksum_type and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'etag',
            'last_modified',
            'checksum_type',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
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
                self.last_modified,
                self.checksum_type,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            etag: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            last_modified: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            checksum_type: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_crc32: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_crc32c: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_crc64nvme: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_sha1: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_sha256: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_sha512: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_md5: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_xxhash64: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_xxhash3: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_xxhash128: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'last_modified', last_modified)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"etag={self.etag!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='bb05a39a69386136ba762cd7fefa6e0fecce5158',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('location_constraint', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('location', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('tags', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, "
            "()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CreateBucketConfiguration'),
    ),
)
def _process_dataclass__bb05a39a69386136ba762cd7fefa6e0fecce5158():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                location_constraint=self.location_constraint,
                location=self.location,
                bucket=self.bucket,
                tags=self.tags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.location_constraint == other.location_constraint and
                self.location == other.location and
                self.bucket == other.bucket and
                self.tags == other.tags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'location_constraint',
            'location',
            'bucket',
            'tags',
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
                self.location_constraint,
                self.location,
                self.bucket,
                self.tags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            location_constraint: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            location: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            bucket: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            tags: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'location_constraint', location_constraint)
            __dataclass__object_setattr(self, 'location', location)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'tags', tags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"location_constraint={self.location_constraint!r}")
            parts.append(f"location={self.location!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"tags={self.tags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c3b577508b8041fa7689c51b36285f4614cca4c7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('location', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('bucket_arn', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CreateBucketOutput'),
    ),
)
def _process_dataclass__c3b577508b8041fa7689c51b36285f4614cca4c7():
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
                location=self.location,
                bucket_arn=self.bucket_arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.location == other.location and
                self.bucket_arn == other.bucket_arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'location',
            'bucket_arn',
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
                self.location,
                self.bucket_arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            location: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            bucket_arn: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'location', location)
            __dataclass__object_setattr(self, 'bucket_arn', bucket_arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"location={self.location!r}")
            parts.append(f"bucket_arn={self.bucket_arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0ee064154efad577a7a2971a9655a09877e940ff',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('acl', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('create_bucket_configuration', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('grant_full_control', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('grant_read', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False), (('grant_read_acp', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('grant_write', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('grant_write_acp', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object_lock_enabled_fo"
            "r_bucket', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'object_ownership', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse), (('bucket_namespace', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)"
            "))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CreateBucketRequest'),
    ),
)
def _process_dataclass__0ee064154efad577a7a2971a9655a09877e940ff():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                acl=self.acl,
                bucket=self.bucket,
                create_bucket_configuration=self.create_bucket_configuration,
                grant_full_control=self.grant_full_control,
                grant_read=self.grant_read,
                grant_read_acp=self.grant_read_acp,
                grant_write=self.grant_write,
                grant_write_acp=self.grant_write_acp,
                object_lock_enabled_for_bucket=self.object_lock_enabled_for_bucket,
                object_ownership=self.object_ownership,
                bucket_namespace=self.bucket_namespace,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.acl == other.acl and
                self.bucket == other.bucket and
                self.create_bucket_configuration == other.create_bucket_configuration and
                self.grant_full_control == other.grant_full_control and
                self.grant_read == other.grant_read and
                self.grant_read_acp == other.grant_read_acp and
                self.grant_write == other.grant_write and
                self.grant_write_acp == other.grant_write_acp and
                self.object_lock_enabled_for_bucket == other.object_lock_enabled_for_bucket and
                self.object_ownership == other.object_ownership and
                self.bucket_namespace == other.bucket_namespace
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'acl',
            'bucket',
            'create_bucket_configuration',
            'grant_full_control',
            'grant_read',
            'grant_read_acp',
            'grant_write',
            'grant_write_acp',
            'object_lock_enabled_for_bucket',
            'object_ownership',
            'bucket_namespace',
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
                self.acl,
                self.bucket,
                self.create_bucket_configuration,
                self.grant_full_control,
                self.grant_read,
                self.grant_read_acp,
                self.grant_write,
                self.grant_write_acp,
                self.object_lock_enabled_for_bucket,
                self.object_ownership,
                self.bucket_namespace,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            acl: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            bucket: __dataclass__init__fields__02__annotation,
            create_bucket_configuration: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            grant_full_control: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            grant_read: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            grant_read_acp: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            grant_write: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            grant_write_acp: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            object_lock_enabled_for_bucket: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            object_ownership: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            bucket_namespace: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'acl', acl)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'create_bucket_configuration', create_bucket_configuration)
            __dataclass__object_setattr(self, 'grant_full_control', grant_full_control)
            __dataclass__object_setattr(self, 'grant_read', grant_read)
            __dataclass__object_setattr(self, 'grant_read_acp', grant_read_acp)
            __dataclass__object_setattr(self, 'grant_write', grant_write)
            __dataclass__object_setattr(self, 'grant_write_acp', grant_write_acp)
            __dataclass__object_setattr(self, 'object_lock_enabled_for_bucket', object_lock_enabled_for_bucket)
            __dataclass__object_setattr(self, 'object_ownership', object_ownership)
            __dataclass__object_setattr(self, 'bucket_namespace', bucket_namespace)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"acl={self.acl!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"create_bucket_configuration={self.create_bucket_configuration!r}")
            parts.append(f"grant_full_control={self.grant_full_control!r}")
            parts.append(f"grant_read={self.grant_read!r}")
            parts.append(f"grant_read_acp={self.grant_read_acp!r}")
            parts.append(f"grant_write={self.grant_write!r}")
            parts.append(f"grant_write_acp={self.grant_write_acp!r}")
            parts.append(f"object_lock_enabled_for_bucket={self.object_lock_enabled_for_bucket!r}")
            parts.append(f"object_ownership={self.object_ownership!r}")
            parts.append(f"bucket_namespace={self.bucket_namespace!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='46ea6e29b35965175cff1d8dd04727a0d52f2a8d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('abort_date', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('abort_rule_id', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('server_side_encryption', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('sse_customer_algorithm', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_key_id', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_encrypti"
            "on_context', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('bucket_key_enabled', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fals"
            "e, False), (('request_charged', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('checksum_algorithm', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('checksum_type', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CreateMultipartUploadOutput'),
    ),
)
def _process_dataclass__46ea6e29b35965175cff1d8dd04727a0d52f2a8d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                abort_date=self.abort_date,
                abort_rule_id=self.abort_rule_id,
                bucket=self.bucket,
                key=self.key,
                upload_id=self.upload_id,
                server_side_encryption=self.server_side_encryption,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                request_charged=self.request_charged,
                checksum_algorithm=self.checksum_algorithm,
                checksum_type=self.checksum_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.abort_date == other.abort_date and
                self.abort_rule_id == other.abort_rule_id and
                self.bucket == other.bucket and
                self.key == other.key and
                self.upload_id == other.upload_id and
                self.server_side_encryption == other.server_side_encryption and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_charged == other.request_charged and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_type == other.checksum_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'abort_date',
            'abort_rule_id',
            'bucket',
            'key',
            'upload_id',
            'server_side_encryption',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'request_charged',
            'checksum_algorithm',
            'checksum_type',
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
                self.abort_date,
                self.abort_rule_id,
                self.bucket,
                self.key,
                self.upload_id,
                self.server_side_encryption,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.request_charged,
                self.checksum_algorithm,
                self.checksum_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            abort_date: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            abort_rule_id: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            bucket: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            key: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            upload_id: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            server_side_encryption: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            sse_customer_algorithm: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            sse_customer_key_md5: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            sse_kms_key_id: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            sse_kms_encryption_context: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            bucket_key_enabled: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            request_charged: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_algorithm: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_type: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'abort_date', abort_date)
            __dataclass__object_setattr(self, 'abort_rule_id', abort_rule_id)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_charged', request_charged)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"abort_date={self.abort_date!r}")
            parts.append(f"abort_rule_id={self.abort_rule_id!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d08c3881b4e1f81c7069ebeb2cfcebec26120572',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('acl', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('cache_control', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('content_disposition', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('content_encoding', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('content_language', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('content_type', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('expires', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('grant_full_control', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_read', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_read_acp', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_write_a"
            "cp', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('key',"
            " True, True, None, True, True, False, None), 'instance', 'missing', None, False, False, False), (('metadat"
            "a', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('server"
            "_side_encryption', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fa"
            "lse), (('storage_class', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('website_redirect_location', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('sse_customer_key', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_key_id', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_encryption_context', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('bucket_key"
            "_enabled', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'request_payer', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('tagging', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('object_lock_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('object_lock_retain_until_date', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('object_lock_legal_hold_status', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold_duration"
            "_days', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('ob"
            "ject_lock_event_hold_duration_years', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('expected_bucket_owner', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('checksum_algorithm', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('checksum_type', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,),"
            " (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'CreateMultipartUploadRequest'),
    ),
)
def _process_dataclass__d08c3881b4e1f81c7069ebeb2cfcebec26120572():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__29__default = __dataclass__spec.fields[29].default.must()
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default = __dataclass__spec.fields[33].default.must()
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                acl=self.acl,
                bucket=self.bucket,
                cache_control=self.cache_control,
                content_disposition=self.content_disposition,
                content_encoding=self.content_encoding,
                content_language=self.content_language,
                content_type=self.content_type,
                expires=self.expires,
                grant_full_control=self.grant_full_control,
                grant_read=self.grant_read,
                grant_read_acp=self.grant_read_acp,
                grant_write_acp=self.grant_write_acp,
                key=self.key,
                metadata=self.metadata,
                server_side_encryption=self.server_side_encryption,
                storage_class=self.storage_class,
                website_redirect_location=self.website_redirect_location,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                request_payer=self.request_payer,
                tagging=self.tagging,
                object_lock_mode=self.object_lock_mode,
                object_lock_retain_until_date=self.object_lock_retain_until_date,
                object_lock_legal_hold_status=self.object_lock_legal_hold_status,
                object_lock_event_hold=self.object_lock_event_hold,
                object_lock_event_hold_duration_days=self.object_lock_event_hold_duration_days,
                object_lock_event_hold_duration_years=self.object_lock_event_hold_duration_years,
                expected_bucket_owner=self.expected_bucket_owner,
                checksum_algorithm=self.checksum_algorithm,
                checksum_type=self.checksum_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.acl == other.acl and
                self.bucket == other.bucket and
                self.cache_control == other.cache_control and
                self.content_disposition == other.content_disposition and
                self.content_encoding == other.content_encoding and
                self.content_language == other.content_language and
                self.content_type == other.content_type and
                self.expires == other.expires and
                self.grant_full_control == other.grant_full_control and
                self.grant_read == other.grant_read and
                self.grant_read_acp == other.grant_read_acp and
                self.grant_write_acp == other.grant_write_acp and
                self.key == other.key and
                self.metadata == other.metadata and
                self.server_side_encryption == other.server_side_encryption and
                self.storage_class == other.storage_class and
                self.website_redirect_location == other.website_redirect_location and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_payer == other.request_payer and
                self.tagging == other.tagging and
                self.object_lock_mode == other.object_lock_mode and
                self.object_lock_retain_until_date == other.object_lock_retain_until_date and
                self.object_lock_legal_hold_status == other.object_lock_legal_hold_status and
                self.object_lock_event_hold == other.object_lock_event_hold and
                self.object_lock_event_hold_duration_days == other.object_lock_event_hold_duration_days and
                self.object_lock_event_hold_duration_years == other.object_lock_event_hold_duration_years and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_type == other.checksum_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'acl',
            'bucket',
            'cache_control',
            'content_disposition',
            'content_encoding',
            'content_language',
            'content_type',
            'expires',
            'grant_full_control',
            'grant_read',
            'grant_read_acp',
            'grant_write_acp',
            'key',
            'metadata',
            'server_side_encryption',
            'storage_class',
            'website_redirect_location',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'request_payer',
            'tagging',
            'object_lock_mode',
            'object_lock_retain_until_date',
            'object_lock_legal_hold_status',
            'object_lock_event_hold',
            'object_lock_event_hold_duration_days',
            'object_lock_event_hold_duration_years',
            'expected_bucket_owner',
            'checksum_algorithm',
            'checksum_type',
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
                self.acl,
                self.bucket,
                self.cache_control,
                self.content_disposition,
                self.content_encoding,
                self.content_language,
                self.content_type,
                self.expires,
                self.grant_full_control,
                self.grant_read,
                self.grant_read_acp,
                self.grant_write_acp,
                self.key,
                self.metadata,
                self.server_side_encryption,
                self.storage_class,
                self.website_redirect_location,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.request_payer,
                self.tagging,
                self.object_lock_mode,
                self.object_lock_retain_until_date,
                self.object_lock_legal_hold_status,
                self.object_lock_event_hold,
                self.object_lock_event_hold_duration_days,
                self.object_lock_event_hold_duration_years,
                self.expected_bucket_owner,
                self.checksum_algorithm,
                self.checksum_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            acl: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            bucket: __dataclass__init__fields__02__annotation,
            cache_control: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            content_disposition: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            content_encoding: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            content_language: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            content_type: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            expires: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            grant_full_control: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            grant_read: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            grant_read_acp: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            grant_write_acp: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            key: __dataclass__init__fields__13__annotation,
            metadata: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            server_side_encryption: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            storage_class: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            website_redirect_location: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            sse_customer_algorithm: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            sse_customer_key: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            sse_customer_key_md5: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            sse_kms_key_id: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            sse_kms_encryption_context: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            bucket_key_enabled: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            request_payer: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            tagging: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            object_lock_mode: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            object_lock_retain_until_date: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            object_lock_legal_hold_status: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            object_lock_event_hold: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            object_lock_event_hold_duration_days: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            object_lock_event_hold_duration_years: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            expected_bucket_owner: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            checksum_algorithm: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            checksum_type: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'acl', acl)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'cache_control', cache_control)
            __dataclass__object_setattr(self, 'content_disposition', content_disposition)
            __dataclass__object_setattr(self, 'content_encoding', content_encoding)
            __dataclass__object_setattr(self, 'content_language', content_language)
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'expires', expires)
            __dataclass__object_setattr(self, 'grant_full_control', grant_full_control)
            __dataclass__object_setattr(self, 'grant_read', grant_read)
            __dataclass__object_setattr(self, 'grant_read_acp', grant_read_acp)
            __dataclass__object_setattr(self, 'grant_write_acp', grant_write_acp)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'website_redirect_location', website_redirect_location)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'tagging', tagging)
            __dataclass__object_setattr(self, 'object_lock_mode', object_lock_mode)
            __dataclass__object_setattr(self, 'object_lock_retain_until_date', object_lock_retain_until_date)
            __dataclass__object_setattr(self, 'object_lock_legal_hold_status', object_lock_legal_hold_status)
            __dataclass__object_setattr(self, 'object_lock_event_hold', object_lock_event_hold)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_days', object_lock_event_hold_duration_days)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_years', object_lock_event_hold_duration_years)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"acl={self.acl!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"cache_control={self.cache_control!r}")
            parts.append(f"content_disposition={self.content_disposition!r}")
            parts.append(f"content_encoding={self.content_encoding!r}")
            parts.append(f"content_language={self.content_language!r}")
            parts.append(f"content_type={self.content_type!r}")
            parts.append(f"expires={self.expires!r}")
            parts.append(f"grant_full_control={self.grant_full_control!r}")
            parts.append(f"grant_read={self.grant_read!r}")
            parts.append(f"grant_read_acp={self.grant_read_acp!r}")
            parts.append(f"grant_write_acp={self.grant_write_acp!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"website_redirect_location={self.website_redirect_location!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"tagging={self.tagging!r}")
            parts.append(f"object_lock_mode={self.object_lock_mode!r}")
            parts.append(f"object_lock_retain_until_date={self.object_lock_retain_until_date!r}")
            parts.append(f"object_lock_legal_hold_status={self.object_lock_legal_hold_status!r}")
            parts.append(f"object_lock_event_hold={self.object_lock_event_hold!r}")
            parts.append(f"object_lock_event_hold_duration_days={self.object_lock_event_hold_duration_days!r}")
            parts.append(f"object_lock_event_hold_duration_years={self.object_lock_event_hold_duration_years!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b1ee0e21166aae7399d2b120f44e6b2d1205fe76',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('objects', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('quiet', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Delete'),
    ),
)
def _process_dataclass__b1ee0e21166aae7399d2b120f44e6b2d1205fe76():
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
                objects=self.objects,
                quiet=self.quiet,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.objects == other.objects and
                self.quiet == other.quiet
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'objects',
            'quiet',
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
                self.objects,
                self.quiet,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            objects: __dataclass__init__fields__1__annotation,
            quiet: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'objects', objects)
            __dataclass__object_setattr(self, 'quiet', quiet)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"objects={self.objects!r}")
            parts.append(f"quiet={self.quiet!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9d67605a5e943dd9bf366ea4b3e5f56d7c530a8c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('expected_bucket_owner', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, F"
            "alse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeleteBucketRequest'),
    ),
)
def _process_dataclass__9d67605a5e943dd9bf366ea4b3e5f56d7c530a8c():
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
                bucket=self.bucket,
                expected_bucket_owner=self.expected_bucket_owner,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.expected_bucket_owner == other.expected_bucket_owner
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'expected_bucket_owner',
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
                self.bucket,
                self.expected_bucket_owner,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__1__annotation,
            expected_bucket_owner: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c640380b71d419edae0169b8ff4814a922fbf32c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('delete_marker', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('request_charged', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeleteObjectOutput'),
    ),
)
def _process_dataclass__c640380b71d419edae0169b8ff4814a922fbf32c():
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
                delete_marker=self.delete_marker,
                version_id=self.version_id,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.delete_marker == other.delete_marker and
                self.version_id == other.version_id and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'delete_marker',
            'version_id',
            'request_charged',
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
                self.delete_marker,
                self.version_id,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            delete_marker: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            version_id: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            request_charged: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'delete_marker', delete_marker)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"delete_marker={self.delete_marker!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='072e57ada3ac0f70059213ace2c0fe73d05c8dfa',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('mfa', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('request_payer', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('bypass_governance_retention', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('if_match', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False), (('if_match_last_modified_time', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('if_match_size"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0,"
            " ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeleteObjectRequest'),
    ),
)
def _process_dataclass__072e57ada3ac0f70059213ace2c0fe73d05c8dfa():
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
                bucket=self.bucket,
                key=self.key,
                mfa=self.mfa,
                version_id=self.version_id,
                request_payer=self.request_payer,
                bypass_governance_retention=self.bypass_governance_retention,
                expected_bucket_owner=self.expected_bucket_owner,
                if_match=self.if_match,
                if_match_last_modified_time=self.if_match_last_modified_time,
                if_match_size=self.if_match_size,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.key == other.key and
                self.mfa == other.mfa and
                self.version_id == other.version_id and
                self.request_payer == other.request_payer and
                self.bypass_governance_retention == other.bypass_governance_retention and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.if_match == other.if_match and
                self.if_match_last_modified_time == other.if_match_last_modified_time and
                self.if_match_size == other.if_match_size
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'key',
            'mfa',
            'version_id',
            'request_payer',
            'bypass_governance_retention',
            'expected_bucket_owner',
            'if_match',
            'if_match_last_modified_time',
            'if_match_size',
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
                self.bucket,
                self.key,
                self.mfa,
                self.version_id,
                self.request_payer,
                self.bypass_governance_retention,
                self.expected_bucket_owner,
                self.if_match,
                self.if_match_last_modified_time,
                self.if_match_size,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation,
            key: __dataclass__init__fields__02__annotation,
            mfa: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            version_id: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            request_payer: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            bypass_governance_retention: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            expected_bucket_owner: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            if_match: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            if_match_last_modified_time: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            if_match_size: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'mfa', mfa)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'bypass_governance_retention', bypass_governance_retention)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'if_match', if_match)
            __dataclass__object_setattr(self, 'if_match_last_modified_time', if_match_last_modified_time)
            __dataclass__object_setattr(self, 'if_match_size', if_match_size)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"mfa={self.mfa!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"bypass_governance_retention={self.bypass_governance_retention!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"if_match={self.if_match!r}")
            parts.append(f"if_match_last_modified_time={self.if_match_last_modified_time!r}")
            parts.append(f"if_match_size={self.if_match_size!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4b31cbeec5d2162bfa9b99773a5532b8ff0d0683',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('deleted', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('request_charged', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('errors', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeleteObjectsOutput'),
    ),
)
def _process_dataclass__4b31cbeec5d2162bfa9b99773a5532b8ff0d0683():
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
                deleted=self.deleted,
                request_charged=self.request_charged,
                errors=self.errors,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.deleted == other.deleted and
                self.request_charged == other.request_charged and
                self.errors == other.errors
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'deleted',
            'request_charged',
            'errors',
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
                self.deleted,
                self.request_charged,
                self.errors,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            deleted: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            request_charged: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            errors: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'deleted', deleted)
            __dataclass__object_setattr(self, 'request_charged', request_charged)
            __dataclass__object_setattr(self, 'errors', errors)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"deleted={self.deleted!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            parts.append(f"errors={self.errors!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e434ba8f53dd211a799a50bd7efed470e8e98823',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('delete', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('mfa', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('request_payer', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('bypass_governance_retention', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('checksum_algorithm', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,),"
            " (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeleteObjectsRequest'),
    ),
)
def _process_dataclass__e434ba8f53dd211a799a50bd7efed470e8e98823():
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
                bucket=self.bucket,
                delete=self.delete,
                mfa=self.mfa,
                request_payer=self.request_payer,
                bypass_governance_retention=self.bypass_governance_retention,
                expected_bucket_owner=self.expected_bucket_owner,
                checksum_algorithm=self.checksum_algorithm,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.delete == other.delete and
                self.mfa == other.mfa and
                self.request_payer == other.request_payer and
                self.bypass_governance_retention == other.bypass_governance_retention and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.checksum_algorithm == other.checksum_algorithm
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'delete',
            'mfa',
            'request_payer',
            'bypass_governance_retention',
            'expected_bucket_owner',
            'checksum_algorithm',
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
                self.bucket,
                self.delete,
                self.mfa,
                self.request_payer,
                self.bypass_governance_retention,
                self.expected_bucket_owner,
                self.checksum_algorithm,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__1__annotation,
            delete: __dataclass__init__fields__2__annotation,
            mfa: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            request_payer: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            bypass_governance_retention: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            expected_bucket_owner: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            checksum_algorithm: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'delete', delete)
            __dataclass__object_setattr(self, 'mfa', mfa)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'bypass_governance_retention', bypass_governance_retention)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"delete={self.delete!r}")
            parts.append(f"mfa={self.mfa!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"bypass_governance_retention={self.bypass_governance_retention!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b4fcdb3b6ee90c312490879f5af3942ad2a54137',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('delete_marker', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('delete_marker_version_id', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (F"
            "alse, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'DeletedObject'),
    ),
)
def _process_dataclass__b4fcdb3b6ee90c312490879f5af3942ad2a54137():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
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
                version_id=self.version_id,
                delete_marker=self.delete_marker,
                delete_marker_version_id=self.delete_marker_version_id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.version_id == other.version_id and
                self.delete_marker == other.delete_marker and
                self.delete_marker_version_id == other.delete_marker_version_id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'key',
            'version_id',
            'delete_marker',
            'delete_marker_version_id',
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
                self.version_id,
                self.delete_marker,
                self.delete_marker_version_id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            version_id: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            delete_marker: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            delete_marker_version_id: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'delete_marker', delete_marker)
            __dataclass__object_setattr(self, 'delete_marker_version_id', delete_marker_version_id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"delete_marker={self.delete_marker!r}")
            parts.append(f"delete_marker_version_id={self.delete_marker_version_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9299836ff2c5926a393f26a11e109afb03f6dce2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('code', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Error'),
    ),
)
def _process_dataclass__9299836ff2c5926a393f26a11e109afb03f6dce2():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
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
                version_id=self.version_id,
                code=self.code,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.version_id == other.version_id and
                self.code == other.code and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'key',
            'version_id',
            'code',
            'message',
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
                self.version_id,
                self.code,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            version_id: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            code: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            message: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'code', code)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"code={self.code!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='64374a85d85ba6accac3c3358bf281032202189d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('body', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('delete_marker', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('accept_ranges', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('expiration', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('restore', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('last_modified', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('content_length', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False), (('etag', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('checksum_crc32', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_s"
            "ha512', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('ch"
            "ecksum_md5', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('checksum_xxhash64', True, True, None, True, True, False, None), 'instance', 'value', None, False, False"
            ", False), (('checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('checksum_type', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('missing_meta', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('version_id', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('cache_control', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('content_disposition', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False), (('content_encoding', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('content_language', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('content_range', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('content_type', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('expires', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('website_redi"
            "rect_location', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False"
            "), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('metadata', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('sse_customer_key_md5', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('sse_kms_key_id', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('bucket_key_enabled', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('storage_class', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('request_charged', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('replication_status', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('parts_count',"
            " True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('tag_count"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object_"
            "lock_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), ("
            "('object_lock_retain_until_date', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('object_lock_legal_hold_status', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('object_lock_event_hold', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold_duration_days', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object_lock_even"
            "t_hold_duration_years', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fals"
            "e, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'GetObjectOutput'),
    ),
)
def _process_dataclass__64374a85d85ba6accac3c3358bf281032202189d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__29__default = __dataclass__spec.fields[29].default.must()
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default = __dataclass__spec.fields[33].default.must()
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__init__fields__35__annotation = __dataclass__spec.fields[35].annotation
        __dataclass__init__fields__35__default = __dataclass__spec.fields[35].default.must()
        __dataclass__init__fields__36__annotation = __dataclass__spec.fields[36].annotation
        __dataclass__init__fields__36__default = __dataclass__spec.fields[36].default.must()
        __dataclass__init__fields__37__annotation = __dataclass__spec.fields[37].annotation
        __dataclass__init__fields__37__default = __dataclass__spec.fields[37].default.must()
        __dataclass__init__fields__38__annotation = __dataclass__spec.fields[38].annotation
        __dataclass__init__fields__38__default = __dataclass__spec.fields[38].default.must()
        __dataclass__init__fields__39__annotation = __dataclass__spec.fields[39].annotation
        __dataclass__init__fields__39__default = __dataclass__spec.fields[39].default.must()
        __dataclass__init__fields__40__annotation = __dataclass__spec.fields[40].annotation
        __dataclass__init__fields__40__default = __dataclass__spec.fields[40].default.must()
        __dataclass__init__fields__41__annotation = __dataclass__spec.fields[41].annotation
        __dataclass__init__fields__41__default = __dataclass__spec.fields[41].default.must()
        __dataclass__init__fields__42__annotation = __dataclass__spec.fields[42].annotation
        __dataclass__init__fields__42__default = __dataclass__spec.fields[42].default.must()
        __dataclass__init__fields__43__annotation = __dataclass__spec.fields[43].annotation
        __dataclass__init__fields__43__default = __dataclass__spec.fields[43].default.must()
        __dataclass__init__fields__44__annotation = __dataclass__spec.fields[44].annotation
        __dataclass__init__fields__44__default = __dataclass__spec.fields[44].default.must()
        __dataclass__init__fields__45__annotation = __dataclass__spec.fields[45].annotation
        __dataclass__init__fields__45__default = __dataclass__spec.fields[45].default.must()
        __dataclass__init__fields__46__annotation = __dataclass__spec.fields[46].annotation
        __dataclass__init__fields__46__default = __dataclass__spec.fields[46].default.must()
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
                delete_marker=self.delete_marker,
                accept_ranges=self.accept_ranges,
                expiration=self.expiration,
                restore=self.restore,
                last_modified=self.last_modified,
                content_length=self.content_length,
                etag=self.etag,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                checksum_type=self.checksum_type,
                missing_meta=self.missing_meta,
                version_id=self.version_id,
                cache_control=self.cache_control,
                content_disposition=self.content_disposition,
                content_encoding=self.content_encoding,
                content_language=self.content_language,
                content_range=self.content_range,
                content_type=self.content_type,
                expires=self.expires,
                website_redirect_location=self.website_redirect_location,
                server_side_encryption=self.server_side_encryption,
                metadata=self.metadata,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                bucket_key_enabled=self.bucket_key_enabled,
                storage_class=self.storage_class,
                request_charged=self.request_charged,
                replication_status=self.replication_status,
                parts_count=self.parts_count,
                tag_count=self.tag_count,
                object_lock_mode=self.object_lock_mode,
                object_lock_retain_until_date=self.object_lock_retain_until_date,
                object_lock_legal_hold_status=self.object_lock_legal_hold_status,
                object_lock_event_hold=self.object_lock_event_hold,
                object_lock_event_hold_duration_days=self.object_lock_event_hold_duration_days,
                object_lock_event_hold_duration_years=self.object_lock_event_hold_duration_years,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.delete_marker == other.delete_marker and
                self.accept_ranges == other.accept_ranges and
                self.expiration == other.expiration and
                self.restore == other.restore and
                self.last_modified == other.last_modified and
                self.content_length == other.content_length and
                self.etag == other.etag and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.checksum_type == other.checksum_type and
                self.missing_meta == other.missing_meta and
                self.version_id == other.version_id and
                self.cache_control == other.cache_control and
                self.content_disposition == other.content_disposition and
                self.content_encoding == other.content_encoding and
                self.content_language == other.content_language and
                self.content_range == other.content_range and
                self.content_type == other.content_type and
                self.expires == other.expires and
                self.website_redirect_location == other.website_redirect_location and
                self.server_side_encryption == other.server_side_encryption and
                self.metadata == other.metadata and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.storage_class == other.storage_class and
                self.request_charged == other.request_charged and
                self.replication_status == other.replication_status and
                self.parts_count == other.parts_count and
                self.tag_count == other.tag_count and
                self.object_lock_mode == other.object_lock_mode and
                self.object_lock_retain_until_date == other.object_lock_retain_until_date and
                self.object_lock_legal_hold_status == other.object_lock_legal_hold_status and
                self.object_lock_event_hold == other.object_lock_event_hold and
                self.object_lock_event_hold_duration_days == other.object_lock_event_hold_duration_days and
                self.object_lock_event_hold_duration_years == other.object_lock_event_hold_duration_years
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'body',
            'delete_marker',
            'accept_ranges',
            'expiration',
            'restore',
            'last_modified',
            'content_length',
            'etag',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'checksum_type',
            'missing_meta',
            'version_id',
            'cache_control',
            'content_disposition',
            'content_encoding',
            'content_language',
            'content_range',
            'content_type',
            'expires',
            'website_redirect_location',
            'server_side_encryption',
            'metadata',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'bucket_key_enabled',
            'storage_class',
            'request_charged',
            'replication_status',
            'parts_count',
            'tag_count',
            'object_lock_mode',
            'object_lock_retain_until_date',
            'object_lock_legal_hold_status',
            'object_lock_event_hold',
            'object_lock_event_hold_duration_days',
            'object_lock_event_hold_duration_years',
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
                self.delete_marker,
                self.accept_ranges,
                self.expiration,
                self.restore,
                self.last_modified,
                self.content_length,
                self.etag,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.checksum_type,
                self.missing_meta,
                self.version_id,
                self.cache_control,
                self.content_disposition,
                self.content_encoding,
                self.content_language,
                self.content_range,
                self.content_type,
                self.expires,
                self.website_redirect_location,
                self.server_side_encryption,
                self.metadata,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.bucket_key_enabled,
                self.storage_class,
                self.request_charged,
                self.replication_status,
                self.parts_count,
                self.tag_count,
                self.object_lock_mode,
                self.object_lock_retain_until_date,
                self.object_lock_legal_hold_status,
                self.object_lock_event_hold,
                self.object_lock_event_hold_duration_days,
                self.object_lock_event_hold_duration_years,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            body: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            delete_marker: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            accept_ranges: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            expiration: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            restore: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            last_modified: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            content_length: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            etag: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_crc32: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_crc32c: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_crc64nvme: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_sha1: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_sha256: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_sha512: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_md5: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            checksum_xxhash64: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            checksum_xxhash3: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            checksum_xxhash128: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            checksum_type: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            missing_meta: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            version_id: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            cache_control: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            content_disposition: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            content_encoding: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            content_language: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            content_range: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            content_type: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            expires: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            website_redirect_location: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            server_side_encryption: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            metadata: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            sse_customer_algorithm: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            sse_customer_key_md5: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            sse_kms_key_id: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            bucket_key_enabled: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            storage_class: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            request_charged: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            replication_status: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            parts_count: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            tag_count: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            object_lock_mode: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            object_lock_retain_until_date: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            object_lock_legal_hold_status: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            object_lock_event_hold: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            object_lock_event_hold_duration_days: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            object_lock_event_hold_duration_years: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'delete_marker', delete_marker)
            __dataclass__object_setattr(self, 'accept_ranges', accept_ranges)
            __dataclass__object_setattr(self, 'expiration', expiration)
            __dataclass__object_setattr(self, 'restore', restore)
            __dataclass__object_setattr(self, 'last_modified', last_modified)
            __dataclass__object_setattr(self, 'content_length', content_length)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'missing_meta', missing_meta)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'cache_control', cache_control)
            __dataclass__object_setattr(self, 'content_disposition', content_disposition)
            __dataclass__object_setattr(self, 'content_encoding', content_encoding)
            __dataclass__object_setattr(self, 'content_language', content_language)
            __dataclass__object_setattr(self, 'content_range', content_range)
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'expires', expires)
            __dataclass__object_setattr(self, 'website_redirect_location', website_redirect_location)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'request_charged', request_charged)
            __dataclass__object_setattr(self, 'replication_status', replication_status)
            __dataclass__object_setattr(self, 'parts_count', parts_count)
            __dataclass__object_setattr(self, 'tag_count', tag_count)
            __dataclass__object_setattr(self, 'object_lock_mode', object_lock_mode)
            __dataclass__object_setattr(self, 'object_lock_retain_until_date', object_lock_retain_until_date)
            __dataclass__object_setattr(self, 'object_lock_legal_hold_status', object_lock_legal_hold_status)
            __dataclass__object_setattr(self, 'object_lock_event_hold', object_lock_event_hold)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_days', object_lock_event_hold_duration_days)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_years', object_lock_event_hold_duration_years)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"delete_marker={self.delete_marker!r}")
            parts.append(f"accept_ranges={self.accept_ranges!r}")
            parts.append(f"expiration={self.expiration!r}")
            parts.append(f"restore={self.restore!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            parts.append(f"content_length={self.content_length!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"missing_meta={self.missing_meta!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"cache_control={self.cache_control!r}")
            parts.append(f"content_disposition={self.content_disposition!r}")
            parts.append(f"content_encoding={self.content_encoding!r}")
            parts.append(f"content_language={self.content_language!r}")
            parts.append(f"content_range={self.content_range!r}")
            parts.append(f"content_type={self.content_type!r}")
            parts.append(f"expires={self.expires!r}")
            parts.append(f"website_redirect_location={self.website_redirect_location!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            parts.append(f"replication_status={self.replication_status!r}")
            parts.append(f"parts_count={self.parts_count!r}")
            parts.append(f"tag_count={self.tag_count!r}")
            parts.append(f"object_lock_mode={self.object_lock_mode!r}")
            parts.append(f"object_lock_retain_until_date={self.object_lock_retain_until_date!r}")
            parts.append(f"object_lock_legal_hold_status={self.object_lock_legal_hold_status!r}")
            parts.append(f"object_lock_event_hold={self.object_lock_event_hold!r}")
            parts.append(f"object_lock_event_hold_duration_days={self.object_lock_event_hold_duration_days!r}")
            parts.append(f"object_lock_event_hold_duration_years={self.object_lock_event_hold_duration_years!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='282829f1b0723f4166f26c5968659dc6e18162e5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('if_match', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('if_modified_since', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('if_none_match', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('if_unmodified_since', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('key', True, True, None, True, True, False,"
            " None), 'instance', 'missing', None, False, False, False), (('range', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('response_cache_control', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('response_content_disposition', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('response_c"
            "ontent_encoding', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('response_content_language', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('response_content_type', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('response_expires', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('version_id', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('request_payer', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('part_number"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('expecte"
            "d_bucket_owner', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('checksum_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, False"
            ", False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'GetObjectRequest'),
        ('ominfra.clouds.aws.models.services.s3', 'HeadObjectRequest'),
    ),
)
def _process_dataclass__282829f1b0723f4166f26c5968659dc6e18162e5():
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
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                bucket=self.bucket,
                if_match=self.if_match,
                if_modified_since=self.if_modified_since,
                if_none_match=self.if_none_match,
                if_unmodified_since=self.if_unmodified_since,
                key=self.key,
                range=self.range,
                response_cache_control=self.response_cache_control,
                response_content_disposition=self.response_content_disposition,
                response_content_encoding=self.response_content_encoding,
                response_content_language=self.response_content_language,
                response_content_type=self.response_content_type,
                response_expires=self.response_expires,
                version_id=self.version_id,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
                request_payer=self.request_payer,
                part_number=self.part_number,
                expected_bucket_owner=self.expected_bucket_owner,
                checksum_mode=self.checksum_mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.if_match == other.if_match and
                self.if_modified_since == other.if_modified_since and
                self.if_none_match == other.if_none_match and
                self.if_unmodified_since == other.if_unmodified_since and
                self.key == other.key and
                self.range == other.range and
                self.response_cache_control == other.response_cache_control and
                self.response_content_disposition == other.response_content_disposition and
                self.response_content_encoding == other.response_content_encoding and
                self.response_content_language == other.response_content_language and
                self.response_content_type == other.response_content_type and
                self.response_expires == other.response_expires and
                self.version_id == other.version_id and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.request_payer == other.request_payer and
                self.part_number == other.part_number and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.checksum_mode == other.checksum_mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'if_match',
            'if_modified_since',
            'if_none_match',
            'if_unmodified_since',
            'key',
            'range',
            'response_cache_control',
            'response_content_disposition',
            'response_content_encoding',
            'response_content_language',
            'response_content_type',
            'response_expires',
            'version_id',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
            'request_payer',
            'part_number',
            'expected_bucket_owner',
            'checksum_mode',
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
                self.bucket,
                self.if_match,
                self.if_modified_since,
                self.if_none_match,
                self.if_unmodified_since,
                self.key,
                self.range,
                self.response_cache_control,
                self.response_content_disposition,
                self.response_content_encoding,
                self.response_content_language,
                self.response_content_type,
                self.response_expires,
                self.version_id,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
                self.request_payer,
                self.part_number,
                self.expected_bucket_owner,
                self.checksum_mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation,
            if_match: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            if_modified_since: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            if_none_match: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            if_unmodified_since: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            key: __dataclass__init__fields__06__annotation,
            range: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            response_cache_control: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            response_content_disposition: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            response_content_encoding: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            response_content_language: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            response_content_type: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            response_expires: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            version_id: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            sse_customer_algorithm: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            sse_customer_key: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            sse_customer_key_md5: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            request_payer: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            part_number: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            expected_bucket_owner: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            checksum_mode: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'if_match', if_match)
            __dataclass__object_setattr(self, 'if_modified_since', if_modified_since)
            __dataclass__object_setattr(self, 'if_none_match', if_none_match)
            __dataclass__object_setattr(self, 'if_unmodified_since', if_unmodified_since)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'range', range)
            __dataclass__object_setattr(self, 'response_cache_control', response_cache_control)
            __dataclass__object_setattr(self, 'response_content_disposition', response_content_disposition)
            __dataclass__object_setattr(self, 'response_content_encoding', response_content_encoding)
            __dataclass__object_setattr(self, 'response_content_language', response_content_language)
            __dataclass__object_setattr(self, 'response_content_type', response_content_type)
            __dataclass__object_setattr(self, 'response_expires', response_expires)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'part_number', part_number)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'checksum_mode', checksum_mode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"if_match={self.if_match!r}")
            parts.append(f"if_modified_since={self.if_modified_since!r}")
            parts.append(f"if_none_match={self.if_none_match!r}")
            parts.append(f"if_unmodified_since={self.if_unmodified_since!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"range={self.range!r}")
            parts.append(f"response_cache_control={self.response_cache_control!r}")
            parts.append(f"response_content_disposition={self.response_content_disposition!r}")
            parts.append(f"response_content_encoding={self.response_content_encoding!r}")
            parts.append(f"response_content_language={self.response_content_language!r}")
            parts.append(f"response_content_type={self.response_content_type!r}")
            parts.append(f"response_expires={self.response_expires!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"part_number={self.part_number!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"checksum_mode={self.checksum_mode!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='39af0461b74ed39f8c54446d7a9d486bb48eb2da',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('delete_marker', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('accept_ranges', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('expiration', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('restore', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('archive_status', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('last_modified', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('content_length', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc32', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc32c', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sh"
            "a1', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('check"
            "sum_sha256', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('checksum_sha512', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('checksum_md5', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('checksum_xxhash64', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('checksum_xxhash128', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('checksum_type', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('missing_meta', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('version_id', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('cache_control', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('content_disposition', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('content_encoding', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('content_language', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('content_type'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('content_"
            "range', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('ex"
            "pires', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('we"
            "bsite_redirect_location', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('metadata', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('sse_kms_key_id', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('bucket_key_enabled', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('storage_class', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('request_charged', True"
            ", True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('replication_st"
            "atus', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('par"
            "ts_count', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'tag_count', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('object_lock_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('object_lock_retain_until_date', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('object_lock_legal_hold_status', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('object_lock_event_hold', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold_duration_day"
            "s', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object"
            "_lock_event_hold_duration_years', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'HeadObjectOutput'),
    ),
)
def _process_dataclass__39af0461b74ed39f8c54446d7a9d486bb48eb2da():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__29__default = __dataclass__spec.fields[29].default.must()
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default = __dataclass__spec.fields[33].default.must()
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__init__fields__35__annotation = __dataclass__spec.fields[35].annotation
        __dataclass__init__fields__35__default = __dataclass__spec.fields[35].default.must()
        __dataclass__init__fields__36__annotation = __dataclass__spec.fields[36].annotation
        __dataclass__init__fields__36__default = __dataclass__spec.fields[36].default.must()
        __dataclass__init__fields__37__annotation = __dataclass__spec.fields[37].annotation
        __dataclass__init__fields__37__default = __dataclass__spec.fields[37].default.must()
        __dataclass__init__fields__38__annotation = __dataclass__spec.fields[38].annotation
        __dataclass__init__fields__38__default = __dataclass__spec.fields[38].default.must()
        __dataclass__init__fields__39__annotation = __dataclass__spec.fields[39].annotation
        __dataclass__init__fields__39__default = __dataclass__spec.fields[39].default.must()
        __dataclass__init__fields__40__annotation = __dataclass__spec.fields[40].annotation
        __dataclass__init__fields__40__default = __dataclass__spec.fields[40].default.must()
        __dataclass__init__fields__41__annotation = __dataclass__spec.fields[41].annotation
        __dataclass__init__fields__41__default = __dataclass__spec.fields[41].default.must()
        __dataclass__init__fields__42__annotation = __dataclass__spec.fields[42].annotation
        __dataclass__init__fields__42__default = __dataclass__spec.fields[42].default.must()
        __dataclass__init__fields__43__annotation = __dataclass__spec.fields[43].annotation
        __dataclass__init__fields__43__default = __dataclass__spec.fields[43].default.must()
        __dataclass__init__fields__44__annotation = __dataclass__spec.fields[44].annotation
        __dataclass__init__fields__44__default = __dataclass__spec.fields[44].default.must()
        __dataclass__init__fields__45__annotation = __dataclass__spec.fields[45].annotation
        __dataclass__init__fields__45__default = __dataclass__spec.fields[45].default.must()
        __dataclass__init__fields__46__annotation = __dataclass__spec.fields[46].annotation
        __dataclass__init__fields__46__default = __dataclass__spec.fields[46].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                delete_marker=self.delete_marker,
                accept_ranges=self.accept_ranges,
                expiration=self.expiration,
                restore=self.restore,
                archive_status=self.archive_status,
                last_modified=self.last_modified,
                content_length=self.content_length,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                checksum_type=self.checksum_type,
                etag=self.etag,
                missing_meta=self.missing_meta,
                version_id=self.version_id,
                cache_control=self.cache_control,
                content_disposition=self.content_disposition,
                content_encoding=self.content_encoding,
                content_language=self.content_language,
                content_type=self.content_type,
                content_range=self.content_range,
                expires=self.expires,
                website_redirect_location=self.website_redirect_location,
                server_side_encryption=self.server_side_encryption,
                metadata=self.metadata,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                bucket_key_enabled=self.bucket_key_enabled,
                storage_class=self.storage_class,
                request_charged=self.request_charged,
                replication_status=self.replication_status,
                parts_count=self.parts_count,
                tag_count=self.tag_count,
                object_lock_mode=self.object_lock_mode,
                object_lock_retain_until_date=self.object_lock_retain_until_date,
                object_lock_legal_hold_status=self.object_lock_legal_hold_status,
                object_lock_event_hold=self.object_lock_event_hold,
                object_lock_event_hold_duration_days=self.object_lock_event_hold_duration_days,
                object_lock_event_hold_duration_years=self.object_lock_event_hold_duration_years,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.delete_marker == other.delete_marker and
                self.accept_ranges == other.accept_ranges and
                self.expiration == other.expiration and
                self.restore == other.restore and
                self.archive_status == other.archive_status and
                self.last_modified == other.last_modified and
                self.content_length == other.content_length and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.checksum_type == other.checksum_type and
                self.etag == other.etag and
                self.missing_meta == other.missing_meta and
                self.version_id == other.version_id and
                self.cache_control == other.cache_control and
                self.content_disposition == other.content_disposition and
                self.content_encoding == other.content_encoding and
                self.content_language == other.content_language and
                self.content_type == other.content_type and
                self.content_range == other.content_range and
                self.expires == other.expires and
                self.website_redirect_location == other.website_redirect_location and
                self.server_side_encryption == other.server_side_encryption and
                self.metadata == other.metadata and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.storage_class == other.storage_class and
                self.request_charged == other.request_charged and
                self.replication_status == other.replication_status and
                self.parts_count == other.parts_count and
                self.tag_count == other.tag_count and
                self.object_lock_mode == other.object_lock_mode and
                self.object_lock_retain_until_date == other.object_lock_retain_until_date and
                self.object_lock_legal_hold_status == other.object_lock_legal_hold_status and
                self.object_lock_event_hold == other.object_lock_event_hold and
                self.object_lock_event_hold_duration_days == other.object_lock_event_hold_duration_days and
                self.object_lock_event_hold_duration_years == other.object_lock_event_hold_duration_years
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'delete_marker',
            'accept_ranges',
            'expiration',
            'restore',
            'archive_status',
            'last_modified',
            'content_length',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'checksum_type',
            'etag',
            'missing_meta',
            'version_id',
            'cache_control',
            'content_disposition',
            'content_encoding',
            'content_language',
            'content_type',
            'content_range',
            'expires',
            'website_redirect_location',
            'server_side_encryption',
            'metadata',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'bucket_key_enabled',
            'storage_class',
            'request_charged',
            'replication_status',
            'parts_count',
            'tag_count',
            'object_lock_mode',
            'object_lock_retain_until_date',
            'object_lock_legal_hold_status',
            'object_lock_event_hold',
            'object_lock_event_hold_duration_days',
            'object_lock_event_hold_duration_years',
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
                self.delete_marker,
                self.accept_ranges,
                self.expiration,
                self.restore,
                self.archive_status,
                self.last_modified,
                self.content_length,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.checksum_type,
                self.etag,
                self.missing_meta,
                self.version_id,
                self.cache_control,
                self.content_disposition,
                self.content_encoding,
                self.content_language,
                self.content_type,
                self.content_range,
                self.expires,
                self.website_redirect_location,
                self.server_side_encryption,
                self.metadata,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.bucket_key_enabled,
                self.storage_class,
                self.request_charged,
                self.replication_status,
                self.parts_count,
                self.tag_count,
                self.object_lock_mode,
                self.object_lock_retain_until_date,
                self.object_lock_legal_hold_status,
                self.object_lock_event_hold,
                self.object_lock_event_hold_duration_days,
                self.object_lock_event_hold_duration_years,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            delete_marker: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            accept_ranges: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            expiration: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            restore: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            archive_status: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            last_modified: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            content_length: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_crc32: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_crc32c: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_crc64nvme: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_sha1: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_sha256: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_sha512: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_md5: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_xxhash64: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            checksum_xxhash3: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            checksum_xxhash128: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            checksum_type: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            etag: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            missing_meta: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            version_id: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            cache_control: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            content_disposition: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            content_encoding: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            content_language: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            content_type: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            content_range: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            expires: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            website_redirect_location: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            server_side_encryption: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            metadata: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            sse_customer_algorithm: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            sse_customer_key_md5: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            sse_kms_key_id: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            bucket_key_enabled: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            storage_class: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            request_charged: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            replication_status: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            parts_count: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            tag_count: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            object_lock_mode: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            object_lock_retain_until_date: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            object_lock_legal_hold_status: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            object_lock_event_hold: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            object_lock_event_hold_duration_days: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            object_lock_event_hold_duration_years: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'delete_marker', delete_marker)
            __dataclass__object_setattr(self, 'accept_ranges', accept_ranges)
            __dataclass__object_setattr(self, 'expiration', expiration)
            __dataclass__object_setattr(self, 'restore', restore)
            __dataclass__object_setattr(self, 'archive_status', archive_status)
            __dataclass__object_setattr(self, 'last_modified', last_modified)
            __dataclass__object_setattr(self, 'content_length', content_length)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'missing_meta', missing_meta)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'cache_control', cache_control)
            __dataclass__object_setattr(self, 'content_disposition', content_disposition)
            __dataclass__object_setattr(self, 'content_encoding', content_encoding)
            __dataclass__object_setattr(self, 'content_language', content_language)
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'content_range', content_range)
            __dataclass__object_setattr(self, 'expires', expires)
            __dataclass__object_setattr(self, 'website_redirect_location', website_redirect_location)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'request_charged', request_charged)
            __dataclass__object_setattr(self, 'replication_status', replication_status)
            __dataclass__object_setattr(self, 'parts_count', parts_count)
            __dataclass__object_setattr(self, 'tag_count', tag_count)
            __dataclass__object_setattr(self, 'object_lock_mode', object_lock_mode)
            __dataclass__object_setattr(self, 'object_lock_retain_until_date', object_lock_retain_until_date)
            __dataclass__object_setattr(self, 'object_lock_legal_hold_status', object_lock_legal_hold_status)
            __dataclass__object_setattr(self, 'object_lock_event_hold', object_lock_event_hold)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_days', object_lock_event_hold_duration_days)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_years', object_lock_event_hold_duration_years)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"delete_marker={self.delete_marker!r}")
            parts.append(f"accept_ranges={self.accept_ranges!r}")
            parts.append(f"expiration={self.expiration!r}")
            parts.append(f"restore={self.restore!r}")
            parts.append(f"archive_status={self.archive_status!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            parts.append(f"content_length={self.content_length!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"missing_meta={self.missing_meta!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"cache_control={self.cache_control!r}")
            parts.append(f"content_disposition={self.content_disposition!r}")
            parts.append(f"content_encoding={self.content_encoding!r}")
            parts.append(f"content_language={self.content_language!r}")
            parts.append(f"content_type={self.content_type!r}")
            parts.append(f"content_range={self.content_range!r}")
            parts.append(f"expires={self.expires!r}")
            parts.append(f"website_redirect_location={self.website_redirect_location!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            parts.append(f"replication_status={self.replication_status!r}")
            parts.append(f"parts_count={self.parts_count!r}")
            parts.append(f"tag_count={self.tag_count!r}")
            parts.append(f"object_lock_mode={self.object_lock_mode!r}")
            parts.append(f"object_lock_retain_until_date={self.object_lock_retain_until_date!r}")
            parts.append(f"object_lock_legal_hold_status={self.object_lock_legal_hold_status!r}")
            parts.append(f"object_lock_event_hold={self.object_lock_event_hold!r}")
            parts.append(f"object_lock_event_hold_duration_days={self.object_lock_event_hold_duration_days!r}")
            parts.append(f"object_lock_event_hold_duration_years={self.object_lock_event_hold_duration_years!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d3ed955322e5ffc24e0e48e149f19da9f7b05a34',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('i_d', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('display_name', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Initiator'),
    ),
)
def _process_dataclass__d3ed955322e5ffc24e0e48e149f19da9f7b05a34():
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
                i_d=self.i_d,
                display_name=self.display_name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.i_d == other.i_d and
                self.display_name == other.display_name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'i_d',
            'display_name',
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
                self.i_d,
                self.display_name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            i_d: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            display_name: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'i_d', i_d)
            __dataclass__object_setattr(self, 'display_name', display_name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"i_d={self.i_d!r}")
            parts.append(f"display_name={self.display_name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='594958d45ecb51d4dc4b41accc48af4817c5b4b9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('storage_class', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('access_tier', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'InvalidObjectState'),
    ),
)
def _process_dataclass__594958d45ecb51d4dc4b41accc48af4817c5b4b9():
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
                storage_class=self.storage_class,
                access_tier=self.access_tier,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.storage_class == other.storage_class and
                self.access_tier == other.access_tier
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'storage_class',
            'access_tier',
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
                self.storage_class,
                self.access_tier,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            storage_class: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            access_tier: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'access_tier', access_tier)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"access_tier={self.access_tier!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ee06c237dd610deda0c484a70c4c48f6c8a1c371',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('buckets', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('owner', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('continuation_token', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListBucketsOutput'),
    ),
)
def _process_dataclass__ee06c237dd610deda0c484a70c4c48f6c8a1c371():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                buckets=self.buckets,
                owner=self.owner,
                continuation_token=self.continuation_token,
                prefix=self.prefix,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.buckets == other.buckets and
                self.owner == other.owner and
                self.continuation_token == other.continuation_token and
                self.prefix == other.prefix
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'buckets',
            'owner',
            'continuation_token',
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
                self.buckets,
                self.owner,
                self.continuation_token,
                self.prefix,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            buckets: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            owner: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            continuation_token: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            prefix: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'buckets', buckets)
            __dataclass__object_setattr(self, 'owner', owner)
            __dataclass__object_setattr(self, 'continuation_token', continuation_token)
            __dataclass__object_setattr(self, 'prefix', prefix)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"buckets={self.buckets!r}")
            parts.append(f"owner={self.owner!r}")
            parts.append(f"continuation_token={self.continuation_token!r}")
            parts.append(f"prefix={self.prefix!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='639c5d1d6b64f8cc21290ca2815562914965c20d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('max_buckets', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('continuation_token', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('bucket_region', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (Fal"
            "se, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListBucketsRequest'),
    ),
)
def _process_dataclass__639c5d1d6b64f8cc21290ca2815562914965c20d():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                max_buckets=self.max_buckets,
                continuation_token=self.continuation_token,
                prefix=self.prefix,
                bucket_region=self.bucket_region,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.max_buckets == other.max_buckets and
                self.continuation_token == other.continuation_token and
                self.prefix == other.prefix and
                self.bucket_region == other.bucket_region
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'max_buckets',
            'continuation_token',
            'prefix',
            'bucket_region',
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
                self.max_buckets,
                self.continuation_token,
                self.prefix,
                self.bucket_region,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            max_buckets: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            continuation_token: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            prefix: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            bucket_region: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'max_buckets', max_buckets)
            __dataclass__object_setattr(self, 'continuation_token', continuation_token)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'bucket_region', bucket_region)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"max_buckets={self.max_buckets!r}")
            parts.append(f"continuation_token={self.continuation_token!r}")
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"bucket_region={self.bucket_region!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5e99ec775ba1f4870fa252e1cc2a4e2c86d78bad',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('key_marker', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('upload_id_marker', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('next_key_marker', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('prefix', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('delimiter', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('next_upload_id_marker', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('max_uploads', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('is_truncated', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('uploads', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('common_prefixes', True, True,"
            " None, True, True, False, None), 'instance', 'value', None, False, False, False), (('encoding_type', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('request_charged"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0,"
            " ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListMultipartUploadsOutput'),
    ),
)
def _process_dataclass__5e99ec775ba1f4870fa252e1cc2a4e2c86d78bad():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                bucket=self.bucket,
                key_marker=self.key_marker,
                upload_id_marker=self.upload_id_marker,
                next_key_marker=self.next_key_marker,
                prefix=self.prefix,
                delimiter=self.delimiter,
                next_upload_id_marker=self.next_upload_id_marker,
                max_uploads=self.max_uploads,
                is_truncated=self.is_truncated,
                uploads=self.uploads,
                common_prefixes=self.common_prefixes,
                encoding_type=self.encoding_type,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.key_marker == other.key_marker and
                self.upload_id_marker == other.upload_id_marker and
                self.next_key_marker == other.next_key_marker and
                self.prefix == other.prefix and
                self.delimiter == other.delimiter and
                self.next_upload_id_marker == other.next_upload_id_marker and
                self.max_uploads == other.max_uploads and
                self.is_truncated == other.is_truncated and
                self.uploads == other.uploads and
                self.common_prefixes == other.common_prefixes and
                self.encoding_type == other.encoding_type and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'key_marker',
            'upload_id_marker',
            'next_key_marker',
            'prefix',
            'delimiter',
            'next_upload_id_marker',
            'max_uploads',
            'is_truncated',
            'uploads',
            'common_prefixes',
            'encoding_type',
            'request_charged',
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
                self.bucket,
                self.key_marker,
                self.upload_id_marker,
                self.next_key_marker,
                self.prefix,
                self.delimiter,
                self.next_upload_id_marker,
                self.max_uploads,
                self.is_truncated,
                self.uploads,
                self.common_prefixes,
                self.encoding_type,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            key_marker: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            upload_id_marker: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            next_key_marker: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            prefix: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            delimiter: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            next_upload_id_marker: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            max_uploads: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            is_truncated: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            uploads: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            common_prefixes: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            encoding_type: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            request_charged: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'key_marker', key_marker)
            __dataclass__object_setattr(self, 'upload_id_marker', upload_id_marker)
            __dataclass__object_setattr(self, 'next_key_marker', next_key_marker)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'delimiter', delimiter)
            __dataclass__object_setattr(self, 'next_upload_id_marker', next_upload_id_marker)
            __dataclass__object_setattr(self, 'max_uploads', max_uploads)
            __dataclass__object_setattr(self, 'is_truncated', is_truncated)
            __dataclass__object_setattr(self, 'uploads', uploads)
            __dataclass__object_setattr(self, 'common_prefixes', common_prefixes)
            __dataclass__object_setattr(self, 'encoding_type', encoding_type)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"key_marker={self.key_marker!r}")
            parts.append(f"upload_id_marker={self.upload_id_marker!r}")
            parts.append(f"next_key_marker={self.next_key_marker!r}")
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"delimiter={self.delimiter!r}")
            parts.append(f"next_upload_id_marker={self.next_upload_id_marker!r}")
            parts.append(f"max_uploads={self.max_uploads!r}")
            parts.append(f"is_truncated={self.is_truncated!r}")
            parts.append(f"uploads={self.uploads!r}")
            parts.append(f"common_prefixes={self.common_prefixes!r}")
            parts.append(f"encoding_type={self.encoding_type!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3c18b94ef253dc5672e86f3a8ccc601a34525167',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('delimiter', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('encoding_type', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('key_marker', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('max_uploads', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('upload_id_marker', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('request_payer', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (Fal"
            "se,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListMultipartUploadsRequest'),
    ),
)
def _process_dataclass__3c18b94ef253dc5672e86f3a8ccc601a34525167():
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
                bucket=self.bucket,
                delimiter=self.delimiter,
                encoding_type=self.encoding_type,
                key_marker=self.key_marker,
                max_uploads=self.max_uploads,
                prefix=self.prefix,
                upload_id_marker=self.upload_id_marker,
                expected_bucket_owner=self.expected_bucket_owner,
                request_payer=self.request_payer,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.delimiter == other.delimiter and
                self.encoding_type == other.encoding_type and
                self.key_marker == other.key_marker and
                self.max_uploads == other.max_uploads and
                self.prefix == other.prefix and
                self.upload_id_marker == other.upload_id_marker and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.request_payer == other.request_payer
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'delimiter',
            'encoding_type',
            'key_marker',
            'max_uploads',
            'prefix',
            'upload_id_marker',
            'expected_bucket_owner',
            'request_payer',
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
                self.bucket,
                self.delimiter,
                self.encoding_type,
                self.key_marker,
                self.max_uploads,
                self.prefix,
                self.upload_id_marker,
                self.expected_bucket_owner,
                self.request_payer,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation,
            delimiter: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            encoding_type: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            key_marker: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            max_uploads: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            prefix: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            upload_id_marker: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            expected_bucket_owner: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            request_payer: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'delimiter', delimiter)
            __dataclass__object_setattr(self, 'encoding_type', encoding_type)
            __dataclass__object_setattr(self, 'key_marker', key_marker)
            __dataclass__object_setattr(self, 'max_uploads', max_uploads)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'upload_id_marker', upload_id_marker)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'request_payer', request_payer)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"delimiter={self.delimiter!r}")
            parts.append(f"encoding_type={self.encoding_type!r}")
            parts.append(f"key_marker={self.key_marker!r}")
            parts.append(f"max_uploads={self.max_uploads!r}")
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"upload_id_marker={self.upload_id_marker!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e929dd153441ce9f46bd99ffbf0723eb3e26ee7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('is_truncated', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('contents', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('delimiter', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('max_keys', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('common_prefixes', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('encoding_type', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('key_count', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('continuation_token', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('next_continuation_token', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('start_after', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('request_charged', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()),"
            " ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListObjectsV2Output'),
    ),
)
def _process_dataclass__e929dd153441ce9f46bd99ffbf0723eb3e26ee7c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                is_truncated=self.is_truncated,
                contents=self.contents,
                name=self.name,
                prefix=self.prefix,
                delimiter=self.delimiter,
                max_keys=self.max_keys,
                common_prefixes=self.common_prefixes,
                encoding_type=self.encoding_type,
                key_count=self.key_count,
                continuation_token=self.continuation_token,
                next_continuation_token=self.next_continuation_token,
                start_after=self.start_after,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.is_truncated == other.is_truncated and
                self.contents == other.contents and
                self.name == other.name and
                self.prefix == other.prefix and
                self.delimiter == other.delimiter and
                self.max_keys == other.max_keys and
                self.common_prefixes == other.common_prefixes and
                self.encoding_type == other.encoding_type and
                self.key_count == other.key_count and
                self.continuation_token == other.continuation_token and
                self.next_continuation_token == other.next_continuation_token and
                self.start_after == other.start_after and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'is_truncated',
            'contents',
            'name',
            'prefix',
            'delimiter',
            'max_keys',
            'common_prefixes',
            'encoding_type',
            'key_count',
            'continuation_token',
            'next_continuation_token',
            'start_after',
            'request_charged',
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
                self.is_truncated,
                self.contents,
                self.name,
                self.prefix,
                self.delimiter,
                self.max_keys,
                self.common_prefixes,
                self.encoding_type,
                self.key_count,
                self.continuation_token,
                self.next_continuation_token,
                self.start_after,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            is_truncated: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            contents: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            name: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            prefix: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            delimiter: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            max_keys: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            common_prefixes: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            encoding_type: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            key_count: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            continuation_token: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            next_continuation_token: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            start_after: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            request_charged: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'is_truncated', is_truncated)
            __dataclass__object_setattr(self, 'contents', contents)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'delimiter', delimiter)
            __dataclass__object_setattr(self, 'max_keys', max_keys)
            __dataclass__object_setattr(self, 'common_prefixes', common_prefixes)
            __dataclass__object_setattr(self, 'encoding_type', encoding_type)
            __dataclass__object_setattr(self, 'key_count', key_count)
            __dataclass__object_setattr(self, 'continuation_token', continuation_token)
            __dataclass__object_setattr(self, 'next_continuation_token', next_continuation_token)
            __dataclass__object_setattr(self, 'start_after', start_after)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"is_truncated={self.is_truncated!r}")
            parts.append(f"contents={self.contents!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"delimiter={self.delimiter!r}")
            parts.append(f"max_keys={self.max_keys!r}")
            parts.append(f"common_prefixes={self.common_prefixes!r}")
            parts.append(f"encoding_type={self.encoding_type!r}")
            parts.append(f"key_count={self.key_count!r}")
            parts.append(f"continuation_token={self.continuation_token!r}")
            parts.append(f"next_continuation_token={self.next_continuation_token!r}")
            parts.append(f"start_after={self.start_after!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2dd2e9589095a8478c7afbe700b7b310f1acc4ac',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('delimiter', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('encoding_type', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('max_keys', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('prefix', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('continuation_token', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('fetch_owner', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('start_after', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('request_payer', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('expected_bucket_owner', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('optional_object_attribut"
            "es', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, "
            "0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ListObjectsV2Request'),
    ),
)
def _process_dataclass__2dd2e9589095a8478c7afbe700b7b310f1acc4ac():
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
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                bucket=self.bucket,
                delimiter=self.delimiter,
                encoding_type=self.encoding_type,
                max_keys=self.max_keys,
                prefix=self.prefix,
                continuation_token=self.continuation_token,
                fetch_owner=self.fetch_owner,
                start_after=self.start_after,
                request_payer=self.request_payer,
                expected_bucket_owner=self.expected_bucket_owner,
                optional_object_attributes=self.optional_object_attributes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.bucket == other.bucket and
                self.delimiter == other.delimiter and
                self.encoding_type == other.encoding_type and
                self.max_keys == other.max_keys and
                self.prefix == other.prefix and
                self.continuation_token == other.continuation_token and
                self.fetch_owner == other.fetch_owner and
                self.start_after == other.start_after and
                self.request_payer == other.request_payer and
                self.expected_bucket_owner == other.expected_bucket_owner and
                self.optional_object_attributes == other.optional_object_attributes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'bucket',
            'delimiter',
            'encoding_type',
            'max_keys',
            'prefix',
            'continuation_token',
            'fetch_owner',
            'start_after',
            'request_payer',
            'expected_bucket_owner',
            'optional_object_attributes',
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
                self.bucket,
                self.delimiter,
                self.encoding_type,
                self.max_keys,
                self.prefix,
                self.continuation_token,
                self.fetch_owner,
                self.start_after,
                self.request_payer,
                self.expected_bucket_owner,
                self.optional_object_attributes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            bucket: __dataclass__init__fields__01__annotation,
            delimiter: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            encoding_type: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            max_keys: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            prefix: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            continuation_token: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            fetch_owner: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            start_after: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            request_payer: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            expected_bucket_owner: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            optional_object_attributes: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'delimiter', delimiter)
            __dataclass__object_setattr(self, 'encoding_type', encoding_type)
            __dataclass__object_setattr(self, 'max_keys', max_keys)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'continuation_token', continuation_token)
            __dataclass__object_setattr(self, 'fetch_owner', fetch_owner)
            __dataclass__object_setattr(self, 'start_after', start_after)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)
            __dataclass__object_setattr(self, 'optional_object_attributes', optional_object_attributes)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"delimiter={self.delimiter!r}")
            parts.append(f"encoding_type={self.encoding_type!r}")
            parts.append(f"max_keys={self.max_keys!r}")
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"continuation_token={self.continuation_token!r}")
            parts.append(f"fetch_owner={self.fetch_owner!r}")
            parts.append(f"start_after={self.start_after!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            parts.append(f"optional_object_attributes={self.optional_object_attributes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='05f6a19655be55cf13bec38a3f9d9b8c0b67856c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'LocationInfo'),
    ),
)
def _process_dataclass__05f6a19655be55cf13bec38a3f9d9b8c0b67856c():
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
                type=self.type,
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'type',
            'name',
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
                self.type,
                self.name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            name: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"name={self.name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='218cf0285f0e639a9dfaf14a750f02fef7425459',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('initiated', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('storage_class', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('owner', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('initiator', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('checksum_algorithm', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('checksum_type', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), ("
            "False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'MultipartUpload'),
    ),
)
def _process_dataclass__218cf0285f0e639a9dfaf14a750f02fef7425459():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__8__default = __dataclass__spec.fields[8].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                upload_id=self.upload_id,
                key=self.key,
                initiated=self.initiated,
                storage_class=self.storage_class,
                owner=self.owner,
                initiator=self.initiator,
                checksum_algorithm=self.checksum_algorithm,
                checksum_type=self.checksum_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.upload_id == other.upload_id and
                self.key == other.key and
                self.initiated == other.initiated and
                self.storage_class == other.storage_class and
                self.owner == other.owner and
                self.initiator == other.initiator and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_type == other.checksum_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'upload_id',
            'key',
            'initiated',
            'storage_class',
            'owner',
            'initiator',
            'checksum_algorithm',
            'checksum_type',
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
                self.upload_id,
                self.key,
                self.initiated,
                self.storage_class,
                self.owner,
                self.initiator,
                self.checksum_algorithm,
                self.checksum_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            upload_id: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            key: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            initiated: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            storage_class: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            owner: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            initiator: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            checksum_algorithm: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            checksum_type: __dataclass__init__fields__8__annotation = __dataclass__init__fields__8__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'initiated', initiated)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'owner', owner)
            __dataclass__object_setattr(self, 'initiator', initiator)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"initiated={self.initiated!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"owner={self.owner!r}")
            parts.append(f"initiator={self.initiator!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1c9f584c09f48e0a3672db72cf60279fe598ae05',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('last_modified', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('checksum_algorithm', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('checksum_type', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('size', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('storage_class', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('owner', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('restore_status', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), "
            "(False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Object'),
    ),
)
def _process_dataclass__1c9f584c09f48e0a3672db72cf60279fe598ae05():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
                last_modified=self.last_modified,
                etag=self.etag,
                checksum_algorithm=self.checksum_algorithm,
                checksum_type=self.checksum_type,
                size=self.size,
                storage_class=self.storage_class,
                owner=self.owner,
                restore_status=self.restore_status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.last_modified == other.last_modified and
                self.etag == other.etag and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_type == other.checksum_type and
                self.size == other.size and
                self.storage_class == other.storage_class and
                self.owner == other.owner and
                self.restore_status == other.restore_status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'key',
            'last_modified',
            'etag',
            'checksum_algorithm',
            'checksum_type',
            'size',
            'storage_class',
            'owner',
            'restore_status',
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
                self.last_modified,
                self.etag,
                self.checksum_algorithm,
                self.checksum_type,
                self.size,
                self.storage_class,
                self.owner,
                self.restore_status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            last_modified: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            etag: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_algorithm: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_type: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            size: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            storage_class: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            owner: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            restore_status: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'last_modified', last_modified)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'owner', owner)
            __dataclass__object_setattr(self, 'restore_status', restore_status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"size={self.size!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"owner={self.owner!r}")
            parts.append(f"restore_status={self.restore_status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c72f0825f47c053d26bcb57be6889f14d282a406',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('last_modified_time', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('size', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'ObjectIdentifier'),
    ),
)
def _process_dataclass__c72f0825f47c053d26bcb57be6889f14d282a406():
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
                version_id=self.version_id,
                etag=self.etag,
                last_modified_time=self.last_modified_time,
                size=self.size,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.version_id == other.version_id and
                self.etag == other.etag and
                self.last_modified_time == other.last_modified_time and
                self.size == other.size
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'key',
            'version_id',
            'etag',
            'last_modified_time',
            'size',
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
                self.version_id,
                self.etag,
                self.last_modified_time,
                self.size,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__1__annotation,
            version_id: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            etag: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            last_modified_time: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            size: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'last_modified_time', last_modified_time)
            __dataclass__object_setattr(self, 'size', size)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"last_modified_time={self.last_modified_time!r}")
            parts.append(f"size={self.size!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='14281f30b02e5d9bea9e43c7d565bcc2980ed16d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('display_name', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('i_d', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'Owner'),
    ),
)
def _process_dataclass__14281f30b02e5d9bea9e43c7d565bcc2980ed16d():
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
                display_name=self.display_name,
                i_d=self.i_d,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.display_name == other.display_name and
                self.i_d == other.i_d
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'display_name',
            'i_d',
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
                self.display_name,
                self.i_d,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            display_name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            i_d: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'display_name', display_name)
            __dataclass__object_setattr(self, 'i_d', i_d)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"display_name={self.display_name!r}")
            parts.append(f"i_d={self.i_d!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7ea0b41f63b50f0eb8dab0ee2cf2d9fe24eae6a9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('expiration', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_xxhash64',"
            " True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_"
            "xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('checksum_type', True, True, None, True, True, False, None), 'instance', 'value', None, False, F"
            "alse, False), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('version_id', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('sse_kms_key_id', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_encryption_context', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('bucket_key_enable"
            "d', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('size',"
            " True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('request_c"
            "harged', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), Fal"
            "se, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'PutObjectOutput'),
    ),
)
def _process_dataclass__7ea0b41f63b50f0eb8dab0ee2cf2d9fe24eae6a9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                expiration=self.expiration,
                etag=self.etag,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                checksum_type=self.checksum_type,
                server_side_encryption=self.server_side_encryption,
                version_id=self.version_id,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                size=self.size,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.expiration == other.expiration and
                self.etag == other.etag and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.checksum_type == other.checksum_type and
                self.server_side_encryption == other.server_side_encryption and
                self.version_id == other.version_id and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.size == other.size and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'expiration',
            'etag',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'checksum_type',
            'server_side_encryption',
            'version_id',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'size',
            'request_charged',
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
                self.expiration,
                self.etag,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.checksum_type,
                self.server_side_encryption,
                self.version_id,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.size,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            expiration: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            etag: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            checksum_crc32: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_crc32c: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_crc64nvme: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_sha1: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_sha256: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_sha512: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_md5: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_xxhash64: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_xxhash3: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_xxhash128: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_type: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            server_side_encryption: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            version_id: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            sse_customer_algorithm: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            sse_customer_key_md5: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            sse_kms_key_id: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            sse_kms_encryption_context: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            bucket_key_enabled: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            size: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            request_charged: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'expiration', expiration)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'checksum_type', checksum_type)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'version_id', version_id)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"expiration={self.expiration!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"checksum_type={self.checksum_type!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"version_id={self.version_id!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"size={self.size!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1924d077c62431e3f24db18b50979ed99fa55db1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('acl', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('body', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('cache_control', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('content_disposition', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('content_encoding', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('content_language', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('content_length', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('content_md5', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('content_type', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_algorithm', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc32'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum"
            "_crc32c', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "checksum_crc64nvme', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('checksum_sha1', True, True, None, True, True, False, None), 'instance', 'value', None, False, F"
            "alse, False), (('checksum_sha256', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('checksum_sha512', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('checksum_md5', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('checksum_xxhash64', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('checksum_xxhash3', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('checksum_xxhash128', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('expires', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('if_match', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('if_none_match', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('grant_full_control', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_read', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_read_acp', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('grant_writ"
            "e_acp', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('ke"
            "y', True, True, None, True, True, False, None), 'instance', 'missing', None, False, False, False), (('writ"
            "e_offset_bytes', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('metadata', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('server_side_encryption', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('storage_class', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('website_redirect_location', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('sse_customer_key', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_key_id', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sse_kms_encrypt"
            "ion_context', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False),"
            " (('bucket_key_enabled', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('request_payer', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('tagging', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('object_lock_mode', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('object_lock_retain_until_date', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('object_lock_legal_hold_status', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('object_lock_event_hold', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('object_lock_event"
            "_hold_duration_days', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('object_lock_event_hold_duration_years', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('expected_bucket_owner', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (F"
            "alse, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'PutObjectRequest'),
    ),
)
def _process_dataclass__1924d077c62431e3f24db18b50979ed99fa55db1():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default = __dataclass__spec.fields[33].default.must()
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__init__fields__35__annotation = __dataclass__spec.fields[35].annotation
        __dataclass__init__fields__35__default = __dataclass__spec.fields[35].default.must()
        __dataclass__init__fields__36__annotation = __dataclass__spec.fields[36].annotation
        __dataclass__init__fields__36__default = __dataclass__spec.fields[36].default.must()
        __dataclass__init__fields__37__annotation = __dataclass__spec.fields[37].annotation
        __dataclass__init__fields__37__default = __dataclass__spec.fields[37].default.must()
        __dataclass__init__fields__38__annotation = __dataclass__spec.fields[38].annotation
        __dataclass__init__fields__38__default = __dataclass__spec.fields[38].default.must()
        __dataclass__init__fields__39__annotation = __dataclass__spec.fields[39].annotation
        __dataclass__init__fields__39__default = __dataclass__spec.fields[39].default.must()
        __dataclass__init__fields__40__annotation = __dataclass__spec.fields[40].annotation
        __dataclass__init__fields__40__default = __dataclass__spec.fields[40].default.must()
        __dataclass__init__fields__41__annotation = __dataclass__spec.fields[41].annotation
        __dataclass__init__fields__41__default = __dataclass__spec.fields[41].default.must()
        __dataclass__init__fields__42__annotation = __dataclass__spec.fields[42].annotation
        __dataclass__init__fields__42__default = __dataclass__spec.fields[42].default.must()
        __dataclass__init__fields__43__annotation = __dataclass__spec.fields[43].annotation
        __dataclass__init__fields__43__default = __dataclass__spec.fields[43].default.must()
        __dataclass__init__fields__44__annotation = __dataclass__spec.fields[44].annotation
        __dataclass__init__fields__44__default = __dataclass__spec.fields[44].default.must()
        __dataclass__init__fields__45__annotation = __dataclass__spec.fields[45].annotation
        __dataclass__init__fields__45__default = __dataclass__spec.fields[45].default.must()
        __dataclass__init__fields__46__annotation = __dataclass__spec.fields[46].annotation
        __dataclass__init__fields__46__default = __dataclass__spec.fields[46].default.must()
        __dataclass__init__fields__47__annotation = __dataclass__spec.fields[47].annotation
        __dataclass__init__fields__47__default = __dataclass__spec.fields[47].default.must()
        __dataclass__init__fields__48__annotation = __dataclass__spec.fields[48].annotation
        __dataclass__init__fields__48__default = __dataclass__spec.fields[48].default.must()
        __dataclass__init__fields__49__annotation = __dataclass__spec.fields[49].annotation
        __dataclass__init__fields__49__default = __dataclass__spec.fields[49].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                acl=self.acl,
                body=self.body,
                bucket=self.bucket,
                cache_control=self.cache_control,
                content_disposition=self.content_disposition,
                content_encoding=self.content_encoding,
                content_language=self.content_language,
                content_length=self.content_length,
                content_md5=self.content_md5,
                content_type=self.content_type,
                checksum_algorithm=self.checksum_algorithm,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                expires=self.expires,
                if_match=self.if_match,
                if_none_match=self.if_none_match,
                grant_full_control=self.grant_full_control,
                grant_read=self.grant_read,
                grant_read_acp=self.grant_read_acp,
                grant_write_acp=self.grant_write_acp,
                key=self.key,
                write_offset_bytes=self.write_offset_bytes,
                metadata=self.metadata,
                server_side_encryption=self.server_side_encryption,
                storage_class=self.storage_class,
                website_redirect_location=self.website_redirect_location,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                sse_kms_encryption_context=self.sse_kms_encryption_context,
                bucket_key_enabled=self.bucket_key_enabled,
                request_payer=self.request_payer,
                tagging=self.tagging,
                object_lock_mode=self.object_lock_mode,
                object_lock_retain_until_date=self.object_lock_retain_until_date,
                object_lock_legal_hold_status=self.object_lock_legal_hold_status,
                object_lock_event_hold=self.object_lock_event_hold,
                object_lock_event_hold_duration_days=self.object_lock_event_hold_duration_days,
                object_lock_event_hold_duration_years=self.object_lock_event_hold_duration_years,
                expected_bucket_owner=self.expected_bucket_owner,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.acl == other.acl and
                self.body == other.body and
                self.bucket == other.bucket and
                self.cache_control == other.cache_control and
                self.content_disposition == other.content_disposition and
                self.content_encoding == other.content_encoding and
                self.content_language == other.content_language and
                self.content_length == other.content_length and
                self.content_md5 == other.content_md5 and
                self.content_type == other.content_type and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.expires == other.expires and
                self.if_match == other.if_match and
                self.if_none_match == other.if_none_match and
                self.grant_full_control == other.grant_full_control and
                self.grant_read == other.grant_read and
                self.grant_read_acp == other.grant_read_acp and
                self.grant_write_acp == other.grant_write_acp and
                self.key == other.key and
                self.write_offset_bytes == other.write_offset_bytes and
                self.metadata == other.metadata and
                self.server_side_encryption == other.server_side_encryption and
                self.storage_class == other.storage_class and
                self.website_redirect_location == other.website_redirect_location and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.sse_kms_encryption_context == other.sse_kms_encryption_context and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_payer == other.request_payer and
                self.tagging == other.tagging and
                self.object_lock_mode == other.object_lock_mode and
                self.object_lock_retain_until_date == other.object_lock_retain_until_date and
                self.object_lock_legal_hold_status == other.object_lock_legal_hold_status and
                self.object_lock_event_hold == other.object_lock_event_hold and
                self.object_lock_event_hold_duration_days == other.object_lock_event_hold_duration_days and
                self.object_lock_event_hold_duration_years == other.object_lock_event_hold_duration_years and
                self.expected_bucket_owner == other.expected_bucket_owner
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'acl',
            'body',
            'bucket',
            'cache_control',
            'content_disposition',
            'content_encoding',
            'content_language',
            'content_length',
            'content_md5',
            'content_type',
            'checksum_algorithm',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'expires',
            'if_match',
            'if_none_match',
            'grant_full_control',
            'grant_read',
            'grant_read_acp',
            'grant_write_acp',
            'key',
            'write_offset_bytes',
            'metadata',
            'server_side_encryption',
            'storage_class',
            'website_redirect_location',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'sse_kms_encryption_context',
            'bucket_key_enabled',
            'request_payer',
            'tagging',
            'object_lock_mode',
            'object_lock_retain_until_date',
            'object_lock_legal_hold_status',
            'object_lock_event_hold',
            'object_lock_event_hold_duration_days',
            'object_lock_event_hold_duration_years',
            'expected_bucket_owner',
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
                self.acl,
                self.body,
                self.bucket,
                self.cache_control,
                self.content_disposition,
                self.content_encoding,
                self.content_language,
                self.content_length,
                self.content_md5,
                self.content_type,
                self.checksum_algorithm,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.expires,
                self.if_match,
                self.if_none_match,
                self.grant_full_control,
                self.grant_read,
                self.grant_read_acp,
                self.grant_write_acp,
                self.key,
                self.write_offset_bytes,
                self.metadata,
                self.server_side_encryption,
                self.storage_class,
                self.website_redirect_location,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.sse_kms_encryption_context,
                self.bucket_key_enabled,
                self.request_payer,
                self.tagging,
                self.object_lock_mode,
                self.object_lock_retain_until_date,
                self.object_lock_legal_hold_status,
                self.object_lock_event_hold,
                self.object_lock_event_hold_duration_days,
                self.object_lock_event_hold_duration_years,
                self.expected_bucket_owner,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            acl: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            body: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            bucket: __dataclass__init__fields__03__annotation,
            cache_control: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            content_disposition: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            content_encoding: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            content_language: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            content_length: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            content_md5: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            content_type: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_algorithm: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_crc32: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_crc32c: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_crc64nvme: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_sha1: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            checksum_sha256: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            checksum_sha512: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            checksum_md5: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            checksum_xxhash64: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            checksum_xxhash3: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            checksum_xxhash128: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            expires: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            if_match: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            if_none_match: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            grant_full_control: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            grant_read: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            grant_read_acp: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            grant_write_acp: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            key: __dataclass__init__fields__29__annotation,
            write_offset_bytes: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            metadata: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            server_side_encryption: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            storage_class: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            website_redirect_location: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            sse_customer_algorithm: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            sse_customer_key: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            sse_customer_key_md5: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            sse_kms_key_id: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            sse_kms_encryption_context: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            bucket_key_enabled: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            request_payer: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            tagging: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            object_lock_mode: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            object_lock_retain_until_date: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            object_lock_legal_hold_status: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            object_lock_event_hold: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
            object_lock_event_hold_duration_days: __dataclass__init__fields__47__annotation = __dataclass__init__fields__47__default,
            object_lock_event_hold_duration_years: __dataclass__init__fields__48__annotation = __dataclass__init__fields__48__default,
            expected_bucket_owner: __dataclass__init__fields__49__annotation = __dataclass__init__fields__49__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'acl', acl)
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'cache_control', cache_control)
            __dataclass__object_setattr(self, 'content_disposition', content_disposition)
            __dataclass__object_setattr(self, 'content_encoding', content_encoding)
            __dataclass__object_setattr(self, 'content_language', content_language)
            __dataclass__object_setattr(self, 'content_length', content_length)
            __dataclass__object_setattr(self, 'content_md5', content_md5)
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'expires', expires)
            __dataclass__object_setattr(self, 'if_match', if_match)
            __dataclass__object_setattr(self, 'if_none_match', if_none_match)
            __dataclass__object_setattr(self, 'grant_full_control', grant_full_control)
            __dataclass__object_setattr(self, 'grant_read', grant_read)
            __dataclass__object_setattr(self, 'grant_read_acp', grant_read_acp)
            __dataclass__object_setattr(self, 'grant_write_acp', grant_write_acp)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'write_offset_bytes', write_offset_bytes)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'storage_class', storage_class)
            __dataclass__object_setattr(self, 'website_redirect_location', website_redirect_location)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'sse_kms_encryption_context', sse_kms_encryption_context)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'tagging', tagging)
            __dataclass__object_setattr(self, 'object_lock_mode', object_lock_mode)
            __dataclass__object_setattr(self, 'object_lock_retain_until_date', object_lock_retain_until_date)
            __dataclass__object_setattr(self, 'object_lock_legal_hold_status', object_lock_legal_hold_status)
            __dataclass__object_setattr(self, 'object_lock_event_hold', object_lock_event_hold)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_days', object_lock_event_hold_duration_days)
            __dataclass__object_setattr(self, 'object_lock_event_hold_duration_years', object_lock_event_hold_duration_years)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"acl={self.acl!r}")
            parts.append(f"body={self.body!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"cache_control={self.cache_control!r}")
            parts.append(f"content_disposition={self.content_disposition!r}")
            parts.append(f"content_encoding={self.content_encoding!r}")
            parts.append(f"content_language={self.content_language!r}")
            parts.append(f"content_length={self.content_length!r}")
            parts.append(f"content_md5={self.content_md5!r}")
            parts.append(f"content_type={self.content_type!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"expires={self.expires!r}")
            parts.append(f"if_match={self.if_match!r}")
            parts.append(f"if_none_match={self.if_none_match!r}")
            parts.append(f"grant_full_control={self.grant_full_control!r}")
            parts.append(f"grant_read={self.grant_read!r}")
            parts.append(f"grant_read_acp={self.grant_read_acp!r}")
            parts.append(f"grant_write_acp={self.grant_write_acp!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"write_offset_bytes={self.write_offset_bytes!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"storage_class={self.storage_class!r}")
            parts.append(f"website_redirect_location={self.website_redirect_location!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"sse_kms_encryption_context={self.sse_kms_encryption_context!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"tagging={self.tagging!r}")
            parts.append(f"object_lock_mode={self.object_lock_mode!r}")
            parts.append(f"object_lock_retain_until_date={self.object_lock_retain_until_date!r}")
            parts.append(f"object_lock_legal_hold_status={self.object_lock_legal_hold_status!r}")
            parts.append(f"object_lock_event_hold={self.object_lock_event_hold!r}")
            parts.append(f"object_lock_event_hold_duration_days={self.object_lock_event_hold_duration_days!r}")
            parts.append(f"object_lock_event_hold_duration_years={self.object_lock_event_hold_duration_years!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d7980ccc967cc6aa3b0dac11b6f68deda60cbdb7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('is_restore_in_progress', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('restore_expiry_date', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,"
            "), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'RestoreStatus'),
    ),
)
def _process_dataclass__d7980ccc967cc6aa3b0dac11b6f68deda60cbdb7():
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
                is_restore_in_progress=self.is_restore_in_progress,
                restore_expiry_date=self.restore_expiry_date,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.is_restore_in_progress == other.is_restore_in_progress and
                self.restore_expiry_date == other.restore_expiry_date
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'is_restore_in_progress',
            'restore_expiry_date',
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
                self.is_restore_in_progress,
                self.restore_expiry_date,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            is_restore_in_progress: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            restore_expiry_date: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'is_restore_in_progress', is_restore_in_progress)
            __dataclass__object_setattr(self, 'restore_expiry_date', restore_expiry_date)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"is_restore_in_progress={self.is_restore_in_progress!r}")
            parts.append(f"restore_expiry_date={self.restore_expiry_date!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7028cae771a7289e3734bbb7aac4e12aeba9a4cf',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('server_side_encryption', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('etag', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('checksum_crc32', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha512', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_md5"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksu"
            "m_xxhash64', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), "
            "(('checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('sse_customer_key_md5', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('sse_kms_key_id', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('bucket_key_enabled', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('request_charged', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (Fals"
            "e,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'UploadPartOutput'),
    ),
)
def _process_dataclass__7028cae771a7289e3734bbb7aac4e12aeba9a4cf():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
                server_side_encryption=self.server_side_encryption,
                etag=self.etag,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key_md5=self.sse_customer_key_md5,
                sse_kms_key_id=self.sse_kms_key_id,
                bucket_key_enabled=self.bucket_key_enabled,
                request_charged=self.request_charged,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.server_side_encryption == other.server_side_encryption and
                self.etag == other.etag and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.sse_kms_key_id == other.sse_kms_key_id and
                self.bucket_key_enabled == other.bucket_key_enabled and
                self.request_charged == other.request_charged
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'server_side_encryption',
            'etag',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'sse_customer_algorithm',
            'sse_customer_key_md5',
            'sse_kms_key_id',
            'bucket_key_enabled',
            'request_charged',
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
                self.server_side_encryption,
                self.etag,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.sse_customer_algorithm,
                self.sse_customer_key_md5,
                self.sse_kms_key_id,
                self.bucket_key_enabled,
                self.request_charged,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            server_side_encryption: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            etag: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            checksum_crc32: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            checksum_crc32c: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_crc64nvme: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_sha1: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_sha256: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_sha512: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_md5: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_xxhash64: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_xxhash3: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_xxhash128: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            sse_customer_algorithm: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            sse_customer_key_md5: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            sse_kms_key_id: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            bucket_key_enabled: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            request_charged: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'server_side_encryption', server_side_encryption)
            __dataclass__object_setattr(self, 'etag', etag)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'sse_kms_key_id', sse_kms_key_id)
            __dataclass__object_setattr(self, 'bucket_key_enabled', bucket_key_enabled)
            __dataclass__object_setattr(self, 'request_charged', request_charged)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"server_side_encryption={self.server_side_encryption!r}")
            parts.append(f"etag={self.etag!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"sse_kms_key_id={self.sse_kms_key_id!r}")
            parts.append(f"bucket_key_enabled={self.bucket_key_enabled!r}")
            parts.append(f"request_charged={self.request_charged!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f37c8e29ece5155b8039181753c674b59dcb058c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('body', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('bucket', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('content_length', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('content_md5', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('checksum_algorithm', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('checksum_crc32', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('checksum_crc32c', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('checksum_crc64nvme', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha1', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha256', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('checksum_sha"
            "512', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('chec"
            "ksum_md5', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'checksum_xxhash64', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('checksum_xxhash3', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False), (('checksum_xxhash128', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('part_number', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('upload_id', True, True, None, True, True, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('sse_customer_algorithm', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('sse_customer_key', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('sse_customer_key_md5', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('request_payer', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('expected_bucket_owner', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()"
            "), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.s3', 'UploadPartRequest'),
    ),
)
def _process_dataclass__f37c8e29ece5155b8039181753c674b59dcb058c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
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
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
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
                bucket=self.bucket,
                content_length=self.content_length,
                content_md5=self.content_md5,
                checksum_algorithm=self.checksum_algorithm,
                checksum_crc32=self.checksum_crc32,
                checksum_crc32c=self.checksum_crc32c,
                checksum_crc64nvme=self.checksum_crc64nvme,
                checksum_sha1=self.checksum_sha1,
                checksum_sha256=self.checksum_sha256,
                checksum_sha512=self.checksum_sha512,
                checksum_md5=self.checksum_md5,
                checksum_xxhash64=self.checksum_xxhash64,
                checksum_xxhash3=self.checksum_xxhash3,
                checksum_xxhash128=self.checksum_xxhash128,
                key=self.key,
                part_number=self.part_number,
                upload_id=self.upload_id,
                sse_customer_algorithm=self.sse_customer_algorithm,
                sse_customer_key=self.sse_customer_key,
                sse_customer_key_md5=self.sse_customer_key_md5,
                request_payer=self.request_payer,
                expected_bucket_owner=self.expected_bucket_owner,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.bucket == other.bucket and
                self.content_length == other.content_length and
                self.content_md5 == other.content_md5 and
                self.checksum_algorithm == other.checksum_algorithm and
                self.checksum_crc32 == other.checksum_crc32 and
                self.checksum_crc32c == other.checksum_crc32c and
                self.checksum_crc64nvme == other.checksum_crc64nvme and
                self.checksum_sha1 == other.checksum_sha1 and
                self.checksum_sha256 == other.checksum_sha256 and
                self.checksum_sha512 == other.checksum_sha512 and
                self.checksum_md5 == other.checksum_md5 and
                self.checksum_xxhash64 == other.checksum_xxhash64 and
                self.checksum_xxhash3 == other.checksum_xxhash3 and
                self.checksum_xxhash128 == other.checksum_xxhash128 and
                self.key == other.key and
                self.part_number == other.part_number and
                self.upload_id == other.upload_id and
                self.sse_customer_algorithm == other.sse_customer_algorithm and
                self.sse_customer_key == other.sse_customer_key and
                self.sse_customer_key_md5 == other.sse_customer_key_md5 and
                self.request_payer == other.request_payer and
                self.expected_bucket_owner == other.expected_bucket_owner
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'body',
            'bucket',
            'content_length',
            'content_md5',
            'checksum_algorithm',
            'checksum_crc32',
            'checksum_crc32c',
            'checksum_crc64nvme',
            'checksum_sha1',
            'checksum_sha256',
            'checksum_sha512',
            'checksum_md5',
            'checksum_xxhash64',
            'checksum_xxhash3',
            'checksum_xxhash128',
            'key',
            'part_number',
            'upload_id',
            'sse_customer_algorithm',
            'sse_customer_key',
            'sse_customer_key_md5',
            'request_payer',
            'expected_bucket_owner',
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
                self.bucket,
                self.content_length,
                self.content_md5,
                self.checksum_algorithm,
                self.checksum_crc32,
                self.checksum_crc32c,
                self.checksum_crc64nvme,
                self.checksum_sha1,
                self.checksum_sha256,
                self.checksum_sha512,
                self.checksum_md5,
                self.checksum_xxhash64,
                self.checksum_xxhash3,
                self.checksum_xxhash128,
                self.key,
                self.part_number,
                self.upload_id,
                self.sse_customer_algorithm,
                self.sse_customer_key,
                self.sse_customer_key_md5,
                self.request_payer,
                self.expected_bucket_owner,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            body: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            bucket: __dataclass__init__fields__02__annotation,
            content_length: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            content_md5: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            checksum_algorithm: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            checksum_crc32: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            checksum_crc32c: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checksum_crc64nvme: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            checksum_sha1: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            checksum_sha256: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            checksum_sha512: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            checksum_md5: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            checksum_xxhash64: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            checksum_xxhash3: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            checksum_xxhash128: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            key: __dataclass__init__fields__16__annotation,
            part_number: __dataclass__init__fields__17__annotation,
            upload_id: __dataclass__init__fields__18__annotation,
            sse_customer_algorithm: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            sse_customer_key: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            sse_customer_key_md5: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            request_payer: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            expected_bucket_owner: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'bucket', bucket)
            __dataclass__object_setattr(self, 'content_length', content_length)
            __dataclass__object_setattr(self, 'content_md5', content_md5)
            __dataclass__object_setattr(self, 'checksum_algorithm', checksum_algorithm)
            __dataclass__object_setattr(self, 'checksum_crc32', checksum_crc32)
            __dataclass__object_setattr(self, 'checksum_crc32c', checksum_crc32c)
            __dataclass__object_setattr(self, 'checksum_crc64nvme', checksum_crc64nvme)
            __dataclass__object_setattr(self, 'checksum_sha1', checksum_sha1)
            __dataclass__object_setattr(self, 'checksum_sha256', checksum_sha256)
            __dataclass__object_setattr(self, 'checksum_sha512', checksum_sha512)
            __dataclass__object_setattr(self, 'checksum_md5', checksum_md5)
            __dataclass__object_setattr(self, 'checksum_xxhash64', checksum_xxhash64)
            __dataclass__object_setattr(self, 'checksum_xxhash3', checksum_xxhash3)
            __dataclass__object_setattr(self, 'checksum_xxhash128', checksum_xxhash128)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'part_number', part_number)
            __dataclass__object_setattr(self, 'upload_id', upload_id)
            __dataclass__object_setattr(self, 'sse_customer_algorithm', sse_customer_algorithm)
            __dataclass__object_setattr(self, 'sse_customer_key', sse_customer_key)
            __dataclass__object_setattr(self, 'sse_customer_key_md5', sse_customer_key_md5)
            __dataclass__object_setattr(self, 'request_payer', request_payer)
            __dataclass__object_setattr(self, 'expected_bucket_owner', expected_bucket_owner)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"bucket={self.bucket!r}")
            parts.append(f"content_length={self.content_length!r}")
            parts.append(f"content_md5={self.content_md5!r}")
            parts.append(f"checksum_algorithm={self.checksum_algorithm!r}")
            parts.append(f"checksum_crc32={self.checksum_crc32!r}")
            parts.append(f"checksum_crc32c={self.checksum_crc32c!r}")
            parts.append(f"checksum_crc64nvme={self.checksum_crc64nvme!r}")
            parts.append(f"checksum_sha1={self.checksum_sha1!r}")
            parts.append(f"checksum_sha256={self.checksum_sha256!r}")
            parts.append(f"checksum_sha512={self.checksum_sha512!r}")
            parts.append(f"checksum_md5={self.checksum_md5!r}")
            parts.append(f"checksum_xxhash64={self.checksum_xxhash64!r}")
            parts.append(f"checksum_xxhash3={self.checksum_xxhash3!r}")
            parts.append(f"checksum_xxhash128={self.checksum_xxhash128!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"part_number={self.part_number!r}")
            parts.append(f"upload_id={self.upload_id!r}")
            parts.append(f"sse_customer_algorithm={self.sse_customer_algorithm!r}")
            parts.append(f"sse_customer_key={self.sse_customer_key!r}")
            parts.append(f"sse_customer_key_md5={self.sse_customer_key_md5!r}")
            parts.append(f"request_payer={self.request_payer!r}")
            parts.append(f"expected_bucket_owner={self.expected_bucket_owner!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
