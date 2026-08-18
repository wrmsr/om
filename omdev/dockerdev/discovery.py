"""
Finding running dockerdev containers, and building a process-manager target to exec into one. This is the seam a
higher-level "run command X in dev container Y and stream it" API (in omllm) will sit on.
"""

from omcore.docker import cli as docker_cli

from .run import LABEL_PREFIX


##


def find_dev_containers() -> list[docker_cli.PsItem]:
    """Running containers launched by dockerdev (carrying the `om.dockerdev` label), newest docker order."""

    return [
        pi
        for pi in docker_cli.cli_ps()
        if LABEL_PREFIX in (pi.labels or '')
    ]


def find_dev_container_id(name: str | None = None) -> str | None:
    """
    The id of a single running dev container, or None if there isn't exactly one match. With `name`, matches a
    container whose names contain it (dockerdev does not set `--name` today, so this usually matches on id prefix).
    """

    cs = find_dev_containers()
    if name is not None:
        cs = [c for c in cs if name in c.names or c.id.startswith(name)]
    if len(cs) != 1:
        return None
    return cs[0].id
