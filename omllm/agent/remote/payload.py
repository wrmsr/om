import typing as ta


RemoteAgentPayloadFile = ta.NewType('RemoteAgentPayloadFile', str)


##


def get_remote_agent_payload_src(*, file: RemoteAgentPayloadFile | None = None) -> str:
    if file is not None:
        with open(file) as f:  # noqa
            return f.read()

    import importlib.resources
    return importlib.resources.files(__package__).joinpath('_amalg.py').read_text()
