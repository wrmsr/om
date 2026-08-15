import itertools
import os
import shlex
import typing as ta

from omcore import check
from omcore import lang
from omcore.argparse import all as ap
from omcore.formats.json import all as json

from ..cli.types import CliModule


with lang.auto_proxy_import(globals()):
    import concurrent.futures as cf
    import re
    import subprocess


##


DEFAULT_DELIMITER = ' '


def _print_list(
        lst: ta.Iterable[str],
        *,
        delimiter: str | None = None,
) -> None:
    check.not_isinstance(lst, str)

    if delimiter is None:
        delimiter = DEFAULT_DELIMITER

    for e in lst:
        check.not_in(delimiter, e)

    print(delimiter.join(lst))


##


class ShellCli(ap.Cli):
    @ap.cmd(
        ap.arg('strs', nargs='*'),
        ap.arg('--delimiter', '-d'),
    )
    def quote(self) -> None:
        _print_list(
            [shlex.quote(e) for e in self.args.strs],
            delimiter=self.args.delimiter,
        )

    #

    _PREFIX_OR_INTERLEAVE_ARGS: ta.ClassVar[ta.Sequence[ta.Any]] = [
        ap.arg('--quote', '-q', action='store_true'),
        ap.arg('--delimiter', '-d'),
    ]

    def _prefix_or_interleave(
            self,
            mode: ta.Literal['prefix', 'interleave'],
            separator: str,
            items: ta.Iterable[str],
    ) -> None:
        lst = []

        for i, e in enumerate(check.not_isinstance(items, str)):
            if i or mode != 'interleave':
                lst.append(separator)

            if self.args.quote:
                e = shlex.quote(e)

            lst.append(e)

        _print_list(
            lst,
            delimiter=self.args.delimiter,
        )

    @ap.cmd(
        ap.arg('prefix'),
        ap.arg('items', nargs='*'),
        *_PREFIX_OR_INTERLEAVE_ARGS,
    )
    def prefix(self) -> None:
        self._prefix_or_interleave(
            'prefix',
            self.args.prefix,
            self.args.items,
        )

    @ap.cmd(
        ap.arg('separator'),
        ap.arg('items', nargs='*'),
        *_PREFIX_OR_INTERLEAVE_ARGS,
    )
    def interleave(self) -> None:
        self._prefix_or_interleave(
            'interleave',
            self.args.separator,
            self.args.items,
        )

    #

    @ap.cmd(accepts_unknown=True)
    def argv(self) -> None:
        print(json.dumps_pretty(self.unknown_args))

    #

    class _DoAllCmd(ta.NamedTuple):
        cmd: str
        env: ta.Mapping[str, str] | None

    @ap.cmd(
        ap.arg('-e', '--env', action='append'),
        ap.arg('-E', '--env-list', action='append'),
        ap.arg('-p', '--placeholder', action='append'),
        ap.arg('-P', '--placeholder-list', action='append'),

        ap.arg('-j', '--jobs', type=int),

        ap.arg('--cmd-timeout', type=float),
        ap.arg('--total-timeout', type=float),

        ap.arg('cmd', nargs=ap.REMAINDER),
    )
    def doall(self) -> None:
        # TODO:
        #  - shared list of live subprocesses
        #  - configurable cancel policy
        #  - --shell toggle
        #  - interleave / tag / prepend / somehow multiplex stdout/err

        def collect_axis(
                raw_lst: ta.Sequence[str] | None,
                raw_lst_lst: ta.Sequence[str] | None,
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

        envs = collect_axis(self.args.env, self.args.env_list)  # noqa
        phs = collect_axis(self.args.placeholder, self.args.placeholder_list)  # noqa

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

        cmd_args = self.args.cmd
        if cmd_args and cmd_args[0] == '--':
            cmd_args = cmd_args[1:]
        base_cmd = check.non_empty_str(' '.join(cmd_args)).replace('%%', '%')

        def prep_cfg(cfg: ta.Sequence[tuple[tuple[str, str], str]]) -> ShellCli._DoAllCmd:
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

            return ShellCli._DoAllCmd(
                cmd,
                env=env or None,
            )

        all_cmds = list(map(prep_cfg, all_cfgs))

        #

        def run_cmd(cmd: ShellCli._DoAllCmd) -> None:
            subprocess.check_call(  # noqa
                cmd.cmd,
                env={**os.environ, **(cmd.env or {})},
                shell=True,
                stdin=subprocess.DEVNULL,
                timeout=self.args.cmd_timeout,
            )

        if (jobs := self.args.jobs) is None:
            jobs = os.process_cpu_count()

        with cf.ThreadPoolExecutor(max_workers=jobs) as exe:
            futs: list[cf.Future] = [
                exe.submit(run_cmd, cmd)
                for cmd in all_cmds
            ]

            total_timeout = lang.Timeout.of(self.args.total_timeout)
            for fut in futs:
                fut.result(timeout=total_timeout.remaining_or(None))


##


# @om-manifest
_CLI_MODULE = CliModule(['shell', 'sh'], __name__)


def _main() -> None:
    ShellCli().cli_run_and_exit()


if __name__ == '__main__':
    _main()
