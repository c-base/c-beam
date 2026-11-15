"""
authentication for registered station devices (rfid readers).

a reader is registered by an admin (django admin or /api/v1/devices/) and
receives a random key once, at registration. it then sends

    Authorization: Device <device_id>:<key>

with every request. the device id is the reader's hardware id — on an esp32
the factory mac from the efuse, written as lowercase hex — and names the
device; the key proves it. hardware ids can be read off the air and cloned,
which is why the id alone is never enough. only the sha256 of the key is
stored, the key itself is shown exactly once.

`DeviceAuthentication` is a drf authentication class; a request it accepts
carries the `Device` row in `request.auth`. `IsRegisteredDevice` is the
matching permission. views that are meant for readers only (the usertag
endpoint) use the two together, replacing the default session / bearer
classes — a crew member's session does not make a reader.
"""

import hashlib
import hmac
import logging
import secrets

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication, exceptions, permissions

from .models import Device, normalize_device_id

logger = logging.getLogger(__name__)

SCHEME = 'device'


def generate_key() -> str:
    """a fresh device key: 32 random bytes, url-safe base64 (43 characters)."""
    return secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    # an unsalted hash is fine here: the key is 256 random bits, not a
    # password, so it cannot be looked up in a table or guessed offline
    return hashlib.sha256(key.encode()).hexdigest()


def assign_key(device: Device) -> str:
    """
    give `device` a new key and return it in the clear. the caller shows it to
    the admin once; it is not stored. does not save the device.
    """
    key = generate_key()
    device.key_hash = hash_key(key)
    return key


def device_credentials(request):
    """
    (device_id, key) from an `Authorization: Device …` header, or None when
    the header is absent or carries another scheme. a header with the right
    scheme but a malformed value raises AuthenticationFailed.
    """
    header = request.META.get('HTTP_AUTHORIZATION', '')
    scheme, _, value = header.partition(' ')
    if scheme.lower() != SCHEME:
        return None
    device_id, sep, key = value.strip().partition(':')
    if not sep or not device_id.strip() or not key.strip():
        raise exceptions.AuthenticationFailed("device credentials must be '<device_id>:<key>'")
    return normalize_device_id(device_id), key.strip()


def authenticate_device(request) -> Device:
    """
    the registered, enabled device behind the request's credentials, or
    AuthenticationFailed. the remote address and time are recorded on success.
    """
    credentials = device_credentials(request)
    if credentials is None:
        return None
    device_id, key = credentials

    device = Device.objects.filter(device_id=device_id).first()
    # compare against a real hash even for unknown ids, so the timing does not
    # tell the two cases apart
    expected = device.key_hash if device else hash_key('')
    if not hmac.compare_digest(hash_key(key), expected) or device is None:
        logger.warning("device auth failed for %r from %s", device_id, request.META.get('REMOTE_ADDR'))
        raise exceptions.AuthenticationFailed("unknown device or wrong key")
    if not device.enabled:
        logger.warning("disabled device %s tried to authenticate", device)
        raise exceptions.AuthenticationFailed("device is disabled")

    Device.objects.filter(pk=device.pk).update(
        last_seen=timezone.now(), last_ip=request.META.get('REMOTE_ADDR') or None)
    return device


class DeviceAuthentication(authentication.BaseAuthentication):
    """drf authentication class: `request.auth` is the Device, there is no user."""

    def authenticate(self, request):
        device = authenticate_device(request._request)
        if device is None:
            return None
        return (AnonymousUser(), device)

    def authenticate_header(self, request):
        return 'Device realm="c-beam"'


class IsRegisteredDevice(permissions.BasePermission):
    message = "only registered devices may call this"

    def has_permission(self, request, view):
        return isinstance(request.auth, Device)


class DeviceAuthenticationScheme(OpenApiAuthenticationExtension):
    """documents the header in the openapi schema at /api/schema/."""
    target_class = 'cbeamd.devices.DeviceAuthentication'
    name = 'deviceAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Device <device_id>:<key>, as issued at registration',
        }
