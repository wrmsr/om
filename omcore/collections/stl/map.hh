#pragma once

#include "base.hh"

#include "ankerl/include/ankerl/unordered_dense.h"
#include "tlx/tlx/container/btree_map.hpp"


//
// Maps
//


struct MapLikeImpl : AnyImpl {
    using AnyImpl::AnyImpl;

    virtual int contains_(PyObject *k) = 0;                                   // 1 / 0 / -1
    virtual int lookup(PyObject *k, PyObject **out) = 0;                      // 1 (new ref) / 0 / -1
    virtual int assign(PyObject *k, PyObject *v, Bin &bin) = 0;               // 0 / -1
    virtual int remove_(PyObject *k, PyObject **out_opt, Bin &bin) = 0;       // 1 / 0 / -1
    virtual int pop_item(PyObject **k_out, PyObject **v_out, Bin &bin) = 0;   // 1 / 0 empty / -1
    virtual int set_default(PyObject *k, PyObject *d, PyObject **out) = 0;    // 0 (new ref) / -1
};


//
// Sorted map
//


template <typename K, typename V>
struct SortedMapImpl final : MapLikeImpl {
    using Cont = tlx::btree_map<
        typename K::Slot,
        typename V::Slot,
        typename K::Less,
        BtreeTraitsFor<K, std::pair<typename K::Slot, typename V::Slot>>,
        PyMemAllocator<std::pair<typename K::Slot, typename V::Slot>>>;

    Cont map_;

    SortedMapImpl(Dt kd, Ovf kovf, Dt vd, Ovf vovf)
        : MapLikeImpl(ColKind::SORTED_MAP, kd, kovf, vd, vovf) {}

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
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        return map_.find(ks) != map_.end() ? 1 : 0;
    }

    int lookup(PyObject *k, PyObject **out) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        PyObject *o = V::box(val_dt, it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int assign(PyObject *k, PyObject *v, Bin &bin) override {
        typename K::Slot ks{};
        if (!K::unbox(k, key_dt, key_ovf, &ks)) {
            return -1;
        }
        typename V::Slot vs{};
        if (!V::unbox(v, val_dt, val_ovf, &vs)) {
            return -1;
        }
        auto [it, inserted] = map_.insert2(ks, vs);  // insert-if-absent, tlx's try_emplace equivalent
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
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        if constexpr (!K::IS_OBJ && !V::IS_OBJ) {
            // No reference bookkeeping for fully-primitive entries: when the value is not wanted back, the
            // single-descent erase-by-key beats the find-then-erase(iterator) double descent.
            if (out_opt == nullptr) {
                if (!map_.erase_one(ks)) {
                    return 0;
                }
                ++version;
                return 1;
            }
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        // Box before erasing so a boxing failure leaves the entry untouched.
        PyObject *o = nullptr;
        if (out_opt != nullptr) {
            o = V::box(val_dt, it->second);
            if (o == nullptr) {
                return -1;
            }
        }
        // Erase before releasing: the btree's erase(iterator) re-descends by key and can throw a comparator error,
        // so the references must not be moved into the bin until the erase has actually succeeded.
        typename K::Slot kslot = it->first;
        typename V::Slot vslot = it->second;
        try {
            map_.erase(it);
        }
        catch (...) {
            Py_XDECREF(o);
            throw;
        }
        K::release_into(kslot, bin);
        V::release_into(vslot, bin);
        ++version;
        if (out_opt != nullptr) {
            *out_opt = o;
        }
        return 1;
    }

    int pop_item(PyObject **k_out, PyObject **v_out, Bin &bin) override {
        if (map_.empty()) {
            return 0;
        }
        auto it = std::prev(map_.end());  // last (greatest) item, sorted-dict flavor
        PyObject *ko = K::box(key_dt, it->first);
        if (ko == nullptr) {
            return -1;
        }
        PyObject *vo = V::box(val_dt, it->second);
        if (vo == nullptr) {
            Py_DECREF(ko);
            return -1;
        }
        // Erase before releasing, as in remove_.
        typename K::Slot kslot = it->first;
        typename V::Slot vslot = it->second;
        try {
            map_.erase(it);
        }
        catch (...) {
            Py_DECREF(ko);
            Py_DECREF(vo);
            throw;
        }
        K::release_into(kslot, bin);
        V::release_into(vslot, bin);
        ++version;
        *k_out = ko;
        *v_out = vo;
        return 1;
    }

    int set_default(PyObject *k, PyObject *d, PyObject **out) override {
        // Insertion may occur, so the key gets full (non-probe) unboxing, like dict.setdefault.
        typename K::Slot ks{};
        if (!K::unbox(k, key_dt, key_ovf, &ks)) {
            return -1;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            // The default is unboxed only if it is actually going to be inserted, dict-style.
            typename V::Slot vs{};
            if (!V::unbox(d, val_dt, val_ovf, &vs)) {
                return -1;
            }
            auto er = map_.insert2(ks, vs);
            it = er.first;
            // An inconsistent user comparator can make the find above miss while this insert still lands on an
            // existing entry - only take ownership of what was actually inserted.
            if (er.second) {
                K::retain(it->first);
                V::retain(it->second);
                ++version;
            }
        }
        PyObject *o = V::box(val_dt, it->second);
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
        auto *n = new SortedMapImpl(key_dt, key_ovf, val_dt, val_ovf);
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
            auto [it, inserted] = map_.insert2(e.first, e.second);
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
                o = V::box(impl->val_dt, cur->second);
                break;
            case IterKind::ITEMS: {
                PyObject *ko = K::box(impl->key_dt, cur->first);
                if (ko == nullptr) {
                    return -1;
                }
                PyObject *vo = V::box(impl->val_dt, cur->second);
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
                o = K::box(impl->key_dt, cur->first);
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
    r->it = desc ? map_.end() : map_.begin();  // tlx btree has no cbegin/cend; converts to const_iterator
    r->expect = version;
    r->ik = ik;
    r->rev = desc;
    return r;
}


template <typename K, typename V>
AnyIter *SortedMapImpl<K, V>::make_iter_from(IterKind ik, bool desc, PyObject *base) {
    typename K::Slot ks{};
    if (!K::unbox(base, key_dt, key_ovf, &ks)) {
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
    using Cont = ankerl::unordered_dense::map<
        typename K::Slot,
        typename V::Slot,
        typename K::Hash,
        typename K::Eq,
        PyMemAllocator<std::pair<typename K::Slot, typename V::Slot>>>;

    Cont map_;

    HashMapImpl(Dt kd, Ovf kovf, Dt vd, Ovf vovf)
        : MapLikeImpl(ColKind::HASH_MAP, kd, kovf, vd, vovf) {}

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
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        return map_.find(ks) != map_.end() ? 1 : 0;
    }

    int lookup(PyObject *k, PyObject **out) override {
        typename K::Slot ks{};
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        PyObject *o = V::box(val_dt, it->second);
        if (o == nullptr) {
            return -1;
        }
        *out = o;
        return 1;
    }

    int assign(PyObject *k, PyObject *v, Bin &bin) override {
        typename K::Slot ks{};
        if (!K::unbox(k, key_dt, key_ovf, &ks)) {
            return -1;
        }
        typename V::Slot vs{};
        if (!V::unbox(v, val_dt, val_ovf, &vs)) {
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
        int r = unbox_probe<K>(k, key_dt, key_ovf, &ks);
        if (r <= 0) {
            return r;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            return 0;
        }
        if (out_opt != nullptr) {
            PyObject *o = V::box(val_dt, it->second);
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
        PyObject *ko = K::box(key_dt, it->first);
        if (ko == nullptr) {
            return -1;
        }
        PyObject *vo = V::box(val_dt, it->second);
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
        if (!K::unbox(k, key_dt, key_ovf, &ks)) {
            return -1;
        }
        auto it = map_.find(ks);
        if (it == map_.end()) {
            typename V::Slot vs{};
            if (!V::unbox(d, val_dt, val_ovf, &vs)) {
                return -1;
            }
            auto er = map_.try_emplace(ks, vs);
            it = er.first;
            // An inconsistent user __eq__ can make the find above miss while this emplace still lands on an existing
            // node - only take ownership of what was actually inserted.
            if (er.second) {
                K::retain(it->first);
                V::retain(it->second);
                ++version;
            }
        }
        PyObject *o = V::box(val_dt, it->second);
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

    void reserve_extra(size_t n) override {
        map_.reserve(map_.size() + n);
    }

    AnyImpl *clone() const override {
        auto *n = new HashMapImpl(key_dt, key_ovf, val_dt, val_ovf);
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
        if (o != this) {
            // Presize once instead of paying incremental rehashes across the bulk insert; safe pre-mutation, and
            // skipped for self-merge (which inserts nothing).
            map_.reserve(map_.size() + o->map_.size());
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
                o = K::box(impl->key_dt, it->first);
                break;
            case IterKind::VALUES:
                o = V::box(impl->val_dt, it->second);
                break;
            default: {
                PyObject *ko = K::box(impl->key_dt, it->first);
                if (ko == nullptr) {
                    return -1;
                }
                PyObject *vo = V::box(impl->val_dt, it->second);
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
// Impl factories
//


template <typename K>
static MapLikeImpl *new_sorted_map_impl(Dt kd, Ovf kovf, Dt vd, Ovf vovf) {
    switch (vd) {
        case Dt::U64:
        case Dt::I64:
        case Dt::F64:
            return new SortedMapImpl<K, Canon64Traits>(kd, kovf, vd, vovf);
        case Dt::I32:
        case Dt::F32:
            return new SortedMapImpl<K, Canon32Traits>(kd, kovf, vd, vovf);
        case Dt::I16:
            return new SortedMapImpl<K, Canon16Traits>(kd, kovf, vd, vovf);
        case Dt::OBJ:
            return new SortedMapImpl<K, ObjectTraits>(kd, kovf, vd, vovf);
    }
    Py_UNREACHABLE();
}


template <typename K>
static MapLikeImpl *new_hash_map_impl(Dt kd, Ovf kovf, Dt vd, Ovf vovf) {
    switch (vd) {
        case Dt::U64:
        case Dt::I64:
        case Dt::F64:
            return new HashMapImpl<K, Canon64Traits>(kd, kovf, vd, vovf);
        case Dt::I32:
        case Dt::F32:
            return new HashMapImpl<K, Canon32Traits>(kd, kovf, vd, vovf);
        case Dt::I16:
            return new HashMapImpl<K, Canon16Traits>(kd, kovf, vd, vovf);
        case Dt::OBJ:
            return new HashMapImpl<K, ObjectTraits>(kd, kovf, vd, vovf);
    }
    Py_UNREACHABLE();
}


inline MapLikeImpl *new_map_impl(ColKind kind, Dt kd, Ovf kovf, Dt vd, Ovf vovf) {
    if (kind == ColKind::SORTED_MAP) {
        switch (kd) {
            case Dt::U64:
            case Dt::I64:
            case Dt::F64:
                return new_sorted_map_impl<Canon64Traits>(kd, kovf, vd, vovf);
            case Dt::I32:
            case Dt::F32:
                return new_sorted_map_impl<Canon32Traits>(kd, kovf, vd, vovf);
            case Dt::I16:
                return new_sorted_map_impl<Canon16Traits>(kd, kovf, vd, vovf);
            case Dt::OBJ:
                return new_sorted_map_impl<ObjectTraits>(kd, kovf, vd, vovf);
        }
        Py_UNREACHABLE();
    }
    switch (kd) {
        case Dt::U64:
        case Dt::I64:
        case Dt::F64:
            return new_hash_map_impl<Canon64Traits>(kd, kovf, vd, vovf);
        case Dt::I32:
        case Dt::F32:
            return new_hash_map_impl<Canon32Traits>(kd, kovf, vd, vovf);
        case Dt::I16:
            return new_hash_map_impl<Canon16Traits>(kd, kovf, vd, vovf);
        case Dt::OBJ:
            return new_hash_map_impl<HashedObjectTraits>(kd, kovf, vd, vovf);
    }
    Py_UNREACHABLE();
}


//
// Python interface
//


inline bool is_our_map(stl_state *st, PyObject *o) {
    return PyObject_TypeCheck(o, st->map_type) || PyObject_TypeCheck(o, st->unordered_map_type);
}


inline int map_assign_obj(ColObject *co, PyObject *k, PyObject *v) {
    Bin bin;
    ColGuard g(co->impl);
    if (!g.held()) {
        return -1;
    }
    return py_shield_int([&] { return static_cast<MapLikeImpl *>(co->impl)->assign(k, v, bin); });
}


// Batch path for pair sources that are an exact list / tuple of exact 2-tuples (notably PyDict_Items snapshots and
// literal pair lists): one lock acquisition for the whole run instead of one per pair. As with the set batch path,
// element code (unboxing / hashing / comparators) runs under the held lock and could mutate a plain list source, so
// lists are snapshotted into a private tuple first; the exact-2-tuple pre-scan means no user code runs when pairs
// are pulled apart under the lock. Returns 1 handled, 0 not applicable (caller falls back to the generic walk,
// which also reproduces the malformed-element errors), -1 error.
inline int map_update_pairs_fast_seq(ColObject *co, PyObject *pairs) {
    PyObject *seq;
    if (PyTuple_CheckExact(pairs)) {
        seq = Py_NewRef(pairs);
    }
    else if (PyList_CheckExact(pairs)) {
        seq = PyList_AsTuple(pairs);
        if (seq == nullptr) {
            return -1;
        }
    }
    else {
        return 0;
    }
    Py_ssize_t sn = PyTuple_GET_SIZE(seq);
    for (Py_ssize_t i = 0; i < sn; ++i) {
        PyObject *pair = PyTuple_GET_ITEM(seq, i);
        if (!PyTuple_CheckExact(pair) || PyTuple_GET_SIZE(pair) != 2) {
            Py_DECREF(seq);
            return 0;
        }
    }
    int r;
    Bin bin;
    {
        ColGuard g(co->impl);
        if (!g.held()) {
            Py_DECREF(seq);
            return -1;
        }
        r = py_shield_int([&] {
            MapLikeImpl *impl = static_cast<MapLikeImpl *>(co->impl);
            impl->reserve_extra((size_t)sn);
            if (impl->val_dt == Dt::OBJ) {
                bin.reserve_rest((size_t)sn);
            }
            for (Py_ssize_t i = 0; i < sn; ++i) {
                PyObject *pair = PyTuple_GET_ITEM(seq, i);
                if (impl->assign(PyTuple_GET_ITEM(pair, 0), PyTuple_GET_ITEM(pair, 1), bin) < 0) {
                    return -1;
                }
            }
            return 0;
        });
    }
    Py_DECREF(seq);
    return r < 0 ? -1 : 1;
}


// Update from an iterable of key/value pairs.
inline int map_update_pairs(ColObject *co, PyObject *pairs) {
    int fr = map_update_pairs_fast_seq(co, pairs);
    if (fr != 0) {
        return fr < 0 ? -1 : 0;
    }

    PyObject *it = PyObject_GetIter(pairs);
    if (it == nullptr) {
        return -1;
    }
    PyObject *pair;
    while ((pair = PyIter_Next(it)) != nullptr) {
        // Snapshot each pair into an owned tuple rather than borrowing its items PySequence_Fast-style: a list pair
        // can be shared, and the assign below both runs user code (__hash__ / __lt__ / __index__) and can block on
        // the container lock with the thread state released - windows in which other code can drop the pair's items
        // and free them out from under an unretained borrowed pointer. The snapshot pins the items (and freezes the
        // length check); for tuple pairs it is just an incref, exactly as PySequence_Fast was.
        PyObject *fast = PySequence_Tuple(pair);
        Py_DECREF(pair);
        if (fast == nullptr) {
            if (PyErr_ExceptionMatches(PyExc_TypeError)) {
                PyErr_SetString(PyExc_TypeError, "map update sequence element is not iterable");
            }
            Py_DECREF(it);
            return -1;
        }
        if (PyTuple_GET_SIZE(fast) != 2) {
            PyErr_Format(
                PyExc_ValueError,
                "map update sequence element has length %zd; 2 is required",
                PyTuple_GET_SIZE(fast));
            Py_DECREF(fast);
            Py_DECREF(it);
            return -1;
        }
        int r = map_assign_obj(co, PyTuple_GET_ITEM(fast, 0), PyTuple_GET_ITEM(fast, 1));
        Py_DECREF(fast);
        if (r < 0) {
            Py_DECREF(it);
            return -1;
        }
    }
    Py_DECREF(it);
    return PyErr_Occurred() != nullptr ? -1 : 0;
}


inline int map_update_from(stl_state *st, ColObject *co, PyObject *src) {
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


inline int map_init_impl(PyObject *self, PyObject *args, PyObject *kwds, ColKind kind) {
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

    MapLikeImpl *impl;
    try {
        impl = new_map_impl(kind, kd.dt, kd.ovf, vd.dt, vd.ovf);
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
        if (map_update_from(st, co, items) < 0) {
            return -1;
        }
    }
    return 0;
}


inline int map_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return map_init_impl(self, args, kwds, ColKind::SORTED_MAP);
}


inline int unordered_map_init(PyObject *self, PyObject *args, PyObject *kwds) {
    return map_init_impl(self, args, kwds, ColKind::HASH_MAP);
}


inline PyObject *map_subscript(PyObject *self, PyObject *k) {
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


inline int map_ass_subscript(PyObject *self, PyObject *k, PyObject *v) {
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


inline int map_sq_contains(PyObject *self, PyObject *k) {
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


// FASTCALL argument extraction for the (key, optional default) methods; *dflt is left untouched when absent so
// callers pick their own default (Py_None for get / setdefault, a raise sentinel for pop).
inline bool map_parse_key_opt(const char *name, PyObject *const *args, Py_ssize_t nargs, PyObject **k, PyObject **dflt) {
    if (nargs < 1) {
        PyErr_Format(PyExc_TypeError, "%s expected at least 1 argument, got %zd", name, nargs);
        return false;
    }
    if (nargs > 2) {
        PyErr_Format(PyExc_TypeError, "%s expected at most 2 arguments, got %zd", name, nargs);
        return false;
    }
    *k = args[0];
    if (nargs == 2) {
        *dflt = args[1];
    }
    return true;
}


inline PyObject *map_get(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = Py_None;
    if (!map_parse_key_opt("get", args, nargs, &k, &dflt)) {
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


inline PyObject *map_pop(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = nullptr;
    if (!map_parse_key_opt("pop", args, nargs, &k, &dflt)) {
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


inline PyObject *map_popitem(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *map_setdefault(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *k;
    PyObject *dflt = Py_None;
    if (!map_parse_key_opt("setdefault", args, nargs, &k, &dflt)) {
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


inline PyObject *map_update(PyObject *self, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    if (nargs > 1) {
        PyErr_Format(PyExc_TypeError, "update expected at most 1 argument, got %zd", nargs);
        return nullptr;
    }
    if (nargs == 1) {
        if (map_update_from(st, co, args[0]) < 0) {
            return nullptr;
        }
    }
    if (kwnames != nullptr) {
        Py_ssize_t nk = PyTuple_GET_SIZE(kwnames);
        for (Py_ssize_t i = 0; i < nk; ++i) {
            if (map_assign_obj(co, PyTuple_GET_ITEM(kwnames, i), args[nargs + i]) < 0) {
                return nullptr;
            }
        }
    }
    Py_RETURN_NONE;
}


inline PyObject *map_copy(PyObject *self, PyObject *Py_UNUSED(ignored)) {
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


inline PyObject *map_view(PyObject *self, PyObject *view_cls) {
    // The collections.abc view classes are the documented, protocol-driven implementation here: they wrap the
    // mapping and route everything through __iter__ / __getitem__ / __len__, and bring the Set mixin along for
    // keys() and items().
    return PyObject_CallOneArg(view_cls, self);
}


inline PyObject *map_keys(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_keys_view);
}


inline PyObject *map_values(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_values_view);
}


inline PyObject *map_items(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    stl_state *st = find_state(Py_TYPE(self));
    if (st == nullptr) {
        return nullptr;
    }
    return map_view(self, st->abc_items_view);
}


inline PyObject *map_richcompare(PyObject *self, PyObject *other, int op) {
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


inline PyObject *map_repr(PyObject *self) {
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


inline PyObject *map_get_key_type(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
}


inline PyObject *map_get_value_type(PyObject *self, void *) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    return PyUnicode_FromString(dtype_name(co->impl->val_dt, co->impl->val_ovf));
}


// Pickle / copy support: (cls, (key_type, value_type), state, None, items_iterator). Contents go through pickle's
// dictitems protocol - applied pair-wise via obj[k] = v after the empty map is created and memoized - so
// self-referential maps round-trip.
inline PyObject *map_reduce(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    ColObject *co = (ColObject *)self;
    if (!col_ready(co)) {
        return nullptr;
    }
    PyObject *kt = PyUnicode_FromString(dtype_name(co->impl->key_dt, co->impl->key_ovf));
    if (kt == nullptr) {
        return nullptr;
    }
    PyObject *vt = PyUnicode_FromString(dtype_name(co->impl->val_dt, co->impl->val_ovf));
    if (vt == nullptr) {
        Py_DECREF(kt);
        return nullptr;
    }
    PyObject *args = PyTuple_Pack(2, kt, vt);
    Py_DECREF(kt);
    Py_DECREF(vt);
    if (args == nullptr) {
        return nullptr;
    }
    PyObject *state = col_reduce_state(self);
    if (state == nullptr) {
        Py_DECREF(args);
        return nullptr;
    }
    PyObject *items_it = col_make_iter(self, IterKind::ITEMS, false);
    if (items_it == nullptr) {
        Py_DECREF(args);
        Py_DECREF(state);
        return nullptr;
    }
    PyObject *r = PyTuple_Pack(5, (PyObject *)Py_TYPE(self), args, state, Py_None, items_it);
    Py_DECREF(args);
    Py_DECREF(state);
    Py_DECREF(items_it);
    return r;
}


// SortedItems surface (sorted variant only).
inline PyObject *map_iteritems(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::ITEMS, false);
}


inline PyObject *map_items_desc(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return col_make_iter(self, IterKind::ITEMS, true);
}


inline PyObject *map_items_from(PyObject *self, PyObject *key) {
    return col_make_iter_from(self, IterKind::ITEMS, false, key);
}


inline PyObject *map_items_from_desc(PyObject *self, PyObject *key) {
    return col_make_iter_from(self, IterKind::ITEMS, true, key);
}
