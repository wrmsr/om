"""
TODO:
 - linux clipboard
"""
import argparse
import io
import os.path
import sys
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..cli import CliModule


with lang.auto_proxy_import(globals()):
    import pytesseract
    import rapidocr_onnxruntime as rapidocr
    from PIL import Image

    from ..clipboard.capi import darwin_cf as darwin_clipboard


##


@dc.dataclass(frozen=True, kw_only=True)
class OcrBackend:
    name: str
    fn: ta.Callable[['Image.Image'], str]
    deps: ta.Sequence[str] | None = None


OCR_BACKENDS: ta.Sequence[OcrBackend] = [

    OcrBackend(
        name='rapidocr',
        fn=lambda img: '\n'.join(text[1] for text in rapidocr.RapidOCR()(_get_img_png_bytes(img))[0] or []),
        deps=[
            'pillow',
            'rapidocr-onnxruntime',
        ],
    ),

    OcrBackend(
        name='tesseract',
        fn=lambda img: pytesseract.image_to_string(img),
        deps=[
            'pillow',
            'pytesseract',
        ],
    ),

]


OCR_BACKENDS_BY_NAME: ta.Mapping[str, OcrBackend] = {b.name: b for b in OCR_BACKENDS}


DEFAULT_OCR_BACKEND = 'rapidocr'


##


def _get_img_data(file: str | None) -> ta.Any:
    if file == '@':
        if sys.platform == 'darwin':
            cis = darwin_clipboard.get_darwin_clipboard_data(types={'public.png'})
            if not cis:
                raise RuntimeError('No clipboard image data found')
            return io.BytesIO(check.not_none(cis[0].data))  # noqa

        else:
            raise OSError(sys.platform)

    elif file:
        return os.path.expanduser(file)

    else:
        return sys.stdin.buffer


def _get_img_png_bytes(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.save(out, format='PNG')
    return out.getvalue()


def _run_ocr(file: str, backend: str) -> None:
    ocr = OCR_BACKENDS_BY_NAME[backend]

    img_data = _get_img_data(file)

    with Image.open(img_data) as img:
        text = ocr.fn(img)

    print(text)


##


def _run_uv_ocr(file: str, backend: str) -> None:
    ocr = OCR_BACKENDS_BY_NAME[backend]

    from ..__about__ import Project  # noqa

    self_ver = f'{Project.name} == {Project.version}'

    dep_vers = {d.split()[0]: d for ds in Project.optional_dependencies.values() for d in ds}

    cmd = [
        'uv',
        'run', '--no-project',
        '--with', self_ver,
        *[s for ss in [
            ['--with', dep_vers[dep]]
            for dep in ocr.deps or []
        ] for s in ss],
        '--',
        'python', '-m', __spec__.name,  # noqa
        '-b', backend,
        file,
    ]

    os.execvp('uv', cmd)


##


def _main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('file', nargs='?')

    parser.add_argument(
        '-b',
        '--backend',
        choices=list(OCR_BACKENDS_BY_NAME),
        default=DEFAULT_OCR_BACKEND,
    )

    parser.add_argument('--uv', action='store_true')

    args = parser.parse_args()

    #

    if args.uv:
        _run_uv_ocr(
            args.file,
            args.backend,
        )

    else:
        _run_ocr(
            args.file,
            args.backend,
        )


# @om-manifest
_CLI_MODULE = CliModule('ocr', __name__)


if __name__ == '__main__':
    _main()
