import os


##


def disable_posix_spawn_setsid(monkeypatch):
    real_posix_spawn = os.posix_spawn
    calls = []

    def posix_spawn(*args, **kwargs):
        if kwargs.get('setsid'):
            calls.append(kwargs)
            raise NotImplementedError('posix_spawn: setsid unavailable on this platform')
        return real_posix_spawn(*args, **kwargs)

    monkeypatch.setattr(os, 'posix_spawn', posix_spawn)
    return calls
