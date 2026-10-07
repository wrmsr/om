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

# Extra options for compile, set through a CompileContext

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

# Optimization directives for compile

OPTIMIZATION_NONE: ta.Final[int]
OPTIMIZATION_FULL: ta.Final[int]
AUTO_POSSESS: ta.Final[int]
AUTO_POSSESS_OFF: ta.Final[int]
DOTSTAR_ANCHOR: ta.Final[int]
DOTSTAR_ANCHOR_OFF: ta.Final[int]
START_OPTIMIZE: ta.Final[int]
START_OPTIMIZE_OFF: ta.Final[int]

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

# Options for dfa_match

DFA_RESTART: ta.Final[int]
DFA_SHORTEST: ta.Final[int]

# Options for substitute

SUBSTITUTE_GLOBAL: ta.Final[int]
SUBSTITUTE_EXTENDED: ta.Final[int]
SUBSTITUTE_UNSET_EMPTY: ta.Final[int]
SUBSTITUTE_UNKNOWN_UNSET: ta.Final[int]
SUBSTITUTE_OVERFLOW_LENGTH: ta.Final[int]
SUBSTITUTE_LITERAL: ta.Final[int]
SUBSTITUTE_MATCHED: ta.Final[int]
SUBSTITUTE_REPLACEMENT_ONLY: ta.Final[int]

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

# Error codes for compile

ERROR_END_BACKSLASH: ta.Final[int]
ERROR_END_BACKSLASH_C: ta.Final[int]
ERROR_UNKNOWN_ESCAPE: ta.Final[int]
ERROR_QUANTIFIER_OUT_OF_ORDER: ta.Final[int]
ERROR_QUANTIFIER_TOO_BIG: ta.Final[int]
ERROR_MISSING_SQUARE_BRACKET: ta.Final[int]
ERROR_ESCAPE_INVALID_IN_CLASS: ta.Final[int]
ERROR_CLASS_RANGE_ORDER: ta.Final[int]
ERROR_QUANTIFIER_INVALID: ta.Final[int]
ERROR_INTERNAL_UNEXPECTED_REPEAT: ta.Final[int]
ERROR_INVALID_AFTER_PARENS_QUERY: ta.Final[int]
ERROR_POSIX_CLASS_NOT_IN_CLASS: ta.Final[int]
ERROR_POSIX_NO_SUPPORT_COLLATING: ta.Final[int]
ERROR_MISSING_CLOSING_PARENTHESIS: ta.Final[int]
ERROR_BAD_SUBPATTERN_REFERENCE: ta.Final[int]
ERROR_NULL_PATTERN: ta.Final[int]
ERROR_BAD_OPTIONS: ta.Final[int]
ERROR_MISSING_COMMENT_CLOSING: ta.Final[int]
ERROR_PARENTHESES_NEST_TOO_DEEP: ta.Final[int]
ERROR_PATTERN_TOO_LARGE: ta.Final[int]
ERROR_HEAP_FAILED: ta.Final[int]
ERROR_UNMATCHED_CLOSING_PARENTHESIS: ta.Final[int]
ERROR_INTERNAL_CODE_OVERFLOW: ta.Final[int]
ERROR_MISSING_CONDITION_CLOSING: ta.Final[int]
ERROR_LOOKBEHIND_NOT_FIXED_LENGTH: ta.Final[int]
ERROR_ZERO_RELATIVE_REFERENCE: ta.Final[int]
ERROR_TOO_MANY_CONDITION_BRANCHES: ta.Final[int]
ERROR_CONDITION_ASSERTION_EXPECTED: ta.Final[int]
ERROR_BAD_RELATIVE_REFERENCE: ta.Final[int]
ERROR_UNKNOWN_POSIX_CLASS: ta.Final[int]
ERROR_INTERNAL_STUDY_ERROR: ta.Final[int]
ERROR_UNICODE_NOT_SUPPORTED: ta.Final[int]
ERROR_PARENTHESES_STACK_CHECK: ta.Final[int]
ERROR_CODE_POINT_TOO_BIG: ta.Final[int]
ERROR_LOOKBEHIND_TOO_COMPLICATED: ta.Final[int]
ERROR_LOOKBEHIND_INVALID_BACKSLASH_C: ta.Final[int]
ERROR_UNSUPPORTED_ESCAPE_SEQUENCE: ta.Final[int]
ERROR_CALLOUT_NUMBER_TOO_BIG: ta.Final[int]
ERROR_MISSING_CALLOUT_CLOSING: ta.Final[int]
ERROR_ESCAPE_INVALID_IN_VERB: ta.Final[int]
ERROR_UNRECOGNIZED_AFTER_QUERY_P: ta.Final[int]
ERROR_MISSING_NAME_TERMINATOR: ta.Final[int]
ERROR_DUPLICATE_SUBPATTERN_NAME: ta.Final[int]
ERROR_INVALID_SUBPATTERN_NAME: ta.Final[int]
ERROR_UNICODE_PROPERTIES_UNAVAILABLE: ta.Final[int]
ERROR_MALFORMED_UNICODE_PROPERTY: ta.Final[int]
ERROR_UNKNOWN_UNICODE_PROPERTY: ta.Final[int]
ERROR_SUBPATTERN_NAME_TOO_LONG: ta.Final[int]
ERROR_TOO_MANY_NAMED_SUBPATTERNS: ta.Final[int]
ERROR_CLASS_INVALID_RANGE: ta.Final[int]
ERROR_OCTAL_BYTE_TOO_BIG: ta.Final[int]
ERROR_INTERNAL_OVERRAN_WORKSPACE: ta.Final[int]
ERROR_INTERNAL_MISSING_SUBPATTERN: ta.Final[int]
ERROR_DEFINE_TOO_MANY_BRANCHES: ta.Final[int]
ERROR_BACKSLASH_O_MISSING_BRACE: ta.Final[int]
ERROR_INTERNAL_UNKNOWN_NEWLINE: ta.Final[int]
ERROR_BACKSLASH_G_SYNTAX: ta.Final[int]
ERROR_PARENS_QUERY_R_MISSING_CLOSING: ta.Final[int]
ERROR_VERB_ARGUMENT_NOT_ALLOWED: ta.Final[int]
ERROR_VERB_UNKNOWN: ta.Final[int]
ERROR_SUBPATTERN_NUMBER_TOO_BIG: ta.Final[int]
ERROR_SUBPATTERN_NAME_EXPECTED: ta.Final[int]
ERROR_INTERNAL_PARSED_OVERFLOW: ta.Final[int]
ERROR_INVALID_OCTAL: ta.Final[int]
ERROR_SUBPATTERN_NAMES_MISMATCH: ta.Final[int]
ERROR_MARK_MISSING_ARGUMENT: ta.Final[int]
ERROR_INVALID_HEXADECIMAL: ta.Final[int]
ERROR_BACKSLASH_C_SYNTAX: ta.Final[int]
ERROR_BACKSLASH_K_SYNTAX: ta.Final[int]
ERROR_INTERNAL_BAD_CODE_LOOKBEHINDS: ta.Final[int]
ERROR_BACKSLASH_N_IN_CLASS: ta.Final[int]
ERROR_CALLOUT_STRING_TOO_LONG: ta.Final[int]
ERROR_UNICODE_DISALLOWED_CODE_POINT: ta.Final[int]
ERROR_UTF_IS_DISABLED: ta.Final[int]
ERROR_UCP_IS_DISABLED: ta.Final[int]
ERROR_VERB_NAME_TOO_LONG: ta.Final[int]
ERROR_BACKSLASH_U_CODE_POINT_TOO_BIG: ta.Final[int]
ERROR_MISSING_OCTAL_OR_HEX_DIGITS: ta.Final[int]
ERROR_VERSION_CONDITION_SYNTAX: ta.Final[int]
ERROR_INTERNAL_BAD_CODE_AUTO_POSSESS: ta.Final[int]
ERROR_CALLOUT_NO_STRING_DELIMITER: ta.Final[int]
ERROR_CALLOUT_BAD_STRING_DELIMITER: ta.Final[int]
ERROR_BACKSLASH_C_CALLER_DISABLED: ta.Final[int]
ERROR_QUERY_BARJX_NEST_TOO_DEEP: ta.Final[int]
ERROR_BACKSLASH_C_LIBRARY_DISABLED: ta.Final[int]
ERROR_PATTERN_TOO_COMPLICATED: ta.Final[int]
ERROR_LOOKBEHIND_TOO_LONG: ta.Final[int]
ERROR_PATTERN_STRING_TOO_LONG: ta.Final[int]
ERROR_INTERNAL_BAD_CODE: ta.Final[int]
ERROR_INTERNAL_BAD_CODE_IN_SKIP: ta.Final[int]
ERROR_NO_SURROGATES_IN_UTF16: ta.Final[int]
ERROR_BAD_LITERAL_OPTIONS: ta.Final[int]
ERROR_SUPPORTED_ONLY_IN_UNICODE: ta.Final[int]
ERROR_INVALID_HYPHEN_IN_OPTIONS: ta.Final[int]
ERROR_ALPHA_ASSERTION_UNKNOWN: ta.Final[int]
ERROR_SCRIPT_RUN_NOT_AVAILABLE: ta.Final[int]
ERROR_TOO_MANY_CAPTURES: ta.Final[int]
ERROR_MISSING_OCTAL_DIGIT: ta.Final[int]
ERROR_BACKSLASH_K_IN_LOOKAROUND: ta.Final[int]
ERROR_MAX_VAR_LOOKBEHIND_EXCEEDED: ta.Final[int]
ERROR_PATTERN_COMPILED_SIZE_TOO_BIG: ta.Final[int]
ERROR_OVERSIZE_PYTHON_OCTAL: ta.Final[int]
ERROR_CALLOUT_CALLER_DISABLED: ta.Final[int]
ERROR_EXTRA_CASING_REQUIRES_UNICODE: ta.Final[int]
ERROR_TURKISH_CASING_REQUIRES_UTF: ta.Final[int]
ERROR_EXTRA_CASING_INCOMPATIBLE: ta.Final[int]
ERROR_ECLASS_NEST_TOO_DEEP: ta.Final[int]
ERROR_ECLASS_INVALID_OPERATOR: ta.Final[int]
ERROR_ECLASS_UNEXPECTED_OPERATOR: ta.Final[int]
ERROR_ECLASS_EXPECTED_OPERAND: ta.Final[int]
ERROR_ECLASS_MIXED_OPERATORS: ta.Final[int]
ERROR_ECLASS_HINT_SQUARE_BRACKET: ta.Final[int]
ERROR_PERL_ECLASS_UNEXPECTED_EXPR: ta.Final[int]
ERROR_PERL_ECLASS_EMPTY_EXPR: ta.Final[int]
ERROR_PERL_ECLASS_MISSING_CLOSE: ta.Final[int]
ERROR_PERL_ECLASS_UNEXPECTED_CHAR: ta.Final[int]
ERROR_EXPECTED_CAPTURE_GROUP: ta.Final[int]
ERROR_MISSING_OPENING_PARENTHESIS: ta.Final[int]
ERROR_MISSING_NUMBER_TERMINATOR: ta.Final[int]
ERROR_NULL_ERROROFFSET: ta.Final[int]

# Error codes for everything else

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
ERROR_UTF16_ERR1: ta.Final[int]
ERROR_UTF16_ERR2: ta.Final[int]
ERROR_UTF16_ERR3: ta.Final[int]
ERROR_UTF32_ERR1: ta.Final[int]
ERROR_UTF32_ERR2: ta.Final[int]
ERROR_BADDATA: ta.Final[int]
ERROR_MIXEDTABLES: ta.Final[int]
ERROR_BADMAGIC: ta.Final[int]
ERROR_BADMODE: ta.Final[int]
ERROR_BADOFFSET: ta.Final[int]
ERROR_BADOPTION: ta.Final[int]
ERROR_BADREPLACEMENT: ta.Final[int]
ERROR_BADUTFOFFSET: ta.Final[int]
ERROR_CALLOUT: ta.Final[int]
ERROR_DFA_BADRESTART: ta.Final[int]
ERROR_DFA_RECURSE: ta.Final[int]
ERROR_DFA_UCOND: ta.Final[int]
ERROR_DFA_UFUNC: ta.Final[int]
ERROR_DFA_UITEM: ta.Final[int]
ERROR_DFA_WSSIZE: ta.Final[int]
ERROR_INTERNAL: ta.Final[int]
ERROR_JIT_BADOPTION: ta.Final[int]
ERROR_JIT_STACKLIMIT: ta.Final[int]
ERROR_MATCHLIMIT: ta.Final[int]
ERROR_NOMEMORY: ta.Final[int]
ERROR_NOSUBSTRING: ta.Final[int]
ERROR_NOUNIQUESUBSTRING: ta.Final[int]
ERROR_NULL: ta.Final[int]
ERROR_RECURSELOOP: ta.Final[int]
ERROR_DEPTHLIMIT: ta.Final[int]
ERROR_RECURSIONLIMIT: ta.Final[int]
ERROR_UNAVAILABLE: ta.Final[int]
ERROR_UNSET: ta.Final[int]
ERROR_BADOFFSETLIMIT: ta.Final[int]
ERROR_BADREPESCAPE: ta.Final[int]
ERROR_REPMISSINGBRACE: ta.Final[int]
ERROR_BADSUBSTITUTION: ta.Final[int]
ERROR_BADSUBSPATTERN: ta.Final[int]
ERROR_TOOMANYREPLACE: ta.Final[int]
ERROR_BADSERIALIZEDDATA: ta.Final[int]
ERROR_HEAPLIMIT: ta.Final[int]
ERROR_CONVERT_SYNTAX: ta.Final[int]
ERROR_INTERNAL_DUPMATCH: ta.Final[int]
ERROR_DFA_UINVALID_UTF: ta.Final[int]
ERROR_INVALIDOFFSET: ta.Final[int]
ERROR_JIT_UNSUPPORTED: ta.Final[int]
ERROR_REPLACECASE: ta.Final[int]
ERROR_TOOLARGEREPLACE: ta.Final[int]
ERROR_DIFFSUBSPATTERN: ta.Final[int]
ERROR_DIFFSUBSSUBJECT: ta.Final[int]
ERROR_DIFFSUBSOFFSET: ta.Final[int]
ERROR_DIFFSUBSOPTIONS: ta.Final[int]
ERROR_BAD_BACKSLASH_K: ta.Final[int]
ERROR_PARTIALSUBS: ta.Final[int]


##


# What pattern_info and config return depends on the item asked for, which a type checker cannot see through: an int
# for most, bytes or None for INFO_NAMETABLE and INFO_FIRSTBITMAP, and a str for the config items which are strings.
# Statically that is Any, json.loads-style - forcing every caller to narrow an answer whose type they already know by
# what they asked for would be hostile for no safety gain.
type _InfoValue = ta.Any


class Error(Exception):
    code: int
    offset: int | None


class CompileError(Error): ...


class MatchError(Error): ...


class SubstituteError(Error): ...


@ta.final
class CompileContext:
    @classmethod
    def create(
            cls,
            *,
            bsr: int | None = None,
            newline: int | None = None,
            max_pattern_length: int | None = None,
            max_pattern_compiled_length: int | None = None,
            max_varlookbehind: int | None = None,
            parens_nest_limit: int | None = None,
            extra_options: int | None = None,
            optimize: int | ta.Iterable[int] | None = None,
    ) -> CompileContext: ...


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
    def pattern_info(self, what: int, /) -> _InfoValue: ...

    def match(
            self,
            subject: collections.abc.Buffer,
            match_data: MatchData,
            start_offset: int = 0,
            options: int = 0,
            match_context: MatchContext | None = None,
    ) -> int: ...

    def dfa_match(
            self,
            subject: collections.abc.Buffer,
            match_data: MatchData,
            start_offset: int = 0,
            options: int = 0,
            match_context: MatchContext | None = None,
            wscount: int = 1000,
    ) -> int: ...

    def substitute(
            self,
            subject: collections.abc.Buffer,
            replacement: collections.abc.Buffer,
            start_offset: int = 0,
            options: int = 0,
            match_data: MatchData | None = None,
            match_context: MatchContext | None = None,
    ) -> tuple[bytes, int]: ...

    def substring_number_from_name(self, name: bytes, /) -> int: ...

    def substring_nametable_scan(self, name: bytes, /) -> tuple[int, ...]: ...


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

    @property
    def mark(self) -> bytes | None: ...

    @property
    def startchar(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def heapframes_size(self) -> int: ...

    def next_match(self) -> tuple[int, int] | None: ...


def compile(  # noqa
        pattern: collections.abc.Buffer,
        options: int = 0,
        compile_context: CompileContext | None = None,
) -> Code: ...


def config(what: int, /) -> _InfoValue: ...


def get_error_message(code: int, /) -> str: ...


##


capi: ta.Final[types.CapsuleType]
