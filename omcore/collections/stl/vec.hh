#pragma once

#include "base.hh"

#include <vector>


//
// Vecs
//


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
// Vector
//


template <typename E>
struct VectorImpl final : VecLikeImpl {
    using Vec = std::vector<typename E::Slot, PyMemAllocator<typename E::Slot>>;

    Vec vec_;

    VectorImpl(Dt dt, Ovf ovf)
        : VecLikeImpl(ColKind::VECTOR, dt, ovf, dt, ovf) {}

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
        PyObject *o = E::box(key_dt, vec_[(size_t)i]);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 0;
    }

    int set_at(Py_ssize_t i, PyObject *v, Bin &bin) override {
        typename E::Slot s{};
        if (!E::unbox(v, key_dt, key_ovf, &s)) {
            return -1;
        }
        E::release_into(vec_[(size_t)i], bin);
        vec_[(size_t)i] = s;
        E::retain(vec_[(size_t)i]);
        return 0;
    }

    int insert_at(Py_ssize_t i, PyObject *v) override {
        typename E::Slot s{};
        if (!E::unbox(v, key_dt, key_ovf, &s)) {
            return -1;
        }
        vec_.insert(vec_.begin() + i, s);
        E::retain(vec_[(size_t)i]);
        ++version;
        return 0;
    }

    int pop_at(Py_ssize_t i, PyObject **out_opt, Bin &bin) override {
        if (out_opt != nullptr) {
            PyObject *o = E::box(key_dt, vec_[(size_t)i]);
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
        if (!E::unbox(v, key_dt, key_ovf, &s)) {
            return -1;
        }
        vec_.push_back(s);
        E::retain(vec_.back());
        ++version;
        return 0;
    }

    int find_(PyObject *probe, Py_ssize_t start, Py_ssize_t stop, Py_ssize_t *at) override {
        typename E::Slot s{};
        int r = unbox_probe<E>(probe, key_dt, key_ovf, &s);
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
        int r = unbox_probe<E>(probe, key_dt, key_ovf, &s);
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
        if constexpr (E::IS_OBJ) {
            // Object sorts deliberately do NOT use std::sort. They round-trip through a temporary list and CPython's
            // listsort instead, which is INEFFICIENT - an extra O(n) list allocation plus a refcount round-trip per
            // element, per sort - and that cost is accepted on purpose: std::sort (like every STL ordering algorithm)
            // is undefined behavior whenever its comparator is not a strict weak ordering - concretely, out-of-bounds
            // reads *and writes* inside libstdc++'s introsort, i.e. native heap corruption - and an arbitrary Python
            // __lt__ can return anything at all, including inconsistent answers. Pure Python code must never be able
            // to corrupt native memory. CPython's listsort is engineered to stay memory-safe (merely producing a
            // garbage order) under arbitrary, even adversarial, comparators, so it does the comparing. A side
            // benefit: object sorts are stable, exactly like list.sort.
            PyObject *lst = PyList_New((Py_ssize_t)n);
            if (lst == nullptr) {
                return -1;
            }
            for (size_t i = 0; i < n; ++i) {
                PyList_SET_ITEM(lst, (Py_ssize_t)i, Py_NewRef(vec_[i]));
            }
            // reverse-sort-reverse is exactly list.sort(reverse=True): with a stable sort the two reversals preserve
            // the original relative order of equal elements while ordering the groups descending.
            int rc = reverse ? PyList_Reverse(lst) : 0;
            if (rc == 0) {
                rc = PyList_Sort(lst);
            }
            if (rc == 0 && reverse) {
                rc = PyList_Reverse(lst);
            }
            if (rc < 0) {
                Py_DECREF(lst);
                return -1;  // vec_ untouched: a raising comparator leaves the vector unchanged
            }
            // The list holds the same multiset of pointers, permuted: vec_'s own references simply move to their new
            // positions, and the list's extra references die with it.
            for (size_t i = 0; i < n; ++i) {
                vec_[i] = PyList_GET_ITEM(lst, (Py_ssize_t)i);
            }
            Py_DECREF(lst);
        }
        else {
            typename E::Less less;
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
        auto *n = new VectorImpl(key_dt, key_ovf);
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
            Vec out;
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
        Vec out;
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
        auto *n = new VectorImpl(key_dt, key_ovf);
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
        PyObject *o = E::box(impl->key_dt, impl->vec_[(size_t)idx]);
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


inline VecLikeImpl *new_vec_impl(Dt dt, Ovf ovf) {
    switch (dt) {
        case Dt::U64:
        case Dt::I64:
        case Dt::F64:
            return new VectorImpl<Canon64Traits>(dt, ovf);
        case Dt::I32:
        case Dt::F32:
            return new VectorImpl<Canon32Traits>(dt, ovf);
        case Dt::I16:
            return new VectorImpl<Canon16Traits>(dt, ovf);
        case Dt::OBJ:
            return new VectorImpl<ObjectTraits>(dt, ovf);
    }
    Py_UNREACHABLE();
}


//
// Python interface
//


inline VecLikeImpl *vec_impl(ColObject *co) {
    return static_cast<VecLikeImpl *>(co->impl);
}


// Builds a private (unshared, unlocked) same-spec VectorImpl holding the elements of src. Used as the right-hand side
// of slice assignment and generic extend, so the actual splice can run as one no-throw step under self's lock.
inline VecLikeImpl *vec_materialize(stl_state *st, ColObject *co, PyObject *src) {
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


inline int vec_extend_from(stl_state *st, ColObject *co, PyObject *src) {
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


inline int vec_init(PyObject *self, PyObject *args, PyObject *kwds) {
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

    VecLikeImpl *impl;
    try {
        impl = new_vec_impl(ds.dt, ds.ovf);
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
        if (vec_extend_from(st, co, items) < 0) {
            return -1;
        }
    }
    return 0;
}


inline PyObject *vec_get_index(ColObject *co, PyObject *self, Py_ssize_t i, bool adjust_negative) {
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


inline PyObject *vec_sq_item(PyObject *self, Py_ssize_t i) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return vec_get_index(co, self, i, false);
}


inline PyObject *vec_subscript(PyObject *self, PyObject *key) {
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


inline int vec_ass_subscript(PyObject *self, PyObject *key, PyObject *v) {
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


inline int vec_sq_contains(PyObject *self, PyObject *o) {
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


inline PyObject *vec_append(PyObject *self, PyObject *o) {
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


inline PyObject *vec_extend(PyObject *self, PyObject *o) {
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


inline PyObject *vec_nb_iadd(PyObject *v, PyObject *w) {
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


inline PyObject *vec_insert(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (nargs != 2) {
        PyErr_Format(PyExc_TypeError, "insert expected 2 arguments, got %zd", nargs);
        return nullptr;
    }
    Py_ssize_t i = PyNumber_AsSsize_t(args[0], PyExc_OverflowError);
    if (i == -1 && PyErr_Occurred() != nullptr) {
        return nullptr;
    }
    PyObject *v = args[1];
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


inline PyObject *vec_pop(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (nargs > 1) {
        PyErr_Format(PyExc_TypeError, "pop expected at most 1 argument, got %zd", nargs);
        return nullptr;
    }
    Py_ssize_t i = -1;
    if (nargs == 1) {
        i = PyNumber_AsSsize_t(args[0], PyExc_OverflowError);
        if (i == -1 && PyErr_Occurred() != nullptr) {
            return nullptr;
        }
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


inline PyObject *vec_remove(PyObject *self, PyObject *o) {
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


inline PyObject *vec_index_meth(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (nargs < 1 || nargs > 3) {
        PyErr_Format(PyExc_TypeError, "index expected 1 to 3 arguments, got %zd", nargs);
        return nullptr;
    }
    PyObject *v = args[0];
    Py_ssize_t start = 0;
    Py_ssize_t stop = PY_SSIZE_T_MAX;
    if (nargs > 1) {
        start = PyNumber_AsSsize_t(args[1], PyExc_OverflowError);
        if (start == -1 && PyErr_Occurred() != nullptr) {
            return nullptr;
        }
    }
    if (nargs > 2) {
        stop = PyNumber_AsSsize_t(args[2], PyExc_OverflowError);
        if (stop == -1 && PyErr_Occurred() != nullptr) {
            return nullptr;
        }
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


inline PyObject *vec_count(PyObject *self, PyObject *o) {
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


inline PyObject *vec_reverse(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *vec_sort(PyObject *self, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    if (nargs > 0) {
        PyErr_Format(PyExc_TypeError, "sort takes no positional arguments (%zd given)", nargs);
        return nullptr;
    }
    int reverse = 0;
    if (kwnames != nullptr) {
        Py_ssize_t nk = PyTuple_GET_SIZE(kwnames);
        for (Py_ssize_t i = 0; i < nk; ++i) {
            PyObject *name = PyTuple_GET_ITEM(kwnames, i);
            if (PyUnicode_EqualToUTF8(name, "reverse") != 1) {
                PyErr_Format(PyExc_TypeError, "sort got an unexpected keyword argument %R", name);
                return nullptr;
            }
            reverse = PyObject_IsTrue(args[i]);
            if (reverse < 0) {
                return nullptr;
            }
        }
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


inline PyObject *vec_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *vec_richcompare(PyObject *self, PyObject *other, int op) {
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


// Pickle / copy support: (cls, (dtype,), state, elements_iterator, None). Contents go through pickle's listitems
// protocol - applied element-wise via append after the empty vector is created and memoized - so self-referential
// vectors round-trip.
inline PyObject *vec_reduce(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *dt = PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
    if (dt == nullptr) {
        return nullptr;
    }
    PyObject *args = PyTuple_Pack(1, dt);
    Py_DECREF(dt);
    if (args == nullptr) {
        return nullptr;
    }
    PyObject *state = col_reduce_state(self);
    if (state == nullptr) {
        Py_DECREF(args);
        return nullptr;
    }
    PyObject *it = col_iter(self);
    if (it == nullptr) {
        Py_DECREF(args);
        Py_DECREF(state);
        return nullptr;
    }
    PyObject *r = PyTuple_Pack(5, (PyObject *)Py_TYPE(self), args, state, it, Py_None);
    Py_DECREF(args);
    Py_DECREF(state);
    Py_DECREF(it);
    return r;
}


inline PyObject *vec_repr(PyObject *self) {
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
