class SandboxError(Exception):
    pass


class SandboxNameError(SandboxError):
    pass


class SandboxSafetyError(SandboxError):
    pass


class SandboxStateError(SandboxError):
    pass
