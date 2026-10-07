// @om-cext {
//   "extra_sources": [
//     "_pcre2_/src/*.c"
//   ],
//   "extra_headers": [
//     "_pcre2_/src/*.c.dist",
//     "_pcre2_/src/*.h",
//     "_pcre2_/src/*.h.generic"
//   ],
//   "extra_compile_args": [
//     "-fvisibility=hidden",
//     "-g0"
//   ],
//   "define_macros": {
//     "PCRE2_CODE_UNIT_WIDTH": "8",
//     "PCRE2_STATIC": "1",
//     "PCRE2_EXPORT": "",
//     "SUPPORT_UNICODE": "1",
//     "SUPPORT_PCRE2_8": "1",
//     "LINK_SIZE": "2",
//     "HEAP_LIMIT": "20000000",
//     "MATCH_LIMIT": "10000000",
//     "MATCH_LIMIT_DEPTH": "10000000",
//     "MAX_NAME_COUNT": "10000",
//     "MAX_NAME_SIZE": "128",
//     "MAX_VARLOOKBEHIND": "255",
//     "NEWLINE_DEFAULT": "2",
//     "PARENS_NEST_LIMIT": "250"
//   }
// }
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define PCRE2_CODE_UNIT_WIDTH 8
#ifndef PCRE2_STATIC
#define PCRE2_STATIC
#endif
#include "_pcre2_/src/pcre2.h"

// The table of constants below is that of 10.49, and names what older releases do not have.
#if PCRE2_MAJOR != 10 || PCRE2_MINOR < 49
#error "PCRE2 10.49 or newer is required"
#endif

// A direct binding of the 8-bit PCRE2 library. Names, option bits, return codes, and offsets are PCRE2's own: patterns
// and subjects are bytes-like, offsets count code units (bytes), `Code.match` returns what `pcre2_match` returns, and
// PCRE2_UNSET surfaces as -1 (its value read as a signed size). Anything `re`-shaped - str subjects, match objects,
// iteration, `re`'s replacement templates - belongs in Python on top of this, not in here.
//
// Not bound: the JIT, DFA matching, serialization, pattern conversion, custom character tables, callouts of every
// kind, and the general context.
//
// A Code, a CompileContext, and a MatchContext are immutable, and may be used from any number of threads at once -
// which is why the contexts take their settings when created, rather than through PCRE2's setters afterwards. A
// MatchData is a mutable result block: using one from two places at once raises RuntimeError rather than corrupting it.
//
// PCRE2 validates a UTF subject and from then on trusts what it validated, reading whole characters without checking
// their length against the end of the subject. A subject which changes during a match is therefore not just a wrong
// answer but an out of bounds read, and one cannot be ruled out by holding the GIL: a match may run detached, and on a
// free-threaded build nothing is held to begin with. Nor is a read-only buffer enough, as it may be a read-only view
// of memory something else still writes to. So a UTF pattern is only matched against a subject which cannot change -
// bytes, or a memoryview of bytes - unless the caller vouches for the subject with NO_UTF_CHECK, exactly as in C.
//
// Other extensions reach the same library through the `capi` capsule at the bottom of this file, rather than linking a
// second copy of PCRE2 into the process.

//

#define _MODULE_NAME "_pcre2"
#define _PACKAGE_NAME "omxtra.text.pcre2"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

// The `pcre2_` prefix belongs to the library (every public name in pcre2.h is a macro), so module boilerplate that
// would otherwise be named `pcre2_*` is named `pcre2mod_*`.

typedef struct pcre2mod_state {
    PyTypeObject *CodeType;
    PyTypeObject *CompileContextType;
    PyTypeObject *MatchContextType;
    PyTypeObject *MatchDataType;
    PyObject *Error;
    PyObject *CompileError;
    PyObject *MatchError;
    PyObject *SubstituteError;
    // The probe (see PROBE_MATCH_LIMIT) for matches given no MatchContext, or NULL if PCRE2's default match limit
    // is already no greater than a probe's. Not Python state, and never written to after the module is executed.
    pcre2_match_context *probe_context;
} pcre2mod_state;

static inline pcre2mod_state * get_pcre2mod_state(PyObject *module)
{
    void *state = PyModule_GetState(module);
    assert(state != NULL);
    return (pcre2mod_state *)state;
}

static inline pcre2mod_state * get_pcre2mod_type_state(PyTypeObject *tp)
{
    void *state = PyType_GetModuleState(tp);
    assert(state != NULL);
    return (pcre2mod_state *)state;
}

//

static int convert_uint32(PyObject *obj, void *out)
{
    unsigned long v = PyLong_AsUnsignedLong(obj);
    if (v == (unsigned long)-1 && PyErr_Occurred()) {
        return 0;
    }
    if (v > UINT32_MAX) {
        PyErr_SetString(PyExc_OverflowError, "value does not fit in 32 unsigned bits");
        return 0;
    }
    *(uint32_t *)out = (uint32_t)v;
    return 1;
}

// Raises exc_type with PCRE2's own message for the code. The exception carries the code, and the offset PCRE2 reported
// alongside it where there is one (pass -1 where there is not).
static void set_error(PyObject *exc_type, int code, Py_ssize_t offset)
{
    PCRE2_UCHAR buf[256];
    PyObject *msg;
    // A message too long for the buffer is truncated, still zero-terminated, and reported as PCRE2_ERROR_NOMEMORY.
    if (pcre2_get_error_message(code, buf, sizeof(buf)) == PCRE2_ERROR_BADDATA) {
        msg = PyUnicode_FromFormat("unknown error %d", code);
    } else if (offset >= 0) {
        msg = PyUnicode_FromFormat("%s at offset %zd", (const char *)buf, offset);
    } else {
        msg = PyUnicode_FromString((const char *)buf);
    }
    if (msg == NULL) {
        return;
    }

    PyObject *exc = PyObject_CallOneArg(exc_type, msg);
    Py_DECREF(msg);
    if (exc == NULL) {
        return;
    }

    PyObject *code_obj = PyLong_FromLong(code);
    PyObject *offset_obj = (offset >= 0) ? PyLong_FromSsize_t(offset) : Py_NewRef(Py_None);
    if (
        code_obj != NULL &&
        offset_obj != NULL &&
        PyObject_SetAttrString(exc, "code", code_obj) == 0 &&
        PyObject_SetAttrString(exc, "offset", offset_obj) == 0
    ) {
        PyErr_SetObject(exc_type, exc);
    }

    Py_XDECREF(code_obj);
    Py_XDECREF(offset_obj);
    Py_DECREF(exc);
}

//

typedef struct {
    PyObject_HEAD
    pcre2_code *code;
    // Whether the pattern is UTF at all, and whether PCRE2 validates its subjects up front - which it does not for one
    // compiled to match invalid UTF, where it instead finds its own way around what is invalid on every call.
    bool utf;
    bool validates_utf;
} Code;

typedef struct {
    PyObject_HEAD
    pcre2_compile_context *context;
} CompileContext;

typedef struct {
    PyObject_HEAD
    pcre2_match_context *context;
    // A copy of the context with its match limit lowered to a probe's, or NULL if its own is already no greater.
    pcre2_match_context *probe;
} MatchContext;

typedef struct {
    PyObject_HEAD
    pcre2_match_data *match_data;
    // The Code of the last match attempt, if PCRE2 saw that attempt through: to a match, to no match, or to a partial
    // one. Only then is what the block holds besides its ovector - a mark above all, which points into the compiled
    // pattern - PCRE2's to have set, rather than left over or never initialized. NULL otherwise.
    PyObject *code;
    // The subject of the last match attempt, held only if it matched. pcre2_next_match reads through the subject of
    // the match it advances from, so it stays pinned until the block is next matched into.
    Py_buffer subject;
    // Whether the pinned subject is bytes proper, whose contents cannot have changed for as long as they are pinned,
    // and if so the least offset the pinned Code has validated it from - everything from there to its end is known to
    // be valid UTF. PY_SSIZE_T_MAX until it has validated any of it.
    bool subject_immutable;
    Py_ssize_t validated_start;
    atomic_flag busy;
} MatchData;

// The most backtracking a match may do from any one starting position while attached to the interpreter, in PCRE2's
// own unit. A match with little subject ahead of it is first tried attached, under this as its match limit, and only
// if that runs out is it run again detached under its real one. PCRE2 counts a match limit afresh at each position it
// tries a match from, so what bounds an attached match is this together with ALLOW_THREADS_MIN_LENGTH. Ordinary
// matches finish well inside it, in microseconds - tokenizing 23 MB of source code with the GPT-4 pattern never needed
// more than 128 - and the worst pattern found for it, 250 alternatives each rescanning the whole subject from every
// position in it, is held to under 20 milliseconds.
//
// Running a match twice is sound only because a match has no effects. Were callouts ever bound, a probed match would
// call out twice.
static const uint32_t PROBE_MATCH_LIMIT = 256;

// A match with at least this much subject ahead of it is run detached from the start, as is the compilation of a
// pattern at least this long.
static const Py_ssize_t ALLOW_THREADS_MIN_LENGTH = 512;

static uint32_t default_match_limit(void)
{
    uint32_t limit = 0;
    pcre2_config(PCRE2_CONFIG_MATCHLIMIT, &limit);
    return limit;
}

// A context to probe under in place of one whose effective match limit is given: a copy of it, or a new one if it is
// NULL, with the probe's limit. Sets *out to NULL where the limit is already no greater than a probe's, and so
// no probe is called for. Returns false, with MemoryError set, if one could not be allocated.
static bool make_probe_context(pcre2_match_context *context, uint32_t match_limit, pcre2_match_context **out)
{
    *out = NULL;
    if (match_limit <= PROBE_MATCH_LIMIT) {
        return true;
    }

    pcre2_match_context *probe = (context != NULL)
        ? pcre2_match_context_copy(context)
        : pcre2_match_context_create(NULL);
    if (probe == NULL) {
        PyErr_NoMemory();
        return false;
    }

    pcre2_set_match_limit(probe, PROBE_MATCH_LIMIT);
    *out = probe;
    return true;
}

//

// Every instance of a heap type holds a reference to its type, and the type one to this module. A module instance
// which holds one of its own objects - in a cache, say - is therefore a cycle, and one the collector can only find if
// the object owns up to its type. So all of the types here are collected, including the three which hold no Python
// objects of their own, for which this is all there is to traverse. Like a MatchData their instances are allocated
// untracked, and tracked only once they are whole - see MatchData_wrap.
static int traverse_type(PyObject *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    return 0;
}

//

static void CompileContext_dealloc(CompileContext *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    pcre2_compile_context_free(self->context);
    tp->tp_free((PyObject *)self);
    Py_DECREF(tp);
}

PyDoc_STRVAR(
    CompileContext_create_doc,
    "create(*, bsr=None, newline=None, max_pattern_length=None, max_pattern_compiled_length=None, "
    "max_varlookbehind=None, parens_nest_limit=None, extra_options=None, optimize=None)\n\n"
    "pcre2_compile_context_create, then pcre2_set_bsr, pcre2_set_newline, pcre2_set_max_pattern_length, "
    "pcre2_set_max_pattern_compiled_length, pcre2_set_max_varlookbehind, pcre2_set_parens_nest_limit, "
    "pcre2_set_compile_extra_options, and pcre2_set_optimize for whichever are given. Those left as None keep PCRE2's "
    "defaults. optimize is one directive, or a sequence of them to apply in order."
);

static PyObject * CompileContext_create(PyObject *cls, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {
        "bsr",
        "newline",
        "max_pattern_length",
        "max_pattern_compiled_length",
        "max_varlookbehind",
        "parens_nest_limit",
        "extra_options",
        "optimize",
        NULL,
    };

    pcre2mod_state *state = get_pcre2mod_type_state((PyTypeObject *)cls);

    PyObject *bsr_obj = Py_None;
    PyObject *newline_obj = Py_None;
    PyObject *max_pattern_length_obj = Py_None;
    PyObject *max_pattern_compiled_length_obj = Py_None;
    PyObject *max_varlookbehind_obj = Py_None;
    PyObject *parens_nest_limit_obj = Py_None;
    PyObject *extra_options_obj = Py_None;
    PyObject *optimize_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "|$OOOOOOOO:create",
        kwlist,
        &bsr_obj,
        &newline_obj,
        &max_pattern_length_obj,
        &max_pattern_compiled_length_obj,
        &max_varlookbehind_obj,
        &parens_nest_limit_obj,
        &extra_options_obj,
        &optimize_obj
    )) {
        return NULL;
    }

    pcre2_compile_context *context = pcre2_compile_context_create(NULL);
    if (context == NULL) {
        return PyErr_NoMemory();
    }

    // Each setting is applied by its own setter, which is also what validates it.
    const struct {
        PyObject *obj;
        int (*set)(pcre2_compile_context *, uint32_t);
    } uint32_settings[] = {
        {bsr_obj, pcre2_set_bsr},
        {newline_obj, pcre2_set_newline},
        {max_varlookbehind_obj, pcre2_set_max_varlookbehind},
        {parens_nest_limit_obj, pcre2_set_parens_nest_limit},
        {extra_options_obj, pcre2_set_compile_extra_options},
    };
    const struct {
        PyObject *obj;
        int (*set)(pcre2_compile_context *, PCRE2_SIZE);
    } size_settings[] = {
        {max_pattern_length_obj, pcre2_set_max_pattern_length},
        {max_pattern_compiled_length_obj, pcre2_set_max_pattern_compiled_length},
    };

    int rc = 0;
    PyObject *directives = NULL;

    for (size_t i = 0; i < sizeof(uint32_settings) / sizeof(uint32_settings[0]); i++) {
        if (uint32_settings[i].obj == Py_None) {
            continue;
        }
        uint32_t value;
        if (!convert_uint32(uint32_settings[i].obj, &value)) {
            goto error;
        }
        if ((rc = uint32_settings[i].set(context, value)) < 0) {
            goto pcre2_error;
        }
    }

    for (size_t i = 0; i < sizeof(size_settings) / sizeof(size_settings[0]); i++) {
        if (size_settings[i].obj == Py_None) {
            continue;
        }
        size_t value = PyLong_AsSize_t(size_settings[i].obj);
        if (value == (size_t)-1 && PyErr_Occurred()) {
            goto error;
        }
        if ((rc = size_settings[i].set(context, (PCRE2_SIZE)value)) < 0) {
            goto pcre2_error;
        }
    }

    if (optimize_obj != Py_None) {
        directives = PyLong_Check(optimize_obj) ? PyTuple_Pack(1, optimize_obj) : PySequence_Tuple(optimize_obj);
        if (directives == NULL) {
            goto error;
        }
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(directives); i++) {
            uint32_t directive;
            if (!convert_uint32(PyTuple_GET_ITEM(directives, i), &directive)) {
                goto error;
            }
            if ((rc = pcre2_set_optimize(context, directive)) < 0) {
                goto pcre2_error;
            }
        }
        Py_CLEAR(directives);
    }

    PyTypeObject *tp = (PyTypeObject *)cls;
    CompileContext *self = PyObject_GC_New(CompileContext, tp);
    if (self == NULL) {
        goto error;
    }

    self->context = context;

    PyObject_GC_Track(self);
    return (PyObject *)self;

pcre2_error:
    set_error(state->Error, rc, -1);

error:
    Py_XDECREF(directives);
    pcre2_compile_context_free(context);
    return NULL;
}

static PyMethodDef CompileContext_methods[] = {
    {
        "create",
        (PyCFunction)(void (*)(void))CompileContext_create,
        METH_VARARGS | METH_KEYWORDS | METH_CLASS,
        CompileContext_create_doc,
    },
    {NULL, NULL, 0, NULL}
};

static PyType_Slot CompileContext_slots[] = {
    {Py_tp_dealloc, (void *)CompileContext_dealloc},
    {Py_tp_traverse, (void *)traverse_type},
    {Py_tp_methods, (void *)CompileContext_methods},
    {Py_tp_doc, (void *)"Settings applied to a compilation (pcre2_compile_context). Created by its create method."},
    {0, NULL}
};

static PyType_Spec CompileContext_spec = {
    .name = _MODULE_FULL_NAME ".CompileContext",
    .basicsize = sizeof(CompileContext),
    .itemsize = 0,
    .flags = (
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION
    ),
    .slots = CompileContext_slots,
};

//

static void MatchContext_dealloc(MatchContext *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    pcre2_match_context_free(self->probe);
    pcre2_match_context_free(self->context);
    tp->tp_free((PyObject *)self);
    Py_DECREF(tp);
}

PyDoc_STRVAR(
    MatchContext_create_doc,
    "create(*, match_limit=None, depth_limit=None, heap_limit=None, offset_limit=None)\n\n"
    "pcre2_match_context_create, then pcre2_set_match_limit, pcre2_set_depth_limit, pcre2_set_heap_limit, and "
    "pcre2_set_offset_limit for whichever are given. Those left as None keep PCRE2's defaults. The heap limit is in "
    "kibibytes, and the offset limit only applies to patterns compiled with USE_OFFSET_LIMIT."
);

static PyObject * MatchContext_create(PyObject *cls, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"match_limit", "depth_limit", "heap_limit", "offset_limit", NULL};

    PyObject *match_limit_obj = Py_None;
    PyObject *depth_limit_obj = Py_None;
    PyObject *heap_limit_obj = Py_None;
    PyObject *offset_limit_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "|$OOOO:create",
        kwlist,
        &match_limit_obj,
        &depth_limit_obj,
        &heap_limit_obj,
        &offset_limit_obj
    )) {
        return NULL;
    }

    uint32_t match_limit = 0;
    uint32_t depth_limit = 0;
    uint32_t heap_limit = 0;
    size_t offset_limit = 0;
    if (
        (match_limit_obj != Py_None && !convert_uint32(match_limit_obj, &match_limit)) ||
        (depth_limit_obj != Py_None && !convert_uint32(depth_limit_obj, &depth_limit)) ||
        (heap_limit_obj != Py_None && !convert_uint32(heap_limit_obj, &heap_limit))
    ) {
        return NULL;
    }
    if (offset_limit_obj != Py_None) {
        offset_limit = PyLong_AsSize_t(offset_limit_obj);
        if (offset_limit == (size_t)-1 && PyErr_Occurred()) {
            return NULL;
        }
    }

    pcre2_match_context *context = pcre2_match_context_create(NULL);
    if (context == NULL) {
        return PyErr_NoMemory();
    }

    if (match_limit_obj != Py_None) {
        pcre2_set_match_limit(context, match_limit);
    }
    if (depth_limit_obj != Py_None) {
        pcre2_set_depth_limit(context, depth_limit);
    }
    if (heap_limit_obj != Py_None) {
        pcre2_set_heap_limit(context, heap_limit);
    }
    if (offset_limit_obj != Py_None) {
        pcre2_set_offset_limit(context, (PCRE2_SIZE)offset_limit);
    }

    pcre2_match_context *probe = NULL;
    uint32_t effective_match_limit = (match_limit_obj != Py_None) ? match_limit : default_match_limit();
    if (!make_probe_context(context, effective_match_limit, &probe)) {
        pcre2_match_context_free(context);
        return NULL;
    }

    PyTypeObject *tp = (PyTypeObject *)cls;
    MatchContext *self = PyObject_GC_New(MatchContext, tp);
    if (self == NULL) {
        pcre2_match_context_free(probe);
        pcre2_match_context_free(context);
        return NULL;
    }

    self->context = context;
    self->probe = probe;

    PyObject_GC_Track(self);
    return (PyObject *)self;
}

static PyMethodDef MatchContext_methods[] = {
    {
        "create",
        (PyCFunction)(void (*)(void))MatchContext_create,
        METH_VARARGS | METH_KEYWORDS | METH_CLASS,
        MatchContext_create_doc,
    },
    {NULL, NULL, 0, NULL}
};

static PyType_Slot MatchContext_slots[] = {
    {Py_tp_dealloc, (void *)MatchContext_dealloc},
    {Py_tp_traverse, (void *)traverse_type},
    {Py_tp_methods, (void *)MatchContext_methods},
    {Py_tp_doc, (void *)"Limits applied to a match (pcre2_match_context). Created by its create method."},
    {0, NULL}
};

static PyType_Spec MatchContext_spec = {
    .name = _MODULE_FULL_NAME ".MatchContext",
    .basicsize = sizeof(MatchContext),
    .itemsize = 0,
    .flags = (
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION
    ),
    .slots = MatchContext_slots,
};

//

static void Code_dealloc(Code *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    pcre2_code_free(self->code);
    tp->tp_free((PyObject *)self);
    Py_DECREF(tp);
}

PyDoc_STRVAR(
    Code_pattern_info_doc,
    "pattern_info(what, /)\n\n"
    "pcre2_pattern_info. Integer items are returned as ints, INFO_NAMETABLE as the raw table (INFO_NAMECOUNT entries "
    "of INFO_NAMEENTRYSIZE bytes each), and INFO_FIRSTBITMAP as its 32 bytes, or None where there is no bitmap."
);

static PyObject * Code_pattern_info(Code *self, PyObject *arg)
{
    uint32_t what;
    if (!convert_uint32(arg, &what)) {
        return NULL;
    }

    pcre2mod_state *state = get_pcre2mod_type_state(Py_TYPE(self));

    // With no destination, pcre2_pattern_info validates the request and returns the size of its result.
    int rc = pcre2_pattern_info(self->code, what, NULL);
    if (rc < 0) {
        set_error(state->Error, rc, -1);
        return NULL;
    }
    size_t size = (size_t)rc;

    if (what == PCRE2_INFO_NAMETABLE) {
        uint32_t count = 0;
        uint32_t entry_size = 0;
        PCRE2_SPTR table = NULL;
        if (
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMECOUNT, &count)) < 0 ||
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMEENTRYSIZE, &entry_size)) < 0 ||
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMETABLE, &table)) < 0
        ) {
            set_error(state->Error, rc, -1);
            return NULL;
        }
        return PyBytes_FromStringAndSize((const char *)table, (Py_ssize_t)count * (Py_ssize_t)entry_size);
    }

    if (what == PCRE2_INFO_FIRSTBITMAP) {
        const uint8_t *bitmap = NULL;
        if ((rc = pcre2_pattern_info(self->code, what, &bitmap)) < 0) {
            set_error(state->Error, rc, -1);
            return NULL;
        }
        if (bitmap == NULL) {
            Py_RETURN_NONE;
        }
        return PyBytes_FromStringAndSize((const char *)bitmap, 32);
    }

    if (size == sizeof(uint32_t)) {
        uint32_t value = 0;
        if ((rc = pcre2_pattern_info(self->code, what, &value)) < 0) {
            set_error(state->Error, rc, -1);
            return NULL;
        }
        return PyLong_FromUnsignedLong(value);
    }

    if (size == sizeof(size_t)) {
        size_t value = 0;
        if ((rc = pcre2_pattern_info(self->code, what, &value)) < 0) {
            set_error(state->Error, rc, -1);
            return NULL;
        }
        return PyLong_FromSize_t(value);
    }

    PyErr_Format(PyExc_NotImplementedError, "pattern_info item %u has an unsupported result size", what);
    return NULL;
}

static int MatchData_acquire(MatchData *self)
{
    if (atomic_flag_test_and_set_explicit(&self->busy, memory_order_acquire)) {
        PyErr_SetString(PyExc_RuntimeError, "MatchData is already in use");
        return -1;
    }
    return 0;
}

static inline void MatchData_release(MatchData *self)
{
    atomic_flag_clear_explicit(&self->busy, memory_order_release);
}

// Letting go of what a block pins calls out: releasing a buffer calls its exporter's release hook, which can be Python
// and so can do anything, this block included. So whatever is being let go of is first taken out of the block, leaving
// the block whole and holding nothing, and only then released - the hook is handed a copy of the buffer, which is all
// a buffer is. That keeps a release from being repeated, or the block from being found half emptied, but not from
// being used meanwhile: that is what holding the block busy is for, which every caller does.

static void MatchData_unpin_subject(MatchData *self)
{
    Py_buffer subject = self->subject;
    memset(&self->subject, 0, sizeof(self->subject));
    self->subject_immutable = false;
    self->validated_start = PY_SSIZE_T_MAX;

    if (subject.obj != NULL) {
        PyBuffer_Release(&subject);
    }
}

static void MatchData_unpin(MatchData *self)
{
    PyObject *code = self->code;
    self->code = NULL;

    MatchData_unpin_subject(self);
    Py_XDECREF(code);
}

// Whether a subject is bytes proper, or a memoryview of them, and so cannot change underneath a buffer held on it. A
// read-only buffer is a weaker thing: a read-only view of memory which something else can still write to - a
// bytearray's, a file mapping's - is still read-only.
static bool is_immutable_subject(PyObject *obj)
{
    if (PyBytes_CheckExact(obj)) {
        return true;
    }
    if (PyMemoryView_Check(obj)) {
        PyObject *base = PyMemoryView_GET_BASE(obj);
        return base != NULL && PyBytes_CheckExact(base);
    }
    return false;
}

// Whether this Code may be matched against a subject. With NO_UTF_CHECK the caller has promised PCRE2 a valid subject,
// which one that changes during the match is not - but that is then theirs to keep, as it is whenever that option is
// given. Returns false, with BufferError set, if it may not.
static bool check_subject(Code *self, PyObject *subject_obj, bool immutable, uint32_t options)
{
    if (!self->utf || immutable || (options & PCRE2_NO_UTF_CHECK) != 0) {
        return true;
    }

    PyErr_Format(
        PyExc_BufferError,
        "a UTF pattern cannot be matched against %T, which could change during the match: PCRE2 trusts a subject "
        "once it has validated it. Pass bytes, or NO_UTF_CHECK to vouch for the subject yourself",
        subject_obj
    );
    return false;
}

// Unwraps an optional MatchContext argument into its context and the probe to try a short match under first, either
// of which may be NULL. Returns false, with TypeError set, for anything but a MatchContext or None.
static bool unwrap_match_context(
    pcre2mod_state *state,
    PyObject *obj,
    pcre2_match_context **context,
    pcre2_match_context **probe
)
{
    if (obj == Py_None) {
        *context = NULL;
        *probe = state->probe_context;
        return true;
    }

    if (!Py_IS_TYPE(obj, state->MatchContextType)) {
        PyErr_Format(PyExc_TypeError, "expected MatchContext or None, got %T", obj);
        return false;
    }

    *context = ((MatchContext *)obj)->context;
    *probe = ((MatchContext *)obj)->probe;
    return true;
}

PyDoc_STRVAR(
    Code_match_doc,
    "match(subject, match_data, start_offset=0, options=0, match_context=None)\n\n"
    "pcre2_match. Returns its return code as is when that is non-negative, ERROR_NOMATCH, or ERROR_PARTIAL, and "
    "raises MatchError for any other - exceeding one of a MatchContext's limits included. The subject must be "
    "bytes-like, and offsets are byte offsets into it. For a UTF pattern it must also be unable to change - bytes, or "
    "a memoryview of bytes - unless NO_UTF_CHECK is given. After a successful match the MatchData holds the subject's "
    "buffer until it is next matched into."
);

static PyObject * Code_match(Code *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {
        "subject",
        "match_data",
        "start_offset",
        "options",
        "match_context",
        NULL,
    };

    pcre2mod_state *state = get_pcre2mod_type_state(Py_TYPE(self));

    PyObject *subject_obj;
    PyObject *match_data_obj;
    Py_ssize_t start_offset = 0;
    uint32_t options = 0;
    PyObject *match_context_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "OO!|nO&O:match",
        kwlist,
        &subject_obj,
        state->MatchDataType,
        &match_data_obj,
        &start_offset,
        convert_uint32,
        &options,
        &match_context_obj
    )) {
        return NULL;
    }

    if (start_offset < 0) {
        PyErr_SetString(PyExc_ValueError, "start_offset must not be negative");
        return NULL;
    }

    pcre2_match_context *context;
    pcre2_match_context *probe;
    if (!unwrap_match_context(state, match_context_obj, &context, &probe)) {
        return NULL;
    }

    MatchData *md = (MatchData *)match_data_obj;
    if (MatchData_acquire(md) < 0) {
        return NULL;
    }

    // A subject which is still pinned from the last match is matched through the buffer already held on it.
    bool same_subject = (md->subject.obj != NULL && md->subject.obj == subject_obj);
    if (!same_subject) {
        MatchData_unpin(md);
        if (PyObject_GetBuffer(subject_obj, &md->subject, PyBUF_SIMPLE) < 0) {
            MatchData_release(md);
            return NULL;
        }
        md->subject_immutable = is_immutable_subject(subject_obj);
    }
    bool same_code = (md->code == (PyObject *)self);

    if (!check_subject(self, subject_obj, md->subject_immutable, options)) {
        MatchData_unpin(md);
        MatchData_release(md);
        return NULL;
    }

    PCRE2_SPTR subject = (PCRE2_SPTR)md->subject.buf;
    PCRE2_SIZE length = (PCRE2_SIZE)md->subject.len;

    // Left to itself PCRE2 validates everything ahead of start_offset on every call, which makes walking a subject
    // match by match quadratic in its length. That is skipped where this Code has already validated this subject from
    // at or before here, the subject can not have changed since, and - as skipping the check also skips PCRE2's own
    // for this - start_offset is not in the middle of a character.
    bool skip_utf_check = (
        same_subject &&
        same_code &&
        self->validates_utf &&
        md->subject_immutable &&
        start_offset >= md->validated_start &&
        (start_offset >= md->subject.len || (subject[start_offset] & 0xC0) != 0x80)
    );
    uint32_t match_options = options | (skip_utf_check ? PCRE2_NO_UTF_CHECK : 0);

    // A match with little subject ahead of it is first tried attached, under the probe's match limit.
    bool attached = (md->subject.len - start_offset < ALLOW_THREADS_MIN_LENGTH);

    int rc = 0;
    if (attached) {
        rc = pcre2_match(
            self->code,
            subject,
            length,
            (PCRE2_SIZE)start_offset,
            match_options,
            md->match_data,
            (probe != NULL) ? probe : context
        );
    }

    // The Code, the MatchContext, the MatchData, and the subject's buffer are all kept alive by this call's own
    // arguments, and the MatchData is marked busy, so nothing the match touches can be freed or reused while detached.
    if (!attached || (probe != NULL && rc == PCRE2_ERROR_MATCHLIMIT)) {
        Py_BEGIN_ALLOW_THREADS
        rc = pcre2_match(
            self->code,
            subject,
            length,
            (PCRE2_SIZE)start_offset,
            match_options,
            md->match_data,
            context
        );
        Py_END_ALLOW_THREADS
    }

    if (rc >= 0 || rc == PCRE2_ERROR_NOMATCH || rc == PCRE2_ERROR_PARTIAL) {
        // PCRE2 saw the attempt through, so what the block now holds is what it set for this Code.
        if (!same_code) {
            Py_XSETREF(md->code, Py_NewRef((PyObject *)self));
            md->validated_start = PY_SSIZE_T_MAX;
        }
        if (rc < 0) {
            // There is no match to advance from, so nothing will read through the subject again.
            MatchData_unpin_subject(md);
        } else if (
            self->validates_utf &&
            (match_options & PCRE2_NO_UTF_CHECK) == 0 &&
            start_offset < md->validated_start
        ) {
            md->validated_start = start_offset;
        }
        MatchData_release(md);
        return PyLong_FromLong(rc);
    }

    // pcre2_get_startchar is the offset of the offending code unit after a UTF-8 validity error, and is not otherwise
    // meaningful after a failure.
    Py_ssize_t error_offset = -1;
    if (rc <= PCRE2_ERROR_UTF8_ERR1 && rc >= PCRE2_ERROR_UTF8_ERR21) {
        error_offset = (Py_ssize_t)pcre2_get_startchar(md->match_data);
    }

    MatchData_unpin(md);
    MatchData_release(md);

    set_error(state->MatchError, rc, error_offset);
    return NULL;
}

PyDoc_STRVAR(
    Code_substitute_doc,
    "substitute(subject, replacement, start_offset=0, options=0, match_data=None, match_context=None)\n\n"
    "pcre2_substitute. Returns the result and the number of substitutions made, and raises SubstituteError for a "
    "negative return code. The replacement is in PCRE2's own syntax, not re's. The subject is held to the same rule "
    "as in match. A MatchData is only needed to reuse a block, or for SUBSTITUTE_MATCHED, which starts from the match "
    "it holds and leaves it as it was - otherwise it holds nothing afterwards."
);

static PyObject * Code_substitute(Code *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {
        "subject",
        "replacement",
        "start_offset",
        "options",
        "match_data",
        "match_context",
        NULL,
    };

    pcre2mod_state *state = get_pcre2mod_type_state(Py_TYPE(self));

    PyObject *subject_obj;
    PyObject *replacement_obj;
    Py_ssize_t start_offset = 0;
    uint32_t options = 0;
    PyObject *match_data_obj = Py_None;
    PyObject *match_context_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "OO|nO&OO:substitute",
        kwlist,
        &subject_obj,
        &replacement_obj,
        &start_offset,
        convert_uint32,
        &options,
        &match_data_obj,
        &match_context_obj
    )) {
        return NULL;
    }

    if (start_offset < 0) {
        PyErr_SetString(PyExc_ValueError, "start_offset must not be negative");
        return NULL;
    }

    pcre2_match_context *context;
    pcre2_match_context *probe;
    if (!unwrap_match_context(state, match_context_obj, &context, &probe)) {
        return NULL;
    }

    MatchData *md = NULL;
    if (match_data_obj != Py_None) {
        if (!Py_IS_TYPE(match_data_obj, state->MatchDataType)) {
            PyErr_Format(PyExc_TypeError, "expected MatchData or None, got %T", match_data_obj);
            return NULL;
        }
        md = (MatchData *)match_data_obj;
        if (MatchData_acquire(md) < 0) {
            return NULL;
        }
    }

    bool matched = (options & PCRE2_SUBSTITUTE_MATCHED) != 0;
    bool ran = false;
    Py_buffer own_subject = {.obj = NULL};
    Py_buffer replacement = {.obj = NULL};
    void *replacement_copy = NULL;
    PyObject *output = NULL;
    PyObject *result = NULL;

    // PCRE2 starts by reading what the block's last match left in it, which is only there to read if that match was
    // seen through. A block holding nothing is no better than no block, which PCRE2 would refuse for itself.
    if (matched && (md == NULL || md->code == NULL)) {
        PyErr_SetString(PyExc_ValueError, "SUBSTITUTE_MATCHED needs a MatchData holding the match to start from");
        goto done;
    }

    // A subject still pinned by the block is used through the buffer already held on it: starting from an existing
    // match, PCRE2 insists on being given the very subject that match was made in.
    Py_buffer *subject;
    bool subject_immutable;
    if (md != NULL && md->subject.obj != NULL && md->subject.obj == subject_obj) {
        subject = &md->subject;
        subject_immutable = md->subject_immutable;
    } else {
        if (PyObject_GetBuffer(subject_obj, &own_subject, PyBUF_SIMPLE) < 0) {
            goto done;
        }
        subject = &own_subject;
        subject_immutable = is_immutable_subject(subject_obj);
    }

    if (!check_subject(self, subject_obj, subject_immutable, options)) {
        goto done;
    }

    // A replacement is validated and then trusted just as a subject is, but is small and used once, so rather than
    // being refused one which could change is used through a copy.
    if (PyObject_GetBuffer(replacement_obj, &replacement, PyBUF_SIMPLE) < 0) {
        goto done;
    }
    PCRE2_SPTR replacement_ptr = (PCRE2_SPTR)replacement.buf;
    if (!is_immutable_subject(replacement_obj) && replacement.len > 0) {
        replacement_copy = PyMem_Malloc((size_t)replacement.len);
        if (replacement_copy == NULL) {
            PyErr_NoMemory();
            goto done;
        }
        memcpy(replacement_copy, replacement.buf, (size_t)replacement.len);
        replacement_ptr = (PCRE2_SPTR)replacement_copy;
    }

    // The result is built in place in a bytes object, whose own terminator takes the zero PCRE2 writes after it. A
    // guess at its size is tried first, and if PCRE2 reports that it needs more then that much exactly.
    if (subject->len > PY_SSIZE_T_MAX - replacement.len - 64) {
        PyErr_NoMemory();
        goto done;
    }
    Py_ssize_t capacity = subject->len + replacement.len + 64;
    output = PyBytes_FromStringAndSize(NULL, capacity);
    if (output == NULL) {
        goto done;
    }

    pcre2_match_data *match_data = (md != NULL) ? md->match_data : NULL;
    uint32_t substitute_options = options | PCRE2_SUBSTITUTE_OVERFLOW_LENGTH;

    // As for a match, one with little subject ahead of it is first tried attached, under the probe's match limit, and
    // run again detached under its real one if that runs out. Nothing a substitution touches while detached can be
    // freed or reused meanwhile: the Code, the MatchContext, and the MatchData are kept alive by this call's own
    // arguments, the buffers are held here, and the output is not yet anyone else's.
    bool attached = (subject->len - start_offset < ALLOW_THREADS_MIN_LENGTH);
    int rc = 0;
    PCRE2_SIZE output_length = 0;
    for (int attempt = 0; ; attempt++) {
        ran = true;

        if (attached) {
            output_length = (PCRE2_SIZE)capacity + 1;
            rc = pcre2_substitute(
                self->code,
                (PCRE2_SPTR)subject->buf,
                (PCRE2_SIZE)subject->len,
                (PCRE2_SIZE)start_offset,
                substitute_options,
                match_data,
                (probe != NULL) ? probe : context,
                replacement_ptr,
                (PCRE2_SIZE)replacement.len,
                (PCRE2_UCHAR *)PyBytes_AS_STRING(output),
                &output_length
            );
            if (probe != NULL && rc == PCRE2_ERROR_MATCHLIMIT) {
                attached = false;
            }
        }

        if (!attached) {
            PCRE2_UCHAR *output_ptr = (PCRE2_UCHAR *)PyBytes_AS_STRING(output);
            output_length = (PCRE2_SIZE)capacity + 1;
            Py_BEGIN_ALLOW_THREADS
            rc = pcre2_substitute(
                self->code,
                (PCRE2_SPTR)subject->buf,
                (PCRE2_SIZE)subject->len,
                (PCRE2_SIZE)start_offset,
                substitute_options,
                match_data,
                context,
                replacement_ptr,
                (PCRE2_SIZE)replacement.len,
                output_ptr,
                &output_length
            );
            Py_END_ALLOW_THREADS
        }

        // Having been asked to, PCRE2 carries on past a full buffer to work out the size of one which would do, the
        // terminating zero included.
        if (rc != PCRE2_ERROR_NOMEMORY || output_length == PCRE2_UNSET || attempt > 0) {
            break;
        }
        if (output_length - 1 > (PCRE2_SIZE)PY_SSIZE_T_MAX) {
            PyErr_NoMemory();
            goto done;
        }
        capacity = (Py_ssize_t)(output_length - 1);
        if (_PyBytes_Resize(&output, capacity) < 0) {
            goto done;
        }
    }

    if (rc < 0) {
        // For a malformed replacement PCRE2 reports where in it, in place of a length.
        Py_ssize_t error_offset = -1;
        if (rc != PCRE2_ERROR_NOMEMORY && output_length != PCRE2_UNSET) {
            error_offset = (Py_ssize_t)output_length;
        }
        set_error(state->SubstituteError, rc, error_offset);
        goto done;
    }

    if (_PyBytes_Resize(&output, (Py_ssize_t)output_length) < 0) {
        goto done;
    }
    result = Py_BuildValue("(Oi)", output, rc);

done:
    Py_XDECREF(output);
    PyMem_Free(replacement_copy);
    if (replacement.obj != NULL) {
        PyBuffer_Release(&replacement);
    }
    if (own_subject.obj != NULL) {
        PyBuffer_Release(&own_subject);
    }
    if (md != NULL) {
        // Starting from an existing match PCRE2 works on a copy of the block, and leaves the block itself alone.
        // Otherwise it has matched into it any number of times, and what is left in it is of no use to anyone.
        if (ran && !matched) {
            MatchData_unpin(md);
        }
        MatchData_release(md);
    }
    return result;
}

PyDoc_STRVAR(
    Code_substring_number_from_name_doc,
    "substring_number_from_name(name, /)\n\n"
    "pcre2_substring_number_from_name: the number of the group with the given name, which must be bytes. Raises "
    "Error with ERROR_NOSUBSTRING if there is none, and with ERROR_NOUNIQUESUBSTRING if there are several."
);

static PyObject * Code_substring_number_from_name(Code *self, PyObject *arg)
{
    // With no length asked for, this refuses a name which is not zero-terminated where it ends, as PCRE2 needs.
    char *name;
    if (PyBytes_AsStringAndSize(arg, &name, NULL) < 0) {
        return NULL;
    }

    int rc = pcre2_substring_number_from_name(self->code, (PCRE2_SPTR)name);
    if (rc < 0) {
        set_error(get_pcre2mod_type_state(Py_TYPE(self))->Error, rc, -1);
        return NULL;
    }
    return PyLong_FromLong(rc);
}

PyDoc_STRVAR(
    Code_substring_nametable_scan_doc,
    "substring_nametable_scan(name, /)\n\n"
    "pcre2_substring_nametable_scan: the numbers of every group with the given name, which must be bytes, in name "
    "table order. Raises Error with ERROR_NOSUBSTRING if there is none."
);

static PyObject * Code_substring_nametable_scan(Code *self, PyObject *arg)
{
    char *name;
    if (PyBytes_AsStringAndSize(arg, &name, NULL) < 0) {
        return NULL;
    }

    PCRE2_SPTR first = NULL;
    PCRE2_SPTR last = NULL;
    int entry_size = pcre2_substring_nametable_scan(self->code, (PCRE2_SPTR)name, &first, &last);
    if (entry_size < 0) {
        set_error(get_pcre2mod_type_state(Py_TYPE(self))->Error, entry_size, -1);
        return NULL;
    }

    // Each entry of the name table is the number of a group, most significant byte first, and then its name.
    Py_ssize_t n = (last - first) / entry_size + 1;
    PyObject *result = PyTuple_New(n);
    if (result == NULL) {
        return NULL;
    }
    for (Py_ssize_t i = 0; i < n; i++) {
        PCRE2_SPTR entry = first + i * entry_size;
        PyObject *item = PyLong_FromLong(((long)entry[0] << 8) | (long)entry[1]);
        if (item == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        PyTuple_SET_ITEM(result, i, item);
    }
    return result;
}

static PyObject * Code_sizeof(Code *self, PyObject *Py_UNUSED(ignored))
{
    size_t size = 0;
    pcre2_pattern_info(self->code, PCRE2_INFO_SIZE, &size);
    return PyLong_FromSize_t((size_t)Py_TYPE(self)->tp_basicsize + size);
}

static PyMethodDef Code_methods[] = {
    {"pattern_info", (PyCFunction)Code_pattern_info, METH_O, Code_pattern_info_doc},
    {"match", (PyCFunction)(void (*)(void))Code_match, METH_VARARGS | METH_KEYWORDS, Code_match_doc},
    {
        "substitute",
        (PyCFunction)(void (*)(void))Code_substitute,
        METH_VARARGS | METH_KEYWORDS,
        Code_substitute_doc,
    },
    {
        "substring_number_from_name",
        (PyCFunction)Code_substring_number_from_name,
        METH_O,
        Code_substring_number_from_name_doc,
    },
    {
        "substring_nametable_scan",
        (PyCFunction)Code_substring_nametable_scan,
        METH_O,
        Code_substring_nametable_scan_doc,
    },
    {"__sizeof__", (PyCFunction)Code_sizeof, METH_NOARGS, NULL},
    {NULL, NULL, 0, NULL}
};

static PyType_Slot Code_slots[] = {
    {Py_tp_dealloc, (void *)Code_dealloc},
    {Py_tp_traverse, (void *)traverse_type},
    {Py_tp_methods, (void *)Code_methods},
    {Py_tp_doc, (void *)"A compiled pattern (pcre2_code). Created by compile()."},
    {0, NULL}
};

static PyType_Spec Code_spec = {
    .name = _MODULE_FULL_NAME ".Code",
    .basicsize = sizeof(Code),
    .itemsize = 0,
    .flags = (
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION
    ),
    .slots = Code_slots,
};

//

static int MatchData_traverse(MatchData *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    Py_VISIT(self->code);
    Py_VISIT(self->subject.obj);
    return 0;
}

static int MatchData_clear(MatchData *self)
{
    // The collector clears a block which is still whole and still reachable from the rest of the cycle it is breaking
    // - above all from the exporter whose release hook this is about to call. So clearing holds the block busy just as
    // an operation on it does, and an operation the hook starts on it is refused, not let loose on a block which is
    // halfway through being emptied. A block is never cleared while in use, as whoever is using it holds a reference
    // to it, so one found busy has nothing to wait for and is left as it is.
    if (atomic_flag_test_and_set_explicit(&self->busy, memory_order_acquire)) {
        return 0;
    }

    MatchData_unpin(self);
    MatchData_release(self);
    return 0;
}

static void MatchData_dealloc(MatchData *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    // Nothing can reach a block with no references left to it, so there is nothing to exclude.
    MatchData_unpin(self);
    pcre2_match_data_free(self->match_data);
    tp->tp_free((PyObject *)self);
    Py_DECREF(tp);
}

static PyObject * MatchData_wrap(PyTypeObject *tp, pcre2_match_data *match_data)
{
    if (match_data == NULL) {
        return PyErr_NoMemory();
    }

    // PCRE2 neither initializes a new ovector nor writes to it on a failed match, so without this an unmatched block
    // would read back as heap garbage rather than as unset.
    PCRE2_SIZE *ovector = pcre2_get_ovector_pointer(match_data);
    size_t n = 2 * (size_t)pcre2_get_ovector_count(match_data);
    for (size_t i = 0; i < n; i++) {
        ovector[i] = PCRE2_UNSET;
    }

    // Not tp_alloc, which starts tracking the object at once: the collector is how one thread comes by another's
    // objects, and on a free-threaded build this one must be whole before it can.
    MatchData *self = PyObject_GC_New(MatchData, tp);
    if (self == NULL) {
        pcre2_match_data_free(match_data);
        return NULL;
    }

    self->match_data = match_data;
    self->code = NULL;
    memset(&self->subject, 0, sizeof(self->subject));
    self->subject_immutable = false;
    self->validated_start = PY_SSIZE_T_MAX;
    // C11 leaves a flag which was not initialized with ATOMIC_FLAG_INIT in an indeterminate state, which this settles.
    atomic_flag_clear(&self->busy);

    PyObject_GC_Track(self);
    return (PyObject *)self;
}

PyDoc_STRVAR(MatchData_create_doc, "create(ovecsize, /)\n\npcre2_match_data_create.");

static PyObject * MatchData_create(PyObject *cls, PyObject *arg)
{
    uint32_t ovecsize;
    if (!convert_uint32(arg, &ovecsize)) {
        return NULL;
    }

    return MatchData_wrap((PyTypeObject *)cls, pcre2_match_data_create(ovecsize, NULL));
}

PyDoc_STRVAR(
    MatchData_create_from_pattern_doc,
    "create_from_pattern(code, /)\n\npcre2_match_data_create_from_pattern."
);

static PyObject * MatchData_create_from_pattern(PyObject *cls, PyObject *arg)
{
    pcre2mod_state *state = get_pcre2mod_type_state((PyTypeObject *)cls);
    if (!Py_IS_TYPE(arg, state->CodeType)) {
        PyErr_Format(PyExc_TypeError, "expected Code, got %T", arg);
        return NULL;
    }

    return MatchData_wrap(
        (PyTypeObject *)cls,
        pcre2_match_data_create_from_pattern(((Code *)arg)->code, NULL)
    );
}

PyDoc_STRVAR(
    MatchData_next_match_doc,
    "next_match()\n\n"
    "pcre2_next_match. After a successful match, returns the (start_offset, options) to make the next attempt of a "
    "global search with - the options to be or'd into the caller's own - or None if no further attempt should be made."
);

static PyObject * MatchData_next_match(MatchData *self, PyObject *Py_UNUSED(ignored))
{
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    // Without a successful match there is nothing to advance from, and a block which has never been matched into holds
    // nothing PCRE2 could safely read. A subject is pinned exactly when the block holds a match.
    int more = 0;
    PCRE2_SIZE start_offset = 0;
    uint32_t options = 0;
    if (self->subject.obj != NULL) {
        more = pcre2_next_match(self->match_data, &start_offset, &options);
    }

    MatchData_release(self);

    if (!more) {
        Py_RETURN_NONE;
    }
    return Py_BuildValue("(nk)", (Py_ssize_t)start_offset, (unsigned long)options);
}

static PyObject * MatchData_get_ovector(MatchData *self, void *Py_UNUSED(closure))
{
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    PCRE2_SIZE *ovector = pcre2_get_ovector_pointer(self->match_data);
    Py_ssize_t n = 2 * (Py_ssize_t)pcre2_get_ovector_count(self->match_data);

    PyObject *result = PyTuple_New(n);
    if (result != NULL) {
        for (Py_ssize_t i = 0; i < n; i++) {
            // PCRE2_UNSET is all ones, so an offset read as a signed size is -1 exactly when it is unset.
            PyObject *item = PyLong_FromSsize_t((Py_ssize_t)ovector[i]);
            if (item == NULL) {
                Py_CLEAR(result);
                break;
            }
            PyTuple_SET_ITEM(result, i, item);
        }
    }

    MatchData_release(self);
    return result;
}

static PyObject * MatchData_get_ovector_count(MatchData *self, void *Py_UNUSED(closure))
{
    return PyLong_FromUnsignedLong(pcre2_get_ovector_count(self->match_data));
}

static PyObject * MatchData_get_mark(MatchData *self, void *Py_UNUSED(closure))
{
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    // A mark points into the compiled pattern, which is pinned whenever PCRE2 has set one, with its length in the
    // code unit ahead of it.
    PyObject *result;
    PCRE2_SPTR mark = (self->code != NULL) ? pcre2_get_mark(self->match_data) : NULL;
    if (mark != NULL) {
        result = PyBytes_FromStringAndSize((const char *)mark, (Py_ssize_t)mark[-1]);
    } else {
        result = Py_NewRef(Py_None);
    }

    MatchData_release(self);
    return result;
}

static PyObject * MatchData_get_startchar(MatchData *self, void *Py_UNUSED(closure))
{
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    PCRE2_SIZE startchar = (self->code != NULL) ? pcre2_get_startchar(self->match_data) : 0;

    MatchData_release(self);
    return PyLong_FromSize_t(startchar);
}

static PyObject * MatchData_get_size(MatchData *self, void *Py_UNUSED(closure))
{
    return PyLong_FromSize_t(pcre2_get_match_data_size(self->match_data));
}

static PyObject * MatchData_get_heapframes_size(MatchData *self, void *Py_UNUSED(closure))
{
    // A match grows the block's heap frames as it needs them.
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    PCRE2_SIZE size = pcre2_get_match_data_heapframes_size(self->match_data);

    MatchData_release(self);
    return PyLong_FromSize_t(size);
}

static PyObject * MatchData_sizeof(MatchData *self, PyObject *Py_UNUSED(ignored))
{
    if (MatchData_acquire(self) < 0) {
        return NULL;
    }

    size_t size = (
        (size_t)Py_TYPE(self)->tp_basicsize +
        pcre2_get_match_data_size(self->match_data) +
        pcre2_get_match_data_heapframes_size(self->match_data)
    );

    MatchData_release(self);
    return PyLong_FromSize_t(size);
}

static PyMethodDef MatchData_methods[] = {
    {"create", (PyCFunction)MatchData_create, METH_O | METH_CLASS, MatchData_create_doc},
    {
        "create_from_pattern",
        (PyCFunction)MatchData_create_from_pattern,
        METH_O | METH_CLASS,
        MatchData_create_from_pattern_doc,
    },
    {"next_match", (PyCFunction)MatchData_next_match, METH_NOARGS, MatchData_next_match_doc},
    {"__sizeof__", (PyCFunction)MatchData_sizeof, METH_NOARGS, NULL},
    {NULL, NULL, 0, NULL}
};

static PyGetSetDef MatchData_getset[] = {
    {
        "ovector",
        (getter)MatchData_get_ovector,
        NULL,
        "The whole ovector, flat: 2 * ovector_count offsets, with unset ones as UNSET.",
        NULL,
    },
    {"ovector_count", (getter)MatchData_get_ovector_count, NULL, "pcre2_get_ovector_count.", NULL},
    {
        "mark",
        (getter)MatchData_get_mark,
        NULL,
        "pcre2_get_mark: the name of the last (*MARK), (*PRUNE), or (*THEN) passed on the way to a match, or the one "
        "PCRE2 reports for a failed or partial match. None if there is none, or the last match raised.",
        NULL,
    },
    {
        "startchar",
        (getter)MatchData_get_startchar,
        NULL,
        "pcre2_get_startchar: where the last match started, which \\K can leave before the start of what it matched. "
        "Zero if the last match found nothing, or raised.",
        NULL,
    },
    {"size", (getter)MatchData_get_size, NULL, "pcre2_get_match_data_size.", NULL},
    {
        "heapframes_size",
        (getter)MatchData_get_heapframes_size,
        NULL,
        "pcre2_get_match_data_heapframes_size: the memory the block is holding for backtracking.",
        NULL,
    },
    {NULL, NULL, NULL, NULL, NULL}
};

static PyType_Slot MatchData_slots[] = {
    {Py_tp_dealloc, (void *)MatchData_dealloc},
    {Py_tp_traverse, (void *)MatchData_traverse},
    {Py_tp_clear, (void *)MatchData_clear},
    {Py_tp_methods, (void *)MatchData_methods},
    {Py_tp_getset, (void *)MatchData_getset},
    {Py_tp_doc, (void *)"A block holding the results of a match (pcre2_match_data). Created by its create methods."},
    {0, NULL}
};

static PyType_Spec MatchData_spec = {
    .name = _MODULE_FULL_NAME ".MatchData",
    .basicsize = sizeof(MatchData),
    .itemsize = 0,
    .flags = (
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION
    ),
    .slots = MatchData_slots,
};

//

PyDoc_STRVAR(
    compile_doc,
    "compile(pattern, options=0, compile_context=None)\n\n"
    "pcre2_compile. The pattern must be bytes-like. Nothing is implied by the options given: in particular a pattern "
    "holding UTF-8 is only treated as such with UTF."
);

static PyObject * pcre2mod_compile(PyObject *module, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"pattern", "options", "compile_context", NULL};

    pcre2mod_state *state = get_pcre2mod_state(module);

    PyObject *pattern_obj;
    uint32_t options = 0;
    PyObject *compile_context_obj = Py_None;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "O|O&O:compile",
        kwlist,
        &pattern_obj,
        convert_uint32,
        &options,
        &compile_context_obj
    )) {
        return NULL;
    }

    pcre2_compile_context *context = NULL;
    if (compile_context_obj != Py_None) {
        if (!Py_IS_TYPE(compile_context_obj, state->CompileContextType)) {
            PyErr_Format(PyExc_TypeError, "expected CompileContext or None, got %T", compile_context_obj);
            return NULL;
        }
        context = ((CompileContext *)compile_context_obj)->context;
    }

    Py_buffer pattern;
    if (PyObject_GetBuffer(pattern_obj, &pattern, PyBUF_SIMPLE) < 0) {
        return NULL;
    }

    // A pattern is validated and then trusted just as a subject is, but is small and compiled once, so rather than
    // being refused one which could change is compiled from a copy.
    PCRE2_SPTR pattern_ptr = (PCRE2_SPTR)pattern.buf;
    void *pattern_copy = NULL;
    if (!is_immutable_subject(pattern_obj) && pattern.len > 0) {
        pattern_copy = PyMem_Malloc((size_t)pattern.len);
        if (pattern_copy == NULL) {
            PyBuffer_Release(&pattern);
            return PyErr_NoMemory();
        }
        memcpy(pattern_copy, pattern.buf, (size_t)pattern.len);
        pattern_ptr = (PCRE2_SPTR)pattern_copy;
    }

    int error_code = 0;
    PCRE2_SIZE error_offset = 0;
    pcre2_code *code;
    if (pattern.len >= ALLOW_THREADS_MIN_LENGTH) {
        Py_BEGIN_ALLOW_THREADS
        code = pcre2_compile(pattern_ptr, (PCRE2_SIZE)pattern.len, options, &error_code, &error_offset, context);
        Py_END_ALLOW_THREADS
    } else {
        code = pcre2_compile(pattern_ptr, (PCRE2_SIZE)pattern.len, options, &error_code, &error_offset, context);
    }

    PyMem_Free(pattern_copy);
    PyBuffer_Release(&pattern);

    if (code == NULL) {
        set_error(state->CompileError, error_code, (Py_ssize_t)error_offset);
        return NULL;
    }

    // What the pattern was compiled as can differ from the options given, as it can also set them for itself.
    uint32_t all_options = 0;
    pcre2_pattern_info(code, PCRE2_INFO_ALLOPTIONS, &all_options);

    Code *self = PyObject_GC_New(Code, state->CodeType);
    if (self == NULL) {
        pcre2_code_free(code);
        return NULL;
    }

    self->code = code;
    self->utf = (all_options & PCRE2_UTF) != 0;
    self->validates_utf = self->utf && (all_options & PCRE2_MATCH_INVALID_UTF) == 0;

    PyObject_GC_Track(self);
    return (PyObject *)self;
}

PyDoc_STRVAR(config_doc, "config(what, /)\n\npcre2_config. String items are returned as strs, all others as ints.");

static PyObject * pcre2mod_config(PyObject *module, PyObject *arg)
{
    uint32_t what;
    if (!convert_uint32(arg, &what)) {
        return NULL;
    }

    pcre2mod_state *state = get_pcre2mod_state(module);

    // With no destination, pcre2_config validates the request and returns the size of its result: in bytes for
    // integer items, and in code units including the terminating zero for string ones.
    int rc = pcre2_config(what, NULL);
    if (rc < 0) {
        set_error(state->Error, rc, -1);
        return NULL;
    }
    size_t size = (size_t)rc;

    switch (what) {
        case PCRE2_CONFIG_JITTARGET:
        case PCRE2_CONFIG_UNICODE_VERSION:
        case PCRE2_CONFIG_VERSION: {
            PCRE2_UCHAR buf[128];
            if (size > sizeof(buf)) {
                PyErr_SetString(PyExc_NotImplementedError, "config string is longer than expected");
                return NULL;
            }
            if ((rc = pcre2_config(what, buf)) < 0) {
                set_error(state->Error, rc, -1);
                return NULL;
            }
            return PyUnicode_FromStringAndSize((const char *)buf, (Py_ssize_t)rc - 1);
        }

        default: {
            if (size != sizeof(uint32_t)) {
                PyErr_Format(PyExc_NotImplementedError, "config item %u has an unsupported result size", what);
                return NULL;
            }
            uint32_t value = 0;
            if ((rc = pcre2_config(what, &value)) < 0) {
                set_error(state->Error, rc, -1);
                return NULL;
            }
            return PyLong_FromUnsignedLong(value);
        }
    }
}

PyDoc_STRVAR(get_error_message_doc, "get_error_message(code, /)\n\npcre2_get_error_message.");

static PyObject * pcre2mod_get_error_message(PyObject *module, PyObject *arg)
{
    int code = PyLong_AsInt(arg);
    if (code == -1 && PyErr_Occurred()) {
        return NULL;
    }

    PCRE2_UCHAR buf[256];
    int rc = pcre2_get_error_message(code, buf, sizeof(buf));
    if (rc == PCRE2_ERROR_BADDATA) {
        set_error(get_pcre2mod_state(module)->Error, rc, -1);
        return NULL;
    }
    return PyUnicode_FromString((const char *)buf);
}

//

typedef struct {
    const char *name;
    long long value;
} IntConstant;

#define _PCRE2_CONSTANT(NAME) {#NAME, (long long)PCRE2_##NAME}

static const IntConstant pcre2mod_constants[] = {
    {"UNSET", -1},

    _PCRE2_CONSTANT(MAJOR),
    _PCRE2_CONSTANT(MINOR),

    // Options for both compile and match

    _PCRE2_CONSTANT(ANCHORED),
    _PCRE2_CONSTANT(NO_UTF_CHECK),
    _PCRE2_CONSTANT(ENDANCHORED),

    // Options for compile

    _PCRE2_CONSTANT(ALLOW_EMPTY_CLASS),
    _PCRE2_CONSTANT(ALT_BSUX),
    _PCRE2_CONSTANT(AUTO_CALLOUT),
    _PCRE2_CONSTANT(CASELESS),
    _PCRE2_CONSTANT(DOLLAR_ENDONLY),
    _PCRE2_CONSTANT(DOTALL),
    _PCRE2_CONSTANT(DUPNAMES),
    _PCRE2_CONSTANT(EXTENDED),
    _PCRE2_CONSTANT(FIRSTLINE),
    _PCRE2_CONSTANT(MATCH_UNSET_BACKREF),
    _PCRE2_CONSTANT(MULTILINE),
    _PCRE2_CONSTANT(NEVER_UCP),
    _PCRE2_CONSTANT(NEVER_UTF),
    _PCRE2_CONSTANT(NO_AUTO_CAPTURE),
    _PCRE2_CONSTANT(NO_AUTO_POSSESS),
    _PCRE2_CONSTANT(NO_DOTSTAR_ANCHOR),
    _PCRE2_CONSTANT(NO_START_OPTIMIZE),
    _PCRE2_CONSTANT(UCP),
    _PCRE2_CONSTANT(UNGREEDY),
    _PCRE2_CONSTANT(UTF),
    _PCRE2_CONSTANT(NEVER_BACKSLASH_C),
    _PCRE2_CONSTANT(ALT_CIRCUMFLEX),
    _PCRE2_CONSTANT(ALT_VERBNAMES),
    _PCRE2_CONSTANT(USE_OFFSET_LIMIT),
    _PCRE2_CONSTANT(EXTENDED_MORE),
    _PCRE2_CONSTANT(LITERAL),
    _PCRE2_CONSTANT(MATCH_INVALID_UTF),
    _PCRE2_CONSTANT(ALT_EXTENDED_CLASS),

    // Extra options for compile, set through a CompileContext

    _PCRE2_CONSTANT(EXTRA_ALLOW_SURROGATE_ESCAPES),
    _PCRE2_CONSTANT(EXTRA_BAD_ESCAPE_IS_LITERAL),
    _PCRE2_CONSTANT(EXTRA_MATCH_WORD),
    _PCRE2_CONSTANT(EXTRA_MATCH_LINE),
    _PCRE2_CONSTANT(EXTRA_ESCAPED_CR_IS_LF),
    _PCRE2_CONSTANT(EXTRA_ALT_BSUX),
    _PCRE2_CONSTANT(EXTRA_ALLOW_LOOKAROUND_BSK),
    _PCRE2_CONSTANT(EXTRA_CASELESS_RESTRICT),
    _PCRE2_CONSTANT(EXTRA_ASCII_BSD),
    _PCRE2_CONSTANT(EXTRA_ASCII_BSS),
    _PCRE2_CONSTANT(EXTRA_ASCII_BSW),
    _PCRE2_CONSTANT(EXTRA_ASCII_POSIX),
    _PCRE2_CONSTANT(EXTRA_ASCII_DIGIT),
    _PCRE2_CONSTANT(EXTRA_PYTHON_OCTAL),
    _PCRE2_CONSTANT(EXTRA_NO_BS0),
    _PCRE2_CONSTANT(EXTRA_NEVER_CALLOUT),
    _PCRE2_CONSTANT(EXTRA_TURKISH_CASING),

    // Optimization directives for compile

    _PCRE2_CONSTANT(OPTIMIZATION_NONE),
    _PCRE2_CONSTANT(OPTIMIZATION_FULL),
    _PCRE2_CONSTANT(AUTO_POSSESS),
    _PCRE2_CONSTANT(AUTO_POSSESS_OFF),
    _PCRE2_CONSTANT(DOTSTAR_ANCHOR),
    _PCRE2_CONSTANT(DOTSTAR_ANCHOR_OFF),
    _PCRE2_CONSTANT(START_OPTIMIZE),
    _PCRE2_CONSTANT(START_OPTIMIZE_OFF),

    // Options for match

    _PCRE2_CONSTANT(NOTBOL),
    _PCRE2_CONSTANT(NOTEOL),
    _PCRE2_CONSTANT(NOTEMPTY),
    _PCRE2_CONSTANT(NOTEMPTY_ATSTART),
    _PCRE2_CONSTANT(PARTIAL_SOFT),
    _PCRE2_CONSTANT(PARTIAL_HARD),
    _PCRE2_CONSTANT(NO_JIT),
    _PCRE2_CONSTANT(COPY_MATCHED_SUBJECT),
    _PCRE2_CONSTANT(DISABLE_RECURSELOOP_CHECK),

    // Options for substitute

    _PCRE2_CONSTANT(SUBSTITUTE_GLOBAL),
    _PCRE2_CONSTANT(SUBSTITUTE_EXTENDED),
    _PCRE2_CONSTANT(SUBSTITUTE_UNSET_EMPTY),
    _PCRE2_CONSTANT(SUBSTITUTE_UNKNOWN_UNSET),
    _PCRE2_CONSTANT(SUBSTITUTE_OVERFLOW_LENGTH),
    _PCRE2_CONSTANT(SUBSTITUTE_LITERAL),
    _PCRE2_CONSTANT(SUBSTITUTE_MATCHED),
    _PCRE2_CONSTANT(SUBSTITUTE_REPLACEMENT_ONLY),

    // Values of INFO_NEWLINE / CONFIG_NEWLINE and INFO_BSR / CONFIG_BSR

    _PCRE2_CONSTANT(NEWLINE_CR),
    _PCRE2_CONSTANT(NEWLINE_LF),
    _PCRE2_CONSTANT(NEWLINE_CRLF),
    _PCRE2_CONSTANT(NEWLINE_ANY),
    _PCRE2_CONSTANT(NEWLINE_ANYCRLF),
    _PCRE2_CONSTANT(NEWLINE_NUL),

    _PCRE2_CONSTANT(BSR_UNICODE),
    _PCRE2_CONSTANT(BSR_ANYCRLF),

    // Items for Code.pattern_info

    _PCRE2_CONSTANT(INFO_ALLOPTIONS),
    _PCRE2_CONSTANT(INFO_ARGOPTIONS),
    _PCRE2_CONSTANT(INFO_BACKREFMAX),
    _PCRE2_CONSTANT(INFO_BSR),
    _PCRE2_CONSTANT(INFO_CAPTURECOUNT),
    _PCRE2_CONSTANT(INFO_FIRSTCODEUNIT),
    _PCRE2_CONSTANT(INFO_FIRSTCODETYPE),
    _PCRE2_CONSTANT(INFO_FIRSTBITMAP),
    _PCRE2_CONSTANT(INFO_HASCRORLF),
    _PCRE2_CONSTANT(INFO_JCHANGED),
    _PCRE2_CONSTANT(INFO_JITSIZE),
    _PCRE2_CONSTANT(INFO_LASTCODEUNIT),
    _PCRE2_CONSTANT(INFO_LASTCODETYPE),
    _PCRE2_CONSTANT(INFO_MATCHEMPTY),
    _PCRE2_CONSTANT(INFO_MATCHLIMIT),
    _PCRE2_CONSTANT(INFO_MAXLOOKBEHIND),
    _PCRE2_CONSTANT(INFO_MINLENGTH),
    _PCRE2_CONSTANT(INFO_NAMECOUNT),
    _PCRE2_CONSTANT(INFO_NAMEENTRYSIZE),
    _PCRE2_CONSTANT(INFO_NAMETABLE),
    _PCRE2_CONSTANT(INFO_NEWLINE),
    _PCRE2_CONSTANT(INFO_DEPTHLIMIT),
    _PCRE2_CONSTANT(INFO_SIZE),
    _PCRE2_CONSTANT(INFO_HASBACKSLASHC),
    _PCRE2_CONSTANT(INFO_FRAMESIZE),
    _PCRE2_CONSTANT(INFO_HEAPLIMIT),
    _PCRE2_CONSTANT(INFO_EXTRAOPTIONS),

    // Items for config

    _PCRE2_CONSTANT(CONFIG_BSR),
    _PCRE2_CONSTANT(CONFIG_JIT),
    _PCRE2_CONSTANT(CONFIG_JITTARGET),
    _PCRE2_CONSTANT(CONFIG_LINKSIZE),
    _PCRE2_CONSTANT(CONFIG_MATCHLIMIT),
    _PCRE2_CONSTANT(CONFIG_NEWLINE),
    _PCRE2_CONSTANT(CONFIG_PARENSLIMIT),
    _PCRE2_CONSTANT(CONFIG_DEPTHLIMIT),
    _PCRE2_CONSTANT(CONFIG_STACKRECURSE),
    _PCRE2_CONSTANT(CONFIG_UNICODE),
    _PCRE2_CONSTANT(CONFIG_UNICODE_VERSION),
    _PCRE2_CONSTANT(CONFIG_VERSION),
    _PCRE2_CONSTANT(CONFIG_HEAPLIMIT),
    _PCRE2_CONSTANT(CONFIG_NEVER_BACKSLASH_C),
    _PCRE2_CONSTANT(CONFIG_COMPILED_WIDTHS),
    _PCRE2_CONSTANT(CONFIG_TABLES_LENGTH),

    // Error codes for compile

    _PCRE2_CONSTANT(ERROR_END_BACKSLASH),
    _PCRE2_CONSTANT(ERROR_END_BACKSLASH_C),
    _PCRE2_CONSTANT(ERROR_UNKNOWN_ESCAPE),
    _PCRE2_CONSTANT(ERROR_QUANTIFIER_OUT_OF_ORDER),
    _PCRE2_CONSTANT(ERROR_QUANTIFIER_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_MISSING_SQUARE_BRACKET),
    _PCRE2_CONSTANT(ERROR_ESCAPE_INVALID_IN_CLASS),
    _PCRE2_CONSTANT(ERROR_CLASS_RANGE_ORDER),
    _PCRE2_CONSTANT(ERROR_QUANTIFIER_INVALID),
    _PCRE2_CONSTANT(ERROR_INTERNAL_UNEXPECTED_REPEAT),
    _PCRE2_CONSTANT(ERROR_INVALID_AFTER_PARENS_QUERY),
    _PCRE2_CONSTANT(ERROR_POSIX_CLASS_NOT_IN_CLASS),
    _PCRE2_CONSTANT(ERROR_POSIX_NO_SUPPORT_COLLATING),
    _PCRE2_CONSTANT(ERROR_MISSING_CLOSING_PARENTHESIS),
    _PCRE2_CONSTANT(ERROR_BAD_SUBPATTERN_REFERENCE),
    _PCRE2_CONSTANT(ERROR_NULL_PATTERN),
    _PCRE2_CONSTANT(ERROR_BAD_OPTIONS),
    _PCRE2_CONSTANT(ERROR_MISSING_COMMENT_CLOSING),
    _PCRE2_CONSTANT(ERROR_PARENTHESES_NEST_TOO_DEEP),
    _PCRE2_CONSTANT(ERROR_PATTERN_TOO_LARGE),
    _PCRE2_CONSTANT(ERROR_HEAP_FAILED),
    _PCRE2_CONSTANT(ERROR_UNMATCHED_CLOSING_PARENTHESIS),
    _PCRE2_CONSTANT(ERROR_INTERNAL_CODE_OVERFLOW),
    _PCRE2_CONSTANT(ERROR_MISSING_CONDITION_CLOSING),
    _PCRE2_CONSTANT(ERROR_LOOKBEHIND_NOT_FIXED_LENGTH),
    _PCRE2_CONSTANT(ERROR_ZERO_RELATIVE_REFERENCE),
    _PCRE2_CONSTANT(ERROR_TOO_MANY_CONDITION_BRANCHES),
    _PCRE2_CONSTANT(ERROR_CONDITION_ASSERTION_EXPECTED),
    _PCRE2_CONSTANT(ERROR_BAD_RELATIVE_REFERENCE),
    _PCRE2_CONSTANT(ERROR_UNKNOWN_POSIX_CLASS),
    _PCRE2_CONSTANT(ERROR_INTERNAL_STUDY_ERROR),
    _PCRE2_CONSTANT(ERROR_UNICODE_NOT_SUPPORTED),
    _PCRE2_CONSTANT(ERROR_PARENTHESES_STACK_CHECK),
    _PCRE2_CONSTANT(ERROR_CODE_POINT_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_LOOKBEHIND_TOO_COMPLICATED),
    _PCRE2_CONSTANT(ERROR_LOOKBEHIND_INVALID_BACKSLASH_C),
    _PCRE2_CONSTANT(ERROR_UNSUPPORTED_ESCAPE_SEQUENCE),
    _PCRE2_CONSTANT(ERROR_CALLOUT_NUMBER_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_MISSING_CALLOUT_CLOSING),
    _PCRE2_CONSTANT(ERROR_ESCAPE_INVALID_IN_VERB),
    _PCRE2_CONSTANT(ERROR_UNRECOGNIZED_AFTER_QUERY_P),
    _PCRE2_CONSTANT(ERROR_MISSING_NAME_TERMINATOR),
    _PCRE2_CONSTANT(ERROR_DUPLICATE_SUBPATTERN_NAME),
    _PCRE2_CONSTANT(ERROR_INVALID_SUBPATTERN_NAME),
    _PCRE2_CONSTANT(ERROR_UNICODE_PROPERTIES_UNAVAILABLE),
    _PCRE2_CONSTANT(ERROR_MALFORMED_UNICODE_PROPERTY),
    _PCRE2_CONSTANT(ERROR_UNKNOWN_UNICODE_PROPERTY),
    _PCRE2_CONSTANT(ERROR_SUBPATTERN_NAME_TOO_LONG),
    _PCRE2_CONSTANT(ERROR_TOO_MANY_NAMED_SUBPATTERNS),
    _PCRE2_CONSTANT(ERROR_CLASS_INVALID_RANGE),
    _PCRE2_CONSTANT(ERROR_OCTAL_BYTE_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_INTERNAL_OVERRAN_WORKSPACE),
    _PCRE2_CONSTANT(ERROR_INTERNAL_MISSING_SUBPATTERN),
    _PCRE2_CONSTANT(ERROR_DEFINE_TOO_MANY_BRANCHES),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_O_MISSING_BRACE),
    _PCRE2_CONSTANT(ERROR_INTERNAL_UNKNOWN_NEWLINE),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_G_SYNTAX),
    _PCRE2_CONSTANT(ERROR_PARENS_QUERY_R_MISSING_CLOSING),
    _PCRE2_CONSTANT(ERROR_VERB_ARGUMENT_NOT_ALLOWED),
    _PCRE2_CONSTANT(ERROR_VERB_UNKNOWN),
    _PCRE2_CONSTANT(ERROR_SUBPATTERN_NUMBER_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_SUBPATTERN_NAME_EXPECTED),
    _PCRE2_CONSTANT(ERROR_INTERNAL_PARSED_OVERFLOW),
    _PCRE2_CONSTANT(ERROR_INVALID_OCTAL),
    _PCRE2_CONSTANT(ERROR_SUBPATTERN_NAMES_MISMATCH),
    _PCRE2_CONSTANT(ERROR_MARK_MISSING_ARGUMENT),
    _PCRE2_CONSTANT(ERROR_INVALID_HEXADECIMAL),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_C_SYNTAX),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_K_SYNTAX),
    _PCRE2_CONSTANT(ERROR_INTERNAL_BAD_CODE_LOOKBEHINDS),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_N_IN_CLASS),
    _PCRE2_CONSTANT(ERROR_CALLOUT_STRING_TOO_LONG),
    _PCRE2_CONSTANT(ERROR_UNICODE_DISALLOWED_CODE_POINT),
    _PCRE2_CONSTANT(ERROR_UTF_IS_DISABLED),
    _PCRE2_CONSTANT(ERROR_UCP_IS_DISABLED),
    _PCRE2_CONSTANT(ERROR_VERB_NAME_TOO_LONG),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_U_CODE_POINT_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_MISSING_OCTAL_OR_HEX_DIGITS),
    _PCRE2_CONSTANT(ERROR_VERSION_CONDITION_SYNTAX),
    _PCRE2_CONSTANT(ERROR_INTERNAL_BAD_CODE_AUTO_POSSESS),
    _PCRE2_CONSTANT(ERROR_CALLOUT_NO_STRING_DELIMITER),
    _PCRE2_CONSTANT(ERROR_CALLOUT_BAD_STRING_DELIMITER),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_C_CALLER_DISABLED),
    _PCRE2_CONSTANT(ERROR_QUERY_BARJX_NEST_TOO_DEEP),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_C_LIBRARY_DISABLED),
    _PCRE2_CONSTANT(ERROR_PATTERN_TOO_COMPLICATED),
    _PCRE2_CONSTANT(ERROR_LOOKBEHIND_TOO_LONG),
    _PCRE2_CONSTANT(ERROR_PATTERN_STRING_TOO_LONG),
    _PCRE2_CONSTANT(ERROR_INTERNAL_BAD_CODE),
    _PCRE2_CONSTANT(ERROR_INTERNAL_BAD_CODE_IN_SKIP),
    _PCRE2_CONSTANT(ERROR_NO_SURROGATES_IN_UTF16),
    _PCRE2_CONSTANT(ERROR_BAD_LITERAL_OPTIONS),
    _PCRE2_CONSTANT(ERROR_SUPPORTED_ONLY_IN_UNICODE),
    _PCRE2_CONSTANT(ERROR_INVALID_HYPHEN_IN_OPTIONS),
    _PCRE2_CONSTANT(ERROR_ALPHA_ASSERTION_UNKNOWN),
    _PCRE2_CONSTANT(ERROR_SCRIPT_RUN_NOT_AVAILABLE),
    _PCRE2_CONSTANT(ERROR_TOO_MANY_CAPTURES),
    _PCRE2_CONSTANT(ERROR_MISSING_OCTAL_DIGIT),
    _PCRE2_CONSTANT(ERROR_BACKSLASH_K_IN_LOOKAROUND),
    _PCRE2_CONSTANT(ERROR_MAX_VAR_LOOKBEHIND_EXCEEDED),
    _PCRE2_CONSTANT(ERROR_PATTERN_COMPILED_SIZE_TOO_BIG),
    _PCRE2_CONSTANT(ERROR_OVERSIZE_PYTHON_OCTAL),
    _PCRE2_CONSTANT(ERROR_CALLOUT_CALLER_DISABLED),
    _PCRE2_CONSTANT(ERROR_EXTRA_CASING_REQUIRES_UNICODE),
    _PCRE2_CONSTANT(ERROR_TURKISH_CASING_REQUIRES_UTF),
    _PCRE2_CONSTANT(ERROR_EXTRA_CASING_INCOMPATIBLE),
    _PCRE2_CONSTANT(ERROR_ECLASS_NEST_TOO_DEEP),
    _PCRE2_CONSTANT(ERROR_ECLASS_INVALID_OPERATOR),
    _PCRE2_CONSTANT(ERROR_ECLASS_UNEXPECTED_OPERATOR),
    _PCRE2_CONSTANT(ERROR_ECLASS_EXPECTED_OPERAND),
    _PCRE2_CONSTANT(ERROR_ECLASS_MIXED_OPERATORS),
    _PCRE2_CONSTANT(ERROR_ECLASS_HINT_SQUARE_BRACKET),
    _PCRE2_CONSTANT(ERROR_PERL_ECLASS_UNEXPECTED_EXPR),
    _PCRE2_CONSTANT(ERROR_PERL_ECLASS_EMPTY_EXPR),
    _PCRE2_CONSTANT(ERROR_PERL_ECLASS_MISSING_CLOSE),
    _PCRE2_CONSTANT(ERROR_PERL_ECLASS_UNEXPECTED_CHAR),
    _PCRE2_CONSTANT(ERROR_EXPECTED_CAPTURE_GROUP),
    _PCRE2_CONSTANT(ERROR_MISSING_OPENING_PARENTHESIS),
    _PCRE2_CONSTANT(ERROR_MISSING_NUMBER_TERMINATOR),
    _PCRE2_CONSTANT(ERROR_NULL_ERROROFFSET),

    // Error codes for everything else

    _PCRE2_CONSTANT(ERROR_NOMATCH),
    _PCRE2_CONSTANT(ERROR_PARTIAL),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR1),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR2),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR3),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR4),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR5),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR6),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR7),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR8),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR9),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR10),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR11),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR12),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR13),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR14),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR15),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR16),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR17),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR18),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR19),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR20),
    _PCRE2_CONSTANT(ERROR_UTF8_ERR21),
    _PCRE2_CONSTANT(ERROR_UTF16_ERR1),
    _PCRE2_CONSTANT(ERROR_UTF16_ERR2),
    _PCRE2_CONSTANT(ERROR_UTF16_ERR3),
    _PCRE2_CONSTANT(ERROR_UTF32_ERR1),
    _PCRE2_CONSTANT(ERROR_UTF32_ERR2),
    _PCRE2_CONSTANT(ERROR_BADDATA),
    _PCRE2_CONSTANT(ERROR_MIXEDTABLES),
    _PCRE2_CONSTANT(ERROR_BADMAGIC),
    _PCRE2_CONSTANT(ERROR_BADMODE),
    _PCRE2_CONSTANT(ERROR_BADOFFSET),
    _PCRE2_CONSTANT(ERROR_BADOPTION),
    _PCRE2_CONSTANT(ERROR_BADREPLACEMENT),
    _PCRE2_CONSTANT(ERROR_BADUTFOFFSET),
    _PCRE2_CONSTANT(ERROR_CALLOUT),
    _PCRE2_CONSTANT(ERROR_DFA_BADRESTART),
    _PCRE2_CONSTANT(ERROR_DFA_RECURSE),
    _PCRE2_CONSTANT(ERROR_DFA_UCOND),
    _PCRE2_CONSTANT(ERROR_DFA_UFUNC),
    _PCRE2_CONSTANT(ERROR_DFA_UITEM),
    _PCRE2_CONSTANT(ERROR_DFA_WSSIZE),
    _PCRE2_CONSTANT(ERROR_INTERNAL),
    _PCRE2_CONSTANT(ERROR_JIT_BADOPTION),
    _PCRE2_CONSTANT(ERROR_JIT_STACKLIMIT),
    _PCRE2_CONSTANT(ERROR_MATCHLIMIT),
    _PCRE2_CONSTANT(ERROR_NOMEMORY),
    _PCRE2_CONSTANT(ERROR_NOSUBSTRING),
    _PCRE2_CONSTANT(ERROR_NOUNIQUESUBSTRING),
    _PCRE2_CONSTANT(ERROR_NULL),
    _PCRE2_CONSTANT(ERROR_RECURSELOOP),
    _PCRE2_CONSTANT(ERROR_DEPTHLIMIT),
    _PCRE2_CONSTANT(ERROR_RECURSIONLIMIT),
    _PCRE2_CONSTANT(ERROR_UNAVAILABLE),
    _PCRE2_CONSTANT(ERROR_UNSET),
    _PCRE2_CONSTANT(ERROR_BADOFFSETLIMIT),
    _PCRE2_CONSTANT(ERROR_BADREPESCAPE),
    _PCRE2_CONSTANT(ERROR_REPMISSINGBRACE),
    _PCRE2_CONSTANT(ERROR_BADSUBSTITUTION),
    _PCRE2_CONSTANT(ERROR_BADSUBSPATTERN),
    _PCRE2_CONSTANT(ERROR_TOOMANYREPLACE),
    _PCRE2_CONSTANT(ERROR_BADSERIALIZEDDATA),
    _PCRE2_CONSTANT(ERROR_HEAPLIMIT),
    _PCRE2_CONSTANT(ERROR_CONVERT_SYNTAX),
    _PCRE2_CONSTANT(ERROR_INTERNAL_DUPMATCH),
    _PCRE2_CONSTANT(ERROR_DFA_UINVALID_UTF),
    _PCRE2_CONSTANT(ERROR_INVALIDOFFSET),
    _PCRE2_CONSTANT(ERROR_JIT_UNSUPPORTED),
    _PCRE2_CONSTANT(ERROR_REPLACECASE),
    _PCRE2_CONSTANT(ERROR_TOOLARGEREPLACE),
    _PCRE2_CONSTANT(ERROR_DIFFSUBSPATTERN),
    _PCRE2_CONSTANT(ERROR_DIFFSUBSSUBJECT),
    _PCRE2_CONSTANT(ERROR_DIFFSUBSOFFSET),
    _PCRE2_CONSTANT(ERROR_DIFFSUBSOPTIONS),
    _PCRE2_CONSTANT(ERROR_BAD_BACKSLASH_K),
    _PCRE2_CONSTANT(ERROR_PARTIALSUBS),
};

#undef _PCRE2_CONSTANT

//

// The C API other extensions use to drive this module's copy of PCRE2, exported as the `capi` capsule. A consumer
// imports this module, and only then fetches the table with PyCapsule_Import(PCRE2_CAPI_CAPSULE_NAME, 0) - which on
// its own finds a submodule only if something has already imported it. It declares this struct verbatim - it needs
// pcre2.h for the types, but links nothing - and must check abi_version, and that struct_size covers what it declares,
// before use. Entries are only ever appended under a given abi_version, so a consumer declaring an earlier, shorter
// table keeps working against a later one.
//
// Everything but the *_from_object entries is the PCRE2 function of the same name, takes the same arguments, touches
// no Python state, and may be called from any thread with or without a thread state attached.

#define PCRE2_CAPI_CAPSULE_NAME _MODULE_FULL_NAME ".capi"
#define PCRE2_CAPI_ABI_VERSION 1

typedef struct Pcre2Capi {
    uint32_t abi_version;
    uint32_t struct_size;

    // The pcre2_code of a Code object, borrowed: valid for as long as the caller keeps the object alive. Returns
    // NULL with a TypeError set if the object is not a Code. Unlike the rest, requires an attached thread state.
    const pcre2_code * (*code_from_object)(PyObject *obj);

    pcre2_code * (*compile)(PCRE2_SPTR, PCRE2_SIZE, uint32_t, int *, PCRE2_SIZE *, pcre2_compile_context *);
    void (*code_free)(pcre2_code *);
    int (*pattern_info)(const pcre2_code *, uint32_t, void *);

    pcre2_match_data * (*match_data_create)(uint32_t, pcre2_general_context *);
    pcre2_match_data * (*match_data_create_from_pattern)(const pcre2_code *, pcre2_general_context *);
    void (*match_data_free)(pcre2_match_data *);

    int (*match)(
        const pcre2_code *,
        PCRE2_SPTR,
        PCRE2_SIZE,
        PCRE2_SIZE,
        uint32_t,
        pcre2_match_data *,
        pcre2_match_context *
    );
    int (*next_match)(pcre2_match_data *, PCRE2_SIZE *, uint32_t *);

    PCRE2_SIZE * (*get_ovector_pointer)(pcre2_match_data *);
    uint32_t (*get_ovector_count)(pcre2_match_data *);
    PCRE2_SIZE (*get_startchar)(pcre2_match_data *);

    int (*get_error_message)(int, PCRE2_UCHAR *, PCRE2_SIZE);

    // Appended since the table's first version, so present only where struct_size covers them.

    // The pcre2_match_context of a MatchContext object, on the same terms as code_from_object. It is shared and
    // immutable: pass it to match, but set nothing on it.
    pcre2_match_context * (*match_context_from_object)(PyObject *obj);

    pcre2_match_context * (*match_context_create)(pcre2_general_context *);
    void (*match_context_free)(pcre2_match_context *);
    int (*set_match_limit)(pcre2_match_context *, uint32_t);
    int (*set_depth_limit)(pcre2_match_context *, uint32_t);
    int (*set_heap_limit)(pcre2_match_context *, uint32_t);
    int (*set_offset_limit)(pcre2_match_context *, PCRE2_SIZE);

    // Appended next, on the same terms.

    // The pcre2_compile_context of a CompileContext object, as match_context_from_object is for a MatchContext.
    pcre2_compile_context * (*compile_context_from_object)(PyObject *obj);

    pcre2_compile_context * (*compile_context_create)(pcre2_general_context *);
    void (*compile_context_free)(pcre2_compile_context *);
    int (*set_bsr)(pcre2_compile_context *, uint32_t);
    int (*set_newline)(pcre2_compile_context *, uint32_t);
    int (*set_max_pattern_length)(pcre2_compile_context *, PCRE2_SIZE);
    int (*set_max_pattern_compiled_length)(pcre2_compile_context *, PCRE2_SIZE);
    int (*set_max_varlookbehind)(pcre2_compile_context *, uint32_t);
    int (*set_parens_nest_limit)(pcre2_compile_context *, uint32_t);
    int (*set_compile_extra_options)(pcre2_compile_context *, uint32_t);
    int (*set_optimize)(pcre2_compile_context *, uint32_t);

    PCRE2_SPTR (*get_mark)(pcre2_match_data *);
    PCRE2_SIZE (*get_match_data_size)(pcre2_match_data *);
    PCRE2_SIZE (*get_match_data_heapframes_size)(pcre2_match_data *);

    int (*substring_number_from_name)(const pcre2_code *, PCRE2_SPTR);
    int (*substring_nametable_scan)(const pcre2_code *, PCRE2_SPTR, PCRE2_SPTR *, PCRE2_SPTR *);

    int (*substitute)(
        const pcre2_code *,
        PCRE2_SPTR,
        PCRE2_SIZE,
        PCRE2_SIZE,
        uint32_t,
        pcre2_match_data *,
        pcre2_match_context *,
        PCRE2_SPTR,
        PCRE2_SIZE,
        PCRE2_UCHAR *,
        PCRE2_SIZE *
    );
} Pcre2Capi;

// Defined below the module definition they need.
static const pcre2_code * capi_code_from_object(PyObject *obj);
static pcre2_match_context * capi_match_context_from_object(PyObject *obj);
static pcre2_compile_context * capi_compile_context_from_object(PyObject *obj);

static const Pcre2Capi pcre2mod_capi = {
    .abi_version = PCRE2_CAPI_ABI_VERSION,
    .struct_size = sizeof(Pcre2Capi),

    .code_from_object = capi_code_from_object,

    .compile = pcre2_compile,
    .code_free = pcre2_code_free,
    .pattern_info = pcre2_pattern_info,

    .match_data_create = pcre2_match_data_create,
    .match_data_create_from_pattern = pcre2_match_data_create_from_pattern,
    .match_data_free = pcre2_match_data_free,

    .match = pcre2_match,
    .next_match = pcre2_next_match,

    .get_ovector_pointer = pcre2_get_ovector_pointer,
    .get_ovector_count = pcre2_get_ovector_count,
    .get_startchar = pcre2_get_startchar,

    .get_error_message = pcre2_get_error_message,

    .match_context_from_object = capi_match_context_from_object,

    .match_context_create = pcre2_match_context_create,
    .match_context_free = pcre2_match_context_free,
    .set_match_limit = pcre2_set_match_limit,
    .set_depth_limit = pcre2_set_depth_limit,
    .set_heap_limit = pcre2_set_heap_limit,
    .set_offset_limit = pcre2_set_offset_limit,

    .compile_context_from_object = capi_compile_context_from_object,

    .compile_context_create = pcre2_compile_context_create,
    .compile_context_free = pcre2_compile_context_free,
    .set_bsr = pcre2_set_bsr,
    .set_newline = pcre2_set_newline,
    .set_max_pattern_length = pcre2_set_max_pattern_length,
    .set_max_pattern_compiled_length = pcre2_set_max_pattern_compiled_length,
    .set_max_varlookbehind = pcre2_set_max_varlookbehind,
    .set_parens_nest_limit = pcre2_set_parens_nest_limit,
    .set_compile_extra_options = pcre2_set_compile_extra_options,
    .set_optimize = pcre2_set_optimize,

    .get_mark = pcre2_get_mark,
    .get_match_data_size = pcre2_get_match_data_size,
    .get_match_data_heapframes_size = pcre2_get_match_data_heapframes_size,

    .substring_number_from_name = pcre2_substring_number_from_name,
    .substring_nametable_scan = pcre2_substring_nametable_scan,

    .substitute = pcre2_substitute,
};

//

PyDoc_STRVAR(pcre2mod_doc, "A direct binding of the 8-bit PCRE2 library");

static int pcre2mod_exec(PyObject *module)
{
    pcre2mod_state *state = get_pcre2mod_state(module);

    if (!make_probe_context(NULL, default_match_limit(), &state->probe_context)) {
        return -1;
    }

    state->CodeType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &Code_spec, NULL);
    if (state->CodeType == NULL) {
        return -1;
    }

    state->CompileContextType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &CompileContext_spec, NULL);
    if (state->CompileContextType == NULL) {
        return -1;
    }

    state->MatchContextType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &MatchContext_spec, NULL);
    if (state->MatchContextType == NULL) {
        return -1;
    }

    state->MatchDataType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &MatchData_spec, NULL);
    if (state->MatchDataType == NULL) {
        return -1;
    }

    state->Error = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".Error",
        "An error reported by PCRE2. Carries its `code`, and the `offset` it was reported at where there is one.",
        NULL,
        NULL
    );
    if (state->Error == NULL) {
        return -1;
    }

    state->CompileError = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".CompileError",
        "A pattern failed to compile. `offset` is where in the pattern.",
        state->Error,
        NULL
    );
    if (state->CompileError == NULL) {
        return -1;
    }

    state->MatchError = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".MatchError",
        "A match failed, as opposed to not matching. `offset` is set for invalid UTF-8, to where in the subject.",
        state->Error,
        NULL
    );
    if (state->MatchError == NULL) {
        return -1;
    }

    state->SubstituteError = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".SubstituteError",
        "A substitution failed. `offset` is set for a malformed replacement, to where in the replacement.",
        state->Error,
        NULL
    );
    if (state->SubstituteError == NULL) {
        return -1;
    }

    if (
        PyModule_AddObjectRef(module, "Code", (PyObject *)state->CodeType) < 0 ||
        PyModule_AddObjectRef(module, "CompileContext", (PyObject *)state->CompileContextType) < 0 ||
        PyModule_AddObjectRef(module, "MatchContext", (PyObject *)state->MatchContextType) < 0 ||
        PyModule_AddObjectRef(module, "MatchData", (PyObject *)state->MatchDataType) < 0 ||
        PyModule_AddObjectRef(module, "Error", state->Error) < 0 ||
        PyModule_AddObjectRef(module, "CompileError", state->CompileError) < 0 ||
        PyModule_AddObjectRef(module, "MatchError", state->MatchError) < 0 ||
        PyModule_AddObjectRef(module, "SubstituteError", state->SubstituteError) < 0
    ) {
        return -1;
    }

    for (size_t i = 0; i < sizeof(pcre2mod_constants) / sizeof(pcre2mod_constants[0]); i++) {
        const IntConstant *c = &pcre2mod_constants[i];
        if (PyModule_Add(module, c->name, PyLong_FromLongLong(c->value)) < 0) {
            return -1;
        }
    }

    if (PyModule_Add(module, "capi", PyCapsule_New((void *)&pcre2mod_capi, PCRE2_CAPI_CAPSULE_NAME, NULL)) < 0) {
        return -1;
    }

    return 0;
}

static int pcre2mod_traverse(PyObject *module, visitproc visit, void *arg)
{
    pcre2mod_state *state = get_pcre2mod_state(module);
    Py_VISIT(state->CodeType);
    Py_VISIT(state->CompileContextType);
    Py_VISIT(state->MatchContextType);
    Py_VISIT(state->MatchDataType);
    Py_VISIT(state->Error);
    Py_VISIT(state->CompileError);
    Py_VISIT(state->MatchError);
    Py_VISIT(state->SubstituteError);
    return 0;
}

static int pcre2mod_clear(PyObject *module)
{
    pcre2mod_state *state = get_pcre2mod_state(module);
    Py_CLEAR(state->CodeType);
    Py_CLEAR(state->CompileContextType);
    Py_CLEAR(state->MatchContextType);
    Py_CLEAR(state->MatchDataType);
    Py_CLEAR(state->Error);
    Py_CLEAR(state->CompileError);
    Py_CLEAR(state->MatchError);
    Py_CLEAR(state->SubstituteError);
    return 0;
}

static void pcre2mod_free(void *module)
{
    pcre2mod_clear((PyObject *)module);

    pcre2mod_state *state = get_pcre2mod_state((PyObject *)module);
    pcre2_match_context_free(state->probe_context);
    state->probe_context = NULL;
}

static PyMethodDef pcre2mod_methods[] = {
    {"compile", (PyCFunction)(void (*)(void))pcre2mod_compile, METH_VARARGS | METH_KEYWORDS, compile_doc},
    {"config", (PyCFunction)pcre2mod_config, METH_O, config_doc},
    {"get_error_message", (PyCFunction)pcre2mod_get_error_message, METH_O, get_error_message_doc},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef_Slot pcre2mod_slots[] = {
    {Py_mod_exec, (void *)pcre2mod_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, NULL}
};

static struct PyModuleDef pcre2mod_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_NAME,
    .m_doc = pcre2mod_doc,
    .m_size = sizeof(pcre2mod_state),
    .m_methods = pcre2mod_methods,
    .m_slots = pcre2mod_slots,
    .m_traverse = pcre2mod_traverse,
    .m_clear = pcre2mod_clear,
    .m_free = pcre2mod_free,
};

// The state of the module whose types obj is an instance of one of, or NULL - with no exception set - if it is not
// an instance of any of them. Knowing the type is one of this module's is what makes it safe to read state through it.
static pcre2mod_state * capi_state_from_object(PyObject *obj)
{
    PyObject *module = PyType_GetModuleByDef(Py_TYPE(obj), &pcre2mod_module);
    if (module == NULL) {
        PyErr_Clear();
        return NULL;
    }
    return get_pcre2mod_state(module);
}

static const pcre2_code * capi_code_from_object(PyObject *obj)
{
    pcre2mod_state *state = capi_state_from_object(obj);
    if (state == NULL || !Py_IS_TYPE(obj, state->CodeType)) {
        PyErr_Format(PyExc_TypeError, "expected Code, got %T", obj);
        return NULL;
    }

    return ((Code *)obj)->code;
}

static pcre2_match_context * capi_match_context_from_object(PyObject *obj)
{
    pcre2mod_state *state = capi_state_from_object(obj);
    if (state == NULL || !Py_IS_TYPE(obj, state->MatchContextType)) {
        PyErr_Format(PyExc_TypeError, "expected MatchContext, got %T", obj);
        return NULL;
    }

    return ((MatchContext *)obj)->context;
}

static pcre2_compile_context * capi_compile_context_from_object(PyObject *obj)
{
    pcre2mod_state *state = capi_state_from_object(obj);
    if (state == NULL || !Py_IS_TYPE(obj, state->CompileContextType)) {
        PyErr_Format(PyExc_TypeError, "expected CompileContext, got %T", obj);
        return NULL;
    }

    return ((CompileContext *)obj)->context;
}

PyMODINIT_FUNC PyInit__pcre2(void)
{
    return PyModuleDef_Init(&pcre2mod_module);
}
