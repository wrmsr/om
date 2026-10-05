# @om-lite
import logging
import os.path
import unittest

from ..std.handlers import ListLoggingHandler
from ..std.loggers import StdLogger
from ..std.records import LoggingContextLogRecord


class TestLogs(unittest.TestCase):
    def test_logs(self):
        handler = ListLoggingHandler()

        logging_log = logging.getLogger(__name__)
        logging_log.handlers.clear()
        logging_log.handlers.append(handler)
        logging_log.setLevel(logging.INFO)

        logging_log.info('hi')
        logging_log.warning('hi')
        logging_log.error('hi')

        log = StdLogger(logging_log)

        log.info('hi')
        log.warning('hi')
        log.error('hi')

        log.info(lambda: 'hi')
        log.info(lambda: ('hi %d', 420))

        log.info(('hi',))
        log.info(('hi %d', 420))

        lr = handler.records[-1]
        assert isinstance(lr, LoggingContextLogRecord)
        assert os.path.basename(lr.pathname) == 'test_logs.py'
        assert lr.funcName == 'test_logs'

        i = 420
        log.info(f'hi! {i}')  # noqa

        c = 0

        def foo() -> str:
            nonlocal c
            c += 1
            return f'foo:{c}'

        log.info(f'{foo()}')  # noqa
        assert c == 1

        log.info(lambda: f'{foo()}')
        assert c == 2

        log.debug(f'{foo()}')  # noqa
        assert c == 3

        log.debug(lambda: f'{foo()}')
        assert c == 3

    def test_exception(self):
        log = StdLogger(logging.getLogger(__name__))
        try:
            raise ValueError('barf')  # noqa
        except Exception as ve:  # noqa
            log.exception()
            log.exception(ve)  # noqa

    def test_exception_message(self):
        handler = ListLoggingHandler()

        logging_log = logging.getLogger(f'{__name__}.exception_message')
        logging_log.handlers.clear()
        logging_log.handlers.append(handler)

        log = StdLogger(logging_log)
        ve = ValueError('barf')
        try:
            raise ve  # noqa
        except Exception:  # noqa
            log.exception('lone message')
            log.exception('message %d', 420)
            log.exception(('tuple message %d', 420))
            log.exception(lambda: 'fn message')
            log.exception('explicit %s', 'exc', exc_info=ve)

        assert [lr.getMessage() for lr in handler.records] == [
            'lone message',
            'message 420',
            'tuple message 420',
            'fn message',
            'explicit exc',
        ]
        for lr in handler.records:
            assert lr.exc_info is not None
            assert lr.exc_info[1] is ve
