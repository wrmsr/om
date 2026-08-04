// @om-cext {
//   "extra_sources": [
//     "quickjs-amalgam.c"
//   ],
//   "extra_headers": [
//     "quickjs.h",
//     "quickjs-libc.h"
//   ],
//   "extra_compile_args": [
//     "-Wno-sign-compare",
//     "-Wno-unreachable-code",
//     "-Wno-unused-but-set-variable",
//     "-Wno-unused-const-variable",
//     "-Wno-unused-function"
//   ],
//   "define_macros": {
//     "_GNU_SOURCE": "1"
//   },
//   "libraries": [
//     ["m", "linux"]
//   ]
// }
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#include "quickjs.h"

//

#define _MODULE_NAME "_pyqjsng"
#define _PACKAGE_NAME "pyqjsng"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

typedef struct pyqjsng_state {
    PyObject *context_type;
    PyObject *object_type;
    PyObject *js_error;
    PyObject *js_stack_overflow_error;
    PyObject *js_interrupt_error;
} pyqjsng_state;

static pyqjsng_state * get_pyqjsng_state(PyObject *module)
{
    void *state = PyModule_GetState(module);
    assert(state != NULL);
    return (pyqjsng_state *)state;
}

//

enum {
    QJS_INTERRUPT_NONE = 0,
    QJS_INTERRUPT_REQUESTED = 1,
    QJS_INTERRUPT_DEADLINE = 2,
};

typedef struct ContextObject {
    PyObject_HEAD

    PyObject *module;

    JSRuntime *runtime;
    JSContext *context;

    // A QuickJS runtime is strictly single-threaded, so every use of it is serialized through this recursive
    // (owner-tracked) mutex. This is load-bearing on freethreaded builds, where multiple Python threads may call
    // into the same Context concurrently.
    PyMutex mutex;
    _Atomic unsigned long lock_owner;
    Py_ssize_t lock_depth;

    // Non-NULL exactly while the lock-owning thread is detached inside JS execution. The Python-callable
    // trampoline uses it to reattach, and its NULL-ness to know whether the JS entry point detached at all.
    PyThreadState *thread_state;

    _Atomic int interrupt_flag;
    int interrupt_reason;
    int64_t time_limit_ns;
    int64_t deadline_ns;

    // Python callables handed to JS. JS function objects hold only borrowed pointers (so JS-side finalizers
    // never need to touch Python state), and this list keeps them alive for the life of the Context.
    PyObject *callables;

    // A Python exception captured in the trampoline, propagating outward through JS as a marked JS error.
    PyObject *pending_pyexc;
} ContextObject;

typedef struct ObjectObject {
    PyObject_HEAD

    ContextObject *ctx;  // NULL once released by tp_clear
    JSValue value;
} ObjectObject;

static pyqjsng_state * ctx_get_state(ContextObject *self)
{
    return get_pyqjsng_state(self->module);
}

//

static int64_t monotonic_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000 + (int64_t)ts.tv_nsec;
}

static void ctx_lock(ContextObject *self)
{
    unsigned long tid = PyThread_get_thread_ident();
    if (atomic_load_explicit(&self->lock_owner, memory_order_relaxed) == tid) {
        self->lock_depth++;
        return;
    }

    PyMutex_Lock(&self->mutex);
    atomic_store_explicit(&self->lock_owner, tid, memory_order_relaxed);
    self->lock_depth = 1;
    // QuickJS checks stack overflow against a recorded stack top, which must be refreshed when the runtime
    // migrates between threads.
    JS_UpdateStackTop(self->runtime);
}

static void ctx_unlock(ContextObject *self)
{
    if (--self->lock_depth == 0) {
        atomic_store_explicit(&self->lock_owner, 0, memory_order_relaxed);
        PyMutex_Unlock(&self->mutex);
    }
}

// Called with the lock held before any JS entry point that executes code. Only the outermost entry resets
// interrupt / deadline state, so reentrant evals share the outer deadline.
static void ctx_begin_run(ContextObject *self)
{
    if (self->lock_depth == 1) {
        atomic_store_explicit(&self->interrupt_flag, 0, memory_order_relaxed);
        self->interrupt_reason = QJS_INTERRUPT_NONE;
        self->deadline_ns = self->time_limit_ns != 0 ? monotonic_ns() + self->time_limit_ns : 0;
    }
}

static void ctx_detach(ContextObject *self)
{
    self->thread_state = PyEval_SaveThread();
}

static void ctx_attach(ContextObject *self)
{
    PyEval_RestoreThread(self->thread_state);
    self->thread_state = NULL;
}

static int qjs_interrupt_handler(JSRuntime *rt, void *opaque)
{
    (void)rt;
    ContextObject *self = (ContextObject *)opaque;

    // Runs on the JS thread while it is detached from Python - must not touch any Python state.
    if (atomic_exchange_explicit(&self->interrupt_flag, 0, memory_order_acq_rel)) {
        self->interrupt_reason = QJS_INTERRUPT_REQUESTED;
        return 1;
    }
    if (self->deadline_ns != 0 && monotonic_ns() >= self->deadline_ns) {
        self->interrupt_reason = QJS_INTERRUPT_DEADLINE;
        return 1;
    }
    return 0;
}

//

static PyObject * wrap_js_value(ContextObject *self, JSValue value);
static PyObject * js_to_py(ContextObject *self, JSValueConst value);
static JSValue py_to_js(ContextObject *self, PyObject *item, int depth);

// Converts the current JS exception into a raised Python exception. Always returns NULL. Must be called with
// the lock held and the thread attached.
static PyObject * raise_js_error(ContextObject *self)
{
    JSContext *jctx = self->context;
    pyqjsng_state *state = ctx_get_state(self);
    JSValue exc = JS_GetException(jctx);

    if (self->pending_pyexc != NULL) {
        int from_python = 0;
        if (JS_IsObject(exc)) {
            JSValue marker = JS_GetPropertyStr(jctx, exc, "pythonError");
            if (JS_IsException(marker)) {
                JS_FreeValue(jctx, JS_GetException(jctx));
            } else {
                from_python = JS_ToBool(jctx, marker) == 1;
                JS_FreeValue(jctx, marker);
            }
        }
        if (from_python) {
            PyObject *pyexc = self->pending_pyexc;
            self->pending_pyexc = NULL;
            JS_FreeValue(jctx, exc);
            PyErr_SetRaisedException(pyexc);
            return NULL;
        }
        // The marked error was caught and replaced JS-side; the stashed Python exception is stale.
        Py_CLEAR(self->pending_pyexc);
    }

    PyObject *exc_type = state->js_error;
    if (self->interrupt_reason != QJS_INTERRUPT_NONE && JS_IsUncatchableError(exc)) {
        exc_type = state->js_interrupt_error;
    }

    const char *msg = JS_ToCString(jctx, exc);
    if (msg == NULL) {
        JS_FreeValue(jctx, JS_GetException(jctx));
    }

    const char *stack = NULL;
    if (JS_IsError(exc)) {
        JSValue stack_value = JS_GetPropertyStr(jctx, exc, "stack");
        if (JS_IsException(stack_value)) {
            JS_FreeValue(jctx, JS_GetException(jctx));
        } else {
            if (JS_IsString(stack_value)) {
                stack = JS_ToCString(jctx, stack_value);
                if (stack == NULL) {
                    JS_FreeValue(jctx, JS_GetException(jctx));
                }
            }
            JS_FreeValue(jctx, stack_value);
        }
    }

    if (exc_type == state->js_error && msg != NULL && strstr(msg, "Maximum call stack size exceeded") != NULL) {
        exc_type = state->js_stack_overflow_error;
    }

    PyObject *exc_obj = PyObject_CallFunction(exc_type, "s", msg != NULL ? msg : "unknown JS error");
    if (exc_obj != NULL) {
        PyObject *stack_obj = stack != NULL ? PyUnicode_FromString(stack) : Py_NewRef(Py_None);
        if (stack_obj != NULL) {
            if (PyObject_SetAttrString(exc_obj, "js_stack", stack_obj) < 0) {
                PyErr_Clear();
            }
            Py_DECREF(stack_obj);
        } else {
            PyErr_Clear();
        }
        PyErr_SetObject(exc_type, exc_obj);
        Py_DECREF(exc_obj);
    }

    if (msg != NULL) {
        JS_FreeCString(jctx, msg);
    }
    if (stack != NULL) {
        JS_FreeCString(jctx, stack);
    }
    JS_FreeValue(jctx, exc);
    return NULL;
}

// Turns a JS-API failure (exception state in the context) into a Python exception, passing successful values
// through. Lets JS-API-heavy code keep the 'Python exception set on failure' convention.
static JSValue jsval_or_pyerr(ContextObject *self, JSValue value)
{
    if (JS_IsException(value)) {
        raise_js_error(self);
    }
    return value;
}

// Consumes 'value', returning its Python conversion, or raising if it is an exception. The common tail of
// every JS entry point.
static PyObject * return_js_value(ContextObject *self, JSValue value)
{
    if (JS_IsException(value)) {
        return raise_js_error(self);
    }
    // The run completed: any stashed Python exception was caught and handled JS-side.
    Py_CLEAR(self->pending_pyexc);
    PyObject *result = js_to_py(self, value);
    JS_FreeValue(self->context, value);
    return result;
}

//

static PyObject * js_to_py(ContextObject *self, JSValueConst value)
{
    JSContext *jctx = self->context;

    switch (JS_VALUE_GET_NORM_TAG(value)) {
        case JS_TAG_INT:
            return PyLong_FromLong(JS_VALUE_GET_INT(value));

        case JS_TAG_FLOAT64:
            return PyFloat_FromDouble(JS_VALUE_GET_FLOAT64(value));

        case JS_TAG_BOOL:
            return PyBool_FromLong(JS_VALUE_GET_BOOL(value));

        case JS_TAG_NULL:
        case JS_TAG_UNDEFINED:
            Py_RETURN_NONE;

        case JS_TAG_STRING:
        case JS_TAG_STRING_ROPE: {
            size_t len;
            const char *cstr = JS_ToCStringLen(jctx, &len, value);
            if (cstr == NULL) {
                return raise_js_error(self);
            }
            PyObject *result = PyUnicode_FromStringAndSize(cstr, (Py_ssize_t)len);
            JS_FreeCString(jctx, cstr);
            return result;
        }

        case JS_TAG_BIG_INT:
        case JS_TAG_SHORT_BIG_INT: {
            const char *cstr = JS_ToCString(jctx, value);
            if (cstr == NULL) {
                return raise_js_error(self);
            }
            PyObject *result = PyLong_FromString(cstr, NULL, 10);
            JS_FreeCString(jctx, cstr);
            return result;
        }

        case JS_TAG_EXCEPTION:
            return raise_js_error(self);

        default:
            // Objects, functions, symbols, modules: wrapped, preserving identity.
            return wrap_js_value(self, JS_DupValue(jctx, value));
    }
}

static JSValue py_long_to_js_bigint(ContextObject *self, PyObject *item)
{
    JSContext *jctx = self->context;

    PyObject *text = PyObject_Str(item);
    if (text == NULL) {
        return JS_EXCEPTION;
    }
    const char *utf8 = PyUnicode_AsUTF8(text);
    if (utf8 == NULL) {
        Py_DECREF(text);
        return JS_EXCEPTION;
    }

    JSValue global = JS_GetGlobalObject(jctx);
    JSValue bigint_ctor = JS_GetPropertyStr(jctx, global, "BigInt");
    JS_FreeValue(jctx, global);
    if (JS_IsException(bigint_ctor)) {
        Py_DECREF(text);
        raise_js_error(self);
        return JS_EXCEPTION;
    }

    JSValue arg = JS_NewString(jctx, utf8);
    Py_DECREF(text);
    if (JS_IsException(arg)) {
        JS_FreeValue(jctx, bigint_ctor);
        raise_js_error(self);
        return JS_EXCEPTION;
    }

    JSValue result = JS_Call(jctx, bigint_ctor, JS_UNDEFINED, 1, &arg);
    JS_FreeValues(jctx, bigint_ctor, arg);
    return jsval_or_pyerr(self, result);
}

static JSValue py_dict_to_js(ContextObject *self, PyObject *item, int depth)
{
    JSContext *jctx = self->context;

    JSValue obj = jsval_or_pyerr(self, JS_NewObject(jctx));
    if (JS_IsException(obj)) {
        return JS_EXCEPTION;
    }

    // A snapshot, so concurrent mutation of the dict cannot upset iteration.
    PyObject *items = PyDict_Items(item);
    if (items == NULL) {
        JS_FreeValue(jctx, obj);
        return JS_EXCEPTION;
    }

    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(items); i++) {
        PyObject *pair = PyList_GET_ITEM(items, i);
        PyObject *key = PyTuple_GET_ITEM(pair, 0);
        PyObject *value = PyTuple_GET_ITEM(pair, 1);

        if (!PyUnicode_Check(key)) {
            PyErr_Format(PyExc_TypeError, "JS object keys must be str, not %.200s", Py_TYPE(key)->tp_name);
            goto fail;
        }
        const char *key_utf8 = PyUnicode_AsUTF8(key);
        if (key_utf8 == NULL) {
            goto fail;
        }

        JSValue jvalue = py_to_js(self, value, depth + 1);
        if (JS_IsException(jvalue)) {
            goto fail;
        }
        if (JS_SetPropertyStr(jctx, obj, key_utf8, jvalue) < 0) {
            raise_js_error(self);
            goto fail;
        }
    }

    Py_DECREF(items);
    return obj;

fail:
    Py_DECREF(items);
    JS_FreeValue(jctx, obj);
    return JS_EXCEPTION;
}

static JSValue py_sequence_to_js(ContextObject *self, PyObject *item, int depth)
{
    JSContext *jctx = self->context;

    JSValue arr = jsval_or_pyerr(self, JS_NewArray(jctx));
    if (JS_IsException(arr)) {
        return JS_EXCEPTION;
    }

    Py_ssize_t size = PySequence_Size(item);
    if (size < 0) {
        goto fail;
    }
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *element = PySequence_GetItem(item, i);
        if (element == NULL) {
            goto fail;
        }
        JSValue jvalue = py_to_js(self, element, depth + 1);
        Py_DECREF(element);
        if (JS_IsException(jvalue)) {
            goto fail;
        }
        if (JS_SetPropertyInt64(jctx, arr, i, jvalue) < 0) {
            raise_js_error(self);
            goto fail;
        }
    }
    return arr;

fail:
    JS_FreeValue(jctx, arr);
    return JS_EXCEPTION;
}

static JSValue qjs_call_python(
        JSContext *jctx, JSValueConst this_val, int argc, JSValueConst *argv, int magic, void *opaque);

static JSValue py_callable_to_js(ContextObject *self, PyObject *item)
{
    JSContext *jctx = self->context;

    // The list owns the reference; the JS closure keeps only a borrowed pointer so its finalizer never has
    // to touch Python state.
    if (PyList_Append(self->callables, item) < 0) {
        return JS_EXCEPTION;
    }

    PyObject *name_obj = NULL;
    const char *name = NULL;
    if (PyObject_GetOptionalAttrString(item, "__name__", &name_obj) < 0) {
        return JS_EXCEPTION;
    }
    if (name_obj != NULL && PyUnicode_Check(name_obj)) {
        name = PyUnicode_AsUTF8(name_obj);
        if (name == NULL) {
            PyErr_Clear();
        }
    }

    JSValue fn = JS_NewCClosure(jctx, qjs_call_python, name, NULL, 0, 0, item);
    Py_XDECREF(name_obj);
    return jsval_or_pyerr(self, fn);
}

static JSValue py_buffer_to_js(ContextObject *self, PyObject *item)
{
    Py_buffer view;
    if (PyObject_GetBuffer(item, &view, PyBUF_SIMPLE) < 0) {
        return JS_EXCEPTION;
    }
    JSValue result = JS_NewUint8ArrayCopy(self->context, (const uint8_t *)view.buf, (size_t)view.len);
    PyBuffer_Release(&view);
    return jsval_or_pyerr(self, result);
}

#define QJS_MAX_CONVERT_DEPTH 64

static JSValue py_to_js(ContextObject *self, PyObject *item, int depth)
{
    JSContext *jctx = self->context;
    pyqjsng_state *state = ctx_get_state(self);

    if (depth > QJS_MAX_CONVERT_DEPTH) {
        PyErr_SetString(PyExc_ValueError, "object nesting too deep to convert to JS");
        return JS_EXCEPTION;
    }

    if (item == Py_None) {
        return JS_NULL;
    }
    if (PyBool_Check(item)) {
        return JS_NewBool(jctx, item == Py_True);
    }
    if (PyLong_Check(item)) {
        int overflow = 0;
        long long v = PyLong_AsLongLongAndOverflow(item, &overflow);
        if (v == -1 && overflow == 0 && PyErr_Occurred()) {
            return JS_EXCEPTION;
        }
        if (overflow == 0) {
            if (v >= INT32_MIN && v <= INT32_MAX) {
                return JS_NewInt32(jctx, (int32_t)v);
            }
            if (v >= -(1LL << 53) && v <= (1LL << 53)) {
                return JS_NewFloat64(jctx, (double)v);
            }
            return jsval_or_pyerr(self, JS_NewBigInt64(jctx, v));
        }
        return py_long_to_js_bigint(self, item);
    }
    if (PyFloat_Check(item)) {
        return JS_NewFloat64(jctx, PyFloat_AS_DOUBLE(item));
    }
    if (PyUnicode_Check(item)) {
        Py_ssize_t len;
        const char *utf8 = PyUnicode_AsUTF8AndSize(item, &len);
        if (utf8 == NULL) {
            return JS_EXCEPTION;
        }
        return jsval_or_pyerr(self, JS_NewStringLen(jctx, utf8, (size_t)len));
    }
    if (Py_IS_TYPE(item, (PyTypeObject *)state->object_type)) {
        ObjectObject *obj = (ObjectObject *)item;
        if (obj->ctx == NULL) {
            PyErr_SetString(PyExc_RuntimeError, "JS object is detached");
            return JS_EXCEPTION;
        }
        if (obj->ctx != self) {
            PyErr_SetString(PyExc_ValueError, "JS object belongs to a different Context");
            return JS_EXCEPTION;
        }
        return JS_DupValue(jctx, obj->value);
    }
    if (PyDict_Check(item)) {
        return py_dict_to_js(self, item, depth);
    }
    if (PyList_Check(item) || PyTuple_Check(item)) {
        return py_sequence_to_js(self, item, depth);
    }
    if (PyCallable_Check(item)) {
        return py_callable_to_js(self, item);
    }
    if (PyObject_CheckBuffer(item)) {
        return py_buffer_to_js(self, item);
    }

    PyErr_Format(PyExc_TypeError, "cannot convert %.200s to a JS value", Py_TYPE(item)->tp_name);
    return JS_EXCEPTION;
}

//

// Stashes the current Python exception on the context and throws a marked JS error carrying its text. The
// marker lets raise_js_error re-raise the original Python exception if the error propagates all the way out.
static JSValue throw_pending_pyexc(ContextObject *self)
{
    JSContext *jctx = self->context;

    PyObject *exc = PyErr_GetRaisedException();
    if (exc == NULL) {
        return JS_ThrowPlainError(jctx, "python error");
    }

    const char *tp_name = Py_TYPE(exc)->tp_name;
    JSValue error;
    PyObject *text = PyObject_Str(exc);
    if (text != NULL) {
        const char *utf8 = PyUnicode_AsUTF8(text);
        if (utf8 == NULL) {
            PyErr_Clear();
            utf8 = "";
        }
        error = JS_NewPlainError(jctx, "%s: %s", tp_name, utf8);
        Py_DECREF(text);
    } else {
        PyErr_Clear();
        error = JS_NewPlainError(jctx, "%s", tp_name);
    }

    if (!JS_IsException(error)) {
        JS_DefinePropertyValueStr(jctx, error, "pythonError", JS_TRUE, 0);
    }
    Py_XSETREF(self->pending_pyexc, exc);
    return JS_Throw(jctx, error);
}

// The JSCClosure trampoline invoking a Python callable from JS.
static JSValue qjs_call_python(
        JSContext *jctx, JSValueConst this_val, int argc, JSValueConst *argv, int magic, void *opaque)
{
    (void)this_val;
    (void)magic;
    ContextObject *self = (ContextObject *)JS_GetContextOpaque(jctx);
    PyObject *callable = (PyObject *)opaque;

    // Reattach if (and only if) the JS entry point that led here detached.
    PyThreadState *ts = self->thread_state;
    if (ts != NULL) {
        PyEval_RestoreThread(ts);
        self->thread_state = NULL;
    }

    JSValue result;
    PyObject *args = PyTuple_New(argc);
    if (args == NULL) {
        result = throw_pending_pyexc(self);
        goto done;
    }
    for (int i = 0; i < argc; i++) {
        PyObject *arg = js_to_py(self, argv[i]);
        if (arg == NULL) {
            Py_DECREF(args);
            result = throw_pending_pyexc(self);
            goto done;
        }
        PyTuple_SET_ITEM(args, i, arg);
    }

    PyObject *py_result = PyObject_CallObject(callable, args);
    Py_DECREF(args);
    if (py_result == NULL) {
        result = throw_pending_pyexc(self);
        goto done;
    }

    result = py_to_js(self, py_result, 0);
    Py_DECREF(py_result);
    if (JS_IsException(result)) {
        result = throw_pending_pyexc(self);
    }

done:
    if (ts != NULL) {
        self->thread_state = PyEval_SaveThread();
    }
    return result;
}

//

PyDoc_STRVAR(
    object_doc,
    "A handle to a JS object (or function, symbol, or module) owned by a Context.\n"
    "\n"
    "Supports calling, item access by str or int key, and JSON extraction. Instances are only ever created\n"
    "by the owning Context.");

static int object_traverse(PyObject *op, visitproc visit, void *arg)
{
    ObjectObject *self = (ObjectObject *)op;
    Py_VISIT(Py_TYPE(op));
    Py_VISIT(self->ctx);
    return 0;
}

static void object_release_value(ObjectObject *self)
{
    if (self->ctx != NULL) {
        ctx_lock(self->ctx);
        JS_FreeValue(self->ctx->context, self->value);
        ctx_unlock(self->ctx);
        self->value = JS_UNDEFINED;
    }
}

static int object_clear(PyObject *op)
{
    ObjectObject *self = (ObjectObject *)op;
    object_release_value(self);
    Py_CLEAR(self->ctx);
    return 0;
}

static void object_dealloc(PyObject *op)
{
    PyTypeObject *tp = Py_TYPE(op);
    PyObject_GC_UnTrack(op);
    object_clear(op);
    tp->tp_free(op);
    Py_DECREF(tp);
}

// Returns the owning context or raises. Every Object entry point goes through this.
static ContextObject * object_ctx(ObjectObject *self)
{
    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "JS object is detached");
        return NULL;
    }
    return self->ctx;
}

static int build_js_args(ContextObject *ctx, PyObject *args, Py_ssize_t start, JSValue **out_args, int *out_n)
{
    Py_ssize_t n = PyTuple_GET_SIZE(args) - start;
    JSValue *jsargs = NULL;
    if (n > 0) {
        jsargs = PyMem_Malloc((size_t)n * sizeof(JSValue));
        if (jsargs == NULL) {
            PyErr_NoMemory();
            return -1;
        }
    }
    for (Py_ssize_t i = 0; i < n; i++) {
        JSValue value = py_to_js(ctx, PyTuple_GET_ITEM(args, start + i), 0);
        if (JS_IsException(value)) {
            for (Py_ssize_t j = 0; j < i; j++) {
                JS_FreeValue(ctx->context, jsargs[j]);
            }
            PyMem_Free(jsargs);
            return -1;
        }
        jsargs[i] = value;
    }
    *out_args = jsargs;
    *out_n = (int)n;
    return 0;
}

static void free_js_args(ContextObject *ctx, JSValue *jsargs, int n)
{
    for (int i = 0; i < n; i++) {
        JS_FreeValue(ctx->context, jsargs[i]);
    }
    PyMem_Free(jsargs);
}

static PyObject * object_call(PyObject *op, PyObject *args, PyObject *kwargs)
{
    ObjectObject *self = (ObjectObject *)op;
    if (kwargs != NULL && PyDict_GET_SIZE(kwargs) != 0) {
        PyErr_SetString(PyExc_TypeError, "JS calls take no keyword arguments");
        return NULL;
    }
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSValue *jsargs;
    int n;
    if (build_js_args(ctx, args, 0, &jsargs, &n) < 0) {
        ctx_unlock(ctx);
        return NULL;
    }

    ctx_begin_run(ctx);
    ctx_detach(ctx);
    JSValue value = JS_Call(ctx->context, self->value, JS_UNDEFINED, n, jsargs);
    ctx_attach(ctx);

    free_js_args(ctx, jsargs, n);
    PyObject *result = return_js_value(ctx, value);
    ctx_unlock(ctx);
    return result;
}

PyDoc_STRVAR(
    object_invoke_doc,
    "invoke(name, *args)\n"
    "\n"
    "Calls the named method of this object, with this object as `this`.");

static PyObject * object_invoke(PyObject *op, PyObject *args)
{
    ObjectObject *self = (ObjectObject *)op;
    if (PyTuple_GET_SIZE(args) < 1 || !PyUnicode_Check(PyTuple_GET_ITEM(args, 0))) {
        PyErr_SetString(PyExc_TypeError, "invoke() requires a method name as its first argument");
        return NULL;
    }
    const char *name = PyUnicode_AsUTF8(PyTuple_GET_ITEM(args, 0));
    if (name == NULL) {
        return NULL;
    }
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSAtom atom = JS_NewAtom(ctx->context, name);
    if (atom == JS_ATOM_NULL) {
        raise_js_error(ctx);
        ctx_unlock(ctx);
        return NULL;
    }
    JSValue *jsargs;
    int n;
    if (build_js_args(ctx, args, 1, &jsargs, &n) < 0) {
        JS_FreeAtom(ctx->context, atom);
        ctx_unlock(ctx);
        return NULL;
    }

    ctx_begin_run(ctx);
    ctx_detach(ctx);
    JSValue value = JS_Invoke(ctx->context, self->value, atom, n, jsargs);
    ctx_attach(ctx);

    free_js_args(ctx, jsargs, n);
    JS_FreeAtom(ctx->context, atom);
    PyObject *result = return_js_value(ctx, value);
    ctx_unlock(ctx);
    return result;
}

PyDoc_STRVAR(
    object_json_doc,
    "json()\n"
    "\n"
    "Returns the JSON.stringify() representation of this object as a str, or None if it is not\n"
    "serializable (e.g. a function).");

static PyObject * object_json(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSValue value = JS_JSONStringify(ctx->context, self->value, JS_UNDEFINED, JS_UNDEFINED);
    PyObject *result = return_js_value(ctx, value);
    ctx_unlock(ctx);
    return result;
}

PyDoc_STRVAR(
    object_keys_doc,
    "keys()\n"
    "\n"
    "Returns the object's own enumerable string-keyed property names as a list of str.");

static PyObject * object_keys(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSContext *jctx = ctx->context;
    JSPropertyEnum *tab;
    uint32_t len;
    if (JS_GetOwnPropertyNames(jctx, &tab, &len, self->value, JS_GPN_STRING_MASK | JS_GPN_ENUM_ONLY) < 0) {
        raise_js_error(ctx);
        ctx_unlock(ctx);
        return NULL;
    }

    PyObject *result = PyList_New((Py_ssize_t)len);
    if (result != NULL) {
        for (uint32_t i = 0; i < len; i++) {
            size_t name_len;
            const char *name = JS_AtomToCStringLen(jctx, &name_len, tab[i].atom);
            if (name == NULL) {
                raise_js_error(ctx);
                Py_CLEAR(result);
                break;
            }
            PyObject *name_obj = PyUnicode_FromStringAndSize(name, (Py_ssize_t)name_len);
            JS_FreeCString(jctx, name);
            if (name_obj == NULL) {
                Py_CLEAR(result);
                break;
            }
            PyList_SET_ITEM(result, (Py_ssize_t)i, name_obj);
        }
    }

    JS_FreePropertyEnum(jctx, tab, len);
    ctx_unlock(ctx);
    return result;
}

PyDoc_STRVAR(
    object_to_bytes_doc,
    "to_bytes()\n"
    "\n"
    "Copies the contents of an ArrayBuffer or Uint8Array into a bytes object.");

static PyObject * object_to_bytes(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    size_t size;
    uint8_t *buf;
    if (JS_IsArrayBuffer(self->value)) {
        buf = JS_GetArrayBuffer(ctx->context, &size, self->value);
    } else {
        buf = JS_GetUint8Array(ctx->context, &size, self->value);
    }
    PyObject *result;
    if (buf == NULL) {
        result = raise_js_error(ctx);
    } else {
        result = PyBytes_FromStringAndSize((const char *)buf, (Py_ssize_t)size);
    }
    ctx_unlock(ctx);
    return result;
}

PyDoc_STRVAR(
    object_promise_state_doc,
    "promise_state()\n"
    "\n"
    "Returns 'pending', 'fulfilled', or 'rejected' if this object is a promise, else None.");

static PyObject * object_promise_state(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSPromiseStateEnum state = JS_PromiseState(ctx->context, self->value);
    ctx_unlock(ctx);

    switch (state) {
        case JS_PROMISE_PENDING:
            return PyUnicode_FromString("pending");
        case JS_PROMISE_FULFILLED:
            return PyUnicode_FromString("fulfilled");
        case JS_PROMISE_REJECTED:
            return PyUnicode_FromString("rejected");
        default:
            Py_RETURN_NONE;
    }
}

PyDoc_STRVAR(
    object_promise_result_doc,
    "promise_result()\n"
    "\n"
    "Returns the result of a fulfilled promise, or raises the rejection reason of a rejected one.");

static PyObject * object_promise_result(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    PyObject *result = NULL;
    switch (JS_PromiseState(ctx->context, self->value)) {
        case JS_PROMISE_FULFILLED:
            result = return_js_value(ctx, JS_PromiseResult(ctx->context, self->value));
            break;
        case JS_PROMISE_REJECTED:
            JS_Throw(ctx->context, JS_PromiseResult(ctx->context, self->value));
            result = raise_js_error(ctx);
            break;
        case JS_PROMISE_PENDING:
            PyErr_SetString(PyExc_RuntimeError, "promise is still pending");
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "not a promise");
            break;
    }
    ctx_unlock(ctx);
    return result;
}

static JSAtom atom_from_py_key(ContextObject *ctx, PyObject *key)
{
    JSContext *jctx = ctx->context;
    JSAtom atom = JS_ATOM_NULL;

    if (PyUnicode_Check(key)) {
        Py_ssize_t len;
        const char *utf8 = PyUnicode_AsUTF8AndSize(key, &len);
        if (utf8 == NULL) {
            return JS_ATOM_NULL;
        }
        atom = JS_NewAtomLen(jctx, utf8, (size_t)len);
    } else if (PyLong_Check(key)) {
        long long v = PyLong_AsLongLong(key);
        if (v == -1 && PyErr_Occurred()) {
            return JS_ATOM_NULL;
        }
        atom = JS_ValueToAtom(jctx, JS_NewInt64(jctx, v));
    } else {
        PyErr_Format(PyExc_TypeError, "JS property keys must be str or int, not %.200s", Py_TYPE(key)->tp_name);
        return JS_ATOM_NULL;
    }

    if (atom == JS_ATOM_NULL) {
        raise_js_error(ctx);
    }
    return atom;
}

static PyObject * object_subscript(PyObject *op, PyObject *key)
{
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    JSAtom atom = atom_from_py_key(ctx, key);
    if (atom == JS_ATOM_NULL) {
        ctx_unlock(ctx);
        return NULL;
    }
    JSValue value = JS_GetProperty(ctx->context, self->value, atom);
    JS_FreeAtom(ctx->context, atom);
    PyObject *result = return_js_value(ctx, value);
    ctx_unlock(ctx);
    return result;
}

static int object_ass_subscript(PyObject *op, PyObject *key, PyObject *value)
{
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return -1;
    }

    ctx_lock(ctx);
    int result = -1;
    JSAtom atom = atom_from_py_key(ctx, key);
    if (atom == JS_ATOM_NULL) {
        goto done;
    }

    if (value == NULL) {
        if (JS_DeleteProperty(ctx->context, self->value, atom, JS_PROP_THROW) < 0) {
            raise_js_error(ctx);
        } else {
            result = 0;
        }
    } else {
        JSValue jvalue = py_to_js(ctx, value, 0);
        if (!JS_IsException(jvalue)) {
            if (JS_SetProperty(ctx->context, self->value, atom, jvalue) < 0) {
                raise_js_error(ctx);
            } else {
                result = 0;
            }
        }
    }
    JS_FreeAtom(ctx->context, atom);

done:
    ctx_unlock(ctx);
    return result;
}

static PyObject * object_str(PyObject *op)
{
    ObjectObject *self = (ObjectObject *)op;
    ContextObject *ctx = object_ctx(self);
    if (ctx == NULL) {
        return NULL;
    }

    ctx_lock(ctx);
    PyObject *result;
    size_t len;
    const char *cstr = JS_ToCStringLen(ctx->context, &len, self->value);
    if (cstr == NULL) {
        result = raise_js_error(ctx);
    } else {
        result = PyUnicode_FromStringAndSize(cstr, (Py_ssize_t)len);
        JS_FreeCString(ctx->context, cstr);
    }
    ctx_unlock(ctx);
    return result;
}

static PyMethodDef object_methods[] = {
    {"invoke", (PyCFunction)object_invoke, METH_VARARGS, object_invoke_doc},
    {"json", (PyCFunction)object_json, METH_NOARGS, object_json_doc},
    {"keys", (PyCFunction)object_keys, METH_NOARGS, object_keys_doc},
    {"to_bytes", (PyCFunction)object_to_bytes, METH_NOARGS, object_to_bytes_doc},
    {"promise_state", (PyCFunction)object_promise_state, METH_NOARGS, object_promise_state_doc},
    {"promise_result", (PyCFunction)object_promise_result, METH_NOARGS, object_promise_result_doc},
    {NULL, NULL, 0, NULL}
};

static PyType_Slot object_type_slots[] = {
    {Py_tp_doc, (void *)object_doc},
    {Py_tp_traverse, (void *)object_traverse},
    {Py_tp_clear, (void *)object_clear},
    {Py_tp_dealloc, (void *)object_dealloc},
    {Py_tp_call, (void *)object_call},
    {Py_tp_str, (void *)object_str},
    {Py_tp_methods, (void *)object_methods},
    {Py_mp_subscript, (void *)object_subscript},
    {Py_mp_ass_subscript, (void *)object_ass_subscript},
    {0, NULL}
};

static PyType_Spec object_type_spec = {
    .name = _PACKAGE_NAME ".Object",
    .basicsize = sizeof(ObjectObject),
    .flags = (
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION),
    .slots = object_type_slots,
};

// Takes ownership of 'value'.
static PyObject * wrap_js_value(ContextObject *self, JSValue value)
{
    PyTypeObject *tp = (PyTypeObject *)ctx_get_state(self)->object_type;
    ObjectObject *obj = (ObjectObject *)tp->tp_alloc(tp, 0);
    if (obj == NULL) {
        JS_FreeValue(self->context, value);
        return NULL;
    }
    obj->ctx = (ContextObject *)Py_NewRef((PyObject *)self);
    obj->value = value;
    return (PyObject *)obj;
}

//

PyDoc_STRVAR(
    context_doc,
    "Context()\n"
    "\n"
    "A self-contained JS runtime plus context (realm).\n"
    "\n"
    "Contexts are safe to share between threads: all use of the underlying runtime is serialized on an\n"
    "internal per-context lock. Distinct Contexts are fully independent and can run in parallel.");

static PyObject * context_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    if ((args != NULL && PyTuple_GET_SIZE(args) != 0) || (kwargs != NULL && PyDict_GET_SIZE(kwargs) != 0)) {
        PyErr_SetString(PyExc_TypeError, "Context() takes no arguments");
        return NULL;
    }

    PyObject *module = PyType_GetModule(type);
    if (module == NULL) {
        return NULL;
    }

    ContextObject *self = (ContextObject *)type->tp_alloc(type, 0);
    if (self == NULL) {
        return NULL;
    }
    self->module = Py_NewRef(module);

    self->callables = PyList_New(0);
    if (self->callables == NULL) {
        Py_DECREF(self);
        return NULL;
    }

    self->runtime = JS_NewRuntime();
    if (self->runtime == NULL) {
        Py_DECREF(self);
        PyErr_NoMemory();
        return NULL;
    }
    self->context = JS_NewContext(self->runtime);
    if (self->context == NULL) {
        Py_DECREF(self);
        PyErr_NoMemory();
        return NULL;
    }

    JS_SetRuntimeOpaque(self->runtime, self);
    JS_SetContextOpaque(self->context, self);
    JS_SetInterruptHandler(self->runtime, qjs_interrupt_handler, self);

    return (PyObject *)self;
}

static int context_traverse(PyObject *op, visitproc visit, void *arg)
{
    ContextObject *self = (ContextObject *)op;
    Py_VISIT(Py_TYPE(op));
    Py_VISIT(self->callables);
    Py_VISIT(self->pending_pyexc);
    Py_VISIT(self->module);
    return 0;
}

static int context_clear(PyObject *op)
{
    ContextObject *self = (ContextObject *)op;
    Py_CLEAR(self->callables);
    Py_CLEAR(self->pending_pyexc);
    Py_CLEAR(self->module);
    return 0;
}

static void context_dealloc(PyObject *op)
{
    ContextObject *self = (ContextObject *)op;
    PyTypeObject *tp = Py_TYPE(op);
    PyObject_GC_UnTrack(op);
    // Any Object wrapper holds a strong reference to the context, so by now all wrapped values have been
    // freed and the runtime can be torn down. JS-side finalizers never touch Python state.
    if (self->context != NULL) {
        JS_FreeContext(self->context);
    }
    if (self->runtime != NULL) {
        JS_FreeRuntime(self->runtime);
    }
    context_clear(op);
    tp->tp_free(op);
    Py_DECREF(tp);
}

PyDoc_STRVAR(
    context_eval_doc,
    "eval(code, *, filename='<eval>', module=False, strict=False)\n"
    "\n"
    "Evaluates JS source and returns the result converted to Python (objects and functions are returned as\n"
    "Object handles). With module=True the source is evaluated as an ES module and the result is a promise;\n"
    "run execute_pending_jobs() to settle it.");

static PyObject * context_eval(PyObject *op, PyObject *args, PyObject *kwargs)
{
    ContextObject *self = (ContextObject *)op;
    static char *kwlist[] = {"code", "filename", "module", "strict", NULL};
    const char *code;
    Py_ssize_t code_len;
    const char *filename = "<eval>";
    int as_module = 0;
    int strict = 0;
    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "s#|$spp", kwlist, &code, &code_len, &filename, &as_module, &strict)) {
        return NULL;
    }

    int flags = as_module ? JS_EVAL_TYPE_MODULE : JS_EVAL_TYPE_GLOBAL;
    if (strict) {
        flags |= JS_EVAL_FLAG_STRICT;
    }

    ctx_lock(self);
    ctx_begin_run(self);
    ctx_detach(self);
    JSValue value = JS_Eval(self->context, code, (size_t)code_len, filename, flags);
    ctx_attach(self);
    PyObject *result = return_js_value(self, value);
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_get_doc,
    "get(name)\n"
    "\n"
    "Returns the value of a global variable (None if undefined).");

static PyObject * context_get(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    const char *name;
    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }

    ctx_lock(self);
    JSValue global = JS_GetGlobalObject(self->context);
    JSValue value = JS_GetPropertyStr(self->context, global, name);
    JS_FreeValue(self->context, global);
    PyObject *result = return_js_value(self, value);
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_set_doc,
    "set(name, value)\n"
    "\n"
    "Sets a global variable to the given Python value. Supported: None, bool, int, float, str, bytes-like\n"
    "objects (as Uint8Array), dicts with str keys, lists and tuples (recursively), Python callables (as JS\n"
    "functions), and Object handles from this context.");

static PyObject * context_set(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    const char *name;
    PyObject *item;
    if (!PyArg_ParseTuple(args, "sO", &name, &item)) {
        return NULL;
    }

    ctx_lock(self);
    PyObject *result = NULL;
    JSValue value = py_to_js(self, item, 0);
    if (!JS_IsException(value)) {
        JSValue global = JS_GetGlobalObject(self->context);
        if (JS_SetPropertyStr(self->context, global, name, value) < 0) {
            raise_js_error(self);
        } else {
            result = Py_NewRef(Py_None);
        }
        JS_FreeValue(self->context, global);
    }
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_parse_json_doc,
    "parse_json(text)\n"
    "\n"
    "Parses a JSON string into a JS value.");

static PyObject * context_parse_json(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    const char *text;
    Py_ssize_t text_len;
    if (!PyArg_ParseTuple(args, "s#", &text, &text_len)) {
        return NULL;
    }

    ctx_lock(self);
    JSValue value = JS_ParseJSON(self->context, text, (size_t)text_len, "<json>");
    PyObject *result = return_js_value(self, value);
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_execute_pending_job_doc,
    "execute_pending_job()\n"
    "\n"
    "Executes one pending job (e.g. a promise reaction). Returns True if a job ran, False if none were\n"
    "pending.");

static PyObject * context_execute_pending_job(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;

    ctx_lock(self);
    ctx_begin_run(self);
    ctx_detach(self);
    JSContext *job_ctx;
    int ret = JS_ExecutePendingJob(self->runtime, &job_ctx);
    ctx_attach(self);
    PyObject *result;
    if (ret < 0) {
        result = raise_js_error(self);
    } else {
        result = PyBool_FromLong(ret > 0);
    }
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_execute_pending_jobs_doc,
    "execute_pending_jobs()\n"
    "\n"
    "Executes pending jobs until none remain. Returns the number of jobs executed.");

static PyObject * context_execute_pending_jobs(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;

    ctx_lock(self);
    ctx_begin_run(self);
    long count = 0;
    PyObject *result = NULL;
    for (;;) {
        ctx_detach(self);
        JSContext *job_ctx;
        int ret = JS_ExecutePendingJob(self->runtime, &job_ctx);
        ctx_attach(self);
        if (ret < 0) {
            raise_js_error(self);
            break;
        }
        if (ret == 0) {
            result = PyLong_FromLong(count);
            break;
        }
        count++;
    }
    ctx_unlock(self);
    return result;
}

PyDoc_STRVAR(
    context_has_pending_jobs_doc,
    "has_pending_jobs()\n"
    "\n"
    "Returns True if any jobs are pending.");

static PyObject * context_has_pending_jobs(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;

    ctx_lock(self);
    bool pending = JS_IsJobPending(self->runtime);
    ctx_unlock(self);
    return PyBool_FromLong(pending);
}

PyDoc_STRVAR(
    context_interrupt_doc,
    "interrupt()\n"
    "\n"
    "Requests that the currently running evaluation (if any) abort with JsInterruptError. Safe to call from\n"
    "any thread; never blocks.");

static PyObject * context_interrupt(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;
    // Deliberately lock-free: this must be callable while another thread is stuck inside JS.
    atomic_store_explicit(&self->interrupt_flag, 1, memory_order_release);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_set_time_limit_doc,
    "set_time_limit(seconds)\n"
    "\n"
    "Limits the wall-clock duration of each subsequent evaluation, aborting it with JsInterruptError. Zero\n"
    "or negative disables the limit.");

static PyObject * context_set_time_limit(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    double seconds;
    if (!PyArg_ParseTuple(args, "d", &seconds)) {
        return NULL;
    }

    ctx_lock(self);
    self->time_limit_ns = seconds > 0.0 ? (int64_t)(seconds * 1e9) : 0;
    ctx_unlock(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_set_memory_limit_doc,
    "set_memory_limit(limit)\n"
    "\n"
    "Sets the runtime memory limit in bytes. Zero disables the limit.");

static PyObject * context_set_memory_limit(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    Py_ssize_t limit;
    if (!PyArg_ParseTuple(args, "n", &limit)) {
        return NULL;
    }
    if (limit < 0) {
        PyErr_SetString(PyExc_ValueError, "memory limit must be >= 0");
        return NULL;
    }

    ctx_lock(self);
    JS_SetMemoryLimit(self->runtime, (size_t)limit);
    ctx_unlock(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_set_max_stack_size_doc,
    "set_max_stack_size(limit)\n"
    "\n"
    "Sets the maximum JS stack size in bytes. Zero disables the check.");

static PyObject * context_set_max_stack_size(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    Py_ssize_t limit;
    if (!PyArg_ParseTuple(args, "n", &limit)) {
        return NULL;
    }
    if (limit < 0) {
        PyErr_SetString(PyExc_ValueError, "stack size must be >= 0");
        return NULL;
    }

    ctx_lock(self);
    JS_SetMaxStackSize(self->runtime, (size_t)limit);
    ctx_unlock(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_set_gc_threshold_doc,
    "set_gc_threshold(threshold)\n"
    "\n"
    "Sets the allocation threshold (in bytes) that triggers the automatic JS GC.");

static PyObject * context_set_gc_threshold(PyObject *op, PyObject *args)
{
    ContextObject *self = (ContextObject *)op;
    Py_ssize_t threshold;
    if (!PyArg_ParseTuple(args, "n", &threshold)) {
        return NULL;
    }
    if (threshold < 0) {
        PyErr_SetString(PyExc_ValueError, "threshold must be >= 0");
        return NULL;
    }

    ctx_lock(self);
    JS_SetGCThreshold(self->runtime, (size_t)threshold);
    ctx_unlock(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_gc_doc,
    "gc()\n"
    "\n"
    "Runs the JS garbage collector.");

static PyObject * context_gc(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;

    ctx_lock(self);
    JS_RunGC(self->runtime);
    ctx_unlock(self);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    context_memory_doc,
    "memory()\n"
    "\n"
    "Returns runtime memory usage statistics as a dict.");

static PyObject * context_memory(PyObject *op, PyObject *ignored)
{
    (void)ignored;
    ContextObject *self = (ContextObject *)op;

    JSMemoryUsage usage;
    ctx_lock(self);
    JS_ComputeMemoryUsage(self->runtime, &usage);
    ctx_unlock(self);

    PyObject *dict = PyDict_New();
    if (dict == NULL) {
        return NULL;
    }

#define QJS_MEM_ENTRY(key) \
    do { \
        PyObject *value = PyLong_FromLongLong(usage.key); \
        if (value == NULL || PyDict_SetItemString(dict, #key, value) < 0) { \
            Py_XDECREF(value); \
            Py_DECREF(dict); \
            return NULL; \
        } \
        Py_DECREF(value); \
    } while (0)

    QJS_MEM_ENTRY(malloc_size);
    QJS_MEM_ENTRY(malloc_limit);
    QJS_MEM_ENTRY(memory_used_size);
    QJS_MEM_ENTRY(malloc_count);
    QJS_MEM_ENTRY(memory_used_count);
    QJS_MEM_ENTRY(atom_count);
    QJS_MEM_ENTRY(atom_size);
    QJS_MEM_ENTRY(str_count);
    QJS_MEM_ENTRY(str_size);
    QJS_MEM_ENTRY(obj_count);
    QJS_MEM_ENTRY(obj_size);
    QJS_MEM_ENTRY(prop_count);
    QJS_MEM_ENTRY(prop_size);
    QJS_MEM_ENTRY(shape_count);
    QJS_MEM_ENTRY(shape_size);
    QJS_MEM_ENTRY(js_func_count);
    QJS_MEM_ENTRY(js_func_size);
    QJS_MEM_ENTRY(js_func_code_size);
    QJS_MEM_ENTRY(js_func_pc2line_count);
    QJS_MEM_ENTRY(js_func_pc2line_size);
    QJS_MEM_ENTRY(c_func_count);
    QJS_MEM_ENTRY(array_count);
    QJS_MEM_ENTRY(fast_array_count);
    QJS_MEM_ENTRY(fast_array_elements);
    QJS_MEM_ENTRY(binary_object_count);
    QJS_MEM_ENTRY(binary_object_size);

#undef QJS_MEM_ENTRY

    return dict;
}

static PyObject * context_global_this(PyObject *op, void *closure)
{
    (void)closure;
    ContextObject *self = (ContextObject *)op;

    ctx_lock(self);
    PyObject *result = wrap_js_value(self, JS_GetGlobalObject(self->context));
    ctx_unlock(self);
    return result;
}

static PyMethodDef context_methods[] = {
    {"eval", (PyCFunction)(void (*)(void))context_eval, METH_VARARGS | METH_KEYWORDS, context_eval_doc},
    {"get", (PyCFunction)context_get, METH_VARARGS, context_get_doc},
    {"set", (PyCFunction)context_set, METH_VARARGS, context_set_doc},
    {"parse_json", (PyCFunction)context_parse_json, METH_VARARGS, context_parse_json_doc},
    {"execute_pending_job", (PyCFunction)context_execute_pending_job, METH_NOARGS, context_execute_pending_job_doc},
    {"execute_pending_jobs", (PyCFunction)context_execute_pending_jobs, METH_NOARGS, context_execute_pending_jobs_doc},
    {"has_pending_jobs", (PyCFunction)context_has_pending_jobs, METH_NOARGS, context_has_pending_jobs_doc},
    {"interrupt", (PyCFunction)context_interrupt, METH_NOARGS, context_interrupt_doc},
    {"set_time_limit", (PyCFunction)context_set_time_limit, METH_VARARGS, context_set_time_limit_doc},
    {"set_memory_limit", (PyCFunction)context_set_memory_limit, METH_VARARGS, context_set_memory_limit_doc},
    {"set_max_stack_size", (PyCFunction)context_set_max_stack_size, METH_VARARGS, context_set_max_stack_size_doc},
    {"set_gc_threshold", (PyCFunction)context_set_gc_threshold, METH_VARARGS, context_set_gc_threshold_doc},
    {"gc", (PyCFunction)context_gc, METH_NOARGS, context_gc_doc},
    {"memory", (PyCFunction)context_memory, METH_NOARGS, context_memory_doc},
    {NULL, NULL, 0, NULL}
};

static PyGetSetDef context_getset[] = {
    {"global_this", context_global_this, NULL, "The context's global object, as an Object handle.", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};

static PyType_Slot context_type_slots[] = {
    {Py_tp_doc, (void *)context_doc},
    {Py_tp_new, (void *)context_new},
    {Py_tp_traverse, (void *)context_traverse},
    {Py_tp_clear, (void *)context_clear},
    {Py_tp_dealloc, (void *)context_dealloc},
    {Py_tp_methods, (void *)context_methods},
    {Py_tp_getset, (void *)context_getset},
    {0, NULL}
};

static PyType_Spec context_type_spec = {
    .name = _PACKAGE_NAME ".Context",
    .basicsize = sizeof(ContextObject),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_IMMUTABLETYPE,
    .slots = context_type_slots,
};

//

PyDoc_STRVAR(pyqjsng_doc, "CPython binding for the quickjs-ng JS engine.");

PyDoc_STRVAR(
    js_error_doc,
    "A JS exception. The formatted JS error is the message; the js_stack attribute holds the JS stack trace\n"
    "as a str (or None).");

PyDoc_STRVAR(js_stack_overflow_error_doc, "A JS stack overflow.");

PyDoc_STRVAR(js_interrupt_error_doc, "A JS evaluation aborted by interrupt() or a time limit.");

static int pyqjsng_exec(PyObject *module)
{
    pyqjsng_state *state = get_pyqjsng_state(module);

    state->context_type = PyType_FromModuleAndSpec(module, &context_type_spec, NULL);
    if (state->context_type == NULL) {
        return -1;
    }
    state->object_type = PyType_FromModuleAndSpec(module, &object_type_spec, NULL);
    if (state->object_type == NULL) {
        return -1;
    }

    state->js_error = PyErr_NewExceptionWithDoc(_PACKAGE_NAME ".JsError", js_error_doc, NULL, NULL);
    if (state->js_error == NULL) {
        return -1;
    }
    state->js_stack_overflow_error = PyErr_NewExceptionWithDoc(
        _PACKAGE_NAME ".JsStackOverflowError", js_stack_overflow_error_doc, state->js_error, NULL);
    if (state->js_stack_overflow_error == NULL) {
        return -1;
    }
    state->js_interrupt_error = PyErr_NewExceptionWithDoc(
        _PACKAGE_NAME ".JsInterruptError", js_interrupt_error_doc, state->js_error, NULL);
    if (state->js_interrupt_error == NULL) {
        return -1;
    }

    if (PyModule_AddObjectRef(module, "Context", state->context_type) < 0 ||
        PyModule_AddObjectRef(module, "Object", state->object_type) < 0 ||
        PyModule_AddObjectRef(module, "JsError", state->js_error) < 0 ||
        PyModule_AddObjectRef(module, "JsStackOverflowError", state->js_stack_overflow_error) < 0 ||
        PyModule_AddObjectRef(module, "JsInterruptError", state->js_interrupt_error) < 0 ||
        PyModule_AddStringConstant(module, "QJS_VERSION", JS_GetVersion()) < 0) {
        return -1;
    }

    return 0;
}

static int pyqjsng_traverse(PyObject *module, visitproc visit, void *arg)
{
    pyqjsng_state *state = get_pyqjsng_state(module);
    Py_VISIT(state->context_type);
    Py_VISIT(state->object_type);
    Py_VISIT(state->js_error);
    Py_VISIT(state->js_stack_overflow_error);
    Py_VISIT(state->js_interrupt_error);
    return 0;
}

static int pyqjsng_clear(PyObject *module)
{
    pyqjsng_state *state = get_pyqjsng_state(module);
    Py_CLEAR(state->context_type);
    Py_CLEAR(state->object_type);
    Py_CLEAR(state->js_error);
    Py_CLEAR(state->js_stack_overflow_error);
    Py_CLEAR(state->js_interrupt_error);
    return 0;
}

static void pyqjsng_free(void *module)
{
    pyqjsng_clear((PyObject *)module);
}

static PyMethodDef pyqjsng_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef_Slot pyqjsng_slots[] = {
    {Py_mod_exec, (void *)pyqjsng_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, NULL}
};

static struct PyModuleDef pyqjsng_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_FULL_NAME,
    .m_doc = pyqjsng_doc,
    .m_size = sizeof(pyqjsng_state),
    .m_methods = pyqjsng_methods,
    .m_slots = pyqjsng_slots,
    .m_traverse = pyqjsng_traverse,
    .m_clear = pyqjsng_clear,
    .m_free = pyqjsng_free,
};

PyMODINIT_FUNC PyInit__pyqjsng(void)
{
    return PyModuleDef_Init(&pyqjsng_module);
}
