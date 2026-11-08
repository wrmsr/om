from ...cli import CliModule


# @om-manifest
_CLI_MODULE = CliModule(['curl'], __name__)


if __name__ == '__main__':
    from .cli import main

    raise SystemExit(main())
