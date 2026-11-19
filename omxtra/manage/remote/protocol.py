# ruff: noqa: UP006 UP007 UP045
"""
The remote execution protocol, over `omcore.rpc`.

The host first calls `manage.bootstrap` with the `MainBootstrap`, from which the remote builds its injector - and with
it the marshaler which knows every command type - and sets up its process (pgid, deathsig, timebomb, log forwarding).
Then each `manage.execute` carries one polymorphic `Command` and returns its `CommandOutputOrExceptionData`. The remote
forwards its log records to the host as `manage.log` notifications, which the host applies inline, in order.
"""


##


REMOTE_EXECUTION_BOOTSTRAP_METHOD = 'manage.bootstrap'
REMOTE_EXECUTION_EXECUTE_METHOD = 'manage.execute'

REMOTE_EXECUTION_LOG_METHOD = 'manage.log'
