"""The main entry point used for CLI."""
import pathlib
import sys
import typing as ta

from ._cli import Options
from ._cli import get_options
from ._cli import parse_packages
from ._detect_env import detect_active_interpreter
from ._detect_env import find_active_interpreter
from ._discovery import InterpreterQueryError
from ._discovery import get_installed_distributions
from ._from_index import FromIndexInputError
from ._from_index import FromIndexUnavailableError
from ._from_index import resolve_from_index
from ._from_lock import FromLockError
from ._from_lock import load_lock
from ._models import PackageDAG
from ._models.dag import IncludeExcludeOverlapError
from ._models.dag import IncludePatternNotFoundError
from ._render import render
from ._validate import validate
from ._warning import WarningPrinter
from ._warning import WarningType
from ._warning import get_warning_printer


##


_OVERLAP_MESSAGE = 'Cannot have --packages and --exclude contain the same entries'


class _FilterError(Exception):
    """Raised by build_tree when the include/exclude filter cannot be satisfied."""

    def __init__(self, message: str, *, is_fatal: bool) -> None:
        super().__init__(message)
        self.is_fatal = is_fatal


def main(args: ta.Sequence[str] | None = None) -> int | None:
    """CLI - The main function called as entry point."""

    options = get_options(args)

    # Warnings are only enabled when using text output.
    if not _is_text_output(options):
        options.warn = 'silence'
    warning_printer = get_warning_printer()
    warning_printer.warning_type = WarningType.from_str(options.warn)

    try:
        tree = build_tree(options, log_resolved=True)
    except InterpreterQueryError as e:
        print(f'Failed to query custom interpreter: {e}', file=sys.stderr)  # noqa: T201
        return 1
    except (FromIndexUnavailableError, FromIndexInputError, FromLockError) as e:
        print(str(e), file=sys.stderr)  # noqa: T201
        return 1
    except _FilterError as e:
        if e.is_fatal:
            print(str(e), file=sys.stderr)  # noqa: T201
            return 1
        if warning_printer.should_warn():
            warning_printer.print_single_line(str(e))
        return _determine_return_code(warning_printer)

    render(options, tree)

    return _determine_return_code(warning_printer)


def build_tree(options: Options, *, log_resolved: bool = False) -> PackageDAG:
    """
    Discover packages and build the (optionally reversed/filtered) dependency tree.

    Shared by the CLI and the programmatic :func:`pipdeptree.render` API.

    :raises InterpreterQueryError: if querying a custom interpreter failed
    :raises FromIndexUnavailableError: if from-index is used but the optional nab resolver is missing
    :raises FromIndexInputError: if a from-index source is missing or a requirements file uses an unsupported directive
    :raises FromLockError: if a from-lock file is missing or is not a valid PEP 751 lock
    :raises _FilterError: if the include/exclude filter cannot be satisfied
    """

    if options.command == 'from-index':
        # from-index resolves requirements by querying the package index instead of inspecting an installed
        # environment, so interpreter resolution is skipped entirely.
        pkgs = resolve_from_index(
            requirements=options.requirement,
            requirement_files=options.requirements or [],
            pyproject_files=options.pyproject or [],
            index_url=options.index_url,
            extra_index_url=options.extra_index_url,
        )
    elif options.command == 'from-lock':
        # A PEP 751 lock is already resolved, so it is read straight off disk -- no interpreter, network, or index.
        pkgs = load_lock(pathlib.Path(options.lock))  # ty: ignore[invalid-argument-type]
    else:
        options.python = _resolve_python(options.python, log_resolved=log_resolved)
        pkgs = get_installed_distributions(
            interpreter=options.python,
            supplied_paths=options.path or None,
            local_only=options.local_only,
            user_only=options.user_only,
        )

    include, requested_extras = parse_packages(options.packages)
    tree = PackageDAG.from_pkgs(pkgs, extras=options.extras, requested_extras=requested_extras)

    validate(tree)

    if options.context.active:
        options.context.full_tree = tree

    # Reverse the tree (if applicable) before filtering, thus ensuring, that the filter will be applied on ReverseTree
    if options.reverse:
        tree = tree.reverse()

    include = include or None
    exclude = set(options.exclude.split(',')) if options.exclude else None

    if include is not None or exclude is not None:
        try:
            tree = tree.filter_nodes(include, exclude, exclude_deps=options.exclude_dependencies)
        except IncludeExcludeOverlapError as e:
            raise _FilterError(_OVERLAP_MESSAGE, is_fatal=True) from e
        except IncludePatternNotFoundError as e:
            raise _FilterError(str(e), is_fatal=False) from e

    return tree


def _resolve_python(python: str | None, *, log_resolved: bool = False) -> str:
    # Default (None): auto-detect the active virtual environment, silently falling back to the running interpreter so
    # users outside a virtual environment keep the historical behavior. "auto" stays strict and fails if none is found.
    # log_resolved keeps the resolved-path note CLI-only so the programmatic API stays quiet in notebooks.
    if python is None:
        if resolved_path := find_active_interpreter():
            if log_resolved:
                print(f'(resolved python: {resolved_path})', file=sys.stderr)  # noqa: T201
            return resolved_path
        return sys.executable
    if python == 'auto':
        resolved_path = detect_active_interpreter()
        if log_resolved:
            print(f'(resolved python: {resolved_path})', file=sys.stderr)  # noqa: T201
        return resolved_path
    return python


def _is_text_output(options: Options) -> bool:
    if any((options.json, options.json_tree, options.graphviz_format, options.mermaid)):
        return False
    return options.output_format in {'freeze', 'rich', 'text'}


def _determine_return_code(warning_printer: WarningPrinter) -> int:
    return 1 if warning_printer.has_warned_with_failure() else 0


if __name__ == '__main__':
    sys.exit(main())
