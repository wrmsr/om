// @om-cext {
//   "extra_sources": [
//     "*.cc"
//   ],
//   "extra_headers": [
//     "*.hh"
//   ],
//   "extra_compile_args": [
//     "-fvisibility=hidden"
//   ]
// }
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#include "base.hh"
#include "map.hh"
#include "set.hh"
#include "vec.hh"


// fastutil-style primitive-specialized containers: Set / UnorderedSet / Map / UnorderedMap / Vector, each parameterized
// (per key / value position) over one of the dtypes 'object', 'int64-{raise,clamp,wrap}', 'uint64-{raise,clamp,wrap}',
// or 'float64'. Primitive dtypes are stored unboxed (as int64_t / uint64_t / double) and box/unbox only at the Python
// boundary; 'object' stores owned PyObject* references and participates fully in GC. Each combination is a distinct
// C++ template instantiation, so the loops that drive lookups, bulk merges, comparisons, sorts, and slices are fully
// type-specialized - the only per-element indirection anywhere is the unavoidable one at the Python boundary itself.


static struct PyModuleDef *stl_module_def();


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
