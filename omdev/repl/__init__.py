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
        DEFAULT_BASH_NAME,
        make_default_session,
    )

    from .dispatch import (  # noqa
        Dispatcher,
        InlineDispatcher,
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
        BashLanguage,
        PYTHON_LANGUAGE,
        JAVASCRIPT_LANGUAGE,
        BASH_LANGUAGE,
    )

    from .lines import (  # noqa
        LineRepl,

        LineCommandResult,
        QUIT_COMMANDS,
        handle_line_command,
    )

    from .outputs import (  # noqa
        Output,
        StdoutOutput,
        ResultOutput,
        ErrorOutput,
        TerminalOutput,
        NoteOutput,
        output_text,

        OutputSink,
        NopOutputSink,
        ListOutputSink,
        CallbackOutputSink,
        TextOutputSink,
    )

    from .ptys import (  # noqa
        PtyProcess,
        PtySpawner,
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

    from .terminals import (  # noqa
        LineTerminal,
    )

    ##
    # asyncio

    from .asyncio import (  # noqa
        AsyncioThreadExecutor,
        AsyncioRunning,
        AsyncioRunner,
        AsyncioLoopDispatcher,
    )

    ##
    # languages

    from .bash.interpreter import (  # noqa
        BashStartError,
        BashInterpreter,
    )

    from .bash.protocol import (  # noqa
        BashPrompt,
        BashPromptScanner,
        BashProtocol,
    )

    from .python.interpreter import (  # noqa
        PythonInterpreter,
    )

    from .quickjs.interpreter import (  # noqa
        quickjs_available,
        QuickjsInterpreter,
    )

    ##
    # frontends

    from . import manhole  # noqa
    from . import minitui  # noqa
