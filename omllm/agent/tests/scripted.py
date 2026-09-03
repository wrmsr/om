"""Shorthand for driving the agent layer offline through the scripted backend."""
import typing as ta

from ... import llm


##


SCRIPTED_MODEL = llm.Model(key=llm.ModelKey('scripted', 'test'), backend='scripted')


def text_message(text: str, *, stop_reason: llm.StopReason | None = 'stop') -> llm.AiMessage:
    return llm.AiMessage([llm.TextContent(text)], stop_reason=stop_reason)


def tool_call_message(*calls: llm.ToolCall, stop_reason: llm.StopReason | None = 'tool_use') -> llm.AiMessage:
    return llm.AiMessage(list(calls), stop_reason=stop_reason)


def scripted_backend(
        *turns: llm.BackendScriptTurn | llm.AiMessage | BaseException,
        stream: bool = False,
        gate: llm.BackendScriptGate | None = None,
) -> ta.Any:
    """Each turn is a script turn, a message the backend returns, or an exception it raises, in invocation order."""

    script_turns: list[llm.BackendScriptTurn] = []
    for t in turns:
        if isinstance(t, llm.BackendScriptTurn):
            script_turns.append(t)
        elif isinstance(t, llm.AiMessage):
            script_turns.append(llm.BackendScriptTurn(t))
        elif isinstance(t, BaseException):
            script_turns.append(llm.BackendScriptTurn(error=t))
        else:
            raise TypeError(t)

    script = llm.BackendScript(script_turns, gate=gate)

    if stream:
        return llm.ScriptedStreamBackend(SCRIPTED_MODEL, script)
    else:
        return llm.ScriptedImmediateBackend(SCRIPTED_MODEL, script)
