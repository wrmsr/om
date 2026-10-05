# fmt: off
# ruff: noqa: I001
"""
https://github.com/mvdan/sh/tree/c6351e95dbeeb2645b68c463ea916eed815bef5e
"""
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from .braces import (  # noqa
    split_braces,
)

from .langs import (  # noqa
    LANG_AUTO,
    LANG_BASH,
    LANG_BATS,
    LANG_MIR_BSD_KORN,
    LANG_POSIX,
    LANG_ZSH,
    LangVariant,
)

from .parser import (  # noqa
    LangError,
    ParseError,
    Parser,
    is_keyword,
    valid_name,
)

from .quote import (  # noqa
    QuoteError,
    quote,
)

from .walk import (  # noqa
    debug_print,
    preorder,
    walk,
)
