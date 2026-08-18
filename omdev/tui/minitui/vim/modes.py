"""Editor modes."""
import enum


##


class Mode(enum.Enum):
    NORMAL = enum.auto()
    INSERT = enum.auto()
    VISUAL = enum.auto()
    VISUAL_LINE = enum.auto()
    VISUAL_BLOCK = enum.auto()
    CMDLINE = enum.auto()


class CmdlineKind(enum.Enum):
    SEARCH_FORWARD = '/'
    SEARCH_BACKWARD = '?'
    EX = ':'
