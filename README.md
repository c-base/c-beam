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
   pytest
   ```

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

`docker run -v "$PWD":/opt/c-beamd --name c-beamd -p 8000:8000 -t c-beamd`

## JSON RPC

- Testing with curl:
  - `curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"id","method":"eta","params":[]}' http://localhost:8000/rpc/`

- Commands:
  - who()
  - login(username)
  - ...
