"""
Only the Objective-C calls needed for synchronous Vision text recognition of encoded image bytes.

No Python callbacks, Objective-C blocks, structure-return messages, or general-purpose object bridge are used. Objects
returned by alloc/init/new are released explicitly; other temporaries live in a per-call autorelease pool. NSError is
translated to VisionError. Objective-C exceptions cannot be unwound safely through ctypes.
"""
import contextlib
import ctypes as ct
import os
import sys
import typing as ta

from omcore import lang


##


class VisionError(Exception):
    pass


class _Vision:
    def __init__(self) -> None:
        super().__init__()

        if sys.platform != 'darwin':
            raise OSError(sys.platform)

        # Retain the library handles for at least as long as the bound callables.
        self._foundation = ct.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation')
        self._vision = ct.CDLL('/System/Library/Frameworks/Vision.framework/Vision')
        self._objc = ct.CDLL('/usr/lib/libobjc.A.dylib')

        self._get_class = self._objc.objc_getClass
        self._get_class.argtypes = [ct.c_char_p]
        self._get_class.restype = ct.c_void_p

        self._get_selector = self._objc.sel_registerName
        self._get_selector.argtypes = [ct.c_char_p]
        self._get_selector.restype = ct.c_void_p

        # Each prototype is a distinct immutable callable. Never mutate objc_msgSend.argtypes/restype between calls:
        # besides being the wrong ABI for some signatures, that would race on free-threaded Python.
        # Apple's BOOL is C bool on arm64 and signed char on Intel macOS.
        objc_bool = ct.c_bool if os.uname().machine == 'arm64' else ct.c_byte
        symbol = ('objc_msgSend', self._objc)
        self._id = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p)(symbol)
        self._id_id = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)(symbol)
        self._id_id_id = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)(symbol)
        self._id_uint = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_ulong)(symbol)
        self._id_bytes_size = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_ulong)(symbol)
        self._id_cstr = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_char_p)(symbol)
        self._uint = ct.CFUNCTYPE(ct.c_ulong, ct.c_void_p, ct.c_void_p)(symbol)
        self._cstr = ct.CFUNCTYPE(ct.c_char_p, ct.c_void_p, ct.c_void_p)(symbol)
        self._void = ct.CFUNCTYPE(None, ct.c_void_p, ct.c_void_p)(symbol)
        self._void_id = ct.CFUNCTYPE(None, ct.c_void_p, ct.c_void_p, ct.c_void_p)(symbol)
        self._void_int = ct.CFUNCTYPE(None, ct.c_void_p, ct.c_void_p, ct.c_long)(symbol)
        self._void_bool = ct.CFUNCTYPE(None, ct.c_void_p, ct.c_void_p, objc_bool)(symbol)
        self._perform = ct.CFUNCTYPE(objc_bool, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.POINTER(ct.c_void_p))(symbol)

    def _cls(self, name: bytes) -> int:
        if not (obj := self._get_class(name)):
            raise VisionError(f'Objective-C class not found: {name!r}')
        return obj

    def _sel(self, name: bytes) -> int:
        return self._get_selector(name)

    def _require(self, obj: int | None, description: str) -> int:
        if not obj:
            raise VisionError(description)
        return obj

    def _release(self, obj: int) -> None:
        self._void(obj, self._sel(b'release'))

    def _string(self, obj: int | None) -> str:
        if not obj:
            return ''
        value = self._cstr(obj, self._sel(b'UTF8String'))
        if value is None:
            raise VisionError('NSString could not be converted to UTF-8')
        return value.decode('utf-8')

    def _make_languages(self, languages: ta.Sequence[str]) -> int:
        array = self._require(
            self._id(self._cls(b'NSMutableArray'), self._sel(b'array')),
            'Could not create recognitionLanguages',
        )
        for language in languages:
            string = self._require(
                self._id_cstr(self._cls(b'NSString'), self._sel(b'stringWithUTF8String:'), language.encode('utf-8')),
                'Could not create a recognition language string',
            )
            self._void_id(array, self._sel(b'addObject:'), string)
        return array

    def recognize_text(
            self,
            data: bytes,
            *,
            languages: ta.Sequence[str] | None,
            fast: bool,
            no_language_correction: bool,
    ) -> str:
        with contextlib.ExitStack() as stack:
            pool = self._require(
                self._id(self._cls(b'NSAutoreleasePool'), self._sel(b'new')),
                'Could not create an autorelease pool',
            )
            stack.callback(self._void, pool, self._sel(b'drain'))

            # dataWithBytes:length: copies the bytes; do not replace this with a no-copy initializer.
            buffer = ct.create_string_buffer(data)
            ns_data = self._require(
                self._id_bytes_size(self._cls(b'NSData'), self._sel(b'dataWithBytes:length:'), buffer, len(data)),
                'Could not create image NSData',
            )
            options = self._require(
                self._id(self._cls(b'NSDictionary'), self._sel(b'dictionary')),
                'Could not create image request options',
            )

            request = self._require(
                self._id(self._cls(b'VNRecognizeTextRequest'), self._sel(b'new')),
                'Could not initialize VNRecognizeTextRequest',
            )
            stack.callback(self._release, request)

            # VNRequestTextRecognitionLevel: accurate = 0, fast = 1 (NSInteger).
            self._void_int(request, self._sel(b'setRecognitionLevel:'), 1 if fast else 0)
            self._void_bool(request, self._sel(b'setUsesLanguageCorrection:'), not no_language_correction)
            if languages is not None:
                self._void_id(request, self._sel(b'setRecognitionLanguages:'), self._make_languages(languages))

            allocated_handler = self._require(
                self._id(self._cls(b'VNImageRequestHandler'), self._sel(b'alloc')),
                'Could not allocate VNImageRequestHandler',
            )
            # Only the result of init is owned: init may replace the allocated object or release it and return nil.
            handler = self._require(
                self._id_id_id(allocated_handler, self._sel(b'initWithData:options:'), ns_data, options),
                'Could not initialize VNImageRequestHandler',
            )
            stack.callback(self._release, handler)

            requests = self._require(
                self._id_id(self._cls(b'NSArray'), self._sel(b'arrayWithObject:'), request),
                'Could not create the request array',
            )
            error = ct.c_void_p()
            if not self._perform(handler, self._sel(b'performRequests:error:'), requests, ct.byref(error)):
                description = self._string(self._id(error, self._sel(b'localizedDescription'))) if error.value else ''
                raise VisionError(description or 'Vision performRequests:error: failed without an NSError')

            results = self._id(request, self._sel(b'results'))
            if not results:
                return ''

            lines = []
            for i in range(self._uint(results, self._sel(b'count'))):
                observation = self._id_uint(results, self._sel(b'objectAtIndex:'), i)
                candidates = self._id_uint(observation, self._sel(b'topCandidates:'), 1)
                if not candidates or not self._uint(candidates, self._sel(b'count')):
                    continue
                candidate = self._id_uint(candidates, self._sel(b'objectAtIndex:'), 0)
                lines.append(self._string(self._id(candidate, self._sel(b'string'))))

            # Strings are copied into Python before draining the pool. Preserve Vision's observation order.
            return '\n'.join(lines)


@lang.cached_function
def _get_vision() -> _Vision:
    return _Vision()


def recognize_text(
        data: bytes,
        *,
        languages: ta.Sequence[str] | None = None,
        fast: bool = False,
        no_language_correction: bool = False,
) -> str:
    if not isinstance(data, bytes):
        raise TypeError(data)
    if not data:
        raise ValueError('Empty image data')
    if isinstance(languages, str):
        raise TypeError(languages)
    if languages is not None:
        languages = tuple(languages)
        if not languages or any(not isinstance(s, str) or not s or '\0' in s for s in languages):
            raise ValueError(languages)

    return _get_vision().recognize_text(
        data,
        languages=languages,
        fast=fast,
        no_language_correction=no_language_correction,
    )
