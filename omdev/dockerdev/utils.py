import re
import subprocess
import sys
import typing as ta

from omcore import check


##


BARE_SHA256_PAT = re.compile(r'[0-9a-f]{64}')
PREFIXED_SHA256_PAT = re.compile(r'sha256:[0-9a-f]{64}')


##


def run_and_tee(cmd: ta.Sequence[str]) -> tuple[subprocess.Popen, str]:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # merge stderr into stdout
        bufsize=1,
        text=True,  # decode to str
    )

    captured = []

    for line in check.not_none(proc.stdout):
        sys.stdout.write(line)
        sys.stdout.flush()
        captured.append(line)

    proc.wait()

    return proc, ''.join(captured)
