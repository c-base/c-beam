mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))

docker-image:
	docker build .. -t c-beamd

docker-run:
	docker rm -f c-beamd; docker run -v "$(current_dir)":/opt/c-beamd --name c-beamd -p 4254:8000 -t c-beamd