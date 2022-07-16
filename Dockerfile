FROM python:3.10

VOLUME /opt/c-beamd

RUN apt-get install -y python3-dev libldap2-dev libsasl2-dev ldap-utils

ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r /requirements.txt

EXPOSE 8000
ENTRYPOINT ["/opt/c-beamd/start"]



