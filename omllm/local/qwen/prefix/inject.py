from omcore import dataclasses as dc
from omcore import inject as inj

from ..decode.stores import NullStateStore
from ..decode.stores import StateStore
from ..ops.base import Ops
from .cache import PrefixCache
from .store import PrefixStateStore


##


@dc.dataclass(frozen=True)
class PrefixConfig:
    enabled: bool = True
    device_mib: int = 4096
    host_mib: int = 8192


def _cache(ops: Ops, config: PrefixConfig) -> PrefixCache:
    return PrefixCache(ops, config.device_mib << 20, config.host_mib << 20)


def bind_prefix(config: PrefixConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(PrefixConfig, to_const=config),
    ]

    if config.enabled:
        lst.extend([
            inj.bind(PrefixCache, to_fn=_cache, singleton=True),
            inj.bind(PrefixStateStore, singleton=True),
            inj.bind(StateStore, to_key=PrefixStateStore),
        ])

    else:
        lst.extend([
            inj.bind(NullStateStore, singleton=True),
            inj.bind(StateStore, to_key=NullStateStore),
        ])

    return inj.as_elements(*lst)
