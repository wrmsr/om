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


IMPLEMENTATION_KEY = '9435723149cde3211bedb6c2958a590435b02c76608192a2caf2a7c46f2eb4b2'


@_register(
    installer_sha1='df90a613a1d162093754d7631f1027d2b37b2c2a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('lambda_managed_instances_capacity_provider_config', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (Fal"
            "se,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'CapacityProviderConfig'),
    ),
)
def _process_dataclass__df90a613a1d162093754d7631f1027d2b37b2c2a():
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
                lambda_managed_instances_capacity_provider_config=self.lambda_managed_instances_capacity_provider_config,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lambda_managed_instances_capacity_provider_config == other.lambda_managed_instances_capacity_provider_config
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'lambda_managed_instances_capacity_provider_config',
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
                self.lambda_managed_instances_capacity_provider_config,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            lambda_managed_instances_capacity_provider_config: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'lambda_managed_instances_capacity_provider_config', lambda_managed_instances_capacity_provider_config)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lambda_managed_instances_capacity_provider_config={self.lambda_managed_instances_capacity_provider_config!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='99f143aa07977396a94025d9431c3a4d264313f0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('target_arn', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'DeadLetterConfig'),
    ),
)
def _process_dataclass__99f143aa07977396a94025d9431c3a4d264313f0():
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
                target_arn=self.target_arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.target_arn == other.target_arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'target_arn',
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
                self.target_arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            target_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'target_arn', target_arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"target_arn={self.target_arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='939c75fa93c8b88a8c1728acd6a1f54544640e7e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('kms_key_arn', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('retention_period_in_days', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('execution_timeout', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (Fa"
            "lse,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'DurableConfig'),
    ),
)
def _process_dataclass__939c75fa93c8b88a8c1728acd6a1f54544640e7e():
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
                kms_key_arn=self.kms_key_arn,
                retention_period_in_days=self.retention_period_in_days,
                execution_timeout=self.execution_timeout,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kms_key_arn == other.kms_key_arn and
                self.retention_period_in_days == other.retention_period_in_days and
                self.execution_timeout == other.execution_timeout
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'kms_key_arn',
            'retention_period_in_days',
            'execution_timeout',
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
                self.kms_key_arn,
                self.retention_period_in_days,
                self.execution_timeout,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            kms_key_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            retention_period_in_days: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            execution_timeout: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kms_key_arn', kms_key_arn)
            __dataclass__object_setattr(self, 'retention_period_in_days', retention_period_in_days)
            __dataclass__object_setattr(self, 'execution_timeout', execution_timeout)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kms_key_arn={self.kms_key_arn!r}")
            parts.append(f"retention_period_in_days={self.retention_period_in_days!r}")
            parts.append(f"execution_timeout={self.execution_timeout!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d2b057f993c117ffa407e785a5e3800cdfca1e25',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('error_code', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'EnvironmentError_'),
        ('ominfra.clouds.aws.models.services.lambda_', 'ImageConfigError'),
        ('ominfra.clouds.aws.models.services.lambda_', 'RuntimeVersionError'),
    ),
)
def _process_dataclass__d2b057f993c117ffa407e785a5e3800cdfca1e25():
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
                error_code=self.error_code,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.error_code == other.error_code and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'error_code',
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
                self.error_code,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            error_code: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            message: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'error_code', error_code)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"error_code={self.error_code!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='560937a002d06232c0bf2dc622cd878163333cc1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('variables', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'EnvironmentResponse'),
    ),
)
def _process_dataclass__560937a002d06232c0bf2dc622cd878163333cc1():
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
                variables=self.variables,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.variables == other.variables and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'variables',
            'error',
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
                self.variables,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            variables: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            error: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'variables', variables)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"variables={self.variables!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='50379ba61943e1ed3794d8f48ea71519cf7974e0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('size', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'EphemeralStorage'),
    ),
)
def _process_dataclass__50379ba61943e1ed3794d8f48ea71519cf7974e0():
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
                size=self.size,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.size == other.size
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
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
                self.size,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            size: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'size', size)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"size={self.size!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1473192131b4cd2e9b197d577b3cdf26ac63ce4b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('arn', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('local_mount_path', True, True, None, True, True, False, None), 'instance',"
            " 'missing', None, False, False, False), (('s3_files_config', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'FileSystemConfig'),
    ),
)
def _process_dataclass__1473192131b4cd2e9b197d577b3cdf26ac63ce4b():
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
                local_mount_path=self.local_mount_path,
                s3_files_config=self.s3_files_config,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.arn == other.arn and
                self.local_mount_path == other.local_mount_path and
                self.s3_files_config == other.s3_files_config
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'arn',
            'local_mount_path',
            's3_files_config',
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
                self.local_mount_path,
                self.s3_files_config,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            arn: __dataclass__init__fields__1__annotation,
            local_mount_path: __dataclass__init__fields__2__annotation,
            s3_files_config: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'arn', arn)
            __dataclass__object_setattr(self, 'local_mount_path', local_mount_path)
            __dataclass__object_setattr(self, 's3_files_config', s3_files_config)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"arn={self.arn!r}")
            parts.append(f"local_mount_path={self.local_mount_path!r}")
            parts.append(f"s3_files_config={self.s3_files_config!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e0c7e45271d2d9861f00aaa7e6d4f873f63b497b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('function_name', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('function_arn', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('runtime', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('role', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('handler', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('code_size', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('description', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('timeout', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('memory_size', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('last_modified', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('code_sha256', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('version', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('vpc_config', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False), (('dead_letter_config', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('environment', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('kms_key_arn', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('tracing_config', True,"
            " True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('master_arn', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('revision_id'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('layers',"
            " True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('state', T"
            "rue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('state_reaso"
            "n', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('state_"
            "reason_code', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False),"
            " (('last_update_status', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('last_update_status_reason', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('last_update_status_reason_code', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('file_system_configs', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('signing_profile_version_arn', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('signing_job_arn', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('package_ty"
            "pe', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('image"
            "_config_response', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fa"
            "lse), (('architectures', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('ephemeral_storage', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('snap_start', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('runtime_version_config', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('logging_config', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('tenancy_config', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('capacity_provider_config', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('config_sha256', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('durable_config', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((Fals"
            "e,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'FunctionConfiguration'),
    ),
)
def _process_dataclass__e0c7e45271d2d9861f00aaa7e6d4f873f63b497b():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                function_name=self.function_name,
                function_arn=self.function_arn,
                runtime=self.runtime,
                role=self.role,
                handler=self.handler,
                code_size=self.code_size,
                description=self.description,
                timeout=self.timeout,
                memory_size=self.memory_size,
                last_modified=self.last_modified,
                code_sha256=self.code_sha256,
                version=self.version,
                vpc_config=self.vpc_config,
                dead_letter_config=self.dead_letter_config,
                environment=self.environment,
                kms_key_arn=self.kms_key_arn,
                tracing_config=self.tracing_config,
                master_arn=self.master_arn,
                revision_id=self.revision_id,
                layers=self.layers,
                state=self.state,
                state_reason=self.state_reason,
                state_reason_code=self.state_reason_code,
                last_update_status=self.last_update_status,
                last_update_status_reason=self.last_update_status_reason,
                last_update_status_reason_code=self.last_update_status_reason_code,
                file_system_configs=self.file_system_configs,
                signing_profile_version_arn=self.signing_profile_version_arn,
                signing_job_arn=self.signing_job_arn,
                package_type=self.package_type,
                image_config_response=self.image_config_response,
                architectures=self.architectures,
                ephemeral_storage=self.ephemeral_storage,
                snap_start=self.snap_start,
                runtime_version_config=self.runtime_version_config,
                logging_config=self.logging_config,
                tenancy_config=self.tenancy_config,
                capacity_provider_config=self.capacity_provider_config,
                config_sha256=self.config_sha256,
                durable_config=self.durable_config,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.function_name == other.function_name and
                self.function_arn == other.function_arn and
                self.runtime == other.runtime and
                self.role == other.role and
                self.handler == other.handler and
                self.code_size == other.code_size and
                self.description == other.description and
                self.timeout == other.timeout and
                self.memory_size == other.memory_size and
                self.last_modified == other.last_modified and
                self.code_sha256 == other.code_sha256 and
                self.version == other.version and
                self.vpc_config == other.vpc_config and
                self.dead_letter_config == other.dead_letter_config and
                self.environment == other.environment and
                self.kms_key_arn == other.kms_key_arn and
                self.tracing_config == other.tracing_config and
                self.master_arn == other.master_arn and
                self.revision_id == other.revision_id and
                self.layers == other.layers and
                self.state == other.state and
                self.state_reason == other.state_reason and
                self.state_reason_code == other.state_reason_code and
                self.last_update_status == other.last_update_status and
                self.last_update_status_reason == other.last_update_status_reason and
                self.last_update_status_reason_code == other.last_update_status_reason_code and
                self.file_system_configs == other.file_system_configs and
                self.signing_profile_version_arn == other.signing_profile_version_arn and
                self.signing_job_arn == other.signing_job_arn and
                self.package_type == other.package_type and
                self.image_config_response == other.image_config_response and
                self.architectures == other.architectures and
                self.ephemeral_storage == other.ephemeral_storage and
                self.snap_start == other.snap_start and
                self.runtime_version_config == other.runtime_version_config and
                self.logging_config == other.logging_config and
                self.tenancy_config == other.tenancy_config and
                self.capacity_provider_config == other.capacity_provider_config and
                self.config_sha256 == other.config_sha256 and
                self.durable_config == other.durable_config
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'function_name',
            'function_arn',
            'runtime',
            'role',
            'handler',
            'code_size',
            'description',
            'timeout',
            'memory_size',
            'last_modified',
            'code_sha256',
            'version',
            'vpc_config',
            'dead_letter_config',
            'environment',
            'kms_key_arn',
            'tracing_config',
            'master_arn',
            'revision_id',
            'layers',
            'state',
            'state_reason',
            'state_reason_code',
            'last_update_status',
            'last_update_status_reason',
            'last_update_status_reason_code',
            'file_system_configs',
            'signing_profile_version_arn',
            'signing_job_arn',
            'package_type',
            'image_config_response',
            'architectures',
            'ephemeral_storage',
            'snap_start',
            'runtime_version_config',
            'logging_config',
            'tenancy_config',
            'capacity_provider_config',
            'config_sha256',
            'durable_config',
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
                self.function_name,
                self.function_arn,
                self.runtime,
                self.role,
                self.handler,
                self.code_size,
                self.description,
                self.timeout,
                self.memory_size,
                self.last_modified,
                self.code_sha256,
                self.version,
                self.vpc_config,
                self.dead_letter_config,
                self.environment,
                self.kms_key_arn,
                self.tracing_config,
                self.master_arn,
                self.revision_id,
                self.layers,
                self.state,
                self.state_reason,
                self.state_reason_code,
                self.last_update_status,
                self.last_update_status_reason,
                self.last_update_status_reason_code,
                self.file_system_configs,
                self.signing_profile_version_arn,
                self.signing_job_arn,
                self.package_type,
                self.image_config_response,
                self.architectures,
                self.ephemeral_storage,
                self.snap_start,
                self.runtime_version_config,
                self.logging_config,
                self.tenancy_config,
                self.capacity_provider_config,
                self.config_sha256,
                self.durable_config,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            function_name: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            function_arn: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            runtime: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            role: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            handler: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            code_size: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            description: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            timeout: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            memory_size: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            last_modified: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            code_sha256: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            version: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            vpc_config: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            dead_letter_config: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            environment: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            kms_key_arn: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            tracing_config: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            master_arn: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            revision_id: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            layers: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            state: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            state_reason: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            state_reason_code: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            last_update_status: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            last_update_status_reason: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            last_update_status_reason_code: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            file_system_configs: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            signing_profile_version_arn: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            signing_job_arn: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            package_type: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            image_config_response: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            architectures: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            ephemeral_storage: __dataclass__init__fields__33__annotation = __dataclass__init__fields__33__default,
            snap_start: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            runtime_version_config: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            logging_config: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            tenancy_config: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            capacity_provider_config: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            config_sha256: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            durable_config: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'function_name', function_name)
            __dataclass__object_setattr(self, 'function_arn', function_arn)
            __dataclass__object_setattr(self, 'runtime', runtime)
            __dataclass__object_setattr(self, 'role', role)
            __dataclass__object_setattr(self, 'handler', handler)
            __dataclass__object_setattr(self, 'code_size', code_size)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'timeout', timeout)
            __dataclass__object_setattr(self, 'memory_size', memory_size)
            __dataclass__object_setattr(self, 'last_modified', last_modified)
            __dataclass__object_setattr(self, 'code_sha256', code_sha256)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'vpc_config', vpc_config)
            __dataclass__object_setattr(self, 'dead_letter_config', dead_letter_config)
            __dataclass__object_setattr(self, 'environment', environment)
            __dataclass__object_setattr(self, 'kms_key_arn', kms_key_arn)
            __dataclass__object_setattr(self, 'tracing_config', tracing_config)
            __dataclass__object_setattr(self, 'master_arn', master_arn)
            __dataclass__object_setattr(self, 'revision_id', revision_id)
            __dataclass__object_setattr(self, 'layers', layers)
            __dataclass__object_setattr(self, 'state', state)
            __dataclass__object_setattr(self, 'state_reason', state_reason)
            __dataclass__object_setattr(self, 'state_reason_code', state_reason_code)
            __dataclass__object_setattr(self, 'last_update_status', last_update_status)
            __dataclass__object_setattr(self, 'last_update_status_reason', last_update_status_reason)
            __dataclass__object_setattr(self, 'last_update_status_reason_code', last_update_status_reason_code)
            __dataclass__object_setattr(self, 'file_system_configs', file_system_configs)
            __dataclass__object_setattr(self, 'signing_profile_version_arn', signing_profile_version_arn)
            __dataclass__object_setattr(self, 'signing_job_arn', signing_job_arn)
            __dataclass__object_setattr(self, 'package_type', package_type)
            __dataclass__object_setattr(self, 'image_config_response', image_config_response)
            __dataclass__object_setattr(self, 'architectures', architectures)
            __dataclass__object_setattr(self, 'ephemeral_storage', ephemeral_storage)
            __dataclass__object_setattr(self, 'snap_start', snap_start)
            __dataclass__object_setattr(self, 'runtime_version_config', runtime_version_config)
            __dataclass__object_setattr(self, 'logging_config', logging_config)
            __dataclass__object_setattr(self, 'tenancy_config', tenancy_config)
            __dataclass__object_setattr(self, 'capacity_provider_config', capacity_provider_config)
            __dataclass__object_setattr(self, 'config_sha256', config_sha256)
            __dataclass__object_setattr(self, 'durable_config', durable_config)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"function_name={self.function_name!r}")
            parts.append(f"function_arn={self.function_arn!r}")
            parts.append(f"runtime={self.runtime!r}")
            parts.append(f"role={self.role!r}")
            parts.append(f"handler={self.handler!r}")
            parts.append(f"code_size={self.code_size!r}")
            parts.append(f"description={self.description!r}")
            parts.append(f"timeout={self.timeout!r}")
            parts.append(f"memory_size={self.memory_size!r}")
            parts.append(f"last_modified={self.last_modified!r}")
            parts.append(f"code_sha256={self.code_sha256!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"vpc_config={self.vpc_config!r}")
            parts.append(f"dead_letter_config={self.dead_letter_config!r}")
            parts.append(f"environment={self.environment!r}")
            parts.append(f"kms_key_arn={self.kms_key_arn!r}")
            parts.append(f"tracing_config={self.tracing_config!r}")
            parts.append(f"master_arn={self.master_arn!r}")
            parts.append(f"revision_id={self.revision_id!r}")
            parts.append(f"layers={self.layers!r}")
            parts.append(f"state={self.state!r}")
            parts.append(f"state_reason={self.state_reason!r}")
            parts.append(f"state_reason_code={self.state_reason_code!r}")
            parts.append(f"last_update_status={self.last_update_status!r}")
            parts.append(f"last_update_status_reason={self.last_update_status_reason!r}")
            parts.append(f"last_update_status_reason_code={self.last_update_status_reason_code!r}")
            parts.append(f"file_system_configs={self.file_system_configs!r}")
            parts.append(f"signing_profile_version_arn={self.signing_profile_version_arn!r}")
            parts.append(f"signing_job_arn={self.signing_job_arn!r}")
            parts.append(f"package_type={self.package_type!r}")
            parts.append(f"image_config_response={self.image_config_response!r}")
            parts.append(f"architectures={self.architectures!r}")
            parts.append(f"ephemeral_storage={self.ephemeral_storage!r}")
            parts.append(f"snap_start={self.snap_start!r}")
            parts.append(f"runtime_version_config={self.runtime_version_config!r}")
            parts.append(f"logging_config={self.logging_config!r}")
            parts.append(f"tenancy_config={self.tenancy_config!r}")
            parts.append(f"capacity_provider_config={self.capacity_provider_config!r}")
            parts.append(f"config_sha256={self.config_sha256!r}")
            parts.append(f"durable_config={self.durable_config!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='61c009c76115874910bc9df7e4844ce4787a4041',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('entry_point', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('command', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('working_directory', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fa"
            "lse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'ImageConfig'),
    ),
)
def _process_dataclass__61c009c76115874910bc9df7e4844ce4787a4041():
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
                entry_point=self.entry_point,
                command=self.command,
                working_directory=self.working_directory,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.entry_point == other.entry_point and
                self.command == other.command and
                self.working_directory == other.working_directory
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'entry_point',
            'command',
            'working_directory',
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
                self.entry_point,
                self.command,
                self.working_directory,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            entry_point: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            command: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            working_directory: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'entry_point', entry_point)
            __dataclass__object_setattr(self, 'command', command)
            __dataclass__object_setattr(self, 'working_directory', working_directory)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"entry_point={self.entry_point!r}")
            parts.append(f"command={self.command!r}")
            parts.append(f"working_directory={self.working_directory!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='dff908dcd9e4875efaa7e4d07e0669d4965cb0b3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('image_config', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'ImageConfigResponse'),
    ),
)
def _process_dataclass__dff908dcd9e4875efaa7e4d07e0669d4965cb0b3():
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
                image_config=self.image_config,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.image_config == other.image_config and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'image_config',
            'error',
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
                self.image_config,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            image_config: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            error: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'image_config', image_config)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"image_config={self.image_config!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d5c2aedadeb5b17df4e88dacf9f45eaeb5ebbc76',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'InvalidParameterValueException'),
        ('ominfra.clouds.aws.models.services.lambda_', 'ServiceException'),
    ),
)
def _process_dataclass__d5c2aedadeb5b17df4e88dacf9f45eaeb5ebbc76():
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
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'type',
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
                self.type,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            message: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cc49195501e061a7f7a3088ce818c9d3caf99fa9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('capacity_provider_arn', True, True, None, True, True, False, None), 'ins"
            "tance', 'missing', None, False, False, False), (('per_execution_environment_max_concurrency', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('execution_environment_"
            "memory_gib_per_vcpu', True, True, None, True, True, False, None), 'instance', 'value', None, False, False,"
            " False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'LambdaManagedInstancesCapacityProviderConfig'),
    ),
)
def _process_dataclass__cc49195501e061a7f7a3088ce818c9d3caf99fa9():
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
                capacity_provider_arn=self.capacity_provider_arn,
                per_execution_environment_max_concurrency=self.per_execution_environment_max_concurrency,
                execution_environment_memory_gib_per_vcpu=self.execution_environment_memory_gib_per_vcpu,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.capacity_provider_arn == other.capacity_provider_arn and
                self.per_execution_environment_max_concurrency == other.per_execution_environment_max_concurrency and
                self.execution_environment_memory_gib_per_vcpu == other.execution_environment_memory_gib_per_vcpu
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'capacity_provider_arn',
            'per_execution_environment_max_concurrency',
            'execution_environment_memory_gib_per_vcpu',
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
                self.capacity_provider_arn,
                self.per_execution_environment_max_concurrency,
                self.execution_environment_memory_gib_per_vcpu,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            capacity_provider_arn: __dataclass__init__fields__1__annotation,
            per_execution_environment_max_concurrency: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            execution_environment_memory_gib_per_vcpu: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'capacity_provider_arn', capacity_provider_arn)
            __dataclass__object_setattr(self, 'per_execution_environment_max_concurrency', per_execution_environment_max_concurrency)
            __dataclass__object_setattr(self, 'execution_environment_memory_gib_per_vcpu', execution_environment_memory_gib_per_vcpu)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"capacity_provider_arn={self.capacity_provider_arn!r}")
            parts.append(f"per_execution_environment_max_concurrency={self.per_execution_environment_max_concurrency!r}")
            parts.append(f"execution_environment_memory_gib_per_vcpu={self.execution_environment_memory_gib_per_vcpu!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d97a4a04ae99a52ec6599d55fe27d6a7d37722a5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('arn', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('code_size', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('signing_profile_version_arn', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('signing_job_arn', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,)"
            ", (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'Layer'),
    ),
)
def _process_dataclass__d97a4a04ae99a52ec6599d55fe27d6a7d37722a5():
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
                arn=self.arn,
                code_size=self.code_size,
                signing_profile_version_arn=self.signing_profile_version_arn,
                signing_job_arn=self.signing_job_arn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.arn == other.arn and
                self.code_size == other.code_size and
                self.signing_profile_version_arn == other.signing_profile_version_arn and
                self.signing_job_arn == other.signing_job_arn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'arn',
            'code_size',
            'signing_profile_version_arn',
            'signing_job_arn',
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
                self.code_size,
                self.signing_profile_version_arn,
                self.signing_job_arn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            code_size: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            signing_profile_version_arn: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            signing_job_arn: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'arn', arn)
            __dataclass__object_setattr(self, 'code_size', code_size)
            __dataclass__object_setattr(self, 'signing_profile_version_arn', signing_profile_version_arn)
            __dataclass__object_setattr(self, 'signing_job_arn', signing_job_arn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"arn={self.arn!r}")
            parts.append(f"code_size={self.code_size!r}")
            parts.append(f"signing_profile_version_arn={self.signing_profile_version_arn!r}")
            parts.append(f"signing_job_arn={self.signing_job_arn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='57b434f04a110c0f56b9b14774bc8d47b96337b5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('master_region', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('function_version', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('marker', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('max_items', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'ListFunctionsRequest'),
    ),
)
def _process_dataclass__57b434f04a110c0f56b9b14774bc8d47b96337b5():
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
                master_region=self.master_region,
                function_version=self.function_version,
                marker=self.marker,
                max_items=self.max_items,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.master_region == other.master_region and
                self.function_version == other.function_version and
                self.marker == other.marker and
                self.max_items == other.max_items
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'master_region',
            'function_version',
            'marker',
            'max_items',
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
                self.master_region,
                self.function_version,
                self.marker,
                self.max_items,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            master_region: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            function_version: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            marker: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            max_items: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'master_region', master_region)
            __dataclass__object_setattr(self, 'function_version', function_version)
            __dataclass__object_setattr(self, 'marker', marker)
            __dataclass__object_setattr(self, 'max_items', max_items)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"master_region={self.master_region!r}")
            parts.append(f"function_version={self.function_version!r}")
            parts.append(f"marker={self.marker!r}")
            parts.append(f"max_items={self.max_items!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d460cefec595794633ce8a866095fef4e10b65f8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('next_marker', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('functions', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'ListFunctionsResponse'),
    ),
)
def _process_dataclass__d460cefec595794633ce8a866095fef4e10b65f8():
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
                next_marker=self.next_marker,
                functions=self.functions,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.next_marker == other.next_marker and
                self.functions == other.functions
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'next_marker',
            'functions',
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
                self.next_marker,
                self.functions,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            next_marker: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            functions: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'next_marker', next_marker)
            __dataclass__object_setattr(self, 'functions', functions)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"next_marker={self.next_marker!r}")
            parts.append(f"functions={self.functions!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1284d077f0cc71c5ef31086aa737a90f55f03bc4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('log_format', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('application_log_level', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('system_log_level', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('log_group', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False"
            ",), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'LoggingConfig'),
    ),
)
def _process_dataclass__1284d077f0cc71c5ef31086aa737a90f55f03bc4():
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
                log_format=self.log_format,
                application_log_level=self.application_log_level,
                system_log_level=self.system_log_level,
                log_group=self.log_group,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.log_format == other.log_format and
                self.application_log_level == other.application_log_level and
                self.system_log_level == other.system_log_level and
                self.log_group == other.log_group
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'log_format',
            'application_log_level',
            'system_log_level',
            'log_group',
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
                self.log_format,
                self.application_log_level,
                self.system_log_level,
                self.log_group,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            log_format: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            application_log_level: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            system_log_level: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            log_group: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'log_format', log_format)
            __dataclass__object_setattr(self, 'application_log_level', application_log_level)
            __dataclass__object_setattr(self, 'system_log_level', system_log_level)
            __dataclass__object_setattr(self, 'log_group', log_group)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"log_format={self.log_format!r}")
            parts.append(f"application_log_level={self.application_log_level!r}")
            parts.append(f"system_log_level={self.system_log_level!r}")
            parts.append(f"log_group={self.log_group!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='23e98e87a932914026c76ba176d68ec63c4ba966',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('runtime_version_arn', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'RuntimeVersionConfig'),
    ),
)
def _process_dataclass__23e98e87a932914026c76ba176d68ec63c4ba966():
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
                runtime_version_arn=self.runtime_version_arn,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.runtime_version_arn == other.runtime_version_arn and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'runtime_version_arn',
            'error',
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
                self.runtime_version_arn,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            runtime_version_arn: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            error: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'runtime_version_arn', runtime_version_arn)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"runtime_version_arn={self.runtime_version_arn!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6bb397fe26a491668cc1c4924afbe075d292fa8e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('direct_s3_read', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'S3FilesConfig'),
    ),
)
def _process_dataclass__6bb397fe26a491668cc1c4924afbe075d292fa8e():
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
                direct_s3_read=self.direct_s3_read,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.direct_s3_read == other.direct_s3_read
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'direct_s3_read',
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
                self.direct_s3_read,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            direct_s3_read: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'direct_s3_read', direct_s3_read)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"direct_s3_read={self.direct_s3_read!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='081b1b4ea1dee5bd384fec1d5c425e66efbd721a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('apply_on', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('optimization_status', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fal"
            "se, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'SnapStartResponse'),
    ),
)
def _process_dataclass__081b1b4ea1dee5bd384fec1d5c425e66efbd721a():
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
                apply_on=self.apply_on,
                optimization_status=self.optimization_status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.apply_on == other.apply_on and
                self.optimization_status == other.optimization_status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'apply_on',
            'optimization_status',
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
                self.apply_on,
                self.optimization_status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            apply_on: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            optimization_status: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'apply_on', apply_on)
            __dataclass__object_setattr(self, 'optimization_status', optimization_status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"apply_on={self.apply_on!r}")
            parts.append(f"optimization_status={self.optimization_status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5809cdf88870b30d1634bf49347781fe4ac5cb0f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('tenant_isolation_mode', True, True, None, True, True, False, None), 'ins"
            "tance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'TenancyConfig'),
    ),
)
def _process_dataclass__5809cdf88870b30d1634bf49347781fe4ac5cb0f():
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
                tenant_isolation_mode=self.tenant_isolation_mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tenant_isolation_mode == other.tenant_isolation_mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'tenant_isolation_mode',
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
                self.tenant_isolation_mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tenant_isolation_mode: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tenant_isolation_mode', tenant_isolation_mode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tenant_isolation_mode={self.tenant_isolation_mode!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e62ab210800b41a05f7aa4da54e40b885ec77836',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('retry_after_seconds', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('message', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('reason', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'TooManyRequestsException'),
    ),
)
def _process_dataclass__e62ab210800b41a05f7aa4da54e40b885ec77836():
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
                retry_after_seconds=self.retry_after_seconds,
                type=self.type,
                message=self.message,
                reason=self.reason,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.retry_after_seconds == other.retry_after_seconds and
                self.type == other.type and
                self.message == other.message and
                self.reason == other.reason
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'retry_after_seconds',
            'type',
            'message',
            'reason',
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
                self.retry_after_seconds,
                self.type,
                self.message,
                self.reason,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            retry_after_seconds: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            type: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            message: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            reason: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'retry_after_seconds', retry_after_seconds)
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'reason', reason)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"retry_after_seconds={self.retry_after_seconds!r}")
            parts.append(f"type={self.type!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"reason={self.reason!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='feba9996b755c042f36346ae4721712b3989c1e7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('mode', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'TracingConfigResponse'),
    ),
)
def _process_dataclass__feba9996b755c042f36346ae4721712b3989c1e7():
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
                mode=self.mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mode == other.mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'mode',
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
                self.mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            mode: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mode', mode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mode={self.mode!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e5a4f44aa243482eb9fc002170d2a01bb260512e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('__shape__', True, True, None, True, None, False, None), 'class_var', 'missing"
            "', None, False, False, False), (('subnet_ids', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('security_group_ids', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('vpc_id', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('ipv6_allowed_for_dual_stack', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), ("
            "False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('ominfra.clouds.aws.models.services.lambda_', 'VpcConfigResponse'),
    ),
)
def _process_dataclass__e5a4f44aa243482eb9fc002170d2a01bb260512e():
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
                subnet_ids=self.subnet_ids,
                security_group_ids=self.security_group_ids,
                vpc_id=self.vpc_id,
                ipv6_allowed_for_dual_stack=self.ipv6_allowed_for_dual_stack,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.subnet_ids == other.subnet_ids and
                self.security_group_ids == other.security_group_ids and
                self.vpc_id == other.vpc_id and
                self.ipv6_allowed_for_dual_stack == other.ipv6_allowed_for_dual_stack
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__shape__',
            'subnet_ids',
            'security_group_ids',
            'vpc_id',
            'ipv6_allowed_for_dual_stack',
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
                self.subnet_ids,
                self.security_group_ids,
                self.vpc_id,
                self.ipv6_allowed_for_dual_stack,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            subnet_ids: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            security_group_ids: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            vpc_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            ipv6_allowed_for_dual_stack: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'subnet_ids', subnet_ids)
            __dataclass__object_setattr(self, 'security_group_ids', security_group_ids)
            __dataclass__object_setattr(self, 'vpc_id', vpc_id)
            __dataclass__object_setattr(self, 'ipv6_allowed_for_dual_stack', ipv6_allowed_for_dual_stack)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"subnet_ids={self.subnet_ids!r}")
            parts.append(f"security_group_ids={self.security_group_ids!r}")
            parts.append(f"vpc_id={self.vpc_id!r}")
            parts.append(f"ipv6_allowed_for_dual_stack={self.ipv6_allowed_for_dual_stack!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
