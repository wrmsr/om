# @om-manifest
_CLI_MODULE = {'!omdev.cli.types.CliModule': {
    'name': 'diffs',
    'module': __name__,
}}


if __name__ == '__main__':
    from .cli import _main

    raise SystemExit(_main())
