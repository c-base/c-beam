"""the eta section on / and /user/online only shows when somebody has an eta."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from cbeamd.models import User as CrewUser


def crew(username, status, eta=''):
    now = timezone.now() - timedelta(hours=1)
    return CrewUser.objects.create(username=username, status=status, eta=eta,
                                   logintime=now, logouttime=now)


class TestEtaSection(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.force_login(get_user_model().objects.create_user('browser', password='pw'))
        crew('onboard', 'online')

    def test_hidden_when_nobody_has_an_eta(self):
        for url in ('/', '/user/online'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, '<h1 align="center">ETA</h1>')
                self.assertNotContains(response, 'momentan ist kein ETA eingetragen')

    def test_shown_when_somebody_has_one(self):
        crew('latecomer', 'eta', eta='20:30')
        for url in ('/', '/user/online'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, '<h1 align="center">ETA</h1>')
                self.assertContains(response, 'latecomer (20:30)')
