from ... import lang as _lang


with _lang.auto_proxy_init(
        globals(),
        update_exports=True,
):
    ##

    from .handlers import (  # noqa
        FdioHandler as Handler,

        SocketFdioHandler as SocketHandler,

        ServerSocketFdioHandler as ServerSocketHandler,
    )

    from .kqueue import (  # noqa
        KqueueFdioPoller as KqueuePoller,
    )

    from .manager import (  # noqa
        FdioManager as Manager,
    )

    from .pollers import (  # noqa
        FdioPoller as Poller,

        SelectFdioPoller as SelectPoller,

        PollFdioPoller as PollPoller,
    )
