from __future__ import annotations

import dataclasses as dc

from collections.abc import Mapping
from collections.abc import Sequence


class RgArgumentError(ValueError):
    pass


@dc.dataclass(frozen=True)
class ParsedRgArguments:
    # Entries are ("--long" or "-x", optional_value).
    options: tuple[tuple[str, str | None], ...]

    # All argv elements that ripgrep would treat as positionals.
    positionals: tuple[str, ...]

    # Whether an unconsumed standalone "--" occurred.
    saw_end_of_options: bool


# Reject these whenever they are parsed as options. In particular, do not
# merely inspect ripgrep's eventual/final configuration: reject the attempt
# even if a later option would turn the behavior off again.
_DENIED_LONG_OPTIONS: Mapping[str, str] = {
    "pre": (
        "--pre is disabled because it executes a preprocessor for input files"
    ),
    "hostname-bin": (
        "--hostname-bin is disabled because it executes a program"
    ),
    "search-zip": (
        "--search-zip is disabled because it launches external decompressors"
    ),
}

_DENIED_SHORT_OPTIONS: Mapping[str, str] = {
    "z": (
        "-z/--search-zip is disabled because it launches external "
        "decompressors"
    ),
}


def parse_allowed_rg_arguments(
        argv: Sequence[str],
        *,
        # Keys do not include leading dashes.
        # True means that the option takes exactly one value.
        allowed_long: Mapping[str, bool],
        allowed_short: Mapping[str, bool],
) -> ParsedRgArguments:
    """
    Parse argv using the ripgrep 15.2.0 / lexopt 0.3.2 option-binding rules.

    This handles lexical binding only. It deliberately rejects every option
    not present in the caller's allowlist.

    It does not validate option-specific values such as integer ranges,
    encoding names or glob complexity. Those should be checked separately.
    """
    options: list[tuple[str, str | None]] = []
    positionals: list[str] = []

    parsing_options = True
    saw_end_of_options = False
    i = 0

    while i < len(argv):
        arg = argv[i]

        if not isinstance(arg, str):
            raise RgArgumentError(
                f"ripgrep argument {i} is not a string: {arg!r}"
            )
        if "\0" in arg:
            raise RgArgumentError(
                f"ripgrep argument {i} contains a NUL byte"
            )

        if not parsing_options:
            positionals.append(arg)
            i += 1
            continue

        # This is an option terminator only when it wasn't consumed as the
        # value of a preceding option.
        if arg == "--":
            parsing_options = False
            saw_end_of_options = True
            i += 1
            continue

        if arg.startswith("--"):
            body = arg[2:]
            name, has_equals, attached_value = body.partition("=")

            denied_reason = _DENIED_LONG_OPTIONS.get(name)
            if denied_reason is not None:
                raise RgArgumentError(denied_reason)

            takes_value = allowed_long.get(name)
            if takes_value is None:
                raise RgArgumentError(
                    f"unsupported ripgrep option: --{name}"
                )

            spelling = f"--{name}"
            if takes_value:
                if has_equals:
                    value = attached_value
                else:
                    i += 1
                    if i >= len(argv):
                        raise RgArgumentError(
                            f"missing value for ripgrep option {spelling}"
                        )
                    value = argv[i]
                    if "\0" in value:
                        raise RgArgumentError(
                            f"value for {spelling} contains a NUL byte"
                        )

                options.append((spelling, value))
            else:
                if has_equals:
                    raise RgArgumentError(
                        f"ripgrep option {spelling} does not take a value"
                    )
                options.append((spelling, None))

            i += 1
            continue

        if arg.startswith("-") and arg != "-":
            # lexopt parses this as a chain of short options. Once a
            # value-taking option is encountered, the remainder becomes
            # that option's value and is no longer parsed as options.
            cluster = arg[1:]
            j = 0

            while j < len(cluster):
                name = cluster[j]

                # ripgrep only recognizes ASCII short option names.
                if not name.isascii():
                    raise RgArgumentError(
                        f"unsupported non-ASCII ripgrep option: -{name}"
                    )

                denied_reason = _DENIED_SHORT_OPTIONS.get(name)
                if denied_reason is not None:
                    raise RgArgumentError(denied_reason)

                takes_value = allowed_short.get(name)
                if takes_value is None:
                    raise RgArgumentError(
                        f"unsupported ripgrep option: -{name}"
                    )

                spelling = f"-{name}"
                if takes_value:
                    remainder = cluster[j + 1:]

                    if remainder:
                        # lexopt's default short-option behavior strips
                        # exactly one syntactic equals sign:
                        #
                        #     -g=*.py  -> value "*.py"
                        #     -g==x    -> value "=x"
                        value = (
                            remainder[1:]
                            if remainder.startswith("=")
                            else remainder
                        )
                    else:
                        i += 1
                        if i >= len(argv):
                            raise RgArgumentError(
                                f"missing value for ripgrep option {spelling}"
                            )
                        value = argv[i]
                        if "\0" in value:
                            raise RgArgumentError(
                                f"value for {spelling} contains a NUL byte"
                            )

                    options.append((spelling, value))

                    # The value-taking option consumed the rest of this
                    # cluster, so there are no further short options here.
                    break

                options.append((spelling, None))
                j += 1

            i += 1
            continue

        positionals.append(arg)
        i += 1

    return ParsedRgArguments(
        options=tuple(options),
        positionals=tuple(positionals),
        saw_end_of_options=saw_end_of_options,
    )


def _main() -> None:
    # True means "takes one value"; False means "switch."
    ALLOWED_LONG = {
        "regexp": True,
        "fixed-strings": False,
        "ignore-case": False,
        "smart-case": False,
        "glob": True,
        "type": True,
        "context": True,
        "json": False,
    }

    ALLOWED_SHORT = {
        "e": True,
        "F": False,
        "i": False,
        "S": False,
        "g": True,
        "t": True,
        "C": True,
    }

    # Accepted: --pre is the value of -e.
    parse_allowed_rg_arguments(
        ["-e", "--pre", "."],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    # Rejected: --pre is an actual option after two positionals.
    parse_allowed_rg_arguments(
        ["needle", ".", "--pre", "/tmp/program"],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    # Accepted: "-z" is the attached value of -g.
    parse_allowed_rg_arguments(
        ["-g-z", "needle", "."],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    # Rejected: this is -F followed by the -z switch.
    parse_allowed_rg_arguments(
        ["-Fz", "needle", "."],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    # Rejected: the first "--" is consumed by -e, so the following --pre
    # is still an option.
    parse_allowed_rg_arguments(
        ["-e", "--", "--pre", "/tmp/program"],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    # Accepted: this "--" really terminates option parsing, so --pre is
    # merely a positional path.
    parse_allowed_rg_arguments(
        ["needle", "--", "--pre"],
        allowed_long=ALLOWED_LONG,
        allowed_short=ALLOWED_SHORT,
    )

    ####

    # parsed = parse_allowed_rg_arguments(
    #     model_options,
    #     allowed_long=ALLOWED_LONG,
    #     allowed_short=ALLOWED_SHORT,
    # )
    #
    # if parsed.positionals:
    #     raise RgArgumentError(
    #         "ripgrep paths and patterns must be supplied through their "
    #         "dedicated tool fields"
    #     )
    # if parsed.saw_end_of_options:
    #     raise RgArgumentError(
    #         "the ripgrep option terminator is not permitted in the options field"
    #     )
    #
    # argv = [
    #     ABSOLUTE_RG_PATH,
    #
    #     "--no-config",
    #
    #     *model_options,
    #
    #     # Defense in depth. Since model_options cannot contain "--" and cannot
    #     # end with an unfulfilled value-taking option, these are guaranteed to
    #     # be parsed as options and occur after all model-controlled options.
    #     "--no-pre",
    #     "--no-search-zip",
    #     "--hostname-bin=",
    #
    #     # Untrusted pattern is unambiguously a value.
    #     "-e",
    #     pattern,
    #
    #     # Search root is unambiguously a positional path.
    #     "--",
    #     fixed_search_root,
    # ]


if __name__ == '__main__':
    _main()
