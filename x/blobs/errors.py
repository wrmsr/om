import typing as ta


##


class BlobStoreError(Exception):
    pass


class InvalidBlobKeyError(BlobStoreError, ValueError):
    pass


class BlobStreamLengthError(BlobStoreError, ValueError):
    """A put_stream source yielded a different number of bytes than its declared length. Nothing was published."""


class UnsupportedBlobOperationError(BlobStoreError):
    pass


class BlobNotFoundError(BlobStoreError):
    pass


class BlobPreconditionFailedError(BlobStoreError):
    """Raised for every failed precondition, including IfMatch against a missing key - never BlobNotFoundError."""


class BlobAlreadyExistsError(BlobPreconditionFailedError):
    pass


class BlobNotModifiedError(BlobStoreError):
    pass


class BlobConflictError(BlobStoreError):
    """
    A conditional request lost a race inside the backend (S3's 409 ConditionalRequestConflict) and nothing retried it.
    Nothing was written, so it is safe to retry.
    """


class BlobTransportError(BlobStoreError):
    """
    A read, or a request known not to have been applied, failed at the transport level and nothing retried it. Retrying
    is always safe.
    """


class BlobIndeterminateError(BlobStoreError):
    """
    A mutating request failed such that it is unknown whether it took effect (timeout, dropped connection, 5xx after
    the body was sent). Backends must never blindly retry a conditional write past this point: a retry of a write that
    did land fails its precondition against itself.
    """


class BlobThrottledError(BlobIndeterminateError):
    """
    The backend asked us to slow down (S3's 503 SlowDown) and nothing retried the request. Treated as indeterminate by
    default: whether the request was applied is not assumed.
    """


class BlobDeleteManyError(BlobStoreError):
    """Raised by delete_many after attempting every key, carrying the per-key failures."""

    def __init__(self, errors: ta.Mapping[str, BlobStoreError]) -> None:
        super().__init__(errors)

        self._errors = errors

    @property
    def errors(self) -> ta.Mapping[str, BlobStoreError]:
        return self._errors
