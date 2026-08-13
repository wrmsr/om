#pragma once

#include "base.hh"

#include <map>
#include <unordered_map>


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
// Impl factories
//


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


inline MapLikeImpl *new_map_impl(ColKind kind, Dt kd, Ovf kovf, Dt vd, Ovf vovf) {
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

