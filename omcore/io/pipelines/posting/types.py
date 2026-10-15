# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Posting: running work inside a pipeline's execution boundary from outside its driver's current turn - from application
code between driver steps, from another pipeline's turn on the same thread, or from the pipeline's own turn.

A post is queued at the driver's boundary like an enqueued message: it runs after the boundary input queued before it
and before that queued after it, when the driver next processes its queue, and so never nested inside a turn already in
progress. A driver which is idle is woken by it. Nothing here is thread-safe: posts are made on the driver's thread.
"""
import abc
import dataclasses as dc
import typing as ta
import weakref

from ....lite.abstract import Abstract
from ....lite.check import check
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineMessages
from ..core import IoPipelineService
from ..core import IoPipelineUpdate
from ..errors import ContextInvalidatedIoPipelineError
from ..errors import StateIoPipelineError


T = ta.TypeVar('T')


##


class ClosedIoPipelinePostingError(StateIoPipelineError):
    """The driver has closed or failed, or the stream has ended, so nothing can be posted into the pipeline any more."""


@ta.final
@dc.dataclass(frozen=True, eq=False)
class IoPipelinePost(IoPipelineMessages.Completable[T], ta.Generic[T]):
    """
    Work posted into a pipeline. Completes with the callable's result once it has run; fails with the exception it
    raised, with AbortedIoPipelineError if the driver closed before it ran, or with ContextInvalidatedIoPipelineError
    if the handler it was posted for was removed first. As for any completable, the outcome is observable only from a
    listener.
    """

    fn: ta.Union[
        ta.Callable[[], T],
        ta.Callable[[IoPipelineHandlerContext], T],
    ]

    _ctx_ref: ta.Optional[ta.Callable[[], ta.Optional[IoPipelineHandlerContext]]] = dc.field(default=None, repr=False)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}({self.fn!r})'

    def run(self, pipeline: IoPipeline) -> None:
        """
        Runs the post inside the pipeline's execution boundary, if it is still pending: for drivers. An exception from
        the callable fails the post and nothing else; one from a completion listener, or a propagation failure on
        leaving the boundary, is the driver's to handle as it handles any other.
        """

        if self.is_done():
            return

        with pipeline.enter():
            try:
                if (ctx_ref := self._ctx_ref) is not None:
                    if (ctx := ctx_ref()) is None or ctx.invalidated:
                        raise ContextInvalidatedIoPipelineError
                    res = self.fn(ctx)  # type: ignore[call-arg]
                else:
                    res = self.fn()  # type: ignore[call-arg]

            except Exception as e:  # noqa
                self.set_failed(e)

            else:
                self.set_succeeded(res)


def fail_io_pipeline_posts(posts: ta.Iterable[IoPipelinePost], exc: BaseException) -> None:
    """Fails every pending post given, raising the first listener error once all have been failed. For drivers."""

    first_listener_exc: ta.Optional[BaseException] = None

    for post in posts:
        if post.is_done():
            continue
        try:
            post.set_failed(exc)
        except BaseException as listener_exc:  # noqa
            if first_listener_exc is None:
                first_listener_exc = listener_exc

    if first_listener_exc is not None:
        raise first_listener_exc


##


class IoPipelinePosting(Abstract):
    """
    Posts work into one pipeline.

    Every driver installs one as a service, as every driver installs scheduling, and it is looked up from
    `ctx.services` by this interface; a pipeline without a driver has none, since nothing would wake for it. A handler
    requiring it validates its presence when added. A multiplexed stream's pipeline has one when its parent does, which
    reaches the stream through the parent's.
    """

    @abc.abstractmethod
    def post(self, fn: ta.Callable[[], T]) -> IoPipelinePost[T]:
        """Queues `fn` to run in the pipeline. Raises ClosedIoPipelinePostingError if nothing can run it any more."""

        raise NotImplementedError

    @abc.abstractmethod
    def post_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            fn: ta.Callable[[IoPipelineHandlerContext], T],
    ) -> IoPipelinePost[T]:
        """
        Queues `fn` to run with the handler's context, which is held only weakly until then - the submitter need not
        retain the ref - failing the post if the handler has been removed by the time it runs.
        """

        raise NotImplementedError


class IoPipelinePostingTarget(Abstract):
    """What a posting service hands posts to: a driver, or something which routes them to one."""

    @abc.abstractmethod
    def accept_post(self, post: IoPipelinePost) -> None:
        """
        Queues the post at the pipeline's boundary and arranges for it to run promptly. Raises
        ClosedIoPipelinePostingError if nothing can run it any more.
        """

        raise NotImplementedError


@ta.final
class TargetIoPipelinePostingService(IoPipelinePosting, IoPipelineService):
    """The posting service a driver installs: it forwards to its target, which it holds only weakly."""

    def __init__(self, target: IoPipelinePostingTarget) -> None:
        super().__init__()

        self.__target_ref = weakref.ref(target)
        self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def _pipeline(self) -> ta.Optional[IoPipeline]:
        if self.__pipeline_ref is None:
            return None
        return self.__pipeline_ref()

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'added':
            check.none(self._pipeline)
            self.__pipeline_ref = weakref.ref(pipeline)

        elif kind == 'removed':
            self.__pipeline_ref = None

    def _target(self) -> IoPipelinePostingTarget:
        if (target := self.__target_ref()) is None:
            raise ClosedIoPipelinePostingError('posting target is gone')
        return target

    def post(self, fn: ta.Callable[[], T]) -> IoPipelinePost[T]:
        post: IoPipelinePost[T] = IoPipelinePost(fn)
        self._target().accept_post(post)
        return post

    def post_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            fn: ta.Callable[[IoPipelineHandlerContext], T],
    ) -> IoPipelinePost[T]:
        pipeline = check.not_none(self._pipeline)
        check.is_(handler_ref.pipeline, pipeline)
        check.state(not handler_ref.invalidated)

        post: IoPipelinePost[T] = IoPipelinePost(fn, _ctx_ref=weakref.ref(handler_ref._context))  # noqa
        self._target().accept_post(post)
        return post
