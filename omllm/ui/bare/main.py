import asyncio
import functools
import sys

from omdev.home.secrets import load_secrets

from ... import agent as ag
from ... import llm


##


async def _a_main() -> None:
    model_key = llm.ModelKey('openai', 'gpt-5.4-mini')
    api_key_name = 'openai_api_key'
    backend_cls = llm.OpenaiCompletionsImmediateBackend

    #

    svc = backend_cls(
        llm.default_model_catalog()[model_key],  # noqa
        api_key=load_secrets().get(api_key_name),
    )

    async def on_event(ev: ag.Event) -> None:
        if isinstance(ev, ag.TurnEndEvent):
            print(ev.message)

    agent = ag.Agent(
        backends=ag.DictBackendManager({llm.ImmediateBackend: {None: svc}}),  # type: ignore
        sink=on_event,
    )

    #

    if sys.stdin.isatty():
        try:
            import readline  # noqa
        except ImportError:
            pass

    while True:
        entry = await asyncio.to_thread(functools.partial(input, '> '))

        if entry == '/quit':
            break

        print(entry)

        await agent.prompt(entry)


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
