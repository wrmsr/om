import collections.abc
import types
import typing as ta

##


UNSET: ta.Final[int]

MAJOR: ta.Final[int]
MINOR: ta.Final[int]

# Options for both compile and match

ANCHORED: ta.Final[int]
NO_UTF_CHECK: ta.Final[int]
ENDANCHORED: ta.Final[int]

# Options for compile

ALLOW_EMPTY_CLASS: ta.Final[int]
ALT_BSUX: ta.Final[int]
AUTO_CALLOUT: ta.Final[int]
CASELESS: ta.Final[int]
DOLLAR_ENDONLY: ta.Final[int]
DOTALL: ta.Final[int]
DUPNAMES: ta.Final[int]
EXTENDED: ta.Final[int]
FIRSTLINE: ta.Final[int]
MATCH_UNSET_BACKREF: ta.Final[int]
MULTILINE: ta.Final[int]
NEVER_UCP: ta.Final[int]
NEVER_UTF: ta.Final[int]
NO_AUTO_CAPTURE: ta.Final[int]
NO_AUTO_POSSESS: ta.Final[int]
NO_DOTSTAR_ANCHOR: ta.Final[int]
NO_START_OPTIMIZE: ta.Final[int]
UCP: ta.Final[int]
UNGREEDY: ta.Final[int]
UTF: ta.Final[int]
NEVER_BACKSLASH_C: ta.Final[int]
ALT_CIRCUMFLEX: ta.Final[int]
ALT_VERBNAMES: ta.Final[int]
USE_OFFSET_LIMIT: ta.Final[int]
EXTENDED_MORE: ta.Final[int]
LITERAL: ta.Final[int]
MATCH_INVALID_UTF: ta.Final[int]
ALT_EXTENDED_CLASS: ta.Final[int]

# Extra options for compile

EXTRA_ALLOW_SURROGATE_ESCAPES: ta.Final[int]
EXTRA_BAD_ESCAPE_IS_LITERAL: ta.Final[int]
EXTRA_MATCH_WORD: ta.Final[int]
EXTRA_MATCH_LINE: ta.Final[int]
EXTRA_ESCAPED_CR_IS_LF: ta.Final[int]
EXTRA_ALT_BSUX: ta.Final[int]
EXTRA_ALLOW_LOOKAROUND_BSK: ta.Final[int]
EXTRA_CASELESS_RESTRICT: ta.Final[int]
EXTRA_ASCII_BSD: ta.Final[int]
EXTRA_ASCII_BSS: ta.Final[int]
EXTRA_ASCII_BSW: ta.Final[int]
EXTRA_ASCII_POSIX: ta.Final[int]
EXTRA_ASCII_DIGIT: ta.Final[int]
EXTRA_PYTHON_OCTAL: ta.Final[int]
EXTRA_NO_BS0: ta.Final[int]
EXTRA_NEVER_CALLOUT: ta.Final[int]
EXTRA_TURKISH_CASING: ta.Final[int]

# Options for match

NOTBOL: ta.Final[int]
NOTEOL: ta.Final[int]
NOTEMPTY: ta.Final[int]
NOTEMPTY_ATSTART: ta.Final[int]
PARTIAL_SOFT: ta.Final[int]
PARTIAL_HARD: ta.Final[int]
NO_JIT: ta.Final[int]
COPY_MATCHED_SUBJECT: ta.Final[int]
DISABLE_RECURSELOOP_CHECK: ta.Final[int]

# Values of INFO_NEWLINE / CONFIG_NEWLINE and INFO_BSR / CONFIG_BSR

NEWLINE_CR: ta.Final[int]
NEWLINE_LF: ta.Final[int]
NEWLINE_CRLF: ta.Final[int]
NEWLINE_ANY: ta.Final[int]
NEWLINE_ANYCRLF: ta.Final[int]
NEWLINE_NUL: ta.Final[int]

BSR_UNICODE: ta.Final[int]
BSR_ANYCRLF: ta.Final[int]

# Items for Code.pattern_info

INFO_ALLOPTIONS: ta.Final[int]
INFO_ARGOPTIONS: ta.Final[int]
INFO_BACKREFMAX: ta.Final[int]
INFO_BSR: ta.Final[int]
INFO_CAPTURECOUNT: ta.Final[int]
INFO_FIRSTCODEUNIT: ta.Final[int]
INFO_FIRSTCODETYPE: ta.Final[int]
INFO_FIRSTBITMAP: ta.Final[int]
INFO_HASCRORLF: ta.Final[int]
INFO_JCHANGED: ta.Final[int]
INFO_JITSIZE: ta.Final[int]
INFO_LASTCODEUNIT: ta.Final[int]
INFO_LASTCODETYPE: ta.Final[int]
INFO_MATCHEMPTY: ta.Final[int]
INFO_MATCHLIMIT: ta.Final[int]
INFO_MAXLOOKBEHIND: ta.Final[int]
INFO_MINLENGTH: ta.Final[int]
INFO_NAMECOUNT: ta.Final[int]
INFO_NAMEENTRYSIZE: ta.Final[int]
INFO_NAMETABLE: ta.Final[int]
INFO_NEWLINE: ta.Final[int]
INFO_DEPTHLIMIT: ta.Final[int]
INFO_SIZE: ta.Final[int]
INFO_HASBACKSLASHC: ta.Final[int]
INFO_FRAMESIZE: ta.Final[int]
INFO_HEAPLIMIT: ta.Final[int]
INFO_EXTRAOPTIONS: ta.Final[int]

# Items for config

CONFIG_BSR: ta.Final[int]
CONFIG_JIT: ta.Final[int]
CONFIG_JITTARGET: ta.Final[int]
CONFIG_LINKSIZE: ta.Final[int]
CONFIG_MATCHLIMIT: ta.Final[int]
CONFIG_NEWLINE: ta.Final[int]
CONFIG_PARENSLIMIT: ta.Final[int]
CONFIG_DEPTHLIMIT: ta.Final[int]
CONFIG_STACKRECURSE: ta.Final[int]
CONFIG_UNICODE: ta.Final[int]
CONFIG_UNICODE_VERSION: ta.Final[int]
CONFIG_VERSION: ta.Final[int]
CONFIG_HEAPLIMIT: ta.Final[int]
CONFIG_NEVER_BACKSLASH_C: ta.Final[int]
CONFIG_COMPILED_WIDTHS: ta.Final[int]
CONFIG_TABLES_LENGTH: ta.Final[int]

# Error codes reachable through what is bound here. Compile errors are the positive codes, and are left unnamed.

ERROR_NOMATCH: ta.Final[int]
ERROR_PARTIAL: ta.Final[int]
ERROR_UTF8_ERR1: ta.Final[int]
ERROR_UTF8_ERR2: ta.Final[int]
ERROR_UTF8_ERR3: ta.Final[int]
ERROR_UTF8_ERR4: ta.Final[int]
ERROR_UTF8_ERR5: ta.Final[int]
ERROR_UTF8_ERR6: ta.Final[int]
ERROR_UTF8_ERR7: ta.Final[int]
ERROR_UTF8_ERR8: ta.Final[int]
ERROR_UTF8_ERR9: ta.Final[int]
ERROR_UTF8_ERR10: ta.Final[int]
ERROR_UTF8_ERR11: ta.Final[int]
ERROR_UTF8_ERR12: ta.Final[int]
ERROR_UTF8_ERR13: ta.Final[int]
ERROR_UTF8_ERR14: ta.Final[int]
ERROR_UTF8_ERR15: ta.Final[int]
ERROR_UTF8_ERR16: ta.Final[int]
ERROR_UTF8_ERR17: ta.Final[int]
ERROR_UTF8_ERR18: ta.Final[int]
ERROR_UTF8_ERR19: ta.Final[int]
ERROR_UTF8_ERR20: ta.Final[int]
ERROR_UTF8_ERR21: ta.Final[int]
ERROR_BADDATA: ta.Final[int]
ERROR_BADMAGIC: ta.Final[int]
ERROR_BADMODE: ta.Final[int]
ERROR_BADOFFSET: ta.Final[int]
ERROR_BADOPTION: ta.Final[int]
ERROR_BADUTFOFFSET: ta.Final[int]
ERROR_INTERNAL: ta.Final[int]
ERROR_MATCHLIMIT: ta.Final[int]
ERROR_NOMEMORY: ta.Final[int]
ERROR_NULL: ta.Final[int]
ERROR_RECURSELOOP: ta.Final[int]
ERROR_DEPTHLIMIT: ta.Final[int]
ERROR_UNSET: ta.Final[int]
ERROR_BADOFFSETLIMIT: ta.Final[int]
ERROR_HEAPLIMIT: ta.Final[int]


##


class Error(Exception):
    code: int
    offset: int | None


class CompileError(Error): ...


class MatchError(Error): ...


@ta.final
class MatchContext:
    @classmethod
    def create(
            cls,
            *,
            match_limit: int | None = None,
            depth_limit: int | None = None,
            heap_limit: int | None = None,
            offset_limit: int | None = None,
    ) -> MatchContext: ...


@ta.final
class Code:
    def pattern_info(self, what: int, /) -> int | bytes | None: ...

    def match(
            self,
            subject: collections.abc.Buffer,
            match_data: MatchData,
            start_offset: int = 0,
            options: int = 0,
            match_context: MatchContext | None = None,
    ) -> int: ...


@ta.final
class MatchData:
    @classmethod
    def create(cls, ovecsize: int, /) -> MatchData: ...

    @classmethod
    def create_from_pattern(cls, code: Code, /) -> MatchData: ...

    @property
    def ovector(self) -> tuple[int, ...]: ...

    @property
    def ovector_count(self) -> int: ...

    def next_match(self) -> tuple[int, int] | None: ...


def compile(  # noqa
        pattern: collections.abc.Buffer,
        options: int = 0,
        *,
        extra_options: int = 0,
) -> Code: ...


def config(what: int, /) -> int | str: ...


def get_error_message(code: int, /) -> str: ...


##


capi: ta.Final[types.CapsuleType]
