// @om-cext
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
#include <map>
#include <mutex>
#include <new>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <vector>


#define _MODULE_NAME "_stl"
#define _PACKAGE_NAME "omxtra.collections.stl"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME


// fastutil-style primitive-specialized containers: Set / UnorderedSet / Map / UnorderedMap / Vector, each parameterized
// (per key / value position) over one of the dtypes 'object', 'int64-{raise,clamp,wrap}', 'uint64-{raise,clamp,wrap}',
// or 'float64'. Primitive dtypes are stored unboxed (as int64_t / uint64_t / double) and box/unbox only at the Python
// boundary; 'object' stores owned PyObject* references and participates fully in GC. Each combination is a distinct
// C++ template instantiation, so the loops that drive lookups, bulk merges, comparisons, sorts, and slices are fully
// type-specialized - the only per-element indirection anywhere is the unavoidable one at the Python boundary itself.


static struct PyModuleDef *stl_module_def();


//
// Dtypes
//

enum class Dt : uint8_t {
    OBJ,
    I64,
    U64,
    F64,
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


static int parse_dtype(PyObject *o, DtypeSpec *out) {
    if (!PyUnicode_Check(o)) {
        PyErr_Format(PyExc_TypeError, "dtype must be a str, got %.100s", Py_TYPE(o)->tp_name);
        return -1;
    }

    const char *s = PyUnicode_AsUTF8(o);
    if (s == nullptr) {
        return -1;
    }

    static const struct {
        const char *name;
        Dt dt;
        Ovf ovf;
    } TABLE[] = {
        {"object", Dt::OBJ, Ovf::RAISE},
        {"int64", Dt::I64, Ovf::RAISE},
        {"int64-raise", Dt::I64, Ovf::RAISE},
        {"int64-clamp", Dt::I64, Ovf::CLAMP},
        {"int64-wrap", Dt::I64, Ovf::WRAP},
        {"uint64", Dt::U64, Ovf::RAISE},
        {"uint64-raise", Dt::U64, Ovf::RAISE},
        {"uint64-clamp", Dt::U64, Ovf::CLAMP},
        {"uint64-wrap", Dt::U64, Ovf::WRAP},
        {"float64", Dt::F64, Ovf::RAISE},
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


static const char *dtype_name(Dt dt, Ovf ovf) {
    switch (dt) {
        case Dt::OBJ:
            return "object";
        case Dt::F64:
            return "float64";
        case Dt::I64:
            switch (ovf) {
                case Ovf::RAISE: return "int64-raise";
                case Ovf::CLAMP: return "int64-clamp";
                default: return "int64-wrap";
            }
        default:
            switch (ovf) {
                case Ovf::RAISE: return "uint64-raise";
                case Ovf::CLAMP: return "uint64-clamp";
                default: return "uint64-wrap";
            }
    }
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
static PyObject *py_shield(F &&fn) noexcept {
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
static int py_shield_int(F &&fn) noexcept {
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
    std::vector<PyObject *> rest;

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

static bool unbox_int64(PyObject *o, Ovf ovf, int64_t *out) {
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

    switch (ovf) {
        case Ovf::RAISE:
            Py_DECREF(idx);
            PyErr_SetString(PyExc_OverflowError, "int out of range for int64");
            return false;

        case Ovf::CLAMP:
            Py_DECREF(idx);
            *out = of > 0 ? INT64_MAX : INT64_MIN;
            return true;

        default: {
            unsigned long long u = PyLong_AsUnsignedLongLongMask(idx);
            Py_DECREF(idx);
            if (u == (unsigned long long)-1 && PyErr_Occurred()) {
                return false;
            }
            *out = (int64_t)u;
            return true;
        }
    }
}


static bool unbox_uint64(PyObject *o, Ovf ovf, uint64_t *out) {
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

    switch (ovf) {
        case Ovf::RAISE:
            Py_DECREF(idx);
            PyErr_SetString(PyExc_OverflowError, "int out of range for uint64");
            return false;

        case Ovf::CLAMP: {
            int of = 0;
            long long sv = PyLong_AsLongLongAndOverflow(idx, &of);
            Py_DECREF(idx);
            if (sv == -1 && of == 0 && PyErr_Occurred()) {
                return false;
            }
            // AsUnsignedLongLong overflowed, so of == 0 here implies sv < 0.
            *out = of > 0 ? UINT64_MAX : 0;
            return true;
        }

        default: {
            unsigned long long u = PyLong_AsUnsignedLongLongMask(idx);
            Py_DECREF(idx);
            if (u == (unsigned long long)-1 && PyErr_Occurred()) {
                return false;
            }
            *out = (uint64_t)u;
            return true;
        }
    }
}


static bool unbox_float64(PyObject *o, double *out) {
    double v = PyFloat_AsDouble(o);
    if (v == -1.0 && PyErr_Occurred()) {
        return false;
    }
    *out = v;
    return true;
}


static inline size_t mix64(uint64_t x) noexcept {
    x ^= x >> 33;
    x *= UINT64_C(0xff51afd7ed558ccd);
    x ^= x >> 33;
    x *= UINT64_C(0xc4ceb9fe1a85ec53);
    x ^= x >> 33;
    return (size_t)x;
}


// Canonical bit pattern for hashing: all NaNs collapse to one pattern, and -0.0 collapses to +0.0, keeping hashing
// consistent with the nan-aware / ieee equality used by the float64 key predicates below.
static inline uint64_t float64_key_bits(double v) noexcept {
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
// Dtype traits
//
// One traits struct per storage representation. Slot is the unboxed in-container representation; unbox produces a
// *borrowed* Slot (no reference is taken for object dtypes), and ownership is only taken via retain() at the moment a
// slot is actually stored. release_into() moves a stored slot's owned reference into a Bin for deferred decref.
// Comparator / hash / equality functors may throw py_err_set for object dtypes.
//

struct Int64Traits {
    using Slot = int64_t;
    static constexpr Dt DT = Dt::I64;
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

    static bool unbox(PyObject *o, Ovf ovf, Slot *out) { return unbox_int64(o, ovf, out); }
    static PyObject *box(const Slot &v) { return PyLong_FromLongLong((long long)v); }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }
    static bool val_eq(const Slot &a, const Slot &b) { return a == b; }
};


struct UInt64Traits {
    using Slot = uint64_t;
    static constexpr Dt DT = Dt::U64;
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

    static bool unbox(PyObject *o, Ovf ovf, Slot *out) { return unbox_uint64(o, ovf, out); }
    static PyObject *box(const Slot &v) { return PyLong_FromUnsignedLongLong((unsigned long long)v); }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }
    static bool val_eq(const Slot &a, const Slot &b) { return a == b; }
};


struct Float64Traits {
    using Slot = double;
    static constexpr Dt DT = Dt::F64;
    static constexpr bool IS_OBJ = false;

    // Strict weak order with NaNs greater than (and equivalent to) everything else, so a NaN is a usable sorted key
    // rather than one that compares 'equivalent' to arbitrary keys under a plain operator<.
    struct Less {
        bool operator()(Slot a, Slot b) const noexcept {
            if (std::isnan(a)) {
                return false;
            }
            if (std::isnan(b)) {
                return true;
            }
            return a < b;
        }
    };

    struct Hash {
        size_t operator()(Slot v) const noexcept { return mix64(float64_key_bits(v)); }
    };

    // Key equality: nan == nan (one NaN key), and ieee == keeps 0.0 / -0.0 as the same key.
    struct Eq {
        bool operator()(Slot a, Slot b) const noexcept {
            return a == b || (std::isnan(a) && std::isnan(b));
        }
    };

    static bool unbox(PyObject *o, Ovf, Slot *out) { return unbox_float64(o, out); }
    static PyObject *box(const Slot &v) { return PyFloat_FromDouble(v); }

    static void retain(const Slot &) noexcept {}
    static void release_into(const Slot &, Bin &) noexcept {}
    static int visit_slot(const Slot &, visitproc, void *) noexcept { return 0; }

    // Value-position equality also treats NaN as equal to NaN: unboxing loses object identity, and the identity
    // shortcut is exactly how `x = nan; x in [x]` succeeds for builtin containers, so this recovers the common case
    // (`nan in Vector('float64', [nan])`, remove(), count(), map value comparison) at the cost of distinguishing
    // separately-created NaNs - which unboxed storage cannot do anyway.
    static bool val_eq(const Slot &a, const Slot &b) {
        return a == b || (std::isnan(a) && std::isnan(b));
    }
};


struct ObjectTraits {
    using Slot = PyObject *;
    static constexpr Dt DT = Dt::OBJ;
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

    static bool unbox(PyObject *o, Ovf, Slot *out) {
        *out = o;  // borrowed
        return true;
    }

    static PyObject *box(const Slot &v) { return Py_NewRef(v); }

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
    static constexpr Dt DT = Dt::OBJ;
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

    static bool unbox(PyObject *o, Ovf, Slot *out) {
        Py_hash_t h = PyObject_Hash(o);
        if (h == -1) {
            return false;
        }
        *out = HObj{h, o};  // borrowed
        return true;
    }

    static PyObject *box(const Slot &v) { return Py_NewRef(v.obj); }

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
static int unbox_probe(PyObject *o, Ovf ovf, typename Tr::Slot *out) {
    if (Tr::unbox(o, ovf, out)) {
        return 1;
    }
    if constexpr (Tr::DT != Dt::OBJ) {
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

    virtual Py_ssize_t size() const noexcept = 0;
    virtual int traverse(visitproc visit, void *arg) noexcept = 0;

    // Moves every owned reference into bin and empties the structure.
    virtual void clear_collect(Bin &bin) = 0;

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


struct SetLikeImpl : AnyImpl {
    using AnyImpl::AnyImpl;

    virtual int contains_(PyObject *o) = 0;            // 1 / 0 / -1
    virtual int add_(PyObject *o) = 0;                 // 1 added / 0 already present / -1
    virtual int discard_(PyObject *o, Bin &bin) = 0;   // 1 removed / 0 absent / -1
    virtual int pop_(PyObject **out, Bin &bin) = 0;    // 1 / 0 empty / -1

    // Boxes the *stored* element equal to the probe (probe semantics like contains_): for primitives that is just the
    // value back, but for object dtypes it returns the canonical stored instance - an interning-style lookup.
    virtual int find_elem(PyObject *probe, PyObject **out) = 0;   // 1 (new ref) / 0 / -1
};


struct MapLikeImpl : AnyImpl {
    using AnyImpl::AnyImpl;

    virtual int contains_(PyObject *k) = 0;                                   // 1 / 0 / -1
    virtual int lookup(PyObject *k, PyObject **out) = 0;                      // 1 (new ref) / 0 / -1
    virtual int assign(PyObject *k, PyObject *v, Bin &bin) = 0;               // 0 / -1
    virtual int remove_(PyObject *k, PyObject **out_opt, Bin &bin) = 0;       // 1 / 0 / -1
    virtual int pop_item(PyObject **k_out, PyObject **v_out, Bin &bin) = 0;   // 1 / 0 empty / -1
    virtual int set_default(PyObject *k, PyObject *d, PyObject **out) = 0;    // 0 (new ref) / -1
};


struct VecLikeImpl : AnyImpl {
    using AnyImpl::AnyImpl;

    // Index arguments are pre-normalized (non-negative, in range) by the Python layer under the same lock.
    virtual int get_at(Py_ssize_t i, PyObject **out) = 0;                                // 0 / -1
    virtual int set_at(Py_ssize_t i, PyObject *v, Bin &bin) = 0;                         // 0 / -1
    virtual int insert_at(Py_ssize_t i, PyObject *v) = 0;                                // 0 / -1
    virtual int pop_at(Py_ssize_t i, PyObject **out_opt, Bin &bin) = 0;                  // 0 / -1
    virtual int append_(PyObject *v) = 0;                                                // 0 / -1
    virtual int find_(PyObject *probe, Py_ssize_t start, Py_ssize_t stop, Py_ssize_t *at) = 0;  // 1 / 0 / -1
    virtual Py_ssize_t count_(PyObject *probe) = 0;                                      // >= 0 / -1
    virtual void reverse_() noexcept = 0;
    virtual int sort_(int reverse) = 0;                                                  // 0 / -1
    virtual VecLikeImpl *slice_(Py_ssize_t start, Py_ssize_t step, Py_ssize_t len) const = 0;
    virtual int set_slice(
        Py_ssize_t start,
        Py_ssize_t stop,
        Py_ssize_t step,
        Py_ssize_t slen,
        VecLikeImpl *src,
        Bin &bin) = 0;                                                                   // 0 / -1
    virtual int del_slice(Py_ssize_t start, Py_ssize_t stop, Py_ssize_t step, Py_ssize_t slen, Bin &bin) = 0;
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

static bool col_lock_acquire(AnyImpl *impl) {
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


static void col_lock_release(AnyImpl *impl) noexcept {
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
// Sorted set
//

template <typename K>
struct SortedSetImpl final : SetLikeImpl {
    using Cont = std::set<typename K::Slot, typename K::Less>;

    Cont set_;

    explicit SortedSetImpl(Ovf ovf)
        : SetLikeImpl(ColKind::SORTED_SET, K::DT, ovf, K::DT, ovf) {}

    ~SortedSetImpl() override {
        if constexpr (K::IS_OBJ) {
            for (const auto &s : set_) {
                Bin b;
                K::release_into(s, b);
            }
        }
    }

    Py_ssize_t size() const noexcept override {
        return (Py_ssize_t)set_.size();
    }

    int contains_(PyObject *o) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(o, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        return set_.find(s) != set_.end() ? 1 : 0;
    }

    int find_elem(PyObject *probe, PyObject **out) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(probe, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        auto it = set_.find(s);
        if (it == set_.end()) {
            return 0;
        }
        PyObject *o = K::box(*it);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int add_(PyObject *o) override {
        typename K::Slot s{};
        if (!K::unbox(o, key_ovf, &s)) {
            return -1;
        }
        auto [it, inserted] = set_.insert(s);
        if (!inserted) {
            return 0;
        }
        K::retain(*it);
        ++version;
        return 1;
    }

    int discard_(PyObject *o, Bin &bin) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(o, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        auto it = set_.find(s);
        if (it == set_.end()) {
            return 0;
        }
        K::release_into(*it, bin);
        set_.erase(it);
        ++version;
        return 1;
    }

    int pop_(PyObject **out, Bin &bin) override {
        if (set_.empty()) {
            return 0;
        }
        auto it = set_.begin();  // smallest element for sorted sets
        PyObject *o = K::box(*it);
        if (o == nullptr) {
            return -1;
        }
        K::release_into(*it, bin);
        set_.erase(it);
        ++version;
        *out = o;
        return 1;
    }

    int traverse(visitproc visit, void *arg) noexcept override {
        if constexpr (K::IS_OBJ) {
            for (const auto &s : set_) {
                int r = K::visit_slot(s, visit, arg);
                if (r != 0) {
                    return r;
                }
            }
        }
        return 0;
    }

    void clear_collect(Bin &bin) override {
        if constexpr (K::IS_OBJ) {
            bin.reserve_rest(set_.size());
            for (const auto &s : set_) {
                K::release_into(s, bin);
            }
        }
        set_.clear();
        ++version;
    }

    AnyImpl *clone() const override {
        auto *n = new SortedSetImpl(key_ovf);
        try {
            n->set_ = set_;  // structural copy; no comparator calls
        }
        catch (...) {
            n->set_.clear();  // nothing retained yet
            delete n;
            throw;
        }
        for (const auto &s : n->set_) {
            K::retain(s);
        }
        return n;
    }

    AnyIter *make_iter(IterKind, bool desc) override;
    AnyIter *make_iter_from(IterKind ik, bool desc, PyObject *base) override;

    int equals_same(AnyImpl *other) override {
        auto *o = static_cast<SortedSetImpl *>(other);
        if (set_.size() != o->set_.size()) {
            return 0;
        }
        typename K::Eq eq;
        auto a = set_.begin();
        auto b = o->set_.begin();
        for (; a != set_.end(); ++a, ++b) {
            if (!eq(*a, *b)) {
                return 0;
            }
        }
        return 1;
    }

    int merge_same(AnyImpl *other, Bin &) override {
        auto *o = static_cast<SortedSetImpl *>(other);
        bool changed = false;
        for (const auto &s : o->set_) {
            auto [it, inserted] = set_.insert(s);
            if (inserted) {
                K::retain(*it);
                changed = true;
            }
        }
        if (changed) {
            ++version;
        }
        return 0;
    }
};


template <typename K>
struct SortedSetIter final : AnyIter {
    SortedSetImpl<K> *impl;
    typename SortedSetImpl<K>::Cont::const_iterator it;
    uint64_t expect;
    bool rev;

    int next(PyObject **out) override {
        if (impl->version != expect) {
            PyErr_SetString(PyExc_RuntimeError, "container mutated during iteration");
            return -1;
        }
        typename SortedSetImpl<K>::Cont::const_iterator cur;
        if (rev) {
            if (it == impl->set_.begin()) {
                return 0;
            }
            cur = std::prev(it);
        }
        else {
            if (it == impl->set_.end()) {
                return 0;
            }
            cur = it;
        }
        PyObject *o = K::box(*cur);
        if (o == nullptr) {
            return -1;
        }
        it = rev ? cur : std::next(cur);
        *out = o;
        return 1;
    }
};


template <typename K>
AnyIter *SortedSetImpl<K>::make_iter(IterKind, bool desc) {
    auto *r = new SortedSetIter<K>();
    r->impl = this;
    r->rev = desc;
    r->it = desc ? set_.cend() : set_.cbegin();
    r->expect = version;
    return r;
}


template <typename K>
AnyIter *SortedSetImpl<K>::make_iter_from(IterKind, bool desc, PyObject *base) {
    typename K::Slot s{};
    if (!K::unbox(base, key_ovf, &s)) {
        return nullptr;
    }
    // Object-dtype bounds run Less (richcompare) here, so this can throw py_err_set; seek before allocating.
    auto it = desc ? set_.upper_bound(s) : set_.lower_bound(s);
    auto *r = new SortedSetIter<K>();
    r->impl = this;
    r->rev = desc;
    r->it = it;
    r->expect = version;
    return r;
}


//
// Hash set
//

template <typename K>
struct HashSetImpl final : SetLikeImpl {
    using Cont = std::unordered_set<typename K::Slot, typename K::Hash, typename K::Eq>;

    Cont set_;

    explicit HashSetImpl(Ovf ovf)
        : SetLikeImpl(ColKind::HASH_SET, K::DT, ovf, K::DT, ovf) {}

    ~HashSetImpl() override {
        if constexpr (K::IS_OBJ) {
            for (const auto &s : set_) {
                Bin b;
                K::release_into(s, b);
            }
        }
    }

    Py_ssize_t size() const noexcept override {
        return (Py_ssize_t)set_.size();
    }

    int contains_(PyObject *o) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(o, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        return set_.find(s) != set_.end() ? 1 : 0;
    }

    int find_elem(PyObject *probe, PyObject **out) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(probe, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        auto it = set_.find(s);
        if (it == set_.end()) {
            return 0;
        }
        PyObject *o = K::box(*it);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int add_(PyObject *o) override {
        typename K::Slot s{};
        if (!K::unbox(o, key_ovf, &s)) {
            return -1;
        }
        auto [it, inserted] = set_.insert(s);
        if (!inserted) {
            return 0;
        }
        K::retain(*it);
        ++version;
        return 1;
    }

    int discard_(PyObject *o, Bin &bin) override {
        typename K::Slot s{};
        int r = unbox_probe<K>(o, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        auto it = set_.find(s);
        if (it == set_.end()) {
            return 0;
        }
        K::release_into(*it, bin);
        set_.erase(it);
        ++version;
        return 1;
    }

    int pop_(PyObject **out, Bin &bin) override {
        if (set_.empty()) {
            return 0;
        }
        auto it = set_.begin();
        PyObject *o = K::box(*it);
        if (o == nullptr) {
            return -1;
        }
        K::release_into(*it, bin);
        set_.erase(it);
        ++version;
        *out = o;
        return 1;
    }

    int traverse(visitproc visit, void *arg) noexcept override {
        if constexpr (K::IS_OBJ) {
            for (const auto &s : set_) {
                int r = K::visit_slot(s, visit, arg);
                if (r != 0) {
                    return r;
                }
            }
        }
        return 0;
    }

    void clear_collect(Bin &bin) override {
        if constexpr (K::IS_OBJ) {
            bin.reserve_rest(set_.size());
            for (const auto &s : set_) {
                K::release_into(s, bin);
            }
        }
        set_.clear();
        ++version;
    }

    AnyImpl *clone() const override {
        auto *n = new HashSetImpl(key_ovf);
        try {
            n->set_ = set_;  // copies buckets; Hash is noexcept (cached for objects), Eq is not called
        }
        catch (...) {
            n->set_.clear();
            delete n;
            throw;
        }
        for (const auto &s : n->set_) {
            K::retain(s);
        }
        return n;
    }

    AnyIter *make_iter(IterKind, bool) override;

    int equals_same(AnyImpl *other) override {
        auto *o = static_cast<HashSetImpl *>(other);
        if (set_.size() != o->set_.size()) {
            return 0;
        }
        for (const auto &s : set_) {
            if (o->set_.find(s) == o->set_.end()) {
                return 0;
            }
        }
        return 1;
    }

    int merge_same(AnyImpl *other, Bin &) override {
        auto *o = static_cast<HashSetImpl *>(other);
        bool changed = false;
        for (const auto &s : o->set_) {
            auto [it, inserted] = set_.insert(s);
            if (inserted) {
                K::retain(*it);
                changed = true;
            }
        }
        if (changed) {
            ++version;
        }
        return 0;
    }
};


template <typename K>
struct HashSetIter final : AnyIter {
    HashSetImpl<K> *impl;
    typename HashSetImpl<K>::Cont::const_iterator it;
    uint64_t expect;

    int next(PyObject **out) override {
        if (impl->version != expect) {
            PyErr_SetString(PyExc_RuntimeError, "container mutated during iteration");
            return -1;
        }
        if (it == impl->set_.end()) {
            return 0;
        }
        PyObject *o = K::box(*it);
        if (o == nullptr) {
            return -1;
        }
        ++it;
        *out = o;
        return 1;
    }
};


// desc is ignored: hashed containers have no meaningful order, and no descending entry point is exposed for them.
template <typename K>
AnyIter *HashSetImpl<K>::make_iter(IterKind, bool) {
    auto *r = new HashSetIter<K>();
    r->impl = this;
    r->it = set_.cbegin();
    r->expect = version;
    return r;
}

//
// Sorted map
//

template <typename K, typename V>
struct SortedMapImpl final : MapLikeImpl {
    using Cont = std::map<typename K::Slot, typename V::Slot, typename K::Less>;

    Cont map_;

    SortedMapImpl(Ovf kovf, Ovf vovf)
        : MapLikeImpl(ColKind::SORTED_MAP, K::DT, kovf, V::DT, vovf) {}

    ~SortedMapImpl() override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            for (const auto &e : map_) {
                Bin b;
                K::release_into(e.first, b);
                V::release_into(e.second, b);
            }
        }
    }

    Py_ssize_t size() const noexcept override {
        return (Py_ssize_t)map_.size();
    }

    int contains_(PyObject *k) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        return map_.find(ks) != map_.end() ? 1 : 0;
    }

    int lookup(PyObject *k, PyObject **out) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        PyObject *o = V::box(it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int assign(PyObject *k, PyObject *v, Bin &bin) override {
        typename K::Slot ks{};
        if (!K::unbox(k, key_ovf, &ks)) {
            return -1;
        }
        typename V::Slot vs{};
        if (!V::unbox(v, val_ovf, &vs)) {
            return -1;
        }
        auto [it, inserted] = map_.try_emplace(ks, vs);
        if (inserted) {
            K::retain(it->first);
            V::retain(it->second);
            ++version;
        }
        else {
            V::release_into(it->second, bin);
            it->second = vs;
            V::retain(it->second);
        }
        return 0;
    }

    int remove_(PyObject *k, PyObject **out_opt, Bin &bin) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        if (out_opt != nullptr) {
            // Box before erasing so a boxing failure leaves the entry untouched.
            PyObject *o = V::box(it->second);
            if (o == nullptr) {
                return -1;
            }
            *out_opt = o;
        }
        K::release_into(it->first, bin);
        V::release_into(it->second, bin);
        map_.erase(it);
        ++version;
        return 1;
    }

    int pop_item(PyObject **k_out, PyObject **v_out, Bin &bin) override {
        if (map_.empty()) {
            return 0;
        }
        auto it = std::prev(map_.end());  // last (greatest) item, sorted-dict flavor
        PyObject *ko = K::box(it->first);
        if (ko == nullptr) {
            return -1;
        }
        PyObject *vo = V::box(it->second);
        if (vo == nullptr) {
            Py_DECREF(ko);
            return -1;
        }
        K::release_into(it->first, bin);
        V::release_into(it->second, bin);
        map_.erase(it);
        ++version;
        *k_out = ko;
        *v_out = vo;
        return 1;
    }

    int set_default(PyObject *k, PyObject *d, PyObject **out) override {
        // Insertion may occur, so the key gets full (non-probe) unboxing, like dict.setdefault.
        typename K::Slot ks{};
        if (!K::unbox(k, key_ovf, &ks)) {
            return -1;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            // The default is unboxed only if it is actually going to be inserted, dict-style.
            typename V::Slot vs{};
            if (!V::unbox(d, val_ovf, &vs)) {
                return -1;
            }
            it = map_.try_emplace(ks, vs).first;
            K::retain(it->first);
            V::retain(it->second);
            ++version;
        }
        PyObject *o = V::box(it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 0;
    }

    int traverse(visitproc visit, void *arg) noexcept override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            for (const auto &e : map_) {
                int r = K::visit_slot(e.first, visit, arg);
                if (r != 0) {
                    return r;
                }
                r = V::visit_slot(e.second, visit, arg);
                if (r != 0) {
                    return r;
                }
            }
        }
        return 0;
    }

    void clear_collect(Bin &bin) override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            bin.reserve_rest(map_.size() * ((K::IS_OBJ ? 1 : 0) + (V::IS_OBJ ? 1 : 0)));
            for (const auto &e : map_) {
                K::release_into(e.first, bin);
                V::release_into(e.second, bin);
            }
        }
        map_.clear();
        ++version;
    }

    AnyImpl *clone() const override {
        auto *n = new SortedMapImpl(key_ovf, val_ovf);
        try {
            n->map_ = map_;  // structural copy; no comparator calls
        }
        catch (...) {
            n->map_.clear();  // nothing retained yet
            delete n;
            throw;
        }
        for (auto &e : n->map_) {
            K::retain(e.first);
            V::retain(e.second);
        }
        return n;
    }

    AnyIter *make_iter(IterKind ik, bool desc) override;
    AnyIter *make_iter_from(IterKind ik, bool desc, PyObject *base) override;

    int equals_same(AnyImpl *other) override {
        auto *o = static_cast<SortedMapImpl *>(other);
        if (map_.size() != o->map_.size()) {
            return 0;
        }
        typename K::Eq eq;
        auto a = map_.begin();
        auto b = o->map_.begin();
        for (; a != map_.end(); ++a, ++b) {
            if (!eq(a->first, b->first) || !V::val_eq(a->second, b->second)) {
                return 0;
            }
        }
        return 1;
    }

    int merge_same(AnyImpl *other, Bin &bin) override {
        auto *o = static_cast<SortedMapImpl *>(other);
        if constexpr (V::IS_OBJ) {
            bin.reserve_rest(o->map_.size());
        }
        bool changed = false;
        for (const auto &e : o->map_) {
            auto [it, inserted] = map_.try_emplace(e.first, e.second);
            if (inserted) {
                K::retain(it->first);
                V::retain(it->second);
                changed = true;
            }
            else {
                V::release_into(it->second, bin);
                it->second = e.second;
                V::retain(it->second);
            }
        }
        if (changed) {
            ++version;
        }
        return 0;
    }
};


template <typename K, typename V>
struct SortedMapIter final : AnyIter {
    SortedMapImpl<K, V> *impl;
    typename SortedMapImpl<K, V>::Cont::const_iterator it;
    uint64_t expect;
    IterKind ik;
    bool rev;

    int next(PyObject **out) override {
        if (impl->version != expect) {
            PyErr_SetString(PyExc_RuntimeError, "container mutated during iteration");
            return -1;
        }
        typename SortedMapImpl<K, V>::Cont::const_iterator cur;
        if (rev) {
            if (it == impl->map_.begin()) {
                return 0;
            }
            cur = std::prev(it);
        }
        else {
            if (it == impl->map_.end()) {
                return 0;
            }
            cur = it;
        }
        PyObject *o;
        switch (ik) {
            case IterKind::VALUES:
                o = V::box(cur->second);
                break;
            case IterKind::ITEMS: {
                PyObject *ko = K::box(cur->first);
                if (ko == nullptr) {
                    return -1;
                }
                PyObject *vo = V::box(cur->second);
                if (vo == nullptr) {
                    Py_DECREF(ko);
                    return -1;
                }
                o = PyTuple_Pack(2, ko, vo);
                Py_DECREF(ko);
                Py_DECREF(vo);
                break;
            }
            default:  // KEYS
                o = K::box(cur->first);
                break;
        }
        if (o == nullptr) {
            return -1;
        }
        it = rev ? cur : std::next(cur);
        *out = o;
        return 1;
    }
};


template <typename K, typename V>
AnyIter *SortedMapImpl<K, V>::make_iter(IterKind ik, bool desc) {
    auto *r = new SortedMapIter<K, V>();
    r->impl = this;
    r->it = desc ? map_.cend() : map_.cbegin();
    r->expect = version;
    r->ik = ik;
    r->rev = desc;
    return r;
}


template <typename K, typename V>
AnyIter *SortedMapImpl<K, V>::make_iter_from(IterKind ik, bool desc, PyObject *base) {
    typename K::Slot ks{};
    if (!K::unbox(base, key_ovf, &ks)) {
        return nullptr;
    }
    // Object-dtype bounds run Less (richcompare) here, so this can throw py_err_set; seek before allocating.
    auto it = desc ? map_.upper_bound(ks) : map_.lower_bound(ks);
    auto *r = new SortedMapIter<K, V>();
    r->impl = this;
    r->it = it;
    r->expect = version;
    r->ik = ik;
    r->rev = desc;
    return r;
}


//
// Hash map
//

template <typename K, typename V>
struct HashMapImpl final : MapLikeImpl {
    using Cont = std::unordered_map<typename K::Slot, typename V::Slot, typename K::Hash, typename K::Eq>;

    Cont map_;

    HashMapImpl(Ovf kovf, Ovf vovf)
        : MapLikeImpl(ColKind::HASH_MAP, K::DT, kovf, V::DT, vovf) {}

    ~HashMapImpl() override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            for (const auto &e : map_) {
                Bin b;
                K::release_into(e.first, b);
                V::release_into(e.second, b);
            }
        }
    }

    Py_ssize_t size() const noexcept override {
        return (Py_ssize_t)map_.size();
    }

    int contains_(PyObject *k) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        return map_.find(ks) != map_.end() ? 1 : 0;
    }

    int lookup(PyObject *k, PyObject **out) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        PyObject *o = V::box(it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int assign(PyObject *k, PyObject *v, Bin &bin) override {
        typename K::Slot ks{};
        if (!K::unbox(k, key_ovf, &ks)) {
            return -1;
        }
        typename V::Slot vs{};
        if (!V::unbox(v, val_ovf, &vs)) {
            return -1;
        }
        auto [it, inserted] = map_.try_emplace(ks, vs);
        if (inserted) {
            K::retain(it->first);
            V::retain(it->second);
            ++version;
        }
        else {
            V::release_into(it->second, bin);
            it->second = vs;
            V::retain(it->second);
        }
        return 0;
    }

    int remove_(PyObject *k, PyObject **out_opt, Bin &bin) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        if (out_opt != nullptr) {
            PyObject *o = V::box(it->second);
            if (o == nullptr) {
                return -1;
            }
            *out_opt = o;
        }
        K::release_into(it->first, bin);
        V::release_into(it->second, bin);
        map_.erase(it);
        ++version;
        return 1;
    }

    int pop_item(PyObject **k_out, PyObject **v_out, Bin &bin) override {
        if (map_.empty()) {
            return 0;
        }
        auto it = map_.begin();  // arbitrary first item, dict-popitem flavor
        PyObject *ko = K::box(it->first);
        if (ko == nullptr) {
            return -1;
        }
        PyObject *vo = V::box(it->second);
        if (vo == nullptr) {
            Py_DECREF(ko);
            return -1;
        }
        K::release_into(it->first, bin);
        V::release_into(it->second, bin);
        map_.erase(it);
        ++version;
        *k_out = ko;
        *v_out = vo;
        return 1;
    }

    int set_default(PyObject *k, PyObject *d, PyObject **out) override {
        typename K::Slot ks{};
        if (!K::unbox(k, key_ovf, &ks)) {
            return -1;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            typename V::Slot vs{};
            if (!V::unbox(d, val_ovf, &vs)) {
                return -1;
            }
            it = map_.try_emplace(ks, vs).first;
            K::retain(it->first);
            V::retain(it->second);
            ++version;
        }
        PyObject *o = V::box(it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 0;
    }

    int traverse(visitproc visit, void *arg) noexcept override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            for (const auto &e : map_) {
                int r = K::visit_slot(e.first, visit, arg);
                if (r != 0) {
                    return r;
                }
                r = V::visit_slot(e.second, visit, arg);
                if (r != 0) {
                    return r;
                }
            }
        }
        return 0;
    }

    void clear_collect(Bin &bin) override {
        if constexpr (K::IS_OBJ || V::IS_OBJ) {
            bin.reserve_rest(map_.size() * ((K::IS_OBJ ? 1 : 0) + (V::IS_OBJ ? 1 : 0)));
            for (const auto &e : map_) {
                K::release_into(e.first, bin);
                V::release_into(e.second, bin);
            }
        }
        map_.clear();
        ++version;
    }

    AnyImpl *clone() const override {
        auto *n = new HashMapImpl(key_ovf, val_ovf);
        try {
            n->map_ = map_;  // copies buckets; Hash is noexcept (cached for objects), Eq is not called
        }
        catch (...) {
            n->map_.clear();
            delete n;
            throw;
        }
        for (auto &e : n->map_) {
            K::retain(e.first);
            V::retain(e.second);
        }
        return n;
    }

    AnyIter *make_iter(IterKind ik, bool) override;

    int equals_same(AnyImpl *other) override {
        auto *o = static_cast<HashMapImpl *>(other);
        if (map_.size() != o->map_.size()) {
            return 0;
        }
        for (const auto &e : map_) {
            auto it = o->map_.find(e.first);
            if (it == o->map_.end()) {
                return 0;
            }
            if (!V::val_eq(e.second, it->second)) {
                return 0;
            }
        }
        return 1;
    }

    int merge_same(AnyImpl *other, Bin &bin) override {
        auto *o = static_cast<HashMapImpl *>(other);
        if constexpr (V::IS_OBJ) {
            bin.reserve_rest(o->map_.size());
        }
        bool changed = false;
        for (const auto &e : o->map_) {
            auto [it, inserted] = map_.try_emplace(e.first, e.second);
            if (inserted) {
                K::retain(it->first);
                V::retain(it->second);
                changed = true;
            }
            else {
                V::release_into(it->second, bin);
                it->second = e.second;
                V::retain(it->second);
            }
        }
        if (changed) {
            ++version;
        }
        return 0;
    }
};


template <typename K, typename V>
struct HashMapIter final : AnyIter {
    HashMapImpl<K, V> *impl;
    typename HashMapImpl<K, V>::Cont::const_iterator it;
    uint64_t expect;
    IterKind ik;

    int next(PyObject **out) override {
        if (impl->version != expect) {
            PyErr_SetString(PyExc_RuntimeError, "container mutated during iteration");
            return -1;
        }
        if (it == impl->map_.end()) {
            return 0;
        }
        PyObject *o;
        switch (ik) {
            case IterKind::KEYS:
                o = K::box(it->first);
                break;
            case IterKind::VALUES:
                o = V::box(it->second);
                break;
            default: {
                PyObject *ko = K::box(it->first);
                if (ko == nullptr) {
                    return -1;
                }
                PyObject *vo = V::box(it->second);
                if (vo == nullptr) {
                    Py_DECREF(ko);
                    return -1;
                }
                o = PyTuple_Pack(2, ko, vo);
                Py_DECREF(ko);
                Py_DECREF(vo);
                break;
            }
        }
        if (o == nullptr) {
            return -1;
        }
        ++it;
        *out = o;
        return 1;
    }
};


template <typename K, typename V>
AnyIter *HashMapImpl<K, V>::make_iter(IterKind ik, bool) {
    auto *r = new HashMapIter<K, V>();
    r->impl = this;
    r->it = map_.cbegin();
    r->expect = version;
    r->ik = ik;
    return r;
}


//
// Vector
//

template <typename E>
struct VectorImpl final : VecLikeImpl {
    std::vector<typename E::Slot> vec_;

    explicit VectorImpl(Ovf ovf)
        : VecLikeImpl(ColKind::VECTOR, E::DT, ovf, E::DT, ovf) {}

    ~VectorImpl() override {
        if constexpr (E::IS_OBJ) {
            for (const auto &s : vec_) {
                Bin b;
                E::release_into(s, b);
            }
        }
    }

    Py_ssize_t size() const noexcept override {
        return (Py_ssize_t)vec_.size();
    }

    int get_at(Py_ssize_t i, PyObject **out) override {
        PyObject *o = E::box(vec_[(size_t)i]);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 0;
    }

    int set_at(Py_ssize_t i, PyObject *v, Bin &bin) override {
        typename E::Slot s{};
        if (!E::unbox(v, key_ovf, &s)) {
            return -1;
        }
        E::release_into(vec_[(size_t)i], bin);
        vec_[(size_t)i] = s;
        E::retain(vec_[(size_t)i]);
        return 0;
    }

    int insert_at(Py_ssize_t i, PyObject *v) override {
        typename E::Slot s{};
        if (!E::unbox(v, key_ovf, &s)) {
            return -1;
        }
        vec_.insert(vec_.begin() + i, s);
        E::retain(vec_[(size_t)i]);
        ++version;
        return 0;
    }

    int pop_at(Py_ssize_t i, PyObject **out_opt, Bin &bin) override {
        if (out_opt != nullptr) {
            PyObject *o = E::box(vec_[(size_t)i]);
            if (o == nullptr) {
                return -1;
            }
            *out_opt = o;
        }
        E::release_into(vec_[(size_t)i], bin);
        vec_.erase(vec_.begin() + i);
        ++version;
        return 0;
    }

    int append_(PyObject *v) override {
        typename E::Slot s{};
        if (!E::unbox(v, key_ovf, &s)) {
            return -1;
        }
        vec_.push_back(s);
        E::retain(vec_.back());
        ++version;
        return 0;
    }

    int find_(PyObject *probe, Py_ssize_t start, Py_ssize_t stop, Py_ssize_t *at) override {
        typename E::Slot s{};
        int r = unbox_probe<E>(probe, key_ovf, &s);
        if (r <= 0) {
            return r;
        }
        for (Py_ssize_t i = start; i < stop; ++i) {
            if (E::val_eq(vec_[(size_t)i], s)) {
                *at = i;
                return 1;
            }
        }
        return 0;
    }

    Py_ssize_t count_(PyObject *probe) override {
        typename E::Slot s{};
        int r = unbox_probe<E>(probe, key_ovf, &s);
        if (r < 0) {
            return -1;
        }
        if (r == 0) {
            return 0;
        }
        Py_ssize_t c = 0;
        for (const auto &e : vec_) {
            if (E::val_eq(e, s)) {
                ++c;
            }
        }
        return c;
    }

    void reverse_() noexcept override {
        std::reverse(vec_.begin(), vec_.end());
        ++version;
    }

    int sort_(int reverse) override {
        size_t n = vec_.size();
        if (n < 2) {
            return 0;
        }
        typename E::Less less;
        if constexpr (E::IS_OBJ) {
            // Sorting object slots in place with a comparator that can throw would lose the reference held in the
            // sort's temporary mid-swap. Sort an index permutation instead - a throw scrambles only the indices - and
            // gather into a fresh vector only on success.
            std::vector<size_t> idx(n);
            for (size_t i = 0; i < n; ++i) {
                idx[i] = i;
            }
            if (reverse) {
                std::sort(idx.begin(), idx.end(), [&](size_t a, size_t b) { return less(vec_[b], vec_[a]); });
            }
            else {
                std::sort(idx.begin(), idx.end(), [&](size_t a, size_t b) { return less(vec_[a], vec_[b]); });
            }
            std::vector<typename E::Slot> out;
            out.reserve(n);
            for (size_t i = 0; i < n; ++i) {
                out.push_back(vec_[idx[i]]);
            }
            vec_.swap(out);
        }
        else {
            if (reverse) {
                std::sort(vec_.begin(), vec_.end(), [&](const auto &a, const auto &b) { return less(b, a); });
            }
            else {
                std::sort(vec_.begin(), vec_.end(), less);
            }
        }
        ++version;
        return 0;
    }

    VecLikeImpl *slice_(Py_ssize_t start, Py_ssize_t step, Py_ssize_t len) const override {
        auto *n = new VectorImpl(key_ovf);
        try {
            n->vec_.reserve((size_t)len);
        }
        catch (...) {
            delete n;
            throw;
        }
        Py_ssize_t i = start;
        for (Py_ssize_t j = 0; j < len; ++j, i += step) {
            n->vec_.push_back(vec_[(size_t)i]);
        }
        for (const auto &s : n->vec_) {
            E::retain(s);
        }
        return n;
    }

    int set_slice(
        Py_ssize_t start,
        Py_ssize_t stop,
        Py_ssize_t step,
        Py_ssize_t slen,
        VecLikeImpl *src,
        Bin &bin) override {
        auto *o = static_cast<VectorImpl *>(src);  // caller guarantees same-shape, private (unshared) source
        if (step == 1) {
            size_t n = vec_.size();
            size_t sn = o->vec_.size();
            if constexpr (E::IS_OBJ) {
                bin.reserve_rest((size_t)slen);
            }
            // Assemble the full result off to the side; every step after the reserves is no-throw, so a failure
            // cannot leave the vector half-spliced.
            std::vector<typename E::Slot> out;
            out.reserve(n - (size_t)slen + sn);
            out.insert(out.end(), vec_.begin(), vec_.begin() + start);
            out.insert(out.end(), o->vec_.begin(), o->vec_.end());
            out.insert(out.end(), vec_.begin() + stop, vec_.end());
            for (const auto &s : o->vec_) {
                E::retain(s);
            }
            for (Py_ssize_t i = start; i < stop; ++i) {
                E::release_into(vec_[(size_t)i], bin);
            }
            vec_.swap(out);
            ++version;
            return 0;
        }
        // Extended slice: the caller has already verified len(src) == slen; overwrite element-wise (works for
        // negative steps too, indices all pre-validated).
        if constexpr (E::IS_OBJ) {
            bin.reserve_rest((size_t)slen);
        }
        for (Py_ssize_t j = 0; j < slen; ++j) {
            Py_ssize_t i = start + j * step;
            E::release_into(vec_[(size_t)i], bin);
            vec_[(size_t)i] = o->vec_[(size_t)j];
            E::retain(vec_[(size_t)i]);
        }
        return 0;
    }

    int del_slice(Py_ssize_t start, Py_ssize_t stop, Py_ssize_t step, Py_ssize_t slen, Bin &bin) override {
        if (slen <= 0) {
            return 0;
        }
        if (step == 1) {
            if constexpr (E::IS_OBJ) {
                bin.reserve_rest((size_t)slen);
            }
            for (Py_ssize_t i = start; i < stop; ++i) {
                E::release_into(vec_[(size_t)i], bin);
            }
            vec_.erase(vec_.begin() + start, vec_.begin() + stop);
            ++version;
            return 0;
        }
        if (step < 0) {
            // Normalize to an ascending deletion sequence.
            start = start + (slen - 1) * step;
            step = -step;
        }
        if constexpr (E::IS_OBJ) {
            bin.reserve_rest((size_t)slen);
        }
        size_t n = vec_.size();
        std::vector<typename E::Slot> out;
        out.reserve(n - (size_t)slen);
        Py_ssize_t next_del = start;
        Py_ssize_t left = slen;
        for (size_t i = 0; i < n; ++i) {
            if (left > 0 && (Py_ssize_t)i == next_del) {
                E::release_into(vec_[i], bin);
                --left;
                next_del += step;
            }
            else {
                out.push_back(vec_[i]);
            }
        }
        vec_.swap(out);
        ++version;
        return 0;
    }

    int traverse(visitproc visit, void *arg) noexcept override {
        if constexpr (E::IS_OBJ) {
            for (const auto &s : vec_) {
                int r = E::visit_slot(s, visit, arg);
                if (r != 0) {
                    return r;
                }
            }
        }
        return 0;
    }

    void clear_collect(Bin &bin) override {
        if constexpr (E::IS_OBJ) {
            bin.reserve_rest(vec_.size());
            for (const auto &s : vec_) {
                E::release_into(s, bin);
            }
        }
        vec_.clear();
        ++version;
    }

    AnyImpl *clone() const override {
        auto *n = new VectorImpl(key_ovf);
        try {
            n->vec_ = vec_;
        }
        catch (...) {
            n->vec_.clear();
            delete n;
            throw;
        }
        for (const auto &s : n->vec_) {
            E::retain(s);
        }
        return n;
    }

    AnyIter *make_iter(IterKind ik, bool desc) override;

    int equals_same(AnyImpl *other) override {
        auto *o = static_cast<VectorImpl *>(other);
        if (vec_.size() != o->vec_.size()) {
            return 0;
        }
        for (size_t i = 0; i < vec_.size(); ++i) {
            if (!E::val_eq(vec_[i], o->vec_[i])) {
                return 0;
            }
        }
        return 1;
    }

    int merge_same(AnyImpl *other, Bin &) override {
        auto *o = static_cast<VectorImpl *>(other);
        size_t on = o->vec_.size();
        if (on == 0) {
            return 0;
        }
        // Reserving up front keeps push_back no-throw and keeps the source indices stable when other == this
        // (v.extend(v) reads only the pre-extension prefix).
        vec_.reserve(vec_.size() + on);
        for (size_t i = 0; i < on; ++i) {
            vec_.push_back(o->vec_[i]);
            E::retain(vec_.back());
        }
        ++version;
        return 0;
    }
};


template <typename E>
struct VectorIter final : AnyIter {
    VectorImpl<E> *impl;
    Py_ssize_t idx;
    bool rev;

    int next(PyObject **out) override {
        // Index-based and mutation-tolerant, matching list iterator semantics: falling off the (possibly shrunk) end
        // exhausts the iterator permanently.
        if (idx < 0) {
            return 0;
        }
        Py_ssize_t n = (Py_ssize_t)impl->vec_.size();
        if (idx >= n) {
            idx = -1;
            return 0;
        }
        PyObject *o = E::box(impl->vec_[(size_t)idx]);
        if (o == nullptr) {
            return -1;
        }
        idx += rev ? -1 : 1;
        *out = o;
        return 1;
    }
};


template <typename E>
AnyIter *VectorImpl<E>::make_iter(IterKind, bool desc) {
    auto *r = new VectorIter<E>();
    r->impl = this;
    r->rev = desc;
    r->idx = r->rev ? (Py_ssize_t)vec_.size() - 1 : 0;
    return r;
}


//
// Impl factories
//

static SetLikeImpl *new_set_impl(ColKind kind, Dt dt, Ovf ovf) {
    if (kind == ColKind::SORTED_SET) {
        switch (dt) {
            case Dt::OBJ:
                return new SortedSetImpl<ObjectTraits>(ovf);
            case Dt::I64:
                return new SortedSetImpl<Int64Traits>(ovf);
            case Dt::U64:
                return new SortedSetImpl<UInt64Traits>(ovf);
            default:
                return new SortedSetImpl<Float64Traits>(ovf);
        }
    }
    switch (dt) {
        case Dt::OBJ:
            return new HashSetImpl<HashedObjectTraits>(ovf);
        case Dt::I64:
            return new HashSetImpl<Int64Traits>(ovf);
        case Dt::U64:
            return new HashSetImpl<UInt64Traits>(ovf);
        default:
            return new HashSetImpl<Float64Traits>(ovf);
    }
}


template <typename K>
static MapLikeImpl *new_sorted_map_impl(Ovf kovf, Dt vd, Ovf vovf) {
    switch (vd) {
        case Dt::OBJ:
            return new SortedMapImpl<K, ObjectTraits>(kovf, vovf);
        case Dt::I64:
            return new SortedMapImpl<K, Int64Traits>(kovf, vovf);
        case Dt::U64:
            return new SortedMapImpl<K, UInt64Traits>(kovf, vovf);
        default:
            return new SortedMapImpl<K, Float64Traits>(kovf, vovf);
    }
}


template <typename K>
static MapLikeImpl *new_hash_map_impl(Ovf kovf, Dt vd, Ovf vovf) {
    switch (vd) {
        case Dt::OBJ:
            return new HashMapImpl<K, ObjectTraits>(kovf, vovf);
        case Dt::I64:
            return new HashMapImpl<K, Int64Traits>(kovf, vovf);
        case Dt::U64:
            return new HashMapImpl<K, UInt64Traits>(kovf, vovf);
        default:
            return new HashMapImpl<K, Float64Traits>(kovf, vovf);
    }
}


static MapLikeImpl *new_map_impl(ColKind kind, Dt kd, Ovf kovf, Dt vd, Ovf vovf) {
    if (kind == ColKind::SORTED_MAP) {
        switch (kd) {
            case Dt::OBJ:
                return new_sorted_map_impl<ObjectTraits>(kovf, vd, vovf);
            case Dt::I64:
                return new_sorted_map_impl<Int64Traits>(kovf, vd, vovf);
            case Dt::U64:
                return new_sorted_map_impl<UInt64Traits>(kovf, vd, vovf);
            default:
                return new_sorted_map_impl<Float64Traits>(kovf, vd, vovf);
        }
    }
    switch (kd) {
        case Dt::OBJ:
            return new_hash_map_impl<HashedObjectTraits>(kovf, vd, vovf);
        case Dt::I64:
            return new_hash_map_impl<Int64Traits>(kovf, vd, vovf);
        case Dt::U64:
            return new_hash_map_impl<UInt64Traits>(kovf, vd, vovf);
        default:
            return new_hash_map_impl<Float64Traits>(kovf, vd, vovf);
    }
}


static VecLikeImpl *new_vec_impl(Dt dt, Ovf ovf) {
    switch (dt) {
        case Dt::OBJ:
            return new VectorImpl<ObjectTraits>(ovf);
        case Dt::I64:
            return new VectorImpl<Int64Traits>(ovf);
        case Dt::U64:
            return new VectorImpl<UInt64Traits>(ovf);
        default:
            return new VectorImpl<Float64Traits>(ovf);
    }
}


//
// Module state
//

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


static stl_state *get_state(PyObject *mod) {
    return (stl_state *)PyModule_GetState(mod);
}


static stl_state *find_state(PyTypeObject *tp) {
    PyObject *mod = PyType_GetModuleByDef(tp, stl_module_def());
    if (mod == nullptr) {
        return nullptr;
    }
    return get_state(mod);
}


// For binary operator slots, where either operand (but at least one) is one of our types.
static stl_state *find_state_2(PyObject *v, PyObject *w) {
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


static int col_ready(ColObject *co) {
    if (co->impl == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "container is not initialized");
        return 0;
    }
    return 1;
}


// KeyError's args must be the key itself, wrapped in a 1-tuple so that tuple keys don't splat.
static void raise_key_error(PyObject *k) {
    PyObject *t = PyTuple_Pack(1, k);
    if (t == nullptr) {
        return;
    }
    PyErr_SetObject(PyExc_KeyError, t);
    Py_DECREF(t);
}


// Takes ownership of impl (deleting it on allocation failure).
static PyObject *col_wrap(PyTypeObject *tp, AnyImpl *impl) {
    ColObject *co = (ColObject *)tp->tp_alloc(tp, 0);
    if (co == nullptr) {
        delete impl;
        return nullptr;
    }
    co->impl = impl;
    return (PyObject *)co;
}


static void col_dealloc(PyObject *self) {
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


static int col_traverse(PyObject *self, visitproc visit, void *arg) {
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


static int col_clear_slot(PyObject *self) {
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


static Py_ssize_t col_len(PyObject *self) {
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


static PyObject *col_clear_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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
static PyObject *col_copy_as(PyTypeObject *tp, ColObject *co) {
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

static void iter_dealloc(PyObject *self) {
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


static int iter_traverse(PyObject *self, visitproc visit, void *arg) {
    Py_VISIT(Py_TYPE(self));
    IterObject *io = (IterObject *)self;
    Py_VISIT(io->owner);
    return 0;
}


static int iter_clear(PyObject *self) {
    IterObject *io = (IterObject *)self;
    // The AnyIter points into the owner's impl, so it must die before the owner reference does.
    AnyIter *it = io->it;
    io->it = nullptr;
    delete it;
    Py_CLEAR(io->owner);
    return 0;
}


static PyObject *iter_next(PyObject *self) {
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


static PyType_Slot iter_slots[] = {
    {Py_tp_dealloc, (void *)iter_dealloc},
    {Py_tp_traverse, (void *)iter_traverse},
    {Py_tp_clear, (void *)iter_clear},
    {Py_tp_iter, (void *)PyObject_SelfIter},
    {Py_tp_iternext, (void *)iter_next},
    {0, nullptr},
};


static PyType_Spec iter_spec = {
    .name = _MODULE_FULL_NAME ".ColIter",
    .basicsize = (int)sizeof(IterObject),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
    .slots = iter_slots,
};


static PyObject *col_make_iter(PyObject *self, IterKind ik, bool desc) {
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


static PyObject *col_iter(PyObject *self) {
    return col_make_iter(self, IterKind::KEYS, false);
}


static PyObject *col_iter_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::KEYS, false);
}


static PyObject *col_reversed_meth(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::KEYS, true);
}


// Backs iter_from / iter_from_desc / items_from / items_from_desc: seeks under the container lock (object-dtype
// bounds run user comparators there, hence the py_err_set catch) and hands the seeded impl iterator to the shared
// iterator object, which re-locks per next() and version-checks like any other iterator.
static PyObject *col_make_iter_from(PyObject *self, IterKind ik, bool desc, PyObject *base) {
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


// Extracts the short class name ("Set") out of the heap type's qualified tp_name ("_stl.Set"), for reprs and
// error messages.
static const char *col_short_name(PyObject *self) {
    const char *tn = Py_TYPE(self)->tp_name;
    const char *dot = std::strrchr(tn, '.');
    return dot != nullptr ? dot + 1 : tn;
}


//
// Set / UnorderedSet
//

static bool is_our_set(stl_state *st, PyObject *o) {
    return PyObject_TypeCheck(o, st->set_type) || PyObject_TypeCheck(o, st->unordered_set_type);
}


static int set_contains_obj(ColObject *co, PyObject *o) {
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->contains_(o); });
}


static int set_add_obj(ColObject *co, PyObject *o) {
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->add_(o); });
}


// 1 removed / 0 absent / -1.
static int set_discard_obj(ColObject *co, PyObject *o) {
    Bin bin;
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->discard_(o, bin); });
}


static int set_extend_from(stl_state *st, ColObject *co, PyObject *items) {
    if (is_our_set(st, items)) {
        ColObject *oc = (ColObject *)items;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            Bin bin;
            ColGuard2 g(co->impl, oc->impl);
            if (!g.held()) {
                return -1;
            }
            return py_shield_int([&] { return co->impl->merge_same(oc->impl, bin); });
        }
    }

    PyObject *it = PyObject_GetIter(items);
    if (it == nullptr) {
        return -1;
    }
    PyObject *o;
    while ((o = PyIter_Next(it)) != nullptr) {
        int r = set_add_obj(co, o);
        Py_DECREF(o);
        if (r < 0) {
            Py_DECREF(it);
            return -1;
        }
    }
    Py_DECREF(it);
    return PyErr_Occurred() != nullptr ? -1 : 0;
}


static PyObject *set_new_like(stl_state *st, ColObject *like) {
    PyTypeObject *tp = like->impl->kind == ColKind::SORTED_SET ? st->set_type : st->unordered_set_type;
    SetLikeImpl *impl;
    try {
        impl = new_set_impl(like->impl->kind, like->impl->key_dt, like->impl->key_ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return nullptr;
    }
    return col_wrap(tp, impl);
}


static int set_init_impl(PyObject *self, PyObject *args, PyObject *kwds, ColKind kind) {
    ColObject *co = (ColObject *)self;
    if (co->impl != nullptr) {
        // Refusing re-init keeps live iterators (which point into the current impl) valid.
        PyErr_SetString(PyExc_TypeError, "container is already initialized");
        return -1;
    }

    static const char *KWLIST[] = {"dtype", "items", nullptr};
    PyObject *dtype_o = nullptr;
    PyObject *items = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", (char **)KWLIST, &dtype_o, &items)) {
        return -1;
    }

    DtypeSpec ds{Dt::OBJ, Ovf::RAISE};
    if (dtype_o != nullptr && dtype_o != Py_None && parse_dtype(dtype_o, &ds) < 0) {
        return -1;
    }

    try {
        co->impl = new_set_impl(kind, ds.dt, ds.ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return -1;
    }

    if (items != nullptr && items != Py_None) {
        stl_state *st = find_state(Py_TYPE(self));
        if (st == nullptr) {
            return -1;
        }
        if (set_extend_from(st, co, items) < 0) {
            return -1;
        }
    }
    return 0;
}


static int set_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return set_init_impl(self, args, kwds, ColKind::SORTED_SET);
}


static int unordered_set_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return set_init_impl(self, args, kwds, ColKind::HASH_SET);
}


static int set_sq_contains(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    return set_contains_obj(co, o);
}


static PyObject *set_add(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (set_add_obj(co, o) < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *set_discard(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (set_discard_obj(co, o) < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *set_remove(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int r = set_discard_obj(co, o);
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        raise_key_error(o);
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *set_pop(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->pop_(&out, bin); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        PyErr_SetString(PyExc_KeyError, "pop from an empty set");
        return nullptr;
    }
    return out;
}


static PyObject *set_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    PyTypeObject *tp = co->impl->kind == ColKind::SORTED_SET ? st->set_type : st->unordered_set_type;
    return col_copy_as(tp, co);
}


static PyObject *set_update(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    Py_ssize_t n = PyTuple_GET_SIZE(args);
    for (Py_ssize_t i = 0; i < n; ++i) {
        if (set_extend_from(st, co, PyTuple_GET_ITEM(args, i)) < 0) {
            return nullptr;
        }
    }
    Py_RETURN_NONE;
}


static PyObject *set_isdisjoint(PyObject *self, PyObject *other) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *it = PyObject_GetIter(other);
    if (it == nullptr) {
        return nullptr;
    }
    PyObject *o;
    while ((o = PyIter_Next(it)) != nullptr) {
        int c = set_contains_obj(co, o);
        Py_DECREF(o);
        if (c < 0) {
            Py_DECREF(it);
            return nullptr;
        }
        if (c) {
            Py_DECREF(it);
            Py_RETURN_FALSE;
        }
    }
    Py_DECREF(it);
    if (PyErr_Occurred() != nullptr) {
        return nullptr;
    }
    Py_RETURN_TRUE;
}


// Generic subset walk: 1 / 0 / -1. Iterates sub, membership-testing each element against sup; locking (where either
// side is ours) is per element and never nested.
static int set_issubset_of(PyObject *sub, PyObject *sup) {
    PyObject *it = PyObject_GetIter(sub);
    if (it == nullptr) {
        return -1;
    }
    PyObject *o;
    while ((o = PyIter_Next(it)) != nullptr) {
        int c = PySequence_Contains(sup, o);
        Py_DECREF(o);
        if (c < 0) {
            Py_DECREF(it);
            return -1;
        }
        if (!c) {
            Py_DECREF(it);
            return 0;
        }
    }
    Py_DECREF(it);
    return PyErr_Occurred() != nullptr ? -1 : 1;
}


static PyObject *set_richcompare(PyObject *self, PyObject *other, int op) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }

    if ((op == Py_EQ || op == Py_NE) && is_our_set(st, other)) {
        ColObject *oc = (ColObject *)other;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            int r;
            {
                ColGuard2 g(co->impl, oc->impl);
                if (!g.held()) {
                    return nullptr;
                }
                r = py_shield_int([&] { return co->impl->equals_same(oc->impl); });
            }
            if (r < 0) {
                return nullptr;
            }
            return PyBool_FromLong(op == Py_EQ ? r : !r);
        }
    }

    bool setlike = is_our_set(st, other) || PyAnySet_Check(other);
    if (!setlike) {
        int r = PyObject_IsInstance(other, st->abc_set);
        if (r < 0) {
            return nullptr;
        }
        setlike = r != 0;
    }
    if (!setlike) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    Py_ssize_t ls = PyObject_Length(self);
    if (ls < 0) {
        return nullptr;
    }
    Py_ssize_t lo = PyObject_Length(other);
    if (lo < 0) {
        return nullptr;
    }

    int r;
    switch (op) {
        case Py_EQ:
        case Py_NE:
            r = ls == lo ? set_issubset_of(self, other) : 0;
            if (r >= 0 && op == Py_NE) {
                r = !r;
            }
            break;
        case Py_LE:
            r = ls <= lo ? set_issubset_of(self, other) : 0;
            break;
        case Py_LT:
            r = ls < lo ? set_issubset_of(self, other) : 0;
            break;
        case Py_GE:
            r = lo <= ls ? set_issubset_of(other, self) : 0;
            break;
        default:  // Py_GT
            r = lo < ls ? set_issubset_of(other, self) : 0;
            break;
    }
    if (r < 0) {
        return nullptr;
    }
    return PyBool_FromLong(r);
}


// Binary set operators, abc.Set-style: the non-set operand may be any iterable, and the result takes its concrete
// type, dtype, and overflow mode from whichever operand is ours (the left one if both are).
static PyObject *set_binop(PyObject *v, PyObject *w, char op) {
    stl_state *st = find_state_2(v, w);
    if (st == nullptr) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    ColObject *ours;
    bool ours_is_left;
    if (is_our_set(st, v)) {
        ours = (ColObject *)v;
        ours_is_left = true;
    }
    else if (is_our_set(st, w)) {
        ours = (ColObject *)w;
        ours_is_left = false;
    }
    else {
        Py_RETURN_NOTIMPLEMENTED;
    }
    if (!col_ready(ours)) {
        return nullptr;
    }
    PyObject *other = ours_is_left ? w : v;

    // abc.Set returns NotImplemented for non-iterable operands.
    PyObject *probe_it = PyObject_GetIter(other);
    if (probe_it == nullptr) {
        if (PyErr_ExceptionMatches(PyExc_TypeError)) {
            PyErr_Clear();
            Py_RETURN_NOTIMPLEMENTED;
        }
        return nullptr;
    }

    PyObject *result = nullptr;

    switch (op) {
        case '|': {
            Py_DECREF(probe_it);
            PyTypeObject *tp = ours->impl->kind == ColKind::SORTED_SET ? st->set_type : st->unordered_set_type;
            result = col_copy_as(tp, ours);
            if (result == nullptr) {
                return nullptr;
            }
            if (set_extend_from(st, (ColObject *)result, other) < 0) {
                Py_DECREF(result);
                return nullptr;
            }
            return result;
        }

        case '&': {
            result = set_new_like(st, ours);
            if (result == nullptr) {
                Py_DECREF(probe_it);
                return nullptr;
            }
            PyObject *o;
            while ((o = PyIter_Next(probe_it)) != nullptr) {
                int c = set_contains_obj(ours, o);
                if (c > 0) {
                    c = set_add_obj((ColObject *)result, o) < 0 ? -1 : 0;
                }
                Py_DECREF(o);
                if (c < 0) {
                    goto fail;
                }
            }
            break;
        }

        case '-': {
            if (ours_is_left) {
                Py_DECREF(probe_it);
                probe_it = nullptr;
                PyTypeObject *tp = ours->impl->kind == ColKind::SORTED_SET ? st->set_type : st->unordered_set_type;
                result = col_copy_as(tp, ours);
                if (result == nullptr) {
                    return nullptr;
                }
                PyObject *it2 = PyObject_GetIter(other);
                if (it2 == nullptr) {
                    Py_DECREF(result);
                    return nullptr;
                }
                PyObject *o;
                while ((o = PyIter_Next(it2)) != nullptr) {
                    int r = set_discard_obj((ColObject *)result, o);
                    Py_DECREF(o);
                    if (r < 0) {
                        Py_DECREF(it2);
                        Py_DECREF(result);
                        return nullptr;
                    }
                }
                Py_DECREF(it2);
                if (PyErr_Occurred() != nullptr) {
                    Py_DECREF(result);
                    return nullptr;
                }
                return result;
            }
            // iterable - ours: keep the left operand's elements not contained in ours.
            result = set_new_like(st, ours);
            if (result == nullptr) {
                Py_DECREF(probe_it);
                return nullptr;
            }
            PyObject *o;
            while ((o = PyIter_Next(probe_it)) != nullptr) {
                int c = set_contains_obj(ours, o);
                if (c == 0) {
                    c = set_add_obj((ColObject *)result, o) < 0 ? -1 : 0;
                }
                Py_DECREF(o);
                if (c < 0) {
                    goto fail;
                }
            }
            break;
        }

        default: {  // '^'
            // Materialize the other operand into a same-spec temp first, so duplicates in it cannot double-toggle.
            Py_DECREF(probe_it);
            probe_it = nullptr;
            PyObject *temp = set_new_like(st, ours);
            if (temp == nullptr) {
                return nullptr;
            }
            if (set_extend_from(st, (ColObject *)temp, other) < 0) {
                Py_DECREF(temp);
                return nullptr;
            }
            PyTypeObject *tp = ours->impl->kind == ColKind::SORTED_SET ? st->set_type : st->unordered_set_type;
            result = col_copy_as(tp, ours);
            if (result == nullptr) {
                Py_DECREF(temp);
                return nullptr;
            }
            PyObject *it2 = PyObject_GetIter(temp);
            if (it2 == nullptr) {
                Py_DECREF(temp);
                Py_DECREF(result);
                return nullptr;
            }
            PyObject *o;
            int r = 0;
            while ((o = PyIter_Next(it2)) != nullptr) {
                r = set_discard_obj((ColObject *)result, o);
                if (r == 0) {
                    r = set_add_obj((ColObject *)result, o);
                }
                Py_DECREF(o);
                if (r < 0) {
                    break;
                }
            }
            Py_DECREF(it2);
            Py_DECREF(temp);
            if (r < 0 || PyErr_Occurred() != nullptr) {
                Py_DECREF(result);
                return nullptr;
            }
            return result;
        }
    }

    Py_DECREF(probe_it);
    if (PyErr_Occurred() != nullptr) {
        Py_DECREF(result);
        return nullptr;
    }
    return result;

fail:
    Py_XDECREF(probe_it);
    Py_XDECREF(result);
    return nullptr;
}


static PyObject *set_nb_or(PyObject *v, PyObject *w) {
    return set_binop(v, w, '|');
}


static PyObject *set_nb_and(PyObject *v, PyObject *w) {
    return set_binop(v, w, '&');
}


static PyObject *set_nb_sub(PyObject *v, PyObject *w) {
    return set_binop(v, w, '-');
}


static PyObject *set_nb_xor(PyObject *v, PyObject *w) {
    return set_binop(v, w, '^');
}


static PyObject *set_inplace(PyObject *v, PyObject *w, char op) {
    stl_state *st = find_state_2(v, w);
    if (st == nullptr || !is_our_set(st, v)) {
        Py_RETURN_NOTIMPLEMENTED;
    }
    ColObject *co = (ColObject *)v;
    if (!col_ready(co)) {
        return nullptr;
    }

    // Self-application shortcuts, matching builtin set semantics (s -= s clears, s ^= s clears, s |= s and
    // s &= s are no-ops).
    if (v == w) {
        if (op == '-' || op == '^') {
            PyObject *r = col_clear_meth(v, nullptr);
            if (r == nullptr) {
                return nullptr;
            }
            Py_DECREF(r);
        }
        return Py_NewRef(v);
    }

    switch (op) {
        case '|':
            if (set_extend_from(st, co, w) < 0) {
                if (PyErr_ExceptionMatches(PyExc_TypeError) && PyObject_GetIter(w) == nullptr) {
                    PyErr_Clear();
                    Py_RETURN_NOTIMPLEMENTED;
                }
                return nullptr;
            }
            break;

        case '-': {
            PyObject *it = PyObject_GetIter(w);
            if (it == nullptr) {
                if (PyErr_ExceptionMatches(PyExc_TypeError)) {
                    PyErr_Clear();
                    Py_RETURN_NOTIMPLEMENTED;
                }
                return nullptr;
            }
            PyObject *o;
            while ((o = PyIter_Next(it)) != nullptr) {
                int r = set_discard_obj(co, o);
                Py_DECREF(o);
                if (r < 0) {
                    Py_DECREF(it);
                    return nullptr;
                }
            }
            Py_DECREF(it);
            if (PyErr_Occurred() != nullptr) {
                return nullptr;
            }
            break;
        }

        case '&': {
            // abc.MutableSet style: materialize (self - w), then discard those elements.
            PyObject *gone = set_binop(v, w, '-');
            if (gone == nullptr) {
                return nullptr;
            }
            if (gone == Py_NotImplemented) {
                return gone;
            }
            PyObject *it = PyObject_GetIter(gone);
            if (it == nullptr) {
                Py_DECREF(gone);
                return nullptr;
            }
            PyObject *o;
            while ((o = PyIter_Next(it)) != nullptr) {
                int r = set_discard_obj(co, o);
                Py_DECREF(o);
                if (r < 0) {
                    Py_DECREF(it);
                    Py_DECREF(gone);
                    return nullptr;
                }
            }
            Py_DECREF(it);
            Py_DECREF(gone);
            if (PyErr_Occurred() != nullptr) {
                return nullptr;
            }
            break;
        }

        default: {  // '^'
            PyObject *temp = set_new_like(st, co);
            if (temp == nullptr) {
                return nullptr;
            }
            if (set_extend_from(st, (ColObject *)temp, w) < 0) {
                Py_DECREF(temp);
                if (PyErr_ExceptionMatches(PyExc_TypeError) && PyObject_GetIter(w) == nullptr) {
                    PyErr_Clear();
                    Py_RETURN_NOTIMPLEMENTED;
                }
                return nullptr;
            }
            PyObject *it = PyObject_GetIter(temp);
            if (it == nullptr) {
                Py_DECREF(temp);
                return nullptr;
            }
            PyObject *o;
            int r = 0;
            while ((o = PyIter_Next(it)) != nullptr) {
                r = set_discard_obj(co, o);
                if (r == 0) {
                    r = set_add_obj(co, o);
                }
                Py_DECREF(o);
                if (r < 0) {
                    break;
                }
            }
            Py_DECREF(it);
            Py_DECREF(temp);
            if (r < 0 || PyErr_Occurred() != nullptr) {
                return nullptr;
            }
            break;
        }
    }

    return Py_NewRef(v);
}


static PyObject *set_nb_ior(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '|');
}


static PyObject *set_nb_iand(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '&');
}


static PyObject *set_nb_isub(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '-');
}


static PyObject *set_nb_ixor(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '^');
}


static PyObject *set_repr(PyObject *self) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int rc = Py_ReprEnter(self);
    if (rc != 0) {
        return rc > 0 ? PyUnicode_FromFormat("%s(...)", col_short_name(self)) : nullptr;
    }
    PyObject *lst = PySequence_List(self);
    if (lst == nullptr) {
        Py_ReprLeave(self);
        return nullptr;
    }
    PyObject *r = PyUnicode_FromFormat(
        "%s('%s', %R)", col_short_name(self), dtype_name(co->impl->key_dt, co->impl->key_ovf), lst);
    Py_DECREF(lst);
    Py_ReprLeave(self);
    return r;
}


static PyObject *col_get_dtype(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
}


static PyGetSetDef set_getset[] = {
    {"dtype", col_get_dtype, nullptr, PyDoc_STR("Canonical element dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};



// SortedCollection surface (sorted variant only): iter / iter_desc are just the existing iterators under the interface
// names; the seeded and find forms ride the new impl primitives.
static PyObject *set_iter_from(PyObject *self, PyObject *base) {
    return col_make_iter_from(self, IterKind::KEYS, false, base);
}


static PyObject *set_iter_from_desc(PyObject *self, PyObject *base) {
    return col_make_iter_from(self, IterKind::KEYS, true, base);
}


static PyObject *set_find(PyObject *self, PyObject *probe) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->find_elem(probe, &out); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        Py_RETURN_NONE;
    }
    return out;
}


static PyMethodDef set_methods[] = {
    {"add", set_add, METH_O, PyDoc_STR("Add an element.")},
    {"discard", set_discard, METH_O, PyDoc_STR("Remove an element if present.")},
    {"remove", set_remove, METH_O, PyDoc_STR("Remove an element; raise KeyError if absent.")},
    {"pop", set_pop, METH_NOARGS,
     PyDoc_STR("Remove and return an element (the smallest for Set); raise KeyError if empty.")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all elements.")},
    {"copy", set_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtype.")},
    {"update", set_update, METH_VARARGS, PyDoc_STR("Add elements from each iterable argument.")},
    {"isdisjoint", set_isdisjoint, METH_O, PyDoc_STR("Return True if the iterable shares no elements with this set.")},
    {"__class_getitem__", Py_GenericAlias, METH_O | METH_CLASS,
     PyDoc_STR("See PEP 585: parameterized generic alias support (e.g. Set[int]).")},
    {nullptr, nullptr, 0, nullptr},
};


// Same as set_methods plus __reversed__: only the sorted variant has a meaningful reverse order.
static PyMethodDef sorted_set_methods[] = {
    {"add", set_add, METH_O, PyDoc_STR("Add an element.")},
    {"discard", set_discard, METH_O, PyDoc_STR("Remove an element if present.")},
    {"remove", set_remove, METH_O, PyDoc_STR("Remove an element; raise KeyError if absent.")},
    {"pop", set_pop, METH_NOARGS,
     PyDoc_STR("Remove and return an element (the smallest for Set); raise KeyError if empty.")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all elements.")},
    {"copy", set_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtype.")},
    {"update", set_update, METH_VARARGS, PyDoc_STR("Add elements from each iterable argument.")},
    {"isdisjoint", set_isdisjoint, METH_O, PyDoc_STR("Return True if the iterable shares no elements with this set.")},
    {"__reversed__", col_reversed_meth, METH_NOARGS, PyDoc_STR("Return a reverse (descending) iterator.")},
    {"iter", col_iter_meth, METH_NOARGS, PyDoc_STR("Return an ascending iterator (SortedIter interface).")},
    {"iter_desc", col_reversed_meth, METH_NOARGS, PyDoc_STR("Return a descending iterator (SortedIter interface).")},
    {"iter_from", set_iter_from, METH_O,
     PyDoc_STR("Return an ascending iterator over elements >= base (SortedIter interface).")},
    {"iter_from_desc", set_iter_from_desc, METH_O,
     PyDoc_STR("Return a descending iterator over elements <= base (SortedIter interface).")},
    {"find", set_find, METH_O,
     PyDoc_STR("Return the stored element equal to the argument, or None (SortedCollection interface).")},
    {"__class_getitem__", Py_GenericAlias, METH_O | METH_CLASS,
     PyDoc_STR("See PEP 585: parameterized generic alias support (e.g. Set[int]).")},
    {nullptr, nullptr, 0, nullptr},
};


static PyType_Slot set_slots[] = {
    {Py_tp_init, (void *)set_init},
    {Py_tp_dealloc, (void *)col_dealloc},
    {Py_tp_traverse, (void *)col_traverse},
    {Py_tp_clear, (void *)col_clear_slot},
    {Py_tp_repr, (void *)set_repr},
    {Py_tp_iter, (void *)col_iter},
    {Py_tp_hash, (void *)PyObject_HashNotImplemented},
    {Py_tp_richcompare, (void *)set_richcompare},
    {Py_tp_methods, (void *)sorted_set_methods},
    {Py_tp_getset, (void *)set_getset},
    {Py_sq_length, (void *)col_len},
    {Py_sq_contains, (void *)set_sq_contains},
    {Py_nb_or, (void *)set_nb_or},
    {Py_nb_and, (void *)set_nb_and},
    {Py_nb_subtract, (void *)set_nb_sub},
    {Py_nb_xor, (void *)set_nb_xor},
    {Py_nb_inplace_or, (void *)set_nb_ior},
    {Py_nb_inplace_and, (void *)set_nb_iand},
    {Py_nb_inplace_subtract, (void *)set_nb_isub},
    {Py_nb_inplace_xor, (void *)set_nb_ixor},
    {0, nullptr},
};


static PyType_Slot unordered_set_slots[] = {
    {Py_tp_init, (void *)unordered_set_init},
    {Py_tp_dealloc, (void *)col_dealloc},
    {Py_tp_traverse, (void *)col_traverse},
    {Py_tp_clear, (void *)col_clear_slot},
    {Py_tp_repr, (void *)set_repr},
    {Py_tp_iter, (void *)col_iter},
    {Py_tp_hash, (void *)PyObject_HashNotImplemented},
    {Py_tp_richcompare, (void *)set_richcompare},
    {Py_tp_methods, (void *)set_methods},
    {Py_tp_getset, (void *)set_getset},
    {Py_sq_length, (void *)col_len},
    {Py_sq_contains, (void *)set_sq_contains},
    {Py_nb_or, (void *)set_nb_or},
    {Py_nb_and, (void *)set_nb_and},
    {Py_nb_subtract, (void *)set_nb_sub},
    {Py_nb_xor, (void *)set_nb_xor},
    {Py_nb_inplace_or, (void *)set_nb_ior},
    {Py_nb_inplace_and, (void *)set_nb_iand},
    {Py_nb_inplace_subtract, (void *)set_nb_isub},
    {Py_nb_inplace_xor, (void *)set_nb_ixor},
    {0, nullptr},
};


#define _COL_TYPE_FLAGS \
    (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_IMMUTABLETYPE)


static PyType_Spec set_spec = {
    .name = _MODULE_FULL_NAME ".Set",
    .basicsize = (int)sizeof(ColObject),
    .itemsize = 0,
    .flags = _COL_TYPE_FLAGS,
    .slots = set_slots,
};


static PyType_Spec unordered_set_spec = {
    .name = _MODULE_FULL_NAME ".UnorderedSet",
    .basicsize = (int)sizeof(ColObject),
    .itemsize = 0,
    .flags = _COL_TYPE_FLAGS,
    .slots = unordered_set_slots,
};


//
// Map / UnorderedMap
//

static bool is_our_map(stl_state *st, PyObject *o) {
    return PyObject_TypeCheck(o, st->map_type) || PyObject_TypeCheck(o, st->unordered_map_type);
}


static int map_assign_obj(ColObject *co, PyObject *k, PyObject *v) {
    Bin bin;
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->assign(k, v, bin); });
}


// Update from an iterable of key/value pairs.
static int map_update_pairs(ColObject *co, PyObject *pairs) {
    PyObject *it = PyObject_GetIter(pairs);
    if (it == nullptr) {
        return -1;
    }
    PyObject *pair;
    while ((pair = PyIter_Next(it)) != nullptr) {
        PyObject *fast = PySequence_Fast(pair, "map update sequence element is not iterable");
        Py_DECREF(pair);
        if (fast == nullptr) {
            Py_DECREF(it);
            return -1;
        }
        if (PySequence_Fast_GET_SIZE(fast) != 2) {
            PyErr_Format(
                PyExc_ValueError,
                "map update sequence element has length %zd; 2 is required",
                PySequence_Fast_GET_SIZE(fast));
            Py_DECREF(fast);
            Py_DECREF(it);
            return -1;
        }
        int r = map_assign_obj(co, PySequence_Fast_GET_ITEM(fast, 0), PySequence_Fast_GET_ITEM(fast, 1));
        Py_DECREF(fast);
        if (r < 0) {
            Py_DECREF(it);
            return -1;
        }
    }
    Py_DECREF(it);
    return PyErr_Occurred() != nullptr ? -1 : 0;
}


static int map_update_from(stl_state *st, ColObject *co, PyObject *src) {
    if (is_our_map(st, src)) {
        ColObject *oc = (ColObject *)src;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            Bin bin;
            ColGuard2 g(co->impl, oc->impl);
            if (!g.held()) {
                return -1;
            }
            return py_shield_int([&] { return co->impl->merge_same(oc->impl, bin); });
        }
        // Different shape: fall through to the generic mapping walk below (our maps have keys()).
    }

    if (PyDict_Check(src)) {
        PyObject *items = PyDict_Items(src);  // snapshot, safe against concurrent dict mutation
        if (items == nullptr) {
            return -1;
        }
        int r = map_update_pairs(co, items);
        Py_DECREF(items);
        return r;
    }

    // dict.update semantics: anything with a keys() method is treated as a mapping, else as an iterable of pairs.
    PyObject *keys_meth = PyObject_GetAttrString(src, "keys");
    if (keys_meth == nullptr) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            return -1;
        }
        PyErr_Clear();
        return map_update_pairs(co, src);
    }
    PyObject *keys = PyObject_CallNoArgs(keys_meth);
    Py_DECREF(keys_meth);
    if (keys == nullptr) {
        return -1;
    }
    PyObject *it = PyObject_GetIter(keys);
    Py_DECREF(keys);
    if (it == nullptr) {
        return -1;
    }
    PyObject *k;
    while ((k = PyIter_Next(it)) != nullptr) {
        PyObject *v = PyObject_GetItem(src, k);
        if (v == nullptr) {
            Py_DECREF(k);
            Py_DECREF(it);
            return -1;
        }
        int r = map_assign_obj(co, k, v);
        Py_DECREF(v);
        Py_DECREF(k);
        if (r < 0) {
            Py_DECREF(it);
            return -1;
        }
    }
    Py_DECREF(it);
    return PyErr_Occurred() != nullptr ? -1 : 0;
}


static int map_init_impl(PyObject *self, PyObject *args, PyObject *kwds, ColKind kind) {
    ColObject *co = (ColObject *)self;
    if (co->impl != nullptr) {
        PyErr_SetString(PyExc_TypeError, "container is already initialized");
        return -1;
    }

    static const char *KWLIST[] = {"key_type", "value_type", "items", nullptr};
    PyObject *kd_o = nullptr;
    PyObject *vd_o = nullptr;
    PyObject *items = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOO", (char **)KWLIST, &kd_o, &vd_o, &items)) {
        return -1;
    }

    DtypeSpec kd{Dt::OBJ, Ovf::RAISE};
    DtypeSpec vd{Dt::OBJ, Ovf::RAISE};
    if (kd_o != nullptr && kd_o != Py_None && parse_dtype(kd_o, &kd) < 0) {
        return -1;
    }
    if (vd_o != nullptr && vd_o != Py_None && parse_dtype(vd_o, &vd) < 0) {
        return -1;
    }

    try {
        co->impl = new_map_impl(kind, kd.dt, kd.ovf, vd.dt, vd.ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return -1;
    }

    if (items != nullptr && items != Py_None) {
        stl_state *st = find_state(Py_TYPE(self));
        if (st == nullptr) {
            return -1;
        }
        if (map_update_from(st, co, items) < 0) {
            return -1;
        }
    }
    return 0;
}


static int map_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return map_init_impl(self, args, kwds, ColKind::SORTED_MAP);
}


static int unordered_map_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return map_init_impl(self, args, kwds, ColKind::HASH_MAP);
}


static PyObject *map_subscript(PyObject *self, PyObject *k) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->lookup(k, &out); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        raise_key_error(k);
        return nullptr;
    }
    return out;
}


static int map_ass_subscript(PyObject *self, PyObject *k, PyObject *v) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    Bin bin;
    if (v == nullptr) {
        int r;
        {
            ColGuard g(co->impl);
            if (!g.held()) {
                return -1;
            }
            r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->remove_(k, nullptr, bin); });
        }
        if (r < 0) {
            return -1;
        }
        if (r == 0) {
            raise_key_error(k);
            return -1;
        }
        return 0;
    }
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return -1;
        }
        return py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->assign(k, v, bin); });
    }
}


static int map_sq_contains(PyObject *self, PyObject *k) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->contains_(k); });
}


static PyObject *map_get(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = Py_None;
    if (!PyArg_ParseTuple(args, "O|O:get", &k, &dflt)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->lookup(k, &out); });
    }
    if (r < 0) {
        return nullptr;
    }
    return r == 0 ? Py_NewRef(dflt) : out;
}


static PyObject *map_pop(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = nullptr;
    if (!PyArg_ParseTuple(args, "O|O:pop", &k, &dflt)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->remove_(k, &out, bin); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        if (dflt != nullptr) {
            return Py_NewRef(dflt);
        }
        raise_key_error(k);
        return nullptr;
    }
    return out;
}


static PyObject *map_popitem(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *ko = nullptr;
    PyObject *vo = nullptr;
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->pop_item(&ko, &vo, bin); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        PyErr_SetString(PyExc_KeyError, "popitem(): container is empty");
        return nullptr;
    }
    PyObject *t = PyTuple_Pack(2, ko, vo);
    Py_DECREF(ko);
    Py_DECREF(vo);
    return t;
}


static PyObject *map_setdefault(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = Py_None;
    if (!PyArg_ParseTuple(args, "O|O:setdefault", &k, &dflt)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->set_default(k, dflt, &out); });
    }
    if (r < 0) {
        return nullptr;
    }
    return out;
}


static PyObject *map_update(PyObject *self, PyObject *args, PyObject *kwds) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    Py_ssize_t n = PyTuple_GET_SIZE(args);
    if (n > 1) {
        PyErr_Format(PyExc_TypeError, "update expected at most 1 argument, got %zd", n);
        return nullptr;
    }
    if (n == 1) {
        if (map_update_from(st, co, PyTuple_GET_ITEM(args, 0)) < 0) {
            return nullptr;
        }
    }
    if (kwds != nullptr && PyDict_GET_SIZE(kwds) > 0) {
        PyObject *items = PyDict_Items(kwds);
        if (items == nullptr) {
            return nullptr;
        }
        int r = map_update_pairs(co, items);
        Py_DECREF(items);
        if (r < 0) {
            return nullptr;
        }
    }
    Py_RETURN_NONE;
}


static PyObject *map_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    PyTypeObject *tp = co->impl->kind == ColKind::SORTED_MAP ? st->map_type : st->unordered_map_type;
    return col_copy_as(tp, co);
}


static PyObject *map_view(PyObject *self, PyObject *view_cls) {
    // The collections.abc view classes are the documented, protocol-driven implementation here: they wrap the
    // mapping and route everything through __iter__ / __getitem__ / __len__, and bring the Set mixin along for
    // keys() and items().
    return PyObject_CallOneArg(view_cls, self);
}


static PyObject *map_keys(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_keys_view);
}


static PyObject *map_values(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_values_view);
}


static PyObject *map_items(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_items_view);
}


static PyObject *map_richcompare(PyObject *self, PyObject *other, int op) {
    if (op != Py_EQ && op != Py_NE) {
        Py_RETURN_NOTIMPLEMENTED;
    }
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }

    if (is_our_map(st, other)) {
        ColObject *oc = (ColObject *)other;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            int r;
            {
                ColGuard2 g(co->impl, oc->impl);
                if (!g.held()) {
                    return nullptr;
                }
                r = py_shield_int([&] { return co->impl->equals_same(oc->impl); });
            }
            if (r < 0) {
                return nullptr;
            }
            return PyBool_FromLong(op == Py_EQ ? r : !r);
        }
    }

    bool maplike = is_our_map(st, other) || PyDict_Check(other);
    if (!maplike) {
        int r = PyObject_IsInstance(other, st->abc_mapping);
        if (r < 0) {
            return nullptr;
        }
        maplike = r != 0;
    }
    if (!maplike) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    int eq = 1;
    Py_ssize_t ls = PyObject_Length(self);
    if (ls < 0) {
        return nullptr;
    }
    Py_ssize_t lo = PyObject_Length(other);
    if (lo < 0) {
        return nullptr;
    }
    if (ls != lo) {
        eq = 0;
    }
    else {
        PyObject *it = col_make_iter(self, IterKind::ITEMS, false);
        if (it == nullptr) {
            return nullptr;
        }
        PyObject *item;
        while (eq && (item = PyIter_Next(it)) != nullptr) {
            PyObject *ov = PyObject_GetItem(other, PyTuple_GET_ITEM(item, 0));
            if (ov == nullptr) {
                if (!PyErr_ExceptionMatches(PyExc_KeyError)) {
                    Py_DECREF(item);
                    Py_DECREF(it);
                    return nullptr;
                }
                PyErr_Clear();
                eq = 0;
            }
            else {
                int r = PyObject_RichCompareBool(PyTuple_GET_ITEM(item, 1), ov, Py_EQ);
                Py_DECREF(ov);
                if (r < 0) {
                    Py_DECREF(item);
                    Py_DECREF(it);
                    return nullptr;
                }
                eq = r;
            }
            Py_DECREF(item);
        }
        Py_DECREF(it);
        if (PyErr_Occurred() != nullptr) {
            return nullptr;
        }
    }
    return PyBool_FromLong(op == Py_EQ ? eq : !eq);
}


static PyObject *map_repr(PyObject *self) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int rc = Py_ReprEnter(self);
    if (rc != 0) {
        return rc > 0 ? PyUnicode_FromFormat("%s(...)", col_short_name(self)) : nullptr;
    }
    PyObject *it = col_make_iter(self, IterKind::ITEMS, false);
    if (it == nullptr) {
        Py_ReprLeave(self);
        return nullptr;
    }
    PyObject *lst = PySequence_List(it);
    Py_DECREF(it);
    if (lst == nullptr) {
        Py_ReprLeave(self);
        return nullptr;
    }
    PyObject *r = PyUnicode_FromFormat(
        "%s('%s', '%s', %R)",
        col_short_name(self),
        dtype_name(co->impl->key_dt, co->impl->key_ovf),
        dtype_name(co->impl->val_dt, co->impl->val_ovf),
        lst);
    Py_DECREF(lst);
    Py_ReprLeave(self);
    return r;
}


static PyObject *map_get_key_type(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
}


static PyObject *map_get_value_type(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->val_dt, co->impl->val_ovf));
}


static PyGetSetDef map_getset[] = {
    {"key_type", map_get_key_type, nullptr, PyDoc_STR("Canonical key dtype string."), nullptr},
    {"value_type", map_get_value_type, nullptr, PyDoc_STR("Canonical value dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};



// SortedItems surface (sorted variant only).
static PyObject *map_iteritems(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::ITEMS, false);
}


static PyObject *map_items_desc(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::ITEMS, true);
}


static PyObject *map_items_from(PyObject *self, PyObject *key) {
    return col_make_iter_from(self, IterKind::ITEMS, false, key);
}


static PyObject *map_items_from_desc(PyObject *self, PyObject *key) {
    return col_make_iter_from(self, IterKind::ITEMS, true, key);
}


static PyMethodDef map_methods[] = {
    {"get", map_get, METH_VARARGS, PyDoc_STR("Return the value for key, or default (None) if absent.")},
    {"pop", map_pop, METH_VARARGS,
     PyDoc_STR("Remove key and return its value; return default if given, else raise KeyError.")},
    {"popitem", map_popitem, METH_NOARGS,
     PyDoc_STR("Remove and return a (key, value) pair (the greatest key for Map); raise KeyError if empty.")},
    {"setdefault", map_setdefault, METH_VARARGS,
     PyDoc_STR("Return the value for key, inserting default (None) first if absent.")},
    {"update", (PyCFunction)(void (*)(void))map_update, METH_VARARGS | METH_KEYWORDS,
     PyDoc_STR("Update from a mapping or iterable of key/value pairs, and from keyword arguments.")},
    {"keys", map_keys, METH_NOARGS, PyDoc_STR("Return a collections.abc.KeysView of the map.")},
    {"values", map_values, METH_NOARGS, PyDoc_STR("Return a collections.abc.ValuesView of the map.")},
    {"items", map_items, METH_NOARGS, PyDoc_STR("Return a collections.abc.ItemsView of the map.")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all items.")},
    {"copy", map_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtypes.")},
    {"__class_getitem__", Py_GenericAlias, METH_O | METH_CLASS,
     PyDoc_STR("See PEP 585: parameterized generic alias support (e.g. Set[int]).")},
    {nullptr, nullptr, 0, nullptr},
};


// Same as map_methods plus __reversed__: only the sorted variant has a meaningful reverse order.
static PyMethodDef sorted_map_methods[] = {
    {"get", map_get, METH_VARARGS, PyDoc_STR("Return the value for key, or default (None) if absent.")},
    {"pop", map_pop, METH_VARARGS,
     PyDoc_STR("Remove key and return its value; return default if given, else raise KeyError.")},
    {"popitem", map_popitem, METH_NOARGS,
     PyDoc_STR("Remove and return a (key, value) pair (the greatest key for Map); raise KeyError if empty.")},
    {"setdefault", map_setdefault, METH_VARARGS,
     PyDoc_STR("Return the value for key, inserting default (None) first if absent.")},
    {"update", (PyCFunction)(void (*)(void))map_update, METH_VARARGS | METH_KEYWORDS,
     PyDoc_STR("Update from a mapping or iterable of key/value pairs, and from keyword arguments.")},
    {"keys", map_keys, METH_NOARGS, PyDoc_STR("Return a collections.abc.KeysView of the map.")},
    {"values", map_values, METH_NOARGS, PyDoc_STR("Return a collections.abc.ValuesView of the map.")},
    {"items", map_items, METH_NOARGS, PyDoc_STR("Return a collections.abc.ItemsView of the map.")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all items.")},
    {"copy", map_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtypes.")},
    {"__reversed__", col_reversed_meth, METH_NOARGS, PyDoc_STR("Return a reverse (descending) key iterator.")},
    {"iteritems", map_iteritems, METH_NOARGS,
     PyDoc_STR("Return an ascending (key, value) iterator (SortedItems interface).")},
    {"items_desc", map_items_desc, METH_NOARGS,
     PyDoc_STR("Return a descending (key, value) iterator (SortedItems interface).")},
    {"items_from", map_items_from, METH_O,
     PyDoc_STR("Return an ascending (key, value) iterator over keys >= key (SortedItems interface).")},
    {"items_from_desc", map_items_from_desc, METH_O,
     PyDoc_STR("Return a descending (key, value) iterator over keys <= key (SortedItems interface).")},
    {"__class_getitem__", Py_GenericAlias, METH_O | METH_CLASS,
     PyDoc_STR("See PEP 585: parameterized generic alias support (e.g. Set[int]).")},
    {nullptr, nullptr, 0, nullptr},
};


static PyType_Slot map_slots[] = {
    {Py_tp_init, (void *)map_init},
    {Py_tp_dealloc, (void *)col_dealloc},
    {Py_tp_traverse, (void *)col_traverse},
    {Py_tp_clear, (void *)col_clear_slot},
    {Py_tp_repr, (void *)map_repr},
    {Py_tp_iter, (void *)col_iter},
    {Py_tp_hash, (void *)PyObject_HashNotImplemented},
    {Py_tp_richcompare, (void *)map_richcompare},
    {Py_tp_methods, (void *)sorted_map_methods},
    {Py_tp_getset, (void *)map_getset},
    {Py_mp_length, (void *)col_len},
    {Py_mp_subscript, (void *)map_subscript},
    {Py_mp_ass_subscript, (void *)map_ass_subscript},
    {Py_sq_contains, (void *)map_sq_contains},
    {0, nullptr},
};


static PyType_Slot unordered_map_slots[] = {
    {Py_tp_init, (void *)unordered_map_init},
    {Py_tp_dealloc, (void *)col_dealloc},
    {Py_tp_traverse, (void *)col_traverse},
    {Py_tp_clear, (void *)col_clear_slot},
    {Py_tp_repr, (void *)map_repr},
    {Py_tp_iter, (void *)col_iter},
    {Py_tp_hash, (void *)PyObject_HashNotImplemented},
    {Py_tp_richcompare, (void *)map_richcompare},
    {Py_tp_methods, (void *)map_methods},
    {Py_tp_getset, (void *)map_getset},
    {Py_mp_length, (void *)col_len},
    {Py_mp_subscript, (void *)map_subscript},
    {Py_mp_ass_subscript, (void *)map_ass_subscript},
    {Py_sq_contains, (void *)map_sq_contains},
    {0, nullptr},
};


static PyType_Spec map_spec = {
    .name = _MODULE_FULL_NAME ".Map",
    .basicsize = (int)sizeof(ColObject),
    .itemsize = 0,
    .flags = _COL_TYPE_FLAGS,
    .slots = map_slots,
};


static PyType_Spec unordered_map_spec = {
    .name = _MODULE_FULL_NAME ".UnorderedMap",
    .basicsize = (int)sizeof(ColObject),
    .itemsize = 0,
    .flags = _COL_TYPE_FLAGS,
    .slots = unordered_map_slots,
};


//
// Vector
//

static VecLikeImpl *vec_impl(ColObject *co) {
    return static_cast<VecLikeImpl *>(co->impl);
}


// Builds a private (unshared, unlocked) same-spec VectorImpl holding the elements of src. Used as the right-hand side
// of slice assignment and generic extend, so the actual splice can run as one no-throw step under self's lock.
static VecLikeImpl *vec_materialize(stl_state *st, ColObject *co, PyObject *src) {
    VecLikeImpl *temp;
    try {
        temp = new_vec_impl(co->impl->key_dt, co->impl->key_ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return nullptr;
    }

    if (PyObject_TypeCheck(src, st->vector_type)) {
        ColObject *oc = (ColObject *)src;
        if (oc->impl != nullptr && temp->same_shape(oc->impl)) {
            int r;
            Bin bin;
            {
                ColGuard g(oc->impl);  // only the source needs locking; temp is private
                if (!g.held()) {
                    delete temp;
                    return nullptr;
                }
                r = py_shield_int([&] { return temp->merge_same(oc->impl, bin); });
            }
            if (r < 0) {
                delete temp;
                return nullptr;
            }
            return temp;
        }
    }

    PyObject *it = PyObject_GetIter(src);
    if (it == nullptr) {
        delete temp;
        return nullptr;
    }
    PyObject *o;
    while ((o = PyIter_Next(it)) != nullptr) {
        int r = py_shield_int([&] { return temp->append_(o); });
        Py_DECREF(o);
        if (r < 0) {
            Py_DECREF(it);
            delete temp;
            return nullptr;
        }
    }
    Py_DECREF(it);
    if (PyErr_Occurred() != nullptr) {
        delete temp;
        return nullptr;
    }
    return temp;
}


static int vec_extend_from(stl_state *st, ColObject *co, PyObject *src) {
    if (PyObject_TypeCheck(src, st->vector_type)) {
        ColObject *oc = (ColObject *)src;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            Bin bin;
            ColGuard2 g(co->impl, oc->impl);
            if (!g.held()) {
                return -1;
            }
            return py_shield_int([&] { return co->impl->merge_same(oc->impl, bin); });
        }
    }
    VecLikeImpl *temp = vec_materialize(st, co, src);
    if (temp == nullptr) {
        return -1;
    }
    int r;
    {
        Bin bin;
        ColGuard g(co->impl);
        if (!g.held()) {
            delete temp;
            return -1;
        }
        r = py_shield_int([&] { return co->impl->merge_same(temp, bin); });
    }
    delete temp;
    return r;
}


static int vec_init(PyObject *self, PyObject *args, PyObject *kwds) {
    ColObject *co = (ColObject *)self;
    if (co->impl != nullptr) {
        PyErr_SetString(PyExc_TypeError, "container is already initialized");
        return -1;
    }

    static const char *KWLIST[] = {"dtype", "items", nullptr};
    PyObject *dtype_o = nullptr;
    PyObject *items = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", (char **)KWLIST, &dtype_o, &items)) {
        return -1;
    }

    DtypeSpec ds{Dt::OBJ, Ovf::RAISE};
    if (dtype_o != nullptr && dtype_o != Py_None && parse_dtype(dtype_o, &ds) < 0) {
        return -1;
    }

    try {
        co->impl = new_vec_impl(ds.dt, ds.ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return -1;
    }

    if (items != nullptr && items != Py_None) {
        stl_state *st = find_state(Py_TYPE(self));
        if (st == nullptr) {
            return -1;
        }
        if (vec_extend_from(st, co, items) < 0) {
            return -1;
        }
    }
    return 0;
}


static PyObject *vec_get_index(ColObject *co, PyObject *self, Py_ssize_t i, bool adjust_negative) {
    PyObject *out = nullptr;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        Py_ssize_t n = co->impl->size();
        if (adjust_negative && i < 0) {
            i += n;
        }
        if (i < 0 || i >= n) {
            g.release();
            PyErr_Format(PyExc_IndexError, "%s index out of range", col_short_name(self));
            return nullptr;
        }
        r = py_shield_int([&] { return vec_impl(co)->get_at(i, &out); });
    }
    if (r < 0) {
        return nullptr;
    }
    return out;
}


static PyObject *vec_sq_item(PyObject *self, Py_ssize_t i) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return vec_get_index(co, self, i, false);
}


static PyObject *vec_subscript(PyObject *self, PyObject *key) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }

    if (PyIndex_Check(key)) {
        Py_ssize_t i = PyNumber_AsSsize_t(key, PyExc_IndexError);
        if (i == -1 && PyErr_Occurred() != nullptr) {
            return nullptr;
        }
        return vec_get_index(co, self, i, true);
    }

    if (PySlice_Check(key)) {
        stl_state *st = find_state(Py_TYPE(self));
        if (st == nullptr) {
            return nullptr;
        }
        Py_ssize_t start, stop, step;
        if (PySlice_Unpack(key, &start, &stop, &step) < 0) {
            return nullptr;
        }
        VecLikeImpl *sl = nullptr;
        {
            ColGuard g(co->impl);
            if (!g.held()) {
                return nullptr;
            }
            Py_ssize_t slen = PySlice_AdjustIndices(co->impl->size(), &start, &stop, step);
            try {
                sl = vec_impl(co)->slice_(start, step, slen);
            }
            catch (std::bad_alloc &) {
                g.release();
                PyErr_NoMemory();
                return nullptr;
            }
        }
        return col_wrap(st->vector_type, sl);
    }

    PyErr_Format(
        PyExc_TypeError, "%s indices must be integers or slices, not %.200s", col_short_name(self),
        Py_TYPE(key)->tp_name);
    return nullptr;
}


static int vec_ass_subscript(PyObject *self, PyObject *key, PyObject *v) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }

    if (PyIndex_Check(key)) {
        Py_ssize_t i = PyNumber_AsSsize_t(key, PyExc_IndexError);
        if (i == -1 && PyErr_Occurred() != nullptr) {
            return -1;
        }
        Bin bin;
        ColGuard g(co->impl);
        if (!g.held()) {
            return -1;
        }
        Py_ssize_t n = co->impl->size();
        if (i < 0) {
            i += n;
        }
        if (i < 0 || i >= n) {
            g.release();
            PyErr_Format(PyExc_IndexError, "%s assignment index out of range", col_short_name(self));
            return -1;
        }
        if (v == nullptr) {
            return py_shield_int([&] { return vec_impl(co)->pop_at(i, nullptr, bin); });
        }
        return py_shield_int([&] { return vec_impl(co)->set_at(i, v, bin); });
    }

    if (PySlice_Check(key)) {
        Py_ssize_t start, stop, step;
        if (PySlice_Unpack(key, &start, &stop, &step) < 0) {
            return -1;
        }

        if (v == nullptr) {
            Bin bin;
            ColGuard g(co->impl);
            if (!g.held()) {
                return -1;
            }
            Py_ssize_t slen = PySlice_AdjustIndices(co->impl->size(), &start, &stop, step);
            return py_shield_int([&] { return vec_impl(co)->del_slice(start, stop, step, slen, bin); });
        }

        stl_state *st = find_state(Py_TYPE(self));
        if (st == nullptr) {
            return -1;
        }
        VecLikeImpl *temp = vec_materialize(st, co, v);
        if (temp == nullptr) {
            return -1;
        }
        int r;
        {
            Bin bin;
            ColGuard g(co->impl);
            if (!g.held()) {
                delete temp;
                return -1;
            }
            // Indices are computed under the same lock as the splice; the length seen here is authoritative.
            Py_ssize_t slen = PySlice_AdjustIndices(co->impl->size(), &start, &stop, step);
            if (step == 1 && stop < start) {
                // AdjustIndices leaves stop < start for an empty forward slice like v[5:2]; list assignment
                // treats that as a pure insertion at start.
                stop = start;
            }
            if (step != 1 && temp->size() != slen) {
                g.release();
                PyErr_Format(
                    PyExc_ValueError,
                    "attempt to assign sequence of size %zd to extended slice of size %zd",
                    temp->size(),
                    slen);
                delete temp;
                return -1;
            }
            r = py_shield_int([&] { return vec_impl(co)->set_slice(start, stop, step, slen, temp, bin); });
        }
        delete temp;
        return r;
    }

    PyErr_Format(
        PyExc_TypeError, "%s indices must be integers or slices, not %.200s", col_short_name(self),
        Py_TYPE(key)->tp_name);
    return -1;
}


static int vec_sq_contains(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    Py_ssize_t at;
    return py_shield_int([&] { return vec_impl(co)->find_(o, 0, co->impl->size(), &at); });
}


static PyObject *vec_append(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return vec_impl(co)->append_(o); });
    }
    if (r < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *vec_extend(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    if (vec_extend_from(st, co, o) < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *vec_nb_iadd(PyObject *v, PyObject *w) {
    stl_state *st = find_state_2(v, w);
    if (st == nullptr || !PyObject_TypeCheck(v, st->vector_type)) {
        Py_RETURN_NOTIMPLEMENTED;
    }
    ColObject *co = (ColObject *)v;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (vec_extend_from(st, co, w) < 0) {
        return nullptr;
    }
    return Py_NewRef(v);
}


static PyObject *vec_insert(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    Py_ssize_t i;
    PyObject *v;
    if (!PyArg_ParseTuple(args, "nO:insert", &i, &v)) {
        return nullptr;
    }
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        Py_ssize_t n = co->impl->size();
        if (i < 0) {
            i += n;
            if (i < 0) {
                i = 0;
            }
        }
        if (i > n) {
            i = n;
        }
        r = py_shield_int([&] { return vec_impl(co)->insert_at(i, v); });
    }
    if (r < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *vec_pop(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    Py_ssize_t i = -1;
    if (!PyArg_ParseTuple(args, "|n:pop", &i)) {
        return nullptr;
    }
    PyObject *out = nullptr;
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        Py_ssize_t n = co->impl->size();
        if (n == 0) {
            g.release();
            PyErr_Format(PyExc_IndexError, "pop from empty %s", col_short_name(self));
            return nullptr;
        }
        if (i < 0) {
            i += n;
        }
        if (i < 0 || i >= n) {
            g.release();
            PyErr_SetString(PyExc_IndexError, "pop index out of range");
            return nullptr;
        }
        r = py_shield_int([&] { return vec_impl(co)->pop_at(i, &out, bin); });
    }
    if (r < 0) {
        return nullptr;
    }
    return out;
}


static PyObject *vec_remove(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] {
            Py_ssize_t at;
            int f = vec_impl(co)->find_(o, 0, co->impl->size(), &at);
            if (f <= 0) {
                return f;
            }
            int p = vec_impl(co)->pop_at(at, nullptr, bin);
            return p < 0 ? p : 1;
        });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        PyErr_Format(PyExc_ValueError, "%s.remove(x): x not in %s", col_short_name(self), col_short_name(self));
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *vec_index_meth(PyObject *self, PyObject *args) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *v;
    Py_ssize_t start = 0;
    Py_ssize_t stop = PY_SSIZE_T_MAX;
    if (!PyArg_ParseTuple(args, "O|nn:index", &v, &start, &stop)) {
        return nullptr;
    }
    Py_ssize_t at = -1;
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        Py_ssize_t n = co->impl->size();
        if (start < 0) {
            start += n;
            if (start < 0) {
                start = 0;
            }
        }
        if (start > n) {
            start = n;
        }
        if (stop < 0) {
            stop += n;
            if (stop < 0) {
                stop = 0;
            }
        }
        if (stop > n) {
            stop = n;
        }
        r = py_shield_int([&] { return vec_impl(co)->find_(v, start, stop, &at); });
    }
    if (r < 0) {
        return nullptr;
    }
    if (r == 0) {
        PyErr_Format(PyExc_ValueError, "%R is not in %s", v, col_short_name(self));
        return nullptr;
    }
    return PyLong_FromSsize_t(at);
}


static PyObject *vec_count(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    Py_ssize_t c;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        try {
            c = vec_impl(co)->count_(o);
        }
        catch (py_err_set &) {
            c = -1;
        }
        catch (std::bad_alloc &) {
            g.release();
            PyErr_NoMemory();
            return nullptr;
        }
    }
    if (c < 0) {
        return nullptr;
    }
    return PyLong_FromSsize_t(c);
}


static PyObject *vec_reverse(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        vec_impl(co)->reverse_();
    }
    Py_RETURN_NONE;
}


static PyObject *vec_sort(PyObject *self, PyObject *args, PyObject *kwds) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    static const char *KWLIST[] = {"reverse", nullptr};
    int reverse = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|$p:sort", (char **)KWLIST, &reverse)) {
        return nullptr;
    }
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            return nullptr;
        }
        r = py_shield_int([&] { return vec_impl(co)->sort_(reverse); });
    }
    if (r < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


static PyObject *vec_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return col_copy_as(st->vector_type, co);
}


static PyObject *vec_richcompare(PyObject *self, PyObject *other, int op) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }

    bool other_ours = PyObject_TypeCheck(other, st->vector_type);
    if ((op == Py_EQ || op == Py_NE) && other_ours) {
        ColObject *oc = (ColObject *)other;
        if (oc->impl != nullptr && co->impl->same_shape(oc->impl)) {
            int r;
            {
                ColGuard2 g(co->impl, oc->impl);
                if (!g.held()) {
                    return nullptr;
                }
                r = py_shield_int([&] { return co->impl->equals_same(oc->impl); });
            }
            if (r < 0) {
                return nullptr;
            }
            return PyBool_FromLong(op == Py_EQ ? r : !r);
        }
    }

    if (!other_ours && !PyList_Check(other)) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Cross-dtype / ordering comparisons: snapshot both sides and delegate to list comparison.
    PyObject *a = PySequence_List(self);
    if (a == nullptr) {
        return nullptr;
    }
    PyObject *b = PySequence_List(other);
    if (b == nullptr) {
        Py_DECREF(a);
        return nullptr;
    }
    PyObject *r = PyObject_RichCompare(a, b, op);
    Py_DECREF(a);
    Py_DECREF(b);
    return r;
}


static PyObject *vec_repr(PyObject *self) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    int rc = Py_ReprEnter(self);
    if (rc != 0) {
        return rc > 0 ? PyUnicode_FromFormat("%s(...)", col_short_name(self)) : nullptr;
    }
    PyObject *lst = PySequence_List(self);
    if (lst == nullptr) {
        Py_ReprLeave(self);
        return nullptr;
    }
    PyObject *r = PyUnicode_FromFormat(
        "%s('%s', %R)", col_short_name(self), dtype_name(co->impl->key_dt, co->impl->key_ovf), lst);
    Py_DECREF(lst);
    Py_ReprLeave(self);
    return r;
}


static PyGetSetDef vector_getset[] = {
    {"dtype", col_get_dtype, nullptr, PyDoc_STR("Canonical element dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};


static PyMethodDef vector_methods[] = {
    {"append", vec_append, METH_O, PyDoc_STR("Append an element.")},
    {"extend", vec_extend, METH_O, PyDoc_STR("Append all elements from an iterable.")},
    {"insert", vec_insert, METH_VARARGS, PyDoc_STR("Insert an element before the given index.")},
    {"pop", vec_pop, METH_VARARGS, PyDoc_STR("Remove and return the element at index (default last).")},
    {"remove", vec_remove, METH_O, PyDoc_STR("Remove the first occurrence of a value.")},
    {"index", vec_index_meth, METH_VARARGS, PyDoc_STR("Return the first index of a value.")},
    {"count", vec_count, METH_O, PyDoc_STR("Return the number of occurrences of a value.")},
    {"reverse", vec_reverse, METH_NOARGS, PyDoc_STR("Reverse in place.")},
    {"sort", (PyCFunction)(void (*)(void))vec_sort, METH_VARARGS | METH_KEYWORDS,
     PyDoc_STR("Sort in place (keyword-only reverse=False).")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all elements.")},
    {"copy", vec_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtype.")},
    {"__reversed__", col_reversed_meth, METH_NOARGS, PyDoc_STR("Return a reverse iterator.")},
    {"__class_getitem__", Py_GenericAlias, METH_O | METH_CLASS,
     PyDoc_STR("See PEP 585: parameterized generic alias support (e.g. Set[int]).")},
    {nullptr, nullptr, 0, nullptr},
};


static PyType_Slot vector_slots[] = {
    {Py_tp_init, (void *)vec_init},
    {Py_tp_dealloc, (void *)col_dealloc},
    {Py_tp_traverse, (void *)col_traverse},
    {Py_tp_clear, (void *)col_clear_slot},
    {Py_tp_repr, (void *)vec_repr},
    {Py_tp_iter, (void *)col_iter},
    {Py_tp_hash, (void *)PyObject_HashNotImplemented},
    {Py_tp_richcompare, (void *)vec_richcompare},
    {Py_tp_methods, (void *)vector_methods},
    {Py_tp_getset, (void *)vector_getset},
    {Py_sq_length, (void *)col_len},
    {Py_sq_item, (void *)vec_sq_item},
    {Py_sq_contains, (void *)vec_sq_contains},
    {Py_mp_length, (void *)col_len},
    {Py_mp_subscript, (void *)vec_subscript},
    {Py_mp_ass_subscript, (void *)vec_ass_subscript},
    {Py_nb_inplace_add, (void *)vec_nb_iadd},
    {0, nullptr},
};


static PyType_Spec vector_spec = {
    .name = _MODULE_FULL_NAME ".Vector",
    .basicsize = (int)sizeof(ColObject),
    .itemsize = 0,
    .flags = _COL_TYPE_FLAGS,
    .slots = vector_slots,
};


//
// Module
//

static int add_col_type(PyObject *mod, PyType_Spec *spec, PyTypeObject **out) {
    PyTypeObject *tp = (PyTypeObject *)PyType_FromModuleAndSpec(mod, spec, nullptr);
    if (tp == nullptr) {
        return -1;
    }
    *out = tp;  // the state slot owns this reference; PyModule_AddType takes its own
    return PyModule_AddType(mod, tp);
}


static int fetch_abc(PyObject *abc, const char *name, PyObject **out) {
    *out = PyObject_GetAttrString(abc, name);
    return *out != nullptr ? 0 : -1;
}


static int reg_abc(PyObject *abc, const char *name, PyTypeObject *tp) {
    PyObject *cls = PyObject_GetAttrString(abc, name);
    if (cls == nullptr) {
        return -1;
    }
    PyObject *r = PyObject_CallMethod(cls, "register", "O", (PyObject *)tp);
    Py_DECREF(cls);
    if (r == nullptr) {
        return -1;
    }
    Py_DECREF(r);
    return 0;
}


static int stl_exec(PyObject *mod) {
    stl_state *st = get_state(mod);

    st->iter_type = (PyTypeObject *)PyType_FromModuleAndSpec(mod, &iter_spec, nullptr);
    if (st->iter_type == nullptr) {
        return -1;
    }

    if (add_col_type(mod, &set_spec, &st->set_type) < 0
        || add_col_type(mod, &unordered_set_spec, &st->unordered_set_type) < 0
        || add_col_type(mod, &map_spec, &st->map_type) < 0
        || add_col_type(mod, &unordered_map_spec, &st->unordered_map_type) < 0
        || add_col_type(mod, &vector_spec, &st->vector_type) < 0) {
        return -1;
    }

    PyObject *abc = PyImport_ImportModule("collections.abc");
    if (abc == nullptr) {
        return -1;
    }
    int rc = 0;
    rc = rc < 0 ? rc : fetch_abc(abc, "Set", &st->abc_set);
    rc = rc < 0 ? rc : fetch_abc(abc, "Mapping", &st->abc_mapping);
    rc = rc < 0 ? rc : fetch_abc(abc, "KeysView", &st->abc_keys_view);
    rc = rc < 0 ? rc : fetch_abc(abc, "ValuesView", &st->abc_values_view);
    rc = rc < 0 ? rc : fetch_abc(abc, "ItemsView", &st->abc_items_view);
    rc = rc < 0 ? rc : reg_abc(abc, "MutableSet", st->set_type);
    rc = rc < 0 ? rc : reg_abc(abc, "MutableSet", st->unordered_set_type);
    rc = rc < 0 ? rc : reg_abc(abc, "MutableMapping", st->map_type);
    rc = rc < 0 ? rc : reg_abc(abc, "MutableMapping", st->unordered_map_type);
    rc = rc < 0 ? rc : reg_abc(abc, "MutableSequence", st->vector_type);

    // sorted interfaces registration (soft): inside the om tree this registers the sorted variants with the
    // sorted-container ABCs, so isinstance checks pass with no Python-side wiring at all; registering with the most
    // derived interface covers its real ancestors (SortedIter / SortedItems / Mapping / ...) transitively.
    if (rc == 0) {
        PyObject *som = PyImport_ImportModule("omcore.collections.sorted");
        if (som == nullptr) {
            if (PyErr_ExceptionMatches(PyExc_ModuleNotFoundError)) {
                PyErr_Clear();
            }
            else {
                rc = -1;
            }
        }
        else {
            rc = reg_abc(som, "SortedCollection", st->set_type);
            rc = rc < 0 ? rc : reg_abc(som, "SortedMutableMapping", st->map_type);
            Py_DECREF(som);
        }
    }
    Py_DECREF(abc);
    if (rc < 0) {
        return -1;
    }

    PyObject *dtypes = Py_BuildValue(
        "(ssssssss)",
        "object",
        "int64-raise",
        "int64-clamp",
        "int64-wrap",
        "uint64-raise",
        "uint64-clamp",
        "uint64-wrap",
        "float64");
    if (dtypes == nullptr) {
        return -1;
    }
    rc = PyModule_AddObjectRef(mod, "DTYPES", dtypes);
    Py_DECREF(dtypes);
    return rc;
}


static int stl_traverse(PyObject *mod, visitproc visit, void *arg) {
    stl_state *st = get_state(mod);
    if (st == nullptr) {
        return 0;
    }
    Py_VISIT(st->set_type);
    Py_VISIT(st->unordered_set_type);
    Py_VISIT(st->map_type);
    Py_VISIT(st->unordered_map_type);
    Py_VISIT(st->vector_type);
    Py_VISIT(st->iter_type);
    Py_VISIT(st->abc_set);
    Py_VISIT(st->abc_mapping);
    Py_VISIT(st->abc_keys_view);
    Py_VISIT(st->abc_values_view);
    Py_VISIT(st->abc_items_view);
    return 0;
}


static int stl_clear(PyObject *mod) {
    stl_state *st = get_state(mod);
    if (st == nullptr) {
        return 0;
    }
    Py_CLEAR(st->set_type);
    Py_CLEAR(st->unordered_set_type);
    Py_CLEAR(st->map_type);
    Py_CLEAR(st->unordered_map_type);
    Py_CLEAR(st->vector_type);
    Py_CLEAR(st->iter_type);
    Py_CLEAR(st->abc_set);
    Py_CLEAR(st->abc_mapping);
    Py_CLEAR(st->abc_keys_view);
    Py_CLEAR(st->abc_values_view);
    Py_CLEAR(st->abc_items_view);
    return 0;
}


static void stl_free(void *mod) {
    (void)stl_clear((PyObject *)mod);
}


static PyModuleDef_Slot stl_slots[] = {
    {Py_mod_exec, (void *)stl_exec},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, nullptr},
};


static struct PyModuleDef stl_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_FULL_NAME,
    .m_doc = PyDoc_STR("fastutil-style dtype-specialized sorted/hashed sets, maps, and vectors."),
    .m_size = (Py_ssize_t)sizeof(stl_state),
    .m_methods = nullptr,
    .m_slots = stl_slots,
    .m_traverse = stl_traverse,
    .m_clear = stl_clear,
    .m_free = stl_free,
};


static struct PyModuleDef *stl_module_def() {
    return &stl_module;
}


extern "C" {

PyMODINIT_FUNC PyInit__stl(void) {
    return PyModuleDef_Init(&stl_module);
}

}
