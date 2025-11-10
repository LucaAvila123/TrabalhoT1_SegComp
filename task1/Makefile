# Makefile — Task 1 (portable: Windows / Linux / macOS)

# ==== OS detection ====
ifeq ($(OS),Windows_NT)
  PYTHON       ?= py
  VENV_DIR     ?= .venv
  VENV_PYTHON  := $(VENV_DIR)/Scripts/python.exe
  PIP_CMD      := $(VENV_PYTHON) -m pip
  READ30       := powershell -NoProfile -Command "Get-Content -TotalCount 30"
  NULDEV       := NUL
else
  PYTHON       ?= python3
  VENV_DIR     ?= .venv
  VENV_PYTHON  := $(VENV_DIR)/bin/python
  PIP_CMD      := $(VENV_PYTHON) -m pip
  READ30       := head -n 30
  NULDEV       := /dev/null
endif

BUILD_PKI   := app/build_pki.py
VERIFY_PY   := app/verify.py

ROOT_CERT   := ca/root/rootCA.cert.pem
INT_CERT    := ca/intermediate/intermediateCA.cert.pem
CHAIN_PEM   := ca/intermediate/chain.pem
SRV_CERT    := server/server.cert.pem
SRV_KEY     := server/server.key.pem
FULLCHAIN   := server/server_fullchain.pem

# ==== Help ====
.PHONY: help
help:
	@echo "Targets:"
	@echo "  make deps     -> create venv and install deps"
	@echo "  make pki      -> generate root CA, intermediate CA, server, chain"
	@echo "  make fullchain-> build server_fullchain.pem (server + intermediate)"
	@echo "  make up       -> start nginx (Docker) https://localhost"
	@echo "  make upf      -> start nginx forcing recreate"
	@echo "  make restart  -> down + up (fresh)"
	@echo "  make verify   -> restart and run Python TLS check"
	@echo "  make check    -> openssl checks"
	@echo "  make info     -> show certs info"
	@echo "  make all      -> deps + pki + up + verify"
	@echo "  make down     -> stop containers"
	@echo "  make clean    -> remove artifacts"
	@echo "  make regen    -> clean + pki + up"

# ==== Env ====
$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV_DIR)

.PHONY: deps
deps: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ensurepip --upgrade
	$(VENV_PYTHON) -m pip --version
	$(VENV_PYTHON) -m pip install --no-cache-dir cryptography==43.0.1

# ==== PKI (creates root/intermediate/server/chain) ====
$(ROOT_CERT) $(INT_CERT) $(SRV_CERT) $(CHAIN_PEM): deps
	$(VENV_PYTHON) $(BUILD_PKI)

.PHONY: pki
pki: $(ROOT_CERT) $(INT_CERT) $(SRV_CERT) $(CHAIN_PEM)
	@echo "[OK] PKI generated into ca/ and server/"

# ==== Full chain (server + intermediate) ====
ifeq ($(OS),Windows_NT)
$(FULLCHAIN): $(SRV_CERT) $(INT_CERT)
	powershell -NoProfile -Command "Get-Content -Raw 'server\server.cert.pem','ca\intermediate\intermediateCA.cert.pem' | Set-Content -Encoding ascii 'server\server_fullchain.pem'"
else
$(FULLCHAIN): $(SRV_CERT) $(INT_CERT)
	cat $(SRV_CERT) $(INT_CERT) > $@
endif

.PHONY: fullchain
fullchain: $(FULLCHAIN)

# ==== Docker (Nginx TLS) ====
.PHONY: up
up: pki $(FULLCHAIN)
	docker compose up -d
	@echo "[OK] Nginx on https://localhost"

.PHONY: upf
upf: pki $(FULLCHAIN)
	docker compose up -d --force-recreate
	@echo "[OK] Nginx (force-recreate) on https://localhost"

.PHONY: down
down:
	docker compose down

.PHONY: restart
restart:
	docker compose down
	docker compose up -d
	@echo "[OK] Restarted Nginx"

# ==== Verify ====
.PHONY: verify
verify: pki fullchain
	$(MAKE) restart
	$(VENV_PYTHON) $(VERIFY_PY)

.PHONY: check
check: pki $(FULLCHAIN)
	@echo "---- s_client (first lines) ----"
	-@echo | openssl s_client -connect localhost:8443 -servername localhost -showcerts 2> $(NULDEV) | $(READ30)
	@echo "---- verify (against chain) ----"
	-@openssl verify -CAfile $(CHAIN_PEM) $(SRV_CERT)
	@echo "---- verify (root + untrusted intermediate) ----"
	-@openssl verify -CAfile $(ROOT_CERT) -untrusted $(INT_CERT) $(SRV_CERT)

.PHONY: info
info: pki
	@echo "==> rootCA:" && openssl x509 -in $(ROOT_CERT) -noout -subject -issuer -dates
	@echo "==> intermediateCA:" && openssl x509 -in $(INT_CERT) -noout -subject -issuer -dates
	@echo "==> server:" && openssl x509 -in $(SRV_CERT) -noout -subject -issuer -dates
	@echo "==> subjectAltName (server):" && openssl x509 -in $(SRV_CERT) -noout -ext subjectAltName

# ==== Flows ====
.PHONY: all
all: deps pki up verify

.PHONY: regen
regen: clean pki up

# ==== Clean ====
ifeq ($(OS),Windows_NT)
  RM_DIRS := if exist ca rmdir /S /Q ca & if exist server rmdir /S /Q server
  MK_DIRS := if not exist ca mkdir ca && if not exist ca\root mkdir ca\root && if not exist ca\intermediate mkdir ca\intermediate && if not exist server mkdir server
else
  RM_DIRS := rm -rf ca server
  MK_DIRS := mkdir -p ca/root ca/intermediate server
endif

.PHONY: clean
clean: down
	-@$(RM_DIRS)
	@$(MK_DIRS)
	@echo "[OK] Clean done. Recreated folders."
