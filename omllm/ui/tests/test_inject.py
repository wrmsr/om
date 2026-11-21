import asyncio
import contextlib
import types
import typing as ta
import uuid

import pytest

from omcore import check
from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ... import llm
from ...agent.inject.backends import BackendBinder
from ...agent.inject.backends import make_opt_async_managed_provider
from ...core import processes as procs
from ..agent.inject.inject import bind_agent_host
from ..agent.inject.inject import bind_root_agent
from ..agent.inject.subagents import bind_subagent_agent
from ..agent.setup import AgentSetup
from ..backends.inject import bind_backends
from ..config import UiConfig
from ..inject.injectors import AgentUiInjector
from .headless import bind_headless_ui
from .headless import headless_ui


##


def test_inject():
    cfg = UiConfig(fs=True, exec=True, web=True, subagents=True)
    els = inj.as_elements(
        bind_agent_host(cfg),
        bind_backends(cfg),
        bind_root_agent(cfg),
    )
    ana = els.analyze()
    deps = ana.known_dependencies_by_key()
    unk = {
        k
        for ks in deps.values()
        if ks
        for k in ks.required
        if k not in deps
    }
    # Only PermissionAsker (imported from UiInjector) and built-in injector keys remain external.
    assert unk <= {
        inj.as_key(agn.PermissionAsker),
        inj.as_key(contextlib.AsyncExitStack),
        inj.as_key(inj.AsyncInjector),
    }, unk


def test_host_and_agent_injectors_have_zero_domain_key_shadowing():
    cfg = UiConfig(fs=True, exec=True, web=True, subagents=True, in_memory=True)

    host_keys = set(inj.as_elements(bind_agent_host(cfg), bind_backends(cfg)).analyze().known_dependencies_by_key())
    root_keys = set(bind_root_agent(cfg).analyze().known_dependencies_by_key())
    subagent_keys = set(bind_subagent_agent(
        cfg,
        run_id=agn.SubagentRunId(uuid.uuid7()),
        profile=agn.GENERAL_SUBAGENT_PROFILE,
        parent_process_scope=ta.cast(procs.ProcessScope, object()),
        progress=None,
    ).analyze().known_dependencies_by_key())

    assert host_keys.isdisjoint(root_keys), host_keys & root_keys
    assert host_keys.isdisjoint(subagent_keys), host_keys & subagent_keys


@pytest.mark.asyncs('asyncio')
async def test_subagent_is_headless_sibling_under_host_injector():
    cfg = UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
        fs=True,
        subagents=True,
    )

    async with headless_ui(bind_headless_ui(cfg)) as hui:
        root_scope = await hui.host_injector[procs.RootProcessScope]

        async with inj.create_asyncio_managed_injector(
            bind_subagent_agent(
                cfg,
                run_id=agn.SubagentRunId(uuid.uuid7()),
                profile=agn.GENERAL_SUBAGENT_PROFILE,
                parent_process_scope=root_scope,
                progress=None,
            ),
            parent=hui.host_injector,
        ) as sub:
            # Shared host singletons.
            assert await sub[agn.BackendManager] is await hui.agent_injector[agn.BackendManager]
            assert await sub[agn.FsOps] is await hui.agent_injector[agn.FsOps]
            assert await sub[agn.FsPathLocks] is await hui.agent_injector[agn.FsPathLocks]
            assert await sub[agn.PermissionsManager] is await hui.agent_injector[agn.PermissionsManager]
            assert await sub[procs.ProcessManager] is await hui.agent_injector[procs.ProcessManager]

            # Distinct per-agent singletons.
            assert await sub[agn.Agent] is not await hui.agent_injector[agn.Agent]
            assert await sub[agn.TurnRunner] is not await hui.agent_injector[agn.TurnRunner]
            assert await sub[agn.ToolInvoker] is not await hui.agent_injector[agn.ToolInvoker]
            assert await sub[agn.ToolSet] is not await hui.agent_injector[agn.ToolSet]
            assert await sub[agn.SystemPromptManager] is not await hui.agent_injector[agn.SystemPromptManager]
            assert await sub[procs.ProcessScope] is not await hui.agent_injector[procs.ProcessScope]

            # Root agent has an AgentUiInjector; subagents run headlessly without one.
            assert await hui.agent_injector[AgentUiInjector] is not None
            with pytest.raises(inj.UnboundKeyError):
                await sub[AgentUiInjector]


@pytest.mark.asyncs('asyncio')
async def test_multi_agent_tenancy_shares_managed_async_cm_backend():
    lifecycle: list[str] = []
    both_entered = asyncio.Event()
    in_flight = 0
    max_in_flight = 0

    class _SharedModelBackend(llm.ImmediateBackend, lang.SelfAsyncContextManaged):
        def __init__(self, model: llm.Model) -> None:
            super().__init__()

            self._model = model

        @property
        def model(self) -> llm.Model:
            return self._model

        async def __aenter__(self) -> ta.Self:
            lifecycle.append('enter')
            return self

        async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: types.TracebackType | None,
        ) -> None:
            lifecycle.append('exit')

        async def immediate(self, context: llm.Context, options: llm.Options | None = None) -> llm.AiMessage:
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            if in_flight == 2:
                both_entered.set()
            await both_entered.wait()
            in_flight -= 1

            user_msg = check.isinstance((context.messages or ())[-1], llm.UserMessage)
            return llm.AiMessage([llm.TextContent(f'reply:{user_msg.content}')], stop_reason='stop')

    class _SharedBinder(BackendBinder):
        def bind_backend(self, cls: type[llm.Backend], model: llm.Model) -> inj.Elements:
            return inj.as_elements(
                inj.bind(
                    cls,
                    singleton=True,
                    to_async_fn=make_opt_async_managed_provider(_SharedModelBackend),
                ),
            )

    cfg = UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
    )

    async with headless_ui(bind_headless_ui(
        cfg,
        host_rewriter=inj.overrider(
            inj.bind(BackendBinder, to_const=_SharedBinder()),
        ),
    )) as hui:
        mgr = check.isinstance(await hui.host_injector[agn.BackendManager], agn.ManagedBackendManager)
        assert lifecycle == ['enter']  # Opened once during root AgentSetup.

        # Stand up a second sibling tenant agent under the same HostInjector.
        async with inj.create_asyncio_managed_injector(
            bind_root_agent(cfg),
            parent=hui.host_injector,
        ) as tenant2:
            agent2 = await tenant2[agn.Agent]
            await (await tenant2[AgentSetup]).run()

            assert agent2 is not hui.agent

            r1, r2 = await asyncio.gather(
                hui.agent.prompt('from-a'),
                agent2.prompt('from-b'),
            )

            m1 = check.isinstance((r1.context.messages or ())[-1], llm.AiMessage)
            m2 = check.isinstance((r2.context.messages or ())[-1], llm.AiMessage)
            assert check.isinstance(check.single(m1.content), llm.TextContent).text == 'reply:from-a'
            assert check.isinstance(check.single(m2.content), llm.TextContent).text == 'reply:from-b'
            assert max_in_flight == 2
            assert lifecycle == ['enter']  # Loaded once and shared across both concurrent sibling agents!
            assert mgr.active_leases(check.not_none(hui.agent.state.model)) == 0

    # Exiting the host injector closes the shared managed backend cleanly.
    assert lifecycle == ['enter', 'exit']
