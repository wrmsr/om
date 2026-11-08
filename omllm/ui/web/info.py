import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ... import agent as agn
from ..commands.manager import CommandsManager
from ..paths import get_agent_cwd
from .feed.feed import Feed
from .submissions import Submitter


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class WebCommandInfo:
    name: str
    description: str | None = None
    can_run_while_busy: bool = False


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class WebSubmissionInfo:
    id: str
    kind: str
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class WebInfo:
    """What the page is told of the session when it loads - and again whenever it asks."""

    session_id: str | None = None
    model: str | None = None
    cwd: str | None = None

    commands: ta.Sequence[WebCommandInfo] = ()

    busy: bool = False
    current: WebSubmissionInfo | None = None

    last_seq: int = 0


class WebInfoBuilder:
    def __init__(
            self,
            *,
            agent: agn.Agent,
            session_id: agn.SessionId | None = None,
            commands: CommandsManager,
            submitter: Submitter,
            feed: Feed,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._session_id = session_id
        self._commands = commands
        self._submitter = submitter
        self._feed = feed

    def build_info(self) -> WebInfo:
        model: str | None = None
        if (m := self._agent.state.model) is not None and (mk := m.key) is not None:
            model = mk.joined

        current: WebSubmissionInfo | None = None
        if (sub := self._submitter.current) is not None:
            current = WebSubmissionInfo(
                id=sub.id,
                kind=sub.kind,
                text=sub.text,
            )

        return WebInfo(
            session_id=str(self._session_id.v) if self._session_id is not None else None,
            model=model,
            cwd=get_agent_cwd(self._agent),

            commands=[
                WebCommandInfo(
                    name=name,
                    description=cmd.description,
                    can_run_while_busy=cmd.can_run_while_busy,
                )
                for name, cmd in sorted(self._commands.get_commands().items())
            ],

            busy=self._submitter.is_busy,
            current=current,

            last_seq=self._feed.last_seq,
        )
