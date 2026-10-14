import abc
import subprocess
import typing as ta

from omcore import lang

from .types import Clipboard
from .types import ClipboardContents
from .types import TextClipboardContents


##


class CommandError(subprocess.CalledProcessError):
    def __str__(self):
        msg = super().__str__()
        if self.stderr:
            msg += f'\nstderr:\n{self.stderr.strip()}'
        return msg


def check_subprocess_output(cmd: ta.Sequence[str], **kwargs: ta.Any) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        **kwargs,
    )

    if result.returncode != 0:
        raise CommandError(
            result.returncode,
            cmd,
            result.stdout,
            result.stderr.decode(),  # noqa
        )

    return result.stdout.decode()  # noqa


##


class TextCommandClipboard(Clipboard, lang.Abstract):
    @property
    @abc.abstractmethod
    def _get_cmd(self) -> ta.Sequence[str]:
        raise NotImplementedError

    def get(self) -> list[ClipboardContents]:
        s = check_subprocess_output(self._get_cmd)
        return [TextClipboardContents(s)]

    @property
    @abc.abstractmethod
    def _put_cmd(self) -> ta.Sequence[str]:
        raise NotImplementedError

    def put(self, c: ClipboardContents) -> None:
        if isinstance(c, TextClipboardContents):
            check_subprocess_output(self._put_cmd, input=c.s.encode())
        else:
            raise TypeError(c)


#


class XclipLinuxClipboard(TextCommandClipboard):
    _get_cmd = ('xclip', '-selection', 'clipboard', '-o')
    _put_cmd = ('xclip', '-selection', 'clipboard')


class PbcopyDarwinClipboard(TextCommandClipboard):
    _get_cmd = ('pbpaste',)
    _put_cmd = ('pbcopy',)
