import subprocess
import typing as ta


##


class ProcessError(subprocess.CalledProcessError):
    def __str__(self):
        msg = super().__str__()
        if self.stderr:
            msg += f'\nstderr:\n{self.stderr.strip()}'
        return msg


def check_subprocess_output(cmd: ta.Sequence[str], **kwargs: ta.Any) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        **kwargs,
    )

    if result.returncode != 0:
        raise ProcessError(
            result.returncode,
            cmd,
            result.stdout,
            result.stderr.decode(),  # noqa
        )

    return result.stdout.decode()  # noqa
