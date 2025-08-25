from pathlib import Path

import grpc


def _load_credential_from_file(filepath: str):
    real_path = Path(filepath).resolve()
    with open(real_path, "rb") as f:
        return f.read()


def get_server_certificate(
    certificate_path: str, certificate_key_path: str
) -> grpc.ServerCredentials:
    server_certificate = _load_credential_from_file(certificate_path)
    server_certificate_key = _load_credential_from_file(certificate_key_path)
    return grpc.ssl_server_credentials(((server_certificate_key, server_certificate),))


def get_client_certificate(certificate_path: str) -> bytes:
    return _load_credential_from_file(certificate_path)
