#!/usr/bin/env python3
"""
An echo ACP agent: a JSON-RPC peer speaking newline-delimited JSON over stdio or a unix socket, answering the
handful of ACP methods needed to hold a conversation and echoing prompt text back as session updates.
"""
import argparse
import asyncio
import dataclasses as dc
import os.path
import typing as ta
import uuid

from omcore import marshal as msh
from omcore.sockets.endpoints import UnixSocketEndpoint
from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl

from .. import protocol


JsonObject: ta.TypeAlias = ta.Mapping[str, ta.Any]


##
# tiny ACP-ish schema subset


def _put_meta(d: JsonObject, field_meta: JsonObject | None) -> JsonObject:
    if field_meta is not None:
        d = {**d, '_meta': field_meta}
    return d


@dc.dataclass(slots=True)
class TextContentBlock:
    text: str
    annotations: JsonObject | None = None
    field_meta: JsonObject | None = None

    @classmethod
    def from_json(cls, obj: ta.Any) -> TextContentBlock | None:
        if not isinstance(obj, dict):
            return None

        typ = obj.get('type')
        if typ is not None and typ != 'text':
            return None

        text = obj.get('text')
        if not isinstance(text, str):
            return None

        return cls(
            text=text,
            annotations=obj.get('annotations') if isinstance(obj.get('annotations'), dict) else None,
            field_meta=obj.get('_meta') if isinstance(obj.get('_meta'), dict) else None,
        )

    def to_json(self) -> JsonObject:
        d: dict[str, ta.Any] = {
            'type': 'text',
            'text': self.text,
        }
        if self.annotations is not None:
            d['annotations'] = self.annotations
        return _put_meta(d, self.field_meta)


@dc.dataclass(slots=True)
class AgentMessageChunk:
    content: TextContentBlock
    field_meta: JsonObject | None = None

    def to_json(self) -> JsonObject:
        d: JsonObject = {
            'sessionUpdate': 'agent_message_chunk',
            'content': self.content.to_json(),
        }
        return _put_meta(d, self.field_meta)


@dc.dataclass(slots=True)
class InitializeResponse:
    protocol_version: int
    agent_info: JsonObject | None = None

    def to_json(self) -> JsonObject:
        return {
            'protocolVersion': self.protocol_version,
            'agentCapabilities': {
                'loadSession': False,
                'mcpCapabilities': {
                    'http': False,
                    'sse': False,
                },
                'promptCapabilities': {
                    'audio': False,
                    'embeddedContext': False,
                    'image': False,
                },
                'sessionCapabilities': {},
            },
            'authMethods': [],
            'agentInfo': self.agent_info or {
                'name': 'zero-dep-echo-agent',
                'version': '0.1.0',
            },
        }


@dc.dataclass(slots=True)
class NewSessionResponse:
    session_id: str

    def to_json(self) -> JsonObject:
        return {'sessionId': self.session_id}


@dc.dataclass(slots=True)
class PromptResponse:
    stop_reason: str = 'end_turn'
    user_message_id: str | None = None

    def to_json(self) -> JsonObject:
        d: dict[str, ta.Any] = {'stopReason': self.stop_reason}

        # Present in the Python SDK echo example you pasted. Some ACP schema versions do not include this field; clients
        # that do not care should ignore it.
        if self.user_message_id is not None:
            d['userMessageId'] = self.user_message_id

        return d


##
# params


_MISSING = object()


def get_param(
    params: JsonObject,
    camel_name: str,
    snake_name: str | None = None,
    default: ta.Any = _MISSING,
) -> ta.Any:
    if camel_name in params:
        return params[camel_name]
    if snake_name is not None and snake_name in params:
        return params[snake_name]
    if default is not _MISSING:
        return default
    raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, f'Missing required param: {camel_name}')


def ensure_params(raw: ta.Any) -> JsonObject:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'params must be an object')
    return raw


##
# echo ACP agent


class EchoAcpAgent(jr.AsyncDispatcher):
    """One agent per connection: sessions are connection-scoped."""

    def __init__(self) -> None:
        super().__init__()

        self._sessions: set[str] = set()

    async def dispatch(self, connection: ta.Any, request: jr.Request) -> ta.Any:
        conn: jpl.AsyncioConnection = connection
        params = ensure_params(request.params)

        match request.method:
            case 'initialize':
                return await self.initialize(params)

            case 'session/new':
                return await self.new_session(params)

            case 'session/prompt':
                return await self.prompt(conn, params)

            case 'session/cancel':
                # This echo agent has no long-running work to cancel. Clients send this as a notification, in which
                # case it never reaches here; as a request it is simply acknowledged.
                return {}

            case _:
                raise jr.JsonrpcMethodError(jr.KnownErrors.METHOD_NOT_FOUND, data=request.method)

    async def handle_notification(self, conn: jpl.AsyncioConnection, note: jr.Request) -> None:
        # session/cancel and anything else: nothing to do.
        pass

    async def initialize(self, params: JsonObject) -> JsonObject:
        protocol_version = get_param(params, 'protocolVersion', 'protocol_version')
        if not isinstance(protocol_version, int):
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'protocolVersion must be an integer')

        return msh.marshal(protocol.InitializeResponse(protocol_version=protocol_version))  # type: ignore

    async def new_session(self, params: JsonObject) -> JsonObject:
        # Equivalent to the SDK sample: accept cwd/additionalDirectories/mcpServers but do not do anything with them.
        cwd = get_param(params, 'cwd', default=None)
        if cwd is not None and not isinstance(cwd, str):
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'cwd must be a string')

        session_id = uuid.uuid7().hex
        self._sessions.add(session_id)
        return NewSessionResponse(session_id=session_id).to_json()

    async def prompt(self, conn: jpl.AsyncioConnection, params: JsonObject) -> JsonObject:
        session_id = get_param(params, 'sessionId', 'session_id')
        if not isinstance(session_id, str):
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'sessionId must be a string')
        if session_id not in self._sessions:
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, f'Unknown sessionId: {session_id}')

        prompt = get_param(params, 'prompt')
        if not isinstance(prompt, list):
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'prompt must be a list')

        message_id = get_param(params, 'messageId', 'message_id', default=None)
        if message_id is not None and not isinstance(message_id, str):
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, 'messageId must be a string when present')

        for raw_block in prompt:
            block = TextContentBlock.from_json(raw_block)
            if block is None:
                # Only TextContentBlock is handled.
                continue

            echoed = TextContentBlock(
                text=block.text,
                field_meta={'echo': True},
            )
            chunk = AgentMessageChunk(
                content=echoed,
                field_meta={'echo': True},
            )

            await self.session_update(
                conn,
                session_id=session_id,
                update=chunk,
                source='echo_agent',
            )

        return PromptResponse(
            stop_reason='end_turn',
            user_message_id=message_id,
        ).to_json()

    async def session_update(
        self,
        conn: jpl.AsyncioConnection,
        *,
        session_id: str,
        update: AgentMessageChunk,
        source: str | None = None,
    ) -> None:
        params: dict[str, ta.Any] = {
            'sessionId': session_id,
            'update': update.to_json(),
        }

        # The SDK echo passes source="echo_agent". The current public schema does not show a top-level source field on
        # SessionNotification, so keep it in ACP's reserved extensibility metadata instead of making the notification
        # shape stricter-client-hostile.
        if source is not None:
            params['_meta'] = {'source': source}

        await conn.notify('session/update', params)


##
# serving


def build_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: jpl.Config = jpl.Config.DEFAULT,
) -> jpl.AsyncioConnection:
    agent = EchoAcpAgent()
    return jpl.AsyncioConnections.of_streams(
        reader,
        writer,
        config,
        dispatcher=agent,
        notification_handler=agent.handle_notification,
    )


async def serve_stdio(config: jpl.Config = jpl.Config.DEFAULT) -> None:
    agent = EchoAcpAgent()
    conn = await jpl.AsyncioConnections.of_stdio(
        config,
        dispatcher=agent,
        notification_handler=agent.handle_notification,
    )
    async with conn:
        await conn.wait_closed()


async def serve_unix(socket_path: str, config: jpl.Config = jpl.Config.DEFAULT) -> None:
    server = jpl.AsyncioServer(
        jpl.AsyncioServerConfig(
            endpoint=UnixSocketEndpoint(path=socket_path),
            pipeline=config,
        ),
        connection_factory=lambda r, w: build_connection(r, w, config),
    )
    async with server:
        await server.serve_forever()


async def main() -> None:
    parser = argparse.ArgumentParser(description='Echo ACP agent server')
    subparsers = parser.add_subparsers()
    parser.set_defaults(_cmd=None)

    serve_parser = subparsers.add_parser('serve')
    serve_parser.set_defaults(_cmd='serve')
    serve_parser.add_argument(
        '-t',
        '--transport',
        choices=['stdio', 'unix'],
        default='stdio',
        help='Transport type to use (default: stdio)',
    )
    serve_parser.add_argument(
        '-s',
        '--socket',
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '.acp.sock')),
        help='Socket path for Unix socket transport',
    )

    args = parser.parse_args()

    match args._cmd:  # noqa
        case 'serve':
            match args.transport:
                case 'stdio':
                    await serve_stdio()

                case 'unix':
                    await serve_unix(args.socket)

                case _:
                    raise ValueError(f'Unknown transport: {args.transport}')

        case _:
            parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
