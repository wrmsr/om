"""
The bare frontend: `input()` and stdout over `LineRepl`, nothing else - the smallest thing that is not minitui, and the
line core's first transport. Loop-free: executions drive under `lang.sync_await`, so top-level `await` is off (it would
have no loop to run on) and the javascript engine evaluates inline. Ctrl+c discards the lines being typed; ctrl+d or
`/quit` leaves.
"""
import sys

from omcore import lang

from ..defaults import make_default_session
from ..interpreters import ResultStatus
from ..lines import LineRepl
from ..outputs import TextOutputSink


##


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    session = make_default_session(allow_await=False)
    repl = LineRepl(session, TextOutputSink(sys.stdout.write))
    write = sys.stdout.write

    write(f'{", ".join("/" + n for n in session.names)} to switch; /quit or ctrl+d leaves\n')

    try:
        while True:
            try:
                line = input(repl.prompt)
            except EOFError:
                write('\n')
                break
            except KeyboardInterrupt:
                write('\nKeyboardInterrupt\n')
                repl.reset()
                continue

            if not repl.pending and line.startswith('/'):
                command = line[1:].strip()
                if command == 'quit':
                    break
                if command in session.names:
                    session.switch(command)
                else:
                    write(f'unknown command: {line}\n')
                continue

            result = lang.sync_await(repl.feed_line(line))
            if result is not None and result.status is ResultStatus.EXIT:
                break

    finally:
        lang.sync_await(session.aclose())


if __name__ == '__main__':
    _main()
