# @om-lite
# ruff: noqa: FURB188 UP006 UP007 UP045
import signal


class SystevisorSignalNameError(ValueError):
    pass


def systevisor_parse_signal_name(value: str) -> int:
    name = value.upper()
    if not name.startswith('SIG'):
        name = f'SIG{name}'
    signal_number = getattr(signal, name, None)
    if not isinstance(signal_number, int) or signal_number <= 0:
        raise SystevisorSignalNameError(value)
    return signal_number


def systevisor_normalize_signal_name(value: str) -> str:
    signal_number = systevisor_parse_signal_name(value)
    name = signal.Signals(signal_number).name
    return name[3:] if name.startswith('SIG') else name


def systevisor_signal_is_catchable(value: str) -> bool:
    signal_number = systevisor_parse_signal_name(value)
    return signal_number not in {signal.SIGKILL, signal.SIGSTOP}
