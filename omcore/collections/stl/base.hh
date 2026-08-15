#pragma once

#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iterator>
#include <limits>
#include <mutex>
#include <new>
#include <type_traits>
#include <vector>

#include "tlx/tlx/container/btree.hpp"


#define _MODULE_NAME "_stl"
#define _PACKAGE_NAME "omcore.collections.stl"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME


//
// Module state
//


struct PyModuleDef *stl_module_def();


struct stl_state {
    PyTypeObject *set_type;
    PyTypeObject *unordered_set_type;
    PyTypeObject *map_type;
    PyTypeObject *unordered_map_type;
    PyTypeObject *vector_type;
    PyTypeObject *iter_type;

    PyObject *abc_set;
    PyObject *abc_mapping;
    PyObject *abc_keys_view;
    PyObject *abc_values_view;
    PyObject *abc_items_view;
};


inline stl_state *get_state(PyObject *mod) {
    return (stl_state *)PyModule_GetState(mod);
}


inline stl_state *find_state(PyTypeObject *tp) {
    PyObject *mod = PyType_GetModuleByDef(tp, stl_module_def());
    if (mod == nullptr) {
        return nullptr;
    }
    return get_state(mod);
}


// For binary operator slots, where either operand (but at least one) is one of our types.
inline stl_state *find_state_2(PyObject *v, PyObject *w) {
    stl_state *st = find_state(Py_TYPE(v));
    if (st == nullptr) {
        PyErr_Clear();
        st = find_state(Py_TYPE(w));
        if (st == nullptr) {
            PyErr_Clear();
        }
    }
    return st;
}


//
// Dtypes
//


enum class Dt : uint8_t {
    U64,
    I64,
    I32,
    I16,
    F64,
    F32,
    OBJ,
};


enum class Ovf : uint8_t {
    RAISE,
    CLAMP,
    WRAP,
};


enum class ColKind : uint8_t {
    SORTED_SET,
    HASH_SET,
    SORTED_MAP,
    HASH_MAP,
    VECTOR,
};


struct DtypeSpec {
    Dt dt;
    Ovf ovf;
};


inline int parse_dtype(PyObject *o, DtypeSpec *out) {
    if (!PyUnicode_Check(o)) {
        PyErr_Format(PyExc_TypeError, "dtype must be a str, got %.100s", Py_TYPE(o)->tp_name);
        return -1;
    }

    Py_ssize_t sn;
    const char *s = PyUnicode_AsUTF8AndSize(o, &sn);
    if (s == nullptr) {
        return -1;
    }
    if (std::strlen(s) != (size_t)sn) {
        // Embedded NUL: the strcmp below would happily match its prefix.
        PyErr_Format(PyExc_ValueError, "unknown dtype: %.200s", s);
        return -1;
    }

    static const struct {
        const char *name;
        Dt dt;
        Ovf ovf;
    } TABLE[] = {
        {"uint64", Dt::U64, Ovf::RAISE},
        {"uint64-raise", Dt::U64, Ovf::RAISE},
        {"uint64-clamp", Dt::U64, Ovf::CLAMP},
        {"uint64-wrap", Dt::U64, Ovf::WRAP},
        {"int64", Dt::I64, Ovf::RAISE},
        {"int64-raise", Dt::I64, Ovf::RAISE},
        {"int64-clamp", Dt::I64, Ovf::CLAMP},
        {"int64-wrap", Dt::I64, Ovf::WRAP},
        {"int32", Dt::I32, Ovf::RAISE},
        {"int32-raise", Dt::I32, Ovf::RAISE},
        {"int32-clamp", Dt::I32, Ovf::CLAMP},
        {"int32-wrap", Dt::I32, Ovf::WRAP},
        {"int16", Dt::I16, Ovf::RAISE},
        {"int16-raise", Dt::I16, Ovf::RAISE},
        {"int16-clamp", Dt::I16, Ovf::CLAMP},
        {"int16-wrap", Dt::I16, Ovf::WRAP},
        {"float64", Dt::F64, Ovf::RAISE},
        {"float32", Dt::F32, Ovf::RAISE},
        {"object", Dt::OBJ, Ovf::RAISE},
    };

    for (const auto &e : TABLE) {
        if (std::strcmp(s, e.name) == 0) {
            *out = DtypeSpec{e.dt, e.ovf};
            return 0;
        }
    }

    PyErr_Format(PyExc_ValueError, "unknown dtype: %.200s", s);
    return -1;
}


// Switches over Dt / Ovf are deliberately exhaustive with no default: a forgotten case in any of them (most
// dangerously the impl factories, where a default would silently materialize the wrong dtype) is a -Wswitch warning
// instead of a runtime misroute.
inline const char *dtype_name(Dt dt, Ovf ovf) {
    switch (dt) {
        case Dt::U64:
            switch (ovf) {
                case Ovf::RAISE: return "uint64-raise";
                case Ovf::CLAMP: return "uint64-clamp";
                case Ovf::WRAP: return "uint64-wrap";
            }
            break;
        case Dt::I64:
            switch (ovf) {
                case Ovf::RAISE: return "int64-raise";
                case Ovf::CLAMP: return "int64-clamp";
                case Ovf::WRAP: return "int64-wrap";
            }
            break;
        case Dt::I32:
            switch (ovf) {
                case Ovf::RAISE: return "int32-raise";
                case Ovf::CLAMP: return "int32-clamp";
                case Ovf::WRAP: return "int32-wrap";
            }
            break;
        case Dt::I16:
            switch (ovf) {
                case Ovf::RAISE: return "int16-raise";
                case Ovf::CLAMP: return "int16-clamp";
                case Ovf::WRAP: return "int16-wrap";
            }
            break;
        case Dt::F64:
            return "float64";
        case Dt::F32:
            return "float32";
        case Dt::OBJ:
            return "object";
    }
    Py_UNREACHABLE();
}


//
// Error plumbing
//
// Python errors raised from inside comparator / hasher functors (which run deep inside STL container machinery) are
// carried out as a py_err_set C++ exception - the Python error indicator is already set when it is thrown. Every
// Python-visible entry point runs under py_shield / py_shield_int, which translate the exception back into the usual
// nullptr / -1 convention. Single-element std::map / std::set / unordered insertions give the strong guarantee when a
// comparator or equality predicate throws, which is what keeps the containers consistent across such errors.
//


struct py_err_set : std::exception {
};


template <typename F>
PyObject *py_shield(F &&fn) noexcept {
    try {
        return fn();
    }
    catch (py_err_set &) {
        return nullptr;
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return nullptr;
    }
}


template <typename F>
int py_shield_int(F &&fn) noexcept {
    try {
        return fn();
    }
    catch (py_err_set &) {
        return -1;
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return -1;
    }
}


//
// PyMem allocator plumbing
//
// All native storage - container nodes and arrays, the impl and iterator objects, the Bin's spill vector - is
// allocated through CPython's PYMEM_DOMAIN_MEM allocator (PyMem_Malloc / PyMem_Free) rather than global operator
// new. Two reasons: tracemalloc hooks that domain, so native container memory becomes visible to Python memory
// profiling; and on free-threaded builds the domain is backed by mimalloc, which behaves far better than glibc
// malloc under cross-thread allocate/free traffic. The obligation this imposes is that every allocation and free
// must happen with an attached thread state - which holds throughout this module: all structural work runs inside
// Python-visible entry points, and the only detached window (blocking on the container mutex in col_lock_acquire)
// neither allocates nor frees. (PyMem_RawMalloc would lift that obligation, but the raw domain is a plain malloc
// passthrough - no mimalloc, no pymalloc pools - so the attached-state discipline is worth keeping.)
//


template <typename T>
struct PyMemAllocator {
    using value_type = T;

    PyMemAllocator() = default;

    template <typename U>
    PyMemAllocator(const PyMemAllocator<U> &) noexcept {}

    T *allocate(size_t n) {
        if (n > SIZE_MAX / sizeof(T)) {
            throw std::bad_alloc();
        }
        void *p = PyMem_Malloc(n * sizeof(T));
        if (p == nullptr) {
            throw std::bad_alloc();
        }
        return (T *)p;
    }

    void deallocate(T *p, size_t) noexcept {
        PyMem_Free(p);
    }

    template <typename U>
    bool operator==(const PyMemAllocator<U> &) const noexcept {
        return true;
    }
};


//
// Deferred decref bin
//
// Structural operations never Py_DECREF displaced references while the container lock is held - a DECREF can run
// arbitrary __del__ code. Instead dead references are moved into a Bin, which is drained (or destructed) only after
// the lock guard has been released. Callers must therefore always declare the Bin *before* the guard, so that on any
// exit path the guard unlocks first and the bin drains second.
//


struct Bin {
    PyObject *slot0 = nullptr;
    PyObject *slot1 = nullptr;
    std::vector<PyObject *, PyMemAllocator<PyObject *>> rest;

    Bin() = default;
    Bin(const Bin &) = delete;
    Bin &operator=(const Bin &) = delete;

    ~Bin() {
        drain();
    }

    // Bulk paths must reserve up front so that put() cannot allocate (and thus cannot throw) mid-mutation.
    void reserve_rest(size_t n) {
        rest.reserve(rest.size() + n);
    }

    void put(PyObject *o) {
        if (o == nullptr) {
            return;
        }
        if (slot0 == nullptr) {
            slot0 = o;
        }
        else if (slot1 == nullptr) {
            slot1 = o;
        }
        else {
            rest.push_back(o);
        }
    }

    void drain() noexcept {
        PyObject *a = slot0;
        slot0 = nullptr;
        PyObject *b = slot1;
        slot1 = nullptr;
        Py_XDECREF(a);
        Py_XDECREF(b);
        while (!rest.empty()) {
            PyObject *o = rest.back();
            rest.pop_back();
            Py_DECREF(o);
        }
    }
};


//
// Numeric boxing / unboxing
//


// idx is a borrowed PyLong that failed PyLong_AsUnsignedLongLong with OverflowError (negative, or > UINT64_MAX).
inline bool unbox_uint64_overflow(PyObject *idx, Ovf ovf, uint64_t *out) {
    switch (ovf) {
        case Ovf::RAISE:
            PyErr_SetString(PyExc_OverflowError, "int out of range for uint64");
            return false;

        case Ovf::CLAMP: {
            int of = 0;
            long long sv = PyLong_AsLongLongAndOverflow(idx, &of);
            if (sv == -1 && of == 0 && PyErr_Occurred()) {
                return false;
            }
            // AsUnsignedLongLong overflowed, so of == 0 here implies sv < 0.
            *out = of > 0 ? UINT64_MAX : 0;
            return true;
        }

        case Ovf::WRAP: {
            unsigned long long u = PyLong_AsUnsignedLongLongMask(idx);
            if (u == (unsigned long long)-1 && PyErr_Occurred()) {
                return false;
            }
            *out = (uint64_t)u;
            return true;
        }
    }
    Py_UNREACHABLE();
}


inline bool unbox_uint64(PyObject *o, Ovf ovf, uint64_t *out) {
    if (PyLong_CheckExact(o)) {
        // Fast path, as in unbox_int64: an exact int cannot fail conversion except by overflow.
        unsigned long long v = PyLong_AsUnsignedLongLong(o);
        if (v != (unsigned long long)-1 || !PyErr_Occurred()) {
            *out = (uint64_t)v;
            return true;
        }
        if (!PyErr_ExceptionMatches(PyExc_OverflowError)) {
            return false;
        }
        PyErr_Clear();
        return unbox_uint64_overflow(o, ovf, out);
    }

    PyObject *idx = PyNumber_Index(o);
    if (idx == nullptr) {
        return false;
    }

    unsigned long long v = PyLong_AsUnsignedLongLong(idx);
    if (v != (unsigned long long)-1 || !PyErr_Occurred()) {
        Py_DECREF(idx);
        *out = (uint64_t)v;
        return true;
    }

    if (!PyErr_ExceptionMatches(PyExc_OverflowError)) {
        Py_DECREF(idx);
        return false;
    }
    PyErr_Clear();

    bool r = unbox_uint64_overflow(idx, ovf, out);
    Py_DECREF(idx);
    return r;
}


// idx is a borrowed PyLong that overflowed int64 in the direction of `of`.
inline bool unbox_int64_overflow(PyObject *idx, int of, Ovf ovf, int64_t *out) {
    switch (ovf) {
        case Ovf::RAISE:
            PyErr_SetString(PyExc_OverflowError, "int out of range for int64");
            return false;

        case Ovf::CLAMP:
            *out = of > 0 ? INT64_MAX : INT64_MIN;
            return true;

        case Ovf::WRAP: {
            unsigned long long u = PyLong_AsUnsignedLongLongMask(idx);
            if (u == (unsigned long long)-1 && PyErr_Occurred()) {
                return false;
            }
            *out = (int64_t)u;
            return true;
        }
    }
    Py_UNREACHABLE();
}


inline bool unbox_int64(PyObject *o, Ovf ovf, int64_t *out) {
    if (PyLong_CheckExact(o)) {
        // Fast path: PyNumber_Index on an exact int is just an incref, so skip the call and the ref traffic. An
        // exact int cannot fail conversion except by overflow.
        int of = 0;
        long long v = PyLong_AsLongLongAndOverflow(o, &of);
        if (of == 0) {
            *out = (int64_t)v;
            return true;
        }
        return unbox_int64_overflow(o, of, ovf, out);
    }

    PyObject *idx = PyNumber_Index(o);
    if (idx == nullptr) {
        return false;
    }

    int of = 0;
    long long v = PyLong_AsLongLongAndOverflow(idx, &of);
    if (v == -1 && of == 0 && PyErr_Occurred()) {
        Py_DECREF(idx);
        return false;
    }

    if (of == 0) {
        Py_DECREF(idx);
        *out = (int64_t)v;
        return true;
    }

    bool r = unbox_int64_overflow(idx, of, ovf, out);
    Py_DECREF(idx);
    return r;
}


// Narrowing signed-integer unbox for the int32 / int16 dtypes, layered on the int64 machinery - the Ovf semantics
// compose: a 64-bit clamp followed by a width clamp is the width clamp; the 64-bit mask followed by truncation is
// exactly mod-2^width wrap (C++20 defines signed narrowing as modular); raise runs a 64-bit clamp first, since any
// clamped (huge) value necessarily fails the width range check below, keeping the error message width-correct.
template <typename I>
inline bool unbox_int_narrow(PyObject *o, Ovf ovf, I *out) {
    static_assert(std::is_signed_v<I> && sizeof(I) < 8);
    constexpr int64_t min = std::numeric_limits<I>::min();
    constexpr int64_t max = std::numeric_limits<I>::max();

    int64_t v;
    switch (ovf) {
        case Ovf::RAISE:
            if (!unbox_int64(o, Ovf::CLAMP, &v)) {
                return false;
            }
            if (v < min || v > max) {
                PyErr_SetString(
                    PyExc_OverflowError,
                    sizeof(I) == 4 ? "int out of range for int32" : "int out of range for int16");
                return false;
            }
            *out = (I)v;
            return true;

        case Ovf::CLAMP:
            if (!unbox_int64(o, Ovf::CLAMP, &v)) {
                return false;
            }
            *out = v < min ? (I)min : v > max ? (I)max : (I)v;
            return true;

        case Ovf::WRAP:
            if (!unbox_int64(o, Ovf::WRAP, &v)) {
                return false;
            }
            *out = (I)v;
            return true;
    }
    Py_UNREACHABLE();
}


inline bool unbox_float64(PyObject *o, double *out) {
    double v = PyFloat_AsDouble(o);
    if (v == -1.0 && PyErr_Occurred()) {
        return false;
    }
    *out = v;
    return true;
}


inline bool unbox_float32(PyObject *o, float *out) {
    double v;
    if (!unbox_float64(o, &v)) {
        return false;
    }
    // IEEE double->float conversion: rounds to nearest, out-of-range finite values become +/-inf - the same
    // narrowing semantics as numpy's float32. (Formally implementation-defined in C++, IEEE on every target.)
    *out = (float)v;
    return true;
}


inline size_t mix64(uint64_t x) noexcept {
    x ^= x >> 33;
    x *= UINT64_C(0xff51afd7ed558ccd);
    x ^= x >> 33;
    x *= UINT64_C(0xc4ceb9fe1a85ec53);
    x ^= x >> 33;
    return (size_t)x;
}


// Canonical bit pattern for hashing: all NaNs collapse to one pattern, and -0.0 collapses to +0.0, keeping hashing
// consistent with the nan-aware / ieee equality used by the float64 key predicates below.
inline uint64_t float64_key_bits(double v) noexcept {
    if (std::isnan(v)) {
        return UINT64_C(0x7ff8000000000000);
    }
    if (v == 0.0) {
        v = 0.0;
    }
    uint64_t b;
    std::memcpy(&b, &v, sizeof(b));
    return b;
}


//
// Canonical primitive forms
//
// Every primitive dtype maps into an unsigned integer of its storage width whose unsigned ordering and bitwise
// equality reproduce the dtype's ordering and value-equality exactly:
//
//  - unsigned ints: identity.
//  - signed ints: sign bit flipped - two's-complement order becomes unsigned order.
//  - floats: canonicalized (single NaN pattern, -0.0 -> +0.0) then the IEEE order-map - negative values are
//    bit-complemented, non-negative values get the sign bit set. The resulting total order preserves the
//    NaN-greatest / NaN-equivalent convention, +/-0.0 share one key, and bitwise equality is exactly the NaN-aware
//    value equality (`x = nan; x in c` succeeds, separately-created NaNs collapse - which unboxed storage cannot
//    distinguish anyway).
//
// This is what lets every primitive dtype of a given width share one container instantiation per container kind
// (see the storage-class traits below) with inner loops that are bare unsigned compares - for floats actually
// cheaper than native comparisons. The runtime dtype decides only how slots convert at the Python boundary.
//


inline uint64_t canon_from_i64(int64_t v) noexcept {
    return (uint64_t)v ^ (UINT64_C(1) << 63);
}


inline int64_t canon_to_i64(uint64_t c) noexcept {
    return (int64_t)(c ^ (UINT64_C(1) << 63));
}


inline uint64_t canon_from_f64(double v) noexcept {
    uint64_t b = float64_key_bits(v);
    return (b >> 63) ? ~b : (b | (UINT64_C(1) << 63));
}


inline double canon_to_f64(uint64_t c) noexcept {
    uint64_t b = (c >> 63) ? (c ^ (UINT64_C(1) << 63)) : ~c;
    double v;
    std::memcpy(&v, &b, sizeof(v));
    return v;
}


// float32 analog of float64_key_bits: all NaNs collapse to one pattern, -0.0f collapses to +0.0f.
inline uint32_t float32_key_bits(float v) noexcept {
    if (std::isnan(v)) {
        return UINT32_C(0x7fc00000);
    }
    if (v == 0.0f) {
        v = 0.0f;
    }
    uint32_t b;
    std::memcpy(&b, &v, sizeof(b));
    return b;
}


inline uint32_t canon_from_i32(int32_t v) noexcept {
    return (uint32_t)v ^ (UINT32_C(1) << 31);
}


inline int32_t canon_to_i32(uint32_t c) noexcept {
    return (int32_t)(c ^ (UINT32_C(1) << 31));
}


inline uint32_t canon_from_f32(float v) noexcept {
    uint32_t b = float32_key_bits(v);
    return (b >> 31) ? ~b : (b | (UINT32_C(1) << 31));
}


inline float canon_to_f32(uint32_t c) noexcept {
    uint32_t b = (c >> 31) ? (c ^ (UINT32_C(1) << 31)) : ~c;
    float v;
    std::memcpy(&v, &b, sizeof(v));
    return v;
}


inline uint16_t canon_from_i16(int16_t v) noexcept {
    return (uint16_t)((uint16_t)v ^ (uint16_t)0x8000);
}


inline int16_t canon_to_i16(uint16_t c) noexcept {
    return (int16_t)(c ^ (uint16_t)0x8000);
}


//
// Dtype traits
//
// One traits struct per storage CLASS, not per dtype: all primitive dtypes of a width share the canonical-form
// traits for that width, and the runtime dtype (carried by the impl and passed to unbox / box) matters only at the
// Python boundary. The comparison / hash / equality functors are dtype-blind bare unsigned operations, so shared
// instantiations lose nothing in the inner loops. Slot is the in-container representation; unbox produces a
// *borrowed* Slot (no reference is taken for object dtypes), and ownership is only taken via retain() at the moment
// a slot is actually stored. release_into() moves a stored slot's owned reference into a Bin for deferred decref.
// Comparator / hash / equality functors may throw py_err_set for object dtypes.
//


struct Canon64Traits {
    using Slot = uint64_t;
    static constexpr bool IS_OBJ = false;

    struct Less {
        bool operator()(Slot a, Slot b) const noexcept { return a < b; }
    };

    struct Hash {
        size_t operator()(Slot v) const noexcept { return mix64(v); }
    };

    struct Eq {
        bool operator()(Slot a, Slot b) const noexcept { return a == b; }
    };

    static bool unbox(PyObject *o, Dt dt, Ovf ovf, Slot *out) {
        switch (dt) {
            case Dt::U64: {
                uint64_t v;
                if (!unbox_uint64(o, ovf, &v)) {
                    return false;
                }
                *out = v;
                return true;
            }
            case Dt::I64: {
                int64_t v;
                if (!unbox_int64(o, ovf, &v)) {
                    return false;
                }
                *out = canon_from_i64(v);
                return true;
            }
            case Dt::F64: {
                double v;
                if (!unbox_float64(o, &v)) {
                    return false;
                }
                *out = canon_from_f64(v);
                return true;
            }
            case Dt::I32:
            case Dt::I16:
            case Dt::F32:
            case Dt::OBJ:
                break;  // not 64-bit-storage dtypes; excluded by the impl factories
        }
        Py_UNREACHABLE();
    }

    static PyObject *box(Dt dt, const Slot &v) {
        switch (dt) {
            case Dt::U64:
                return PyLong_FromUnsignedLongLong((unsigned long long)v);
            case Dt::I64:
                return PyLong_FromLongLong((long long)canon_to_i64(v));
            case Dt::F64:
                return PyFloat_FromDouble(canon_to_f64(v));
            case Dt::I32:
            case Dt::I16:
            case Dt::F32:
            case Dt::OBJ:
                break;
        }
        Py_UNREACHABLE();
    }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }

    // Bitwise equality on canonical form is each dtype's value equality (see the canonical-form comment).
    static bool val_eq(const Slot &a, const Slot &b) { return a == b; }
};


struct Canon32Traits {
    using Slot = uint32_t;
    static constexpr bool IS_OBJ = false;

    struct Less {
        bool operator()(Slot a, Slot b) const noexcept { return a < b; }
    };

    struct Hash {
        size_t operator()(Slot v) const noexcept { return mix64((uint64_t)v); }
    };

    struct Eq {
        bool operator()(Slot a, Slot b) const noexcept { return a == b; }
    };

    static bool unbox(PyObject *o, Dt dt, Ovf ovf, Slot *out) {
        switch (dt) {
            case Dt::I32: {
                int32_t v;
                if (!unbox_int_narrow<int32_t>(o, ovf, &v)) {
                    return false;
                }
                *out = canon_from_i32(v);
                return true;
            }
            case Dt::F32: {
                float v;
                if (!unbox_float32(o, &v)) {
                    return false;
                }
                *out = canon_from_f32(v);
                return true;
            }
            case Dt::U64:
            case Dt::I64:
            case Dt::I16:
            case Dt::F64:
            case Dt::OBJ:
                break;  // not 32-bit-storage dtypes; excluded by the impl factories
        }
        Py_UNREACHABLE();
    }

    static PyObject *box(Dt dt, const Slot &v) {
        switch (dt) {
            case Dt::I32:
                return PyLong_FromLong((long)canon_to_i32(v));
            case Dt::F32:
                return PyFloat_FromDouble((double)canon_to_f32(v));
            case Dt::U64:
            case Dt::I64:
            case Dt::I16:
            case Dt::F64:
            case Dt::OBJ:
                break;
        }
        Py_UNREACHABLE();
    }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }

    static bool val_eq(const Slot &a, const Slot &b) { return a == b; }
};


struct Canon16Traits {
    using Slot = uint16_t;
    static constexpr bool IS_OBJ = false;

    struct Less {
        bool operator()(Slot a, Slot b) const noexcept { return a < b; }
    };

    struct Hash {
        size_t operator()(Slot v) const noexcept { return mix64((uint64_t)v); }
    };

    struct Eq {
        bool operator()(Slot a, Slot b) const noexcept { return a == b; }
    };

    static bool unbox(PyObject *o, Dt dt, Ovf ovf, Slot *out) {
        switch (dt) {
            case Dt::I16: {
                int16_t v;
                if (!unbox_int_narrow<int16_t>(o, ovf, &v)) {
                    return false;
                }
                *out = canon_from_i16(v);
                return true;
            }
            case Dt::U64:
            case Dt::I64:
            case Dt::I32:
            case Dt::F64:
            case Dt::F32:
            case Dt::OBJ:
                break;  // not 16-bit-storage dtypes; excluded by the impl factories
        }
        Py_UNREACHABLE();
    }

    static PyObject *box(Dt dt, const Slot &v) {
        switch (dt) {
            case Dt::I16:
                return PyLong_FromLong((long)canon_to_i16(v));
            case Dt::U64:
            case Dt::I64:
            case Dt::I32:
            case Dt::F64:
            case Dt::F32:
            case Dt::OBJ:
                break;
        }
        Py_UNREACHABLE();
    }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }

    static bool val_eq(const Slot &a, const Slot &b) { return a == b; }
};


struct ObjectTraits {
    using Slot = PyObject *;
    static constexpr bool IS_OBJ = true;

    struct Less {
        bool operator()(PyObject *a, PyObject *b) const {
            int r = PyObject_RichCompareBool(a, b, Py_LT);
            if (r < 0) {
                throw py_err_set();
            }
            return r != 0;
        }
    };

    struct Eq {
        bool operator()(PyObject *a, PyObject *b) const {
            int r = PyObject_RichCompareBool(a, b, Py_EQ);
            if (r < 0) {
                throw py_err_set();
            }
            return r != 0;
        }
    };

    struct Hash {
        size_t operator()(PyObject *) const noexcept { return 0; }  // unused; hashed objects use HashedObjectTraits
    };

    static bool unbox(PyObject *o, Dt, Ovf, Slot *out) {
        *out = o;  // borrowed
        return true;
    }

    static PyObject *box(Dt, const Slot &v) { return Py_NewRef(v); }

    static void retain(const Slot &v) noexcept { Py_INCREF(v); }
    static void release_into(const Slot &v, Bin &bin) { bin.put(v); }

    static int visit_slot(const Slot &v, visitproc visit, void *arg) noexcept {
        Py_VISIT(v);
        return 0;
    }

    static bool val_eq(const Slot &a, const Slot &b) {
        int r = PyObject_RichCompareBool(a, b, Py_EQ);
        if (r < 0) {
            throw py_err_set();
        }
        return r != 0;
    }
};


// Hashed-object slots cache the hash so that rehashing never calls back into Python: the noexcept Hash functor below
// just reads the cached value, and Eq only rich-compares when the cached hashes already agree.
struct HObj {
    Py_hash_t hash;
    PyObject *obj;
};


struct HashedObjectTraits {
    using Slot = HObj;
    static constexpr bool IS_OBJ = true;

    struct Less {
        bool operator()(const HObj &, const HObj &) const noexcept { return false; }  // unused
    };

    struct Hash {
        size_t operator()(const HObj &k) const noexcept { return (size_t)k.hash; }
    };

    struct Eq {
        bool operator()(const HObj &a, const HObj &b) const {
            if (a.obj == b.obj) {
                return true;
            }
            if (a.hash != b.hash) {
                return false;
            }
            int r = PyObject_RichCompareBool(a.obj, b.obj, Py_EQ);
            if (r < 0) {
                throw py_err_set();
            }
            return r != 0;
        }
    };

    static bool unbox(PyObject *o, Dt, Ovf, Slot *out) {
        Py_hash_t h = PyObject_Hash(o);
        if (h == -1) {
            return false;
        }
        *out = HObj{h, o};  // borrowed
        return true;
    }

    static PyObject *box(Dt, const Slot &v) { return Py_NewRef(v.obj); }

    static void retain(const Slot &v) noexcept { Py_INCREF(v.obj); }
    static void release_into(const Slot &v, Bin &bin) { bin.put(v.obj); }

    static int visit_slot(const Slot &v, visitproc visit, void *arg) noexcept {
        Py_VISIT(v.obj);
        return 0;
    }

    static bool val_eq(const Slot &a, const Slot &b) {
        return Eq()(a, b);
    }
};


//
// tlx btree traits
//
// The sorted containers are (vendored) tlx B+ trees rather than std::map / std::set: an order of magnitude better
// node density than one heap-allocated red-black node per element, and cache-linear leaf-chain iteration. Primitive
// dtypes keep tlx's default in-node linear search - the cache-friendly choice when a comparison is one instruction.
// Object dtypes force binary search (binsearch_threshold = 0): every comparison there is a Python richcompare call,
// so call count dominates any cache effect.
//
// Two tlx behaviors the sorted impls must respect (see the erase reordering comments in set.hh / map.hh):
//  - btree iterators are invalidated by EVERY insert / erase (slots shift within leaves, end() captures the tail
//    leaf), not just by erasure of the pointed-to element as with std::map - the iterator version-check discipline
//    is what makes the stored iterators safe, and is load-bearing.
//  - erase(iterator) re-descends by key, so for object dtypes it runs comparators and can throw py_err_set; unlike
//    std::map's erase(iterator) it must be treated as fallible.
//


template <typename Key, typename Value>
struct ObjBtreeTraits : tlx::btree_default_traits<Key, Value> {
    static const size_t binsearch_threshold = 0;
};


template <typename K, typename Value>
using BtreeTraitsFor = std::conditional_t<
    K::IS_OBJ,
    ObjBtreeTraits<typename K::Slot, Value>,
    tlx::btree_default_traits<typename K::Slot, Value>>;


// Probe unboxing, used by non-mutating lookups (contains / getitem / discard / find / ...): for primitive dtypes a
// value that cannot be represented in the container's dtype at all is simply treated as absent - mirroring how a dict
// lookup of a never-insertable key just misses - so only representation errors (TypeError, OverflowError in raise
// mode) are swallowed. Object dtypes propagate everything (an unhashable probe raises, exactly as with dict / set).
//
// Callers brace-initialize their Slot locals (`Slot s{};`) even though every read is dominated by a success check on
// the returned status: gcc's late -Wmaybe-uninitialized pass (at -O3, after inlining and jump threading) loses the
// correlation between the status and the store to *out and emits false positives otherwise. The zero-init is a single
// dead store the optimizer routinely deletes, and makes any future unguarded read deterministic rather than garbage.
template <typename Tr>
int unbox_probe(PyObject *o, Dt dt, Ovf ovf, typename Tr::Slot *out) {
    if (Tr::unbox(o, dt, ovf, out)) {
        return 1;
    }
    if constexpr (!Tr::IS_OBJ) {
        if (PyErr_ExceptionMatches(PyExc_TypeError) || PyErr_ExceptionMatches(PyExc_OverflowError)) {
            PyErr_Clear();
            return 0;
        }
    }
    return -1;
}


//
// Impl interfaces
//
// Runtime dtype dispatch happens exactly once per operation, through the virtual calls below; everything underneath is
// a fully type-specialized template instantiation. Interface methods use the CPython-ish status convention noted per
// method; on -1 the Python error indicator is set. Methods may additionally throw py_err_set (comparator errors) or
// std::bad_alloc; entry points translate via py_shield.
//


// What an iterator yields; direction is an orthogonal flag on make_iter / make_iter_from ("desc"), so kinds compose
// with both directions (e.g. reversed keys for __reversed__, descending items for items_desc).
enum class IterKind : uint8_t {
    KEYS,
    VALUES,
    ITEMS,
};


struct AnyIter {
    virtual ~AnyIter() = default;

    // PyMem-domain allocation - see the allocator comment above; inherited by every concrete iterator.
    static void *operator new(size_t n) {
        void *p = PyMem_Malloc(n);
        if (p == nullptr) {
            throw std::bad_alloc();
        }
        return p;
    }

    static void operator delete(void *p) noexcept {
        PyMem_Free(p);
    }

    // 1 = item produced (new ref in *out), 0 = exhausted, -1 = error.
    virtual int next(PyObject **out) = 0;
};


struct AnyImpl {
    // Locking state - see the locking discipline comment below. Guarded by the Python layer, not by impl methods.
    std::mutex mutex;
    std::atomic<unsigned long> lock_owner{0};

    // Bumped on any insert / erase / reorder (not on value overwrite); sorted / hashed iterators snapshot it and fail
    // with RuntimeError on mismatch, dict-style.
    uint64_t version = 0;

    const ColKind kind;
    const Dt key_dt;
    const Ovf key_ovf;
    const Dt val_dt;
    const Ovf val_ovf;

    AnyImpl(ColKind k, Dt kd, Ovf ko, Dt vd, Ovf vo)
        : kind(k), key_dt(kd), key_ovf(ko), val_dt(vd), val_ovf(vo) {}

    virtual ~AnyImpl() = default;

    // PyMem-domain allocation - see the allocator comment above; inherited by every concrete impl.
    static void *operator new(size_t n) {
        void *p = PyMem_Malloc(n);
        if (p == nullptr) {
            throw std::bad_alloc();
        }
        return p;
    }

    static void operator delete(void *p) noexcept {
        PyMem_Free(p);
    }

    virtual Py_ssize_t size() const noexcept = 0;
    virtual int traverse(visitproc visit, void *arg) noexcept = 0;

    // Moves every owned reference into bin and empties the structure.
    virtual void clear_collect(Bin &bin) = 0;

    // Best-effort presizing ahead of a bulk insert of up to n additional elements; hashed impls override to grow
    // their bucket arrays once up front instead of rehashing incrementally. May throw bad_alloc, so callers must
    // invoke it before any mutation.
    virtual void reserve_extra(size_t) {}

    virtual AnyImpl *clone() const = 0;
    virtual AnyIter *make_iter(IterKind ik, bool desc) = 0;

    // Iteration seeded at a key bound, for the sorted interfaces: ascending starts at lower_bound(base) (first element
    // >= base), descending starts walking down from upper_bound(base) (so the first element yielded is the greatest <=
    // base) - the exact bisect_left / bisect_right semantics. The bound is unboxed strictly (same acceptance as an
    // insert would have), and only the sorted impls override this.
    virtual AnyIter *make_iter_from(IterKind, bool, PyObject *) {
        PyErr_SetString(PyExc_TypeError, "container does not support ordered iteration");
        return nullptr;
    }

    // Typed fast paths; preconditions: other has the same kind / key_dt / val_dt (overflow mode may differ).
    virtual int equals_same(AnyImpl *other) = 0;            // 1 / 0 / -1
    virtual int merge_same(AnyImpl *other, Bin &bin) = 0;   // 0 / -1

    bool same_shape(const AnyImpl *other) const noexcept {
        return kind == other->kind && key_dt == other->key_dt && val_dt == other->val_dt;
    }
};


//
// Locking discipline
//
// A single per-container std::mutex serializes all structural access, on GIL and free-threaded builds alike:
//
//  - The mutex is acquired only via col_lock_acquire, which detaches the thread state (Py_BEGIN_ALLOW_THREADS) around
//    a blocking acquire. On GIL builds this means no thread ever blocks on the mutex while holding the GIL - so the
//    mutex holder can always reacquire the GIL and make progress - and on free-threaded builds a blocked thread is
//    detached and cannot stall a stop-the-world GC.
//
//  - Operations on object-dtype containers call back into arbitrary Python (__lt__ / __eq__ / __hash__ / __index__,
//    and any allocation can trigger GC finalizers) *while holding the lock* - comparison-driven tree and hash
//    operations cannot be run any other way. The classic cross-thread lock-order deadlock is excluded by the acquire
//    protocol above; same-thread reentrancy (user comparison or finalizer code calling back into the same container)
//    is detected via lock_owner and refused with RuntimeError rather than deadlocking.
//    Note the exclusion covers only the locks the guards themselves take: user code running under one (or, in the
//    typed two-container fast paths, two) container locks can still operate on *other* containers, and two threads
//    doing that in inverted roles can deadlock through the user code's lock edges. That hazard is accepted as
//    inherent - plain per-container mutexes, unlike CPython's free-threaded critical sections, cannot be suspended
//    while their holder blocks.
//
//  - Displaced references are never DECREFed under the lock - they go through a Bin (declared before the guard, see
//    above) and are drained after release.
//
//  - tp_traverse deliberately takes no lock: free-threaded GC is stop-the-world, and a suspended thread could hold
//    the mutex forever. Threads only suspend at safe points inside Python code - i.e. inside the user-code callbacks
//    above, during which the STL structures are never mid-mutation - so an unlocked traversal only ever observes a
//    consistent structure. tp_clear also runs unlocked: it only ever runs on objects GC has proven unreachable, which
//    no thread can concurrently be operating on.
//


inline bool col_lock_acquire(AnyImpl *impl) {
    unsigned long tid = PyThread_get_thread_ident();

    if (impl->lock_owner.load(std::memory_order_relaxed) == tid) {
        PyErr_SetString(PyExc_RuntimeError, "reentrant operation on " _MODULE_NAME " container");
        return false;
    }

    if (!impl->mutex.try_lock()) {
        Py_BEGIN_ALLOW_THREADS
        impl->mutex.lock();
        Py_END_ALLOW_THREADS
    }

    impl->lock_owner.store(tid, std::memory_order_relaxed);
    return true;
}


inline void col_lock_release(AnyImpl *impl) noexcept {
    impl->lock_owner.store(0, std::memory_order_relaxed);
    impl->mutex.unlock();
}


class ColGuard {
public:
    explicit ColGuard(AnyImpl *impl) {
        if (col_lock_acquire(impl)) {
            impl_ = impl;
        }
    }

    ColGuard(const ColGuard &) = delete;
    ColGuard &operator=(const ColGuard &) = delete;

    ~ColGuard() {
        release();
    }

    void release() noexcept {
        if (impl_ != nullptr) {
            col_lock_release(impl_);
            impl_ = nullptr;
        }
    }

    bool held() const noexcept {
        return impl_ != nullptr;
    }

private:
    AnyImpl *impl_ = nullptr;
};


// Address-ordered two-container guard, for the typed same-shape fast paths (merge / equals / etc.). Address ordering
// excludes lock-order inversion between two containers being operated on concurrently in opposite roles.
class ColGuard2 {
public:
    ColGuard2(AnyImpl *x, AnyImpl *y) {
        AnyImpl *lo = x;
        AnyImpl *hi = x == y ? nullptr : y;
        if (hi != nullptr && hi < lo) {
            AnyImpl *t = lo;
            lo = hi;
            hi = t;
        }

        if (!col_lock_acquire(lo)) {
            return;
        }
        if (hi != nullptr && !col_lock_acquire(hi)) {
            col_lock_release(lo);
            return;
        }

        lo_ = lo;
        hi_ = hi;
    }

    ColGuard2(const ColGuard2 &) = delete;
    ColGuard2 &operator=(const ColGuard2 &) = delete;

    ~ColGuard2() {
        if (hi_ != nullptr) {
            col_lock_release(hi_);
        }
        if (lo_ != nullptr) {
            col_lock_release(lo_);
        }
    }

    bool held() const noexcept {
        return lo_ != nullptr;
    }

private:
    AnyImpl *lo_ = nullptr;
    AnyImpl *hi_ = nullptr;
};


//
// Container / iterator objects
//


struct ColObject {
    PyObject_HEAD
    AnyImpl *impl;
};


struct IterObject {
    PyObject_HEAD
    PyObject *owner;  // strong reference to the ColObject; keeps impl alive while the iterator lives
    AnyIter *it;
};


inline int col_ready(ColObject *co) {
    if (co->impl == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "container is not initialized");
        return 0;
    }
    return 1;
}


// Publishes a freshly-constructed impl into co->impl iff it is still null, taking ownership either way. tp_init has
// no lock to take (the impl IS the lock), so two threads can race the first __init__ of a shared uninitialized
// object; the CAS lets exactly one publish, and the loser's impl is deleted and the usual re-init error raised.
inline int col_publish_impl(ColObject *co, AnyImpl *impl) {
    AnyImpl *expected = nullptr;
    if (!std::atomic_ref<AnyImpl *>(co->impl).compare_exchange_strong(expected, impl)) {
        delete impl;
        PyErr_SetString(PyExc_TypeError, "container is already initialized");
        return -1;
    }
    return 0;
}


// KeyError's args must be the key itself, wrapped in a 1-tuple so that tuple keys don't splat.
inline void raise_key_error(PyObject *k) {
    PyObject *t = PyTuple_Pack(1, k);
    if (t == nullptr) {
        return;
    }
    PyErr_SetObject(PyExc_KeyError, t);
    Py_DECREF(t);
}


// Takes ownership of impl (deleting it on allocation failure).
inline PyObject *col_wrap(PyTypeObject *tp, AnyImpl *impl) {
    ColObject *co = (ColObject *)tp->tp_alloc(tp, 0);
    if (co == nullptr) {
        delete impl;
        return nullptr;
    }
    co->impl = impl;
    return (PyObject *)co;
}


inline void col_dealloc(PyObject *self) {
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    ColObject *co = (ColObject *)self;
    AnyImpl *impl = co->impl;
    co->impl = nullptr;
    // No lock and no bin: the object is unreachable, so nothing else can hold the lock, and the impl destructor's
    // direct DECREFs may run arbitrary __del__ code safely here.
    delete impl;
    tp->tp_free(self);
    Py_DECREF((PyObject *)tp);
}


inline int col_traverse(PyObject *self, visitproc visit, void *arg) {
    Py_VISIT(Py_TYPE(self));
    ColObject *co = (ColObject *)self;
    if (co->impl != nullptr) {
        // Deliberately unlocked - see the locking discipline comment.
        int r = co->impl->traverse(visit, arg);
        if (r != 0) {
            return r;
        }
    }
    return 0;
}


inline int col_clear_slot(PyObject *self) {
    ColObject *co = (ColObject *)self;
    if (co->impl != nullptr) {
        // Unlocked by design - tp_clear only runs on objects GC has proven unreachable.
        try {
            Bin bin;
            co->impl->clear_collect(bin);
        }
        catch (...) {
            // Only a bin allocation failure lands here; leaving the elements in place is safe.
        }
    }
    return 0;
}


inline Py_ssize_t col_len(PyObject *self) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return co->impl->size();
}


inline PyObject *col_clear_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        int r = py_shield_int([&] {
            co->impl->clear_collect(bin);
            return 0;
        });
        if (r < 0) {
            return nullptr;
        }
    }
    Py_RETURN_NONE;
}


// Clones under the lock and wraps the clone in the given (plain, module-owned) type.
inline PyObject *col_copy_as(PyTypeObject *tp, ColObject *co) {
    AnyImpl *n = nullptr;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        try {
            n = co->impl->clone();
        }
        catch (std::bad_alloc &) {
            g.release();
            PyErr_NoMemory();
            return nullptr;
        }
    }
    return col_wrap(tp, n);
}


//
// Iterator type
//


inline void iter_dealloc(PyObject *self) {
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    IterObject *io = (IterObject *)self;
    AnyIter *it = io->it;
    io->it = nullptr;
    delete it;
    Py_CLEAR(io->owner);
    tp->tp_free(self);
    Py_DECREF((PyObject *)tp);
}


inline int iter_traverse(PyObject *self, visitproc visit, void *arg) {
    Py_VISIT(Py_TYPE(self));
    IterObject *io = (IterObject *)self;
    Py_VISIT(io->owner);
    return 0;
}


inline int iter_clear(PyObject *self) {
    IterObject *io = (IterObject *)self;
    // The AnyIter points into the owner's impl, so it must die before the owner reference does.
    AnyIter *it = io->it;
    io->it = nullptr;
    delete it;
    Py_CLEAR(io->owner);
    return 0;
}


inline PyObject *iter_next(PyObject *self) {
    IterObject *io = (IterObject *)self;
    if (io->owner == nullptr || io->it == nullptr) {
        return nullptr;  // exhausted / cleared - bare null means StopIteration
    }
    ColObject *co = (ColObject *)io->owner;
    ColGuard g(co->impl);
    if (!g.held()) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r = py_shield_int([&] { return io->it->next(&out); });
    g.release();
    if (r <= 0) {
        return nullptr;
    }
    return out;
}


inline PyObject *col_make_iter(PyObject *self, IterKind ik, bool desc) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    AnyIter *it = nullptr;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        try {
            it = co->impl->make_iter(ik, desc);
        }
        catch (std::bad_alloc &) {
            g.release();
            PyErr_NoMemory();
            return nullptr;
        }
    }
    IterObject *io = (IterObject *)st->iter_type->tp_alloc(st->iter_type, 0);
    if (io == nullptr) {
        delete it;
        return nullptr;
    }
    io->owner = Py_NewRef(self);
    io->it = it;
    return (PyObject *)io;
}


inline PyObject *col_iter(PyObject *self) {
    return col_make_iter(self, IterKind::KEYS, false);
}


inline PyObject *col_iter_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::KEYS, false);
}


inline PyObject *col_reversed_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::KEYS, true);
}


// Backs iter_from / iter_from_desc / items_from / items_from_desc: seeks under the container lock (object-dtype
// bounds run user comparators there, hence the py_err_set catch) and hands the seeded impl iterator to the shared
// iterator object, which re-locks per next() and version-checks like any other iterator.
inline PyObject *col_make_iter_from(PyObject *self, IterKind ik, bool desc, PyObject *base) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    AnyIter *it = nullptr;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        try {
            it = co->impl->make_iter_from(ik, desc, base);
        }
        catch (py_err_set &) {
            g.release();
            return nullptr;
        }
        catch (std::bad_alloc &) {
            g.release();
            PyErr_NoMemory();
            return nullptr;
        }
        if (it == nullptr) {
            g.release();
            return nullptr;
        }
    }
    IterObject *io = (IterObject *)st->iter_type->tp_alloc(st->iter_type, 0);
    if (io == nullptr) {
        delete it;
        return nullptr;
    }
    io->owner = Py_NewRef(self);
    io->it = it;
    return (PyObject *)io;
}


// The state element for __reduce__ tuples: a non-empty instance __dict__ (Python subclasses carrying attributes)
// rides along and is applied by pickle via __dict__.update; base instances have no __dict__ at all and get None.
inline PyObject *col_reduce_state(PyObject *self) {
    PyObject *d = nullptr;
    if (PyObject_GetOptionalAttrString(self, "__dict__", &d) < 0) {
        return nullptr;
    }
    if (d == nullptr) {
        Py_RETURN_NONE;
    }
    if (PyDict_Check(d) && PyDict_GET_SIZE(d) == 0) {
        Py_DECREF(d);
        Py_RETURN_NONE;
    }
    return d;
}


// Extracts the short class name ("Set") out of the heap type's qualified tp_name ("_stl.Set"), for reprs and
// error messages.
inline const char *col_short_name(PyObject *self) {
    const char *tn = Py_TYPE(self)->tp_name;
    const char *dot = std::strrchr(tn, '.');
    return dot != nullptr ? dot + 1 : tn;
}
