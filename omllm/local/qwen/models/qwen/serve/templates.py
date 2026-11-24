"""
What the Qwen checkpoints' chat templates are seen to take and to say, beside the formats themselves (chat.py): the
reasoning-effort switch and the instruction each level puts in the system turn, and the template's plain rendering of
a conversation without tools, for the command-line tools and the bench.
"""
from ....tokenizer import Tokenizer


##


# Reasoning effort, for a checkpoint whose chat template takes that switch (`takes_reasoning_effort`). With
# thinking on, the template opens the system turn with one instruction for the level -- none at 'medium' -- and its
# default is the highest; with thinking off it says nothing. The levels and the wording are the template's, which is
# what the model was trained against: observed by rendering it (tests/oracle.py), as the tool preamble in chat.py is.
REASONING_EFFORT_INSTRUCTIONS: dict[str, str | None] = {
    'low': (
        'Reasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion '
        'without unnecessary elaboration.'
    ),
    'medium': None,
    'xhigh': (
        'Reasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, '
        'consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.'
    ),
}

DEFAULT_REASONING_EFFORT = 'xhigh'


def takes_reasoning_effort(tok: Tokenizer) -> bool:
    """Whether the checkpoint's chat template takes a `reasoning_effort` (qwen3.8's does; qwen3.5's does not)."""

    return 'reasoning_effort' in (tok.chat_template or '')


def reasoning_instruction(tok: Tokenizer, effort: str | None = None, think: bool = True) -> str | None:
    """
    What the checkpoint's template puts at the head of the system turn for a reasoning effort (None: the template's
    default, `DEFAULT_REASONING_EFFORT`), or None when it puts nothing there: thinking off, the level that has no
    instruction, or a template without the switch.
    """

    if effort is not None and effort not in REASONING_EFFORT_INSTRUCTIONS:
        raise ValueError(f'reasoning effort must be one of {", ".join(REASONING_EFFORT_INSTRUCTIONS)}: {effort!r}')
    if not think or not takes_reasoning_effort(tok):
        return None
    return REASONING_EFFORT_INSTRUCTIONS[effort or DEFAULT_REASONING_EFFORT]


def apply_chat(
        tok: Tokenizer,
        messages: list[dict],
        think: bool = False,
        reasoning_effort: str | None = None,
        *,
        open_think: bool = False,
        continuation: bool = False,
) -> str:
    """
    Minimal Qwen3.5 ChatML rendering (no tools). Set think=False to disable reasoning; with it on, a checkpoint whose
    template takes a reasoning effort gets that level's instruction (`reasoning_instruction`) -- unless the messages
    are the `continuation` of a conversation already rendered, whose system turn has it -- and `open_think` ends the
    prompt with the opened reasoning block, as the checkpoints' templates do (the generation then starts inside it).
    """

    instr = None if continuation else reasoning_instruction(tok, reasoning_effort, think)
    out: list[str] = []
    for i, m in enumerate(messages):
        content = m['content']
        if instr is not None and i == 0:
            if m['role'] == 'system':
                content = f'{instr}\n\n{content}'
            else:
                out.append(f'<|im_start|>system\n{instr}<|im_end|>\n')
        out.append(f"<|im_start|>{m['role']}\n{content}<|im_end|>\n")
    out.append('<|im_start|>assistant\n')
    if not think:
        out.append('<think>\n\n</think>\n\n')
    elif open_think:
        out.append('<think>\n')
    return ''.join(out)
