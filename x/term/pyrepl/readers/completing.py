#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Antonio Cuni
#
#                    All Rights Reserved
#
#
# Permission to use, copy, modify, and distribute this software and its documentation for any purpose is hereby granted
# without fee, provided that the above copyright notice appear in all copies and that both that copyright notice and
# this permission notice appear in supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES
# OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
import re
import typing as ta

from ..commands import Command
from ..commands import self_insert as base_self_insert
from ..console import Console
from ..render import RenderLine
from ..render import ScreenOverlay
from ..types import CommandName
from ..types import CompletionAction
from ..types import KeySpec
from .reader import SYNTAX_WORD
from .reader import Reader


##


def prefix(wordlist: list[str], j: int = 0) -> str:
    d = {}
    i = j
    try:
        while 1:
            for word in wordlist:
                d[word[i]] = 1
            if len(d) > 1:
                return wordlist[0][j:i]
            i += 1
            d = {}
    except IndexError:
        return wordlist[0][j:i]


STRIP_COLOR_REGEX = re.compile(r'\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[m|K]')


def strip_color(s: str) -> str:
    return STRIP_COLOR_REGEX.sub('', s)


def real_len(s: str) -> int:
    return len(strip_color(s))


def left_align(s: str, maxlen: int) -> str:
    stripped = strip_color(s)
    if len(stripped) > maxlen:
        # too bad, we remove the color
        return stripped[:maxlen]
    padding = maxlen - len(stripped)
    return s + ' ' * padding


def build_menu(
        cons: Console,
        wordlist: list[str],
        start: int,
        use_brackets: bool,
        sort_in_column: bool,
) -> tuple[list[str], int]:
    if use_brackets:
        item = '[ %s ]'
        padding = 4
    else:
        item = '%s  '
        padding = 2

    maxlen = min(max(map(real_len, wordlist)), cons.width - padding)

    cols = int(cons.width / (maxlen + padding))
    rows = int((len(wordlist) - 1) / cols + 1)

    if sort_in_column:
        # sort_in_column=False (default)     sort_in_column=True
        #          A B C                       A D G
        #          D E F                       B E
        #          G                           C F
        #
        # "fill" the table with empty words, so we always have the same amount
        # of rows for each column
        missing = cols * rows - len(wordlist)
        wordlist = wordlist + [''] * missing
        indexes = [(i % cols) * rows + i // cols for i in range(len(wordlist))]
        wordlist = [wordlist[i] for i in indexes]

    menu = []

    i = start
    for r in range(rows):
        row = []

        for col in range(cols):  # noqa
            row.append(item % left_align(wordlist[i], maxlen))

            i += 1
            if i >= len(wordlist):
                break

        menu.append(''.join(row))

        if i >= len(wordlist):
            i = 0
            break

        if r + 5 > cons.height:
            menu.append(f'   {len(wordlist) - i:d} more... ')
            break

    return menu, i


# this gets somewhat user interface-y, and as a result the logic gets very convoluted.
#
#  To summarise the summary of the summary:- people are a problem.
#                  -- The Hitch-Hikers Guide to the Galaxy, Episode 12
#
##
# Desired behaviour of the completions commands.
#
# the considerations are:
# (1) how many completions are possible
# (2) whether the last command was a completion
# (3) if we can assume that the completer is going to return the same set of completions: this is controlled by the
#     ``assume_immutable_completions`` variable on the reader, which is True by default to match the historical
#     behaviour of pyrepl, but e.g. False in the ReadlineAlikeReader to match more closely readline's semantics (this is
#     needed e.g. by fancycompleter)
#
# if there's no possible completion, beep at the user and point this out. this is easy.
#
# if there's only one possible completion, stick it in. if the last thing user did was a completion, point out that he
# isn't getting anywhere, but only if the ``assume_immutable_completions`` is True.
#
# now it gets complicated.
#
# for the first press of a completion key:
#  if there's a common prefix, stick it in.
#
#  irrespective of whether anything got stuck in, if the word is now complete, show the "complete but not unique"
#  message
#
#  if there's no common prefix and if the word is not now complete, beep.
#
#        common prefix ->    yes          no
#        word complete \/
#            yes           "cbnu"      "cbnu"
#            no              -          beep
#
# for the second bang on the completion key there will necessarily be no common prefix show a menu of the choices.
#
# for subsequent bangs, rotate the menu around (if there are sufficient choices).


class complete(Command):  # noqa
    def do(self) -> None:
        r: CompletingReader
        r = self.reader  # type: ignore[assignment]

        last_is_completer = r.last_command_is(self.__class__)
        if r.cmpltn_action:
            if last_is_completer:  # double-tab: execute action
                msg = r.cmpltn_action[1]()
                r.cmpltn_action = None  # consumed
                if msg:
                    r.msg = msg
                    r.cmpltn_message_visible = True
                    r.invalidate_message()
            else:  # other input since last tab: cancel action
                r.cmpltn_action = None

        immutable_completions = r.assume_immutable_completions
        completions_unchangable = last_is_completer and immutable_completions
        stem = r.get_stem()
        if not completions_unchangable:
            r.cmpltn_menu_choices, r.cmpltn_action = r.get_completions(stem)

        completions = r.cmpltn_menu_choices
        if not completions:
            if not r.cmpltn_action:
                r.error('no matches')

        elif len(completions) == 1:
            completion = strip_color(completions[0])
            if completions_unchangable and len(completion) == len(stem):
                r.msg = '[ sole completion ]'
                r.cmpltn_message_visible = True
                r.invalidate_message()
            r.insert(completion[len(stem):])

        else:
            clean_completions = [strip_color(word) for word in completions]
            p = prefix(clean_completions, len(stem))
            if p:
                r.insert(p)

            if last_is_completer:
                r.cmpltn_menu_visible = True
                r.cmpltn_menu, r.cmpltn_menu_end = build_menu(
                    r.console,
                    completions,
                    r.cmpltn_menu_end,
                    r.use_brackets,
                    r.sort_in_column,
                )
                if r.msg:
                    r.msg = ''
                    r.cmpltn_message_visible = False
                    r.invalidate_message()
                r.invalidate_overlay()

            elif not r.cmpltn_menu_visible:
                if stem + p in clean_completions:
                    r.msg = '[ complete but not unique ]'
                    r.cmpltn_message_visible = True
                    r.invalidate_message()
                else:
                    r.msg = '[ not unique ]'
                    r.cmpltn_message_visible = True
                    r.invalidate_message()

        if r.cmpltn_action:
            if r.msg and r.cmpltn_message_visible:
                # There is already a message (eg. [ not unique ]) that
                # would conflict for next tab: cancel action
                r.cmpltn_action = None
            else:
                r.msg = r.cmpltn_action[0]
                r.cmpltn_message_visible = True
                r.invalidate_message()


class self_insert(base_self_insert):  # noqa
    def do(self) -> None:
        r: CompletingReader
        r = self.reader  # type: ignore[assignment]

        super().do()

        if r.cmpltn_menu_visible:
            stem = r.get_stem()

            if len(stem) < 1:
                r.cmpltn_reset()

            else:
                completions = [w for w in r.cmpltn_menu_choices if strip_color(w).startswith(stem)]
                if completions:
                    r.cmpltn_menu, r.cmpltn_menu_end = build_menu(
                        r.console,
                        completions,
                        0,
                        r.use_brackets,
                        r.sort_in_column,
                    )
                    r.invalidate_overlay()

                else:
                    r.cmpltn_reset()


class CompletingReader(Reader):
    """Adds completion support"""

    def __init__(
            self,
            console: Console,
    ) -> None:
        super().__init__(console)

        # see the comment for the complete command
        self.assume_immutable_completions = True
        self.use_brackets = True  # display completions inside []
        self.sort_in_column = False

        # cmpltn_reset checks this to decide whether it must invalidate the overlay, so it must exist before the first
        # call.
        self.cmpltn_menu_visible = False

        self.cmpltn_reset()

        for c in (complete, self_insert):
            self.commands[c.__name__] = c
            self.commands[c.__name__.replace('_', '-')] = c

    def collect_keymap(self) -> ta.Sequence[tuple[KeySpec, CommandName]]:
        return (
            *super().collect_keymap(),
            (r'\t', 'complete'),
        )

    def after_command(self, cmd: Command) -> None:
        super().after_command(cmd)

        if not isinstance(cmd, (complete, self_insert)):
            self.cmpltn_reset()

    def get_screen_overlays(self) -> tuple[ScreenOverlay, ...]:
        if not self.cmpltn_menu_visible:
            return ()

        # We display the completions menu below the current prompt
        return (
            ScreenOverlay(
                self.lxy[1] + 1,
                tuple(RenderLine.from_rendered_text(line) for line in self.cmpltn_menu),
                insert=True,
            ),
        )

    def finish(self) -> None:
        super().finish()

        self.cmpltn_reset()

    cmpltn_menu: list[str]
    cmpltn_menu_visible: bool
    cmpltn_message_visible: bool
    cmpltn_menu_end: int
    cmpltn_menu_choices: list[str]
    cmpltn_action: CompletionAction | None

    def cmpltn_reset(self) -> None:
        if self.cmpltn_menu_visible:
            self.invalidate_overlay()
        self.cmpltn_menu = []
        self.cmpltn_menu_visible = False
        self.cmpltn_message_visible = False
        self.cmpltn_menu_end = 0
        self.cmpltn_menu_choices = []
        self.cmpltn_action = None

    def get_stem(self) -> str:
        st = self.syntax_table
        sw = SYNTAX_WORD
        b = self.buffer
        p = self.pos - 1
        while p >= 0 and st.get(b[p], sw) == sw:
            p -= 1
        return ''.join(b[p + 1:self.pos])

    def get_completions(self, stem: str) -> tuple[list[str], CompletionAction | None]:
        return [], None

    def get_line(self) -> str:
        """Return the current line until the cursor position."""

        return ''.join(self.buffer[:self.pos])
