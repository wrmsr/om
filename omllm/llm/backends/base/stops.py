from omcore.logs import all as logs

from ...types.messages import StopReason


log = logs.get_module_logger(globals())


##


def unknown_stop_reason(backend: str, raw: str) -> StopReason:
    """
    What a backend's stop reason translation returns for a value it does not know: noted here, and carried through as
    'other', so that the run is decided by what the message holds - as it is for a plain stop - rather than failed over
    a word the provider added after this was written.
    """

    log.warning('Unknown %s stop reason: %r', backend, raw)

    return 'other'
