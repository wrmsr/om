from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...io.pipelines.drivers.pure import PureIoPipelineDriver
from ...io.streambufs.utils import ByteStreamBuffers
from ..http import HttpPipelineFailure
from ..http import HttpServerRequest
from ..http import HttpServerSendResponse
from ..http import pipeline_http_server_spec


##


def test_pipeline_http_server_pure_driver_fragmented_request_and_response():
    driver = PureIoPipelineDriver(pipeline_http_server_spec(max_request_body_bytes=16))
    assert driver.next(read=False) is None

    request_bytes = (
        b'POST /work?item=one HTTP/1.1\r\n'
        b'Host: example.test\r\n'
        b'Content-Length: 5\r\n'
        b'Connection: close\r\n'
        b'\r\n'
        b'hello'
    )
    for byte in request_bytes:
        driver.feed_input(bytes([byte]))

    event = driver.next()
    assert isinstance(event, HttpServerRequest)
    assert event.request.head.method == 'POST'
    assert event.request.head.target == '/work?item=one'
    assert ByteStreamBuffers.to_bytes(event.request.body, strict=True) == b'hello'

    driver.enqueue(HttpServerSendResponse(response=FullIoPipelineHttpResponse.simple(
        status=201,
        body=b'created',
    )))
    assert driver.next(read=False) is None
    response_bytes = driver.drain_output()
    assert response_bytes.startswith(b'HTTP/1.1 201 Created\r\n')
    assert b'Content-Length: 7\r\n' in response_bytes
    assert response_bytes.endswith(b'\r\n\r\ncreated')
    assert not driver.is_running


def test_pipeline_http_server_rejects_request_body_over_bound():
    driver = PureIoPipelineDriver(pipeline_http_server_spec(max_request_body_bytes=4))
    driver.feed_input(
        b'POST /work HTTP/1.1\r\n'
        b'Host: example.test\r\n'
        b'Content-Length: 5\r\n'
        b'\r\n'
        b'hello',
    )

    failure = driver.next()
    assert isinstance(failure, HttpPipelineFailure)
    assert 'exceeded max_body' in str(failure.exc)
    assert driver.next(read=False) is None
    assert driver.drain_output() == b''
    assert not driver.is_running
