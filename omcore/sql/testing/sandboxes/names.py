import re
import uuid

from .... import dataclasses as dc
from .... import lang
from .config import SandboxesConfig
from .errors import SandboxNameError


##


# A run id is a uuid7 rendered with its hyphens: time-ordered, and visually distinct from any other hex.
RUN_ID_PAT = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

# The tightest identifier limit among the target backends (postgres' NAMEDATALEN - 1); mysql allows 64.
MAX_NAME_LENGTH = 63


def new_run_id() -> str:
    return str(uuid.uuid7())


@dc.dataclass(frozen=True)
class ParsedSandboxName(lang.Final):
    run_id: str
    seq: int


class SandboxNames(lang.Final):
    """The one place sandbox names are minted and validated. No destructive statement ever names an unvalidated name."""

    def __init__(self, cfg: SandboxesConfig) -> None:
        super().__init__()

        self._cfg = cfg
        self._pat = re.compile(f'^{re.escape(cfg.prefix)}({RUN_ID_PAT})_([0-9]+)$')
        self._run_id_pat = re.compile(f'^{RUN_ID_PAT}$')

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    def check_run_id(self, run_id: str) -> str:
        if self._run_id_pat.fullmatch(run_id) is None:
            raise SandboxNameError(f'not a run id: {run_id!r}')
        return run_id

    def sandbox_name(self, run_id: str, seq: int) -> str:
        return self.check_sandbox_name(f'{self._cfg.prefix}{self.check_run_id(run_id)}_{seq}')

    def parse_sandbox_name(self, name: str) -> ParsedSandboxName | None:
        if (m := self._pat.fullmatch(name)) is None:
            return None
        if len(name.encode('utf-8')) > MAX_NAME_LENGTH:
            return None
        return ParsedSandboxName(m.group(1), int(m.group(2)))

    def check_sandbox_name(self, name: str) -> str:
        if self.parse_sandbox_name(name) is None:
            raise SandboxNameError(f'not a sandbox name: {name!r}')
        return name

    def is_internal_name(self, name: str) -> bool:
        return name.startswith(self._cfg.internal_prefix)

    def application_name(self, run_id: str) -> str:
        # Stamped on every session a run opens, so a reaper can tell a dead run from an idle one.
        return f'{self._cfg.prefix}{self.check_run_id(run_id)}'
