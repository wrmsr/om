from omcore import dataclasses as dc
from omcore.argparse import all as ap

from ... import agent as agn
from ... import llm
from .argparse import ArgparseCommand
from .base import CommandContext


##


def _format_model_label(model: llm.Model) -> str:
    if (key := model.key) is not None:
        return key.joined
    return model.name or '<unnamed>'


def _model_short_ids(short_ids: llm.ModelShortIds | None) -> tuple[str, ...]:
    return tuple(llm.ModelShortIds.iter(short_ids))


class ModelCommand(ArgparseCommand):
    def __init__(
            self,
            *,
            agent: agn.Agent,
            backends: agn.BackendManager,
            catalog: llm.ModelCatalog,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._backends = backends
        self._catalog = catalog

    @property
    def description(self) -> str:
        return 'Shows, lists, switches, or unloads the active LLM model.'

    def _configure_parser(self, parser: ap.ArgumentParser) -> None:
        super()._configure_parser(parser)

        parser.add_argument('model', nargs='?', help='Model short id or provider::id')
        parser.add_argument('-l', '--list', action='store_true', dest='list_models', help='List available models')
        parser.add_argument('--unload', action='store_true', help='Unload idle cached backends')

    def _loaded_keys(self) -> set[llm.ModelKey]:
        if not isinstance(self._backends, agn.ManagedBackendManager):
            return set()
        return {m.key for m in self._backends.loaded_models if m.key is not None}

    async def _show_current(self, ctx: CommandContext) -> None:
        state = self._agent.state
        lines: list[str] = []

        if (model := state.model) is not None:
            label = _format_model_label(model)
            if model.name and model.name != label:
                lines.append(f'Model: {label} ({model.name})')
            else:
                lines.append(f'Model: {label}')

            if (sids := _model_short_ids(model.short_ids)):
                lines.append(f'Short IDs: {", ".join(sids)}')

            if model.backend is not None:
                lines.append(f'Backend: {model.backend}')

            if (limits := llm.resolve_model_limits(model)) is not None:
                lines.append(f'Limits: context {limits.context:,}, output {limits.output:,}')
        else:
            lines.append('Model: none')

        if isinstance(self._backends, agn.ManagedBackendManager):
            loaded = self._backends.loaded_models
            if loaded:
                parts = []
                for m in loaded:
                    leases = self._backends.active_leases(m)
                    suffix = f' ({leases} active)' if leases else ''
                    parts.append(f'{_format_model_label(m)}{suffix}')
                lines.append(f'Loaded: {", ".join(parts)}')

        await ctx.print('\n'.join(lines))

    async def _list_models(self, ctx: CommandContext) -> None:
        active_key = self._agent.state.model.key if self._agent.state.model is not None else None
        loaded_keys = self._loaded_keys()

        lines: list[str] = []
        for entry in self._catalog.seq:
            marker = '*' if entry.key == active_key else ' '
            sids = _model_short_ids(entry.short_ids)
            sids_s = f'  [{", ".join(sids)}]' if sids else ''
            loaded_s = '  (loaded)' if entry.key in loaded_keys else ''
            lines.append(f'{marker} {entry.key.joined}{sids_s}{loaded_s}')

        await ctx.print('\n'.join(lines) if lines else 'No catalog models available.')

    async def _unload(self, ctx: CommandContext, target: str | None) -> None:
        if not isinstance(self._backends, agn.ManagedBackendManager):
            await ctx.print('Backend unloading is not supported by the active backend manager.')
            return

        if target is None:
            count = await self._backends.unload_idle()
            await ctx.print(f'Unloaded {count} idle backend(s).')
            return

        key: llm.ModelKey | None = llm.ModelKey.try_parse(target)
        if key is None:
            try:
                key = self._catalog[target].key
            except KeyError:
                await ctx.print(f'Unknown model: {target!r}')
                return

        if await self._backends.unload(key):
            await ctx.print(f'Unloaded: {key.joined}')
        elif self._backends.active_leases(key) > 0:
            await ctx.print(f'Cannot unload {key.joined}: backend is currently in use.')
        else:
            await ctx.print(f'Not loaded: {key.joined}')

    async def _switch_model(self, ctx: CommandContext, target: str) -> None:
        try:
            entry = self._catalog[target]
        except KeyError:
            await ctx.print(f'Unknown model: {target!r}. Use /model --list to see available models.')
            return

        new_model = entry.model()
        notes: list[str] = []
        resolved_models: list[llm.Model] = []

        async def update(state: agn.State) -> agn.State:
            # Validate and warm the backend before mutating agent state so a broken/unconfigured model leaves the
            # conversation untouched.
            async with self._backends.acquire_backend(
                llm.ImmediateBackend,  # type: ignore[type-abstract]
                new_model,
            ) as backend:
                resolved = backend.model

            resolved_models.append(resolved)

            turn_config = state.turn_config
            if (
                    turn_config is not None and
                    (llm_options := turn_config.llm_options) is not None and
                    (effort := llm_options.reasoning_effort) is not None
            ):
                with_tools = bool(state.context.tools)
                if effort not in llm.supported_reasoning_efforts(resolved, with_tools=with_tools):
                    turn_config = dc.replace(
                        turn_config,
                        llm_options=dc.replace(llm_options, reasoning_effort=None),
                    )
                    notes.append(f'Cleared unsupported reasoning effort: {effort}')

            # Drop any cached occupancy budget from the previous model so the next turn recomputes against the new
            # model's limits and tokenizer.
            context = dc.replace(state.context, context_budget=None)

            return dc.replace(
                state,
                model=resolved,
                context=context,
                turn_config=turn_config,
            )

        try:
            await self._agent.update_state_exclusively(update)
        except agn.AgentBusyError:
            await ctx.print('Cannot change model: the agent is busy')
            return
        except Exception as e:  # noqa: BLE001
            await ctx.print(f'Cannot change model: {e}')
            return

        [resolved] = resolved_models
        lines = [f'Model: {_format_model_label(resolved)}', *notes]
        await ctx.print('\n'.join(lines))

    async def _run_args(self, ctx: CommandContext, args: ap.Namespace) -> None:
        if args.unload:
            await self._unload(ctx, args.model)
            return

        if args.list_models or (args.model == 'list' and 'list' not in self._catalog):
            await self._list_models(ctx)
            return

        if args.model is None:
            await self._show_current(ctx)
            return

        await self._switch_model(ctx, args.model)
