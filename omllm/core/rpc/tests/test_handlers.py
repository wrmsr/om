import pytest

from ..errors import RpcMethodNotFoundError
from ..handlers import RpcNotificationRouter


def test_notification_router_routes_inline():
    seen: list = []
    router = RpcNotificationRouter()
    router.add_routes(['a.x', 'a.y'], lambda method, params: seen.append((method, params)))

    assert router.handle_notification_inline('a.x', 1)
    assert router.handle_notification_inline('a.y', {'k': 2})
    assert not router.handle_notification_inline('b.z', None)
    assert seen == [('a.x', 1), ('a.y', {'k': 2})]


def test_notification_router_rejects_duplicates_and_calls():
    router = RpcNotificationRouter()
    router.add_routes(['a.x'], lambda method, params: None)
    with pytest.raises(ValueError):  # noqa: PT011
        router.add_routes(['a.x'], lambda method, params: None)


@pytest.mark.asyncs('asyncio')
async def test_notification_router_has_no_methods():
    router = RpcNotificationRouter()
    with pytest.raises(RpcMethodNotFoundError):
        await router.handle('a.x', None)
