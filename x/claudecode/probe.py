"""
probe_claude_code.py - zero-dependency smoke test for the stdio protocol.

Run against YOUR pinned CLI before building on any of the undocumented bits. It verifies, in order:
  1. the initialize handshake + prints the `capabilities` array from system/init
  2. an `sdk` MCP server round-trip: tools/list + a tools/call to a fake tool
  3. shouldQuery:false history replay: inject a prior [user, assistant] exchange as non-querying frames, then ask a
     question that can only be answered if that history is actually in context ("what number did I say?")

Env:
  OM_CLAUDE_CLI (default "claude")
  ANTHROPIC_API_KEY or a logged-in CLI.

If step 3 fails, fall back to real --session-id/--resume for multi-turn and keep manual replay for cold-start only.
"""
import asyncio
import json
import os
import sys


##


def frame(obj) -> bytes:
    return (json.dumps(obj) + '\n').encode()


async def main() -> int:
    cli = os.environ.get('OM_CLAUDE_CLI', 'claude')

    argv = [
        cli, '--print',
        '--output-format', 'stream-json',
        '--input-format', 'stream-json',
        '--verbose', '--include-partial-messages',
        '--bare', '--tools', '',
        '--strict-mcp-config', '--no-session-persistence',
        '--permission-mode', 'bypassPermissions',
        '--system-prompt', 'You are a terse test harness. Answer in one short sentence.',
        '--mcp-config', json.dumps({'mcpServers': {'om': {'type': 'sdk', 'name': 'om'}}}),
        '--allowedTools', 'mcp__om__*',
    ]
    env = {
        **os.environ,
        'ENABLE_TOOL_SEARCH': 'false',
        'CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK': '1',
    }

    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    async def pump_stderr():
        while line := await proc.stderr.readline():
            sys.stderr.write('[cli] ' + line.decode(errors='replace'))

    asyncio.create_task(pump_stderr())

    async def write(obj):
        proc.stdin.write(frame(obj))
        await proc.stdin.drain()

    # 1) initialize

    await write({
        'type': 'control_request',
        'request_id': 'r1',
        'request': {
            'subtype': 'initialize',
            'hooks': None,
        },
    })

    # 2) history replay: two non-querying frames seeding a secret number

    await write({
        'type': 'user',
        'shouldQuery': False,
        'parent_tool_use_id': None,
        'session_id': 'default',
        'message': {
            'role': 'user',
            'content': 'Remember the number 4271.',
        },
    })

    await write({
        'type': 'assistant',
        'parent_tool_use_id': None,
        'session_id': 'default',
        'message': {
            'role': 'assistant',
            'id': 'msg_seed_1',
            'content': [
                {
                    'type': 'text',
                    'text': 'Noted: 4271.',
                },
            ],
        },
    })

    # 3) the real turn - forces a model call; also nudges a tool call

    await write({
        'type': 'user',
        'parent_tool_use_id': None,
        'session_id': 'default',
        'message': {
            'role': 'user',
            'content': (
                'First call the om echo tool with text="hi". '
                'Then tell me: what number did I ask you to remember?'
            ),
        },
    })

    async for _ in read_until_result(proc, write):
        pass

    proc.stdin.close()
    await proc.wait()
    return 0


async def read_until_result(proc, write):
    """Demux stdout, answer om MCP requests, print interesting lines, stop at result."""

    while True:
        raw = await proc.stdout.readline()
        if not raw:
            return
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        typ = obj.get('type')

        if typ == 'system' and obj.get('subtype') == 'init':
            print('capabilities =', obj.get('capabilities'))
            print('mcp_servers  =', obj.get('mcp_servers'))

        elif typ == 'control_request' and obj['request'].get('subtype') == 'mcp_message':
            resp = handle_mcp(obj['request']['message'])
            if resp is not None :
                payload = {'mcp_response': resp}
            else:
                payload = {'mcp_response': {'jsonrpc': '2.0', 'result': {}}}
            await write({
                'type': 'control_response',
                'response': {
                    'subtype': 'success',
                    'request_id': obj['request_id'],
                    'response': payload,
                },
            })

        elif typ == 'assistant':
            for c in obj['message'].get('content', []):
                if c.get('type') == 'text':
                    print('assistant text:', c['text'])
                elif c.get('type') == 'tool_use':
                    print('assistant tool_use:', c.get('name'), c.get('input'))

        elif typ == 'result':
            print('RESULT:', obj.get('subtype'), '| session', obj.get('session_id'))
            return
        yield obj


def handle_mcp(msg):
    method, mid = msg.get('method'), msg.get('id')
    if mid is None:
        return None
    if method == 'initialize':
        print('  [om] initialize')
        return {
            'jsonrpc': '2.0',
            'id': mid,
            'result': {
                'protocolVersion': msg.get('params', {}).get('protocolVersion', '2025-06-18'),
                'capabilities': {
                    'tools': {},
                },
                'serverInfo': {
                    'name': 'om',
                    'version': '0',
                },
            },
        }

    if method == 'tools/list':
        print('  [om] tools/list')
        return {
            'jsonrpc': '2.0',
            'id': mid,
            'result': {
                'tools': [
                    {
                        'name': 'echo',
                        'description': 'Echo text back.',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'text': {
                                    'type': 'string',
                                },
                            },
                            'required': [
                                'text',
                            ],
                        },
                    },
                ],
            },
        }

    if method == 'tools/call':
        args = msg.get('params', {}).get('arguments', {})
        print('  [om] tools/call echo', args)
        return {
            'jsonrpc': '2.0',
            'id': mid,
            'result': {
                'content': [
                    {
                        'type': 'text',
                        'text': f"echo: {args.get('text')}",
                    },
                ],
            },
        }

    if method == 'ping':
        return {
            'jsonrpc': '2.0',
            'id': mid,
            'result': {},
        }

    return {
        'jsonrpc': '2.0',
        'id': mid,
        'error': {
            'code': -32601,
            'message': 'nope',
        },
    }


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
