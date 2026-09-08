import typing as ta

from omcore import check
from omcore import collections as col
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

    def _render_rule(
            self,
            rule: agn.PermissionRule,
            *,
            prefix_cols: lang.SequenceNotStr[str] | None = None,
    ) -> ui.CanText:
        sp = ' ' * 2
        return list(lang.interleave(sp, [
            *(prefix_cols or []),
            ui.Text.style(
                rule.result.name.lower().ljust(self._TOOL_PERMISSION_STATE_NAME_LEN),
                bold=True,
                color=self._PERMISSION_STATE_COLORS[rule.result],
            ),
            ui.JsonText(
                msh.marshal(rule.matcher, agn.PermissionMatcher),
                ui.JsonTextStyle(
                    mode='compact',
                    five=True,
                    unquote_idents=True,
                ),
            ),
        ]))

    def _render_rules(
            self,
            rules: agn.PermissionRules,
            *,
            filter: ta.Callable[[agn.PermissionRule], bool] | None = None,  # Noqa
    ) -> ui.CanText:
        ij = len(str(len(rules)))
        return ui.Text.join('\n', [
            self._render_rule(
                r,
                prefix_cols=[
                    f'#{str(i).ljust(ij)}',
                    rmd,
                ],
            )
            for i, (rmd, r) in enumerate(rules.by_min_digest.items())
            if (filter is None or filter(r))
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

        await ctx.print(self._render_rules(rules), '\n')

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

        new_rules = self._permissions.update_rules(lambda old_rules: agn.PermissionRules([*old_rules, rule]))

        rmd = new_rules.min_digests[rule]
        await ctx.print(self._render_rules(new_rules, filter=lambda r: r is rmd), '\n')

    #

    @ap.cmd(
        ap.arg('digest', nargs='+'),
        name='rm',
    )
    async def _run_rm(self, ctx: CommandContext, args: ap.Namespace) -> None:
        def update(old_rules: agn.PermissionRules) -> agn.PermissionRules:
            rm_rules = col.IdentitySet(r for d in args.digest if (r := old_rules.get(d)) is not None)
            return agn.PermissionRules([r for r in old_rules if r not in rm_rules])

        self._permissions.update_rules(update)

    #

    @ap.cmd(
        name='clear',
    )
    async def _run_clear(self, ctx: CommandContext, args: ap.Namespace) -> None:
        self._permissions.update_rules(lambda _: agn.PermissionRules())
