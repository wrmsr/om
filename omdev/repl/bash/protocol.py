r"""
The conversation with a bash on a pty, as bytes each way and nothing else: no process, no IO, no clock.

To the shell, a submission is a few short lines of printable ascii - the source as `$'\x..'` quoted chunks appended to
a variable, then an `eval` of it. A terminal's input is not a transparent channel: in its canonical mode a line longer
than a kernel constant (4096 bytes on linux, 1024 on macos) is silently cut, and the control characters among its bytes
are acted on rather than delivered. Escaped and chunked, the source is immune to both, and an unfinished quote in it is
a syntax error the shell reports rather than a continuation prompt it waits at forever.

From the shell, a command's end is a mark its `PROMPT_COMMAND` prints before every prompt: an operating system command
escape no terminal acts on, carrying a nonce only this conversation knows, the number of the submission the shell last
began, its exit status, and the working directory. The number is what makes the mark trustworthy: an interrupt arriving
at an idle prompt makes the shell print another, and without it that one would be taken for the end of the next
command.
"""
import re
import secrets
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


##


# The terminal's INTR character: SIGINT to the foreground job.
INTERRUPT: ta.Final[bytes] = b'\x03'

# SUSP: SIGTSTP, which stops what an interrupt did not end - and the shell has its terminal, and its prompt, back.
SUSPEND: ta.Final[bytes] = b'\x1a'


@dc.dataclass(frozen=True)
class BashPrompt(lang.Final):
    """The shell is at its prompt again."""

    seq: int  # the submission the shell last began: the one which just ended, unless nothing ran in between
    returncode: int
    cwd: str


##


class BashPromptScanner:
    """Splits a shell's output into what its commands wrote and the prompt marks between."""

    def __init__(self, mark_prefix: bytes, *, max_mark_bytes: int = 8192) -> None:
        super().__init__()

        self._prefix = check.not_empty(mark_prefix)
        self._max_mark_bytes = max_mark_bytes

        self._pat = re.compile(re.escape(mark_prefix) + rb'(\d+);(\d+);([^\x07]*)\x07')
        self._buf = b''

    def _held(self, buf: bytes) -> int:
        """How many bytes at the end of `buf` may be the beginning of a mark the rest of which has yet to arrive."""

        if (i := buf.find(self._prefix)) >= 0:
            n = len(buf) - i
            return n if n <= self._max_mark_bytes else 0

        for n in range(min(len(self._prefix) - 1, len(buf)), 0, -1):
            if buf.endswith(self._prefix[:n]):
                return n
        return 0

    def feed(self, data: bytes) -> list[bytes | BashPrompt]:
        """What `data` completed, in order: runs of output, and prompts."""

        buf = self._buf + data
        out: list[bytes | BashPrompt] = []

        pos = 0
        for m in self._pat.finditer(buf):
            if m.start() > pos:
                out.append(buf[pos:m.start()])
            out.append(BashPrompt(
                seq=int(m.group(1)),
                returncode=int(m.group(2)),
                cwd=m.group(3).decode('utf-8', 'replace'),
            ))
            pos = m.end()

        rest = buf[pos:]
        held = self._held(rest)
        if len(rest) > held:
            out.append(rest[:len(rest) - held])
        self._buf = rest[len(rest) - held:] if held else b''

        return out


##


class BashProtocol:
    def __init__(
            self,
            nonce: str | None = None,
            *,
            max_line_bytes: int = 768,
    ) -> None:
        """`max_line_bytes` bounds every line sent - under the smallest canonical-mode limit there is, with room."""

        super().__init__()

        if nonce is None:
            nonce = secrets.token_hex(16)
        check.arg(nonce.isalnum())
        check.arg(max_line_bytes >= 64)

        self._nonce = nonce
        self._max_line_bytes = max_line_bytes

        self._mark_prefix = f'\x1b]7770;{nonce};'.encode('ascii')

    @property
    def nonce(self) -> str:
        return self._nonce

    def new_scanner(self) -> BashPromptScanner:
        return BashPromptScanner(self._mark_prefix)

    #

    _ENV: ta.ClassVar[ta.Mapping[str, str]] = {
        # Nothing here can page: there is no screen to page on.
        'PAGER': 'cat',
        'GIT_PAGER': 'cat',
        'MANPAGER': 'cat',
    }

    def init(self) -> bytes:
        """
        The line which makes a freshly started interactive bash this conversation's: sent once, first, and done when
        the first prompt (of submission 0) arrives - everything the shell wrote before that is its startup's, and the
        terminal's echo of this line, and is discarded.
        """

        mark = rf'printf "\033]7770;{self._nonce};%s;%s;%s\007" "$__om_n" "$__om_last" "$PWD"'
        return (' ' + '; '.join([
            'stty -echo',
            'unset HISTFILE',
            'set +o history',
            'trap - DEBUG',
            'export ' + ' '.join(f'{k}={v}' for k, v in self._ENV.items()),
            '__om_n=0',
            '__om_last=0',
            '__om_rc() { return "$1"; }',
            # Leaving is hanging up, as closing a terminal's window is: the jobs still there go with the shell - by its
            # own hand, since they are in process groups of their own which nobody else can account for - unless they
            # were disowned.
            (
                '__om_exit() { local j; for j in $(jobs -p); do '
                'kill -HUP -- "-$j"; kill -CONT -- "-$j"; '
                'done 2>/dev/null; }'
            ),
            'trap __om_exit EXIT',
            'PS0=',
            'PS1=',
            'PS2=',
            'unset PROMPT_COMMAND',
            # Echo is switched off again before every prompt: whatever a command did to the terminal, the next
            # submission is not echoed back as if it were output.
            f"PROMPT_COMMAND='__om_last=$?; stty -echo 2>/dev/null; {mark}'",
        ]) + '\n').encode('ascii')

    #

    @staticmethod
    def _escape(b: int) -> str:
        if 0x20 <= b < 0x7f and b not in (0x27, 0x5c):
            return chr(b)
        return f'\\x{b:02x}'

    def _quote_lines(self, var: str, data: bytes) -> list[str]:
        """`data` as assignments to `var` of `$'...'` strings, none longer than a line may be."""

        room = self._max_line_bytes - len(f"{var}+=$''")

        lines: list[str] = []
        cur: list[str] = []
        cur_len = 0
        for b in data:
            esc = self._escape(b)
            if cur_len + len(esc) > room:
                lines.append(''.join(cur))
                cur = []
                cur_len = 0
            cur.append(esc)
            cur_len += len(esc)
        lines.append(''.join(cur))

        return [f"{var}{'+' if i else ''}=$'{line}'" for i, line in enumerate(lines)]

    def submit(self, seq: int, source: str) -> bytes:
        """
        A submission of user source: run by `eval` in the shell itself, so what it changes - the directory, variables,
        functions - stays changed; with `$?` as the last submission left it; and with nothing to read on its standard
        input, so a command which wants input fails at once rather than waiting for what cannot be typed to it.
        """

        check.arg(seq > 0)

        # A NUL cannot be in a shell word, and would end the quoted string it was in.
        data = source.encode('utf-8').replace(b'\0', b'')

        return ('\n'.join([
            '{',
            *self._quote_lines('__om_s', data),
            f'}}; __om_n={seq}; __om_rc "$__om_last"; eval "$__om_s" </dev/null',
        ]) + '\n').encode('ascii')

    def command(self, seq: int, command: str) -> bytes:
        """A submission of the conversation's own: a short line of plain ascii, run as it is."""

        check.arg(seq > 0)
        line = f' __om_n={seq}; {command}\n'.encode('ascii')
        check.arg(len(line) <= self._max_line_bytes)
        return line

    # A command which does nothing: its prompt says the shell has read everything sent before it.
    SYNC: ta.ClassVar[str] = ':'

    # Kills, by process group, the jobs a SUSPEND stopped - and has the shell forget them first, so that it does not
    # announce their deaths at some later prompt. Only the stopped ones: a job the user put in the background and left
    # running is theirs.
    KILL_STOPPED_JOBS: ta.ClassVar[str] = (
        'for __om_j in $(jobs -ps); do disown "$__om_j"; kill -KILL -- "-$__om_j"; done 2>/dev/null'
    )
