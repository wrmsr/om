"""The `hy`, `hyc`, and `hy2py` commands. These are process entrypoints, and so install the global runtime."""
from .hy2py import hy2py_main  # noqa
from .hyc import hyc_main  # noqa
from .main import hy_main  # noqa
