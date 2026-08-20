import hashlib
import typing as ta


##


CertificateBackend: ta.TypeAlias = ta.Literal[
    'auto',
    'cryptography',
    'asn1crypto',
]


class CertificateBackendUnavailable(ImportError):
    pass


class ChannelBindingUndefined(ValueError):
    pass


def _tls_server_end_point_cryptography(cert_der: bytes) -> bytes:
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes

    except ModuleNotFoundError as exc:
        # Don't mistake a broken cryptography installation for an installation where cryptography simply isn't present.
        if exc.name != 'cryptography':
            raise

        raise CertificateBackendUnavailable('cryptography') from exc

    cert = x509.load_der_x509_certificate(cert_der)
    hash_algorithm = cert.signature_hash_algorithm

    if hash_algorithm is None:
        raise ChannelBindingUndefined(
            'tls-server-end-point is undefined for certificate '
            f'signature algorithm {cert.signature_algorithm_oid.dotted_string}',
        )

    if hash_algorithm.name in {'md5', 'sha1'}:
        hash_algorithm = hashes.SHA256()

    digest = hashes.Hash(hash_algorithm)
    digest.update(cert_der)
    return digest.finalize()


def _tls_server_end_point_asn1crypto(cert_der: bytes) -> bytes:
    try:
        from asn1crypto.x509 import Certificate

    except ModuleNotFoundError as exc:
        if exc.name != 'asn1crypto':
            raise

        raise CertificateBackendUnavailable('asn1crypto') from exc

    cert = Certificate.load(cert_der)

    signature_algorithm = (
        cert['signature_algorithm']['algorithm'].native
    )

    # asn1crypto 1.5.1 reports SHA-512 for Ed25519 and SHAKE-256 for Ed448, but RFC 5929 says a signature algorithm with
    # no separate hash makes tls-server-end-point undefined.
    if signature_algorithm in {'ed25519', 'ed448'}:
        raise ChannelBindingUndefined(
            'tls-server-end-point is undefined for certificate '
            f'signature algorithm {signature_algorithm}',
        )

    try:
        hash_name = cert.hash_algo
    except ValueError as exc:
        raise ChannelBindingUndefined("couldn't determine the certificate signature hash algorithm") from exc

    if hash_name in {'md5', 'sha1'}:
        hash_name = 'sha256'

    try:
        return hashlib.new(hash_name, cert_der).digest()
    except (TypeError, ValueError) as exc:
        raise ChannelBindingUndefined(f'unsupported certificate signature hash {hash_name!r}') from exc


def tls_server_end_point(
        cert_der: bytes,
        *,
        backend: CertificateBackend = 'auto',
) -> bytes:
    if backend == 'cryptography':
        return _tls_server_end_point_cryptography(cert_der)

    if backend == 'asn1crypto':
        return _tls_server_end_point_asn1crypto(cert_der)

    if backend != 'auto':
        raise ValueError(
            f'unknown certificate backend {backend!r}',
        )

    # Prefer cryptography when the application already has it.
    #
    # Fall back only when the backend isn't installed. Do not silently retry with another parser when the certificate is
    # malformed or its signature algorithm is unsupported.
    try:
        return _tls_server_end_point_cryptography(cert_der)
    except CertificateBackendUnavailable:
        pass

    try:
        return _tls_server_end_point_asn1crypto(cert_der)
    except CertificateBackendUnavailable:
        pass

    raise CertificateBackendUnavailable('tls-server-end-point requires either cryptography or asn1crypto')
