"""
A pseudo-terminal tour. Run with:

    ./python -m omllm.core.processes.tests.demos.pty

Shows: a child that sees a real controlling terminal with a given window size, live interactive echo through the pty
(note the cooked-mode CRLF), and a resize delivering SIGWINCH.
"""
import asyncio

from .... import processes


async def _a_main() -> None:
    async with processes.AsyncioProcessManager() as m:
        print('== a child under a real pty ==')
        run = await m.root.run(processes.ProcessSpec(
            ['sh', '-c', 'echo "tty: $(tty)"; echo "size: $(stty size)"; echo "term: $TERM"; echo "ctty: $(ps -o tty= -p $$)"'],  # noqa
            stdio=processes.PtyStdio(rows=30, cols=100),
        ))
        print(processes.RawRenderer().render(run.output.records).rstrip())

        print('\n== interactive: type into the pty, read the echo ==')
        p = await m.root.spawn(processes.ProcessSpec(['cat'], stdio=processes.PtyStdio()))
        print('  initial winsize:', p.get_winsize())
        for line in (b'one\n', b'two\n'):
            await p.write(line)
        await asyncio.sleep(0.2)
        got = p.spool.read_available(0).data()
        print('  pty saw (raw):', got)  # cooked-mode echo -> CRLF

        await p.resize(40, 120)
        print('  winsize after resize:', p.get_winsize())
        await p.aclose()
        print('  final:', p.state.name, 'rc', p.returncode)


if __name__ == '__main__':
    asyncio.run(_a_main())
