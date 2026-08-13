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


inline VecLikeImpl *new_vec_impl(Dt dt, Ovf ovf) {
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

