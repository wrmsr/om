import typing as ta

from omcore import check
from omcore import lang
from omcore import marshal as msh
from omcore.argparse import all as ap
from omcore.formats import json5

from ... import agent as agn
from ...core import ui
from .base import CommandContext
from .classes import ParserCommandClass


##


class PermissionsCommand(ParserCommandClass):
    def __init__(self, permissions: agn.PermissionsManager) -> None:
        super().__init__()

        self._permissions = permissions

    #

    _PERMISSION_STATE_COLORS: ta.ClassVar[ta.Mapping[agn.PermissionState, ui.TextColor]] = {  # noqa
        agn.PermissionState.DENY: 'red',
        agn.PermissionState.ASK: 'yellow',
        agn.PermissionState.ALLOW: 'green',
    }

    _TOOL_PERMISSION_STATE_NAME_LEN: ta.ClassVar = max(len(tps.name) for tps in agn.PermissionState)

    def _render_rule(self, rmd: str, r: agn.PermissionRule) -> ui.CanText:
        sp = ' ' * 2
        return list(lang.interleave(sp, [
            rmd,
            ui.Text.style(
                r.result.name.lower().ljust(self._TOOL_PERMISSION_STATE_NAME_LEN),
                bold=True,
                color=self._PERMISSION_STATE_COLORS[r.result],
            ),
            ui.JsonText(
                msh.marshal(r.matcher, agn.PermissionMatcher),
                ui.JsonTextStyle(
                    mode='compact',
                    five=True,
                    unquote_idents=True,
                ),
            ),
        ]))

    def _render_rules(self, rs: ta.Iterable[tuple[str, agn.PermissionRule]]) -> ui.CanText:
        return ui.Text.join('\n', [
            self._render_rule(rmd, r)
            for rmd, r in rs
        ])

    #

    @ap.cmd(
        name='list',
        default=True,
    )
    async def _run_list(self, ctx: CommandContext, args: ap.Namespace) -> None:
        rules = self._permissions.get_rules()
        if not rules:
            await ctx.print('No permissions set')
            return

        await ctx.print(self._render_rules(rules.by_min_digest.items()), '\n')

    #

    @ap.cmd(
        ap.arg('state', choices=('allow', 'ask', 'deny')),
        ap.arg('kind'),
        ap.arg('body'),
        name='add',
    )
    async def _run_add(self, ctx: CommandContext, args: ap.Namespace) -> None:
        body = json5.loads(args.body or '{}', allow_ident_values=True)
        dct: dict = {check.non_empty_str(args.kind): body}
        matcher = msh.unmarshal(dct, agn.PermissionMatcher)
        rule = agn.PermissionRule(matcher, agn.PermissionState[args.state.upper()])

        self._permissions.add_rule(rule)

        rmd = self._permissions.get_rules().min_digests[rule]
        await ctx.print(self._render_rule(rmd, rule), '\n')
