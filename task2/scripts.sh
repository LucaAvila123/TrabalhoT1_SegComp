#!/usr/bin/env bash
set -euo pipefail

mkdir -p ca/root ca/intermediate server

# CA Raiz
openssl genrsa -out ca/root/rootCA.key.pem 4096
openssl req -x509 -new -nodes -sha256 -days 3650 \
  -key ca/root/rootCA.key.pem \
  -subj "/C=BR/O=UFES/CN=UFES Root CA" \
  -out ca/root/rootCA.cert.pem

# CA Intermediária
openssl genrsa -out ca/intermediate/intermediateCA.key.pem 4096
openssl req -new -sha256 \
  -key ca/intermediate/intermediateCA.key.pem \
  -subj "/C=BR/O=UFES/CN=UFES Intermediate CA" \
  -out ca/intermediate/intermediateCA.csr.pem

cat > ca/intermediate/ca_ext.cnf <<'EOF'
basicConstraints=critical,CA:true,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
EOF

openssl x509 -req -in ca/intermediate/intermediateCA.csr.pem \
  -CA ca/root/rootCA.cert.pem -CAkey ca/root/rootCA.key.pem -CAcreateserial \
  -out ca/intermediate/intermediateCA.cert.pem -days 3650 -sha256 \
  -extfile ca/intermediate/ca_ext.cnf

cat ca/intermediate/intermediateCA.cert.pem ca/root/rootCA.cert.pem \
  > ca/intermediate/chain.pem

# Cert do servidor (SAN=localhost)
openssl genrsa -out server/server.key.pem 4096
cat > server/san.cnf <<'EOF'
subjectAltName=DNS:localhost
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
EOF

openssl req -new -sha256 \
  -key server/server.key.pem \
  -subj "/C=BR/O=UFES/CN=localhost" \
  -out server/server.csr.pem

openssl x509 -req -in server/server.csr.pem \
  -CA ca/intermediate/intermediateCA.cert.pem \
  -CAkey ca/intermediate/intermediateCA.key.pem -CAcreateserial \
  -out server/server.cert.pem -days 365 -sha256 \
  -extfile server/san.cnf

cat server/server.cert.pem ca/intermediate/intermediateCA.cert.pem > server/server_fullchain.pem

echo "[OK] PKI criada em task2-openssl-pki/. Agora suba o Nginx com docker compose."
