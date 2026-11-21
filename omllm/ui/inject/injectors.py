import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang


##


class InjectorBox(dc.Box[inj.AsyncInjector], abstract=True):
    pass


def bind_injector_import(box_cls: type[InjectorBox], key: ta.Any) -> inj.Elemental:
    return inj.bind(key, to_async_fn=inj.target(i=box_cls)(lambda i: i.v[key]))


##


class UiInjector(InjectorBox, final=True):
    pass


class HostInjector(InjectorBox, final=True):
    pass


class AgentInjector(InjectorBox, final=True):
    pass


class AgentUiInjector(InjectorBox, final=True):
    pass


##


HostInjectorBindings = ta.NewType('HostInjectorBindings', ta.Sequence[inj.Elements])
AgentInjectorBindings = ta.NewType('AgentInjectorBindings', ta.Sequence[inj.Elements])
AgentUiInjectorBindings = ta.NewType('AgentUiInjectorBindings', ta.Sequence[inj.Elements])


@lang.cached_function
def host_injector_bindings_binder() -> inj.ItemsBinderHelper[inj.Elements]:
    return inj.items_binder_helper[inj.Elements](HostInjectorBindings)


@lang.cached_function
def agent_injector_bindings_binder() -> inj.ItemsBinderHelper[inj.Elements]:
    return inj.items_binder_helper[inj.Elements](AgentInjectorBindings)


@lang.cached_function
def agent_ui_injector_bindings_binder() -> inj.ItemsBinderHelper[inj.Elements]:
    return inj.items_binder_helper[inj.Elements](AgentUiInjectorBindings)


def bind_host_injector_bindings(*els: inj.Elemental) -> inj.Elemental:
    return host_injector_bindings_binder().bind_item(to_const=inj.as_elements(*els))


def bind_agent_injector_bindings(*els: inj.Elemental) -> inj.Elemental:
    return agent_injector_bindings_binder().bind_item(to_const=inj.as_elements(*els))


def bind_agent_ui_injector_bindings(*els: inj.Elemental) -> inj.Elemental:
    return agent_ui_injector_bindings_binder().bind_item(to_const=inj.as_elements(*els))
