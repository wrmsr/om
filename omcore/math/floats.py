import struct


##


def float_to_bytes(f: float) -> bytes:
    return struct.pack('>f', f)


def bytes_to_float(b: bytes) -> float:
    return struct.unpack('>f', b)[0]
