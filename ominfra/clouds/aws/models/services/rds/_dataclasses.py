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


IMPLEMENTATION_KEY = '0b058e19e67cdb26e91b1c38203523e9cefe1242a3d73dbb76cc5c75c41df941'


@_register(
    installer_sha1='d483803c8b8f15916684dabc6604eda7c61d87d9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('volume_name', True, True, None, True, True, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('allocated_storage', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('iops', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('max_allocated_storage', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('storage_throughput', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('storage_type', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, ("
            "), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'AdditionalStorageVolume'),
    ),
)
def _process_dataclass__d483803c8b8f15916684dabc6604eda7c61d87d9():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                volume_name=self.volume_name,
                allocated_storage=self.allocated_storage,
                iops=self.iops,
                max_allocated_storage=self.max_allocated_storage,
                storage_throughput=self.storage_throughput,
                storage_type=self.storage_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.volume_name == other.volume_name and
                self.allocated_storage == other.allocated_storage and
                self.iops == other.iops and
                self.max_allocated_storage == other.max_allocated_storage and
                self.storage_throughput == other.storage_throughput and
                self.storage_type == other.storage_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'volume_name',
            'allocated_storage',
            'iops',
            'max_allocated_storage',
            'storage_throughput',
            'storage_type',
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
                self.volume_name,
                self.allocated_storage,
                self.iops,
                self.max_allocated_storage,
                self.storage_throughput,
                self.storage_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            volume_name: __dataclass__init__fields__1__annotation,
            allocated_storage: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            iops: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            max_allocated_storage: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            storage_throughput: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            storage_type: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'volume_name', volume_name)
            __dataclass__object_setattr(self, 'allocated_storage', allocated_storage)
            __dataclass__object_setattr(self, 'iops', iops)
            __dataclass__object_setattr(self, 'max_allocated_storage', max_allocated_storage)
            __dataclass__object_setattr(self, 'storage_throughput', storage_throughput)
            __dataclass__object_setattr(self, 'storage_type', storage_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"volume_name={self.volume_name!r}")
            parts.append(f"allocated_storage={self.allocated_storage!r}")
            parts.append(f"iops={self.iops!r}")
            parts.append(f"max_allocated_storage={self.max_allocated_storage!r}")
            parts.append(f"storage_throughput={self.storage_throughput!r}")
            parts.append(f"storage_type={self.storage_type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2effd8a3025d3310831df773f6a359de01595aeb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('volume_name', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('storage_volume_status', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('storage_operation_status', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('storage_operation_percent_progress', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('allocated_"
            "storage', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "iops', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('max"
            "_allocated_storage', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('storage_throughput', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('storage_type', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'AdditionalStorageVolumeOutput'),
    ),
)
def _process_dataclass__2effd8a3025d3310831df773f6a359de01595aeb():
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
                volume_name=self.volume_name,
                storage_volume_status=self.storage_volume_status,
                storage_operation_status=self.storage_operation_status,
                storage_operation_percent_progress=self.storage_operation_percent_progress,
                allocated_storage=self.allocated_storage,
                iops=self.iops,
                max_allocated_storage=self.max_allocated_storage,
                storage_throughput=self.storage_throughput,
                storage_type=self.storage_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.volume_name == other.volume_name and
                self.storage_volume_status == other.storage_volume_status and
                self.storage_operation_status == other.storage_operation_status and
                self.storage_operation_percent_progress == other.storage_operation_percent_progress and
                self.allocated_storage == other.allocated_storage and
                self.iops == other.iops and
                self.max_allocated_storage == other.max_allocated_storage and
                self.storage_throughput == other.storage_throughput and
                self.storage_type == other.storage_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'volume_name',
            'storage_volume_status',
            'storage_operation_status',
            'storage_operation_percent_progress',
            'allocated_storage',
            'iops',
            'max_allocated_storage',
            'storage_throughput',
            'storage_type',
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
                self.volume_name,
                self.storage_volume_status,
                self.storage_operation_status,
                self.storage_operation_percent_progress,
                self.allocated_storage,
                self.iops,
                self.max_allocated_storage,
                self.storage_throughput,
                self.storage_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            volume_name: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            storage_volume_status: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            storage_operation_status: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            storage_operation_percent_progress: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            allocated_storage: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            iops: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            max_allocated_storage: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            storage_throughput: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            storage_type: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'volume_name', volume_name)
            __dataclass__object_setattr(self, 'storage_volume_status', storage_volume_status)
            __dataclass__object_setattr(self, 'storage_operation_status', storage_operation_status)
            __dataclass__object_setattr(self, 'storage_operation_percent_progress', storage_operation_percent_progress)
            __dataclass__object_setattr(self, 'allocated_storage', allocated_storage)
            __dataclass__object_setattr(self, 'iops', iops)
            __dataclass__object_setattr(self, 'max_allocated_storage', max_allocated_storage)
            __dataclass__object_setattr(self, 'storage_throughput', storage_throughput)
            __dataclass__object_setattr(self, 'storage_type', storage_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"volume_name={self.volume_name!r}")
            parts.append(f"storage_volume_status={self.storage_volume_status!r}")
            parts.append(f"storage_operation_status={self.storage_operation_status!r}")
            parts.append(f"storage_operation_percent_progress={self.storage_operation_percent_progress!r}")
            parts.append(f"allocated_storage={self.allocated_storage!r}")
            parts.append(f"iops={self.iops!r}")
            parts.append(f"max_allocated_storage={self.max_allocated_storage!r}")
            parts.append(f"storage_throughput={self.storage_throughput!r}")
            parts.append(f"storage_type={self.storage_type!r}")
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
            "', None, False, False, False),), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fals"
            "e))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'AuthorizationNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'BackupPolicyNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'CertificateNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBClusterNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceAlreadyExistsFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceAutomatedBackupQuotaExceededFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBParameterGroupNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBSecurityGroupNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBSnapshotAlreadyExistsFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DBSubnetGroupDoesNotCoverEnoughAZs'),
        ('ominfra.clouds.aws.models.services.rds', 'DBSubnetGroupNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'DomainNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'InstanceQuotaExceededFault'),
        ('ominfra.clouds.aws.models.services.rds', 'InsufficientDBInstanceCapacityFault'),
        ('ominfra.clouds.aws.models.services.rds', 'InvalidDBClusterStateFault'),
        ('ominfra.clouds.aws.models.services.rds', 'InvalidDBInstanceStateFault'),
        ('ominfra.clouds.aws.models.services.rds', 'InvalidSubnet'),
        ('ominfra.clouds.aws.models.services.rds', 'InvalidVPCNetworkStateFault'),
        ('ominfra.clouds.aws.models.services.rds', 'KMSKeyNotAccessibleFault'),
        ('ominfra.clouds.aws.models.services.rds', 'NetworkTypeNotSupported'),
        ('ominfra.clouds.aws.models.services.rds', 'OptionGroupNotFoundFault'),
        ('ominfra.clouds.aws.models.services.rds', 'ProvisionedIopsNotAvailableInAZFault'),
        ('ominfra.clouds.aws.models.services.rds', 'SnapshotQuotaExceededFault'),
        ('ominfra.clouds.aws.models.services.rds', 'StorageQuotaExceededFault'),
        ('ominfra.clouds.aws.models.services.rds', 'StorageTypeNotSupportedFault'),
        ('ominfra.clouds.aws.models.services.rds', 'TenantDatabaseQuotaExceededFault'),
        ('ominfra.clouds.aws.models.services.rds', 'VpcEncryptionControlViolationException'),
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
    installer_sha1='1d54f0e79f9555ab3393b80415a6078f900b8d21',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'AvailabilityZone'),
    ),
)
def _process_dataclass__1d54f0e79f9555ab3393b80415a6078f900b8d21():
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
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
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
                self.name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='bbb1d032a77cb075cd9760117b990a4e2e4a3249',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('ca_identifier', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('valid_till', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), "
            "(), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'CertificateDetails'),
    ),
)
def _process_dataclass__bbb1d032a77cb075cd9760117b990a4e2e4a3249():
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
                ca_identifier=self.ca_identifier,
                valid_till=self.valid_till,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ca_identifier == other.ca_identifier and
                self.valid_till == other.valid_till
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'ca_identifier',
            'valid_till',
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
                self.ca_identifier,
                self.valid_till,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            ca_identifier: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            valid_till: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ca_identifier', ca_identifier)
            __dataclass__object_setattr(self, 'valid_till', valid_till)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ca_identifier={self.ca_identifier!r}")
            parts.append(f"valid_till={self.valid_till!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='656a146807f1abd624694d4f11b5988c9b486ea8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_name', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('allocated_storage', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('db_instance_class', True, True, None, True, T"
            "rue, False, None), 'instance', 'missing', None, False, False, False), (('engine', True, True, None, True, "
            "True, False, None), 'instance', 'missing', None, False, False, False), (('master_username', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('master_user_password', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_security"
            "_groups', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "vpc_security_group_ids', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('availability_zone', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('db_subnet_group_name', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('preferred_maintenance_window', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False), (('db_parameter_group_name', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('backup_retention_period', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('preferred_backu"
            "p_window', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'port', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('mu"
            "lti_az', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('e"
            "ngine_version', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False"
            "), (('auto_minor_version_upgrade', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('license_model', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('iops', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('storage_throughput', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('option_group_name', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('character_set_name', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('nchar_character_set_name', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('publicly_accessible', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('tags', True, True"
            ", None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_cluster_identifie"
            "r', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('storag"
            "e_type', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('t"
            "de_credential_arn', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse), (('tde_credential_password', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('storage_encrypted', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('kms_key_id', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('domain', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('domain_fqdn', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('domain_ou', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('domain_auth_secret_arn', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False), (('domain_dns_ips', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('copy_tags_to_snapshot', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('monitoring_interval', True"
            ", True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('monitoring_rol"
            "e_arn', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('do"
            "main_iam_role_name', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('promotion_tier', True, True, None, True, True, False, None), 'instance', 'value', None, False, "
            "False, False), (('timezone', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('enable_iam_database_authentication', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('database_insights_mode', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('enable_performance_insights', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('performance_insights_kms_"
            "key_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('p"
            "erformance_insights_retention_period', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('enable_cloudwatch_logs_exports', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('processor_features', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('deletion_protection', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('max_allocated_storage', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('enable_customer_o"
            "wned_ip', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "network_type', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)"
            ", (('backup_target', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('custom_iam_instance_profile', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('db_system_id', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('ca_certificate_identifier', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('manage_master_user_password', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('master_user_secret_kms_key_id', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('multi_tena"
            "nt', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('dedic"
            "ated_log_volume', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('engine_lifecycle_support', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('additional_storage_volumes', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('tag_specifications', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('master_user_authentication_type', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False,"
            " (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'CreateDBInstanceMessage'),
    ),
)
def _process_dataclass__656a146807f1abd624694d4f11b5988c9b486ea8():
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
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
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
        __dataclass__init__fields__47__annotation = __dataclass__spec.fields[47].annotation
        __dataclass__init__fields__47__default = __dataclass__spec.fields[47].default.must()
        __dataclass__init__fields__48__annotation = __dataclass__spec.fields[48].annotation
        __dataclass__init__fields__48__default = __dataclass__spec.fields[48].default.must()
        __dataclass__init__fields__49__annotation = __dataclass__spec.fields[49].annotation
        __dataclass__init__fields__49__default = __dataclass__spec.fields[49].default.must()
        __dataclass__init__fields__50__annotation = __dataclass__spec.fields[50].annotation
        __dataclass__init__fields__50__default = __dataclass__spec.fields[50].default.must()
        __dataclass__init__fields__51__annotation = __dataclass__spec.fields[51].annotation
        __dataclass__init__fields__51__default = __dataclass__spec.fields[51].default.must()
        __dataclass__init__fields__52__annotation = __dataclass__spec.fields[52].annotation
        __dataclass__init__fields__52__default = __dataclass__spec.fields[52].default.must()
        __dataclass__init__fields__53__annotation = __dataclass__spec.fields[53].annotation
        __dataclass__init__fields__53__default = __dataclass__spec.fields[53].default.must()
        __dataclass__init__fields__54__annotation = __dataclass__spec.fields[54].annotation
        __dataclass__init__fields__54__default = __dataclass__spec.fields[54].default.must()
        __dataclass__init__fields__55__annotation = __dataclass__spec.fields[55].annotation
        __dataclass__init__fields__55__default = __dataclass__spec.fields[55].default.must()
        __dataclass__init__fields__56__annotation = __dataclass__spec.fields[56].annotation
        __dataclass__init__fields__56__default = __dataclass__spec.fields[56].default.must()
        __dataclass__init__fields__57__annotation = __dataclass__spec.fields[57].annotation
        __dataclass__init__fields__57__default = __dataclass__spec.fields[57].default.must()
        __dataclass__init__fields__58__annotation = __dataclass__spec.fields[58].annotation
        __dataclass__init__fields__58__default = __dataclass__spec.fields[58].default.must()
        __dataclass__init__fields__59__annotation = __dataclass__spec.fields[59].annotation
        __dataclass__init__fields__59__default = __dataclass__spec.fields[59].default.must()
        __dataclass__init__fields__60__annotation = __dataclass__spec.fields[60].annotation
        __dataclass__init__fields__60__default = __dataclass__spec.fields[60].default.must()
        __dataclass__init__fields__61__annotation = __dataclass__spec.fields[61].annotation
        __dataclass__init__fields__61__default = __dataclass__spec.fields[61].default.must()
        __dataclass__init__fields__62__annotation = __dataclass__spec.fields[62].annotation
        __dataclass__init__fields__62__default = __dataclass__spec.fields[62].default.must()
        __dataclass__init__fields__63__annotation = __dataclass__spec.fields[63].annotation
        __dataclass__init__fields__63__default = __dataclass__spec.fields[63].default.must()
        __dataclass__init__fields__64__annotation = __dataclass__spec.fields[64].annotation
        __dataclass__init__fields__64__default = __dataclass__spec.fields[64].default.must()
        __dataclass__init__fields__65__annotation = __dataclass__spec.fields[65].annotation
        __dataclass__init__fields__65__default = __dataclass__spec.fields[65].default.must()
        __dataclass__init__fields__66__annotation = __dataclass__spec.fields[66].annotation
        __dataclass__init__fields__66__default = __dataclass__spec.fields[66].default.must()
        __dataclass__init__fields__67__annotation = __dataclass__spec.fields[67].annotation
        __dataclass__init__fields__67__default = __dataclass__spec.fields[67].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                db_name=self.db_name,
                db_instance_identifier=self.db_instance_identifier,
                allocated_storage=self.allocated_storage,
                db_instance_class=self.db_instance_class,
                engine=self.engine,
                master_username=self.master_username,
                master_user_password=self.master_user_password,
                db_security_groups=self.db_security_groups,
                vpc_security_group_ids=self.vpc_security_group_ids,
                availability_zone=self.availability_zone,
                db_subnet_group_name=self.db_subnet_group_name,
                preferred_maintenance_window=self.preferred_maintenance_window,
                db_parameter_group_name=self.db_parameter_group_name,
                backup_retention_period=self.backup_retention_period,
                preferred_backup_window=self.preferred_backup_window,
                port=self.port,
                multi_az=self.multi_az,
                engine_version=self.engine_version,
                auto_minor_version_upgrade=self.auto_minor_version_upgrade,
                license_model=self.license_model,
                iops=self.iops,
                storage_throughput=self.storage_throughput,
                option_group_name=self.option_group_name,
                character_set_name=self.character_set_name,
                nchar_character_set_name=self.nchar_character_set_name,
                publicly_accessible=self.publicly_accessible,
                tags=self.tags,
                db_cluster_identifier=self.db_cluster_identifier,
                storage_type=self.storage_type,
                tde_credential_arn=self.tde_credential_arn,
                tde_credential_password=self.tde_credential_password,
                storage_encrypted=self.storage_encrypted,
                kms_key_id=self.kms_key_id,
                domain=self.domain,
                domain_fqdn=self.domain_fqdn,
                domain_ou=self.domain_ou,
                domain_auth_secret_arn=self.domain_auth_secret_arn,
                domain_dns_ips=self.domain_dns_ips,
                copy_tags_to_snapshot=self.copy_tags_to_snapshot,
                monitoring_interval=self.monitoring_interval,
                monitoring_role_arn=self.monitoring_role_arn,
                domain_iam_role_name=self.domain_iam_role_name,
                promotion_tier=self.promotion_tier,
                timezone=self.timezone,
                enable_iam_database_authentication=self.enable_iam_database_authentication,
                database_insights_mode=self.database_insights_mode,
                enable_performance_insights=self.enable_performance_insights,
                performance_insights_kms_key_id=self.performance_insights_kms_key_id,
                performance_insights_retention_period=self.performance_insights_retention_period,
                enable_cloudwatch_logs_exports=self.enable_cloudwatch_logs_exports,
                processor_features=self.processor_features,
                deletion_protection=self.deletion_protection,
                max_allocated_storage=self.max_allocated_storage,
                enable_customer_owned_ip=self.enable_customer_owned_ip,
                network_type=self.network_type,
                backup_target=self.backup_target,
                custom_iam_instance_profile=self.custom_iam_instance_profile,
                db_system_id=self.db_system_id,
                ca_certificate_identifier=self.ca_certificate_identifier,
                manage_master_user_password=self.manage_master_user_password,
                master_user_secret_kms_key_id=self.master_user_secret_kms_key_id,
                multi_tenant=self.multi_tenant,
                dedicated_log_volume=self.dedicated_log_volume,
                engine_lifecycle_support=self.engine_lifecycle_support,
                additional_storage_volumes=self.additional_storage_volumes,
                tag_specifications=self.tag_specifications,
                master_user_authentication_type=self.master_user_authentication_type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_name == other.db_name and
                self.db_instance_identifier == other.db_instance_identifier and
                self.allocated_storage == other.allocated_storage and
                self.db_instance_class == other.db_instance_class and
                self.engine == other.engine and
                self.master_username == other.master_username and
                self.master_user_password == other.master_user_password and
                self.db_security_groups == other.db_security_groups and
                self.vpc_security_group_ids == other.vpc_security_group_ids and
                self.availability_zone == other.availability_zone and
                self.db_subnet_group_name == other.db_subnet_group_name and
                self.preferred_maintenance_window == other.preferred_maintenance_window and
                self.db_parameter_group_name == other.db_parameter_group_name and
                self.backup_retention_period == other.backup_retention_period and
                self.preferred_backup_window == other.preferred_backup_window and
                self.port == other.port and
                self.multi_az == other.multi_az and
                self.engine_version == other.engine_version and
                self.auto_minor_version_upgrade == other.auto_minor_version_upgrade and
                self.license_model == other.license_model and
                self.iops == other.iops and
                self.storage_throughput == other.storage_throughput and
                self.option_group_name == other.option_group_name and
                self.character_set_name == other.character_set_name and
                self.nchar_character_set_name == other.nchar_character_set_name and
                self.publicly_accessible == other.publicly_accessible and
                self.tags == other.tags and
                self.db_cluster_identifier == other.db_cluster_identifier and
                self.storage_type == other.storage_type and
                self.tde_credential_arn == other.tde_credential_arn and
                self.tde_credential_password == other.tde_credential_password and
                self.storage_encrypted == other.storage_encrypted and
                self.kms_key_id == other.kms_key_id and
                self.domain == other.domain and
                self.domain_fqdn == other.domain_fqdn and
                self.domain_ou == other.domain_ou and
                self.domain_auth_secret_arn == other.domain_auth_secret_arn and
                self.domain_dns_ips == other.domain_dns_ips and
                self.copy_tags_to_snapshot == other.copy_tags_to_snapshot and
                self.monitoring_interval == other.monitoring_interval and
                self.monitoring_role_arn == other.monitoring_role_arn and
                self.domain_iam_role_name == other.domain_iam_role_name and
                self.promotion_tier == other.promotion_tier and
                self.timezone == other.timezone and
                self.enable_iam_database_authentication == other.enable_iam_database_authentication and
                self.database_insights_mode == other.database_insights_mode and
                self.enable_performance_insights == other.enable_performance_insights and
                self.performance_insights_kms_key_id == other.performance_insights_kms_key_id and
                self.performance_insights_retention_period == other.performance_insights_retention_period and
                self.enable_cloudwatch_logs_exports == other.enable_cloudwatch_logs_exports and
                self.processor_features == other.processor_features and
                self.deletion_protection == other.deletion_protection and
                self.max_allocated_storage == other.max_allocated_storage and
                self.enable_customer_owned_ip == other.enable_customer_owned_ip and
                self.network_type == other.network_type and
                self.backup_target == other.backup_target and
                self.custom_iam_instance_profile == other.custom_iam_instance_profile and
                self.db_system_id == other.db_system_id and
                self.ca_certificate_identifier == other.ca_certificate_identifier and
                self.manage_master_user_password == other.manage_master_user_password and
                self.master_user_secret_kms_key_id == other.master_user_secret_kms_key_id and
                self.multi_tenant == other.multi_tenant and
                self.dedicated_log_volume == other.dedicated_log_volume and
                self.engine_lifecycle_support == other.engine_lifecycle_support and
                self.additional_storage_volumes == other.additional_storage_volumes and
                self.tag_specifications == other.tag_specifications and
                self.master_user_authentication_type == other.master_user_authentication_type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_name',
            'db_instance_identifier',
            'allocated_storage',
            'db_instance_class',
            'engine',
            'master_username',
            'master_user_password',
            'db_security_groups',
            'vpc_security_group_ids',
            'availability_zone',
            'db_subnet_group_name',
            'preferred_maintenance_window',
            'db_parameter_group_name',
            'backup_retention_period',
            'preferred_backup_window',
            'port',
            'multi_az',
            'engine_version',
            'auto_minor_version_upgrade',
            'license_model',
            'iops',
            'storage_throughput',
            'option_group_name',
            'character_set_name',
            'nchar_character_set_name',
            'publicly_accessible',
            'tags',
            'db_cluster_identifier',
            'storage_type',
            'tde_credential_arn',
            'tde_credential_password',
            'storage_encrypted',
            'kms_key_id',
            'domain',
            'domain_fqdn',
            'domain_ou',
            'domain_auth_secret_arn',
            'domain_dns_ips',
            'copy_tags_to_snapshot',
            'monitoring_interval',
            'monitoring_role_arn',
            'domain_iam_role_name',
            'promotion_tier',
            'timezone',
            'enable_iam_database_authentication',
            'database_insights_mode',
            'enable_performance_insights',
            'performance_insights_kms_key_id',
            'performance_insights_retention_period',
            'enable_cloudwatch_logs_exports',
            'processor_features',
            'deletion_protection',
            'max_allocated_storage',
            'enable_customer_owned_ip',
            'network_type',
            'backup_target',
            'custom_iam_instance_profile',
            'db_system_id',
            'ca_certificate_identifier',
            'manage_master_user_password',
            'master_user_secret_kms_key_id',
            'multi_tenant',
            'dedicated_log_volume',
            'engine_lifecycle_support',
            'additional_storage_volumes',
            'tag_specifications',
            'master_user_authentication_type',
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
                self.db_name,
                self.db_instance_identifier,
                self.allocated_storage,
                self.db_instance_class,
                self.engine,
                self.master_username,
                self.master_user_password,
                self.db_security_groups,
                self.vpc_security_group_ids,
                self.availability_zone,
                self.db_subnet_group_name,
                self.preferred_maintenance_window,
                self.db_parameter_group_name,
                self.backup_retention_period,
                self.preferred_backup_window,
                self.port,
                self.multi_az,
                self.engine_version,
                self.auto_minor_version_upgrade,
                self.license_model,
                self.iops,
                self.storage_throughput,
                self.option_group_name,
                self.character_set_name,
                self.nchar_character_set_name,
                self.publicly_accessible,
                self.tags,
                self.db_cluster_identifier,
                self.storage_type,
                self.tde_credential_arn,
                self.tde_credential_password,
                self.storage_encrypted,
                self.kms_key_id,
                self.domain,
                self.domain_fqdn,
                self.domain_ou,
                self.domain_auth_secret_arn,
                self.domain_dns_ips,
                self.copy_tags_to_snapshot,
                self.monitoring_interval,
                self.monitoring_role_arn,
                self.domain_iam_role_name,
                self.promotion_tier,
                self.timezone,
                self.enable_iam_database_authentication,
                self.database_insights_mode,
                self.enable_performance_insights,
                self.performance_insights_kms_key_id,
                self.performance_insights_retention_period,
                self.enable_cloudwatch_logs_exports,
                self.processor_features,
                self.deletion_protection,
                self.max_allocated_storage,
                self.enable_customer_owned_ip,
                self.network_type,
                self.backup_target,
                self.custom_iam_instance_profile,
                self.db_system_id,
                self.ca_certificate_identifier,
                self.manage_master_user_password,
                self.master_user_secret_kms_key_id,
                self.multi_tenant,
                self.dedicated_log_volume,
                self.engine_lifecycle_support,
                self.additional_storage_volumes,
                self.tag_specifications,
                self.master_user_authentication_type,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_name: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            db_instance_identifier: __dataclass__init__fields__02__annotation,
            allocated_storage: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            db_instance_class: __dataclass__init__fields__04__annotation,
            engine: __dataclass__init__fields__05__annotation,
            master_username: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            master_user_password: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            db_security_groups: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            vpc_security_group_ids: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            availability_zone: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            db_subnet_group_name: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            preferred_maintenance_window: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            db_parameter_group_name: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            backup_retention_period: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            preferred_backup_window: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            port: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            multi_az: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            engine_version: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            auto_minor_version_upgrade: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            license_model: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            iops: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            storage_throughput: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            option_group_name: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            character_set_name: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            nchar_character_set_name: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            publicly_accessible: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            tags: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            db_cluster_identifier: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            storage_type: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            tde_credential_arn: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            tde_credential_password: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            storage_encrypted: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            kms_key_id: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            domain: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            domain_fqdn: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            domain_ou: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            domain_auth_secret_arn: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            domain_dns_ips: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            copy_tags_to_snapshot: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            monitoring_interval: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            monitoring_role_arn: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            domain_iam_role_name: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            promotion_tier: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            timezone: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            enable_iam_database_authentication: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            database_insights_mode: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
            enable_performance_insights: __dataclass__init__fields__47__annotation = __dataclass__init__fields__47__default,
            performance_insights_kms_key_id: __dataclass__init__fields__48__annotation = __dataclass__init__fields__48__default,
            performance_insights_retention_period: __dataclass__init__fields__49__annotation = __dataclass__init__fields__49__default,
            enable_cloudwatch_logs_exports: __dataclass__init__fields__50__annotation = __dataclass__init__fields__50__default,
            processor_features: __dataclass__init__fields__51__annotation = __dataclass__init__fields__51__default,
            deletion_protection: __dataclass__init__fields__52__annotation = __dataclass__init__fields__52__default,
            max_allocated_storage: __dataclass__init__fields__53__annotation = __dataclass__init__fields__53__default,
            enable_customer_owned_ip: __dataclass__init__fields__54__annotation = __dataclass__init__fields__54__default,
            network_type: __dataclass__init__fields__55__annotation = __dataclass__init__fields__55__default,
            backup_target: __dataclass__init__fields__56__annotation = __dataclass__init__fields__56__default,
            custom_iam_instance_profile: __dataclass__init__fields__57__annotation = __dataclass__init__fields__57__default,
            db_system_id: __dataclass__init__fields__58__annotation = __dataclass__init__fields__58__default,
            ca_certificate_identifier: __dataclass__init__fields__59__annotation = __dataclass__init__fields__59__default,
            manage_master_user_password: __dataclass__init__fields__60__annotation = __dataclass__init__fields__60__default,
            master_user_secret_kms_key_id: __dataclass__init__fields__61__annotation = __dataclass__init__fields__61__default,
            multi_tenant: __dataclass__init__fields__62__annotation = __dataclass__init__fields__62__default,
            dedicated_log_volume: __dataclass__init__fields__63__annotation = __dataclass__init__fields__63__default,
            engine_lifecycle_support: __dataclass__init__fields__64__annotation = __dataclass__init__fields__64__default,
            additional_storage_volumes: __dataclass__init__fields__65__annotation = __dataclass__init__fields__65__default,
            tag_specifications: __dataclass__init__fields__66__annotation = __dataclass__init__fields__66__default,
            master_user_authentication_type: __dataclass__init__fields__67__annotation = __dataclass__init__fields__67__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_name', db_name)
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'allocated_storage', allocated_storage)
            __dataclass__object_setattr(self, 'db_instance_class', db_instance_class)
            __dataclass__object_setattr(self, 'engine', engine)
            __dataclass__object_setattr(self, 'master_username', master_username)
            __dataclass__object_setattr(self, 'master_user_password', master_user_password)
            __dataclass__object_setattr(self, 'db_security_groups', db_security_groups)
            __dataclass__object_setattr(self, 'vpc_security_group_ids', vpc_security_group_ids)
            __dataclass__object_setattr(self, 'availability_zone', availability_zone)
            __dataclass__object_setattr(self, 'db_subnet_group_name', db_subnet_group_name)
            __dataclass__object_setattr(self, 'preferred_maintenance_window', preferred_maintenance_window)
            __dataclass__object_setattr(self, 'db_parameter_group_name', db_parameter_group_name)
            __dataclass__object_setattr(self, 'backup_retention_period', backup_retention_period)
            __dataclass__object_setattr(self, 'preferred_backup_window', preferred_backup_window)
            __dataclass__object_setattr(self, 'port', port)
            __dataclass__object_setattr(self, 'multi_az', multi_az)
            __dataclass__object_setattr(self, 'engine_version', engine_version)
            __dataclass__object_setattr(self, 'auto_minor_version_upgrade', auto_minor_version_upgrade)
            __dataclass__object_setattr(self, 'license_model', license_model)
            __dataclass__object_setattr(self, 'iops', iops)
            __dataclass__object_setattr(self, 'storage_throughput', storage_throughput)
            __dataclass__object_setattr(self, 'option_group_name', option_group_name)
            __dataclass__object_setattr(self, 'character_set_name', character_set_name)
            __dataclass__object_setattr(self, 'nchar_character_set_name', nchar_character_set_name)
            __dataclass__object_setattr(self, 'publicly_accessible', publicly_accessible)
            __dataclass__object_setattr(self, 'tags', tags)
            __dataclass__object_setattr(self, 'db_cluster_identifier', db_cluster_identifier)
            __dataclass__object_setattr(self, 'storage_type', storage_type)
            __dataclass__object_setattr(self, 'tde_credential_arn', tde_credential_arn)
            __dataclass__object_setattr(self, 'tde_credential_password', tde_credential_password)
            __dataclass__object_setattr(self, 'storage_encrypted', storage_encrypted)
            __dataclass__object_setattr(self, 'kms_key_id', kms_key_id)
            __dataclass__object_setattr(self, 'domain', domain)
            __dataclass__object_setattr(self, 'domain_fqdn', domain_fqdn)
            __dataclass__object_setattr(self, 'domain_ou', domain_ou)
            __dataclass__object_setattr(self, 'domain_auth_secret_arn', domain_auth_secret_arn)
            __dataclass__object_setattr(self, 'domain_dns_ips', domain_dns_ips)
            __dataclass__object_setattr(self, 'copy_tags_to_snapshot', copy_tags_to_snapshot)
            __dataclass__object_setattr(self, 'monitoring_interval', monitoring_interval)
            __dataclass__object_setattr(self, 'monitoring_role_arn', monitoring_role_arn)
            __dataclass__object_setattr(self, 'domain_iam_role_name', domain_iam_role_name)
            __dataclass__object_setattr(self, 'promotion_tier', promotion_tier)
            __dataclass__object_setattr(self, 'timezone', timezone)
            __dataclass__object_setattr(self, 'enable_iam_database_authentication', enable_iam_database_authentication)
            __dataclass__object_setattr(self, 'database_insights_mode', database_insights_mode)
            __dataclass__object_setattr(self, 'enable_performance_insights', enable_performance_insights)
            __dataclass__object_setattr(self, 'performance_insights_kms_key_id', performance_insights_kms_key_id)
            __dataclass__object_setattr(self, 'performance_insights_retention_period', performance_insights_retention_period)
            __dataclass__object_setattr(self, 'enable_cloudwatch_logs_exports', enable_cloudwatch_logs_exports)
            __dataclass__object_setattr(self, 'processor_features', processor_features)
            __dataclass__object_setattr(self, 'deletion_protection', deletion_protection)
            __dataclass__object_setattr(self, 'max_allocated_storage', max_allocated_storage)
            __dataclass__object_setattr(self, 'enable_customer_owned_ip', enable_customer_owned_ip)
            __dataclass__object_setattr(self, 'network_type', network_type)
            __dataclass__object_setattr(self, 'backup_target', backup_target)
            __dataclass__object_setattr(self, 'custom_iam_instance_profile', custom_iam_instance_profile)
            __dataclass__object_setattr(self, 'db_system_id', db_system_id)
            __dataclass__object_setattr(self, 'ca_certificate_identifier', ca_certificate_identifier)
            __dataclass__object_setattr(self, 'manage_master_user_password', manage_master_user_password)
            __dataclass__object_setattr(self, 'master_user_secret_kms_key_id', master_user_secret_kms_key_id)
            __dataclass__object_setattr(self, 'multi_tenant', multi_tenant)
            __dataclass__object_setattr(self, 'dedicated_log_volume', dedicated_log_volume)
            __dataclass__object_setattr(self, 'engine_lifecycle_support', engine_lifecycle_support)
            __dataclass__object_setattr(self, 'additional_storage_volumes', additional_storage_volumes)
            __dataclass__object_setattr(self, 'tag_specifications', tag_specifications)
            __dataclass__object_setattr(self, 'master_user_authentication_type', master_user_authentication_type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_name={self.db_name!r}")
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"allocated_storage={self.allocated_storage!r}")
            parts.append(f"db_instance_class={self.db_instance_class!r}")
            parts.append(f"engine={self.engine!r}")
            parts.append(f"master_username={self.master_username!r}")
            parts.append(f"master_user_password={self.master_user_password!r}")
            parts.append(f"db_security_groups={self.db_security_groups!r}")
            parts.append(f"vpc_security_group_ids={self.vpc_security_group_ids!r}")
            parts.append(f"availability_zone={self.availability_zone!r}")
            parts.append(f"db_subnet_group_name={self.db_subnet_group_name!r}")
            parts.append(f"preferred_maintenance_window={self.preferred_maintenance_window!r}")
            parts.append(f"db_parameter_group_name={self.db_parameter_group_name!r}")
            parts.append(f"backup_retention_period={self.backup_retention_period!r}")
            parts.append(f"preferred_backup_window={self.preferred_backup_window!r}")
            parts.append(f"port={self.port!r}")
            parts.append(f"multi_az={self.multi_az!r}")
            parts.append(f"engine_version={self.engine_version!r}")
            parts.append(f"auto_minor_version_upgrade={self.auto_minor_version_upgrade!r}")
            parts.append(f"license_model={self.license_model!r}")
            parts.append(f"iops={self.iops!r}")
            parts.append(f"storage_throughput={self.storage_throughput!r}")
            parts.append(f"option_group_name={self.option_group_name!r}")
            parts.append(f"character_set_name={self.character_set_name!r}")
            parts.append(f"nchar_character_set_name={self.nchar_character_set_name!r}")
            parts.append(f"publicly_accessible={self.publicly_accessible!r}")
            parts.append(f"tags={self.tags!r}")
            parts.append(f"db_cluster_identifier={self.db_cluster_identifier!r}")
            parts.append(f"storage_type={self.storage_type!r}")
            parts.append(f"tde_credential_arn={self.tde_credential_arn!r}")
            parts.append(f"tde_credential_password={self.tde_credential_password!r}")
            parts.append(f"storage_encrypted={self.storage_encrypted!r}")
            parts.append(f"kms_key_id={self.kms_key_id!r}")
            parts.append(f"domain={self.domain!r}")
            parts.append(f"domain_fqdn={self.domain_fqdn!r}")
            parts.append(f"domain_ou={self.domain_ou!r}")
            parts.append(f"domain_auth_secret_arn={self.domain_auth_secret_arn!r}")
            parts.append(f"domain_dns_ips={self.domain_dns_ips!r}")
            parts.append(f"copy_tags_to_snapshot={self.copy_tags_to_snapshot!r}")
            parts.append(f"monitoring_interval={self.monitoring_interval!r}")
            parts.append(f"monitoring_role_arn={self.monitoring_role_arn!r}")
            parts.append(f"domain_iam_role_name={self.domain_iam_role_name!r}")
            parts.append(f"promotion_tier={self.promotion_tier!r}")
            parts.append(f"timezone={self.timezone!r}")
            parts.append(f"enable_iam_database_authentication={self.enable_iam_database_authentication!r}")
            parts.append(f"database_insights_mode={self.database_insights_mode!r}")
            parts.append(f"enable_performance_insights={self.enable_performance_insights!r}")
            parts.append(f"performance_insights_kms_key_id={self.performance_insights_kms_key_id!r}")
            parts.append(f"performance_insights_retention_period={self.performance_insights_retention_period!r}")
            parts.append(f"enable_cloudwatch_logs_exports={self.enable_cloudwatch_logs_exports!r}")
            parts.append(f"processor_features={self.processor_features!r}")
            parts.append(f"deletion_protection={self.deletion_protection!r}")
            parts.append(f"max_allocated_storage={self.max_allocated_storage!r}")
            parts.append(f"enable_customer_owned_ip={self.enable_customer_owned_ip!r}")
            parts.append(f"network_type={self.network_type!r}")
            parts.append(f"backup_target={self.backup_target!r}")
            parts.append(f"custom_iam_instance_profile={self.custom_iam_instance_profile!r}")
            parts.append(f"db_system_id={self.db_system_id!r}")
            parts.append(f"ca_certificate_identifier={self.ca_certificate_identifier!r}")
            parts.append(f"manage_master_user_password={self.manage_master_user_password!r}")
            parts.append(f"master_user_secret_kms_key_id={self.master_user_secret_kms_key_id!r}")
            parts.append(f"multi_tenant={self.multi_tenant!r}")
            parts.append(f"dedicated_log_volume={self.dedicated_log_volume!r}")
            parts.append(f"engine_lifecycle_support={self.engine_lifecycle_support!r}")
            parts.append(f"additional_storage_volumes={self.additional_storage_volumes!r}")
            parts.append(f"tag_specifications={self.tag_specifications!r}")
            parts.append(f"master_user_authentication_type={self.master_user_authentication_type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b96e3a8edc26faedfc34e34ad72ad81bfee82fee',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'CreateDBInstanceResult'),
        ('ominfra.clouds.aws.models.services.rds', 'DeleteDBInstanceResult'),
        ('ominfra.clouds.aws.models.services.rds', 'RebootDBInstanceResult'),
        ('ominfra.clouds.aws.models.services.rds', 'StartDBInstanceResult'),
        ('ominfra.clouds.aws.models.services.rds', 'StopDBInstanceResult'),
    ),
)
def _process_dataclass__b96e3a8edc26faedfc34e34ad72ad81bfee82fee():
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
                db_instance=self.db_instance,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance == other.db_instance
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance',
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
                self.db_instance,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance', db_instance)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance={self.db_instance!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e46e35686fba0a8e2aa5d19676cb617b88b3cd22',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('db_instance_class', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False), (('engine', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('db_instance_status', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('master_username', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('db_name', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('endpoint', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('allocated_storage', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('instance_create_ti"
            "me', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('prefe"
            "rred_backup_window', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('backup_retention_period', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('db_security_groups', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('vpc_security_groups', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('db_parameter_groups', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('availability_zone', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('db_subnet_group', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('preferred_maintenance_wind"
            "ow', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('upgra"
            "de_rollout_order', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fa"
            "lse), (('pending_modified_values', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('latest_restorable_time', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('multi_az', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('engine_version', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('auto_minor_version_upgrade', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('read_replica_source_db_instance_identif"
            "ier', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('read"
            "_replica_db_instance_identifiers', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('read_replica_db_cluster_identifiers', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('replica_mode', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('license_model', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('iops', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('storage_throughput', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('option_group_memberships', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('character_set_nam"
            "e', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('nchar_"
            "character_set_name', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('secondary_availability_zone', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('publicly_accessible', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('status_infos', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('storage_type', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('storage_encryption_type', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('tde_credential_arn', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('db_instance_port', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_cluster_identi"
            "fier', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('sto"
            "rage_encrypted', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('kms_key_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, F"
            "alse), (('dbi_resource_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, "
            "False, False), (('ca_certificate_identifier', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('domain_memberships', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('copy_tags_to_snapshot', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('monitoring_interval', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False), (('enhanced_monitoring_resource_arn'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('monitori"
            "ng_role_arn', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False),"
            " (('promotion_tier', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('db_instance_arn', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('timezone', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False), (('iam_database_authentication_enabled', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('database_insights_mode', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('performance_insights_enabled', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('performance_insights_k"
            "ms_key_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), ("
            "('performance_insights_retention_period', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('enabled_cloudwatch_logs_exports', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('processor_features', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('deletion_protection', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False), (('associated_roles', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('listener_endpoint'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('max_allo"
            "cated_storage', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False"
            "), (('tag_list', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('automation_mode', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('resume_full_automation_mode_time', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('customer_owned_ip_enabled', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('network_type', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('activity_stream_status', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('activity_stream_kms_key_id',"
            " True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('activity_"
            "stream_kinesis_stream_name', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('activity_stream_mode', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('activity_stream_engine_native_audit_fields_included', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('aws_backup_recovery_point_arn'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_insta"
            "nce_automated_backups_replications', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('backup_target', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('automatic_restart_time', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('custom_iam_instance_profile', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('activity_stream_policy_status', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('certificate_deta"
            "ils', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_s"
            "ystem_id', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (("
            "'master_user_secret', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('read_replica_source_db_cluster_identifier', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('percent_progress', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('multi_tenant', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('dedicated_log_volume', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False), (('is_storage_config_upgrade_availab"
            "le', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('engin"
            "e_lifecycle_support', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False), (('additional_storage_volumes', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('storage_volume_status', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('storage_operation_status', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('storage_operation_percent_progress', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (Fal"
            "se, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBInstance'),
    ),
)
def _process_dataclass__e46e35686fba0a8e2aa5d19676cb617b88b3cd22():
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
        __dataclass__init__fields__47__annotation = __dataclass__spec.fields[47].annotation
        __dataclass__init__fields__47__default = __dataclass__spec.fields[47].default.must()
        __dataclass__init__fields__48__annotation = __dataclass__spec.fields[48].annotation
        __dataclass__init__fields__48__default = __dataclass__spec.fields[48].default.must()
        __dataclass__init__fields__49__annotation = __dataclass__spec.fields[49].annotation
        __dataclass__init__fields__49__default = __dataclass__spec.fields[49].default.must()
        __dataclass__init__fields__50__annotation = __dataclass__spec.fields[50].annotation
        __dataclass__init__fields__50__default = __dataclass__spec.fields[50].default.must()
        __dataclass__init__fields__51__annotation = __dataclass__spec.fields[51].annotation
        __dataclass__init__fields__51__default = __dataclass__spec.fields[51].default.must()
        __dataclass__init__fields__52__annotation = __dataclass__spec.fields[52].annotation
        __dataclass__init__fields__52__default = __dataclass__spec.fields[52].default.must()
        __dataclass__init__fields__53__annotation = __dataclass__spec.fields[53].annotation
        __dataclass__init__fields__53__default = __dataclass__spec.fields[53].default.must()
        __dataclass__init__fields__54__annotation = __dataclass__spec.fields[54].annotation
        __dataclass__init__fields__54__default = __dataclass__spec.fields[54].default.must()
        __dataclass__init__fields__55__annotation = __dataclass__spec.fields[55].annotation
        __dataclass__init__fields__55__default = __dataclass__spec.fields[55].default.must()
        __dataclass__init__fields__56__annotation = __dataclass__spec.fields[56].annotation
        __dataclass__init__fields__56__default = __dataclass__spec.fields[56].default.must()
        __dataclass__init__fields__57__annotation = __dataclass__spec.fields[57].annotation
        __dataclass__init__fields__57__default = __dataclass__spec.fields[57].default.must()
        __dataclass__init__fields__58__annotation = __dataclass__spec.fields[58].annotation
        __dataclass__init__fields__58__default = __dataclass__spec.fields[58].default.must()
        __dataclass__init__fields__59__annotation = __dataclass__spec.fields[59].annotation
        __dataclass__init__fields__59__default = __dataclass__spec.fields[59].default.must()
        __dataclass__init__fields__60__annotation = __dataclass__spec.fields[60].annotation
        __dataclass__init__fields__60__default = __dataclass__spec.fields[60].default.must()
        __dataclass__init__fields__61__annotation = __dataclass__spec.fields[61].annotation
        __dataclass__init__fields__61__default = __dataclass__spec.fields[61].default.must()
        __dataclass__init__fields__62__annotation = __dataclass__spec.fields[62].annotation
        __dataclass__init__fields__62__default = __dataclass__spec.fields[62].default.must()
        __dataclass__init__fields__63__annotation = __dataclass__spec.fields[63].annotation
        __dataclass__init__fields__63__default = __dataclass__spec.fields[63].default.must()
        __dataclass__init__fields__64__annotation = __dataclass__spec.fields[64].annotation
        __dataclass__init__fields__64__default = __dataclass__spec.fields[64].default.must()
        __dataclass__init__fields__65__annotation = __dataclass__spec.fields[65].annotation
        __dataclass__init__fields__65__default = __dataclass__spec.fields[65].default.must()
        __dataclass__init__fields__66__annotation = __dataclass__spec.fields[66].annotation
        __dataclass__init__fields__66__default = __dataclass__spec.fields[66].default.must()
        __dataclass__init__fields__67__annotation = __dataclass__spec.fields[67].annotation
        __dataclass__init__fields__67__default = __dataclass__spec.fields[67].default.must()
        __dataclass__init__fields__68__annotation = __dataclass__spec.fields[68].annotation
        __dataclass__init__fields__68__default = __dataclass__spec.fields[68].default.must()
        __dataclass__init__fields__69__annotation = __dataclass__spec.fields[69].annotation
        __dataclass__init__fields__69__default = __dataclass__spec.fields[69].default.must()
        __dataclass__init__fields__70__annotation = __dataclass__spec.fields[70].annotation
        __dataclass__init__fields__70__default = __dataclass__spec.fields[70].default.must()
        __dataclass__init__fields__71__annotation = __dataclass__spec.fields[71].annotation
        __dataclass__init__fields__71__default = __dataclass__spec.fields[71].default.must()
        __dataclass__init__fields__72__annotation = __dataclass__spec.fields[72].annotation
        __dataclass__init__fields__72__default = __dataclass__spec.fields[72].default.must()
        __dataclass__init__fields__73__annotation = __dataclass__spec.fields[73].annotation
        __dataclass__init__fields__73__default = __dataclass__spec.fields[73].default.must()
        __dataclass__init__fields__74__annotation = __dataclass__spec.fields[74].annotation
        __dataclass__init__fields__74__default = __dataclass__spec.fields[74].default.must()
        __dataclass__init__fields__75__annotation = __dataclass__spec.fields[75].annotation
        __dataclass__init__fields__75__default = __dataclass__spec.fields[75].default.must()
        __dataclass__init__fields__76__annotation = __dataclass__spec.fields[76].annotation
        __dataclass__init__fields__76__default = __dataclass__spec.fields[76].default.must()
        __dataclass__init__fields__77__annotation = __dataclass__spec.fields[77].annotation
        __dataclass__init__fields__77__default = __dataclass__spec.fields[77].default.must()
        __dataclass__init__fields__78__annotation = __dataclass__spec.fields[78].annotation
        __dataclass__init__fields__78__default = __dataclass__spec.fields[78].default.must()
        __dataclass__init__fields__79__annotation = __dataclass__spec.fields[79].annotation
        __dataclass__init__fields__79__default = __dataclass__spec.fields[79].default.must()
        __dataclass__init__fields__80__annotation = __dataclass__spec.fields[80].annotation
        __dataclass__init__fields__80__default = __dataclass__spec.fields[80].default.must()
        __dataclass__init__fields__81__annotation = __dataclass__spec.fields[81].annotation
        __dataclass__init__fields__81__default = __dataclass__spec.fields[81].default.must()
        __dataclass__init__fields__82__annotation = __dataclass__spec.fields[82].annotation
        __dataclass__init__fields__82__default = __dataclass__spec.fields[82].default.must()
        __dataclass__init__fields__83__annotation = __dataclass__spec.fields[83].annotation
        __dataclass__init__fields__83__default = __dataclass__spec.fields[83].default.must()
        __dataclass__init__fields__84__annotation = __dataclass__spec.fields[84].annotation
        __dataclass__init__fields__84__default = __dataclass__spec.fields[84].default.must()
        __dataclass__init__fields__85__annotation = __dataclass__spec.fields[85].annotation
        __dataclass__init__fields__85__default = __dataclass__spec.fields[85].default.must()
        __dataclass__init__fields__86__annotation = __dataclass__spec.fields[86].annotation
        __dataclass__init__fields__86__default = __dataclass__spec.fields[86].default.must()
        __dataclass__init__fields__87__annotation = __dataclass__spec.fields[87].annotation
        __dataclass__init__fields__87__default = __dataclass__spec.fields[87].default.must()
        __dataclass__init__fields__88__annotation = __dataclass__spec.fields[88].annotation
        __dataclass__init__fields__88__default = __dataclass__spec.fields[88].default.must()
        __dataclass__init__fields__89__annotation = __dataclass__spec.fields[89].annotation
        __dataclass__init__fields__89__default = __dataclass__spec.fields[89].default.must()
        __dataclass__init__fields__90__annotation = __dataclass__spec.fields[90].annotation
        __dataclass__init__fields__90__default = __dataclass__spec.fields[90].default.must()
        __dataclass__init__fields__91__annotation = __dataclass__spec.fields[91].annotation
        __dataclass__init__fields__91__default = __dataclass__spec.fields[91].default.must()
        __dataclass__init__fields__92__annotation = __dataclass__spec.fields[92].annotation
        __dataclass__init__fields__92__default = __dataclass__spec.fields[92].default.must()
        __dataclass__init__fields__93__annotation = __dataclass__spec.fields[93].annotation
        __dataclass__init__fields__93__default = __dataclass__spec.fields[93].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                db_instance_identifier=self.db_instance_identifier,
                db_instance_class=self.db_instance_class,
                engine=self.engine,
                db_instance_status=self.db_instance_status,
                master_username=self.master_username,
                db_name=self.db_name,
                endpoint=self.endpoint,
                allocated_storage=self.allocated_storage,
                instance_create_time=self.instance_create_time,
                preferred_backup_window=self.preferred_backup_window,
                backup_retention_period=self.backup_retention_period,
                db_security_groups=self.db_security_groups,
                vpc_security_groups=self.vpc_security_groups,
                db_parameter_groups=self.db_parameter_groups,
                availability_zone=self.availability_zone,
                db_subnet_group=self.db_subnet_group,
                preferred_maintenance_window=self.preferred_maintenance_window,
                upgrade_rollout_order=self.upgrade_rollout_order,
                pending_modified_values=self.pending_modified_values,
                latest_restorable_time=self.latest_restorable_time,
                multi_az=self.multi_az,
                engine_version=self.engine_version,
                auto_minor_version_upgrade=self.auto_minor_version_upgrade,
                read_replica_source_db_instance_identifier=self.read_replica_source_db_instance_identifier,
                read_replica_db_instance_identifiers=self.read_replica_db_instance_identifiers,
                read_replica_db_cluster_identifiers=self.read_replica_db_cluster_identifiers,
                replica_mode=self.replica_mode,
                license_model=self.license_model,
                iops=self.iops,
                storage_throughput=self.storage_throughput,
                option_group_memberships=self.option_group_memberships,
                character_set_name=self.character_set_name,
                nchar_character_set_name=self.nchar_character_set_name,
                secondary_availability_zone=self.secondary_availability_zone,
                publicly_accessible=self.publicly_accessible,
                status_infos=self.status_infos,
                storage_type=self.storage_type,
                storage_encryption_type=self.storage_encryption_type,
                tde_credential_arn=self.tde_credential_arn,
                db_instance_port=self.db_instance_port,
                db_cluster_identifier=self.db_cluster_identifier,
                storage_encrypted=self.storage_encrypted,
                kms_key_id=self.kms_key_id,
                dbi_resource_id=self.dbi_resource_id,
                ca_certificate_identifier=self.ca_certificate_identifier,
                domain_memberships=self.domain_memberships,
                copy_tags_to_snapshot=self.copy_tags_to_snapshot,
                monitoring_interval=self.monitoring_interval,
                enhanced_monitoring_resource_arn=self.enhanced_monitoring_resource_arn,
                monitoring_role_arn=self.monitoring_role_arn,
                promotion_tier=self.promotion_tier,
                db_instance_arn=self.db_instance_arn,
                timezone=self.timezone,
                iam_database_authentication_enabled=self.iam_database_authentication_enabled,
                database_insights_mode=self.database_insights_mode,
                performance_insights_enabled=self.performance_insights_enabled,
                performance_insights_kms_key_id=self.performance_insights_kms_key_id,
                performance_insights_retention_period=self.performance_insights_retention_period,
                enabled_cloudwatch_logs_exports=self.enabled_cloudwatch_logs_exports,
                processor_features=self.processor_features,
                deletion_protection=self.deletion_protection,
                associated_roles=self.associated_roles,
                listener_endpoint=self.listener_endpoint,
                max_allocated_storage=self.max_allocated_storage,
                tag_list=self.tag_list,
                automation_mode=self.automation_mode,
                resume_full_automation_mode_time=self.resume_full_automation_mode_time,
                customer_owned_ip_enabled=self.customer_owned_ip_enabled,
                network_type=self.network_type,
                activity_stream_status=self.activity_stream_status,
                activity_stream_kms_key_id=self.activity_stream_kms_key_id,
                activity_stream_kinesis_stream_name=self.activity_stream_kinesis_stream_name,
                activity_stream_mode=self.activity_stream_mode,
                activity_stream_engine_native_audit_fields_included=self.activity_stream_engine_native_audit_fields_included,
                aws_backup_recovery_point_arn=self.aws_backup_recovery_point_arn,
                db_instance_automated_backups_replications=self.db_instance_automated_backups_replications,
                backup_target=self.backup_target,
                automatic_restart_time=self.automatic_restart_time,
                custom_iam_instance_profile=self.custom_iam_instance_profile,
                activity_stream_policy_status=self.activity_stream_policy_status,
                certificate_details=self.certificate_details,
                db_system_id=self.db_system_id,
                master_user_secret=self.master_user_secret,
                read_replica_source_db_cluster_identifier=self.read_replica_source_db_cluster_identifier,
                percent_progress=self.percent_progress,
                multi_tenant=self.multi_tenant,
                dedicated_log_volume=self.dedicated_log_volume,
                is_storage_config_upgrade_available=self.is_storage_config_upgrade_available,
                engine_lifecycle_support=self.engine_lifecycle_support,
                additional_storage_volumes=self.additional_storage_volumes,
                storage_volume_status=self.storage_volume_status,
                storage_operation_status=self.storage_operation_status,
                storage_operation_percent_progress=self.storage_operation_percent_progress,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier and
                self.db_instance_class == other.db_instance_class and
                self.engine == other.engine and
                self.db_instance_status == other.db_instance_status and
                self.master_username == other.master_username and
                self.db_name == other.db_name and
                self.endpoint == other.endpoint and
                self.allocated_storage == other.allocated_storage and
                self.instance_create_time == other.instance_create_time and
                self.preferred_backup_window == other.preferred_backup_window and
                self.backup_retention_period == other.backup_retention_period and
                self.db_security_groups == other.db_security_groups and
                self.vpc_security_groups == other.vpc_security_groups and
                self.db_parameter_groups == other.db_parameter_groups and
                self.availability_zone == other.availability_zone and
                self.db_subnet_group == other.db_subnet_group and
                self.preferred_maintenance_window == other.preferred_maintenance_window and
                self.upgrade_rollout_order == other.upgrade_rollout_order and
                self.pending_modified_values == other.pending_modified_values and
                self.latest_restorable_time == other.latest_restorable_time and
                self.multi_az == other.multi_az and
                self.engine_version == other.engine_version and
                self.auto_minor_version_upgrade == other.auto_minor_version_upgrade and
                self.read_replica_source_db_instance_identifier == other.read_replica_source_db_instance_identifier and
                self.read_replica_db_instance_identifiers == other.read_replica_db_instance_identifiers and
                self.read_replica_db_cluster_identifiers == other.read_replica_db_cluster_identifiers and
                self.replica_mode == other.replica_mode and
                self.license_model == other.license_model and
                self.iops == other.iops and
                self.storage_throughput == other.storage_throughput and
                self.option_group_memberships == other.option_group_memberships and
                self.character_set_name == other.character_set_name and
                self.nchar_character_set_name == other.nchar_character_set_name and
                self.secondary_availability_zone == other.secondary_availability_zone and
                self.publicly_accessible == other.publicly_accessible and
                self.status_infos == other.status_infos and
                self.storage_type == other.storage_type and
                self.storage_encryption_type == other.storage_encryption_type and
                self.tde_credential_arn == other.tde_credential_arn and
                self.db_instance_port == other.db_instance_port and
                self.db_cluster_identifier == other.db_cluster_identifier and
                self.storage_encrypted == other.storage_encrypted and
                self.kms_key_id == other.kms_key_id and
                self.dbi_resource_id == other.dbi_resource_id and
                self.ca_certificate_identifier == other.ca_certificate_identifier and
                self.domain_memberships == other.domain_memberships and
                self.copy_tags_to_snapshot == other.copy_tags_to_snapshot and
                self.monitoring_interval == other.monitoring_interval and
                self.enhanced_monitoring_resource_arn == other.enhanced_monitoring_resource_arn and
                self.monitoring_role_arn == other.monitoring_role_arn and
                self.promotion_tier == other.promotion_tier and
                self.db_instance_arn == other.db_instance_arn and
                self.timezone == other.timezone and
                self.iam_database_authentication_enabled == other.iam_database_authentication_enabled and
                self.database_insights_mode == other.database_insights_mode and
                self.performance_insights_enabled == other.performance_insights_enabled and
                self.performance_insights_kms_key_id == other.performance_insights_kms_key_id and
                self.performance_insights_retention_period == other.performance_insights_retention_period and
                self.enabled_cloudwatch_logs_exports == other.enabled_cloudwatch_logs_exports and
                self.processor_features == other.processor_features and
                self.deletion_protection == other.deletion_protection and
                self.associated_roles == other.associated_roles and
                self.listener_endpoint == other.listener_endpoint and
                self.max_allocated_storage == other.max_allocated_storage and
                self.tag_list == other.tag_list and
                self.automation_mode == other.automation_mode and
                self.resume_full_automation_mode_time == other.resume_full_automation_mode_time and
                self.customer_owned_ip_enabled == other.customer_owned_ip_enabled and
                self.network_type == other.network_type and
                self.activity_stream_status == other.activity_stream_status and
                self.activity_stream_kms_key_id == other.activity_stream_kms_key_id and
                self.activity_stream_kinesis_stream_name == other.activity_stream_kinesis_stream_name and
                self.activity_stream_mode == other.activity_stream_mode and
                self.activity_stream_engine_native_audit_fields_included == other.activity_stream_engine_native_audit_fields_included and
                self.aws_backup_recovery_point_arn == other.aws_backup_recovery_point_arn and
                self.db_instance_automated_backups_replications == other.db_instance_automated_backups_replications and
                self.backup_target == other.backup_target and
                self.automatic_restart_time == other.automatic_restart_time and
                self.custom_iam_instance_profile == other.custom_iam_instance_profile and
                self.activity_stream_policy_status == other.activity_stream_policy_status and
                self.certificate_details == other.certificate_details and
                self.db_system_id == other.db_system_id and
                self.master_user_secret == other.master_user_secret and
                self.read_replica_source_db_cluster_identifier == other.read_replica_source_db_cluster_identifier and
                self.percent_progress == other.percent_progress and
                self.multi_tenant == other.multi_tenant and
                self.dedicated_log_volume == other.dedicated_log_volume and
                self.is_storage_config_upgrade_available == other.is_storage_config_upgrade_available and
                self.engine_lifecycle_support == other.engine_lifecycle_support and
                self.additional_storage_volumes == other.additional_storage_volumes and
                self.storage_volume_status == other.storage_volume_status and
                self.storage_operation_status == other.storage_operation_status and
                self.storage_operation_percent_progress == other.storage_operation_percent_progress
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
            'db_instance_class',
            'engine',
            'db_instance_status',
            'master_username',
            'db_name',
            'endpoint',
            'allocated_storage',
            'instance_create_time',
            'preferred_backup_window',
            'backup_retention_period',
            'db_security_groups',
            'vpc_security_groups',
            'db_parameter_groups',
            'availability_zone',
            'db_subnet_group',
            'preferred_maintenance_window',
            'upgrade_rollout_order',
            'pending_modified_values',
            'latest_restorable_time',
            'multi_az',
            'engine_version',
            'auto_minor_version_upgrade',
            'read_replica_source_db_instance_identifier',
            'read_replica_db_instance_identifiers',
            'read_replica_db_cluster_identifiers',
            'replica_mode',
            'license_model',
            'iops',
            'storage_throughput',
            'option_group_memberships',
            'character_set_name',
            'nchar_character_set_name',
            'secondary_availability_zone',
            'publicly_accessible',
            'status_infos',
            'storage_type',
            'storage_encryption_type',
            'tde_credential_arn',
            'db_instance_port',
            'db_cluster_identifier',
            'storage_encrypted',
            'kms_key_id',
            'dbi_resource_id',
            'ca_certificate_identifier',
            'domain_memberships',
            'copy_tags_to_snapshot',
            'monitoring_interval',
            'enhanced_monitoring_resource_arn',
            'monitoring_role_arn',
            'promotion_tier',
            'db_instance_arn',
            'timezone',
            'iam_database_authentication_enabled',
            'database_insights_mode',
            'performance_insights_enabled',
            'performance_insights_kms_key_id',
            'performance_insights_retention_period',
            'enabled_cloudwatch_logs_exports',
            'processor_features',
            'deletion_protection',
            'associated_roles',
            'listener_endpoint',
            'max_allocated_storage',
            'tag_list',
            'automation_mode',
            'resume_full_automation_mode_time',
            'customer_owned_ip_enabled',
            'network_type',
            'activity_stream_status',
            'activity_stream_kms_key_id',
            'activity_stream_kinesis_stream_name',
            'activity_stream_mode',
            'activity_stream_engine_native_audit_fields_included',
            'aws_backup_recovery_point_arn',
            'db_instance_automated_backups_replications',
            'backup_target',
            'automatic_restart_time',
            'custom_iam_instance_profile',
            'activity_stream_policy_status',
            'certificate_details',
            'db_system_id',
            'master_user_secret',
            'read_replica_source_db_cluster_identifier',
            'percent_progress',
            'multi_tenant',
            'dedicated_log_volume',
            'is_storage_config_upgrade_available',
            'engine_lifecycle_support',
            'additional_storage_volumes',
            'storage_volume_status',
            'storage_operation_status',
            'storage_operation_percent_progress',
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
                self.db_instance_identifier,
                self.db_instance_class,
                self.engine,
                self.db_instance_status,
                self.master_username,
                self.db_name,
                self.endpoint,
                self.allocated_storage,
                self.instance_create_time,
                self.preferred_backup_window,
                self.backup_retention_period,
                self.db_security_groups,
                self.vpc_security_groups,
                self.db_parameter_groups,
                self.availability_zone,
                self.db_subnet_group,
                self.preferred_maintenance_window,
                self.upgrade_rollout_order,
                self.pending_modified_values,
                self.latest_restorable_time,
                self.multi_az,
                self.engine_version,
                self.auto_minor_version_upgrade,
                self.read_replica_source_db_instance_identifier,
                self.read_replica_db_instance_identifiers,
                self.read_replica_db_cluster_identifiers,
                self.replica_mode,
                self.license_model,
                self.iops,
                self.storage_throughput,
                self.option_group_memberships,
                self.character_set_name,
                self.nchar_character_set_name,
                self.secondary_availability_zone,
                self.publicly_accessible,
                self.status_infos,
                self.storage_type,
                self.storage_encryption_type,
                self.tde_credential_arn,
                self.db_instance_port,
                self.db_cluster_identifier,
                self.storage_encrypted,
                self.kms_key_id,
                self.dbi_resource_id,
                self.ca_certificate_identifier,
                self.domain_memberships,
                self.copy_tags_to_snapshot,
                self.monitoring_interval,
                self.enhanced_monitoring_resource_arn,
                self.monitoring_role_arn,
                self.promotion_tier,
                self.db_instance_arn,
                self.timezone,
                self.iam_database_authentication_enabled,
                self.database_insights_mode,
                self.performance_insights_enabled,
                self.performance_insights_kms_key_id,
                self.performance_insights_retention_period,
                self.enabled_cloudwatch_logs_exports,
                self.processor_features,
                self.deletion_protection,
                self.associated_roles,
                self.listener_endpoint,
                self.max_allocated_storage,
                self.tag_list,
                self.automation_mode,
                self.resume_full_automation_mode_time,
                self.customer_owned_ip_enabled,
                self.network_type,
                self.activity_stream_status,
                self.activity_stream_kms_key_id,
                self.activity_stream_kinesis_stream_name,
                self.activity_stream_mode,
                self.activity_stream_engine_native_audit_fields_included,
                self.aws_backup_recovery_point_arn,
                self.db_instance_automated_backups_replications,
                self.backup_target,
                self.automatic_restart_time,
                self.custom_iam_instance_profile,
                self.activity_stream_policy_status,
                self.certificate_details,
                self.db_system_id,
                self.master_user_secret,
                self.read_replica_source_db_cluster_identifier,
                self.percent_progress,
                self.multi_tenant,
                self.dedicated_log_volume,
                self.is_storage_config_upgrade_available,
                self.engine_lifecycle_support,
                self.additional_storage_volumes,
                self.storage_volume_status,
                self.storage_operation_status,
                self.storage_operation_percent_progress,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            db_instance_class: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            engine: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            db_instance_status: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            master_username: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            db_name: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            endpoint: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            allocated_storage: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            instance_create_time: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            preferred_backup_window: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            backup_retention_period: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            db_security_groups: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            vpc_security_groups: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            db_parameter_groups: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            availability_zone: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            db_subnet_group: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            preferred_maintenance_window: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            upgrade_rollout_order: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            pending_modified_values: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            latest_restorable_time: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            multi_az: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            engine_version: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            auto_minor_version_upgrade: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            read_replica_source_db_instance_identifier: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            read_replica_db_instance_identifiers: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            read_replica_db_cluster_identifiers: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            replica_mode: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            license_model: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            iops: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            storage_throughput: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            option_group_memberships: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            character_set_name: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            nchar_character_set_name: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            secondary_availability_zone: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            publicly_accessible: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            status_infos: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            storage_type: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            storage_encryption_type: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            tde_credential_arn: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            db_instance_port: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            db_cluster_identifier: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
            storage_encrypted: __dataclass__init__fields__42__annotation = __dataclass__init__fields__42__default,
            kms_key_id: __dataclass__init__fields__43__annotation = __dataclass__init__fields__43__default,
            dbi_resource_id: __dataclass__init__fields__44__annotation = __dataclass__init__fields__44__default,
            ca_certificate_identifier: __dataclass__init__fields__45__annotation = __dataclass__init__fields__45__default,
            domain_memberships: __dataclass__init__fields__46__annotation = __dataclass__init__fields__46__default,
            copy_tags_to_snapshot: __dataclass__init__fields__47__annotation = __dataclass__init__fields__47__default,
            monitoring_interval: __dataclass__init__fields__48__annotation = __dataclass__init__fields__48__default,
            enhanced_monitoring_resource_arn: __dataclass__init__fields__49__annotation = __dataclass__init__fields__49__default,
            monitoring_role_arn: __dataclass__init__fields__50__annotation = __dataclass__init__fields__50__default,
            promotion_tier: __dataclass__init__fields__51__annotation = __dataclass__init__fields__51__default,
            db_instance_arn: __dataclass__init__fields__52__annotation = __dataclass__init__fields__52__default,
            timezone: __dataclass__init__fields__53__annotation = __dataclass__init__fields__53__default,
            iam_database_authentication_enabled: __dataclass__init__fields__54__annotation = __dataclass__init__fields__54__default,
            database_insights_mode: __dataclass__init__fields__55__annotation = __dataclass__init__fields__55__default,
            performance_insights_enabled: __dataclass__init__fields__56__annotation = __dataclass__init__fields__56__default,
            performance_insights_kms_key_id: __dataclass__init__fields__57__annotation = __dataclass__init__fields__57__default,
            performance_insights_retention_period: __dataclass__init__fields__58__annotation = __dataclass__init__fields__58__default,
            enabled_cloudwatch_logs_exports: __dataclass__init__fields__59__annotation = __dataclass__init__fields__59__default,
            processor_features: __dataclass__init__fields__60__annotation = __dataclass__init__fields__60__default,
            deletion_protection: __dataclass__init__fields__61__annotation = __dataclass__init__fields__61__default,
            associated_roles: __dataclass__init__fields__62__annotation = __dataclass__init__fields__62__default,
            listener_endpoint: __dataclass__init__fields__63__annotation = __dataclass__init__fields__63__default,
            max_allocated_storage: __dataclass__init__fields__64__annotation = __dataclass__init__fields__64__default,
            tag_list: __dataclass__init__fields__65__annotation = __dataclass__init__fields__65__default,
            automation_mode: __dataclass__init__fields__66__annotation = __dataclass__init__fields__66__default,
            resume_full_automation_mode_time: __dataclass__init__fields__67__annotation = __dataclass__init__fields__67__default,
            customer_owned_ip_enabled: __dataclass__init__fields__68__annotation = __dataclass__init__fields__68__default,
            network_type: __dataclass__init__fields__69__annotation = __dataclass__init__fields__69__default,
            activity_stream_status: __dataclass__init__fields__70__annotation = __dataclass__init__fields__70__default,
            activity_stream_kms_key_id: __dataclass__init__fields__71__annotation = __dataclass__init__fields__71__default,
            activity_stream_kinesis_stream_name: __dataclass__init__fields__72__annotation = __dataclass__init__fields__72__default,
            activity_stream_mode: __dataclass__init__fields__73__annotation = __dataclass__init__fields__73__default,
            activity_stream_engine_native_audit_fields_included: __dataclass__init__fields__74__annotation = __dataclass__init__fields__74__default,
            aws_backup_recovery_point_arn: __dataclass__init__fields__75__annotation = __dataclass__init__fields__75__default,
            db_instance_automated_backups_replications: __dataclass__init__fields__76__annotation = __dataclass__init__fields__76__default,
            backup_target: __dataclass__init__fields__77__annotation = __dataclass__init__fields__77__default,
            automatic_restart_time: __dataclass__init__fields__78__annotation = __dataclass__init__fields__78__default,
            custom_iam_instance_profile: __dataclass__init__fields__79__annotation = __dataclass__init__fields__79__default,
            activity_stream_policy_status: __dataclass__init__fields__80__annotation = __dataclass__init__fields__80__default,
            certificate_details: __dataclass__init__fields__81__annotation = __dataclass__init__fields__81__default,
            db_system_id: __dataclass__init__fields__82__annotation = __dataclass__init__fields__82__default,
            master_user_secret: __dataclass__init__fields__83__annotation = __dataclass__init__fields__83__default,
            read_replica_source_db_cluster_identifier: __dataclass__init__fields__84__annotation = __dataclass__init__fields__84__default,
            percent_progress: __dataclass__init__fields__85__annotation = __dataclass__init__fields__85__default,
            multi_tenant: __dataclass__init__fields__86__annotation = __dataclass__init__fields__86__default,
            dedicated_log_volume: __dataclass__init__fields__87__annotation = __dataclass__init__fields__87__default,
            is_storage_config_upgrade_available: __dataclass__init__fields__88__annotation = __dataclass__init__fields__88__default,
            engine_lifecycle_support: __dataclass__init__fields__89__annotation = __dataclass__init__fields__89__default,
            additional_storage_volumes: __dataclass__init__fields__90__annotation = __dataclass__init__fields__90__default,
            storage_volume_status: __dataclass__init__fields__91__annotation = __dataclass__init__fields__91__default,
            storage_operation_status: __dataclass__init__fields__92__annotation = __dataclass__init__fields__92__default,
            storage_operation_percent_progress: __dataclass__init__fields__93__annotation = __dataclass__init__fields__93__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'db_instance_class', db_instance_class)
            __dataclass__object_setattr(self, 'engine', engine)
            __dataclass__object_setattr(self, 'db_instance_status', db_instance_status)
            __dataclass__object_setattr(self, 'master_username', master_username)
            __dataclass__object_setattr(self, 'db_name', db_name)
            __dataclass__object_setattr(self, 'endpoint', endpoint)
            __dataclass__object_setattr(self, 'allocated_storage', allocated_storage)
            __dataclass__object_setattr(self, 'instance_create_time', instance_create_time)
            __dataclass__object_setattr(self, 'preferred_backup_window', preferred_backup_window)
            __dataclass__object_setattr(self, 'backup_retention_period', backup_retention_period)
            __dataclass__object_setattr(self, 'db_security_groups', db_security_groups)
            __dataclass__object_setattr(self, 'vpc_security_groups', vpc_security_groups)
            __dataclass__object_setattr(self, 'db_parameter_groups', db_parameter_groups)
            __dataclass__object_setattr(self, 'availability_zone', availability_zone)
            __dataclass__object_setattr(self, 'db_subnet_group', db_subnet_group)
            __dataclass__object_setattr(self, 'preferred_maintenance_window', preferred_maintenance_window)
            __dataclass__object_setattr(self, 'upgrade_rollout_order', upgrade_rollout_order)
            __dataclass__object_setattr(self, 'pending_modified_values', pending_modified_values)
            __dataclass__object_setattr(self, 'latest_restorable_time', latest_restorable_time)
            __dataclass__object_setattr(self, 'multi_az', multi_az)
            __dataclass__object_setattr(self, 'engine_version', engine_version)
            __dataclass__object_setattr(self, 'auto_minor_version_upgrade', auto_minor_version_upgrade)
            __dataclass__object_setattr(self, 'read_replica_source_db_instance_identifier', read_replica_source_db_instance_identifier)
            __dataclass__object_setattr(self, 'read_replica_db_instance_identifiers', read_replica_db_instance_identifiers)
            __dataclass__object_setattr(self, 'read_replica_db_cluster_identifiers', read_replica_db_cluster_identifiers)
            __dataclass__object_setattr(self, 'replica_mode', replica_mode)
            __dataclass__object_setattr(self, 'license_model', license_model)
            __dataclass__object_setattr(self, 'iops', iops)
            __dataclass__object_setattr(self, 'storage_throughput', storage_throughput)
            __dataclass__object_setattr(self, 'option_group_memberships', option_group_memberships)
            __dataclass__object_setattr(self, 'character_set_name', character_set_name)
            __dataclass__object_setattr(self, 'nchar_character_set_name', nchar_character_set_name)
            __dataclass__object_setattr(self, 'secondary_availability_zone', secondary_availability_zone)
            __dataclass__object_setattr(self, 'publicly_accessible', publicly_accessible)
            __dataclass__object_setattr(self, 'status_infos', status_infos)
            __dataclass__object_setattr(self, 'storage_type', storage_type)
            __dataclass__object_setattr(self, 'storage_encryption_type', storage_encryption_type)
            __dataclass__object_setattr(self, 'tde_credential_arn', tde_credential_arn)
            __dataclass__object_setattr(self, 'db_instance_port', db_instance_port)
            __dataclass__object_setattr(self, 'db_cluster_identifier', db_cluster_identifier)
            __dataclass__object_setattr(self, 'storage_encrypted', storage_encrypted)
            __dataclass__object_setattr(self, 'kms_key_id', kms_key_id)
            __dataclass__object_setattr(self, 'dbi_resource_id', dbi_resource_id)
            __dataclass__object_setattr(self, 'ca_certificate_identifier', ca_certificate_identifier)
            __dataclass__object_setattr(self, 'domain_memberships', domain_memberships)
            __dataclass__object_setattr(self, 'copy_tags_to_snapshot', copy_tags_to_snapshot)
            __dataclass__object_setattr(self, 'monitoring_interval', monitoring_interval)
            __dataclass__object_setattr(self, 'enhanced_monitoring_resource_arn', enhanced_monitoring_resource_arn)
            __dataclass__object_setattr(self, 'monitoring_role_arn', monitoring_role_arn)
            __dataclass__object_setattr(self, 'promotion_tier', promotion_tier)
            __dataclass__object_setattr(self, 'db_instance_arn', db_instance_arn)
            __dataclass__object_setattr(self, 'timezone', timezone)
            __dataclass__object_setattr(self, 'iam_database_authentication_enabled', iam_database_authentication_enabled)
            __dataclass__object_setattr(self, 'database_insights_mode', database_insights_mode)
            __dataclass__object_setattr(self, 'performance_insights_enabled', performance_insights_enabled)
            __dataclass__object_setattr(self, 'performance_insights_kms_key_id', performance_insights_kms_key_id)
            __dataclass__object_setattr(self, 'performance_insights_retention_period', performance_insights_retention_period)
            __dataclass__object_setattr(self, 'enabled_cloudwatch_logs_exports', enabled_cloudwatch_logs_exports)
            __dataclass__object_setattr(self, 'processor_features', processor_features)
            __dataclass__object_setattr(self, 'deletion_protection', deletion_protection)
            __dataclass__object_setattr(self, 'associated_roles', associated_roles)
            __dataclass__object_setattr(self, 'listener_endpoint', listener_endpoint)
            __dataclass__object_setattr(self, 'max_allocated_storage', max_allocated_storage)
            __dataclass__object_setattr(self, 'tag_list', tag_list)
            __dataclass__object_setattr(self, 'automation_mode', automation_mode)
            __dataclass__object_setattr(self, 'resume_full_automation_mode_time', resume_full_automation_mode_time)
            __dataclass__object_setattr(self, 'customer_owned_ip_enabled', customer_owned_ip_enabled)
            __dataclass__object_setattr(self, 'network_type', network_type)
            __dataclass__object_setattr(self, 'activity_stream_status', activity_stream_status)
            __dataclass__object_setattr(self, 'activity_stream_kms_key_id', activity_stream_kms_key_id)
            __dataclass__object_setattr(self, 'activity_stream_kinesis_stream_name', activity_stream_kinesis_stream_name)
            __dataclass__object_setattr(self, 'activity_stream_mode', activity_stream_mode)
            __dataclass__object_setattr(self, 'activity_stream_engine_native_audit_fields_included', activity_stream_engine_native_audit_fields_included)
            __dataclass__object_setattr(self, 'aws_backup_recovery_point_arn', aws_backup_recovery_point_arn)
            __dataclass__object_setattr(self, 'db_instance_automated_backups_replications', db_instance_automated_backups_replications)
            __dataclass__object_setattr(self, 'backup_target', backup_target)
            __dataclass__object_setattr(self, 'automatic_restart_time', automatic_restart_time)
            __dataclass__object_setattr(self, 'custom_iam_instance_profile', custom_iam_instance_profile)
            __dataclass__object_setattr(self, 'activity_stream_policy_status', activity_stream_policy_status)
            __dataclass__object_setattr(self, 'certificate_details', certificate_details)
            __dataclass__object_setattr(self, 'db_system_id', db_system_id)
            __dataclass__object_setattr(self, 'master_user_secret', master_user_secret)
            __dataclass__object_setattr(self, 'read_replica_source_db_cluster_identifier', read_replica_source_db_cluster_identifier)
            __dataclass__object_setattr(self, 'percent_progress', percent_progress)
            __dataclass__object_setattr(self, 'multi_tenant', multi_tenant)
            __dataclass__object_setattr(self, 'dedicated_log_volume', dedicated_log_volume)
            __dataclass__object_setattr(self, 'is_storage_config_upgrade_available', is_storage_config_upgrade_available)
            __dataclass__object_setattr(self, 'engine_lifecycle_support', engine_lifecycle_support)
            __dataclass__object_setattr(self, 'additional_storage_volumes', additional_storage_volumes)
            __dataclass__object_setattr(self, 'storage_volume_status', storage_volume_status)
            __dataclass__object_setattr(self, 'storage_operation_status', storage_operation_status)
            __dataclass__object_setattr(self, 'storage_operation_percent_progress', storage_operation_percent_progress)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"db_instance_class={self.db_instance_class!r}")
            parts.append(f"engine={self.engine!r}")
            parts.append(f"db_instance_status={self.db_instance_status!r}")
            parts.append(f"master_username={self.master_username!r}")
            parts.append(f"db_name={self.db_name!r}")
            parts.append(f"endpoint={self.endpoint!r}")
            parts.append(f"allocated_storage={self.allocated_storage!r}")
            parts.append(f"instance_create_time={self.instance_create_time!r}")
            parts.append(f"preferred_backup_window={self.preferred_backup_window!r}")
            parts.append(f"backup_retention_period={self.backup_retention_period!r}")
            parts.append(f"db_security_groups={self.db_security_groups!r}")
            parts.append(f"vpc_security_groups={self.vpc_security_groups!r}")
            parts.append(f"db_parameter_groups={self.db_parameter_groups!r}")
            parts.append(f"availability_zone={self.availability_zone!r}")
            parts.append(f"db_subnet_group={self.db_subnet_group!r}")
            parts.append(f"preferred_maintenance_window={self.preferred_maintenance_window!r}")
            parts.append(f"upgrade_rollout_order={self.upgrade_rollout_order!r}")
            parts.append(f"pending_modified_values={self.pending_modified_values!r}")
            parts.append(f"latest_restorable_time={self.latest_restorable_time!r}")
            parts.append(f"multi_az={self.multi_az!r}")
            parts.append(f"engine_version={self.engine_version!r}")
            parts.append(f"auto_minor_version_upgrade={self.auto_minor_version_upgrade!r}")
            parts.append(f"read_replica_source_db_instance_identifier={self.read_replica_source_db_instance_identifier!r}")
            parts.append(f"read_replica_db_instance_identifiers={self.read_replica_db_instance_identifiers!r}")
            parts.append(f"read_replica_db_cluster_identifiers={self.read_replica_db_cluster_identifiers!r}")
            parts.append(f"replica_mode={self.replica_mode!r}")
            parts.append(f"license_model={self.license_model!r}")
            parts.append(f"iops={self.iops!r}")
            parts.append(f"storage_throughput={self.storage_throughput!r}")
            parts.append(f"option_group_memberships={self.option_group_memberships!r}")
            parts.append(f"character_set_name={self.character_set_name!r}")
            parts.append(f"nchar_character_set_name={self.nchar_character_set_name!r}")
            parts.append(f"secondary_availability_zone={self.secondary_availability_zone!r}")
            parts.append(f"publicly_accessible={self.publicly_accessible!r}")
            parts.append(f"status_infos={self.status_infos!r}")
            parts.append(f"storage_type={self.storage_type!r}")
            parts.append(f"storage_encryption_type={self.storage_encryption_type!r}")
            parts.append(f"tde_credential_arn={self.tde_credential_arn!r}")
            parts.append(f"db_instance_port={self.db_instance_port!r}")
            parts.append(f"db_cluster_identifier={self.db_cluster_identifier!r}")
            parts.append(f"storage_encrypted={self.storage_encrypted!r}")
            parts.append(f"kms_key_id={self.kms_key_id!r}")
            parts.append(f"dbi_resource_id={self.dbi_resource_id!r}")
            parts.append(f"ca_certificate_identifier={self.ca_certificate_identifier!r}")
            parts.append(f"domain_memberships={self.domain_memberships!r}")
            parts.append(f"copy_tags_to_snapshot={self.copy_tags_to_snapshot!r}")
            parts.append(f"monitoring_interval={self.monitoring_interval!r}")
            parts.append(f"enhanced_monitoring_resource_arn={self.enhanced_monitoring_resource_arn!r}")
            parts.append(f"monitoring_role_arn={self.monitoring_role_arn!r}")
            parts.append(f"promotion_tier={self.promotion_tier!r}")
            parts.append(f"db_instance_arn={self.db_instance_arn!r}")
            parts.append(f"timezone={self.timezone!r}")
            parts.append(f"iam_database_authentication_enabled={self.iam_database_authentication_enabled!r}")
            parts.append(f"database_insights_mode={self.database_insights_mode!r}")
            parts.append(f"performance_insights_enabled={self.performance_insights_enabled!r}")
            parts.append(f"performance_insights_kms_key_id={self.performance_insights_kms_key_id!r}")
            parts.append(f"performance_insights_retention_period={self.performance_insights_retention_period!r}")
            parts.append(f"enabled_cloudwatch_logs_exports={self.enabled_cloudwatch_logs_exports!r}")
            parts.append(f"processor_features={self.processor_features!r}")
            parts.append(f"deletion_protection={self.deletion_protection!r}")
            parts.append(f"associated_roles={self.associated_roles!r}")
            parts.append(f"listener_endpoint={self.listener_endpoint!r}")
            parts.append(f"max_allocated_storage={self.max_allocated_storage!r}")
            parts.append(f"tag_list={self.tag_list!r}")
            parts.append(f"automation_mode={self.automation_mode!r}")
            parts.append(f"resume_full_automation_mode_time={self.resume_full_automation_mode_time!r}")
            parts.append(f"customer_owned_ip_enabled={self.customer_owned_ip_enabled!r}")
            parts.append(f"network_type={self.network_type!r}")
            parts.append(f"activity_stream_status={self.activity_stream_status!r}")
            parts.append(f"activity_stream_kms_key_id={self.activity_stream_kms_key_id!r}")
            parts.append(f"activity_stream_kinesis_stream_name={self.activity_stream_kinesis_stream_name!r}")
            parts.append(f"activity_stream_mode={self.activity_stream_mode!r}")
            parts.append(f"activity_stream_engine_native_audit_fields_included={self.activity_stream_engine_native_audit_fields_included!r}")
            parts.append(f"aws_backup_recovery_point_arn={self.aws_backup_recovery_point_arn!r}")
            parts.append(f"db_instance_automated_backups_replications={self.db_instance_automated_backups_replications!r}")
            parts.append(f"backup_target={self.backup_target!r}")
            parts.append(f"automatic_restart_time={self.automatic_restart_time!r}")
            parts.append(f"custom_iam_instance_profile={self.custom_iam_instance_profile!r}")
            parts.append(f"activity_stream_policy_status={self.activity_stream_policy_status!r}")
            parts.append(f"certificate_details={self.certificate_details!r}")
            parts.append(f"db_system_id={self.db_system_id!r}")
            parts.append(f"master_user_secret={self.master_user_secret!r}")
            parts.append(f"read_replica_source_db_cluster_identifier={self.read_replica_source_db_cluster_identifier!r}")
            parts.append(f"percent_progress={self.percent_progress!r}")
            parts.append(f"multi_tenant={self.multi_tenant!r}")
            parts.append(f"dedicated_log_volume={self.dedicated_log_volume!r}")
            parts.append(f"is_storage_config_upgrade_available={self.is_storage_config_upgrade_available!r}")
            parts.append(f"engine_lifecycle_support={self.engine_lifecycle_support!r}")
            parts.append(f"additional_storage_volumes={self.additional_storage_volumes!r}")
            parts.append(f"storage_volume_status={self.storage_volume_status!r}")
            parts.append(f"storage_operation_status={self.storage_operation_status!r}")
            parts.append(f"storage_operation_percent_progress={self.storage_operation_percent_progress!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='119ab1c224ed6a03592aeafab078c63c1c7fd50c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_automated_backups_arn', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False,"
            " False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceAutomatedBackupsReplication'),
    ),
)
def _process_dataclass__119ab1c224ed6a03592aeafab078c63c1c7fd50c():
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
                db_instance_automated_backups_arn=self.db_instance_automated_backups_arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_automated_backups_arn == other.db_instance_automated_backups_arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_automated_backups_arn',
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
                self.db_instance_automated_backups_arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_automated_backups_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_automated_backups_arn', db_instance_automated_backups_arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_automated_backups_arn={self.db_instance_automated_backups_arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='179bc13374d14293e6e4482da15639f7814acdb9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('marker', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('db_instances', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceMessage'),
    ),
)
def _process_dataclass__179bc13374d14293e6e4482da15639f7814acdb9():
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
                marker=self.marker,
                db_instances=self.db_instances,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.marker == other.marker and
                self.db_instances == other.db_instances
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'marker',
            'db_instances',
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
                self.marker,
                self.db_instances,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            marker: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            db_instances: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'marker', marker)
            __dataclass__object_setattr(self, 'db_instances', db_instances)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"marker={self.marker!r}")
            parts.append(f"db_instances={self.db_instances!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='50b4823012fa2cbc57b26e6cc0de96283b73cd69',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('role_arn', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('feature_name', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('status', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceRole'),
    ),
)
def _process_dataclass__50b4823012fa2cbc57b26e6cc0de96283b73cd69():
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
                role_arn=self.role_arn,
                feature_name=self.feature_name,
                status=self.status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.role_arn == other.role_arn and
                self.feature_name == other.feature_name and
                self.status == other.status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'role_arn',
            'feature_name',
            'status',
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
                self.role_arn,
                self.feature_name,
                self.status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            role_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            feature_name: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            status: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'role_arn', role_arn)
            __dataclass__object_setattr(self, 'feature_name', feature_name)
            __dataclass__object_setattr(self, 'status', status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"role_arn={self.role_arn!r}")
            parts.append(f"feature_name={self.feature_name!r}")
            parts.append(f"status={self.status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3bbbfa38a25b94d79376e5c1aa001ac55298e4d4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('status_type', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('normal', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('status', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fal"
            "se))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBInstanceStatusInfo'),
    ),
)
def _process_dataclass__3bbbfa38a25b94d79376e5c1aa001ac55298e4d4():
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
                status_type=self.status_type,
                normal=self.normal,
                status=self.status,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status_type == other.status_type and
                self.normal == other.normal and
                self.status == other.status and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'status_type',
            'normal',
            'status',
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
                self.status_type,
                self.normal,
                self.status,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            status_type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            normal: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            status: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            message: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status_type', status_type)
            __dataclass__object_setattr(self, 'normal', normal)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status_type={self.status_type!r}")
            parts.append(f"normal={self.normal!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b3784f8712a5cf1b532411ed6964a5dd3fbc6b45',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_parameter_group_name', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('parameter_apply_status', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (F"
            "alse, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBParameterGroupStatus'),
    ),
)
def _process_dataclass__b3784f8712a5cf1b532411ed6964a5dd3fbc6b45():
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
                db_parameter_group_name=self.db_parameter_group_name,
                parameter_apply_status=self.parameter_apply_status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_parameter_group_name == other.db_parameter_group_name and
                self.parameter_apply_status == other.parameter_apply_status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_parameter_group_name',
            'parameter_apply_status',
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
                self.db_parameter_group_name,
                self.parameter_apply_status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_parameter_group_name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            parameter_apply_status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_parameter_group_name', db_parameter_group_name)
            __dataclass__object_setattr(self, 'parameter_apply_status', parameter_apply_status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_parameter_group_name={self.db_parameter_group_name!r}")
            parts.append(f"parameter_apply_status={self.parameter_apply_status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f94f767e7e2a53c7bb3f32b1d0245271c39616fb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_security_group_name', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('status', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()),"
            " (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBSecurityGroupMembership'),
    ),
)
def _process_dataclass__f94f767e7e2a53c7bb3f32b1d0245271c39616fb():
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
                db_security_group_name=self.db_security_group_name,
                status=self.status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_security_group_name == other.db_security_group_name and
                self.status == other.status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_security_group_name',
            'status',
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
                self.db_security_group_name,
                self.status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_security_group_name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_security_group_name', db_security_group_name)
            __dataclass__object_setattr(self, 'status', status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_security_group_name={self.db_security_group_name!r}")
            parts.append(f"status={self.status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a07601ffc870a42220f37e7ff9d138cee848f927',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_subnet_group_name', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('db_subnet_group_description', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('vpc_id', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('subnet_group_status', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('subnets', True, True, None, "
            "True, True, False, None), 'instance', 'value', None, False, False, False), (('db_subnet_group_arn', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('supported_networ"
            "k_types', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), Fa"
            "lse, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DBSubnetGroup'),
    ),
)
def _process_dataclass__a07601ffc870a42220f37e7ff9d138cee848f927():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                db_subnet_group_name=self.db_subnet_group_name,
                db_subnet_group_description=self.db_subnet_group_description,
                vpc_id=self.vpc_id,
                subnet_group_status=self.subnet_group_status,
                subnets=self.subnets,
                db_subnet_group_arn=self.db_subnet_group_arn,
                supported_network_types=self.supported_network_types,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_subnet_group_name == other.db_subnet_group_name and
                self.db_subnet_group_description == other.db_subnet_group_description and
                self.vpc_id == other.vpc_id and
                self.subnet_group_status == other.subnet_group_status and
                self.subnets == other.subnets and
                self.db_subnet_group_arn == other.db_subnet_group_arn and
                self.supported_network_types == other.supported_network_types
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_subnet_group_name',
            'db_subnet_group_description',
            'vpc_id',
            'subnet_group_status',
            'subnets',
            'db_subnet_group_arn',
            'supported_network_types',
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
                self.db_subnet_group_name,
                self.db_subnet_group_description,
                self.vpc_id,
                self.subnet_group_status,
                self.subnets,
                self.db_subnet_group_arn,
                self.supported_network_types,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_subnet_group_name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            db_subnet_group_description: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            vpc_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            subnet_group_status: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            subnets: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            db_subnet_group_arn: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            supported_network_types: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_subnet_group_name', db_subnet_group_name)
            __dataclass__object_setattr(self, 'db_subnet_group_description', db_subnet_group_description)
            __dataclass__object_setattr(self, 'vpc_id', vpc_id)
            __dataclass__object_setattr(self, 'subnet_group_status', subnet_group_status)
            __dataclass__object_setattr(self, 'subnets', subnets)
            __dataclass__object_setattr(self, 'db_subnet_group_arn', db_subnet_group_arn)
            __dataclass__object_setattr(self, 'supported_network_types', supported_network_types)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_subnet_group_name={self.db_subnet_group_name!r}")
            parts.append(f"db_subnet_group_description={self.db_subnet_group_description!r}")
            parts.append(f"vpc_id={self.vpc_id!r}")
            parts.append(f"subnet_group_status={self.subnet_group_status!r}")
            parts.append(f"subnets={self.subnets!r}")
            parts.append(f"db_subnet_group_arn={self.db_subnet_group_arn!r}")
            parts.append(f"supported_network_types={self.supported_network_types!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3b3447da704a504301d048be4b47d0e153c1e5ce',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('skip_final_snapshot', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('final_db_snapshot_identifier', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('delete_automated_backu"
            "ps', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, "
            "0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DeleteDBInstanceMessage'),
    ),
)
def _process_dataclass__3b3447da704a504301d048be4b47d0e153c1e5ce():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                db_instance_identifier=self.db_instance_identifier,
                skip_final_snapshot=self.skip_final_snapshot,
                final_db_snapshot_identifier=self.final_db_snapshot_identifier,
                delete_automated_backups=self.delete_automated_backups,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier and
                self.skip_final_snapshot == other.skip_final_snapshot and
                self.final_db_snapshot_identifier == other.final_db_snapshot_identifier and
                self.delete_automated_backups == other.delete_automated_backups
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
            'skip_final_snapshot',
            'final_db_snapshot_identifier',
            'delete_automated_backups',
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
                self.db_instance_identifier,
                self.skip_final_snapshot,
                self.final_db_snapshot_identifier,
                self.delete_automated_backups,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__1__annotation,
            skip_final_snapshot: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            final_db_snapshot_identifier: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            delete_automated_backups: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'skip_final_snapshot', skip_final_snapshot)
            __dataclass__object_setattr(self, 'final_db_snapshot_identifier', final_db_snapshot_identifier)
            __dataclass__object_setattr(self, 'delete_automated_backups', delete_automated_backups)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"skip_final_snapshot={self.skip_final_snapshot!r}")
            parts.append(f"final_db_snapshot_identifier={self.final_db_snapshot_identifier!r}")
            parts.append(f"delete_automated_backups={self.delete_automated_backups!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d3c7cba42290aba517ae1cb761dedf44a72c5f8a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('filters', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('max_records', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('marker', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, "
            "()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DescribeDBInstancesMessage'),
    ),
)
def _process_dataclass__d3c7cba42290aba517ae1cb761dedf44a72c5f8a():
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
                db_instance_identifier=self.db_instance_identifier,
                filters=self.filters,
                max_records=self.max_records,
                marker=self.marker,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier and
                self.filters == other.filters and
                self.max_records == other.max_records and
                self.marker == other.marker
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
            'filters',
            'max_records',
            'marker',
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
                self.db_instance_identifier,
                self.filters,
                self.max_records,
                self.marker,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            filters: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            max_records: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            marker: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'filters', filters)
            __dataclass__object_setattr(self, 'max_records', max_records)
            __dataclass__object_setattr(self, 'marker', marker)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"filters={self.filters!r}")
            parts.append(f"max_records={self.max_records!r}")
            parts.append(f"marker={self.marker!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0aaee42e4d1f458c0b19a3773387c2c67ec5606e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('domain', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('status', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('fqdn', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('iam_role_name', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('ou', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('auth_secret_arn', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('dns_ips', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'DomainMembership'),
    ),
)
def _process_dataclass__0aaee42e4d1f458c0b19a3773387c2c67ec5606e():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                domain=self.domain,
                status=self.status,
                fqdn=self.fqdn,
                iam_role_name=self.iam_role_name,
                ou=self.ou,
                auth_secret_arn=self.auth_secret_arn,
                dns_ips=self.dns_ips,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.domain == other.domain and
                self.status == other.status and
                self.fqdn == other.fqdn and
                self.iam_role_name == other.iam_role_name and
                self.ou == other.ou and
                self.auth_secret_arn == other.auth_secret_arn and
                self.dns_ips == other.dns_ips
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'domain',
            'status',
            'fqdn',
            'iam_role_name',
            'ou',
            'auth_secret_arn',
            'dns_ips',
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
                self.domain,
                self.status,
                self.fqdn,
                self.iam_role_name,
                self.ou,
                self.auth_secret_arn,
                self.dns_ips,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            domain: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            fqdn: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            iam_role_name: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            ou: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            auth_secret_arn: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            dns_ips: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'domain', domain)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'fqdn', fqdn)
            __dataclass__object_setattr(self, 'iam_role_name', iam_role_name)
            __dataclass__object_setattr(self, 'ou', ou)
            __dataclass__object_setattr(self, 'auth_secret_arn', auth_secret_arn)
            __dataclass__object_setattr(self, 'dns_ips', dns_ips)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"domain={self.domain!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"fqdn={self.fqdn!r}")
            parts.append(f"iam_role_name={self.iam_role_name!r}")
            parts.append(f"ou={self.ou!r}")
            parts.append(f"auth_secret_arn={self.auth_secret_arn!r}")
            parts.append(f"dns_ips={self.dns_ips!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f4b335ac7a2d06019d9f707d8daa1b1a610f024c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('address', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('port', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('hosted_zone_id', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'Endpoint'),
    ),
)
def _process_dataclass__f4b335ac7a2d06019d9f707d8daa1b1a610f024c():
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
                address=self.address,
                port=self.port,
                hosted_zone_id=self.hosted_zone_id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.address == other.address and
                self.port == other.port and
                self.hosted_zone_id == other.hosted_zone_id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'address',
            'port',
            'hosted_zone_id',
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
                self.address,
                self.port,
                self.hosted_zone_id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            address: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            port: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            hosted_zone_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'address', address)
            __dataclass__object_setattr(self, 'port', port)
            __dataclass__object_setattr(self, 'hosted_zone_id', hosted_zone_id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"address={self.address!r}")
            parts.append(f"port={self.port!r}")
            parts.append(f"hosted_zone_id={self.hosted_zone_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='21142fae7a13d66dd910b350ac4c840d29ae2dfb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('values', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False"
            "))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'Filter'),
    ),
)
def _process_dataclass__21142fae7a13d66dd910b350ac4c840d29ae2dfb():
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
                name=self.name,
                values=self.values,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.values == other.values
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'name',
            'values',
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
                self.values,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__1__annotation,
            values: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'values', values)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"values={self.values!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4eb76eae390d6a3e798516034c677b09e9f1dcf0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('secret_arn', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('secret_status', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('kms_key_id', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), ("
            "), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'MasterUserSecret'),
    ),
)
def _process_dataclass__4eb76eae390d6a3e798516034c677b09e9f1dcf0():
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
                secret_arn=self.secret_arn,
                secret_status=self.secret_status,
                kms_key_id=self.kms_key_id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.secret_arn == other.secret_arn and
                self.secret_status == other.secret_status and
                self.kms_key_id == other.kms_key_id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'secret_arn',
            'secret_status',
            'kms_key_id',
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
                self.secret_arn,
                self.secret_status,
                self.kms_key_id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            secret_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            secret_status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            kms_key_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'secret_arn', secret_arn)
            __dataclass__object_setattr(self, 'secret_status', secret_status)
            __dataclass__object_setattr(self, 'kms_key_id', kms_key_id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"secret_arn={self.secret_arn!r}")
            parts.append(f"secret_status={self.secret_status!r}")
            parts.append(f"kms_key_id={self.kms_key_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b6eb9e253c256654a786809a982a3eee8fbbeedb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('option_group_name', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('status', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), "
            "(), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'OptionGroupMembership'),
    ),
)
def _process_dataclass__b6eb9e253c256654a786809a982a3eee8fbbeedb():
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
                option_group_name=self.option_group_name,
                status=self.status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.option_group_name == other.option_group_name and
                self.status == other.status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'option_group_name',
            'status',
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
                self.option_group_name,
                self.status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            option_group_name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'option_group_name', option_group_name)
            __dataclass__object_setattr(self, 'status', status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"option_group_name={self.option_group_name!r}")
            parts.append(f"status={self.status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b6f91ccfac47c466183137ec0d9a608258e7ff52',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('arn', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'Outpost'),
    ),
)
def _process_dataclass__b6f91ccfac47c466183137ec0d9a608258e7ff52():
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
                arn=self.arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.arn == other.arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'arn',
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
                self.arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'arn', arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"arn={self.arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e36e93701173e1ac63e1c00bb3ff9a1e91837ba8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('log_types_to_enable', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('log_types_to_disable', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, "
            "False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'PendingCloudwatchLogsExports'),
    ),
)
def _process_dataclass__e36e93701173e1ac63e1c00bb3ff9a1e91837ba8():
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
                log_types_to_enable=self.log_types_to_enable,
                log_types_to_disable=self.log_types_to_disable,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.log_types_to_enable == other.log_types_to_enable and
                self.log_types_to_disable == other.log_types_to_disable
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'log_types_to_enable',
            'log_types_to_disable',
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
                self.log_types_to_enable,
                self.log_types_to_disable,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            log_types_to_enable: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            log_types_to_disable: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'log_types_to_enable', log_types_to_enable)
            __dataclass__object_setattr(self, 'log_types_to_disable', log_types_to_disable)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"log_types_to_enable={self.log_types_to_enable!r}")
            parts.append(f"log_types_to_disable={self.log_types_to_disable!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cfad17bbb4865b56c32437db12745bb934d82dc8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_class', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('allocated_storage', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('master_user_password', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('port', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('backup_retention_period', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('multi_az', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('engine_version', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('license_model', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('iops', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('storage_through"
            "put', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('db_i"
            "nstance_identifier', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('storage_type', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('ca_certificate_identifier', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('db_subnet_group_name', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('pending_cloudwatch_logs_exports', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('processor_features', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('automation_mode', True, "
            "True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('resume_full_auto"
            "mation_mode_time', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fa"
            "lse), (('multi_tenant', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fals"
            "e, False), (('iam_database_authentication_enabled', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('dedicated_log_volume', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('engine', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('additional_storage_volumes', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), F"
            "alse, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'PendingModifiedValues'),
    ),
)
def _process_dataclass__cfad17bbb4865b56c32437db12745bb934d82dc8():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                db_instance_class=self.db_instance_class,
                allocated_storage=self.allocated_storage,
                master_user_password=self.master_user_password,
                port=self.port,
                backup_retention_period=self.backup_retention_period,
                multi_az=self.multi_az,
                engine_version=self.engine_version,
                license_model=self.license_model,
                iops=self.iops,
                storage_throughput=self.storage_throughput,
                db_instance_identifier=self.db_instance_identifier,
                storage_type=self.storage_type,
                ca_certificate_identifier=self.ca_certificate_identifier,
                db_subnet_group_name=self.db_subnet_group_name,
                pending_cloudwatch_logs_exports=self.pending_cloudwatch_logs_exports,
                processor_features=self.processor_features,
                automation_mode=self.automation_mode,
                resume_full_automation_mode_time=self.resume_full_automation_mode_time,
                multi_tenant=self.multi_tenant,
                iam_database_authentication_enabled=self.iam_database_authentication_enabled,
                dedicated_log_volume=self.dedicated_log_volume,
                engine=self.engine,
                additional_storage_volumes=self.additional_storage_volumes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_class == other.db_instance_class and
                self.allocated_storage == other.allocated_storage and
                self.master_user_password == other.master_user_password and
                self.port == other.port and
                self.backup_retention_period == other.backup_retention_period and
                self.multi_az == other.multi_az and
                self.engine_version == other.engine_version and
                self.license_model == other.license_model and
                self.iops == other.iops and
                self.storage_throughput == other.storage_throughput and
                self.db_instance_identifier == other.db_instance_identifier and
                self.storage_type == other.storage_type and
                self.ca_certificate_identifier == other.ca_certificate_identifier and
                self.db_subnet_group_name == other.db_subnet_group_name and
                self.pending_cloudwatch_logs_exports == other.pending_cloudwatch_logs_exports and
                self.processor_features == other.processor_features and
                self.automation_mode == other.automation_mode and
                self.resume_full_automation_mode_time == other.resume_full_automation_mode_time and
                self.multi_tenant == other.multi_tenant and
                self.iam_database_authentication_enabled == other.iam_database_authentication_enabled and
                self.dedicated_log_volume == other.dedicated_log_volume and
                self.engine == other.engine and
                self.additional_storage_volumes == other.additional_storage_volumes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_class',
            'allocated_storage',
            'master_user_password',
            'port',
            'backup_retention_period',
            'multi_az',
            'engine_version',
            'license_model',
            'iops',
            'storage_throughput',
            'db_instance_identifier',
            'storage_type',
            'ca_certificate_identifier',
            'db_subnet_group_name',
            'pending_cloudwatch_logs_exports',
            'processor_features',
            'automation_mode',
            'resume_full_automation_mode_time',
            'multi_tenant',
            'iam_database_authentication_enabled',
            'dedicated_log_volume',
            'engine',
            'additional_storage_volumes',
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
                self.db_instance_class,
                self.allocated_storage,
                self.master_user_password,
                self.port,
                self.backup_retention_period,
                self.multi_az,
                self.engine_version,
                self.license_model,
                self.iops,
                self.storage_throughput,
                self.db_instance_identifier,
                self.storage_type,
                self.ca_certificate_identifier,
                self.db_subnet_group_name,
                self.pending_cloudwatch_logs_exports,
                self.processor_features,
                self.automation_mode,
                self.resume_full_automation_mode_time,
                self.multi_tenant,
                self.iam_database_authentication_enabled,
                self.dedicated_log_volume,
                self.engine,
                self.additional_storage_volumes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_class: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            allocated_storage: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            master_user_password: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            port: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            backup_retention_period: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            multi_az: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            engine_version: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            license_model: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            iops: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            storage_throughput: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            db_instance_identifier: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            storage_type: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            ca_certificate_identifier: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            db_subnet_group_name: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            pending_cloudwatch_logs_exports: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            processor_features: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            automation_mode: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            resume_full_automation_mode_time: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            multi_tenant: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            iam_database_authentication_enabled: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            dedicated_log_volume: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            engine: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            additional_storage_volumes: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_class', db_instance_class)
            __dataclass__object_setattr(self, 'allocated_storage', allocated_storage)
            __dataclass__object_setattr(self, 'master_user_password', master_user_password)
            __dataclass__object_setattr(self, 'port', port)
            __dataclass__object_setattr(self, 'backup_retention_period', backup_retention_period)
            __dataclass__object_setattr(self, 'multi_az', multi_az)
            __dataclass__object_setattr(self, 'engine_version', engine_version)
            __dataclass__object_setattr(self, 'license_model', license_model)
            __dataclass__object_setattr(self, 'iops', iops)
            __dataclass__object_setattr(self, 'storage_throughput', storage_throughput)
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'storage_type', storage_type)
            __dataclass__object_setattr(self, 'ca_certificate_identifier', ca_certificate_identifier)
            __dataclass__object_setattr(self, 'db_subnet_group_name', db_subnet_group_name)
            __dataclass__object_setattr(self, 'pending_cloudwatch_logs_exports', pending_cloudwatch_logs_exports)
            __dataclass__object_setattr(self, 'processor_features', processor_features)
            __dataclass__object_setattr(self, 'automation_mode', automation_mode)
            __dataclass__object_setattr(self, 'resume_full_automation_mode_time', resume_full_automation_mode_time)
            __dataclass__object_setattr(self, 'multi_tenant', multi_tenant)
            __dataclass__object_setattr(self, 'iam_database_authentication_enabled', iam_database_authentication_enabled)
            __dataclass__object_setattr(self, 'dedicated_log_volume', dedicated_log_volume)
            __dataclass__object_setattr(self, 'engine', engine)
            __dataclass__object_setattr(self, 'additional_storage_volumes', additional_storage_volumes)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_class={self.db_instance_class!r}")
            parts.append(f"allocated_storage={self.allocated_storage!r}")
            parts.append(f"master_user_password={self.master_user_password!r}")
            parts.append(f"port={self.port!r}")
            parts.append(f"backup_retention_period={self.backup_retention_period!r}")
            parts.append(f"multi_az={self.multi_az!r}")
            parts.append(f"engine_version={self.engine_version!r}")
            parts.append(f"license_model={self.license_model!r}")
            parts.append(f"iops={self.iops!r}")
            parts.append(f"storage_throughput={self.storage_throughput!r}")
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"storage_type={self.storage_type!r}")
            parts.append(f"ca_certificate_identifier={self.ca_certificate_identifier!r}")
            parts.append(f"db_subnet_group_name={self.db_subnet_group_name!r}")
            parts.append(f"pending_cloudwatch_logs_exports={self.pending_cloudwatch_logs_exports!r}")
            parts.append(f"processor_features={self.processor_features!r}")
            parts.append(f"automation_mode={self.automation_mode!r}")
            parts.append(f"resume_full_automation_mode_time={self.resume_full_automation_mode_time!r}")
            parts.append(f"multi_tenant={self.multi_tenant!r}")
            parts.append(f"iam_database_authentication_enabled={self.iam_database_authentication_enabled!r}")
            parts.append(f"dedicated_log_volume={self.dedicated_log_volume!r}")
            parts.append(f"engine={self.engine!r}")
            parts.append(f"additional_storage_volumes={self.additional_storage_volumes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='868c7bc6021648d31c80e0b7086870081451f48f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('value', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'ProcessorFeature'),
    ),
)
def _process_dataclass__868c7bc6021648d31c80e0b7086870081451f48f():
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
                name=self.name,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'name',
            'value',
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
                self.value,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            value: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'value', value)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"value={self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b59928241da14a4282bcb8db01524244d9941708',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('force_failover', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, F"
            "alse, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'RebootDBInstanceMessage'),
    ),
)
def _process_dataclass__b59928241da14a4282bcb8db01524244d9941708():
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
                db_instance_identifier=self.db_instance_identifier,
                force_failover=self.force_failover,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier and
                self.force_failover == other.force_failover
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
            'force_failover',
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
                self.db_instance_identifier,
                self.force_failover,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__1__annotation,
            force_failover: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'force_failover', force_failover)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"force_failover={self.force_failover!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='230bd3f3eb38398fc5902daf6773b144f1958c8b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ("
            ")), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'StartDBInstanceMessage'),
    ),
)
def _process_dataclass__230bd3f3eb38398fc5902daf6773b144f1958c8b():
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
                db_instance_identifier=self.db_instance_identifier,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
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
                self.db_instance_identifier,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1042ae28fa60bffee61ee11505e06e7bfc4a0c1d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('db_instance_identifier', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('db_snapshot_identifier', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, ("
            "False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'StopDBInstanceMessage'),
    ),
)
def _process_dataclass__1042ae28fa60bffee61ee11505e06e7bfc4a0c1d():
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
                db_instance_identifier=self.db_instance_identifier,
                db_snapshot_identifier=self.db_snapshot_identifier,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.db_instance_identifier == other.db_instance_identifier and
                self.db_snapshot_identifier == other.db_snapshot_identifier
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'db_instance_identifier',
            'db_snapshot_identifier',
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
                self.db_instance_identifier,
                self.db_snapshot_identifier,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            db_instance_identifier: __dataclass__init__fields__1__annotation,
            db_snapshot_identifier: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'db_instance_identifier', db_instance_identifier)
            __dataclass__object_setattr(self, 'db_snapshot_identifier', db_snapshot_identifier)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"db_instance_identifier={self.db_instance_identifier!r}")
            parts.append(f"db_snapshot_identifier={self.db_snapshot_identifier!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='de9b503562a4d8bd75d2c1e34eeed3af0e5f610d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('subnet_identifier', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('subnet_availability_zone', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('subnet_outpost', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('subnet_status', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), "
            "False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'Subnet'),
    ),
)
def _process_dataclass__de9b503562a4d8bd75d2c1e34eeed3af0e5f610d():
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
                subnet_identifier=self.subnet_identifier,
                subnet_availability_zone=self.subnet_availability_zone,
                subnet_outpost=self.subnet_outpost,
                subnet_status=self.subnet_status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.subnet_identifier == other.subnet_identifier and
                self.subnet_availability_zone == other.subnet_availability_zone and
                self.subnet_outpost == other.subnet_outpost and
                self.subnet_status == other.subnet_status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'subnet_identifier',
            'subnet_availability_zone',
            'subnet_outpost',
            'subnet_status',
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
                self.subnet_identifier,
                self.subnet_availability_zone,
                self.subnet_outpost,
                self.subnet_status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            subnet_identifier: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            subnet_availability_zone: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            subnet_outpost: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            subnet_status: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'subnet_identifier', subnet_identifier)
            __dataclass__object_setattr(self, 'subnet_availability_zone', subnet_availability_zone)
            __dataclass__object_setattr(self, 'subnet_outpost', subnet_outpost)
            __dataclass__object_setattr(self, 'subnet_status', subnet_status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"subnet_identifier={self.subnet_identifier!r}")
            parts.append(f"subnet_availability_zone={self.subnet_availability_zone!r}")
            parts.append(f"subnet_outpost={self.subnet_outpost!r}")
            parts.append(f"subnet_status={self.subnet_status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6800d064b1a5156893763a9990ac9f94b500e067',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('resource_type', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('tags', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fa"
            "lse))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'TagSpecification'),
    ),
)
def _process_dataclass__6800d064b1a5156893763a9990ac9f94b500e067():
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
                resource_type=self.resource_type,
                tags=self.tags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.resource_type == other.resource_type and
                self.tags == other.tags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'resource_type',
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
                self.resource_type,
                self.tags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            resource_type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            tags: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'resource_type', resource_type)
            __dataclass__object_setattr(self, 'tags', tags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"resource_type={self.resource_type!r}")
            parts.append(f"tags={self.tags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f89b7da0435b303082e1a81af5436fc49ec8ec0f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('vpc_security_group_id', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('status', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.rds', 'VpcSecurityGroupMembership'),
    ),
)
def _process_dataclass__f89b7da0435b303082e1a81af5436fc49ec8ec0f():
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
                vpc_security_group_id=self.vpc_security_group_id,
                status=self.status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.vpc_security_group_id == other.vpc_security_group_id and
                self.status == other.status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'vpc_security_group_id',
            'status',
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
                self.vpc_security_group_id,
                self.status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            vpc_security_group_id: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'vpc_security_group_id', vpc_security_group_id)
            __dataclass__object_setattr(self, 'status', status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"vpc_security_group_id={self.vpc_security_group_id!r}")
            parts.append(f"status={self.status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
