from omcore.argparse import all as ap

from ... import agent as agn
from ..skills.catalogs import SkillCatalog
from ..skills.reading import SkillReader
from .base import CommandContext
from .classes import CommandClass


##


class SkillsCommand(CommandClass):
    def __init__(self, *, agent: agn.Agent, catalog: SkillCatalog, reader: SkillReader) -> None:
        super().__init__()

        self._agent = agent
        self._catalog = catalog
        self._reader = reader

    @property
    def description(self) -> str:
        return 'Lists, shows, or applies a configured host skill.'

    def _configure_parser(self, parser: ap.ArgumentParser) -> None:
        super()._configure_parser(parser)

        sub = parser.add_subparsers(dest='action')
        sub.add_parser('list')
        show = sub.add_parser('show')
        show.add_argument('name')
        show.add_argument('path', nargs='?', default='SKILL.md')
        use = sub.add_parser('use')
        use.add_argument('name')
        use.add_argument('task', nargs='*')

    async def _run_args(self, ctx: CommandContext, args: ap.Namespace) -> None:
        if args.action is None or args.action == 'list':
            await ctx.print('\n'.join([
                *([f'{s.name}: {s.description}' for s in self._catalog.skills] or ['No skills configured.']),
                *[f'{d.path}: {d.message}' for d in self._catalog.diagnostics],
            ]))
            return

        text = await self._reader.read(args.name, args.path if args.action == 'show' else 'SKILL.md')
        if args.action == 'show':
            await ctx.print(text)
            return

        await self._agent.prompt('\n\n'.join([
            f'Use the configured skill {args.name}. Its full instructions follow:',
            text,
            'Task: ' + (' '.join(args.task) or 'Apply this skill to the current task.'),
        ]))
