mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))
env_file := $(current_dir)/../.env

# container engine: whichever of docker/podman is on PATH, docker first.
# override per invocation (`make CONTAINER=podman docker-run`), per shell
# (`export CONTAINER=podman`) or permanently in a local config file — see
# Makefile.local below. the flags used here are the same for both engines.
#
# on an SELinux host, rootless podman needs a relabelled bind mount for
# docker-run-dev; add :z to the -v argument there if the container cannot
# read the source.
CONTAINER ?= $(shell for c in docker podman; do command -v $$c >/dev/null 2>&1 && { echo $$c; break; }; done)

image ?= c-beamd
name ?= c-beamd
port ?= 4254

# optional, untracked: a place to pin CONTAINER/port/image for this machine
-include $(current_dir)/Makefile.local

# the image carries the source, so `docker-run` needs nothing from the host but
# the environment — no .env and no local_settings.py are baked into it, and
# SECRET_KEY has no default. `docker-run-dev` mounts this directory over the
# copy in the image instead: same image, same paths, edits without a rebuild.
#
# the database follows DATABASE_NAME. under docker-run it lives in the
# container's writable layer and dies with it; point DATABASE_NAME at
# /data/c-beam.sqlite and add -v c-beamd-data:/data to keep it.

docker-image: check-engine
	$(CONTAINER) build .. -t $(image)

docker-run: check-engine
	@test -f "$(env_file)" || { echo "no .env at $(env_file) — cp .env.example .env and set SECRET_KEY"; exit 1; }
	$(CONTAINER) rm -f $(name); $(CONTAINER) run --env-file "$(env_file)" --name $(name) -p $(port):8000 -t $(image)

docker-run-dev: check-engine
	$(CONTAINER) rm -f $(name); $(CONTAINER) run -v "$(current_dir)":/opt/c-beamd --name $(name) -p $(port):8000 -t $(image)

check-engine:
	@test -n "$(CONTAINER)" || { echo "neither docker nor podman found on PATH — install one, or run make CONTAINER=<engine>"; exit 1; }
	@command -v $(CONTAINER) >/dev/null 2>&1 || { echo "CONTAINER is set to '$(CONTAINER)', which is not on PATH"; exit 1; }

.PHONY: docker-image docker-run docker-run-dev check-engine
