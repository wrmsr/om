// @om-cext {
//   "extra_sources": [
//     "_pcre2_/src/*.c",
//     "_pcre2_/*.c.dist"
//   ],
//   "extra_headers": [
//     "_pcre2_/src/*.h",
//     "_pcre2_/*.h.generic"
//   ],
//   "extra_compile_args": [
//     "-fvisibility=hidden",
//     "-g0"
//   ],
//   "define_macros": [
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
//   ]
// }
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <atomic>
#include <cstdint>
#include <cstring>
#include <new>

#define PCRE2_CODE_UNIT_WIDTH 8
#ifndef PCRE2_STATIC
#define PCRE2_STATIC
#endif
#include "_pcre2_/src/pcre2.h"

#if PCRE2_MAJOR != 10 || PCRE2_MINOR < 47
#error "PCRE2 10.47 or newer is required (pcre2_next_match)"
#endif

// A direct binding of the 8-bit PCRE2 library. Names, option bits, return codes, and offsets are PCRE2's own: patterns
// and subjects are bytes-like, offsets count code units (bytes), `Code.match` returns what `pcre2_match` returns, and
// PCRE2_UNSET surfaces as -1 (its value read as a signed size). Anything `re`-shaped - str subjects, match objects,
// iteration, substitution - belongs in Python on top of this, not in here.
//
// Not bound: the JIT, DFA matching, substitution, serialization, callouts, the general context, and the compile and
// match contexts beyond the former's extra options word and the latter's limits.
//
// A Code and a MatchContext are immutable, and may be matched with from any number of threads at once - which is why a
// MatchContext takes its limits when created, rather than through PCRE2's setters afterwards. A MatchData is a mutable
// result block: using one from two places at once raises RuntimeError rather than corrupting it.
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
#define _PACKAGE_NAME "omcore.text.pcre2"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

// The `pcre2_` prefix belongs to the library (every public name in pcre2.h is a macro), so module boilerplate that
// would otherwise be named `pcre2_*` is named `pcre2mod_*`.

typedef struct pcre2mod_state {
    PyTypeObject *CodeType;
    PyTypeObject *MatchContextType;
    PyTypeObject *MatchDataType;
    PyObject *Error;
    PyObject *CompileError;
    PyObject *MatchError;
    // The probe (see PROBE_MATCH_LIMIT) for matches given no MatchContext, or nullptr if PCRE2's default match limit
    // is already no greater than a probe's. Not Python state, and never written to after the module is executed.
    pcre2_match_context *probe_context;
} pcre2mod_state;

static inline pcre2mod_state * get_pcre2mod_state(PyObject *module)
{
    void *state = PyModule_GetState(module);
    assert(state != nullptr);
    return (pcre2mod_state *)state;
}

static inline pcre2mod_state * get_pcre2mod_type_state(PyTypeObject *tp)
{
    void *state = PyType_GetModuleState(tp);
    assert(state != nullptr);
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
    if (msg == nullptr) {
        return;
    }

    PyObject *exc = PyObject_CallOneArg(exc_type, msg);
    Py_DECREF(msg);
    if (exc == nullptr) {
        return;
    }

    PyObject *code_obj = PyLong_FromLong(code);
    PyObject *offset_obj = (offset >= 0) ? PyLong_FromSsize_t(offset) : Py_NewRef(Py_None);
    if (
        code_obj != nullptr &&
        offset_obj != nullptr &&
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
    pcre2_match_context *context;
    // A copy of the context with its match limit lowered to a probe's, or nullptr if its own is already no greater.
    pcre2_match_context *probe;
} MatchContext;

typedef struct {
    PyObject_HEAD
    pcre2_match_data *match_data;
    // Set only while the block holds a successful match. pcre2_next_match reads through both the compiled pattern and
    // the subject of the match it advances from, so both are pinned until the block is next matched into.
    PyObject *code;
    Py_buffer subject;
    // Whether the pinned subject is bytes proper, whose contents cannot have changed for as long as they are pinned,
    // and if so the least offset the pinned Code has validated it from - everything from there to its end is known to
    // be valid UTF. PY_SSIZE_T_MAX until it has validated any of it.
    bool subject_immutable;
    Py_ssize_t validated_start;
    std::atomic_flag busy;
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
static constexpr uint32_t PROBE_MATCH_LIMIT = 256;

// A match with at least this much subject ahead of it is run detached from the start, as is the compilation of a
// pattern at least this long.
static constexpr Py_ssize_t ALLOW_THREADS_MIN_LENGTH = 512;

static uint32_t default_match_limit()
{
    uint32_t limit = 0;
    pcre2_config(PCRE2_CONFIG_MATCHLIMIT, &limit);
    return limit;
}

// A context to probe under in place of one whose effective match limit is given: a copy of it, or a new one if it is
// nullptr, with the probe's limit. Sets *out to nullptr where the limit is already no greater than a probe's, and so
// no probe is called for. Returns false, with MemoryError set, if one could not be allocated.
static bool make_probe_context(pcre2_match_context *context, uint32_t match_limit, pcre2_match_context **out)
{
    *out = nullptr;
    if (match_limit <= PROBE_MATCH_LIMIT) {
        return true;
    }

    pcre2_match_context *probe = (context != nullptr)
        ? pcre2_match_context_copy(context)
        : pcre2_match_context_create(nullptr);
    if (probe == nullptr) {
        PyErr_NoMemory();
        return false;
    }

    pcre2_set_match_limit(probe, PROBE_MATCH_LIMIT);
    *out = probe;
    return true;
}

//

static void MatchContext_dealloc(MatchContext *self)
{
    PyTypeObject *tp = Py_TYPE(self);
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
    static const char * const kwlist[] = {"match_limit", "depth_limit", "heap_limit", "offset_limit", nullptr};

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
        return nullptr;
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
        return nullptr;
    }
    if (offset_limit_obj != Py_None) {
        offset_limit = PyLong_AsSize_t(offset_limit_obj);
        if (offset_limit == (size_t)-1 && PyErr_Occurred()) {
            return nullptr;
        }
    }

    pcre2_match_context *context = pcre2_match_context_create(nullptr);
    if (context == nullptr) {
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

    pcre2_match_context *probe = nullptr;
    uint32_t effective_match_limit = (match_limit_obj != Py_None) ? match_limit : default_match_limit();
    if (!make_probe_context(context, effective_match_limit, &probe)) {
        pcre2_match_context_free(context);
        return nullptr;
    }

    PyTypeObject *tp = (PyTypeObject *)cls;
    MatchContext *self = (MatchContext *)tp->tp_alloc(tp, 0);
    if (self == nullptr) {
        pcre2_match_context_free(probe);
        pcre2_match_context_free(context);
        return nullptr;
    }

    self->context = context;
    self->probe = probe;
    return (PyObject *)self;
}

static PyMethodDef MatchContext_methods[] = {
    {
        "create",
        (PyCFunction)(void (*)(void))MatchContext_create,
        METH_VARARGS | METH_KEYWORDS | METH_CLASS,
        MatchContext_create_doc,
    },
    {nullptr, nullptr, 0, nullptr}
};

static PyType_Slot MatchContext_slots[] = {
    {Py_tp_dealloc, (void *)MatchContext_dealloc},
    {Py_tp_methods, (void *)MatchContext_methods},
    {Py_tp_doc, (void *)"Limits applied to a match (pcre2_match_context). Created by its create method."},
    {0, nullptr}
};

static PyType_Spec MatchContext_spec = {
    .name = _MODULE_FULL_NAME ".MatchContext",
    .basicsize = sizeof(MatchContext),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
    .slots = MatchContext_slots,
};

//

static void Code_dealloc(Code *self)
{
    PyTypeObject *tp = Py_TYPE(self);
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
        return nullptr;
    }

    pcre2mod_state *state = get_pcre2mod_type_state(Py_TYPE(self));

    // With no destination, pcre2_pattern_info validates the request and returns the size of its result.
    int rc = pcre2_pattern_info(self->code, what, nullptr);
    if (rc < 0) {
        set_error(state->Error, rc, -1);
        return nullptr;
    }
    size_t size = (size_t)rc;

    if (what == PCRE2_INFO_NAMETABLE) {
        uint32_t count = 0;
        uint32_t entry_size = 0;
        PCRE2_SPTR table = nullptr;
        if (
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMECOUNT, &count)) < 0 ||
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMEENTRYSIZE, &entry_size)) < 0 ||
            (rc = pcre2_pattern_info(self->code, PCRE2_INFO_NAMETABLE, &table)) < 0
        ) {
            set_error(state->Error, rc, -1);
            return nullptr;
        }
        return PyBytes_FromStringAndSize((const char *)table, (Py_ssize_t)count * (Py_ssize_t)entry_size);
    }

    if (what == PCRE2_INFO_FIRSTBITMAP) {
        const uint8_t *bitmap = nullptr;
        if ((rc = pcre2_pattern_info(self->code, what, &bitmap)) < 0) {
            set_error(state->Error, rc, -1);
            return nullptr;
        }
        if (bitmap == nullptr) {
            Py_RETURN_NONE;
        }
        return PyBytes_FromStringAndSize((const char *)bitmap, 32);
    }

    if (size == sizeof(uint32_t)) {
        uint32_t value = 0;
        if ((rc = pcre2_pattern_info(self->code, what, &value)) < 0) {
            set_error(state->Error, rc, -1);
            return nullptr;
        }
        return PyLong_FromUnsignedLong(value);
    }

    if (size == sizeof(size_t)) {
        size_t value = 0;
        if ((rc = pcre2_pattern_info(self->code, what, &value)) < 0) {
            set_error(state->Error, rc, -1);
            return nullptr;
        }
        return PyLong_FromSize_t(value);
    }

    PyErr_Format(PyExc_NotImplementedError, "pattern_info item %u has an unsupported result size", what);
    return nullptr;
}

static int MatchData_acquire(MatchData *self)
{
    if (self->busy.test_and_set(std::memory_order_acquire)) {
        PyErr_SetString(PyExc_RuntimeError, "MatchData is already in use");
        return -1;
    }
    return 0;
}

static inline void MatchData_release(MatchData *self)
{
    self->busy.clear(std::memory_order_release);
}

static void MatchData_unpin(MatchData *self)
{
    if (self->subject.obj != nullptr) {
        PyBuffer_Release(&self->subject);
    }
    Py_CLEAR(self->code);
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
        return base != nullptr && PyBytes_CheckExact(base);
    }
    return false;
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
    static const char * const kwlist[] = {
        "subject",
        "match_data",
        "start_offset",
        "options",
        "match_context",
        nullptr,
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
        return nullptr;
    }

    if (start_offset < 0) {
        PyErr_SetString(PyExc_ValueError, "start_offset must not be negative");
        return nullptr;
    }

    pcre2_match_context *context = nullptr;
    if (match_context_obj != Py_None) {
        if (!Py_IS_TYPE(match_context_obj, state->MatchContextType)) {
            PyErr_Format(PyExc_TypeError, "expected MatchContext or None, got %T", match_context_obj);
            return nullptr;
        }
        context = ((MatchContext *)match_context_obj)->context;
    }

    MatchData *md = (MatchData *)match_data_obj;
    if (MatchData_acquire(md) < 0) {
        return nullptr;
    }

    // A subject which is still pinned from the last match is matched through the buffer already held on it.
    bool same_subject = (md->subject.obj != nullptr && md->subject.obj == subject_obj);
    if (!same_subject) {
        MatchData_unpin(md);
        if (PyObject_GetBuffer(subject_obj, &md->subject, PyBUF_SIMPLE) < 0) {
            MatchData_release(md);
            return nullptr;
        }
        md->subject_immutable = is_immutable_subject(subject_obj);
    }
    bool same_code = (md->code == (PyObject *)self);

    // With NO_UTF_CHECK the caller has promised PCRE2 a valid subject, which one that changes during the match is
    // not - but that is then theirs to keep, as it is whenever that option is given.
    if (self->utf && !md->subject_immutable && (options & PCRE2_NO_UTF_CHECK) == 0) {
        MatchData_unpin(md);
        MatchData_release(md);
        PyErr_Format(
            PyExc_BufferError,
            "a UTF pattern cannot be matched against %T, which could change during the match: PCRE2 trusts a subject "
            "once it has validated it. Pass bytes, or NO_UTF_CHECK to vouch for the subject yourself",
            subject_obj
        );
        return nullptr;
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
    pcre2_match_context *probe = (match_context_obj != Py_None)
        ? ((MatchContext *)match_context_obj)->probe
        : state->probe_context;
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
            (probe != nullptr) ? probe : context
        );
    }

    // The Code, the MatchContext, the MatchData, and the subject's buffer are all kept alive by this call's own
    // arguments, and the MatchData is marked busy, so nothing the match touches can be freed or reused while detached.
    if (!attached || (probe != nullptr && rc == PCRE2_ERROR_MATCHLIMIT)) {
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

    if (rc >= 0) {
        if (!same_code) {
            Py_XSETREF(md->code, Py_NewRef((PyObject *)self));
            md->validated_start = PY_SSIZE_T_MAX;
        }
        if (self->validates_utf && (match_options & PCRE2_NO_UTF_CHECK) == 0 && start_offset < md->validated_start) {
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

    if (rc == PCRE2_ERROR_NOMATCH || rc == PCRE2_ERROR_PARTIAL) {
        return PyLong_FromLong(rc);
    }

    set_error(state->MatchError, rc, error_offset);
    return nullptr;
}

static PyMethodDef Code_methods[] = {
    {"pattern_info", (PyCFunction)Code_pattern_info, METH_O, Code_pattern_info_doc},
    {"match", (PyCFunction)(void (*)(void))Code_match, METH_VARARGS | METH_KEYWORDS, Code_match_doc},
    {nullptr, nullptr, 0, nullptr}
};

static PyType_Slot Code_slots[] = {
    {Py_tp_dealloc, (void *)Code_dealloc},
    {Py_tp_methods, (void *)Code_methods},
    {Py_tp_doc, (void *)"A compiled pattern (pcre2_code). Created by compile()."},
    {0, nullptr}
};

static PyType_Spec Code_spec = {
    .name = _MODULE_FULL_NAME ".Code",
    .basicsize = sizeof(Code),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
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
    MatchData_unpin(self);
    return 0;
}

static void MatchData_dealloc(MatchData *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    MatchData_clear(self);
    pcre2_match_data_free(self->match_data);
    tp->tp_free((PyObject *)self);
    Py_DECREF(tp);
}

static PyObject * MatchData_wrap(PyTypeObject *tp, pcre2_match_data *match_data)
{
    if (match_data == nullptr) {
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
    if (self == nullptr) {
        pcre2_match_data_free(match_data);
        return nullptr;
    }

    self->match_data = match_data;
    self->code = nullptr;
    memset(&self->subject, 0, sizeof(self->subject));
    self->subject_immutable = false;
    self->validated_start = PY_SSIZE_T_MAX;
    new (&self->busy) std::atomic_flag();

    PyObject_GC_Track(self);
    return (PyObject *)self;
}

PyDoc_STRVAR(MatchData_create_doc, "create(ovecsize, /)\n\npcre2_match_data_create.");

static PyObject * MatchData_create(PyObject *cls, PyObject *arg)
{
    uint32_t ovecsize;
    if (!convert_uint32(arg, &ovecsize)) {
        return nullptr;
    }

    return MatchData_wrap((PyTypeObject *)cls, pcre2_match_data_create(ovecsize, nullptr));
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
        return nullptr;
    }

    return MatchData_wrap(
        (PyTypeObject *)cls,
        pcre2_match_data_create_from_pattern(((Code *)arg)->code, nullptr)
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
        return nullptr;
    }

    // Without a successful match there is nothing to advance from, and a block which has never been matched into holds
    // nothing PCRE2 could safely read.
    int more = 0;
    PCRE2_SIZE start_offset = 0;
    uint32_t options = 0;
    if (self->code != nullptr) {
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
        return nullptr;
    }

    PCRE2_SIZE *ovector = pcre2_get_ovector_pointer(self->match_data);
    Py_ssize_t n = 2 * (Py_ssize_t)pcre2_get_ovector_count(self->match_data);

    PyObject *result = PyTuple_New(n);
    if (result != nullptr) {
        for (Py_ssize_t i = 0; i < n; i++) {
            // PCRE2_UNSET is all ones, so an offset read as a signed size is -1 exactly when it is unset.
            PyObject *item = PyLong_FromSsize_t((Py_ssize_t)ovector[i]);
            if (item == nullptr) {
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

static PyMethodDef MatchData_methods[] = {
    {"create", (PyCFunction)MatchData_create, METH_O | METH_CLASS, MatchData_create_doc},
    {
        "create_from_pattern",
        (PyCFunction)MatchData_create_from_pattern,
        METH_O | METH_CLASS,
        MatchData_create_from_pattern_doc,
    },
    {"next_match", (PyCFunction)MatchData_next_match, METH_NOARGS, MatchData_next_match_doc},
    {nullptr, nullptr, 0, nullptr}
};

static PyGetSetDef MatchData_getset[] = {
    {
        "ovector",
        (getter)MatchData_get_ovector,
        nullptr,
        "The whole ovector, flat: 2 * ovector_count offsets, with unset ones as UNSET.",
        nullptr,
    },
    {"ovector_count", (getter)MatchData_get_ovector_count, nullptr, "pcre2_get_ovector_count.", nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr}
};

static PyType_Slot MatchData_slots[] = {
    {Py_tp_dealloc, (void *)MatchData_dealloc},
    {Py_tp_traverse, (void *)MatchData_traverse},
    {Py_tp_clear, (void *)MatchData_clear},
    {Py_tp_methods, (void *)MatchData_methods},
    {Py_tp_getset, (void *)MatchData_getset},
    {Py_tp_doc, (void *)"A block holding the results of a match (pcre2_match_data). Created by its create methods."},
    {0, nullptr}
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
    "compile(pattern, options=0, *, extra_options=0)\n\n"
    "pcre2_compile. The pattern must be bytes-like. Nothing is implied by the options given: in particular a pattern "
    "holding UTF-8 is only treated as such with UTF. extra_options is the compile context's extra options word."
);

static PyObject * pcre2mod_compile(PyObject *module, PyObject *args, PyObject *kwargs)
{
    static const char * const kwlist[] = {"pattern", "options", "extra_options", nullptr};

    pcre2mod_state *state = get_pcre2mod_state(module);

    Py_buffer pattern;
    uint32_t options = 0;
    uint32_t extra_options = 0;
    if (!PyArg_ParseTupleAndKeywords(
        args,
        kwargs,
        "y*|O&$O&:compile",
        kwlist,
        &pattern,
        convert_uint32,
        &options,
        convert_uint32,
        &extra_options
    )) {
        return nullptr;
    }

    pcre2_compile_context *context = nullptr;
    if (extra_options != 0) {
        context = pcre2_compile_context_create(nullptr);
        if (context == nullptr) {
            PyBuffer_Release(&pattern);
            return PyErr_NoMemory();
        }
        pcre2_set_compile_extra_options(context, extra_options);
    }

    // A pattern is validated and then trusted just as a subject is, but is small and compiled once, so rather than
    // being refused a writable one is compiled from a copy.
    PCRE2_SPTR pattern_ptr = (PCRE2_SPTR)pattern.buf;
    void *pattern_copy = nullptr;
    if (!pattern.readonly && pattern.len > 0) {
        pattern_copy = PyMem_Malloc((size_t)pattern.len);
        if (pattern_copy == nullptr) {
            pcre2_compile_context_free(context);
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
    pcre2_compile_context_free(context);
    PyBuffer_Release(&pattern);

    if (code == nullptr) {
        set_error(state->CompileError, error_code, (Py_ssize_t)error_offset);
        return nullptr;
    }

    // What the pattern was compiled as can differ from the options given, as it can also set them for itself.
    uint32_t all_options = 0;
    pcre2_pattern_info(code, PCRE2_INFO_ALLOPTIONS, &all_options);

    Code *self = (Code *)state->CodeType->tp_alloc(state->CodeType, 0);
    if (self == nullptr) {
        pcre2_code_free(code);
        return nullptr;
    }

    self->code = code;
    self->utf = (all_options & PCRE2_UTF) != 0;
    self->validates_utf = self->utf && (all_options & PCRE2_MATCH_INVALID_UTF) == 0;
    return (PyObject *)self;
}

PyDoc_STRVAR(config_doc, "config(what, /)\n\npcre2_config. String items are returned as strs, all others as ints.");

static PyObject * pcre2mod_config(PyObject *module, PyObject *arg)
{
    uint32_t what;
    if (!convert_uint32(arg, &what)) {
        return nullptr;
    }

    pcre2mod_state *state = get_pcre2mod_state(module);

    // With no destination, pcre2_config validates the request and returns the size of its result: in bytes for
    // integer items, and in code units including the terminating zero for string ones.
    int rc = pcre2_config(what, nullptr);
    if (rc < 0) {
        set_error(state->Error, rc, -1);
        return nullptr;
    }
    size_t size = (size_t)rc;

    switch (what) {
        case PCRE2_CONFIG_JITTARGET:
        case PCRE2_CONFIG_UNICODE_VERSION:
        case PCRE2_CONFIG_VERSION: {
            PCRE2_UCHAR buf[128];
            if (size > sizeof(buf)) {
                PyErr_SetString(PyExc_NotImplementedError, "config string is longer than expected");
                return nullptr;
            }
            if ((rc = pcre2_config(what, buf)) < 0) {
                set_error(state->Error, rc, -1);
                return nullptr;
            }
            return PyUnicode_FromStringAndSize((const char *)buf, (Py_ssize_t)rc - 1);
        }

        default: {
            if (size != sizeof(uint32_t)) {
                PyErr_Format(PyExc_NotImplementedError, "config item %u has an unsupported result size", what);
                return nullptr;
            }
            uint32_t value = 0;
            if ((rc = pcre2_config(what, &value)) < 0) {
                set_error(state->Error, rc, -1);
                return nullptr;
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
        return nullptr;
    }

    PCRE2_UCHAR buf[256];
    int rc = pcre2_get_error_message(code, buf, sizeof(buf));
    if (rc == PCRE2_ERROR_BADDATA) {
        set_error(get_pcre2mod_state(module)->Error, rc, -1);
        return nullptr;
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

    // Extra options for compile

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

    // Error codes reachable through what is bound here. Compile errors are the positive codes, and are left unnamed.

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
    _PCRE2_CONSTANT(ERROR_BADDATA),
    _PCRE2_CONSTANT(ERROR_BADMAGIC),
    _PCRE2_CONSTANT(ERROR_BADMODE),
    _PCRE2_CONSTANT(ERROR_BADOFFSET),
    _PCRE2_CONSTANT(ERROR_BADOPTION),
    _PCRE2_CONSTANT(ERROR_BADUTFOFFSET),
    _PCRE2_CONSTANT(ERROR_INTERNAL),
    _PCRE2_CONSTANT(ERROR_MATCHLIMIT),
    _PCRE2_CONSTANT(ERROR_NOMEMORY),
    _PCRE2_CONSTANT(ERROR_NULL),
    _PCRE2_CONSTANT(ERROR_RECURSELOOP),
    _PCRE2_CONSTANT(ERROR_DEPTHLIMIT),
    _PCRE2_CONSTANT(ERROR_UNSET),
    _PCRE2_CONSTANT(ERROR_BADOFFSETLIMIT),
    _PCRE2_CONSTANT(ERROR_HEAPLIMIT),
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
// Everything but the two *_from_object entries is the PCRE2 function of the same name, takes the same arguments,
// touches no Python state, and may be called from any thread with or without a thread state attached.

#define PCRE2_CAPI_CAPSULE_NAME _MODULE_FULL_NAME ".capi"
#define PCRE2_CAPI_ABI_VERSION 1

typedef struct Pcre2Capi {
    uint32_t abi_version;
    uint32_t struct_size;

    // The pcre2_code of a Code object, borrowed: valid for as long as the caller keeps the object alive. Returns
    // nullptr with a TypeError set if the object is not a Code. Unlike the rest, requires an attached thread state.
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
} Pcre2Capi;

// Defined below the module definition they need.
static const pcre2_code * capi_code_from_object(PyObject *obj);
static pcre2_match_context * capi_match_context_from_object(PyObject *obj);

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
};

//

PyDoc_STRVAR(pcre2mod_doc, "A direct binding of the 8-bit PCRE2 library");

static int pcre2mod_exec(PyObject *module)
{
    pcre2mod_state *state = get_pcre2mod_state(module);

    if (!make_probe_context(nullptr, default_match_limit(), &state->probe_context)) {
        return -1;
    }

    state->CodeType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &Code_spec, nullptr);
    if (state->CodeType == nullptr) {
        return -1;
    }

    state->MatchContextType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &MatchContext_spec, nullptr);
    if (state->MatchContextType == nullptr) {
        return -1;
    }

    state->MatchDataType = (PyTypeObject *)PyType_FromModuleAndSpec(module, &MatchData_spec, nullptr);
    if (state->MatchDataType == nullptr) {
        return -1;
    }

    state->Error = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".Error",
        "An error reported by PCRE2. Carries its `code`, and the `offset` it was reported at where there is one.",
        nullptr,
        nullptr
    );
    if (state->Error == nullptr) {
        return -1;
    }

    state->CompileError = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".CompileError",
        "A pattern failed to compile. `offset` is where in the pattern.",
        state->Error,
        nullptr
    );
    if (state->CompileError == nullptr) {
        return -1;
    }

    state->MatchError = PyErr_NewExceptionWithDoc(
        _MODULE_FULL_NAME ".MatchError",
        "A match failed, as opposed to not matching. `offset` is set for invalid UTF-8, to where in the subject.",
        state->Error,
        nullptr
    );
    if (state->MatchError == nullptr) {
        return -1;
    }

    if (
        PyModule_AddObjectRef(module, "Code", (PyObject *)state->CodeType) < 0 ||
        PyModule_AddObjectRef(module, "MatchContext", (PyObject *)state->MatchContextType) < 0 ||
        PyModule_AddObjectRef(module, "MatchData", (PyObject *)state->MatchDataType) < 0 ||
        PyModule_AddObjectRef(module, "Error", state->Error) < 0 ||
        PyModule_AddObjectRef(module, "CompileError", state->CompileError) < 0 ||
        PyModule_AddObjectRef(module, "MatchError", state->MatchError) < 0
    ) {
        return -1;
    }

    for (const IntConstant &c : pcre2mod_constants) {
        if (PyModule_Add(module, c.name, PyLong_FromLongLong(c.value)) < 0) {
            return -1;
        }
    }

    if (PyModule_Add(module, "capi", PyCapsule_New((void *)&pcre2mod_capi, PCRE2_CAPI_CAPSULE_NAME, nullptr)) < 0) {
        return -1;
    }

    return 0;
}

static int pcre2mod_traverse(PyObject *module, visitproc visit, void *arg)
{
    pcre2mod_state *state = get_pcre2mod_state(module);
    Py_VISIT(state->CodeType);
    Py_VISIT(state->MatchContextType);
    Py_VISIT(state->MatchDataType);
    Py_VISIT(state->Error);
    Py_VISIT(state->CompileError);
    Py_VISIT(state->MatchError);
    return 0;
}

static int pcre2mod_clear(PyObject *module)
{
    pcre2mod_state *state = get_pcre2mod_state(module);
    Py_CLEAR(state->CodeType);
    Py_CLEAR(state->MatchContextType);
    Py_CLEAR(state->MatchDataType);
    Py_CLEAR(state->Error);
    Py_CLEAR(state->CompileError);
    Py_CLEAR(state->MatchError);
    return 0;
}

static void pcre2mod_free(void *module)
{
    pcre2mod_clear((PyObject *)module);

    pcre2mod_state *state = get_pcre2mod_state((PyObject *)module);
    pcre2_match_context_free(state->probe_context);
    state->probe_context = nullptr;
}

static PyMethodDef pcre2mod_methods[] = {
    {"compile", (PyCFunction)(void (*)(void))pcre2mod_compile, METH_VARARGS | METH_KEYWORDS, compile_doc},
    {"config", (PyCFunction)pcre2mod_config, METH_O, config_doc},
    {"get_error_message", (PyCFunction)pcre2mod_get_error_message, METH_O, get_error_message_doc},
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef_Slot pcre2mod_slots[] = {
    {Py_mod_exec, (void *)pcre2mod_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, nullptr}
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

// The state of the module whose types obj is an instance of one of, or nullptr - with no exception set - if it is not
// an instance of any of them. Knowing the type is one of this module's is what makes it safe to read state through it.
static pcre2mod_state * capi_state_from_object(PyObject *obj)
{
    PyObject *module = PyType_GetModuleByDef(Py_TYPE(obj), &pcre2mod_module);
    if (module == nullptr) {
        PyErr_Clear();
        return nullptr;
    }
    return get_pcre2mod_state(module);
}

static const pcre2_code * capi_code_from_object(PyObject *obj)
{
    pcre2mod_state *state = capi_state_from_object(obj);
    if (state == nullptr || !Py_IS_TYPE(obj, state->CodeType)) {
        PyErr_Format(PyExc_TypeError, "expected Code, got %T", obj);
        return nullptr;
    }

    return ((Code *)obj)->code;
}

static pcre2_match_context * capi_match_context_from_object(PyObject *obj)
{
    pcre2mod_state *state = capi_state_from_object(obj);
    if (state == nullptr || !Py_IS_TYPE(obj, state->MatchContextType)) {
        PyErr_Format(PyExc_TypeError, "expected MatchContext, got %T", obj);
        return nullptr;
    }

    return ((MatchContext *)obj)->context;
}

extern "C" {

PyMODINIT_FUNC PyInit__pcre2(void)
{
    return PyModuleDef_Init(&pcre2mod_module);
}

}
