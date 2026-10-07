# OCR

A Pillow image in, a string out:

```python
from PIL import Image

from omdev.ocr.backends.darwin import DarwinOcrBackend

backend = DarwinOcrBackend(no_language_correction=True)
with Image.open('screenshot.png') as image:
    text = backend.ocr(image)
```

The interface in `types.py` has only `ocr(image) -> str` and `is_available() -> bool`.
Availability is deliberately shallow: package specs, executable lookup, or the current OS. It does not validate native
libraries, hardware, executables wrapped by Python packages, or model files. Errors are not hidden by fallback
selection.
Constructors retain configuration; optional dependencies are accessed on execution. There is no shared model instance.

## CLI

This package does not register a `CliModule` or change `omdev.tools.ocr`.

```sh
python -m omdev.ocr.cli --list-backends
python -m omdev.ocr.cli -b darwin @
python -m omdev.ocr.cli -b ocrs screenshot.png
cat screenshot.png | python -m omdev.ocr.cli -b tesseract
python -m omdev.ocr.cli -b rapidocr-torch --torch-device mps screenshot.png
python -m omdev.ocr.cli -b uv-rapidocr-torch screenshot.png
```

Omitting the filename or using `-` reads image bytes from stdin. `@` uses the existing macOS clipboard implementation's
`public.png` data. Other platforms' clipboards remain unsupported. Text is written without stripping whitespace or
adding
an extra blank line; the CLI adds a terminating newline only when a nonempty result lacks one.

| CLI name | Implementation | Shallow availability check |
| --- | --- | --- |
| `rapidocr` (default) | Legacy `rapidocr_onnxruntime` | Package spec |
| `rapidocr-ort` | Modern `rapidocr`, ONNX Runtime engine | Both package specs |
| `rapidocr-torch` | Modern `rapidocr`, native Torch engine | Both package specs |
| `tesseract` | `pytesseract.image_to_string` | `pytesseract` package spec |
| `darwin` | System Vision framework through ctypes | Running on Darwin |
| `ocrs` | `ocrs` subprocess | Executable on PATH |
| `uv-tesseract` | Standalone pytesseract worker in uv | `uv` on PATH |
| `uv-rapidocr-ort` | Standalone modern RapidOCR/ORT worker in uv | `uv` on PATH |
| `uv-rapidocr-torch` | Standalone modern RapidOCR/Torch worker in uv | `uv` on PATH |

`--uv` is a convenience alias for the corresponding uv backend. In particular, `--uv -b rapidocr` selects
`uv-rapidocr-ort`: unlike the non-uv legacy backend, it uses the **modern** package. Darwin and ocrs have no uv variant.

`--timeout` bounds subprocess execution, including uv installation/model loading. It does not impose a hard deadline on
in-process RapidOCR or Vision calls. All selections are explicit; selecting an unavailable backend is an error.

## Tesseract

`TesseractOcrBackend` and `UvTesseractOcrBackend` accept `config`, `language`, and `timeout` keyword arguments.
The default config is `--oem 1 --psm 6`, and `nice=0` is kept fixed: niceness is scheduling priority, not recognition
quality.
Neither variant installs the system Tesseract executable or its language data. `tessdata_best` is separately installed
model data, not an effort/quality flag.

```sh
python -m omdev.ocr.cli -b tesseract --tesseract-config='--oem 1 --psm 7' line.png
python -m omdev.ocr.cli -b tesseract --tesseract-config='--oem 1 --psm 11' screenshot.png
python -m omdev.ocr.cli -b tesseract --tesseract-language eng screenshot.png
python -m omdev.ocr.cli -b uv-tesseract --tesseract-config='--oem 1 --psm 6' screenshot.png
```

An empty `config=''` restores the original wrapper's use of Tesseract's own segmentation defaults. A custom tessdata
location can be passed using `--tessdata-dir` inside `config`.

## RapidOCR

`backends/rapidocrort.py` preserves the old `RapidOCR()(png_bytes)` and newline-joined row text behavior.
It retains the old package's interpreter/dependency restrictions; a spec check does not prove the package will import.

`backends/rapidocr.py` contains `RapidocrOcrBackend` and `UvRapidocrOcrBackend`. Both select the engine for detection,
classification, and recognition, using PP-OCRv4 mobile models and the `ch` model family explicitly. The modern result's
`txts` is joined with newlines, with an empty string for no detections. Engines are constructed per call.

The constructor's `engine` is `onnxruntime` or `torch`. `device` is `cpu` by default; `cuda` and `mps` are supported for
Torch only. `--torch-device` controls the Torch selections in the CLI. These wrappers do not probe accelerators in
`is_available()` and do not add custom kernels or tensor abstractions.

For a direct modern installation, install `rapidocr>=3.9.2,<4` and the chosen engine package (`onnxruntime` or `torch`)
in an environment supporting their native dependencies. Selecting the Torch engine does not request ONNX Runtime.
The modern pipeline still has its own image-processing dependencies; this package does not replace them.

`model_root_dir` (CLI: `--rapidocr-model-dir`) overrides the modern model download directory. Direct backends otherwise
leave it to RapidOCR. The uv variant defaults to `~/.cache/omdev/ocr/rapidocr` so downloaded models outlive its
temporary
environment. RapidOCR itself creates/manages this directory. This does not promise numerical identity between modern
Torch checkpoints and the legacy ONNX artifacts.

## uv workers

The shared `UvOcrBackend` extracts a self-contained worker with `inspect.getsource`, writes a temporary script and JSON
arguments, and sends PNG bytes on stdin. The script writes the result to a separate UTF-8 file; child stdout/stderr go
to
stderr so installation or model messages cannot corrupt OCR text. The temporary directory is removed on success or
error.
Timeout/interrupt cleanup kills the uv process group, including its worker when it remains in that group.

Workers import only their third-party dependencies and stdlib helpers. They do not install/import omdev or reenter its
CLI.
Normal uv dependency caching is left enabled. The default interpreter request is `cpython@3.12`, not the parent
interpreter.
The invocation uses `--no-project --isolated --no-config` and `python -I`. Override it with `--uv-python`, for example
`--uv-python '3.14+gil'` with a recent uv and compatible dependencies.

The generated workers target ordinary Python 3.12+, independently of the containing repository's Python 3.14 target.
Source extraction requires the worker's source to be available through its loader.

## Apple Vision

`DarwinOcrBackend` serializes PNG bytes and calls the small binding in `omdev/capi/darwin/vn.py`.
The binding loads Foundation, Vision, and libobjc and uses only synchronous recognition. It does not need PyObjC, a
compiled
helper, Objective-C blocks, callbacks, or a general object bridge.

Each message signature has its own fixed ctypes callable. A per-call autorelease pool bounds temporary lifetimes;
`new`/`alloc` + `init` results are released explicitly, and strings/errors are copied before releasing their owners.
Requests, handlers, and error storage are not reused across calls. Objective-C exceptions are not catchable through this
binding; reported `NSError` failures become `VisionError`.

Accurate recognition and language correction are the defaults. Use `--vision-fast` to trade quality for speed,
`--vision-no-language-correction` for identifiers/filenames, and repeated `--vision-language` options to provide an
ordered
language list (for example `en-US`, `fr-FR`). The binding preserves Vision's observation order and exposes no geometry.

The native path needs validation on macOS, including your free-threaded interpreter. Useful manual checks are a normal
screenshot, a blank image, invalid encoded bytes passed to `vn.recognize_text`, non-ASCII output, and repeated calls.

## ocrs

Install the executable independently:

```sh
cargo install ocrs-cli --locked
```

`OcrsOcrBackend` sends PNG on stdin and decodes plain-text stdout as UTF-8. It accepts an optional `executable` and
`timeout`.
Models and their downloads/caches are managed by ocrs. Its optional clipboard feature is not needed. Executable failures
propagate as subprocess errors.

## Tests

```sh
python -m pytest omdev/ocr/tests omdev/ocr/backends/tests
```

The tests cover adapter options/result handling, PNG transport, worker execution/error cleanup, process timeout, and CLI
parsing/input handling. Third-party calls are substituted where needed; subprocess transport tests use small executable
stand-ins rather than downloading models. The optional Pillow roundtrip tests use real Pillow when installed. There are
no tests of lazy-import behavior and no automated native OCR/model-download smoke tests.

Upstream API references used for these adapters:

- https://github.com/RapidAI/RapidOCR/tree/v3.9.2/python/rapidocr
- https://github.com/madmaze/pytesseract
- https://github.com/robertknight/ocrs/tree/main/ocrs-cli
- https://developer.apple.com/documentation/vision/vnimagerequesthandler
- https://developer.apple.com/documentation/vision/vnrecognizetextrequest
- https://docs.astral.sh/uv/reference/cli/
