from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True, kw_only=True)
class LsmOptions:
    memtable_max_bytes: int = 4 * 1024 * 1024
    block_size: int = 4 * 1024
    sst_target_size: int = 64 * 1024 * 1024
    l0_compaction_trigger: int = 4
    prefetch_bytes: int = 64 * 1024
    commit_conflict_retries: int = 3
    open_retries: int = 8
    block_cache_size: int = 16
