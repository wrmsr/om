# @om-lite
# ruff: noqa: UP006 UP007 UP045
import typing as ta

from omcore.lite.inject import InjectorBindingOrBindings
from omcore.lite.inject import InjectorBindings
from omcore.lite.inject import inj

from .cgroups import SystevisorCgroupFs
from .cgroups import SystevisorCgroupManager
from .cgroups import SystevisorSystemCgroupFs
from .namespaces import SystevisorLinuxNamespaceBackend
from .namespaces import SystevisorNamespaceBackend
from .namespaces import SystevisorNamespaceChildModifier
from .runtime import SystevisorResourceObserver
from .sampling import SystevisorProcessResourceSampler
from .sampling import SystevisorSystemProcessResourceSampler
from .sockets import SystevisorInheritedSocketChildModifier
from .sockets import SystevisorInheritedSocketRegistry


def _systevisor_resources_inject_provide_socket_registry() -> SystevisorInheritedSocketRegistry:
    return SystevisorInheritedSocketRegistry()


def systevisor_bind_resources() -> InjectorBindings:
    bindings: ta.List[InjectorBindingOrBindings] = [
        inj.bind(SystevisorSystemCgroupFs, singleton=True),
        inj.bind(SystevisorCgroupFs, to_key=SystevisorSystemCgroupFs),
        inj.bind(SystevisorCgroupManager, singleton=True),
        inj.bind(SystevisorLinuxNamespaceBackend, singleton=True),
        inj.bind(SystevisorNamespaceBackend, to_key=SystevisorLinuxNamespaceBackend),
        inj.bind(SystevisorNamespaceChildModifier, singleton=True),
        inj.bind(_systevisor_resources_inject_provide_socket_registry, singleton=True),
        inj.bind(SystevisorInheritedSocketChildModifier, singleton=True),
        inj.bind(SystevisorSystemProcessResourceSampler, singleton=True),
        inj.bind(SystevisorProcessResourceSampler, to_key=SystevisorSystemProcessResourceSampler),
        inj.bind(SystevisorResourceObserver, singleton=True),
    ]
    return inj.as_bindings(*bindings)
