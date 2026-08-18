"""
The normal/visual-mode command grammar and parser.

    command := ["reg] [count] ( motion
                              | operator [count] (motion | i/a obj | operator)
                              | action )

feed() consumes one key and returns ('more' | 'cmd' | 'abort', Command?). The incremental shape is what lets a real
frontend drive it key-by-key; `pending` exposes the keys typed so far for status-bar display. In visual mode the grammar
inverts: the range already exists, so an operator key *terminates*. (Adapted from x/vibes/minivim.)
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .motions import MOTION_KEYS
from .motions import MOTION_NEEDS_ARG
from .textobjs import TEXTOBJ_KEYS


ParseResult: ta.TypeAlias = tuple[str, ta.Optional['Command']]  # ('more'|'cmd'|'abort', command)


##


ESC = '\x1b'

OPERATORS: ta.AbstractSet[str] = frozenset('dcy><')
ACTIONS: ta.AbstractSet[str] = frozenset('xXDCsSYpPiIaAoOuJrvV.~')
ACTION_NEEDS_ARG: ta.AbstractSet[str] = frozenset('r')

CMDLINE_STARTERS: ta.AbstractSet[str] = frozenset('/?:')


@dc.dataclass(frozen=True, kw_only=True)
class Command(lang.Final):
    register: str | None = None
    count: int = 1
    has_count: bool = False
    op: str | None = None
    doubled: bool = False  # dd / yy / cc / >> / <<
    motion_key: str | None = None
    motion_arg: str | None = None
    tobj: tuple[bool, str] | None = None  # (around, obj)
    action: str | None = None
    action_arg: str | None = None


class Parser:
    def __init__(self) -> None:
        super().__init__()

        # in visual mode the grammar inverts: the operator key terminates rather than pends
        self.visual = False

        self.register: str | None = None
        self.count1 = 0
        self.count2 = 0
        self.op: str | None = None
        self.wait: tuple | None = None  # ('reg',) ('char',key) ('obj',ia) ('g',) ('achar',key)
        self.pending = ''  # the raw keys of the in-progress command, for status display

        self.reset()

    def reset(self) -> None:
        self.register = None
        self.count1 = 0
        self.count2 = 0
        self.op = None
        self.wait = None
        self.pending = ''

    @property
    def is_idle(self) -> bool:
        return (
            self.register is None and
            not self.count1 and
            not self.count2 and
            self.op is None and
            self.wait is None
        )

    def _cmd(self, **kw: ta.Any) -> Command:
        c = Command(
            register=self.register,
            count=max(1, self.count1) * max(1, self.count2),
            has_count=self.count1 > 0 or self.count2 > 0,
            op=self.op,
            **kw,
        )
        self.reset()
        return c

    def _abort(self) -> ParseResult:
        self.reset()
        return ('abort', None)

    def feed(self, key: str) -> ParseResult:  # noqa: C901
        self.pending += key if len(key) == 1 else f'<{key}>'

        if self.wait:
            tag = self.wait[0]

            if tag == 'reg':
                self.wait = None
                self.register = key
                return ('more', None)

            if tag == 'char':
                mkey = self.wait[1]
                self.wait = None
                return ('cmd', self._cmd(motion_key=mkey, motion_arg=key))

            if tag == 'achar':
                akey = self.wait[1]
                self.wait = None
                return ('cmd', self._cmd(action=akey, action_arg=key))

            if tag == 'g':
                self.wait = None
                if key == 'g':
                    return ('cmd', self._cmd(motion_key='gg'))
                return self._abort()  # (real vim: gU gu g~ g_ ge ... omitted)

            if tag == 'obj':
                around = self.wait[1] == 'a'
                self.wait = None
                if key in TEXTOBJ_KEYS:
                    return ('cmd', self._cmd(tobj=(around, key)))
                return self._abort()

        if key == ESC or len(key) > 1:
            # Esc, or a special key token nothing below understands, aborts.
            return self._abort()

        if key.isdigit():
            active = self.count2 if self.op else self.count1

            if key == '0' and active == 0:
                return ('cmd', self._cmd(motion_key='0'))

            if self.op:
                self.count2 = self.count2 * 10 + int(key)
            else:
                self.count1 = self.count1 * 10 + int(key)

            return ('more', None)

        if key == '"' and self.register is None and self.op is None:
            self.wait = ('reg',)
            return ('more', None)

        if key == 'g':
            self.wait = ('g',)
            return ('more', None)

        if key in OPERATORS:
            if self.visual:
                self.op = key
                return ('cmd', self._cmd())

            if self.op is None:
                self.op = key
                return ('more', None)

            if key == self.op:
                return ('cmd', self._cmd(doubled=True))

            return self._abort()

        if (self.op or self.visual) and key in ('i', 'a'):
            self.wait = ('obj', key)
            return ('more', None)

        if key in MOTION_KEYS:
            if key in MOTION_NEEDS_ARG:
                self.wait = ('char', key)
                return ('more', None)

            return ('cmd', self._cmd(motion_key=key))

        if self.op is None and key in ACTIONS:
            if key in ACTION_NEEDS_ARG:
                self.wait = ('achar', key)
                return ('more', None)

            return ('cmd', self._cmd(action=key))

        return self._abort()
