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
    installer_sha1='b626e24c115ef7a8b3dbddf1132ed121c045b4fa',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('poll_interval', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('heartbeat_interval', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('poll_limit', True, True, None, True, False, False, None),"
            " 'instance', 'value', None, False, False, False), (('flush_batch_size', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('connect_timeout', True, True, None, True, F"
            "alse, False, None), 'instance', 'value', None, False, False, False), (('reconnect_backoff', True, True, No"
            "ne, True, False, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,),"
            " (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.loop', 'LoopConfig'),
    ),
)
def _process_dataclass__b626e24c115ef7a8b3dbddf1132ed121c045b4fa():
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
                poll_interval=self.poll_interval,
                heartbeat_interval=self.heartbeat_interval,
                poll_limit=self.poll_limit,
                flush_batch_size=self.flush_batch_size,
                connect_timeout=self.connect_timeout,
                reconnect_backoff=self.reconnect_backoff,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.poll_interval == other.poll_interval and
                self.heartbeat_interval == other.heartbeat_interval and
                self.poll_limit == other.poll_limit and
                self.flush_batch_size == other.flush_batch_size and
                self.connect_timeout == other.connect_timeout and
                self.reconnect_backoff == other.reconnect_backoff
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'poll_interval',
            'heartbeat_interval',
            'poll_limit',
            'flush_batch_size',
            'connect_timeout',
            'reconnect_backoff',
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
                self.poll_interval,
                self.heartbeat_interval,
                self.poll_limit,
                self.flush_batch_size,
                self.connect_timeout,
                self.reconnect_backoff,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            poll_interval: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            heartbeat_interval: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            poll_limit: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            flush_batch_size: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            connect_timeout: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            reconnect_backoff: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'poll_interval', poll_interval)
            __dataclass__object_setattr(self, 'heartbeat_interval', heartbeat_interval)
            __dataclass__object_setattr(self, 'poll_limit', poll_limit)
            __dataclass__object_setattr(self, 'flush_batch_size', flush_batch_size)
            __dataclass__object_setattr(self, 'connect_timeout', connect_timeout)
            __dataclass__object_setattr(self, 'reconnect_backoff', reconnect_backoff)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"poll_interval={self.poll_interval!r}")
            parts.append(f"heartbeat_interval={self.heartbeat_interval!r}")
            parts.append(f"poll_limit={self.poll_limit!r}")
            parts.append(f"flush_batch_size={self.flush_batch_size!r}")
            parts.append(f"connect_timeout={self.connect_timeout!r}")
            parts.append(f"reconnect_backoff={self.reconnect_backoff!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f17300e1a4d4ed0395865dba5be3f53a5db3b0a0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('messages', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('seqs_after', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.outbox', 'Batch'),
    ),
)
def _process_dataclass__f17300e1a4d4ed0395865dba5be3f53a5db3b0a0():
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
                messages=self.messages,
                seqs_after=self.seqs_after,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.messages == other.messages and
                self.seqs_after == other.seqs_after
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'messages',
            'seqs_after',
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
                self.messages,
                self.seqs_after,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            messages: __dataclass__init__fields__0__annotation,
            seqs_after: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'messages', messages)
            __dataclass__object_setattr(self, 'seqs_after', seqs_after)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"messages={self.messages!r}")
            parts.append(f"seqs_after={self.seqs_after!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='22ea54f147533a13d35f45f930f005df94efb1c8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('upsert_worker', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('select_worker_seqs', True, True, None, True, False, False, None), '"
            "instance', 'missing', None, False, False, False), (('update_heartbeat', True, True, None, True, False, Fal"
            "se, None), 'instance', 'missing', None, False, False, False), (('select_workers', True, True, None, True, "
            "False, False, None), 'instance', 'missing', None, False, False, False), (('insert_message', True, True, No"
            "ne, True, False, False, None), 'instance', 'missing', None, False, False, False), (('update_seqs', True, T"
            "rue, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('select_message"
            "s', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('del"
            "ete_message', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, Fals"
            "e)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.statements', 'Statements'),
    ),
)
def _process_dataclass__22ea54f147533a13d35f45f930f005df94efb1c8():
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
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                upsert_worker=self.upsert_worker,
                select_worker_seqs=self.select_worker_seqs,
                update_heartbeat=self.update_heartbeat,
                select_workers=self.select_workers,
                insert_message=self.insert_message,
                update_seqs=self.update_seqs,
                select_messages=self.select_messages,
                delete_message=self.delete_message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.upsert_worker == other.upsert_worker and
                self.select_worker_seqs == other.select_worker_seqs and
                self.update_heartbeat == other.update_heartbeat and
                self.select_workers == other.select_workers and
                self.insert_message == other.insert_message and
                self.update_seqs == other.update_seqs and
                self.select_messages == other.select_messages and
                self.delete_message == other.delete_message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'upsert_worker',
            'select_worker_seqs',
            'update_heartbeat',
            'select_workers',
            'insert_message',
            'update_seqs',
            'select_messages',
            'delete_message',
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
                self.upsert_worker,
                self.select_worker_seqs,
                self.update_heartbeat,
                self.select_workers,
                self.insert_message,
                self.update_seqs,
                self.select_messages,
                self.delete_message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            upsert_worker: __dataclass__init__fields__0__annotation,
            select_worker_seqs: __dataclass__init__fields__1__annotation,
            update_heartbeat: __dataclass__init__fields__2__annotation,
            select_workers: __dataclass__init__fields__3__annotation,
            insert_message: __dataclass__init__fields__4__annotation,
            update_seqs: __dataclass__init__fields__5__annotation,
            select_messages: __dataclass__init__fields__6__annotation,
            delete_message: __dataclass__init__fields__7__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'upsert_worker', upsert_worker)
            __dataclass__object_setattr(self, 'select_worker_seqs', select_worker_seqs)
            __dataclass__object_setattr(self, 'update_heartbeat', update_heartbeat)
            __dataclass__object_setattr(self, 'select_workers', select_workers)
            __dataclass__object_setattr(self, 'insert_message', insert_message)
            __dataclass__object_setattr(self, 'update_seqs', update_seqs)
            __dataclass__object_setattr(self, 'select_messages', select_messages)
            __dataclass__object_setattr(self, 'delete_message', delete_message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"upsert_worker={self.upsert_worker!r}")
            parts.append(f"select_worker_seqs={self.select_worker_seqs!r}")
            parts.append(f"update_heartbeat={self.update_heartbeat!r}")
            parts.append(f"select_workers={self.select_workers!r}")
            parts.append(f"insert_message={self.insert_message!r}")
            parts.append(f"update_seqs={self.update_seqs!r}")
            parts.append(f"select_messages={self.select_messages!r}")
            parts.append(f"delete_message={self.delete_message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c1ebe4bfca6c3ed428477e214dda57beb525f5ed',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('dst_id', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('src_id', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('seq', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('payload', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('created_at', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.types', 'Message'),
    ),
)
def _process_dataclass__c1ebe4bfca6c3ed428477e214dda57beb525f5ed():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                dst_id=self.dst_id,
                src_id=self.src_id,
                seq=self.seq,
                payload=self.payload,
                created_at=self.created_at,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dst_id == other.dst_id and
                self.src_id == other.src_id and
                self.seq == other.seq and
                self.payload == other.payload and
                self.created_at == other.created_at
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'dst_id',
            'src_id',
            'seq',
            'payload',
            'created_at',
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
                self.dst_id,
                self.src_id,
                self.seq,
                self.payload,
                self.created_at,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            dst_id: __dataclass__init__fields__0__annotation,
            src_id: __dataclass__init__fields__1__annotation,
            seq: __dataclass__init__fields__2__annotation,
            payload: __dataclass__init__fields__3__annotation,
            created_at: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'dst_id', dst_id)
            __dataclass__object_setattr(self, 'src_id', src_id)
            __dataclass__object_setattr(self, 'seq', seq)
            __dataclass__object_setattr(self, 'payload', payload)
            __dataclass__object_setattr(self, 'created_at', created_at)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dst_id={self.dst_id!r}")
            parts.append(f"src_id={self.src_id!r}")
            parts.append(f"seq={self.seq!r}")
            parts.append(f"payload={self.payload!r}")
            parts.append(f"created_at={self.created_at!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a1f79607a72b5ffb5534b4f56843d722eab584b4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('dst_id', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('payload', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.types', 'OutgoingMessage'),
    ),
)
def _process_dataclass__a1f79607a72b5ffb5534b4f56843d722eab584b4():
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
                dst_id=self.dst_id,
                payload=self.payload,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dst_id == other.dst_id and
                self.payload == other.payload
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'dst_id',
            'payload',
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
                self.dst_id,
                self.payload,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            dst_id: __dataclass__init__fields__0__annotation,
            payload: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'dst_id', dst_id)
            __dataclass__object_setattr(self, 'payload', payload)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dst_id={self.dst_id!r}")
            parts.append(f"payload={self.payload!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3a113d0405f84524c7e3096bfcf9f6f9345b8460',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('worker_id', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('started_at', True, True, None, True, False, False, None), 'instance', '"
            "missing', None, False, False, False), (('heartbeat_at', True, True, None, True, False, False, None), 'inst"
            "ance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, F"
            "alse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.messagebus.types', 'WorkerInfo'),
    ),
)
def _process_dataclass__3a113d0405f84524c7e3096bfcf9f6f9345b8460():
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
                worker_id=self.worker_id,
                name=self.name,
                started_at=self.started_at,
                heartbeat_at=self.heartbeat_at,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.worker_id == other.worker_id and
                self.name == other.name and
                self.started_at == other.started_at and
                self.heartbeat_at == other.heartbeat_at
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'worker_id',
            'name',
            'started_at',
            'heartbeat_at',
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
                self.worker_id,
                self.name,
                self.started_at,
                self.heartbeat_at,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            worker_id: __dataclass__init__fields__0__annotation,
            name: __dataclass__init__fields__1__annotation,
            started_at: __dataclass__init__fields__2__annotation,
            heartbeat_at: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'worker_id', worker_id)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'started_at', started_at)
            __dataclass__object_setattr(self, 'heartbeat_at', heartbeat_at)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"worker_id={self.worker_id!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"started_at={self.started_at!r}")
            parts.append(f"heartbeat_at={self.heartbeat_at!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
