"""
Not collected on its own - these are the cases test_outcomes runs under a child pytest, one per pytest outcome an async
test can end in, so that the asyncs plugin's reporting of each can be asserted from the outside.
"""
import pytest


##


@pytest.mark.asyncs('asyncio')
async def test_pass():
    pass


@pytest.mark.asyncs('asyncio')
async def test_fail():
    raise AssertionError('expected failure')


@pytest.mark.asyncs('asyncio')
async def test_skip():
    pytest.skip('expected skip')


@pytest.mark.asyncs('asyncio')
async def test_xfail():
    pytest.xfail('expected xfail')


@pytest.fixture
async def skipping_fixture():
    pytest.skip('expected fixture skip')


@pytest.mark.asyncs('asyncio')
async def test_fixture_skip(skipping_fixture):
    raise AssertionError('must not run')
