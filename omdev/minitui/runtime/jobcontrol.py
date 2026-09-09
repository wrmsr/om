"""
Job control: the suspend / resume sequence shared by the drivers.

A stop must hand the terminal back the way the shell expects it, so the teardown runs first and only then is the process
stopped for real; SIGCONT re-enters application mode. Two triggers converge here: a legacy-wire ctrl+z, which the kernel
turns into SIGTSTP because raw mode keeps ISIG on, and an app binding on extended-key terminals, where the chord arrives
as a key event instead and the app calls the driver's `suspend()`. The drivers own the signal wiring - each applies it
at its own safe point, between renders and never inside one - and this holds the sequence and state.

The `bg` case: a job continued in the background gets SIGCONT too but may not touch the tty. A resume probes for that
first (textual's trick) and stays suspended when the probe fails; the `fg` that eventually follows delivers another
SIGCONT, and that one goes through.
"""
import os
import signal
import typing as ta


##


def stop_self() -> None:
    """The real stop: returns only once the process has been continued."""

    os.kill(os.getpid(), signal.SIGSTOP)


class JobControl:
    """
    `suspend` leaves application mode and `resume` re-enters it, returning False if the terminal isn't ours yet.
    `stop_process` is the stop itself - injectable so tests never stop the test runner.
    """

    def __init__(
            self,
            *,
            suspend: ta.Callable[[], None],
            resume: ta.Callable[[], bool],
            stop_process: ta.Callable[[], None] | None = None,
    ) -> None:
        super().__init__()

        self._suspend = suspend
        self._resume = resume
        self._stop_process = stop_process if stop_process is not None else stop_self

        self._suspended = False

    @property
    def suspended(self) -> bool:
        """Between a suspend and a successful resume - including while continued in the background."""

        return self._suspended

    def suspend(self) -> None:
        """
        Leave application mode, then stop the process. Returns once the process has been continued; the resume itself
        runs from the SIGCONT handler, which the drivers route to `resume`.
        """

        if self._suspended:
            return
        self._suspended = True
        self._suspend()
        self._stop_process()

    def resume(self) -> None:
        """Back from a stop: re-enter application mode - unless continued in the background, then wait for the next."""

        if not self._suspended:
            return
        if self._resume():
            self._suspended = False
