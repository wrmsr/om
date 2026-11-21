import abc
import contextlib
import typing as ta

from omcore import lang

from .context import Context
from .messages import AiMessage
from .models import Model
from .options import Options
from .streams import AiStream


BackendT = ta.TypeVar('BackendT', bound='Backend')


##


class Backend(lang.Abstract):
    @property
    @abc.abstractmethod
    def model(self) -> Model:
        raise NotImplementedError


@contextlib.asynccontextmanager
async def manage_backend(backend: BackendT) -> ta.AsyncIterator[BackendT]:
    """
    Enters `backend` if it is an async or sync context manager, otherwise yields it as-is.

    Backends may optionally implement async (or sync) context management when they own expensive resources such as
    in-process model weights or persistent client pools.
    """

    obj: ta.Any = backend
    if isinstance(obj, contextlib.AbstractAsyncContextManager):
        async with obj as entered:
            yield entered
    elif isinstance(obj, contextlib.AbstractContextManager):
        with obj as entered:
            yield entered
    else:
        yield backend


##


# @om-manifest $.core.registry.manifests.RegistryTypeManifest
class ImmediateBackend(Backend, lang.Abstract):
    @abc.abstractmethod
    def immediate(self, context: Context, options: Options | None = None) -> ta.Awaitable[AiMessage]:
        raise NotImplementedError


##


# @om-manifest $.core.registry.manifests.RegistryTypeManifest
class StreamBackend(ImmediateBackend, lang.Abstract):
    @abc.abstractmethod
    def stream(self, context: Context, options: Options | None = None) -> ta.Awaitable[AiStream]:
        raise NotImplementedError

    #

    async def immediate(self, context: Context, options: Options | None = None) -> AiMessage:
        async with (await self.stream(context, options)) as it:
            async for _ in it:
                pass
            return it.result.must()
