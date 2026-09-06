FROM python:3.14

# the image ships the application at /opt/c-beamd, which is also where the
# repo's c-beamd/ directory gets bind-mounted. a mount shadows the baked-in
# copy, so one image serves both modes:
#
#   self-contained   docker run -p 4254:8000 c-beamd
#   live source      docker run -p 4254:8000 -v "$PWD":/opt/c-beamd c-beamd
#
# nothing is declared as a VOLUME on purpose — that would hand every plain
# `docker run` an anonymous volume seeded from the image and hide later rebuilds.

# python-ldap builds from source and needs these headers
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-dev libldap2-dev libsasl2-dev ldap-utils \
    && rm -rf /var/lib/apt/lists/*

# requirements first, so a source change does not reinstall the world
ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r /requirements.txt

# the build context is the repo root; only the django project belongs in the
# image, laid out exactly as the bind mount lays it out
COPY c-beamd/ /opt/c-beamd/

# manage.py and preise.csv sit here and are reached by relative path
WORKDIR /opt/c-beamd

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
ENTRYPOINT ["/opt/c-beamd/start"]
