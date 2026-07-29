# @om-lite
import enum


##


class IoPipelineDriverState(enum.Enum):
    """
    Transport-facing lifecycle shared by I/O pipeline drivers.

    DRAINING means the transport terminal has accepted FinalOutput and is finishing output that preceded it. Explicit
    close remains abortive in RUNNING or DRAINING. CLOSED records successful graceful or explicit closure; FAILED is a
    terminal record of transport, pipeline-driving, or teardown failure.
    """

    NEW = 'new'
    RUNNING = 'running'
    DRAINING = 'draining'
    CLOSED = 'closed'
    FAILED = 'failed'
