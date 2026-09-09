c-beam
======

c-beam backend based on django

c-beam API: https://c-beam.cbrp3.c-base.org/api (from crew network only)

## Security Notice

⚠️ **Important**: This application has been updated with security improvements. The `SECRET_KEY` is no longer hardcoded and must be set via environment variables.

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd c-beam
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   cd c-beamd
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run tests**
   ```bash
   pytest                        # from the repository root
   MQTT_ENABLED=False pytest     # away from the c-base network
   ```

   From `c-beamd/`, `make test` does the same with `MQTT_ENABLED=False` already
   set, `make coverage` adds a line and branch coverage report, and
   `make coverage-html` writes a browsable one to `htmlcov/`.

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_*`: Database configuration (use PostgreSQL in production)
- `CSRF_TRUSTED_ORIGINS`: Trusted origins for CSRF protection

## Running with Docker

Build from the repository root:

```bash
cd c-beamd && make docker-image     # or: docker build . -t c-beamd
```

The image ships the application at `/opt/c-beamd` and runs it as it is, so
there are two ways to start it.

**Self-contained** — nothing from the host but the environment. No `.env` and no
`local_settings.py` are baked into the image (see `.dockerignore`), and
`SECRET_KEY` has no default, so the env file has to be passed in:

```bash
make docker-run
# or: docker run --env-file .env --name c-beamd -p 4254:8000 -t c-beamd
```

**Live source** — a bind mount at the same path shadows the copy in the image,
so the working tree runs instead and edits need no rebuild. This is the mode to
develop in, and the one that picks up a local `cbeamd/local_settings.py`:

```bash
make docker-run-dev
# or: docker run -v "$PWD":/opt/c-beamd --name c-beamd -p 4254:8000 -t c-beamd
```

Both serve on <http://localhost:4254>.

The make targets work with either engine: they call whichever of `docker` and
`podman` is on `PATH`, docker first. Force one with `make CONTAINER=podman
docker-run`, or pin it for this machine in an untracked `c-beamd/Makefile.local`
(`CONTAINER := podman`), which can also override `image`, `name` and `port`. On
an SELinux host, rootless podman may need `:z` appended to the bind mount in
`docker-run-dev`.

The database follows `DATABASE_NAME`. Under `docker-run` it defaults into the
container's writable layer and dies with the container; to keep it, point
`DATABASE_NAME` at `/data/c-beam.sqlite` and add `-v c-beamd-data:/data`.
Postgres needs no volume, just the `DATABASE_*` variables.

## JSON RPC

- Testing with curl:
  - `curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"id","method":"eta","params":[]}' http://localhost:8000/rpc/`

- Commands:
  - who()
  - login(username)

### authenticating as a crew member (android app, own clients)

c-beam accepts oauth2 bearer tokens issued by the c-base identity provider on
both the json-rpc endpoint and the rest api:

    Authorization: Bearer <access token>

log in at the identity provider (`https://c-base.org/oauth/`) with
authorization code + pkce, then send the access token with every request. the
idp currently issues opaque access tokens; c-beam checks those through the
idp's introspection endpoint and takes the crew nickname from the `username`
it reports. jwt access tokens are validated locally against the idp's jwks
instead — that is the form the mqtt broker needs, should the idp switch.
json-rpc methods marked as authenticated answer error `-32000` (http 401) with
the reason in `error.data` when the token is missing or refused; the rest api
answers 401 with a `WWW-Authenticate: Bearer` challenge.

the web ui can log in through the same identity provider: `/login/` shows the
password form for local accounts plus a "mit c-base-account anmelden" button
for crew members.

operators configure this through the `OAUTH_*` entries in `.env.example`.

  - ...
