import typing as ta

from ..errors import InterfaceError


##


def make_startup_params(
        *,
        user: str | bytes,
        database: str | bytes | None = None,
        application_name: str | bytes | None = None,
        replication: str | bytes | None = None,
        startup_params: ta.Mapping[str, str | bytes] | None = None,
) -> dict[str, bytes]:
    """Builds the parameter mapping of a StartupMessage from the usual connection arguments."""

    if user is None:
        raise InterfaceError("The 'user' connection parameter cannot be None")

    init_params: dict[str, ta.Any] = {
        'user': user,
        'database': database,
        'application_name': application_name,
        'replication': replication,
    }
    start_params = {} if startup_params is None else startup_params
    common_params = init_params.keys() & start_params.keys()

    if len(common_params) > 0:
        raise InterfaceError(
            f"The parameters '{common_params}' can't appear in startup_params, they "
            f"must be set using keyword arguments.",
        )
    init_params.update(start_params)

    startup: dict[str, bytes] = {}
    for k, v in init_params.items():
        if isinstance(v, str):
            startup[k] = v.encode('utf8')
        elif v is None:
            continue
        elif isinstance(v, (bytes, bytearray)):
            startup[k] = bytes(v)
        else:
            raise InterfaceError(f"The parameter {k} can't be of type {type(v)}.")

    return startup
