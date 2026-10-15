# ruff: noqa: UP006 UP007 UP045
# @om-lite
import argparse
import concurrent.futures as cf
import itertools
import os
import re
import subprocess
import typing as ta

from omcore.lite.check import check
from omcore.lite.timeouts import Timeout


##


class _DoAllCmd(ta.NamedTuple):
    cmd: str
    env: ta.Optional[ta.Mapping[str, str]]


def doall(args) -> None:
    # TODO:
    #  - shared list of live subprocesses
    #  - configurable cancel policy
    #  - --shell toggle
    #  - interleave / tag / prepend / somehow multiplex stdout/err

    def collect_axis(
            raw_lst: ta.Optional[ta.Sequence[str]],
            raw_lst_lst: ta.Optional[ta.Sequence[str]],
    ) -> dict[str, list[str]]:
        if not raw_lst and not raw_lst_lst:
            return {}

        out: dict[str, list[str]] = {}

        for s in raw_lst or []:
            k, v = s.split('=')
            out.setdefault(check.non_empty_str(k), []).append(v)

        for s in raw_lst_lst or []:
            k, v = s.split('=')
            vs = [ss for s in v.split() if (ss := s.strip())]
            out.setdefault(check.non_empty_str(k), []).extend(vs)

        return out

    envs = collect_axis(args.env, args.env_list)  # noqa
    phs = collect_axis(args.placeholder, args.placeholder_list)  # noqa

    #

    all_axes = [
        ((tag, k), vs)
        for tag, dct in [
            ('e', envs),
            ('p', phs),
        ]
        for k, vs in dct.items()
    ]
    all_axis_ks, all_axis_vs = zip(*all_axes)

    all_cfgs = [
        list(zip(all_axis_ks, prod_vs, strict=True))
        for prod_vs in itertools.product(*all_axis_vs)
    ]

    for ph in phs:
        check.not_none(re.fullmatch(r'[a-zA-Z0-9_][a-zA-Z0-9_\-]*', ph))
    ph_ranks = {ph: i for i, ph in enumerate(sorted(phs, key=lambda ph: (-len(ph), ph)))}

    cmd_args = args.cmd
    if cmd_args and cmd_args[0] == '--':
        cmd_args = cmd_args[1:]
    base_cmd = check.non_empty_str(' '.join(cmd_args)).replace('%%', '%')

    def prep_cfg(cfg: ta.Sequence[tuple[tuple[str, str], str]]) -> _DoAllCmd:
        cmd = base_cmd
        env: dict[str, str] = {}
        ph_vs: dict[str, str] = {}

        for (tag, k), v in cfg:
            if tag == 'e':
                env[k] = v
            elif tag == 'p':
                ph_vs[k] = v
            else:
                raise ValueError(tag)

        for ph_k in sorted(ph_vs, key=ph_ranks.__getitem__):
            cmd = cmd.replace(f'%{ph_k}', ph_vs[ph_k])

        return _DoAllCmd(
            cmd,
            env=env or None,
        )

    all_cmds = list(map(prep_cfg, all_cfgs))

    #

    def run_cmd(cmd: _DoAllCmd) -> None:
        subprocess.check_call(  # noqa
            cmd.cmd,
            env={**os.environ, **(cmd.env or {})},
            shell=True,
            stdin=subprocess.DEVNULL,
            timeout=args.cmd_timeout,
        )

    if (jobs := args.jobs) is None:
        if (jobs_fn := getattr(os, 'process_cpu_count', None)) is None:
            import multiprocessing as mp

            jobs_fn = mp.cpu_count

        jobs = jobs_fn()

    with cf.ThreadPoolExecutor(max_workers=jobs) as exe:
        futs: list[cf.Future] = [
            exe.submit(run_cmd, cmd)
            for cmd in all_cmds
        ]

        total_timeout = Timeout.of(args.total_timeout)
        for fut in futs:
            fut.result(timeout=total_timeout.remaining_or(None))


def _main(argv=None) -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--env', action='append')
    parser.add_argument('-E', '--env-list', action='append')
    parser.add_argument('-p', '--placeholder', action='append')
    parser.add_argument('-P', '--placeholder-list', action='append')

    parser.add_argument('-j', '--jobs', type=int)

    parser.add_argument('--cmd-timeout', type=float)
    parser.add_argument('--total-timeout', type=float)

    parser.add_argument('cmd', nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)

    doall(args)


# @om-manifest omdev.cli.CliModule(['doall'], __name__)


if __name__ == '__main__':
    _main()
