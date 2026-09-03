from ..jobcontrol import JobControl


##


def test_job_control_sequence():
    log: list[str] = []

    def resume() -> bool:
        log.append('up')
        return True

    jc = JobControl(
        suspend=lambda: log.append('down'),
        resume=resume,
        stop_process=lambda: log.append('stop'),
    )

    # (The state is snapshotted rather than asserted step by step: mypy narrows a property expression on assert and
    # keeps the narrowing across method calls, so a later contradicting assert reads as unreachable.)
    states: list[bool] = []

    # A stray SIGCONT while running is a no-op.
    jc.resume()
    states.append(jc.suspended)
    assert log == []

    # Teardown strictly precedes the stop.
    jc.suspend()
    states.append(jc.suspended)
    assert log == ['down', 'stop']

    # Idempotent while suspended.
    jc.suspend()
    states.append(jc.suspended)
    assert log == ['down', 'stop']

    jc.resume()
    states.append(jc.suspended)
    assert log == ['down', 'stop', 'up']

    assert states == [False, True, True, False]


def test_job_control_background_continue_stays_suspended():
    # Continued with `bg`: the resume callback reports the terminal isn't ours; the state holds until the `fg` SIGCONT.
    foreground = [False]
    attempts: list[int] = []

    def resume() -> bool:
        attempts.append(1)
        return foreground[0]

    jc = JobControl(suspend=lambda: None, resume=resume, stop_process=lambda: None)
    jc.suspend()

    jc.resume()
    still_suspended = jc.suspended
    assert attempts == [1]

    foreground[0] = True
    jc.resume()
    assert attempts == [1, 1]
    assert (still_suspended, jc.suspended) == (True, False)
