from ..api.configs import ConfigRegistry
from ..api.types import MarshalerFactory
from ..api.types import UnmarshalerFactory
from .api import StandardMarshalerFactories
from .api import StandardUnmarshalerFactories
from .defaults import DEFAULT_STANDARD_FACTORIES


##


def install_standard_factories(
        cr: ConfigRegistry,
        *factories: MarshalerFactory | UnmarshalerFactory,
) -> None:
    # FIXME: private lock access! bad coder!
    with cr._lock:  # noqa
        m_cfg = cr.get().get(StandardMarshalerFactories)
        u_cfg = cr.get().get(StandardUnmarshalerFactories)

        m_lst: list[MarshalerFactory] = list(
            m_cfg.lst if m_cfg is not None else DEFAULT_STANDARD_FACTORIES.marshaler_factories,
        )
        u_lst: list[UnmarshalerFactory] = list(
            u_cfg.lst if u_cfg is not None else DEFAULT_STANDARD_FACTORIES.unmarshaler_factories,
        )

        m_new = False
        u_new = False

        for f in factories:
            k = False

            if isinstance(f, MarshalerFactory):
                m_lst[0:0] = [f]
                m_new = True
                k = True

            if isinstance(f, UnmarshalerFactory):
                u_lst[0:0] = [f]
                u_new = True
                k = True

            if not k:
                raise TypeError(f)

        if m_new:
            cr.update(None, StandardMarshalerFactories(m_lst), mode='override')
        if u_new:
            cr.update(None, StandardUnmarshalerFactories(u_lst), mode='override')
