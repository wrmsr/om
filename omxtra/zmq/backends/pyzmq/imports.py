from omcore import lang

from ...api.errors import BackendUnavailableError


##


def check_pyzmq_available() -> None:
    if not lang.can_import('zmq'):
        raise BackendUnavailableError(
            'The pyzmq backend requires the optional pyzmq package, available as the omxtra[zmq] extra.',
        )
