# -*- coding: utf-8 -*-
"""
static configuration for the c-beam daemon.

secrets belong in the environment (or .env), not in this file — it is tracked in
git. use decouple's config() for anything that must not be shared, and keep the
plain assignments below for values that are safe to publish.
"""

from decouple import config

# CONFIG BEGIN ######################################################################
userdir = "/home/c-beam/users"
vuserdir = "/home/c-beam/vusers"
datafile = "/home/c-beam/c-beam.data"
c_outurl = "http://shout:1775"
monitorurl = "http://10.0.1.27:9090"
logfile = config('CBEAM_LOGFILE', default='/var/log/c-beam/c-beam.log')
logindelta = 30
eta_timeout = 120
etd_timeout = 20
timeoutdelta = 600
ttsgreeting = "hallo %s, willkommen an bord"
ttsenabled = 1
sampledir = "/home/c-beam"
mqtt_client_name = config('MQTT_CLIENT_NAME', default='c-beam')
mqtt_client_password = config('MQTT_CLIENT_PASSWORD', default='')
# CONFIG END ########################################################################

mqtt_server = config('MQTT_SERVER', default='c-beam.cbrp3.c-base.org')
mqtt_server_tls = config('MQTT_SERVER_TLS', default=False, cast=bool)
mqtt_server_cert = config('MQTT_SERVER_CERT', default='/etc/ssl/certs/c-beam-mqtt.crt')
