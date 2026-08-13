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


//
// Iterator type
//


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


//
// Set / UnorderedSet
//


static PyMethodDef set_methods[] = {
    {"add", set_add, METH_O, PyDoc_STR("Add an element.")},
    {"discard", set_discard, METH_O, PyDoc_STR("Remove an element if present.")},
    {"remove", set_remove, METH_O, PyDoc_STR("Remove an element; raise KeyError if absent.")},
    {"pop", set_pop, METH_NOARGS,
     PyDoc_STR("Remove and return an element (the smallest for Set); raise KeyError if empty.")},
    {"clear", col_clear_meth, METH_NOARGS, PyDoc_STR("Remove all elements.")},
    {"copy", set_copy, METH_NOARGS, PyDoc_STR("Return a shallow copy with the same dtype.")},
    {"update", (PyCFunction)(void (*)(void))set_update, METH_FASTCALL,
     PyDoc_STR("Add elements from each iterable argument.")},
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
    {"update", (PyCFunction)(void (*)(void))set_update, METH_FASTCALL,
     PyDoc_STR("Add elements from each iterable argument.")},
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


static PyGetSetDef map_getset[] = {
    {"key_type", map_get_key_type, nullptr, PyDoc_STR("Canonical key dtype string."), nullptr},
    {"value_type", map_get_value_type, nullptr, PyDoc_STR("Canonical value dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};


static PyMethodDef map_methods[] = {
    {"get", (PyCFunction)(void (*)(void))map_get, METH_FASTCALL,
     PyDoc_STR("Return the value for key, or default (None) if absent.")},
    {"pop", (PyCFunction)(void (*)(void))map_pop, METH_FASTCALL,
     PyDoc_STR("Remove key and return its value; return default if given, else raise KeyError.")},
    {"popitem", map_popitem, METH_NOARGS,
     PyDoc_STR("Remove and return a (key, value) pair (the greatest key for Map); raise KeyError if empty.")},
    {"setdefault", (PyCFunction)(void (*)(void))map_setdefault, METH_FASTCALL,
     PyDoc_STR("Return the value for key, inserting default (None) first if absent.")},
    {"update", (PyCFunction)(void (*)(void))map_update, METH_FASTCALL | METH_KEYWORDS,
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
    {"get", (PyCFunction)(void (*)(void))map_get, METH_FASTCALL,
     PyDoc_STR("Return the value for key, or default (None) if absent.")},
    {"pop", (PyCFunction)(void (*)(void))map_pop, METH_FASTCALL,
     PyDoc_STR("Remove key and return its value; return default if given, else raise KeyError.")},
    {"popitem", map_popitem, METH_NOARGS,
     PyDoc_STR("Remove and return a (key, value) pair (the greatest key for Map); raise KeyError if empty.")},
    {"setdefault", (PyCFunction)(void (*)(void))map_setdefault, METH_FASTCALL,
     PyDoc_STR("Return the value for key, inserting default (None) first if absent.")},
    {"update", (PyCFunction)(void (*)(void))map_update, METH_FASTCALL | METH_KEYWORDS,
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


static PyGetSetDef vector_getset[] = {
    {"dtype", col_get_dtype, nullptr, PyDoc_STR("Canonical element dtype string."), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr},
};


static PyMethodDef vector_methods[] = {
    {"append", vec_append, METH_O, PyDoc_STR("Append an element.")},
    {"extend", vec_extend, METH_O, PyDoc_STR("Append all elements from an iterable.")},
    {"insert", (PyCFunction)(void (*)(void))vec_insert, METH_FASTCALL,
     PyDoc_STR("Insert an element before the given index.")},
    {"pop", (PyCFunction)(void (*)(void))vec_pop, METH_FASTCALL,
     PyDoc_STR("Remove and return the element at index (default last).")},
    {"remove", vec_remove, METH_O, PyDoc_STR("Remove the first occurrence of a value.")},
    {"index", (PyCFunction)(void (*)(void))vec_index_meth, METH_FASTCALL,
     PyDoc_STR("Return the first index of a value.")},
    {"count", vec_count, METH_O, PyDoc_STR("Return the number of occurrences of a value.")},
    {"reverse", vec_reverse, METH_NOARGS, PyDoc_STR("Reverse in place.")},
    {"sort", (PyCFunction)(void (*)(void))vec_sort, METH_FASTCALL | METH_KEYWORDS,
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


struct PyModuleDef *stl_module_def() {
    return &stl_module;
}


extern "C" {

PyMODINIT_FUNC PyInit__stl(void) {
    return PyModuleDef_Init(&stl_module);
}

}
