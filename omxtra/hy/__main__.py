# @om-manifest omdev.cli.CliModule(['llm'], __name__)


# Running hy as a module (e.g. `python -m <package>`) is equivalent to running the main `hy` command.
if __name__ == '__main__':
    import sys

    from .cli import hy_main

    sys.exit(hy_main())
