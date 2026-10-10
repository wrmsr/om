"""
Regression tests for defects in the JSON-RPC session found reviewing the io.pipelines half-close work. The ids in the
comments are those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect
as it was found.
"""
from .....io.pipelines import all as ipl
from ..messages import JsonrpcPipelineMessages as Jpm
from .harness import Harness


##


def test_events_still_reach_the_host_after_output_half_close():
    # T1 (TODO.md: "mark host-facing messages AfterShutdownOutput - jsonrpc JsonrpcPipelineMessages.Event ... which
    # would otherwise be rejected after a half-close"). The session's events travel outbound to the host. Once
    # something has half-closed the connection's output - here an innermost handler, as a transport policy might -
    # the session keeps receiving, but every event it emits is rejected at the terminal with
    # SawShutdownOutputIoPipelineError, so the host never learns of the peer's notification.
    fb = ipl.FeedbackHandler()
    h = Harness(innermost_handlers=[fb])
    h.events()

    so = ipl.Messages.ShutdownOutput()
    h.drv.enqueue(fb.wrap(so))
    h.events()
    assert so.is_succeeded()
    assert h.drv.output_shutdown

    evs = h.recv({'jsonrpc': '2.0', 'method': 'notify_hello', 'params': [1]})
    assert h.raised == []
    assert [type(e) for e in evs] == [Jpm.NotificationReceived]
    assert evs[0].notification.method == 'notify_hello'
