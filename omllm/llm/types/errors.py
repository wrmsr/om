import typing as ta


##


class Error(Exception):
    pass


class BackendError(Error):
    pass


class TransientBackendError(BackendError):
    """
    A backend failure which may not recur if the same request is simply retried: rate limiting, overload, a transient
    server fault, a dropped connection. Anything else a backend raises is taken to be a fault in the request itself, and
    is not retried.

    Carries the delay the backend asked for before a retry, if it gave one.
    """

    def __init__(self, *args: ta.Any, retry_after_s: float | None = None) -> None:
        super().__init__(*args)

        self.retry_after_s = retry_after_s
