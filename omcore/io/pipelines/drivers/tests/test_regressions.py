# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""Regression tests for defects found reviewing the half-close driver work. See ../../FINDINGS.md."""
import fcntl
import os
import socket
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ..sync import FdSyncIoPipelineDriver


##


def _is_nonblocking(fd: int) -> bool:
    return bool(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK)


class _CloseAtOnce(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return

        ctx.feed_in(msg)


class TestFdSyncSharedOpenFileDescription(unittest.TestCase):
    # The nonblocking flag lives on the open file description. When the read and write descriptors are dups of one
    # description - a process's stdin and stdout on the same terminal, typically - the driver must restore the
    # description to its original mode, not leave the terminal nonblocking for whatever runs next.

    def _run(self, read_fd: int, write_fd: int) -> None:
        d = FdSyncIoPipelineDriver(IoPipeline.Spec([_CloseAtOnce()]), read_fd, write_fd)
        d.loop_until_done()

    def test_dup_pair_restored_to_blocking(self) -> None:
        a, b = socket.socketpair()
        try:
            r = a.fileno()
            w = os.dup(r)
            try:
                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))

                self._run(r, w)

                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))
            finally:
                os.close(w)
        finally:
            a.close()
            b.close()

    def test_dup_pair_restored_to_blocking_with_higher_read_fd(self) -> None:
        # The order in which the two descriptors are visited must not matter.
        a, b = socket.socketpair()
        try:
            w = a.fileno()
            r = os.dup(w)
            try:
                self._run(r, w)

                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))
            finally:
                os.close(r)
        finally:
            a.close()
            b.close()

    def test_originally_nonblocking_description_stays_nonblocking(self) -> None:
        a, b = socket.socketpair()
        try:
            a.setblocking(False)
            r = a.fileno()
            w = os.dup(r)
            try:
                self._run(r, w)

                self.assertTrue(_is_nonblocking(r))
                self.assertTrue(_is_nonblocking(w))
            finally:
                os.close(w)
        finally:
            a.close()
            b.close()
