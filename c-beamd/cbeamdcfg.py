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

# set MQTT_ENABLED=False for development away from the c-base network, so that
# publish() short-circuits instead of waiting on a broker it cannot reach
mqtt_enabled = config('MQTT_ENABLED', default=True, cast=bool)
mqtt_server = config('MQTT_SERVER', default='c-beam.cbrp3.c-base.org')
mqtt_server_tls = config('MQTT_SERVER_TLS', default=False, cast=bool)
mqtt_server_cert = config('MQTT_SERVER_CERT', default='/etc/ssl/certs/c-beam-mqtt.crt')

# json-rpc endpoints of the collaborating c-base services. these were previously
# hardcoded ServiceProxy() calls, commented out, which left every call site
# raising NameError. set a url to an empty string to disable that client.
service_timeout = config('SERVICE_TIMEOUT', default=5, cast=int)
cout_url = config('COUT_URL', default='http://shout.cbrp3.c-base.org:1775/')
cerebrum_url = config('CEREBRUM_URL', default='http://c-leuse.cbrp3.c-base.org:7777/')
monitord_url = config('MONITORD_URL', default='http://c-leuse.cbrp3.c-base.org:9090/')
nerdctrl_cout_url = config('NERDCTRL_COUT_URL', default='http://nerdctrl.cbrp3.c-base.org:1775/')
c_leuse_c_out_url = config('C_LEUSE_C_OUT_URL', default='http://c-leuse.cbrp3.c-base.org:1775/')
ampelrpc_url = config('AMPELRPC_URL', default='http://10.0.1.24:1337/')
