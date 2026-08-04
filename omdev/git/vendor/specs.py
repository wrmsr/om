import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json


with lang.auto_proxy_import(globals()):
    from omcore import marshal as msh


##


VENDOR_SPEC_FILE_NAME = '.om-vendor.json'


@dc.dataclass(frozen=True, kw_only=True)
class GitVendorSpec:
    """
    Describes a directory of sources vendored from an upstream git repo.

    Lives as a json file (`.om-vendor.json`) inside the vendored directory itself. `files` are paths relative to both
    the upstream repo root and the vendored directory. `rev` is the upstream commit the directory was last synced to -
    it serves as the base for three-way merges on subsequent pulls - and `ref` is the human-readable name (tag/branch)
    that rev was requested as, if any.
    """

    url: str
    rev: str | None = None
    ref: str | None = None
    files: ta.Sequence[str] = ()


def vendor_spec_path(vendor_dir: str) -> str:
    return os.path.join(vendor_dir, VENDOR_SPEC_FILE_NAME)


def load_vendor_spec(vendor_dir: str) -> GitVendorSpec:
    with open(vendor_spec_path(vendor_dir)) as f:
        return msh.unmarshal(json.loads(f.read()), GitVendorSpec)


def save_vendor_spec(vendor_dir: str, spec: GitVendorSpec) -> None:
    with open(vendor_spec_path(vendor_dir), 'w') as f:
        f.write(json.dumps_pretty(msh.marshal(spec)) + '\n')
