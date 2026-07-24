# @om-lite
import abc
import unittest

from ....lite.abstract import Abstract
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineService


class FooService(IoPipelineService, Abstract):
    @abc.abstractmethod
    def frob(self) -> str:
        raise NotImplementedError


class FooServiceImpl(FooService):
    def frob(self) -> str:
        return 'foo!'


class LifecycleService(IoPipelineService):
    def __init__(self):
        super().__init__()

        self.events = []

    def pipeline_update(self, pipeline, kind):
        self.events.append(('pipeline_update', pipeline, kind))

    def handler_update(self, handler_ref, kind):
        self.events.append(('handler_update', handler_ref, kind))

    def pipeline_enter(self, pipeline):
        self.events.append(('pipeline_enter', pipeline, None))

    def pipeline_exit(self, pipeline):
        self.events.append(('pipeline_exit', pipeline, None))


class NopIoPipelineHandler(IoPipelineHandler):
    pass


class TestServices(unittest.TestCase):
    def test_services(self):
        ch = IoPipeline.new(services=[FooServiceImpl()])
        foo = ch.services[FooService]
        assert isinstance(foo, FooServiceImpl)
        assert foo.frob() == 'foo!'

    def test_lifecycle(self):
        svc = LifecycleService()
        ch = IoPipeline.new(
            [NopIoPipelineHandler()],
            services=[svc],
        )
        handler_ref = ch.handlers()[0]
        assert isinstance(handler_ref, IoPipelineHandlerRef)

        ch.destroy()

        assert svc.events == [
            ('pipeline_update', ch, 'added'),
            ('handler_update', handler_ref, 'adding'),
            ('handler_update', handler_ref, 'added'),
            ('pipeline_enter', ch, None),
            ('pipeline_exit', ch, None),
            ('pipeline_enter', ch, None),
            ('handler_update', handler_ref, 'removing'),
            ('handler_update', handler_ref, 'removed'),
            ('pipeline_exit', ch, None),
            ('pipeline_update', ch, 'removed'),
        ]
