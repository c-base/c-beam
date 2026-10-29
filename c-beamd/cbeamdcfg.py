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

# the airlock led stripe listens on the broker (c_leuse_leds.py in
# github.com/c-base/c_leuse subscribes to c_leuse/+ and only acts on this one)
c_leuse_led_topic = config('C_LEUSE_LED_TOPIC', default='c_leuse/led_pattern')

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

# the station's ai server (lemonade/llama.cpp behind an ollama-style facade) and
# the knowledge base behind the web assistant, see AI-ASSISTANT.md and
# ASSISTANT-TODO.md. the browser never talks to these directly; django does, so
# the qdrant key stays here. leave AI_URL empty to switch the assistant off.
ai_url = config('AI_URL', default='https://ai.cbrp3.c-base.org/ollama/v1')
ai_model = config('AI_MODEL', default='gemma4:e4b')
ai_whisper_model = config('AI_WHISPER_MODEL', default='Whisper-Large-v3-Turbo')
ai_embed_model = config('AI_EMBED_MODEL', default='nomic-embed-text-v1-GGUF')
ai_connect_timeout = config('AI_CONNECT_TIMEOUT', default=5, cast=int)
ai_read_timeout = config('AI_READ_TIMEOUT', default=60, cast=int)
# qdrant. without RAG_KEY the station_knowledge tool is not offered to the model
rag_url = config('RAG_URL', default='http://lazee-nerdserv.cbrp3.c-base.org:8123')
rag_key = config('RAG_KEY', default='')
rag_collection = config('RAG_COLLECTION', default='cbase_knowledge')
# which source station_knowledge uses: 'qdrant' (above) or 'sandy', the station's
# own assistant with its rag, over its voice websocket (text only, 10 to 90 s)
knowledge_source = config('KNOWLEDGE_SOURCE', default='qdrant')
sandy_url = config('SANDY_URL', default='wss://ai.cbrp3.c-base.org:8444/ws/voice')
