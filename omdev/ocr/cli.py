"""
Run with python -m omdev.ocr.cli. No CliModule registration is installed by this package.

TODO:
 - linux clipboard
"""
import argparse
import io
import os.path
import sys
import typing as ta

from omcore import check
from omcore import lang

from .backends.darwin import DarwinOcrBackend
from .backends.ocrs import OcrsOcrBackend
from .backends.rapidocr import RapidocrOcrBackend
from .backends.rapidocr import UvRapidocrOcrBackend
from .backends.rapidocrort import RapidocrOnnxruntimeOcrBackend
from .backends.tesseract import DEFAULT_TESSERACT_CONFIG
from .backends.tesseract import TesseractOcrBackend
from .backends.tesseract import UvTesseractOcrBackend
from .backends.uv import DEFAULT_UV_PYTHON
from .types import OcrBackend


with lang.auto_proxy_import(globals()):
    from PIL import Image

    from ..clipboard.capi import darwin_cf as darwin_clipboard


##


DEFAULT_OCR_BACKEND = 'rapidocr'

OCR_BACKEND_NAMES = (
    'rapidocr',
    'rapidocr-ort',
    'rapidocr-torch',
    'tesseract',
    'darwin',
    'ocrs',
    'uv-tesseract',
    'uv-rapidocr-ort',
    'uv-rapidocr-torch',
)

_UV_BACKENDS = {
    'rapidocr': 'uv-rapidocr-ort',
    'rapidocr-ort': 'uv-rapidocr-ort',
    'rapidocr-torch': 'uv-rapidocr-torch',
    'tesseract': 'uv-tesseract',
}


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Recognize an image file, stdin, or @ for the macOS clipboard.',
    )
    parser.add_argument(
        'file',
        nargs='?',
    )
    parser.add_argument(
        '-b',
        '--backend',
        choices=OCR_BACKEND_NAMES,
        default=DEFAULT_OCR_BACKEND,
    )
    parser.add_argument(
        '--list-backends',
        action='store_true',
    )
    parser.add_argument(
        '--uv',
        action='store_true',
        help='Use the selected backend in uv; RapidOCR uses the modern package.',
    )
    parser.add_argument(
        '--uv-python',
        default=DEFAULT_UV_PYTHON,
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=600.,
        help='Timeout for subprocess-backed OCR, in seconds.',
    )
    parser.add_argument(
        '--tesseract-config',
        default=DEFAULT_TESSERACT_CONFIG,
    )
    parser.add_argument('--tesseract-language')
    parser.add_argument('--rapidocr-model-dir')
    parser.add_argument(
        '--torch-device',
        choices=('cpu', 'cuda', 'mps'),
        default='cpu',
    )
    parser.add_argument(
        '--vision-language',
        action='append',
    )
    parser.add_argument(
        '--vision-fast',
        action='store_true',
    )
    parser.add_argument(
        '--vision-no-language-correction',
        action='store_true',
    )
    return parser


def _make_backends(args: argparse.Namespace) -> dict[str, OcrBackend]:
    return {
        'rapidocr': RapidocrOnnxruntimeOcrBackend(),
        'rapidocr-ort': RapidocrOcrBackend(
            engine='onnxruntime',
            model_root_dir=args.rapidocr_model_dir,
        ),
        'rapidocr-torch': RapidocrOcrBackend(
            engine='torch',
            device=args.torch_device,
            model_root_dir=args.rapidocr_model_dir,
        ),
        'tesseract': TesseractOcrBackend(
            config=args.tesseract_config,
            language=args.tesseract_language,
            timeout=args.timeout,
        ),
        'darwin': DarwinOcrBackend(
            languages=args.vision_language,
            fast=args.vision_fast,
            no_language_correction=args.vision_no_language_correction,
        ),
        'ocrs': OcrsOcrBackend(
            timeout=args.timeout,
        ),
        'uv-tesseract': UvTesseractOcrBackend(
            config=args.tesseract_config,
            language=args.tesseract_language,
            python=args.uv_python,
            timeout=args.timeout,
        ),
        'uv-rapidocr-ort': UvRapidocrOcrBackend(
            engine='onnxruntime',
            model_root_dir=args.rapidocr_model_dir,
            python=args.uv_python,
            timeout=args.timeout,
        ),
        'uv-rapidocr-torch': UvRapidocrOcrBackend(
            engine='torch',
            device=args.torch_device,
            model_root_dir=args.rapidocr_model_dir,
            python=args.uv_python,
            timeout=args.timeout,
        ),
    }


def _select_backend_name(name: str, *, uv: bool) -> str:
    if not uv or name.startswith('uv-'):
        return name
    try:
        return _UV_BACKENDS[name]
    except KeyError:
        raise ValueError(f'No uv variant for backend {name!r}') from None


def _get_image_data(file: str | None) -> ta.Any:
    if file == '@':
        if getattr(sys, 'platform') != 'darwin':
            raise OSError(sys.platform)
        items = darwin_clipboard.get_darwin_clipboard_data(types={'public.png'})
        if not items:
            raise RuntimeError('No clipboard image data found')
        return io.BytesIO(check.not_none(items[0].data))  # noqa
    elif file and file != '-':
        return os.path.expanduser(file)
    else:
        return sys.stdin.buffer


def _run_ocr(file: str | None, backend: OcrBackend) -> str:
    with Image.open(_get_image_data(file)) as image:
        return backend.ocr(image)


def _main(argv: ta.Sequence[str] | None = None) -> None:
    parser = _make_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error('--timeout must be positive')

    backends = _make_backends(args)
    if args.list_backends:
        for name, backend in backends.items():
            print(f'{name}\t{"available" if backend.is_available() else "unavailable"}')
        return

    try:
        name = _select_backend_name(args.backend, uv=args.uv)
    except ValueError as e:
        parser.error(str(e))

    backend = backends[name]
    if not backend.is_available():
        parser.error(f'Backend {name!r} is unavailable; see --list-backends and omdev/ocr/README.md')

    text = _run_ocr(args.file, backend)
    sys.stdout.write(text)
    if text and not text.endswith('\n'):
        sys.stdout.write('\n')


if __name__ == '__main__':
    _main()
