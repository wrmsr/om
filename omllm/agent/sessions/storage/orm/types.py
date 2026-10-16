import abc
import typing as ta

from omcore import lang
from omcore import orm


##


class Orm(lang.Abstract):
    @abc.abstractmethod
    def new_session(self) -> ta.AsyncContextManager[orm.Session]:
        raise NotImplementedError

    def read_session(self) -> ta.AsyncContextManager[orm.Session]:
        return self.new_session()

    @abc.abstractmethod
    def ensure_session(self) -> ta.AsyncContextManager[orm.Session]:
        raise NotImplementedError
