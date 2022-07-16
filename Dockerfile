FROM python:3.10

VOLUME /opt/c-beamd

RUN apt-get update && apt-get install -y python3-dev libldap2-dev libsasl2-dev ldap-utils 

ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r /requirements.txt
RUN pip install /opt/c-beamd/wheels/django_json_rpc-0.7.2-py3-none-any.whl

EXPOSE 8000
ENTRYPOINT ["/opt/c-beamd/c-beamd/start"]



