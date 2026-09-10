"""
basedpyright 'pyright[nodejs]'
"""
import asyncio
import contextlib
import subprocess

from omcore import marshal as msh

from ..client import LspClient
from ..data import DefinitionResponse
from ..data import DidOpenTextDocumentParams
from ..data import InitializeParams
from ..data import InitializeResult
from ..data import Position
from ..data import TextDocumentIdentifier
from ..data import TextDocumentItem
from ..data import TextDocumentPositionParams


##


async def _a_main_(aes: contextlib.AsyncExitStack) -> None:
    process = await asyncio.create_subprocess_exec(
        'pyright-langserver',
        # 'basedpyright-langserver',
        '--stdio',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    async def finish_process() -> None:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), 5.)
            except TimeoutError:
                process.kill()
                await process.wait()

    aes.push_async_callback(finish_process)

    client = await aes.enter_async_context(LspClient.of_subprocess(process))

    init_response = await client.request('initialize', InitializeParams(
        process_id=None,
        root_uri='file:///tmp',
        capabilities={},
    ))
    init_result = msh.unmarshal(init_response.result, InitializeResult)
    print(init_result)

    await client.notify('initialized')
    await asyncio.sleep(.5)

    #

    # Simulated Python file content
    python_code = """
def foo():
    return 42

foo()
    """.strip()

    file_uri = 'file:///tmp/example.py'

    await client.notify('textDocument/didOpen', DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri=file_uri,
            language_id='python',
            version=1,
            text=python_code,
        ),
    ))

    definition_response = await client.request('textDocument/definition', TextDocumentPositionParams(
        text_document=TextDocumentIdentifier(uri=file_uri),
        position=Position(line=3, character=1),
    ))
    definition_result: DefinitionResponse = msh.unmarshal(definition_response.result, DefinitionResponse)  # noqa

    for loc in definition_result or []:
        print(loc)

    #

    await client.request('shutdown', {})
    await client.notify('exit', {})
    await asyncio.sleep(.5)


async def _a_main() -> None:
    async with contextlib.AsyncExitStack() as aes:
        await _a_main_(aes)


if __name__ == '__main__':
    asyncio.run(_a_main())
