"""
tests for the rfid reader registration (cbeamd/devices.py, the devices
endpoint and the usertag endpoint that checks against it).

the ldap lookup behind /usertag/seen/ and the tag event it triggers are
patched out; nothing here reaches the station.
"""

from unittest.mock import patch

from django.contrib.auth.models import User as AuthUser
from django.test import TestCase

from cbeamd.devices import assign_key, hash_key
from cbeamd.models import Device

SEEN = "/api/v1/usertag/seen/"
DEVICES = "/api/v1/devices/"


def register(device_id="esp32-a4cf12b3e9d0", name="airlock reader", **kwargs):
    """a registered device; returns (device, key in the clear)."""
    device = Device(device_id=device_id, name=name, **kwargs)
    key = assign_key(device)
    device.save()
    return device, key


def device_header(device_id, key):
    return {"HTTP_AUTHORIZATION": f"Device {device_id}:{key}"}


class DeviceModelTest(TestCase):
    def test_key_is_stored_hashed_only(self):
        device, key = register()
        self.assertNotIn(key, device.key_hash)
        self.assertEqual(device.key_hash, hash_key(key))
        self.assertEqual(len(key), 43)

    def test_device_id_is_normalized(self):
        device, _ = register(device_id="  A4:CF:12:B3:E9:D0 ")
        self.assertEqual(device.device_id, "a4:cf:12:b3:e9:d0")

    def test_str_is_name_and_id(self):
        device, _ = register()
        self.assertEqual(str(device), "airlock reader (esp32-a4cf12b3e9d0)")


@patch("cbeamd.views.api.tagevent", return_value="login")
@patch("cbeamd.views.api.LdapRfidCheck")
class UserTagDeviceCheckTest(TestCase):
    """only a registered, enabled device may post to /usertag/seen/."""

    def setUp(self):
        self.device, self.key = register()

    def _ldap_returns(self, ldap_cls, dn):
        ldap_cls.return_value.getUserForRfid.return_value = dn

    def test_registered_device_may_post(self, ldap_cls, tagevent):
        self._ldap_returns(ldap_cls, "uid=cuser,ou=crew,dc=c-base,dc=org")
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header(self.device.device_id, self.key))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"user": "cuser", "result": "login", "device": self.device.device_id})
        tagevent.assert_called_once()
        self.assertEqual(tagevent.call_args.args[1], "cuser")

    def test_device_id_in_header_is_case_insensitive(self, ldap_cls, tagevent):
        self._ldap_returns(ldap_cls, "uid=cuser,ou=crew,dc=c-base,dc=org")
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header("ESP32-A4CF12B3E9D0", self.key))
        self.assertEqual(response.status_code, 200)

    def test_last_seen_and_ip_are_recorded(self, ldap_cls, tagevent):
        self._ldap_returns(ldap_cls, "uid=cuser,ou=crew,dc=c-base,dc=org")
        self.assertIsNone(self.device.last_seen)
        self.client.post(SEEN, {"rfid": "0123"}, REMOTE_ADDR="10.0.1.23",
                         **device_header(self.device.device_id, self.key))
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.last_seen)
        self.assertEqual(self.device.last_ip, "10.0.1.23")

    def test_anonymous_post_is_refused_with_device_challenge(self, ldap_cls, tagevent):
        response = self.client.post(SEEN, {"rfid": "0123"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Device", response["WWW-Authenticate"])
        ldap_cls.assert_not_called()
        tagevent.assert_not_called()

    def test_crew_session_is_not_a_device(self, ldap_cls, tagevent):
        """a logged-in crew member (even a superuser) cannot stand in for a reader."""
        admin = AuthUser.objects.create_superuser("admin", password="not-a-real-password")
        self.client.force_login(admin)
        response = self.client.post(SEEN, {"rfid": "0123"})
        self.assertEqual(response.status_code, 401)
        tagevent.assert_not_called()

    def test_wrong_key_is_refused(self, ldap_cls, tagevent):
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header(self.device.device_id, "x" * 43))
        self.assertEqual(response.status_code, 401)
        self.assertIn("unknown device or wrong key", response.json()["detail"])
        tagevent.assert_not_called()

    def test_unknown_device_is_refused(self, ldap_cls, tagevent):
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header("nope", self.key))
        self.assertEqual(response.status_code, 401)
        tagevent.assert_not_called()

    def test_disabled_device_is_refused(self, ldap_cls, tagevent):
        Device.objects.filter(pk=self.device.pk).update(enabled=False)
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header(self.device.device_id, self.key))
        self.assertEqual(response.status_code, 401)
        self.assertIn("disabled", response.json()["detail"])
        tagevent.assert_not_called()

    def test_malformed_credentials_are_refused(self, ldap_cls, tagevent):
        for value in ("Device", "Device onlyid", "Device :key", "Device id:"):
            with self.subTest(header=value):
                response = self.client.post(SEEN, {"rfid": "0123"}, HTTP_AUTHORIZATION=value)
                self.assertEqual(response.status_code, 401)
        tagevent.assert_not_called()

    def test_other_schemes_are_ignored(self, ldap_cls, tagevent):
        """a bearer token is not device credentials; the request is simply anonymous."""
        response = self.client.post(SEEN, {"rfid": "0123"}, HTTP_AUTHORIZATION="Bearer sometoken")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Device", response["WWW-Authenticate"])

    def test_rfid_still_required(self, ldap_cls, tagevent):
        response = self.client.post(SEEN, {}, **device_header(self.device.device_id, self.key))
        self.assertEqual(response.status_code, 400)

    def test_unknown_rfid_is_404(self, ldap_cls, tagevent):
        self._ldap_returns(ldap_cls, None)
        response = self.client.post(SEEN, {"rfid": "0123"}, **device_header(self.device.device_id, self.key))
        self.assertEqual(response.status_code, 404)
        tagevent.assert_not_called()


class DeviceEndpointPermissionTest(TestCase):
    """/api/v1/devices/ is for staff accounts only."""

    def test_anonymous_is_refused(self):
        self.assertEqual(self.client.get(DEVICES).status_code, 401)

    def test_crew_member_without_staff_flag_is_refused(self):
        user = AuthUser.objects.create_user("crew", password="not-a-real-password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(DEVICES).status_code, 403)
        response = self.client.post(DEVICES, {"device_id": "x", "name": "y"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Device.objects.exists())

    def test_a_device_cannot_manage_devices(self):
        device, key = register()
        response = self.client.get(DEVICES, **device_header(device.device_id, key))
        self.assertEqual(response.status_code, 401)


class DeviceEndpointTest(TestCase):
    def setUp(self):
        self.admin = AuthUser.objects.create_user("admin", password="not-a-real-password", is_staff=True)
        self.client.force_login(self.admin)

    def test_create_returns_the_key_once(self):
        response = self.client.post(DEVICES, {
            "device_id": "ESP32-A4CF12B3E9D0", "name": "airlock reader", "location": "schleuse",
        })
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        key = data["key"]
        self.assertEqual(len(key), 43)
        self.assertEqual(data["device_id"], "esp32-a4cf12b3e9d0")
        device = Device.objects.get(device_id="esp32-a4cf12b3e9d0")
        self.assertEqual(device.key_hash, hash_key(key))
        self.assertEqual(device.location, "schleuse")
        self.assertTrue(device.enabled)

        # neither list nor retrieve ever shows a key, hashed or otherwise
        for url in (DEVICES, f"{DEVICES}{device.pk}/"):
            body = self.client.get(url).json()
            entries = body if isinstance(body, list) else [body]
            for entry in entries:
                self.assertNotIn("key", entry)
                self.assertNotIn("key_hash", entry)

    def test_create_rejects_duplicate_id_regardless_of_case(self):
        register(device_id="esp32-a4cf12b3e9d0")
        response = self.client.post(DEVICES, {"device_id": "ESP32-A4CF12B3E9D0", "name": "clone"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("device_id", response.json())
        self.assertEqual(Device.objects.count(), 1)

    def test_list(self):
        register(device_id="one", name="b reader")
        register(device_id="two", name="a reader")
        response = self.client.get(DEVICES)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([d["name"] for d in response.json()], ["a reader", "b reader"])

    def test_disable_via_patch(self):
        device, _ = register()
        response = self.client.patch(f"{DEVICES}{device.pk}/", {"enabled": False}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertFalse(device.enabled)

    def test_update_cannot_touch_the_key(self):
        device, key = register()
        response = self.client.patch(f"{DEVICES}{device.pk}/", {"key": "mine", "key_hash": "0" * 64},
                                     content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertEqual(device.key_hash, hash_key(key))

    def test_rotate_key_invalidates_the_old_one(self):
        device, old_key = register()
        response = self.client.post(f"{DEVICES}{device.pk}/rotate_key/")
        self.assertEqual(response.status_code, 200, response.content)
        new_key = response.json()["key"]
        self.assertNotEqual(new_key, old_key)
        device.refresh_from_db()
        self.assertEqual(device.key_hash, hash_key(new_key))
        with patch("cbeamd.views.api.LdapRfidCheck") as ldap_cls, patch("cbeamd.views.api.tagevent", return_value="login"):
            ldap_cls.return_value.getUserForRfid.return_value = "uid=cuser,ou=crew,dc=c-base,dc=org"
            self.client.logout()
            self.assertEqual(self.client.post(SEEN, {"rfid": "1"}, **device_header(device.device_id, old_key)).status_code, 401)
            self.assertEqual(self.client.post(SEEN, {"rfid": "1"}, **device_header(device.device_id, new_key)).status_code, 200)

    def test_delete(self):
        device, _ = register()
        response = self.client.delete(f"{DEVICES}{device.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Device.objects.exists())


class DeviceAdminTest(TestCase):
    """the django admin generates the key on add and shows it once."""

    def setUp(self):
        self.admin = AuthUser.objects.create_superuser("admin", password="not-a-real-password")
        self.client.force_login(self.admin)

    def test_add_shows_the_key_once(self):
        response = self.client.post("/admin/cbeamd/device/add/", {
            "device_id": "ESP32-A4CF12B3E9D0", "name": "airlock reader", "location": "", "notes": "",
            "enabled": "on",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        device = Device.objects.get(device_id="esp32-a4cf12b3e9d0")
        shown = [m.message for m in response.context["messages"] if "key fu:r" in m.message]
        self.assertEqual(len(shown), 1)
        key = shown[0].split(": ", 1)[1].split(" ")[0]
        self.assertEqual(device.key_hash, hash_key(key))

    def test_add_rejects_duplicate_id_regardless_of_case(self):
        register(device_id="esp32-a4cf12b3e9d0")
        response = self.client.post("/admin/cbeamd/device/add/", {
            "device_id": "ESP32-A4CF12B3E9D0", "name": "clone", "location": "", "notes": "", "enabled": "on",
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.assertEqual(Device.objects.count(), 1)

    def test_rotate_key_action(self):
        device, old_key = register()
        response = self.client.post("/admin/cbeamd/device/", {
            "action": "rotate_key", "_selected_action": [device.pk],
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertNotEqual(device.key_hash, hash_key(old_key))
        shown = [m.message for m in response.context["messages"] if "key fu:r" in m.message]
        self.assertEqual(len(shown), 1)

    def test_non_staff_cannot_open_the_admin(self):
        self.client.logout()
        user = AuthUser.objects.create_user("crew", password="not-a-real-password")
        self.client.force_login(user)
        response = self.client.get("/admin/cbeamd/device/")
        self.assertEqual(response.status_code, 302)
