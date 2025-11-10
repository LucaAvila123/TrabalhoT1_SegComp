from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE / "ca" / "root"
INT_DIR  = BASE / "ca" / "intermediate"
SRV_DIR  = BASE / "server"
for d in [ROOT_DIR, INT_DIR, SRV_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def save_key(key, path):
    path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))

def save_cert(cert, path):
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

def make_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)

def name(common, org="UFES", country="BR"):
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
        x509.NameAttribute(NameOID.COMMON_NAME, common),
    ])

def self_signed_ca(key, common):
    now = datetime.utcnow()
    builder = (x509.CertificateBuilder()
        .subject_name(name(common))
        .issuer_name(name(common))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=3650))  # ~10 anos
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .add_extension(x509.KeyUsage(key_cert_sign=True, crl_sign=True,
                                     digital_signature=False, key_encipherment=False,
                                     content_commitment=False, data_encipherment=False,
                                     key_agreement=False, encipher_only=False, decipher_only=False),
                       critical=True)
    )
    return builder.sign(private_key=key, algorithm=hashes.SHA256())

def sign_intermediate_ca(child_key, child_subject, issuer_cert, issuer_key):
    now = datetime.utcnow()
    builder = (
        x509.CertificateBuilder()
        .subject_name(child_subject)              # subject da Intermediária
        .issuer_name(issuer_cert.subject)         # issuer = subject da Raiz
        .public_key(child_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(
            key_cert_sign=True, crl_sign=True,
            digital_signature=False, key_encipherment=False,
            content_commitment=False, data_encipherment=False,
            key_agreement=False, encipher_only=False, decipher_only=False
        ), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(child_key.public_key()),
            critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            critical=False
        )
    )
    return builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())

def sign_server_csr(csr, issuer_cert, issuer_key):
    now = datetime.utcnow()
    builder = (x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(issuer_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.KeyUsage(key_cert_sign=False, crl_sign=False,
                                     digital_signature=True, key_encipherment=True,
                                     content_commitment=False, data_encipherment=False,
                                     key_agreement=False, encipher_only=False, decipher_only=False),
                       critical=True)
    )
    return builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())

def main():
    # 1) CA Raiz
    root_key = make_key()
    root_cert = self_signed_ca(root_key, "UFES Root CA")
    save_key(root_key, ROOT_DIR / "rootCA.key.pem")
    save_cert(root_cert, ROOT_DIR / "rootCA.cert.pem")

    # 2) CA Intermediária
    int_key = make_key()
    int_subject = name("UFES Intermediate CA")
    int_cert = sign_intermediate_ca(int_key, int_subject, root_cert, root_key)
    save_key(int_key, INT_DIR / "intermediateCA.key.pem")
    save_cert(int_cert, INT_DIR / "intermediateCA.cert.pem")

    # 3) Servidor (CSR → assinado pela Intermediária)
    srv_key = make_key()
    save_key(srv_key, SRV_DIR / "server.key.pem")
    csr = (x509.CertificateSigningRequestBuilder()
           .subject_name(name("localhost"))
           .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
           .sign(srv_key, hashes.SHA256()))
    # Assina
    srv_cert = sign_server_csr(csr, int_cert, int_key)
    save_cert(srv_cert, SRV_DIR / "server.cert.pem")

    # 4) Cadeia
    chain = (INT_DIR / "chain.pem")
    chain.write_bytes(int_cert.public_bytes(serialization.Encoding.PEM) +
                      root_cert.public_bytes(serialization.Encoding.PEM))

    print("[OK] Raiz, Intermediária, Server e cadeia gerados em:", BASE)

if __name__ == "__main__":
    main()
