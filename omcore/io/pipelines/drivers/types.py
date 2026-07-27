# @om-lite
import enum


##


class IoPipelineDriverState(enum.Enum):
    """Transport-facing lifecycle shared by I/O pipeline drivers."""

    NEW = 'new'
    RUNNING = 'running'
    DRAINING = 'draining'
    CLOSED = 'closed'
    FAILED = 'failed'
