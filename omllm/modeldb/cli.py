# ruff: noqa: SLF001
"""
https://models.dev/
https://github.com/anomalyco/models.dev
"""
import compression.zstd
import datetime
import os.path
import typing as ta
import urllib.request

from omcore.argparse import all as ap
from omcore.formats.json import all as json

from . import cache
from . import consts


##


def fetch_providers(url: str | None = None) -> dict[str, dict[str, ta.Any]]:
    if url is None:
        url = consts.MODELS_URL

    with urllib.request.urlopen(urllib.request.Request(  # noqa
            url,
            headers={
                'User-Agent': 'curl/8.7.1',
            },
    )) as f:
        src = f.read()

    providers = json.loads(src.decode('utf-8'))
    return providers


##


def _render_cache_data(data: ta.Any) -> bytes:
    return compression.zstd.compress(json.dumps_compact(data).encode('utf-8'))  # noqa


class Cli(ap.Cli):
    @ap.cmd(
        ap.arg('-P', '--primary', action='append', default=consts.DEFAULT_PRIMARY_PROVIDERS),
        ap.arg('-u', '--url'),
    )
    def fetch(self) -> None:
        providers = fetch_providers(self.args.url)

        cache_dir = os.path.join(os.path.dirname(__file__), '_cache')
        os.makedirs(cache_dir, exist_ok=True)
        for fn in os.listdir(cache_dir):
            if (
                    os.path.isfile(fp := os.path.join(cache_dir, fn)) and
                    (fn == consts._CACHE_METADATA_FILE_NAME or fn.endswith(consts._CACHE_FILE_SUFFIX))
            ):
                os.unlink(fp)

        for pp in self.args.primary:
            v = providers.pop(pp, {})
            with open(os.path.join(cache_dir, pp + consts._CACHE_FILE_SUFFIX), 'wb') as f:
                f.write(_render_cache_data(v))

        with open(os.path.join(cache_dir, consts._OTHER_PROVIDERS_KEY + consts._CACHE_FILE_SUFFIX), 'wb') as f:
            f.write(_render_cache_data(providers))

        with open(os.path.join(cache_dir, consts._CACHE_METADATA_FILE_NAME), 'w') as f:
            f.write(json.dumps_pretty({
                'fetched_at': datetime.datetime.now(datetime.UTC).isoformat(),
            }))

    @ap.cmd(
        ap.arg('-m', '--marshal', action='store_true'),
    )
    def dump(self) -> None:
        dct: ta.Any = {
            p: cache.get_provider(p) if self.args.marshal else cache.get_provider_raw(p)
            for p in cache.get_all_provider_names()
        }

        print(json.dumps_pretty(dct))


def _main() -> None:
    Cli()()


if __name__ == '__main__':
    _main()
