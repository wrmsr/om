from omcore import check
from omcore import dataclasses as dc
from omcore.formats.json import all as json

from .providers import provider_model_catalog


##


def _main() -> None:
    dcts: dict[str, dict] = {}

    for m in provider_model_catalog():
        dct: dict = {}

        limits = m.limits
        if callable(limits):
            limits = limits()
        if limits is not None:
            dct.update(
                limits={k: v for k, v in dc.asdict(limits).items() if v is not None},
            )

        pricing = m.pricing
        if callable(pricing):
            pricing = pricing()
        if pricing is not None:
            dct.update(
                pricing={k: v for k, v in dc.asdict(pricing).items() if v is not None},
            )

        dcts[check.not_none(m.key).joined] = dct

    print(json.dumps_pretty(dcts))


if __name__ == '__main__':
    _main()
