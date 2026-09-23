# fmt: off
# ruff: noqa: I001
from .... import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from .... import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from . import adapters  # noqa

    from . import backend  # noqa

    from . import connecting  # noqa

    from . import dialect  # noqa

    from . import inspect  # noqa

    from . import tabledefs  # noqa
    from . import tabledefs as td  # noqa

    from . import values  # noqa
