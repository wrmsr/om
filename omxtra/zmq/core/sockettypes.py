import enum


##


class SocketType(enum.Enum):
    PAIR = 'PAIR'
    PUB = 'PUB'
    SUB = 'SUB'
    REQ = 'REQ'
    REP = 'REP'
    DEALER = 'DEALER'
    ROUTER = 'ROUTER'
    PULL = 'PULL'
    PUSH = 'PUSH'
    XPUB = 'XPUB'
    XSUB = 'XSUB'


# The peer types each socket type may connect to under ZMTP 3.0.
ZMTP_COMPATIBLE_PEERS: dict[SocketType, frozenset[SocketType]] = {
    SocketType.PAIR: frozenset([SocketType.PAIR]),
    SocketType.PUB: frozenset([SocketType.SUB, SocketType.XSUB]),
    SocketType.SUB: frozenset([SocketType.PUB, SocketType.XPUB]),
    SocketType.REQ: frozenset([SocketType.REP, SocketType.ROUTER]),
    SocketType.REP: frozenset([SocketType.REQ, SocketType.DEALER]),
    SocketType.DEALER: frozenset([SocketType.REP, SocketType.DEALER, SocketType.ROUTER]),
    SocketType.ROUTER: frozenset([SocketType.REQ, SocketType.DEALER, SocketType.ROUTER]),
    SocketType.PULL: frozenset([SocketType.PUSH]),
    SocketType.PUSH: frozenset([SocketType.PULL]),
    SocketType.XPUB: frozenset([SocketType.SUB, SocketType.XSUB]),
    SocketType.XSUB: frozenset([SocketType.PUB, SocketType.XPUB]),
}


# The peer types the in-house implementation supports for each socket type it implements: a subset of the above.
SUPPORTED_PEERS: dict[SocketType, frozenset[SocketType]] = {
    SocketType.PUB: frozenset([SocketType.SUB, SocketType.XSUB]),
    SocketType.SUB: frozenset([SocketType.PUB, SocketType.XPUB]),
    SocketType.DEALER: frozenset([SocketType.DEALER, SocketType.ROUTER]),
    SocketType.ROUTER: frozenset([SocketType.DEALER, SocketType.ROUTER]),
}


def is_supported_peer(local: SocketType, remote: SocketType) -> bool:
    return remote in SUPPORTED_PEERS.get(local, frozenset())


# Socket types whose READY carries an Identity property.
IDENTITY_SOCKET_TYPES: frozenset[SocketType] = frozenset([SocketType.REQ, SocketType.DEALER, SocketType.ROUTER])
