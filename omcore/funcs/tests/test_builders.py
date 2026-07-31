import os.path
import sys
import tempfile
import uuid

from ..builders import DebugFnBuilder
from ..builders import build_fn


def test_build_fn():
    ns = {'offset': 3}
    fn = build_fn(
        'add_offset',
        'def add_offset(value):\n'
        '    return value + offset\n',
        ns,
    )

    assert fn(4) == 7
    assert ns == {'offset': 3}


def test_debug_fn_builder_sys_path_ownership():
    mod_name_prefix = f'_test_debug_fn_builder_{uuid.uuid4().hex}_'

    with tempfile.TemporaryDirectory() as src_dir:
        builder = DebugFnBuilder(
            mod_name_prefix=mod_name_prefix,
            src_dir=src_dir,
        )
        try:
            fn = builder.build_fn(
                'add_offset',
                'def add_offset(value):\n'
                '    return value + offset\n',
                {'offset': 3},
            )

            assert fn(4) == 7
            assert os.path.dirname(fn.__code__.co_filename) == src_dir
            assert src_dir in sys.path

            builder.uninstall_sys_path()
            assert src_dir not in sys.path

            sys.path.append(src_dir)
            builder.uninstall_sys_path()
            assert src_dir in sys.path

        finally:
            while True:
                try:
                    sys.path.remove(src_dir)
                except ValueError:
                    break

            for mod_name in list(sys.modules):
                if mod_name.startswith(mod_name_prefix):
                    del sys.modules[mod_name]
