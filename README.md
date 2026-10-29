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
   git submodule update --init   # the c-base-bootstrap theme under cbeamd/static
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

   From the repository root, `make test` does the same with `MQTT_ENABLED=False` already
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

## Running with podman-compose

`podman-compose.yml` runs the image with `c-beamd/` bind-mounted over the copy
inside it and the `.env` from the repository root. The make targets wrap it
and work from the repository root; they use `podman-compose` when installed
and fall back to the `docker compose` / `podman compose` plugin (override with
`COMPOSE=...`):

```bash
make build        # (re)build the image — needed after a change to requirements.txt
make up           # start in the background
make logs         # follow gunicorn's output
make restart      # after source edits
make down
```

`make up` does not run migrations (`c-beamd/start` only collects static
files), so after pulling new migrations:

```bash
make migrate
make shell                          # manage.py shell
make manage cmd="showmigrations"    # any other manage.py command
```

These run inside the running container, with `/opt/c-beamd` as working
directory, which is where a relative `DATABASE_NAME` such as `c-beam.sqlite`
resolves. While the stack is down, e.g. to migrate before the first `make up`,
add `mode=run` to start a one-off container instead: `make migrate mode=run`.

## Running with Docker

Build from the repository root:

```bash
make image     # or: docker build . -t c-beamd
```

The image ships the application at `/opt/c-beamd` and runs it as it is, so
there are two ways to start it.

**Self-contained** — nothing from the host but the environment. No `.env` and no
`local_settings.py` are baked into the image (see `.dockerignore`), and
`SECRET_KEY` has no default, so the env file has to be passed in:

```bash
make run
# or: docker run --env-file .env --name c-beamd -p 4254:4254 -it c-beamd
```

**Live source** — a bind mount at the same path shadows the copy in the image,
so the working tree runs instead and edits need no rebuild. This is the mode to
develop in, and the one that picks up a local `cbeamd/local_settings.py`:

```bash
make run-dev
# or: docker run -v "$PWD":/opt/c-beamd --name c-beamd -p 4254:4254 -it c-beamd
```

Both serve on <http://localhost:4254>.

The make targets work with either engine: they call whichever of `docker` and
`podman` is on `PATH`, docker first. Force one with `make CONTAINER=podman
run`, or pin it for this machine in an untracked `Makefile.local`
(`CONTAINER := podman`), which can also override `image`, `name` and `port`. On
an SELinux host, rootless podman may need `:z` appended to the bind mount in
`run-dev`.

The database follows `DATABASE_NAME`. Under `run` it defaults into the
container's writable layer and dies with the container; to keep it, point
`DATABASE_NAME` at `/data/c-beam.sqlite` and add `-v c-beamd-data:/data`.
Postgres needs no volume, just the `DATABASE_*` variables.

## Airlock LEDs (c_leuse)

the led stripe in the airlock is driven by `c_leuse_leds.py` from
<https://github.com/c-base/c_leuse>, which subscribes to the mqtt broker and
passes the payload of `c_leuse/led_pattern` (`C_LEUSE_LED_TOPIC`) to the
arduino firmware. the payload is a pattern name: `off`, `rainbow`,
`notbeleuchtung`, `scanning`, `success` or `failure`; the firmware shows
rainbow for anything it does not know. `set_stripe_pattern` accepts those
names as well as the numeric ids of the old cerebrum api (0 off, 1 rainbow,
2 success, 4 failure, 10 notbeleuchtung, others rainbow). speed, offset and
buffer no longer exist on this hardware; the json-rpc methods remain as no-ops.

## Push notifications (FCM)

the android app gets its pushes through firebase cloud messaging (pyfcm). the
service account json is looked up at `FCM_SERVICE_ACCOUNT_FILE`, which defaults
to `<BASE_DIR>/fcm.json` — `/opt/c-beamd/fcm.json` inside the container, where
`podman-compose.yml` mounts it. `FCM_PROJECT_ID` has to match the `project_id`
inside that file. pyfcm only opens the file on the first send, so a wrong path
shows up as "The service account file does not exist or is not a regular file"
when calling e.g. `gcm_send_test`, not at startup.

## Web assistant (c-beam fragen)

the android app's voice assistant, rebuilt for the browser: `/assistant` shows a
terminal where crew can type (or hold the microphone button and speak) a question
or a command, and the station's language model answers or proposes a tool call.
`AI-ASSISTANT.md` describes the original; `ASSISTANT-TODO.md` what was built and
how it deviates. the browser only ever talks to c-beam — django talks to the ai
server and to qdrant on its behalf, so the qdrant key never leaves the server.

the assistant needs the station's ai server (whisper, chat model, embeddings)
and the knowledge base, both reachable from the crew network only:

```
AI_URL=https://ai.cbrp3.c-base.org/ollama/v1   # empty disables the assistant
AI_MODEL=gemma4:e4b
AI_WHISPER_MODEL=Whisper-Large-v3-Turbo
AI_EMBED_MODEL=nomic-embed-text-v1-GGUF
RAG_URL=http://lazee-nerdserv.cbrp3.c-base.org:8123
RAG_KEY=                                        # empty: no knowledge base, no station_knowledge tool
RAG_COLLECTION=cbase_knowledge
KNOWLEDGE_SOURCE=qdrant                         # or sandy: sandy strands over SANDY_URL, slower
```

what the model may do is fixed in `cbeamd/assistant/tools.py`: station queries
(who is on board, bar, events, missions, artefacts, the knowledge base), login
and logout of the logged-in user, and, only after the user confirms in the
terminal, an announcement, a spoken text or a sound over c_out (shout). answers are read aloud in the
browser if the user switches that on; nothing the assistant says goes over the
station's speakers. a chat request can take up to 60 s, so a reverse proxy in
front of c-beam needs a read timeout of at least 90 s for `/assistant/`.

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
