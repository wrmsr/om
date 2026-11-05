"""
TODO:
 - unbound keys
 - unreferenced keys
 - full toposort/dag
 - togglable unbound/cycle handling (lax default)
 - explicit opaques
"""
import typing as ta

from .. import check
from .. import lang
from .bindings import Binding
from .dependencies import Dependencies
from .elements import CollectedElements
from .elements import Element
from .elements import Elements
from .elements import collect_elements
from .impl.elements import ElementCollection
from .keys import Key


ElementT = ta.TypeVar('ElementT', bound=Element)


##


class ElementsAnalysis:
    def __init__(self, es: Elements | CollectedElements) -> None:
        super().__init__()

        self._ec = check.isinstance(collect_elements(es), ElementCollection)

    @property
    def elements(self) -> Elements:
        return self._ec.elements

    #

    def element_multimap(self) -> ta.Mapping[Key | None, ta.Sequence[Element]]:
        return self._ec.element_multimap()

    def elements_of_type(self, *tys: type[ElementT]) -> ta.Sequence[ElementT]:
        return self._ec.elements_of_type(*tys)

    #

    def bindings_by_key(self) -> ta.Mapping[Key, Binding]:
        return self._ec.bindings_by_key()

    #

    @lang.cached_function
    def known_dependencies_by_key(self) -> ta.Mapping[Key, Dependencies | None]:
        return {
            k: bi.provider.deep_known_dependencies()
            for k, bi in self._ec.binding_impl_map().items()
        }


def analyze_elements(es: Elements | CollectedElements) -> ElementsAnalysis:
    return ElementsAnalysis(es)
