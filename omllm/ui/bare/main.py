import asyncio


##


async def _a_main() -> None:
    print('hi')


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
