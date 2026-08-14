#pragma once

#include "base.hh"

#include <set>
#include <unordered_set>


//
// Sets
//


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


//
// Sorted set
//


template <typename K>
struct SortedSetImpl final : SetLikeImpl {
    using Cont = std::set<typename K::Slot, typename K::Less, PyMemAllocator<typename K::Slot>>;

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
    using Cont = std::unordered_set<
        typename K::Slot,
        typename K::Hash,
        typename K::Eq,
        PyMemAllocator<typename K::Slot>>;

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

    void reserve_extra(size_t n) override {
        set_.reserve(set_.size() + n);
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
        if (o != this) {
            // Presize once instead of paying incremental rehashes across the bulk insert; safe pre-mutation, and
            // skipped for self-merge (which inserts nothing).
            set_.reserve(set_.size() + o->set_.size());
        }
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
// Impl factories
//


inline SetLikeImpl *new_set_impl(ColKind kind, Dt dt, Ovf ovf) {
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


//
// Python interface
//


inline bool is_our_set(stl_state *st, PyObject *o) {
    return PyObject_TypeCheck(o, st->set_type) || PyObject_TypeCheck(o, st->unordered_set_type);
}


inline int set_contains_obj(ColObject *co, PyObject *o) {
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->contains_(o); });
}


inline int set_add_obj(ColObject *co, PyObject *o) {
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->add_(o); });
}


// 1 removed / 0 absent / -1.
inline int set_discard_obj(ColObject *co, PyObject *o) {
    Bin bin;
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<SetLikeImpl *>(co->impl)->discard_(o, bin); });
}


// Batch path for exact list / tuple sources: one lock acquisition for the whole run instead of one per element.
// Element code runs under the held lock exactly as it would per-element (object dtypes call __hash__ / __lt__ /
// __eq__, primitive unboxing may call __index__), and such code can reach back and mutate a plain list source
// mid-loop - so lists are snapshotted into a private tuple (a C-level copy, no user hooks) first. Tuples are
// immutable and are used as-is. Error semantics match the per-element path: elements before the failing one stay
// added.
inline int set_extend_from_fast_seq(ColObject *co, PyObject *items) {
    PyObject *seq;
    if (PyTuple_CheckExact(items)) {
        seq = Py_NewRef(items);
    }
    else {
        seq = PyList_AsTuple(items);
        if (seq == nullptr) {
            return -1;
        }
    }
    int r;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            Py_DECREF(seq);
            return -1;
        }
        r = py_shield_int([&] {
            SetLikeImpl *impl = static_cast<SetLikeImpl *>(co->impl);
            Py_ssize_t sn = PyTuple_GET_SIZE(seq);
            impl->reserve_extra((size_t)sn);
            for (Py_ssize_t i = 0; i < sn; ++i) {
                if (impl->add_(PyTuple_GET_ITEM(seq, i)) < 0) {
                    return -1;
                }
            }
            return 0;
        });
    }
    Py_DECREF(seq);
    return r;
}


inline int set_extend_from(stl_state *st, ColObject *co, PyObject *items) {
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

    if (PyList_CheckExact(items) || PyTuple_CheckExact(items)) {
        return set_extend_from_fast_seq(co, items);
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


inline PyObject *set_new_like(stl_state *st, ColObject *like) {
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


inline int set_init_impl(PyObject *self, PyObject *args, PyObject *kwds, ColKind kind) {
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

    SetLikeImpl *impl;
    try {
        impl = new_set_impl(kind, ds.dt, ds.ovf);
    }
    catch (std::bad_alloc &) {
        PyErr_NoMemory();
        return -1;
    }
    if (col_publish_impl(co, impl) < 0) {
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


inline int set_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return set_init_impl(self, args, kwds, ColKind::SORTED_SET);
}


inline int unordered_set_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return set_init_impl(self, args, kwds, ColKind::HASH_SET);
}


inline int set_sq_contains(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return -1;
    }
    return set_contains_obj(co, o);
}


inline PyObject *set_add(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (set_add_obj(co, o) < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


inline PyObject *set_discard(PyObject *self, PyObject *o) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (set_discard_obj(co, o) < 0) {
        return nullptr;
    }
    Py_RETURN_NONE;
}


inline PyObject *set_remove(PyObject *self, PyObject *o) {
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


inline PyObject *set_pop(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *set_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *set_update(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    for (Py_ssize_t i = 0; i < nargs; ++i) {
        if (set_extend_from(st, co, args[i]) < 0) {
            return nullptr;
        }
    }
    Py_RETURN_NONE;
}


inline PyObject *set_isdisjoint(PyObject *self, PyObject *other) {
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
inline int set_issubset_of(PyObject *sub, PyObject *sup) {
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


inline PyObject *set_richcompare(PyObject *self, PyObject *other, int op) {
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
inline PyObject *set_binop(PyObject *v, PyObject *w, char op) {
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


inline PyObject *set_nb_or(PyObject *v, PyObject *w) {
    return set_binop(v, w, '|');
}


inline PyObject *set_nb_and(PyObject *v, PyObject *w) {
    return set_binop(v, w, '&');
}


inline PyObject *set_nb_sub(PyObject *v, PyObject *w) {
    return set_binop(v, w, '-');
}


inline PyObject *set_nb_xor(PyObject *v, PyObject *w) {
    return set_binop(v, w, '^');
}


// A failed inplace update should degrade to NotImplemented only when the right operand is not iterable at all
// (abc.MutableSet semantics); a TypeError raised by an *element* must propagate. The pending exception is stashed
// around the iterability probe - calling into the API with the error indicator set is illegal - and a successful
// probe's iterator is released rather than leaked.
inline bool set_inplace_rhs_not_iterable(PyObject *w) {
    if (!PyErr_ExceptionMatches(PyExc_TypeError)) {
        return false;
    }
    PyObject *exc = PyErr_GetRaisedException();
    PyObject *probe = PyObject_GetIter(w);
    if (probe == nullptr) {
        PyErr_Clear();
        Py_DECREF(exc);
        return true;
    }
    Py_DECREF(probe);
    PyErr_SetRaisedException(exc);
    return false;
}


inline PyObject *set_inplace(PyObject *v, PyObject *w, char op) {
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
                if (set_inplace_rhs_not_iterable(w)) {
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
                if (set_inplace_rhs_not_iterable(w)) {
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


inline PyObject *set_nb_ior(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '|');
}


inline PyObject *set_nb_iand(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '&');
}


inline PyObject *set_nb_isub(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '-');
}


inline PyObject *set_nb_ixor(PyObject *v, PyObject *w) {
    return set_inplace(v, w, '^');
}


inline PyObject *set_repr(PyObject *self) {
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


inline PyObject *col_get_dtype(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
}


inline PyGetSetDef set_getset[] = {
    {"dtype", col_get_dtype, nullptr, PyDoc_STR("Canonical element dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};


// Pickle / copy support: reduce to the public constructor form - (cls, (dtype, [elements]), state) - the same shape
// as the repr. Elements are inlined into the constructor args because pickle's listitems protocol needs an append /
// extend method, which sets do not have; a (degenerate) self-containing set therefore cannot be pickled - the
// pickler recurses on the args and raises rather than anything worse.
inline PyObject *set_reduce(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *items = PySequence_List(self);
    if (items == nullptr) {
        return nullptr;
    }
    PyObject *dt = PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
    if (dt == nullptr) {
        Py_DECREF(items);
        return nullptr;
    }
    PyObject *args = PyTuple_Pack(2, dt, items);
    Py_DECREF(dt);
    Py_DECREF(items);
    if (args == nullptr) {
        return nullptr;
    }
    PyObject *state = col_reduce_state(self);
    if (state == nullptr) {
        Py_DECREF(args);
        return nullptr;
    }
    PyObject *r = PyTuple_Pack(3, (PyObject *)Py_TYPE(self), args, state);
    Py_DECREF(args);
    Py_DECREF(state);
    return r;
}


// SortedCollection surface (sorted variant only): iter / iter_desc are just the existing iterators under the interface
// names; the seeded and find forms ride the new impl primitives.
inline PyObject *set_iter_from(PyObject *self, PyObject *base) {
    return col_make_iter_from(self, IterKind::KEYS, false, base);
}


inline PyObject *set_iter_from_desc(PyObject *self, PyObject *base) {
    return col_make_iter_from(self, IterKind::KEYS, true, base);
}


inline PyObject *set_find(PyObject *self, PyObject *probe) {
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
