"""
static files in production: the proxy at the station has no /static/
location, so the app has to serve its collected files itself (whitenoise).
"""

import tempfile

import pytest
from django.core.management import call_command
from django.test import Client, override_settings


# the 404 for a missing file falls through to django, whose error page renders
# the assistant's context processor, which looks the user up in the session
@pytest.mark.django_db
def test_collected_static_files_are_served_with_debug_off():
    with tempfile.TemporaryDirectory() as root:
        with override_settings(STATIC_ROOT=root, DEBUG=False):
            call_command('collectstatic', interactive=False, verbosity=0)
            client = Client()   # a fresh middleware stack, scanning the new STATIC_ROOT
            response = client.get('/static/assistant.js')
            assert response.status_code == 200
            assert b'cbeamAssistant' in b''.join(response.streaming_content)
            response.close()   # whitenoise streams the file; unclosed, it is a ResourceWarning
            response = client.get('/static/assistant.css')
            assert response.status_code == 200
            assert response['Content-Type'].startswith('text/css')
            response.close()
            assert client.get('/static/does-not-exist.js').status_code == 404
