# ruff: noqa: SLF001
# @om-lite
import typing as ta
import unittest

from ...core import IoPipeline
from ..fdio import IoPipelineDriverSocketFdioHandler


class ScriptedSendSocket:
    def __init__(self, *send_results):
        super().__init__()

        self._send_results = list(send_results)
        self.sent = []

    def send(self, data):
        if self._send_results:
            result = self._send_results.pop(0)
            if isinstance(result, BaseException):
                raise result
        else:
            result = len(data)

        self.sent.append(bytes(data[:result]))
        return result


class TestIoPipelineDriverSocketFdioHandler(unittest.TestCase):
    def test_queues_new_output_behind_existing_backlog(self):
        sock: ta.Any = ScriptedSendSocket(
            2,
            BlockingIOError(),
        )
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(),
        )

        drv._do_write_or_q([b'abcd'])
        assert sock.sent == [b'ab']
        assert [bytes(b) for b in drv._write_q] == [b'cd']

        drv._do_write_or_q([b'ef'])
        assert sock.sent == [b'ab']
        assert [bytes(b) for b in drv._write_q] == [b'cd', b'ef']

        drv._try_flush_write_q()
        assert sock.sent == [b'ab', b'cd', b'ef']
        assert not drv._write_q
