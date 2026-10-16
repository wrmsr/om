#include <Python.h>


typedef struct {
    long counter;
} TestState;


static TestState *
get_test_state(PyObject *module)
{
    return (TestState *) PyModule_GetState(module);
}


static PyObject *
increment(PyObject *module, PyObject *args)
{
    long delta;
    if (!PyArg_ParseTuple(args, "l:increment", &delta)) {
        return NULL;
    }

    TestState *state = get_test_state(module);
    if (state == NULL) {
        return NULL;
    }
    state->counter += delta;

    return Py_BuildValue("(lk)", state->counter, PyThread_get_thread_ident());
}


static PyMethodDef test_methods[] = {
    {"increment", increment, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL},
};


static PyModuleDef_Slot test_slots[] = {
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {Py_mod_gil, Py_MOD_GIL_USED},
    {0, NULL},
};


static struct PyModuleDef test_module = {
    PyModuleDef_HEAD_INIT,
    "_omcore_daemons_subinterpreter_test",
    NULL,
    sizeof(TestState),
    test_methods,
    test_slots,
    NULL,
    NULL,
    NULL,
};


PyMODINIT_FUNC
PyInit__omcore_daemons_subinterpreter_test(void)
{
    return PyModuleDef_Init(&test_module);
}
