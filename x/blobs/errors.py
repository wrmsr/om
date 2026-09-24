class BlobStoreError(Exception):
    pass


class InvalidBlobKeyError(BlobStoreError, ValueError):
    pass


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
    A conditional request lost a race inside the backend (S3's 409 ConditionalRequestConflict) and the backend's own
    bounded retries ran out. Nothing was written, so it is safe to retry.
    """


class BlobIndeterminateError(BlobStoreError):
    """
    A mutating request failed such that it is unknown whether it took effect (timeout, dropped connection, 5xx after
    the body was sent). Backends must never blindly retry a conditional write past this point: a retry of a write that
    did land fails its precondition against itself.
    """
