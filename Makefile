mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
repo_root := $(patsubst %/,%,$(dir $(mkfile_path)))
app_dir := $(repo_root)/c-beamd
env_file := $(repo_root)/.env
compose_file := $(repo_root)/podman-compose.yml

# container engine: whichever of docker/podman is on PATH, docker first.
# override per invocation (`make CONTAINER=podman run`), per shell
# (`export CONTAINER=podman`) or permanently in a local config file — see
# Makefile.local below. the flags used here are the same for both engines.
#
# on an SELinux host, rootless podman needs a relabelled bind mount for
# run-dev; add :z to the -v argument there if the container cannot
# read the source.
#
# the run targets attach with -it, not just -t. with a tty but no stdin the
# terminal is in raw mode, so ctrl-c neither becomes a SIGINT for the client
# nor reaches the container as ^C — the only way out is `stop` from another
# shell. with stdin attached the ^C travels through the pty to gunicorn.
CONTAINER ?= $(shell for c in docker podman; do command -v $$c >/dev/null 2>&1 && { echo $$c; break; }; done)

# compose frontend for podman-compose.yml: podman-compose when installed,
# otherwise the compose plugin of whichever engine has one. override with
# `make COMPOSE="docker compose" up` or in Makefile.local.
COMPOSE ?= $(shell if command -v podman-compose >/dev/null 2>&1; then echo podman-compose; \
	elif docker compose version >/dev/null 2>&1; then echo "docker compose"; \
	elif podman compose version >/dev/null 2>&1; then echo "podman compose"; fi)
compose := $(COMPOSE) -f $(compose_file)

image ?= c-beamd:latest
name ?= c-beamd
port ?= 4254
# the service in podman-compose.yml that runs django
service ?= cbeam

# optional, untracked: a place to pin CONTAINER/COMPOSE/port/image for this machine
-include $(repo_root)/Makefile.local

# tests run from the repository root, where pytest.ini lives. MQTT_ENABLED
# defaults to False so a test run never waits on a broker it cannot reach;
# override with `make MQTT_ENABLED=True test` inside the c-base network.
MQTT_ENABLED ?= False

test:
	cd $(repo_root) && MQTT_ENABLED=$(MQTT_ENABLED) pytest

coverage:
	cd $(repo_root) && MQTT_ENABLED=$(MQTT_ENABLED) pytest --cov --cov-report=term-missing

coverage-html:
	cd $(repo_root) && MQTT_ENABLED=$(MQTT_ENABLED) pytest --cov --cov-report=html
	@echo "open $(repo_root)/htmlcov/index.html"

# --- compose ---------------------------------------------------------------
#
# podman-compose.yml runs the image with c-beamd/ bind-mounted over the copy
# inside, so source edits only need `make restart`; a change to
# requirements.txt needs `make build` (the image installs them) and a restart.
#
# `make up` does not migrate: c-beamd/start only collects static files. run
# `make migrate` after pulling new migrations.

build: check-compose
	$(compose) build

up: check-compose
	@test -f "$(env_file)" || { echo "no .env at $(env_file) — cp .env.example .env and set SECRET_KEY"; exit 1; }
	$(compose) up -d

down: check-compose
	$(compose) down

restart: check-compose
	$(compose) restart $(service)

logs: check-compose
	$(compose) logs -f $(service)

ps: check-compose
	$(compose) ps

# manage.py inside the running container, with the compose environment and
# /opt/c-beamd as working directory (where a relative DATABASE_NAME resolves):
#
#   make manage cmd="showmigrations"
#   make shell
#   make migrate
#
# while the stack is down, e.g. to migrate before the first `make up`, the
# same targets with mode=run start a one-off container instead:
#
#   make migrate mode=run
mode ?= exec
ifeq ($(mode),run)
manage_py := $(compose) run --rm --entrypoint python $(service) manage.py
else
manage_py := $(compose) exec $(service) python manage.py
endif

manage: check-compose
	@test -n "$(cmd)" || { echo 'usage: make manage cmd="<manage.py arguments>"'; exit 1; }
	$(manage_py) $(cmd)

shell: check-compose
	$(manage_py) shell

migrate: check-compose
	$(manage_py) migrate

check-compose:
	@test -n "$(COMPOSE)" || { echo "no compose frontend found — install podman-compose or the docker compose plugin, or run make COMPOSE=<command>"; exit 1; }
	@test -f "$(compose_file)" || { echo "no compose file at $(compose_file)"; exit 1; }

# --- single container, without compose -------------------------------------
#
# the image carries the source, so `run` needs nothing from the host but
# the environment — no .env and no local_settings.py are baked into it, and
# SECRET_KEY has no default. `run-dev` mounts c-beamd/ over the copy in the
# image instead: same image, same paths, edits without a rebuild.
#
# the database follows DATABASE_NAME. under `run` it lives in the
# container's writable layer and dies with it; point DATABASE_NAME at
# /data/c-beam.sqlite and add -v c-beamd-data:/data to keep it.

image: check-engine
	$(CONTAINER) build --network=host $(repo_root) -t $(image)

run: check-engine
	@test -f "$(env_file)" || { echo "no .env at $(env_file) — cp .env.example .env and set SECRET_KEY"; exit 1; }
	$(CONTAINER) rm -f $(name); $(CONTAINER) run --network=host --env-file "$(env_file)" --name $(name) -p $(port):4254 -it $(image)

run-dev: check-engine
	$(CONTAINER) rm -f $(name); $(CONTAINER) run -v "$(app_dir)":/opt/c-beamd --name $(name) -p $(port):4254 -it $(image)

check-engine:
	@test -n "$(CONTAINER)" || { echo "neither docker nor podman found on PATH — install one, or run make CONTAINER=<engine>"; exit 1; }
	@command -v $(CONTAINER) >/dev/null 2>&1 || { echo "CONTAINER is set to '$(CONTAINER)', which is not on PATH"; exit 1; }

.PHONY: test coverage coverage-html build up down restart logs ps manage shell migrate check-compose image run run-dev check-engine
