mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))
env_file := $(current_dir)/../.env

# the image carries the source, so `docker-run` needs nothing from the host but
# the environment — no .env and no local_settings.py are baked into it, and
# SECRET_KEY has no default. `docker-run-dev` mounts this directory over the
# copy in the image instead: same image, same paths, edits without a rebuild.
#
# the database follows DATABASE_NAME. under docker-run it lives in the
# container's writable layer and dies with it; point DATABASE_NAME at
# /data/c-beam.sqlite and add -v c-beamd-data:/data to keep it.

docker-image:
	docker build .. -t c-beamd

docker-run:
	@test -f "$(env_file)" || { echo "no .env at $(env_file) — cp .env.example .env and set SECRET_KEY"; exit 1; }
	docker rm -f c-beamd; docker run --env-file "$(env_file)" --name c-beamd -p 4254:8000 -t c-beamd

docker-run-dev:
	docker rm -f c-beamd; docker run -v "$(current_dir)":/opt/c-beamd --name c-beamd -p 4254:8000 -t c-beamd

.PHONY: docker-image docker-run docker-run-dev
