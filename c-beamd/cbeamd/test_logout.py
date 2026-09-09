"""django 5 dropped GET on LogoutView; the navbar has to post."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class TestLogout(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user('crew', password='pw')
        self.client.force_login(self.user)

    def test_navbar_offers_logout_as_a_post_form(self):
        response = self.client.get('/login/')  # any page rendering base.django
        self.assertContains(response, 'action="/logout/" method="post"')
        self.assertContains(response, 'c-logout')

    def test_get_logout_is_refused(self):
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_logout_ends_the_session(self):
        response = self.client.post('/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
