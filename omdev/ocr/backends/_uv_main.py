def _uv_main(worker):
    import json
    import sys

    with open(sys.argv[1], encoding='utf-8') as f:
        kwargs = json.load(f)

    result = worker(sys.stdin.buffer.read(), **kwargs)

    if not isinstance(result, str):
        raise TypeError(type(result))

    with open(sys.argv[2], 'w', encoding='utf-8', newline='') as f:
        f.write(result)
