# fmt: off
# ruff: noqa: I001
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(
        globals(),
):
    ##

    from .defaults import (  # noqa
        DEFAULT_PYTHON_NAME,
        DEFAULT_JAVASCRIPT_NAME,
        make_default_session,
    )

    from .executors import (  # noqa
        Executor,
        ImmediateExecutor,
    )

    from .interpreters import (  # noqa
        ResultStatus,
        Result,
        Completion,

        InterpreterError,
        InterpreterBusyError,

        Interpreter,
    )

    from .languages import (  # noqa
        Completeness,
        Language,
        PythonLanguage,
        JavascriptLanguage,
        PYTHON_LANGUAGE,
        JAVASCRIPT_LANGUAGE,
    )

    from .lines import (  # noqa
        LineRepl,
    )

    from .outputs import (  # noqa
        Output,
        StdoutOutput,
        ResultOutput,
        ErrorOutput,
        output_text,

        OutputSink,
        NopOutputSink,
        ListOutputSink,
        CallbackOutputSink,
        TextOutputSink,
    )

    from .runners import (  # noqa
        Running,
        Runner,
        ImmediateRunner,
    )

    from .sessions import (  # noqa
        SessionError,
        NoSuchInterpreterError,
        DuplicateInterpreterError,
        NoActiveInterpreterError,

        SessionListener,
        Session,
    )

    ##
    # asyncio

    from .asyncio import (  # noqa
        AsyncioThreadExecutor,
        AsyncioRunning,
        AsyncioRunner,
    )

    ##
    # languages

    from .python.interpreter import (  # noqa
        PythonInterpreter,
    )

    from .quickjs.interpreter import (  # noqa
        quickjs_available,
        QuickjsInterpreter,
    )

    ##
    # frontends

    from . import minitui  # noqa
