import dataclasses as dc
import os.path
import typing as ta

from omcore import check

from ...py.tokens import all as tks


##


@dc.dataclass(frozen=True, kw_only=True)
class Import:
    mod: str | None
    mod_src_path: str | None

    item: str | None
    as_: str | None

    src_path: str
    line: int

    toks: tks.Tokens = dc.field(repr=False)


def make_import(
        lts: tks.Tokens,
        *,
        src_path: str,
        mounts: ta.Mapping[str, str],
) -> Import | None:
    if not lts:
        return None
    ft = lts[0]

    if ft.name != 'NAME' or ft.src not in ('import', 'from'):
        return None

    ml = []
    il: list[str] | None = None
    as_ = None
    for tok in (it := iter(tks.ignore_ws(lts[1:]))):
        if tok.name in ('NAME', 'OP'):
            if tok.src == 'as':
                check.none(as_)
                nt = next(it)
                check.equal(nt.name, 'NAME')
                as_ = nt.src
            elif tok.src == 'import':
                check.equal(ft.src, 'from')
                il = []
            elif il is not None:
                il.append(tok.src)
            else:
                ml.append(tok.src)
        else:
            raise Exception(tok)

    mod = ''.join(ml)
    item = ''.join(il) if il is not None else None

    mod_src_path: str | None
    out_mod: str | None

    if mod.startswith('.'):
        parts = mod.split('.')
        nd = len(parts) - parts[::-1].index('')
        if src_mount := check.opt_single([mk for mk, mp in mounts.items() if os.path.commonpath([src_path, mp]) == mp]):
            rel_mnt = mounts[src_mount]
            mod_ps = [src_mount, *os.path.relpath(src_path, start=rel_mnt).split('/')[:-1]]
            mod = '.'.join([*mod_ps[:-(nd - 1) or None], *parts[nd:]])
            ps = mod.split('.')
            mod_src_path = os.path.abspath(os.path.join(
                rel_mnt,
                *ps[1:-1],
                ps[-1] + '.py',
            ))
            out_mod = mod
        else:
            mod_src_path = os.path.abspath(os.path.join(
                os.path.dirname(src_path),
                '../' * (nd - 1),
                *parts[nd:-1],
                parts[-1] + '.py',
            ))
            out_mod = None

    elif (mnt := mounts.get(mod.partition('.')[0])) is not None:
        ps = mod.split('.')
        mod_src_path = os.path.abspath(os.path.join(
            mnt,
            *ps[1:-1],
            ps[-1] + '.py',
        ))
        out_mod = mod

    else:
        mod_src_path = None
        out_mod = mod

    return Import(
        mod=out_mod,
        mod_src_path=mod_src_path,

        item=item,
        as_=as_,

        src_path=src_path,
        line=check.not_none(ft.line),

        toks=lts,
    )
