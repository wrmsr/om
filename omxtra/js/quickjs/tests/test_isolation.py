import pytest

from ... import quickjs


##


# Globals the qjs CLI environment would provide but a Context deliberately must not: the std/os modules, the
# js_std_add_helpers globals (print, console, scriptArgs), and anything event-loop-ish.
_ABSENT_GLOBALS = [
    'std',
    'os',
    'print',
    'console',
    'scriptArgs',
    'setTimeout',
    'setInterval',
    'navigator',
]


def _import_module(ctx, mod, gname):
    ctx.eval(f'import * as m from "{mod}"; globalThis.{gname} = m', module=True)
    ctx.execute_pending_jobs()


def test_default_context_has_no_ambient_globals():
    ctx = quickjs.Context()
    for name in _ABSENT_GLOBALS:
        assert ctx.eval(f'typeof {name}') == 'undefined', name


def test_default_context_cannot_import_modules():
    ctx = quickjs.Context()
    for mod in ['qjs:std', 'qjs:os', 'qjs:bjson', 'std', 'os', './x.js']:
        with pytest.raises(quickjs.JsError):
            _import_module(ctx, mod, 'm')


def test_module_flags_are_independent():
    std_only = quickjs.Context(with_std=True)
    _import_module(std_only, 'qjs:std', '_std')
    with pytest.raises(quickjs.JsError):
        _import_module(std_only, 'qjs:bjson', '_bjson')

    bjson_only = quickjs.Context(with_bjson=True)
    _import_module(bjson_only, 'qjs:bjson', '_bjson')
    for mod in ['qjs:std', 'qjs:os']:
        with pytest.raises(quickjs.JsError):
            _import_module(bjson_only, mod, 'm')

    both = quickjs.Context(with_std=True, with_bjson=True)
    _import_module(both, 'qjs:std', '_std')
    _import_module(both, 'qjs:bjson', '_bjson')


def test_with_bjson_module():
    ctx = quickjs.Context(with_bjson=True)
    _import_module(ctx, 'qjs:bjson', '_bjson')

    assert ctx.eval('typeof _bjson.read') == 'function'
    assert ctx.eval('typeof _bjson.write') == 'function'
    assert ctx.eval('typeof _bjson.WRITE_OBJ_REFERENCE') == 'number'

    # A JS-side round trip through the same serializer the Python API uses.
    ctx.eval(
        'globalThis.rt = function(v) {'
        '    var b = _bjson.write(v, _bjson.WRITE_OBJ_REFERENCE);'
        '    return _bjson.read(b, 0, b.byteLength, _bjson.READ_OBJ_REFERENCE);'
        '};',
    )
    assert ctx.eval('rt({a: [1, "x"]}).a[1] === "x"') is True
    # Exercises the local JS_ReadRegExp reference-registration patch from the JS side.
    assert ctx.eval('(function() { var s = {v: 1}; var r = rt({re: /a/, x: s, x2: s}); return r.x2 === r.x; })()') \
        is True


def test_bjson_python_interop():
    ctx = quickjs.Context(with_bjson=True)
    _import_module(ctx, 'qjs:bjson', '_bjson')

    # Python-written blob, read by JS.
    blob = ctx.eval('({a: 1, arr: [1, 2]})').serialize()
    ctx.set('blob', blob)
    assert ctx.eval(
        '(function() {'
        '    var b = blob.buffer;'
        '    var v = _bjson.read(b, 0, b.byteLength, _bjson.READ_OBJ_REFERENCE);'
        '    return v.a === 1 && v.arr[1] === 2;'
        '})()',
    ) is True

    # JS-written blob, read by Python.
    out = ctx.eval('_bjson.write({b: 2}, _bjson.WRITE_OBJ_REFERENCE)')
    ctx.set('r', ctx.deserialize(out.to_bytes()))
    assert ctx.eval('r.b') == 2


def test_with_std_installs_importable_modules():
    ctx = quickjs.Context(with_std=True)

    # Still modules, not globals - the ambient namespace stays clean.
    for name in _ABSENT_GLOBALS:
        assert ctx.eval(f'typeof {name}') == 'undefined', name

    _import_module(ctx, 'qjs:std', '_std')
    assert ctx.eval('typeof _std.open') == 'function'
    assert ctx.eval('typeof _std.getenv') == 'function'
    assert ctx.eval('typeof _std.getenv("PATH")') == 'string'

    _import_module(ctx, 'qjs:os', '_os')
    assert ctx.eval('typeof _os.remove') == 'function'
    assert ctx.eval('Array.isArray(_os.readdir(".")[0])') is True


def test_with_std_is_keyword_only_and_off_by_default():
    with pytest.raises(TypeError):
        quickjs.Context(True)  # type: ignore[call-arg]  # deliberately invalid

    for ctx in [quickjs.Context(), quickjs.Context(with_std=False)]:
        with pytest.raises(quickjs.JsError):
            _import_module(ctx, 'qjs:std', 'm')


def test_with_std_contexts_are_independent():
    trusted = quickjs.Context(with_std=True)
    untrusted = quickjs.Context()

    _import_module(trusted, 'qjs:std', '_std')
    with pytest.raises(quickjs.JsError):
        _import_module(untrusted, 'qjs:std', '_std')
