from omcore.testing.pytest import plugins as ptp


def pytest_addhooks(pluginmanager):
    # Skips what needs the bpe extension where it has not been built, or has been without the one it gets PCRE2 from.
    ptp.depskip.fn_register(
        pluginmanager,
        lambda ctx: (
            ctx.file_name.startswith('/'.join([*__package__.split('.'), ''])) and
            ctx.import_name in (
                f'{__package__}.bpe._bpe',
                'omcore.text.pcre2._pcre2',
            )
        ),
    )
