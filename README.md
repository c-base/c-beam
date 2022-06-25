c-beam
======

c-beam backend based on django

c-beam API: https://c-beam.cbrp3.c-base.org/api (from crew network only)

Running with Docker
-------------------

`docker run -v "$PWD":/opt/c-beamd --name c-beamd -p 8000:8000 -t c-beamd`

JSON RPC
--------

- Testing with curl:
  - `curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"id","method":"eta","params":[]}' http://localhost:8000/rpc/`

- Commands:
  - who()
  - login(username)
  - ...
