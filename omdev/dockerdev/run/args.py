import re
import typing as ta
import uuid

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh


##
# Args


def _coerce_env_secret(v: str | tuple[str, str]) -> str | tuple[str, str]:
    if isinstance(v, str):
        check.in_(v, (v.lower(), v.upper()))
        return check.non_empty_str(v)
    elif isinstance(v, tuple):
        return col.tuple_of(check.non_empty_str, check.non_empty_str)(v)
    else:
        raise TypeError(v)


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
@msh.update_field_options(omit_if=lang.is_none)
class RunArgs:
    names: ta.Sequence[str] | None = dc.xfield(None, coerce=col.seq_of_or_none(check.non_empty_str))

    verbose: bool | None = None

    no_rm: bool | None = None
    no_interactive: bool | None = None
    no_tty: bool | None = None

    detach: bool | None = None

    mounts: ta.Sequence[str] | None = dc.xfield(None, coerce=col.opt_seq_of(check.non_empty_str))
    mount_docker_sock: bool | None = None

    mount_caches: bool | None = None

    mount_persist: bool | None = None

    mount_git: bool | None = None
    clone_mount_git: bool | None = None

    privileged: bool | None = None

    cuda: bool | None = None

    offline: bool | None = None

    no_host_platform: bool | None = None

    autoexecs: ta.Sequence[str] | None = dc.xfield(None, coerce=col.opt_seq_of(check.of_isinstance(str)))

    x11: bool | None = None

    id: uuid.UUID | None = None
    no_id_label: bool | None = None

    env_secrets: ta.Sequence[str | tuple[str, str]] | None = dc.xfield(
        None,
        coerce=col.opt_seq_of(_coerce_env_secret),
    )
    non_strict_env_secrets: bool | None = None
    env_secret_pats: ta.Sequence[re.Pattern[str]] | None = dc.xfield(
        None,
        coerce=col.opt_seq_of(check.of_isinstance(re.Pattern)),
    )

    shift_uid: tuple[int, int] | None = None

    unknown_args: ta.Sequence[str] | None = dc.xfield(None, coerce=col.opt_seq)
    extra_args: ta.Sequence[str] | None = dc.xfield(None, coerce=col.opt_seq)
