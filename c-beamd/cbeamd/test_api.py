"""
Tests for the DRF surface in views/api.py.

The viewsets had no coverage at all: the suite imported them, so every `def`
line counted as covered, but no request ever reached one. These tests drive
the six registered viewsets through the router at /api/v1/.

Nothing here talks to station hardware. The two viewsets that would leave the
machine — Events (feedparser against www.c-base.org) and Matelight (http to
matelight.cbrp3.c-base.org) — are exercised against patched collaborators, so
the tests pass away from the c-base network.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User as AuthUser
from django.test import TestCase
from django.utils import timezone

from cbeamd.models import Status, User


def make_user(username, status="online", **kwargs):
    """A c-base crew member. username/status/logintime/logouttime have no defaults."""
    now = timezone.now()
    return User.objects.create(
        username=username,
        status=status,
        logintime=kwargs.pop("logintime", now),
        logouttime=kwargs.pop("logouttime", now + timedelta(hours=1)),
        **kwargs,
    )


class ApiTestCase(TestCase):
    """Base case that logs in a django auth user; every viewset is IsAuthenticated."""

    def setUp(self):
        self.auth_user = AuthUser.objects.create_user("tester", password="not-a-real-password")
        self.client.force_login(self.auth_user)


class ApiAuthenticationTest(TestCase):
    """Every endpoint below is permission_classes = [IsAuthenticated]."""

    endpoints = [
        "/api/v1/users/",
        "/api/v1/member/",
        "/api/v1/prices/",
        "/api/v1/events/",
        "/api/v1/barstatus/",
        "/api/v1/matelight/",
    ]

    def test_anonymous_access_is_refused(self):
        for url in self.endpoints:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_anonymous_write_is_refused(self):
        response = self.client.post("/api/v1/users/", {"username": "intruder"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="intruder").exists())


class UserApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.crew = make_user("cuser", status="online", ap=42)

    def test_list_returns_users(self):
        make_user("other", status="offline")
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        usernames = [u["username"] for u in response.json()]
        self.assertCountEqual(usernames, ["cuser", "other"])

    def test_retrieve_returns_the_serializer_fields(self):
        response = self.client.get(f"/api/v1/users/{self.crew.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "cuser")
        self.assertEqual(data["status"], "online")
        # the three SerializerMethodFields, which the model computes
        self.assertIn("autologout_in", data)
        self.assertIn("online_percentage", data)
        self.assertIn("ap", data)

    def test_ap_is_computed_not_the_stored_column(self):
        """`ap` is a read-only method field backed by calc_ap(), not User.ap."""
        response = self.client.get(f"/api/v1/users/{self.crew.id}/")
        self.assertEqual(response.json()["ap"], self.crew.calc_ap())
        self.assertNotEqual(response.json()["ap"], self.crew.ap)

    def test_create(self):
        now = timezone.now()
        response = self.client.post("/api/v1/users/", {
            "username": "newcrew",
            "status": "offline",
            "logintime": now.isoformat(),
            "logouttime": (now + timedelta(hours=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="newcrew").exists())

    def test_create_rejects_a_duplicate_username(self):
        now = timezone.now()
        response = self.client.post("/api/v1/users/", {
            "username": "cuser",
            "status": "offline",
            "logintime": now.isoformat(),
            "logouttime": now.isoformat(),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())

    def test_partial_update(self):
        response = self.client.patch(
            f"/api/v1/users/{self.crew.id}/",
            data={"status": "offline"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.crew.refresh_from_db()
        self.assertEqual(self.crew.status, "offline")

    def test_read_only_fields_are_ignored_on_write(self):
        response = self.client.patch(
            f"/api/v1/users/{self.crew.id}/",
            data={"ap": 9999},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.crew.refresh_from_db()
        self.assertEqual(self.crew.ap, 42)

    def test_delete(self):
        response = self.client.delete(f"/api/v1/users/{self.crew.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(id=self.crew.id).exists())


class MemberApiTest(ApiTestCase):
    def test_list_returns_only_online_members_by_username(self):
        make_user("zaphod", status="online")
        make_user("arthur", status="online")
        make_user("marvin", status="offline")
        make_user("trillian", status="eta")

        response = self.client.get("/api/v1/member/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([u["username"] for u in response.json()], ["arthur", "zaphod"])

    def test_list_is_empty_when_nobody_is_aboard(self):
        make_user("marvin", status="offline")
        self.assertEqual(self.client.get("/api/v1/member/").json(), [])


class PriceApiTest(ApiTestCase):
    def test_list_returns_the_price_list(self):
        prices = [{"name": "club mate", "price": "1.50"}]
        # get_prices() reads preise.csv relative to the process cwd, so it is
        # patched here rather than depending on where pytest was started.
        with patch("cbeamd.views.api.get_prices", return_value=prices) as get_prices:
            response = self.client.get("/api/v1/prices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), prices)
        get_prices.assert_called_once_with()


class EventApiTest(ApiTestCase):
    def test_list_returns_todays_events(self):
        events = [{"title": "plenum", "start": "2000", "end": "2200"}]
        with patch("cbeamd.views.api.event_list", return_value=events) as event_list:
            response = self.client.get("/api/v1/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), events)
        event_list.assert_called_once()


class BarApiTest(ApiTestCase):
    def test_list_reports_the_bar_status(self):
        Status.objects.create(bar_open=True)
        response = self.client.get("/api/v1/barstatus/")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json(), True)

    def test_list_reports_a_closed_bar(self):
        Status.objects.create(bar_open=False)
        self.assertIs(self.client.get("/api/v1/barstatus/").json(), False)


class MatelightApiTest(ApiTestCase):
    videos = [
        {"title": "fnord", "thumbnailName": "fnord.jpg"},
        {"title": "nyan", "thumbnailName": "nyan.jpg"},
    ]

    def mock_get(self, payload=None, content=b""):
        """Stand in for requests.get() against matelight.cbrp3.c-base.org."""
        response = patch("cbeamd.views.api.requests.get").start()
        self.addCleanup(patch.stopall)
        response.return_value.json.return_value = self.videos if payload is None else payload
        response.return_value.content = content
        return response

    def test_list_returns_the_available_videos(self):
        get = self.mock_get()
        response = self.client.get("/api/v1/matelight/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.videos)
        get.assert_called_once_with(url="http://matelight.cbrp3.c-base.org/api/getvideos")

    def test_retrieve_finds_a_video_by_title(self):
        self.mock_get()
        response = self.client.get("/api/v1/matelight/nyan/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "nyan")

    def test_retrieve_unknown_title_is_404(self):
        self.mock_get()
        response = self.client.get("/api/v1/matelight/missing/")
        self.assertEqual(response.status_code, 404)

    def test_play_posts_the_title_to_the_display(self):
        get = self.mock_get(payload={"playing": "nyan"})
        response = self.client.get("/api/v1/matelight/nyan/play/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"playing": "nyan"})
        get.assert_called_once_with(url="http://matelight.cbrp3.c-base.org/api/play/nyan")

    def test_image_returns_the_thumbnail_as_jpeg(self):
        get = self.mock_get(content=b"\xff\xd8jpegbytes")
        response = self.client.get("/api/v1/matelight/nyan/image/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response.content, b"\xff\xd8jpegbytes")
        self.assertEqual(
            get.call_args.kwargs["url"],
            "http://matelight.cbrp3.c-base.org/assets/thumbs/nyan.jpg",
        )

    def test_image_for_an_unknown_title_is_404(self):
        self.mock_get()
        self.assertEqual(self.client.get("/api/v1/matelight/missing/image/").status_code, 404)

    def test_stop(self):
        get = self.mock_get(payload={"stopped": True})
        response = self.client.get("/api/v1/matelight/stop/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"stopped": True})
        get.assert_called_once_with(url="http://matelight.cbrp3.c-base.org/api/stop")

    def test_status(self):
        get = self.mock_get(payload={"playing": None})
        response = self.client.get("/api/v1/matelight/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"playing": None})
        get.assert_called_once_with(url="http://matelight.cbrp3.c-base.org/api/getstatus")
