// @om-cext
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stddef.h>

//

#define _MODULE_NAME "_hash"
#define _PACKAGE_NAME "omcore.lang.cached"
#define _MODULE_FULL_NAME _PACKAGE_NAME "." _MODULE_NAME

//

typedef struct {
    PyObject *cached_hash_type;
    PyObject *str_default_attr;
} module_state;

static module_state * get_module_state(PyObject *module)
{
    return (module_state *) PyModule_GetState(module);
}

//

typedef struct {
    PyObject_HEAD
    vectorcallfunc vectorcall;
    PyObject *fn;
    PyObject *attr;
} cached_hash_object;

static PyObject * cached_hash_object_vectorcall(PyObject *op, PyObject *const *args, size_t nargsf, PyObject *kwnames)
{
    cached_hash_object *self = (cached_hash_object *) op;

    if (kwnames != NULL && PyTuple_GET_SIZE(kwnames) != 0) {
        PyErr_SetString(PyExc_TypeError, "__hash__ takes no keyword arguments");
        return NULL;
    }
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    if (nargs != 1) {
        PyErr_Format(PyExc_TypeError, "__hash__ expected 1 argument, got %zd", nargs);
        return NULL;
    }
    PyObject *obj = args[0];

    PyObject *h;
    int found = PyObject_GetOptionalAttr(obj, self->attr, &h);
    if (found < 0) {
        return NULL;
    }
    if (found) {
        return h;
    }

    h = PyObject_CallOneArg(self->fn, obj);
    if (h == NULL) {
        return NULL;
    }

    // PyObject_GenericSetAttr is object.__setattr__ - deliberately bypassing any frozen __setattr__. Under
    // free-threading concurrent first hashes may each compute and store - harmless duplicate initialization.
    if (PyObject_GenericSetAttr(obj, self->attr, h) < 0) {
        Py_DECREF(h);
        return NULL;
    }

    return h;
}

// Binds like a plain function so `__hash__ = cached_hash(...)` in a class body receives the instance - also required by
// Py_TPFLAGS_METHOD_DESCRIPTOR, which lets the tp_hash slot skip the temporary bound method.
static PyObject * cached_hash_object_descr_get(PyObject *op, PyObject *obj, PyObject *type)
{
    if (obj == NULL || obj == Py_None) {
        return Py_NewRef(op);
    }

    return PyMethod_New(op, obj);
}

static int cached_hash_object_traverse(PyObject *op, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(op));

    cached_hash_object *self = (cached_hash_object *) op;
    Py_VISIT(self->fn);
    Py_VISIT(self->attr);
    return 0;
}

static int cached_hash_object_clear(PyObject *op)
{
    cached_hash_object *self = (cached_hash_object *) op;
    Py_CLEAR(self->fn);
    Py_CLEAR(self->attr);
    return 0;
}

static void cached_hash_object_dealloc(PyObject *op)
{
    PyTypeObject *tp = Py_TYPE(op);
    PyObject_GC_UnTrack(op);
    (void) cached_hash_object_clear(op);
    tp->tp_free(op);
    Py_DECREF(tp);
}

static PyMemberDef cached_hash_object_members[] = {
    {"__vectorcalloffset__", Py_T_PYSSIZET, offsetof(cached_hash_object, vectorcall), Py_READONLY, NULL},
    {NULL, 0, 0, 0, NULL}
};

static PyType_Slot cached_hash_object_type_slots[] = {
    {Py_tp_dealloc, (void *) cached_hash_object_dealloc},
    {Py_tp_traverse, (void *) cached_hash_object_traverse},
    {Py_tp_clear, (void *) cached_hash_object_clear},
    {Py_tp_call, (void *) PyVectorcall_Call},
    {Py_tp_descr_get, (void *) cached_hash_object_descr_get},
    {Py_tp_members, (void *) cached_hash_object_members},
    {0, NULL}
};

static PyType_Spec cached_hash_object_type_spec = {
    .name = _MODULE_FULL_NAME ".cached_hash",
    .basicsize = sizeof(cached_hash_object),
    .flags =
        Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_HAVE_GC |
        Py_TPFLAGS_HAVE_VECTORCALL |
        Py_TPFLAGS_METHOD_DESCRIPTOR |
        Py_TPFLAGS_IMMUTABLETYPE |
        Py_TPFLAGS_DISALLOW_INSTANTIATION,
    .slots = cached_hash_object_type_slots,
};

//

static PyObject * cached_hash(PyObject *module, PyObject *args, PyObject *kwargs)
{
    module_state *state = get_module_state(module);

    static const char * const kwlist[] = {"fn", "attr", NULL};
    PyObject *fn;
    PyObject *attr = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$U:cached_hash", kwlist, &fn, &attr)) {
        return NULL;
    }
    if (!PyCallable_Check(fn)) {
        PyErr_SetString(PyExc_TypeError, "fn must be callable");
        return NULL;
    }

    PyTypeObject *tp = (PyTypeObject *) state->cached_hash_type;
    cached_hash_object *self = (cached_hash_object *) tp->tp_alloc(tp, 0);
    if (self == NULL) {
        return NULL;
    }

    self->vectorcall = cached_hash_object_vectorcall;
    self->fn = Py_NewRef(fn);
    if (attr != NULL) {
        self->attr = Py_NewRef(attr);
        PyUnicode_InternInPlace(&self->attr);
    } else {
        self->attr = Py_NewRef(state->str_default_attr);
    }

    return (PyObject *) self;
}

//

PyDoc_STRVAR(cached_hash_doc, "cached_hash(fn, *, attr='_hash')");

static PyMethodDef mod_methods[] = {
    {"cached_hash", (PyCFunction) (void (*)(void)) cached_hash, METH_VARARGS | METH_KEYWORDS, cached_hash_doc},
    {NULL, NULL, 0, NULL}
};

static int module_traverse(PyObject *module, visitproc visit, void *arg)
{
    module_state *state = get_module_state(module);
    Py_VISIT(state->cached_hash_type);
    Py_VISIT(state->str_default_attr);
    return 0;
}

static int module_clear(PyObject *module)
{
    module_state *state = get_module_state(module);
    Py_CLEAR(state->cached_hash_type);
    Py_CLEAR(state->str_default_attr);
    return 0;
}

static void module_free(void *module)
{
    module_clear((PyObject *) module);
}

static int module_exec(PyObject *module)
{
    module_state *state = get_module_state(module);

    state->str_default_attr = PyUnicode_InternFromString("_hash");
    if (!state->str_default_attr) {
        return -1;
    }

    state->cached_hash_type = PyType_FromModuleAndSpec(module, &cached_hash_object_type_spec, NULL);
    if (!state->cached_hash_type) {
        return -1;
    }

    return 0;
}

//

PyDoc_STRVAR(module_doc, _MODULE_NAME);

static PyModuleDef_Slot module_slots[] = {
    {Py_mod_exec, (void *) module_exec},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, NULL}
};

static PyModuleDef module_def = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = _MODULE_NAME,
    .m_doc = module_doc,
    .m_size = sizeof(module_state),
    .m_methods = mod_methods,
    .m_slots = module_slots,
    .m_traverse = module_traverse,
    .m_clear = module_clear,
    .m_free = module_free,
};

extern "C" {

PyMODINIT_FUNC
PyInit__hash(void)
{
    return PyModuleDef_Init(&module_def);
}

}
