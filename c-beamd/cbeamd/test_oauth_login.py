"""
tests for the browser login through the c-base identity provider.

the idp is never contacted: the code exchange and the token introspection are
mocked at the http boundary, the flow in between is real.
"""

from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cbeamd import oauth
from cbeamd.models import User as CrewUser
from cbeamd.views.oauth_login import SESSION_KEY

ISSUER = 'https://idp.c-base.org/oauth'

SETTINGS = dict(
    OAUTH_ISSUER=ISSUER, OAUTH_JWKS_URL='', OAUTH_AUDIENCE='', OAUTH_REQUIRED_SCOPE='',
    OAUTH_USERNAME_CLAIM='preferred_username',
    OAUTH_INTROSPECTION_URL=ISSUER + '/introspect/',
    OAUTH_CLIENT_ID='c-beam', OAUTH_CLIENT_SECRET='s3cret',
    OAUTH_AUTHORIZATION_URL='', OAUTH_TOKEN_URL='', OAUTH_LOGIN_SCOPE='openid', OAUTH_REDIRECT_URI='',
)


def _response(status, body):
    r = mock.Mock()
    r.status_code = status
    r.json.return_value = body
    r.raise_for_status.return_value = None
    return r


@override_settings(**SETTINGS)
class TestOAuthLoginRedirect(TestCase):
    def setUp(self):
        self.client = Client()

    def test_redirects_to_the_idp_with_pkce_and_state(self):
        response = self.client.get(reverse('oauth_login') + '?next=/preferences/')
        self.assertEqual(response.status_code, 302)
        url = urlparse(response['Location'])
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", ISSUER + '/authorize/')
        q = parse_qs(url.query)
        self.assertEqual(q['response_type'], ['code'])
        self.assertEqual(q['client_id'], ['c-beam'])
        self.assertEqual(q['scope'], ['openid'])
        self.assertEqual(q['code_challenge_method'], ['S256'])
        self.assertEqual(q['redirect_uri'], ['http://testserver/oauth/callback/'])
        pending = self.client.session[SESSION_KEY]
        self.assertEqual(q['state'], [pending['state']])
        self.assertEqual(pending['next'], '/preferences/')
        self.assertTrue(len(pending['verifier']) >= 43)

    def test_unsafe_next_falls_back_to_index(self):
        self.client.get(reverse('oauth_login') + '?next=https://evil.example/')
        self.assertEqual(self.client.session[SESSION_KEY]['next'], reverse('index'))

    @override_settings(OAUTH_REDIRECT_URI='https://c-beam.example/oauth/callback/')
    def test_redirect_uri_can_be_pinned(self):
        response = self.client.get(reverse('oauth_login'))
        self.assertEqual(parse_qs(urlparse(response['Location']).query)['redirect_uri'],
                         ['https://c-beam.example/oauth/callback/'])

    @override_settings(OAUTH_ISSUER='')
    def test_without_idp_falls_back_to_the_password_form(self):
        response = self.client.get(reverse('oauth_login') + '?next=/x/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(reverse('login')))

    def test_login_required_keeps_sending_browsers_to_the_password_form(self):
        response = self.client.get('/c_buttons/login')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(reverse('login')), response['Location'])

    def test_password_form_offers_the_idp_button(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, reverse('oauth_login'))
        self.assertContains(response, 'mit c-base-account anmelden')


@override_settings(**SETTINGS)
class TestOAuthCallback(TestCase):
    def setUp(self):
        self.client = Client()
        # start a flow so that state and verifier are in the session
        self.client.get(reverse('oauth_login') + '?next=/preferences/')
        self.pending = self.client.session[SESSION_KEY]

    def _idp(self, token_body=None, token_status=200, introspection=None):
        """mock the two idp calls: code exchange, then introspection of the access token."""
        token_body = token_body if token_body is not None else {'access_token': 'opaque-123', 'token_type': 'Bearer'}
        introspection = introspection if introspection is not None else {'active': True, 'username': 'crewmember'}

        def post(url, **kwargs):
            if url == ISSUER + '/token/':
                return _response(token_status, token_body)
            if url == ISSUER + '/introspect/':
                return _response(200, introspection)
            raise AssertionError(f"unexpected post to {url}")
        return mock.patch.object(oauth.requests, 'post', side_effect=post)

    def callback(self, **params):
        return self.client.get(reverse('oauth_callback'), params)

    def test_happy_path_opens_a_session_and_redirects_to_next(self):
        with self._idp() as post:
            response = self.callback(code='abc', state=self.pending['state'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/preferences/')
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         get_user_model().objects.get(username='crewmember').pk)
        self.assertTrue(CrewUser.objects.filter(username='crewmember').exists())

        exchange = post.call_args_list[0]
        self.assertEqual(exchange.kwargs['data']['grant_type'], 'authorization_code')
        self.assertEqual(exchange.kwargs['data']['code'], 'abc')
        self.assertEqual(exchange.kwargs['data']['code_verifier'], self.pending['verifier'])
        self.assertEqual(exchange.kwargs['data']['redirect_uri'], 'http://testserver/oauth/callback/')
        self.assertEqual(exchange.kwargs['auth'], ('c-beam', 's3cret'))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_state_mismatch_is_refused(self):
        with self._idp():
            response = self.callback(code='abc', state='forged')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_state_can_only_be_used_once(self):
        with self._idp():
            self.callback(code='abc', state=self.pending['state'])
            self.client.logout()
            response = self.callback(code='abc', state=self.pending['state'])
        self.assertEqual(response.status_code, 400)

    def test_idp_error_is_shown_not_exchanged(self):
        with self._idp() as post:
            response = self.callback(error='access_denied', state=self.pending['state'])
        self.assertEqual(response.status_code, 400)
        post.assert_not_called()

    def test_refused_code_exchange_is_a_400(self):
        with self._idp(token_body={'error': 'invalid_grant'}, token_status=400):
            response = self.callback(code='stale', state=self.pending['state'])
        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid_grant', response.content.decode())

    def test_inactive_token_after_exchange_is_refused(self):
        with self._idp(introspection={'active': False}):
            response = self.callback(code='abc', state=self.pending['state'])
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authorization_and_token_urls_follow_the_issuer(self):
        self.assertEqual(oauth.authorization_url(), ISSUER + '/authorize/')
        self.assertEqual(oauth.token_url(), ISSUER + '/token/')
        with override_settings(OAUTH_TOKEN_URL='https://elsewhere/t/'):
            self.assertEqual(oauth.token_url(), 'https://elsewhere/t/')
