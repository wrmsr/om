import types

from .. import completer
from .. import mangle


##


def test_completion():
    completer_ = completer.Completer(
        {
            'hy': None,
            'simple_pythonic_var_name': None,
            mangle('complicated->@#%!name'): types.SimpleNamespace(
                **{mangle('another$^@#$name'): None},
            ),
            'hyx_XaXaXaX': types.SimpleNamespace(hyx_XbXbX=None),
        },
    )
    assert completer_.complete('hy.', 0) is not None
    for test in [
        ('simple_pyth', 'simple-pythonic-var-name'),
        ('compli', 'complicated->@#%!name'),
        ('complicated->@#', 'complicated->@#%!name'),
        ('complicated->@#%!name', 'complicated->@#%!name'),
        ('complicated->@#%!name.ano', 'complicated->@#%!name.another$^@#$name'),
        ('complicated->@#%!name.another$^@', 'complicated->@#%!name.another$^@#$name'),
        ('hyx_XaX', 'hyx_XaXaXaX'),
        ('hyx_XaXaXaX.hyx_Xb', 'hyx_XaXaXaX.hyx_XbXbX'),
    ]:
        assert completer_.complete(test[0], 0) == test[1]
