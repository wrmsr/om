class ReplicationError(Exception):
    pass


class ReplicationSchemaError(ReplicationError):
    pass


class ReplicationInstallError(ReplicationError):
    pass


class ReplicationConflictError(ReplicationError):
    """
    A target holds a version above the source's, or a different origin, for the same key. Under the single-writer rule
    that cannot happen, so it means either a violated writer rule or a key collision; the link halts rather than guess.
    """
