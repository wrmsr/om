import typing as ta

from .. import SystemPromptPart
from ..systemprompt.types import SystemPromptContributor
from ..systemprompt.types import SystemPromptPriority


##


class FsSystemPromptContributor(SystemPromptContributor):
    def get_system_prompt_parts(self) -> ta.Sequence[SystemPromptPart] | None:
        return [
            # FIXME: just include in tool descriptions, but maybe move cwd here?
            SystemPromptPart(
                SystemPromptPriority.TOOLS,
                'Strongly prefer to use a simple fs tool like `ls`, `glob`, or `read` if available as opposed to using '
                'a more general tool like `bash`. For example to read a line range from a file just use the builtin'
                '`read` tool as opposed to calling `cat` or `set` via the `bash` tool.',
            ),
        ]
