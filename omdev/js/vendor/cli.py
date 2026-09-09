import argparse
import os
import typing as ta

from .generation import vendor
from .manifests import load_lock
from .manifests import load_manifest
from .manifests import render_manifest
from .models import AddRequest
from .models import ManifestUpdateResult
from .models import OutdatedRequest
from .models import OutdatedResult
from .models import RegistryConfig
from .models import RemoveRequest
from .models import ResolveRequest
from .models import UpdateRequest
from .models import VendorRequest
from .models import VerifyRequest
from .operations import add
from .operations import outdated
from .operations import parse_package_argument
from .operations import remove
from .operations import update
from .outputs import render_lock
from .outputs import write_path
from .resolution import resolve
from .verification import verify


##


_COMMANDS: ta.Sequence[str] = (
    'add',
    'update',
    'remove',
    'outdated',
    'resolve',
    'vendor',
    'verify',
)


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Manage, vendor, and verify browser ESM dependencies')
    parser.add_argument('command', choices=_COMMANDS)
    parser.add_argument('packages', nargs='*')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--cache-dir', default='.cache/jsvendor')
    parser.add_argument('--registry', default='https://registry.npmjs.org')
    parser.add_argument('--registry-timeout', default=60.0, type=float)
    return parser.parse_args(argv)


def _registry(args: argparse.Namespace, /) -> RegistryConfig:
    return RegistryConfig(url=args.registry, timeout=args.registry_timeout)


def _write_update(args: argparse.Namespace, result: ManifestUpdateResult, /) -> None:
    write_path(args.manifest, render_manifest(result.manifest))
    write_path(os.path.join(args.destination, 'lock.json'), render_lock(result.lock))
    print(
        f'Resolved {len(result.manifest.roots)} roots to {len(result.lock.packages)} packages; '
        f'run vendor to regenerate files.',
    )


def _package_names(values: list[str], /) -> tuple[str, ...]:
    names = []
    for value in values:
        argument = parse_package_argument(value)
        if argument.version is not None:
            raise ValueError(f'Package version is not allowed here: {value}')
        names.append(argument.name)
    return tuple(names)


def _print_outdated(result: OutdatedResult, /) -> None:
    if not result.packages:
        print('All root packages are current.')
        return

    rows = [('Package', 'Current', 'Wanted', 'Latest', 'Requirement')]
    rows.extend(
        (package.name, package.current, package.wanted, package.latest, package.requirement)
        for package in result.packages
    )
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    for row in rows:
        print('  '.join(value.ljust(widths[index]) for index, value in enumerate(row)).rstrip())


def _main(argv=None) -> None:
    args = _parse_args(argv)
    manifest = load_manifest(args.manifest)
    registry = _registry(args)

    if args.command == 'add':
        _write_update(args, add(AddRequest(
            manifest=manifest,
            packages=tuple(parse_package_argument(value) for value in args.packages),
            registry=registry,
        )))
        return

    if args.command == 'update':
        _write_update(args, update(UpdateRequest(
            manifest=manifest,
            packages=tuple(parse_package_argument(value) for value in args.packages),
            registry=registry,
        )))
        return

    if args.command == 'remove':
        _write_update(args, remove(RemoveRequest(
            manifest=manifest,
            packages=_package_names(args.packages),
            registry=registry,
        )))
        return

    if args.command == 'outdated':
        lock = load_lock(os.path.join(args.destination, 'lock.json'))
        _print_outdated(outdated(OutdatedRequest(
            manifest=manifest,
            lock=lock,
            packages=_package_names(args.packages),
            registry=registry,
        )))
        return

    if args.packages:
        raise ValueError(f'{args.command} does not accept package arguments')

    if args.command == 'resolve':
        result = resolve(ResolveRequest(
            manifest=manifest,
            registry=registry,
        ))
        write_path(os.path.join(args.destination, 'lock.json'), render_lock(result.lock))
        return

    lock = load_lock(os.path.join(args.destination, 'lock.json'))

    if args.command == 'vendor':
        vendor(VendorRequest(
            manifest=manifest,
            lock=lock,
            destination=args.destination,
            cache_directory=args.cache_dir,
        ))

    else:
        verify(VerifyRequest(
            manifest=manifest,
            lock=lock,
            destination=args.destination,
        ))


if __name__ == '__main__':
    _main()
