#!/usr/bin/env python3
"""
Expose cached pip HTTP artifacts as an offline --find-links directory.

Usage: python pip_cache_to_wheelhouse.py /path/to/wheelhouse

Requires only the standard library. Targets pip's undocumented http-v2 layout.

Caveats:
- Reconstructing wheel filenames from embedded metadata can be ambiguous
- Duplicate distribution versions can collide

====

python pip_cache_to_wheelhouse.py ~/.cache/pip/offline-wheelhouse

python -m pip install \
    --no-index \
    --find-links ~/.cache/pip/offline-wheelhouse \
    mypackage
"""
import email.parser
import pathlib
import re
import subprocess
import sys
import tarfile
import zipfile


##


def link_once(source: pathlib.Path, dest: pathlib.Path) -> bool:
    if dest.is_symlink() or dest.exists():
        return False
    dest.symlink_to(source.resolve())
    return True


def sdist_stem(data: bytes) -> str | None:
    meta = email.parser.BytesParser().parsebytes(data, headersonly=True)
    name, version = meta.get('Name'), meta.get('Version')
    if not name or not version or '/' in name + version or '\\' in name + version:
        return None
    return f"{re.sub(r'[-_.]+', '-', name).lower()}-{version}"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f'usage: {sys.argv[0]} WHEELHOUSE_DIR')

    cache = pathlib.Path(subprocess.check_output(
        [
            sys.executable,
            '-m',
            'pip',
            'cache',
            'dir',
        ],
        text=True,
    ).strip())

    wheelhouse = pathlib.Path(sys.argv[1]).expanduser().resolve()
    wheelhouse.mkdir(parents=True, exist_ok=True)

    linked = 0

    for wheel in (cache / 'wheels').rglob('*.whl'):
        linked += link_once(wheel, wheelhouse / wheel.name)

    for body in (cache / 'http-v2').rglob('*.body'):
        try:
            with body.open('rb') as fp:
                signature = fp.read(6)

            names = []
            if signature.startswith(b'PK'):
                with zipfile.ZipFile(body) as zf:
                    wheels = [
                        p
                        for p in zf.namelist()
                        if p.count('/') == 1 and p.endswith('.dist-info/WHEEL')
                    ]

                    if len(wheels) == 1:
                        info = wheels[0]
                        prefix = info.split('/')[0][:-len('.dist-info')]
                        tags = [
                            line[5:].strip()
                            for line in zf.read(info).decode().splitlines()
                            if line.startswith('Tag: ')
                        ]
                        names = [f'{prefix}-{tag}.whl' for tag in set(tags)]

                    else:
                        sdists = [
                            p
                            for p in zf.namelist()
                            if p.count('/') == 1
                            and p.endswith('/PKG-INFO')
                        ]

                        if len(sdists) == 1:
                            stem = sdist_stem(zf.read(sdists[0]))
                            if stem:
                                names = [f'{stem}.zip']

            else:
                ext = (
                    '.tar.gz' if signature.startswith(b'\x1f\x8b') else
                    '.tar.bz2' if signature.startswith(b'BZh') else
                    '.tar.xz' if signature.startswith(b'\xfd7zXZ\x00') else
                    None
                )

                if ext is not None:
                    with tarfile.open(body, 'r:*') as tf:
                        for member in tf:
                            if (
                                    member.isfile() and
                                    member.name.count('/') == 1 and
                                    member.name.endswith('/PKG-INFO')
                            ):
                                src = tf.extractfile(member)
                                if src is not None:
                                    stem = sdist_stem(src.read(262144))
                                    if stem:
                                        names = [f'{stem}{ext}']
                                break

            for name in names:
                linked += link_once(body, wheelhouse / name)

        except (
                EOFError,
                OSError,
                UnicodeDecodeError,
                ValueError,
                tarfile.TarError,
                zipfile.BadZipFile,
        ):
            continue  # Cached index responses and metadata aren't package archives.

    print(f'Linked {linked} distributions into {wheelhouse}')


if __name__ == '__main__':
    main()
