import ssl, socket, pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE / "ca" / "root" / "rootCA.cert.pem"
CHAIN= BASE / "ca" / "intermediate" / "chain.pem"
PORT = 8443

# carrega a raiz; opcionalmente dá para concatenar chain se quiser
ctx = ssl.create_default_context(cafile=str(ROOT))
# Caso queira exigir a cadeia completa no handshake:
# ctx.load_verify_locations(cafile=str(CHAIN))

with socket.create_connection(("localhost", PORT)) as sock:
    with ctx.wrap_socket(sock, server_hostname="localhost") as tls:
        cert = tls.getpeercert()
        print("[OK] TLS estabelecido. Sujeito:", cert.get("subject"))
