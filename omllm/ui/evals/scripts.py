import json

from ... import llm


##


def load_script(path: str | None) -> llm.BackendScript:
    if path is None:
        return llm.BackendScript([
            llm.BackendScriptTurn(llm.AiMessage([
                llm.ToolCall('inspect', 'bash', {'command': 'pwd'}),
            ], stop_reason='tool_use')),
            llm.BackendScriptTurn(llm.AiMessage([
                llm.TextContent('Offline scripted smoke test complete.'),
            ], stop_reason='stop')),
        ])

    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    if not isinstance(raw, list) or not raw:
        raise ValueError('Script must be a nonempty JSON array of turns')
    turns = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) - {'text', 'tool_calls'}:
            raise ValueError(f'Invalid script turn {index}')
        if ('text' in item) == ('tool_calls' in item):
            raise ValueError(f'Script turn {index} needs text or tool_calls')
        if 'text' in item:
            if not isinstance(item['text'], str):
                raise ValueError(f'Script turn {index} text must be a string')
            message = llm.AiMessage([llm.TextContent(item['text'])], stop_reason='stop')
        else:
            calls = item['tool_calls']
            if not isinstance(calls, list) or not calls:
                raise ValueError(f'Script turn {index} tool_calls must be a nonempty array')
            content = []
            for call_index, call in enumerate(calls):
                if not isinstance(call, dict) or set(call) != {'name', 'args'}:
                    raise TypeError(f'Invalid tool call in script turn {index}')
                if not isinstance(call['name'], str) or not isinstance(call['args'], dict):
                    raise TypeError(f'Invalid tool call in script turn {index}')
                content.append(llm.ToolCall(f'script-{index}-{call_index}', call['name'], call['args']))
            message = llm.AiMessage(content, stop_reason='tool_use')
        turns.append(llm.BackendScriptTurn(message))
    return llm.BackendScript(turns)
