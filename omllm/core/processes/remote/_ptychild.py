import fcntl
import json
import os
import signal
import sys
import termios


if __name__ == '__main__':
    argv = json.loads(sys.argv[1])
    # This interpreter ignored these at its own startup, and an ignored disposition survives exec: the target would
    # never see a SIGPIPE. Popen's restore_signals undid that for this process only as far as its exec of this
    # interpreter.
    for name in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, signal.SIG_DFL)

    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    os.tcsetpgrp(0, os.getpgrp())

    os.execvpe(argv[0], argv, os.environ)
