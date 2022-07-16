FROM python:3.10

VOLUME /opt/c-beamd

RUN apt install libsasl2-dev python-dev libldap2-dev libssl-dev

ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r /requirements.txt

EXPOSE 8000
ENTRYPOINT ["/opt/c-beamd/start"]



