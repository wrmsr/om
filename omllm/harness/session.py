import typing as ta

from .. import agent as agn


##


class Session:
    def __init__(
            self,
            *,
            agent: agn.Agent,
    ) -> None:
        super().__init__()

        self._agent = agent

    async def prompt(
            self,
            input: str | agn.Message | ta.Sequence[agn.Message],  # noqa
    ) -> None:
        await self._agent.prompt(input)
