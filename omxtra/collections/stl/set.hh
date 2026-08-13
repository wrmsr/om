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
