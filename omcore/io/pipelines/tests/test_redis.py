import argparse
import asyncio
import shutil
import socket
import unittest

from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..drivers.sync import SyncSocketIoPipelineDriver
from .redis import BaseRedisClient
from .redis import RedisClient
from .redis import RedisCommand
from .redis import RedisReplyError
from .redis import _parse_redis_address
from .redis import _RedisRequest
from .redis import _RedisResult
from .redis import _RedisServer
from .redis import _run_async_demo
from .redis import _run_sync_demo
from .redis import make_redis_client_pipeline_spec


_REDIS_SERVER = shutil.which('redis-server')


class TestRedisCodec(unittest.TestCase):
    def test_parse_redis_address(self) -> None:
        self.assertEqual(_parse_redis_address('localhost:6379'), ('localhost', 6379))
        self.assertEqual(_parse_redis_address('[::1]:6380'), ('::1', 6380))

        for invalid in ('localhost', ':6379', 'localhost:', 'localhost:nope', 'localhost:0', 'localhost:65536'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(argparse.ArgumentTypeError):
                    _parse_redis_address(invalid)

    def test_fragmented_array_reply(self) -> None:
        pipeline = IoPipeline(make_redis_client_pipeline_spec())
        try:
            request = _RedisRequest(7, RedisCommand((b'MGET', b'key')))
            pipeline.feed_in(request)

            encoded = pipeline.output.poll()
            self.assertEqual(
                ByteStreamBuffers.to_bytes(encoded, strict=True),
                b'*2\r\n$4\r\nMGET\r\n$3\r\nkey\r\n',
            )

            reply = b'*3\r\n$5\r\nhello\r\n:42\r\n$-1\r\n'
            for b in reply:
                pipeline.feed_in(bytes((b,)))

            result = pipeline.output.poll()
            self.assertIsInstance(result, _RedisResult)
            assert isinstance(result, _RedisResult)
            self.assertEqual(result.request_id, 7)
            self.assertEqual(
                BaseRedisClient._materialize_value(result.value),  # noqa
                [b'hello', 42, None],
            )
            self.assertIsNone(pipeline.output.poll())
        finally:
            pipeline.destroy()


@unittest.skipIf(_REDIS_SERVER is None, 'redis-server is not installed')
class TestRedisClients(unittest.TestCase):
    def test_sync_and_async_end_to_end(self) -> None:
        assert _REDIS_SERVER is not None
        with _RedisServer(_REDIS_SERVER) as port:
            self.assertEqual(_run_sync_demo(port, host='127.0.0.1')['INCRBY'], 42)
            self.assertEqual(asyncio.run(_run_async_demo(port, host='127.0.0.1'))['INCRBY'], 42)

    def test_reply_error_does_not_close_connection(self) -> None:
        assert _REDIS_SERVER is not None
        with _RedisServer(_REDIS_SERVER) as port:
            with socket.create_connection(('127.0.0.1', port)) as sock:
                client = RedisClient(SyncSocketIoPipelineDriver(make_redis_client_pipeline_spec(), sock))
                try:
                    with self.assertRaises(ValueError):
                        client.execute()
                    with self.assertRaisesRegex(RedisReplyError, 'unknown command'):
                        client.execute('OMCORE_NOT_A_REDIS_COMMAND')
                    self.assertEqual(client.execute('PING'), b'PONG')
                finally:
                    client.close()


if __name__ == '__main__':
    unittest.main()
