"""
Registers: named clipboards with a kind.

Contents are stored as line-pieces plus a Kind; the kind decides whether `p` opens new lines (LINEWISE) or splices into
the current one (charwise). "A appends to "a; the unnamed register always mirrors the last write; "0 holds the last
yank. (Adapted from x/vibes/minivim.)
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..docs.positions import Kind


##


@dc.dataclass(frozen=True)
class RegValue(lang.Final):
    pieces: tuple[str, ...]  # linewise: whole lines
    kind: Kind               # EXCLUSIVE (charwise) or LINEWISE


def _reg_append(old: RegValue, new: RegValue) -> RegValue:
    if old.kind is Kind.BLOCK or new.kind is Kind.BLOCK:
        # Blocks stack vertically on append. (vim's horizontal-join subtleties are out of scope.)
        return RegValue((*old.pieces, *new.pieces), Kind.BLOCK)
    if old.kind is Kind.LINEWISE or new.kind is Kind.LINEWISE:
        return RegValue((*old.pieces, *new.pieces), Kind.LINEWISE)
    joined = (*old.pieces[:-1], old.pieces[-1] + new.pieces[0], *new.pieces[1:])
    return RegValue(joined, Kind.EXCLUSIVE)


def pieces_repeat(pieces: ta.Sequence[str], count: int) -> list[str]:
    out = list(pieces)
    for _ in range(count - 1):
        out = [*out[:-1], out[-1] + pieces[0], *pieces[1:]]
    return out


class Registers:
    def __init__(self) -> None:
        super().__init__()

        self._regs: dict[str, RegValue] = {}

    def get(self, name: str) -> RegValue | None:
        return self._regs.get(name)

    def set(self, name: str, val: RegValue, *, is_yank: bool) -> None:
        if name.isalpha() and name.isupper():  # "A appends to "a
            if (old := self._regs.get(name.lower())) is not None:
                val = _reg_append(old, val)
            name = name.lower()
        self._regs[name] = val
        self._regs['"'] = val  # unnamed always mirrors
        if is_yank and name == '"':
            self._regs['0'] = val  # yank register
        # (vim also shifts deletes through "1-"9 and keeps "- ; omitted.)
