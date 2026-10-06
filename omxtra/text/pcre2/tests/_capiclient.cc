// @om-cext
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <atomic>
#include <cstdint>
#include <exception>
#include <string>
#include <string_view>
#include <system_error>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

// For its types and constants only: this extension links no PCRE2 of its own, and reaches the library solely through
// the capsule exported by _pcre2.
#define PCRE2_CODE_UNIT_WIDTH 8
#ifndef PCRE2_STATIC
#define PCRE2_STATIC
#endif
#include "pcre2.h"

// A consumer of _pcre2's `capi` capsule, shaped like the ingest stage of a BPE trainer: given a Code object it splits
// subjects into regex chunks and counts them, off the interpreter and across threads.

//

#define _MODULE_NAME "_capiclient"
#define _PACKAGE_NAME "omcore.text.pcre2.tests"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

// Declared verbatim from ../_pcre2.cc.

#define PCRE2_CAPI_MODULE_NAME "omcore.text.pcre2._pcre2"
#define PCRE2_CAPI_CAPSULE_NAME PCRE2_CAPI_MODULE_NAME ".capi"
#define PCRE2_CAPI_ABI_VERSION 1

typedef struct Pcre2Capi {
    uint32_t abi_version;
    uint32_t struct_size;

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

    pcre2_match_context * (*match_context_from_object)(PyObject *obj);

    pcre2_match_context * (*match_context_create)(pcre2_general_context *);
    void (*match_context_free)(pcre2_match_context *);
    int (*set_match_limit)(pcre2_match_context *, uint32_t);
    int (*set_depth_limit)(pcre2_match_context *, uint32_t);
    int (*set_heap_limit)(pcre2_match_context *, uint32_t);
    int (*set_offset_limit)(pcre2_match_context *, PCRE2_SIZE);
} Pcre2Capi;

//

typedef struct capiclient_state {
    const Pcre2Capi *capi;
} capiclient_state;

static inline capiclient_state * get_capiclient_state(PyObject *module)
{
    void *state = PyModule_GetState(module);
    assert(state != nullptr);
    return (capiclient_state *)state;
}

//

static void set_pcre2_error(const Pcre2Capi *capi, int code)
{
    if (code == PCRE2_ERROR_NOMEMORY) {
        PyErr_NoMemory();
        return;
    }

    PCRE2_UCHAR buf[256];
    if (capi->get_error_message(code, buf, sizeof(buf)) == PCRE2_ERROR_BADDATA) {
        PyErr_Format(PyExc_RuntimeError, "unknown PCRE2 error %d", code);
    } else {
        PyErr_Format(PyExc_RuntimeError, "%s", (const char *)buf);
    }
}

// Unwraps an optional MatchContext argument: nullptr for None. Returns false with an exception set for anything else
// which is not a MatchContext.
static bool match_context_from_arg(const Pcre2Capi *capi, PyObject *obj, pcre2_match_context **out)
{
    *out = nullptr;
    if (obj == Py_None) {
        return true;
    }
    *out = capi->match_context_from_object(obj);
    return *out != nullptr;
}

// Acquires a buffer which the workers can read with no thread state attached. PCRE2 trusts a UTF subject once it has
// validated it, so one which can change underneath a match is an out of bounds read waiting to happen - and nothing is
// held here to stop it changing. A read-only buffer does not rule that out, as it may be a view of memory something
// else writes to, so only bytes and memoryviews of them are taken. A trainer proper takes str, whose UTF-8 is as
// immutable, and has no such concern.
static int get_immutable_buffer(PyObject *obj, Py_buffer *out)
{
    bool immutable = PyBytes_CheckExact(obj);
    if (!immutable && PyMemoryView_Check(obj)) {
        PyObject *base = PyMemoryView_GET_BASE(obj);
        immutable = (base != nullptr && PyBytes_CheckExact(base));
    }
    if (!immutable) {
        PyErr_Format(PyExc_BufferError, "expected bytes or a memoryview of bytes, got %T", obj);
        return -1;
    }
    return PyObject_GetBuffer(obj, out, PyBUF_SIMPLE);
}

// Whether PCRE2 validates the subjects of code up front, and so whether a subject it has validated once can be spared
// it for the rest of a search. It does not for a pattern compiled to match invalid UTF.
static bool validates_utf(const Pcre2Capi *capi, const pcre2_code *code)
{
    uint32_t all_options = 0;
    capi->pattern_info(code, PCRE2_INFO_ALLOPTIONS, &all_options);
    return (all_options & PCRE2_UTF) != 0 && (all_options & PCRE2_MATCH_INVALID_UTF) == 0;
}

// Hands fn the [start, end) of every match of code in subject, as a global search finds them. Returns 0, or the PCRE2
// error which stopped it. Touches no Python state.
template <typename F>
static int for_each_match(
    const Pcre2Capi *capi,
    const pcre2_code *code,
    bool code_validates_utf,
    pcre2_match_context *match_context,
    pcre2_match_data *match_data,
    std::string_view subject,
    F &&fn
)
{
    PCRE2_SIZE *ovector = capi->get_ovector_pointer(match_data);
    PCRE2_SIZE start_offset = 0;
    uint32_t options = 0;
    uint32_t next_options = 0;

    for (;;) {
        int rc = capi->match(
            code,
            (PCRE2_SPTR)subject.data(),
            (PCRE2_SIZE)subject.size(),
            start_offset,
            options | next_options,
            match_data,
            match_context
        );
        if (rc == PCRE2_ERROR_NOMATCH) {
            return 0;
        }
        if (rc < 0) {
            return rc;
        }

        fn(ovector[0], ovector[1]);

        if (!capi->next_match(match_data, &start_offset, &next_options)) {
            return 0;
        }

        // Left to itself PCRE2 validates everything ahead of start_offset on every call, making this loop quadratic
        // in the length of the subject. One successful match has validated all of it, the subject cannot change, and
        // next_match only ever moves forward to the start of a character - which is all that skipping the check needs.
        if (code_validates_utf) {
            options = PCRE2_NO_UTF_CHECK;
        }
    }
}

//

PyDoc_STRVAR(find_spans_doc, "find_spans(code, subject, match_context=None, /)");

static PyObject * find_spans(PyObject *module, PyObject *args)
{
    const Pcre2Capi *capi = get_capiclient_state(module)->capi;

    PyObject *code_obj;
    PyObject *subject_obj;
    PyObject *match_context_obj = Py_None;
    if (!PyArg_ParseTuple(args, "OO|O:find_spans", &code_obj, &subject_obj, &match_context_obj)) {
        return nullptr;
    }

    const pcre2_code *code = capi->code_from_object(code_obj);
    pcre2_match_context *match_context = nullptr;
    if (code == nullptr || !match_context_from_arg(capi, match_context_obj, &match_context)) {
        return nullptr;
    }

    Py_buffer subject;
    if (get_immutable_buffer(subject_obj, &subject) < 0) {
        return nullptr;
    }

    pcre2_match_data *match_data = capi->match_data_create_from_pattern(code, nullptr);
    if (match_data == nullptr) {
        PyBuffer_Release(&subject);
        return PyErr_NoMemory();
    }

    std::vector<std::pair<PCRE2_SIZE, PCRE2_SIZE>> spans;
    int rc;

    Py_BEGIN_ALLOW_THREADS
    try {
        rc = for_each_match(
            capi,
            code,
            validates_utf(capi, code),
            match_context,
            match_data,
            std::string_view((const char *)subject.buf, (size_t)subject.len),
            [&](PCRE2_SIZE start, PCRE2_SIZE end) {
                spans.emplace_back(start, end);
            }
        );
    } catch (const std::exception &) {
        rc = PCRE2_ERROR_NOMEMORY;
    }
    Py_END_ALLOW_THREADS

    capi->match_data_free(match_data);
    PyBuffer_Release(&subject);

    if (rc < 0) {
        set_pcre2_error(capi, rc);
        return nullptr;
    }

    PyObject *result = PyList_New((Py_ssize_t)spans.size());
    if (result == nullptr) {
        return nullptr;
    }
    for (size_t i = 0; i < spans.size(); i++) {
        PyObject *item = Py_BuildValue("(nn)", (Py_ssize_t)spans[i].first, (Py_ssize_t)spans[i].second);
        if (item == nullptr) {
            Py_DECREF(result);
            return nullptr;
        }
        PyList_SET_ITEM(result, (Py_ssize_t)i, item);
    }
    return result;
}

//

typedef std::unordered_map<std::string, int64_t> ChunkCounts;

// Counts the non-empty chunks code splits texts into. The code and match context are shared by every worker, each of
// which has a match data block of its own. Returns 0, or the first PCRE2 error any worker hit. Touches no Python state.
static int count_chunks_in(
    const Pcre2Capi *capi,
    const pcre2_code *code,
    pcre2_match_context *match_context,
    const std::vector<std::string_view> &texts,
    size_t num_threads,
    ChunkCounts &out
)
{
    std::vector<ChunkCounts> partials(num_threads);
    std::vector<int> errors(num_threads, 0);
    std::atomic<size_t> next_text{0};
    bool code_validates_utf = validates_utf(capi, code);

    auto work = [&](size_t worker) {
        pcre2_match_data *match_data = capi->match_data_create_from_pattern(code, nullptr);
        if (match_data == nullptr) {
            errors[worker] = PCRE2_ERROR_NOMEMORY;
            return;
        }

        try {
            ChunkCounts &counts = partials[worker];
            for (;;) {
                size_t i = next_text.fetch_add(1, std::memory_order_relaxed);
                if (i >= texts.size()) {
                    break;
                }

                std::string_view text = texts[i];
                int rc = for_each_match(
                    capi,
                    code,
                    code_validates_utf,
                    match_context,
                    match_data,
                    text,
                    [&](PCRE2_SIZE start, PCRE2_SIZE end) {
                        if (end > start) {
                            counts[std::string(text.substr(start, end - start))]++;
                        }
                    }
                );
                if (rc < 0) {
                    errors[worker] = rc;
                    break;
                }
            }
        } catch (const std::exception &) {
            errors[worker] = PCRE2_ERROR_NOMEMORY;
        }

        capi->match_data_free(match_data);
    };

    // Workers pull texts from a shared counter, so failing to start some of them only costs speed.
    std::vector<std::thread> threads;
    threads.reserve(num_threads - 1);
    try {
        for (size_t worker = 1; worker < num_threads; worker++) {
            threads.emplace_back(work, worker);
        }
    } catch (const std::system_error &) {
    }
    work(0);
    for (std::thread &thread : threads) {
        thread.join();
    }

    for (int error : errors) {
        if (error < 0) {
            return error;
        }
    }

    out = std::move(partials[0]);
    for (size_t worker = 1; worker < num_threads; worker++) {
        for (const auto &[chunk, count] : partials[worker]) {
            out[chunk] += count;
        }
    }
    return 0;
}

PyDoc_STRVAR(count_chunks_doc, "count_chunks(code, texts, num_threads=1, match_context=None, /)");

static PyObject * count_chunks(PyObject *module, PyObject *args)
{
    const Pcre2Capi *capi = get_capiclient_state(module)->capi;

    PyObject *code_obj;
    PyObject *texts_obj;
    int num_threads = 1;
    PyObject *match_context_obj = Py_None;
    if (!PyArg_ParseTuple(
        args,
        "OO|iO:count_chunks",
        &code_obj,
        &texts_obj,
        &num_threads,
        &match_context_obj
    )) {
        return nullptr;
    }

    if (num_threads < 1 || num_threads > 256) {
        PyErr_SetString(PyExc_ValueError, "num_threads must be between 1 and 256");
        return nullptr;
    }

    const pcre2_code *code = capi->code_from_object(code_obj);
    pcre2_match_context *match_context = nullptr;
    if (code == nullptr || !match_context_from_arg(capi, match_context_obj, &match_context)) {
        return nullptr;
    }

    // Snapshotting into a tuple, and holding a buffer on each - immutable - item, is what keeps every text in place
    // and unchanged while the workers read them with no thread state attached.
    PyObject *texts_tuple = PySequence_Tuple(texts_obj);
    if (texts_tuple == nullptr) {
        return nullptr;
    }

    Py_ssize_t num_texts = PyTuple_GET_SIZE(texts_tuple);
    std::vector<Py_buffer> buffers;
    std::vector<std::string_view> texts;
    ChunkCounts counts;
    PyObject *result = nullptr;
    int rc = 0;
    bool acquired = true;

    try {
        buffers.reserve((size_t)num_texts);
        texts.reserve((size_t)num_texts);
    } catch (const std::exception &) {
        Py_DECREF(texts_tuple);
        return PyErr_NoMemory();
    }

    for (Py_ssize_t i = 0; i < num_texts; i++) {
        Py_buffer buffer;
        if (get_immutable_buffer(PyTuple_GET_ITEM(texts_tuple, i), &buffer) < 0) {
            acquired = false;
            break;
        }
        buffers.push_back(buffer);
        texts.emplace_back((const char *)buffer.buf, (size_t)buffer.len);
    }

    if (acquired) {
        Py_BEGIN_ALLOW_THREADS
        try {
            rc = count_chunks_in(capi, code, match_context, texts, (size_t)num_threads, counts);
        } catch (const std::exception &) {
            rc = PCRE2_ERROR_NOMEMORY;
        }
        Py_END_ALLOW_THREADS

        if (rc < 0) {
            set_pcre2_error(capi, rc);
        } else {
            result = PyDict_New();
        }
    }

    for (Py_buffer &buffer : buffers) {
        PyBuffer_Release(&buffer);
    }
    Py_DECREF(texts_tuple);

    if (result == nullptr) {
        return nullptr;
    }

    for (const auto &[chunk, count] : counts) {
        PyObject *key = PyBytes_FromStringAndSize(chunk.data(), (Py_ssize_t)chunk.size());
        PyObject *value = PyLong_FromLongLong(count);
        int failed = (key == nullptr || value == nullptr || PyDict_SetItem(result, key, value) < 0);
        Py_XDECREF(key);
        Py_XDECREF(value);
        if (failed) {
            Py_DECREF(result);
            return nullptr;
        }
    }
    return result;
}

//

PyDoc_STRVAR(capiclient_doc, "A consumer of the _pcre2 capi capsule");

static int capiclient_exec(PyObject *module)
{
    capiclient_state *state = get_capiclient_state(module);

    // PyCapsule_Import walks the dotted name by attribute access, which finds a submodule only once something has
    // imported it - so that has to be done here first, or this module would only load after _pcre2 happened to.
    PyObject *pcre2_module = PyImport_ImportModule(PCRE2_CAPI_MODULE_NAME);
    if (pcre2_module == nullptr) {
        return -1;
    }
    const Pcre2Capi *capi = (const Pcre2Capi *)PyCapsule_Import(PCRE2_CAPI_CAPSULE_NAME, 0);
    Py_DECREF(pcre2_module);
    if (capi == nullptr) {
        return -1;
    }

    // abi_version and struct_size lead the struct in every version of it, so are always safe to read.
    if (capi->abi_version != PCRE2_CAPI_ABI_VERSION || capi->struct_size < sizeof(Pcre2Capi)) {
        PyErr_Format(
            PyExc_ImportError,
            "incompatible %s: abi version %u with size %u, need version %u with size of at least %zu",
            PCRE2_CAPI_CAPSULE_NAME,
            capi->abi_version,
            capi->struct_size,
            PCRE2_CAPI_ABI_VERSION,
            sizeof(Pcre2Capi)
        );
        return -1;
    }

    state->capi = capi;
    return 0;
}

static PyMethodDef capiclient_methods[] = {
    {"find_spans", (PyCFunction)find_spans, METH_VARARGS, find_spans_doc},
    {"count_chunks", (PyCFunction)count_chunks, METH_VARARGS, count_chunks_doc},
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef_Slot capiclient_slots[] = {
    {Py_mod_exec, (void *)capiclient_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, nullptr}
};

static struct PyModuleDef capiclient_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_NAME,
    .m_doc = capiclient_doc,
    .m_size = sizeof(capiclient_state),
    .m_methods = capiclient_methods,
    .m_slots = capiclient_slots,
};

extern "C" {

PyMODINIT_FUNC PyInit__capiclient(void)
{
    return PyModuleDef_Init(&capiclient_module);
}

}
