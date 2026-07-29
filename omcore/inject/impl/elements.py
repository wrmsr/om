"""
Scopes in general:
 - clearly some notion of 'activeness for a given request'

Overrides + Scopes:
 -

Multi's + Scopes:
 - scope on a multi vs each element?

Element Types:
 - Binding
 - ProvisionListenerBinding
 - SetBinding
 - MapBinding
 - Eager
 - Overrides
 - Expose
 - Private
 - ScopeBinding
"""
import copy
import typing as ta

from ... import check
from ... import collections as col
from ... import lang
from ..bindings import Binding
from ..eagers import Eager
from ..elements import CollectedElements
from ..elements import Element
from ..elements import Elements
from ..errors import ConflictingKeyError
from ..errors import ScopeEagerUnsupportedError
from ..errors import UnboundKeyError
from ..keys import Key
from ..listeners import ProvisionListenerBinding
from ..multis import MapBinding
from ..multis import MapProvider
from ..multis import SetBinding
from ..multis import SetProvider
from ..overrides import Overrides
from ..privates import Expose
from ..privates import Private
from ..scopes import ScopeBinding
from ..types import Scope
from .bindings import BindingImpl
from .multis import make_multi_provider_impl
from .origins import Origins
from .origins import set_origins
from .providers import ProviderImpl
from .providersmap import make_provider_impl
from .scopes import get_scope_impl


if ta.TYPE_CHECKING:
    from . import privates as _privates
else:
    _privates = lang.proxy_import('.privates', __package__)


ElementT = ta.TypeVar('ElementT', bound=Element)


##


_SIMPLE_KEYED_ELEMENT_TYPES: tuple[type[Element], ...] = (
    Binding,
    Eager,
    Expose,
)

_SIMPLE_NON_KEYED_ELEMENT_TYPES: tuple[type[Element], ...] = (
    ProvisionListenerBinding,
)

_NON_BINDING_ELEMENT_TYPES: tuple[type[Element], ...] = (
    Eager,
    Expose,
    ProvisionListenerBinding,
)


class ElementCollection(CollectedElements, lang.Final):
    def __init__(self, es: Elements) -> None:
        super().__init__()

        self._es = check.isinstance(es, Elements)

        self._private_infos: ta.MutableMapping[Private, _privates.PrivateInfo] | None = None
        self._scope_auto_elements: dict[Scope, Elements | None] = {}

    ##

    def _get_private_info(self, p: Private) -> _privates.PrivateInfo:
        if (pis := self._private_infos) is None:
            self._private_infos = pis = col.IdentityKeyDict()
        try:
            return pis[p]
        except KeyError:
            pis[p] = ec = _privates.PrivateInfo(self, p)
            return ec

    ##

    def _get_scope_auto_elements(self, sc: Scope) -> Elements | None:
        # Cached so equal ScopeBindings expand to identical elements, which then squash as duplicates rather than
        # conflict - auto elements (like SeededScope's Manager binding) are not otherwise value-comparable.
        try:
            return self._scope_auto_elements[sc]
        except KeyError:
            pass
        self._scope_auto_elements[sc] = sae = get_scope_impl(sc).auto_elements(sc)
        return sae

    ##

    def _build_raw_element_multimap(
            self,
            es: ta.Iterable[Element],
            out: dict[Key | None, list[Element]] | None = None,
    ) -> dict[Key | None, list[Element]]:
        if out is None:
            out = {}

        def add(k: Key | None, *e: Element) -> None:
            out.setdefault(k, []).extend(e)

        for e in es:
            if isinstance(e, _SIMPLE_KEYED_ELEMENT_TYPES):
                add(e.key, e)  # type: ignore[attr-defined]  # noqa

            elif isinstance(e, _SIMPLE_NON_KEYED_ELEMENT_TYPES):
                add(None, e)

            elif isinstance(e, (SetBinding, MapBinding)):
                add(e.multi_key, e)

            elif isinstance(e, ScopeBinding):
                add(None, e)
                if (sae := self._get_scope_auto_elements(e.scope)) is not None:
                    self._build_raw_element_multimap(sae, out)

            elif isinstance(e, Private):
                pi = self._get_private_info(e)
                self._build_raw_element_multimap(pi.owner_elements(), out)

            elif isinstance(e, Overrides):
                src = self._build_raw_element_multimap(e.src)
                ovr = self._build_raw_element_multimap(e.ovr)
                for k, b in src.items():  # FIXME: merge None keys?
                    try:
                        bs = ovr[k]
                    except KeyError:
                        bs = b
                    add(k, *bs)
                for k, bs in ovr.items():
                    if k not in src:
                        add(k, *bs)

            else:
                raise TypeError(e)

        return out

    @lang.cached_function
    def element_multimap(self) -> ta.Mapping[Key | None, ta.Sequence[Element]]:
        return self._build_raw_element_multimap(self._es)

    @lang.cached_function
    def elements_of_type(self, *tys: type[ElementT]) -> ta.Sequence[ElementT]:
        return tuple(e for es in self.element_multimap().values() for e in es if isinstance(e, tys))  # noqa

    ##

    def _get_single_binding(self, k: Key, bs: ta.Sequence[Binding]) -> Binding:
        if not bs:
            raise UnboundKeyError(k)

        elif len(bs) > 1:
            # Grouped pairwise by equality, not in a dict - bindings need not be hashable (eg. unhashable consts).
            gs: list[list[Binding]] = []
            for b in bs:
                for g in gs:
                    if b == g[0]:
                        g.append(b)
                        break
                else:
                    gs.append([b])
            if len(gs) > 1:
                raise ConflictingKeyError(k)
            l = check.single(gs)
            b = copy.copy(l[0])
            set_origins(b, Origins(tuple(o for c in l for o in c.origins)))
            return b

        else:
            return check.isinstance(check.single(bs), Binding)

    def _build_binding_impl_map(self, em: ta.Mapping[Key | None, ta.Sequence[Element]]) -> dict[Key, BindingImpl]:
        pm: dict[Key, BindingImpl] = {}
        for k, es in em.items():
            if k is None:
                continue

            es_by_ty = col.multi_map_by(type, es)

            for nb_ty in _NON_BINDING_ELEMENT_TYPES:
                es_by_ty.pop(nb_ty, None)

            if (bs := es_by_ty.pop(Binding, None)):
                b = self._get_single_binding(k, bs)  # type: ignore

                p: ProviderImpl
                if isinstance(b.provider, (SetProvider, MapProvider)):
                    p = make_multi_provider_impl(b.provider, es_by_ty)
                else:
                    p = make_provider_impl(b.provider)

                pm[k] = BindingImpl(b.key, p, b.scope, b)

            if es_by_ty:
                raise TypeError(es_by_ty)

        return pm

    @lang.cached_function
    def binding_impl_map(self) -> ta.Mapping[Key, BindingImpl]:
        return self._build_binding_impl_map(self.element_multimap())

    ##

    @lang.cached_function
    def scope_binding_scopes(self) -> ta.Sequence[Scope]:
        return [sb.scope for sb in self.elements_of_type(ScopeBinding)]

    @lang.cached_function
    def sorted_eager_keys_by_scope(self) -> ta.Mapping[Scope, ta.Sequence[Key]]:
        bim = self.binding_impl_map()

        dct: dict[Scope, list[Eager]] = {}
        for e in self.elements_of_type(Eager):
            try:
                bi = bim[e.key]
            except KeyError:
                raise UnboundKeyError(e.key) from None
            dct.setdefault(bi.scope, []).append(e)

        # Temporary impls, as with _get_scope_auto_elements - eagerability is declared by the impl, and the injector's
        # long-lived impls don't exist at collection time.
        for sc, egs in dct.items():
            if get_scope_impl(sc).eager_point() is None:
                raise ScopeEagerUnsupportedError(sc, egs[0].key)

        return {
            sc: tuple(eg.key for eg in sorted(egs, key=lambda eg: eg.priority))
            for sc, egs in dct.items()
        }


##


def collect_elements(es: Elements | CollectedElements) -> ElementCollection:
    if isinstance(es, CollectedElements):
        return check.isinstance(es, ElementCollection)
    else:
        return ElementCollection(es)
