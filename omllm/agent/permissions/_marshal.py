from omcore import marshal as msh

from .fs import FsPermissionTarget  # noqa
from .fs import GlobFsPermissionMatcher  # noqa
from .shell import ShellPermissionMatcher  # noqa
from .types import PermissionMatcher
from .types import PermissionTarget
from .url import RegexUrlPermissionMatcher  # noqa
from .url import UrlPermissionTarget  # noqa


##


@msh.register_global_lazy_init
def _install_standard_marshaling(cfgs: msh.ConfigRegistry) -> None:
    for cls in [
        PermissionMatcher,
        PermissionTarget,
    ]:
        msh.install_standard_factories(
            cfgs,
            *msh.standard_polymorphism_factories(
                msh.polymorphism_from_subclasses(
                    cls,
                    strip_suffix=True,
                    naming=msh.Naming.SNAKE,
                ),
            ),
        )
