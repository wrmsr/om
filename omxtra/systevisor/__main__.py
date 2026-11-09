# @om-lite
# @om-amalg ./_bin/systevisor.py
# mypy: ignore-errors
from .main import systevisor_main


if __name__ == '__main__':
    raise SystemExit(systevisor_main())
