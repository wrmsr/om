from ...testing.pytest import plugins as ptp


def pytest_addhooks(pluginmanager):
    ptp.depskip.fn_register(
        pluginmanager,
        lambda ctx: (
            ctx.file_name.startswith('/'.join([*__package__.split('.'), ''])) and
            ctx.import_name == f'{__package__}._pcre2'
        ),
    )
