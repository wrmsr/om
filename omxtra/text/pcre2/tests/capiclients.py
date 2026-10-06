"""
Builds and loads _capiclient.cc, the test consumer of the capi capsule.

It is deliberately not a cext: nothing under a tests directory is built or published with the package. So rather than
being imported it is compiled on demand, somewhere temporary, and loaded from there by path. Run as a module this loads
an already built one into a fresh process, which is how its not depending on _pcre2 having been imported first is
tested.
"""
import importlib.machinery
import importlib.util
import os.path
import sys

from omcore import lang


with lang.auto_proxy_import(globals()):
    from omdev.cexts import _distutils as du
    from omdev.cexts import build as cb


##


CAPICLIENT_NAME = f'{__package__}._capiclient'
CAPICLIENT_SRC_FILE = os.path.join(os.path.dirname(__file__), '_capiclient.cc')

BINDING_NAME = f'{__package__.rpartition(".")[0]}._pcre2'


def build_capiclient(build_dir):
    """Compiles the client with the same machinery, and so the same flags, as cexts proper. Returns the built file."""

    ext = du.Extension(
        CAPICLIENT_NAME,
        sources=[CAPICLIENT_SRC_FILE],
        extra_compile_args=[f'-std={cb.CPP_STD}'],
        extra_link_args=(['-Wl,-no_fixup_chains'] if sys.platform == 'darwin' else []),
    )

    cmd = du.BuildExt(du.BuildExt.Options(
        build_lib=os.path.join(build_dir, 'lib'),
        build_temp=os.path.join(build_dir, 'temp'),
    ))
    cmd.build_extension(ext)

    return cmd.get_ext_fullpath(ext.name)


def load_capiclient(so_file):
    """Loads a built client by path, without making it importable: it is neither on sys.path nor in sys.modules."""

    loader = importlib.machinery.ExtensionFileLoader(CAPICLIENT_NAME, so_file)
    spec = importlib.util.spec_from_file_location(CAPICLIENT_NAME, so_file, loader=loader)
    if spec is None:
        raise ImportError(f'cannot load {CAPICLIENT_NAME} from {so_file}')
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


##


def _main() -> None:
    [so_file] = sys.argv[1:]

    if BINDING_NAME in sys.modules:
        raise RuntimeError(f'{BINDING_NAME} was imported before the client was loaded')

    load_capiclient(so_file)

    if BINDING_NAME not in sys.modules:
        raise RuntimeError(f'{BINDING_NAME} was not imported by loading the client')


if __name__ == '__main__':
    _main()
