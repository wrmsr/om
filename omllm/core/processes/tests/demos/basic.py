"""
A little end-to-end tour of the processes manager. Run it with:

    ./python -m omllm.core.processes.tests.demos.basic

It spawns some `sh` producers, shows the tagged-line rendering, backgrounds a process by reparenting it past a closing
scope, then tears everything down and confirms (via /proc, best effort) that nothing was left behind.
"""
import asyncio
import os

from .... import processes


async def _a_main() -> None:
    async with processes.AsyncioProcessManager(
        # launcher=processes.ShimLauncher(
        #     shell_wrap_shim=True,
        # ),
    ) as m:
        m.subscribe(lambda e: print('  event:', type(e).__name__, getattr(e, 'process_id', '')))

        print('== foreground run, tagged rendering ==')
        run = await m.root.run(processes.ProcessSpec(
            ['sh', '-c', 'echo starting; echo oops >&2; for i in 1 2 3; do echo line $i; done; exit 2'],
            name='demo',
        ))
        print(f'  rc={run.returncode}')
        print(processes.TaggedLinesRenderer().render(run.output.records))

        print('== background across a closing scope ==')
        pids = []
        async with m.root.child('turn') as turn:
            async with turn.child('tool') as tool:
                bg = await tool.spawn(processes.ProcessSpec(
                    ['sh', '-c', 'i=0; while :; do i=$((i+1)); echo tick $i; sleep 0.1; done'],
                    name='ticker',
                ))
                pids.append(bg.pid)
                m.root.adopt(bg)  # 'run in the background'
            print('  tool scope closed; ticker still alive:', bg.state.name)
            await asyncio.sleep(0.35)
        read = bg.spool.read_available(0)
        print('  ticks so far:', read.data().count(b'tick'))

        print('== stubborn process, graceful then forceful ==')
        stubborn = await m.root.spawn(
            processes.ProcessSpec(['sh', '-c', 'trap "" TERM; echo ready; while :; do sleep 0.1; done']),
            processes.TerminationPolicy(grace_s=0.3),
        )
        while b'ready' not in stubborn.spool.read_available(0).data():  # noqa: ASYNC110
            await asyncio.sleep(0.02)
        await stubborn.aclose()
        print('  stubborn final state:', stubborn.state.name, 'rc:', stubborn.returncode)

        live = [p.pid for p in m.processes.values()]
        print('  live processes before manager close:', live)

    print('== after manager close ==')
    for pid in [*pids, stubborn.pid]:
        alive = os.path.exists(f'/proc/{pid}') if os.path.isdir('/proc') else '?'
        print(f'  pid {pid} alive: {alive}')
    try:
        os.waitpid(-1, os.WNOHANG)  # noqa: ASYNC222
        print('  WARNING: still have unreaped children')
    except ChildProcessError:
        print('  no children remain')


if __name__ == '__main__':
    asyncio.run(_a_main())
