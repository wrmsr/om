"""
A best effort at the standard library's `re`, matched by PCRE2: the same functions, flags, and objects, over patterns
and replacements written the way `re` reads them. See the package's README for where the two still differ.
"""
from re import (  # noqa
    PatternError,
    error,

    RegexFlag,

    NOFLAG,
    A,
    ASCII,
    DEBUG,
    DOTALL,
    I,
    IGNORECASE,
    L,
    LOCALE,
    M,
    MULTILINE,
    S,
    U,
    UNICODE,
    VERBOSE,
    X,
)

from .functions import (  # noqa
    compile,  # noqa
    purge,
    escape,

    search,
    match,
    fullmatch,
    finditer,
    findall,
    split,
    sub,
    subn,
)

from .matches import (  # noqa
    Match,
)

from .patterns import (  # noqa
    Pattern,
)
