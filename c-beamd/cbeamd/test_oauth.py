"""
tests for bearer-token authentication against the c-base identity provider.

tokens are signed with an rsa key generated per test run; the jwks lookup is
stubbed so that no idp needs to be reachable.
"""

import json
import time
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

import cbeamd.views  # noqa: F401  (registers the json-rpc methods)
from cbeamd import oauth
from cbeamd.json_rpc_client import _jsonrpc_method_registry, jsonrpc_method
from cbeamd.models import User as CrewUser

ISSUER = 'https://idp.c-base.org/o'
KID = 'test-key'

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


class _StubSigningKey:
    key = _PUBLIC_KEY


class _StubJWKSClient:
    """stands in for PyJWKClient: knows exactly one key id."""
    uri = ISSUER + '/.well-known/jwks.json'

    def get_signing_key_from_jwt(self, token):
        header = jwt.get_unverified_header(token)
        if header.get('kid') != KID:
            raise jwt.PyJWKClientError('unknown kid')
        return _StubSigningKey()


def make_token(**overrides):
    now = int(time.time())
    claims = {
        'iss': ISSUER,
        'sub': '4711',
        'preferred_username': 'crewmember',
        'email': 'crewmember@c-base.org',
        'scope': 'openid c-beam',
        'iat': now,
        'exp': now + 600,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, _PRIVATE_KEY, algorithm='RS256', headers={'kid': KID})


OAUTH_SETTINGS = dict(
    OAUTH_ISSUER=ISSUER,
    OAUTH_JWKS_URL='',
    OAUTH_AUDIENCE='',
    OAUTH_USERNAME_CLAIM='preferred_username',
    OAUTH_INTROSPECTION_URL='',
    OAUTH_CLIENT_ID='',
    OAUTH_CLIENT_SECRET='',
    OAUTH_REQUIRED_SCOPE='',
)


@override_settings(**OAUTH_SETTINGS)
class BearerTokenTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        patcher = mock.patch.object(oauth, 'jwks_client', return_value=_StubJWKSClient())
        patcher.start()
        self.addCleanup(patcher.stop)

    def rpc(self, method, params=None, token=None, **kwargs):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if token else {}
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params or [], 'id': 1}
        return self.client.post('/rpc/', data=json.dumps(payload),
                                content_type='application/json', **headers, **kwargs)


class TestBearerOnJSONRPC(BearerTokenTestCase):
    def setUp(self):
        super().setUp()
        self._registry_backup = dict(_jsonrpc_method_registry)
        self.addCleanup(lambda: (_jsonrpc_method_registry.clear(),
                                 _jsonrpc_method_registry.update(self._registry_backup)))

        @jsonrpc_method('whoami', authenticated=True)
        def whoami(request):
            return request.user.username

    def test_valid_token_authenticates(self):
        response = self.rpc('whoami', token=make_token())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], 'crewmember')

    def test_first_token_creates_django_and_crew_user(self):
        self.assertFalse(get_user_model().objects.filter(username='crewmember').exists())
        self.rpc('whoami', token=make_token())
        auth_user = get_user_model().objects.get(username='crewmember')
        self.assertFalse(auth_user.has_usable_password())
        self.assertEqual(auth_user.email, 'crewmember@c-base.org')
        self.assertTrue(CrewUser.objects.filter(username='crewmember').exists())

    def test_expired_token_is_refused(self):
        response = self.rpc('whoami', token=make_token(exp=int(time.time()) - 600))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], -32000)
        self.assertIn('expired', response.json()['error']['data'])

    def test_issuer_matches_with_or_without_trailing_slash(self):
        with override_settings(OAUTH_ISSUER=ISSUER + '/'):
            self.assertEqual(self.rpc('whoami', token=make_token()).status_code, 200)
        self.assertEqual(self.rpc('whoami', token=make_token(iss=ISSUER + '/')).status_code, 200)

    def test_wrong_issuer_is_refused(self):
        response = self.rpc('whoami', token=make_token(iss='https://evil.example/o'))
        self.assertEqual(response.status_code, 401)

    def test_unknown_signing_key_is_refused(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = jwt.encode({'iss': ISSUER, 'sub': 'x', 'exp': int(time.time()) + 60},
                           other_key, algorithm='RS256', headers={'kid': KID})
        response = self.rpc('whoami', token=token)
        self.assertEqual(response.status_code, 401)

    def test_garbage_bearer_is_refused_not_ignored(self):
        response = self.rpc('whoami', token='not-a-token')
        self.assertEqual(response.status_code, 401)
        self.assertIn('introspection is not configured', response.json()['error']['data'])

    @override_settings(OAUTH_REQUIRED_SCOPE='c-beam')
    def test_required_scope_is_enforced(self):
        self.assertEqual(self.rpc('whoami', token=make_token(scope='openid')).status_code, 401)
        self.assertEqual(self.rpc('whoami', token=make_token(scope='openid c-beam')).status_code, 200)

    @override_settings(OAUTH_AUDIENCE='c-beam')
    def test_audience_is_enforced_when_configured(self):
        self.assertEqual(self.rpc('whoami', token=make_token()).status_code, 401)
        self.assertEqual(self.rpc('whoami', token=make_token(aud='c-beam')).status_code, 200)

    @override_settings(OAUTH_USERNAME_CLAIM='uid')
    def test_username_claim_is_configurable_with_sub_fallback(self):
        self.assertEqual(self.rpc('whoami', token=make_token(uid='fromuid')).json()['result'], 'fromuid')
        self.assertEqual(self.rpc('whoami', token=make_token(preferred_username=None)).json()['result'], '4711')

    def test_open_methods_do_not_need_a_token(self):
        @jsonrpc_method('open')
        def open_method(request):
            return 'ok'
        self.assertEqual(self.rpc('open').json()['result'], 'ok')

    @override_settings(OAUTH_ISSUER='')
    def test_disabled_when_no_issuer_configured(self):
        response = self.rpc('whoami', token=make_token())
        self.assertEqual(response.status_code, 401)


class TestIntrospectionFallback(BearerTokenTestCase):
    def setUp(self):
        super().setUp()
        self._registry_backup = dict(_jsonrpc_method_registry)
        self.addCleanup(lambda: (_jsonrpc_method_registry.clear(),
                                 _jsonrpc_method_registry.update(self._registry_backup)))

        @jsonrpc_method('whoami', authenticated=True)
        def whoami(request):
            return request.user.username

    def _introspection(self, body):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = body
        return mock.patch.object(oauth.requests, 'post', return_value=response)

    @override_settings(OAUTH_INTROSPECTION_URL=ISSUER + '/introspect/',
                       OAUTH_CLIENT_ID='c-beam', OAUTH_CLIENT_SECRET='s3cret')
    def test_opaque_token_is_introspected(self):
        with self._introspection({'active': True, 'username': 'opaque-user', 'scope': 'c-beam'}) as post:
            response = self.rpc('whoami', token='opaque-token-value')
        self.assertEqual(response.json()['result'], 'opaque-user')
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs['data'], {'token': 'opaque-token-value'})
        self.assertEqual(post.call_args.kwargs['auth'], ('c-beam', 's3cret'))

    @override_settings(OAUTH_INTROSPECTION_URL=ISSUER + '/introspect/')
    def test_inactive_token_is_refused(self):
        with self._introspection({'active': False}):
            response = self.rpc('whoami', token='revoked')
        self.assertEqual(response.status_code, 401)

    @override_settings(OAUTH_INTROSPECTION_URL=ISSUER + '/introspect/')
    def test_jwt_with_unknown_key_falls_back_to_introspection(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = jwt.encode({'iss': ISSUER, 'sub': 'x', 'exp': int(time.time()) + 60},
                           other_key, algorithm='RS256', headers={'kid': 'rotated'})
        with self._introspection({'active': True, 'username': 'rotated-user'}):
            response = self.rpc('whoami', token=token)
        self.assertEqual(response.json()['result'], 'rotated-user')

    def test_opaque_token_without_introspection_is_refused(self):
        response = self.rpc('whoami', token='opaque')
        self.assertEqual(response.status_code, 401)


class TestBearerOnREST(BearerTokenTestCase):
    def test_token_grants_access_to_the_rest_api(self):
        response = self.client.get('/api/v1/users/', HTTP_AUTHORIZATION=f'Bearer {make_token()}')
        self.assertEqual(response.status_code, 200)

    def test_without_token_answers_401_with_bearer_challenge(self):
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 401)
        self.assertIn('Bearer', response['WWW-Authenticate'])

    def test_bad_token_is_401_with_reason(self):
        response = self.client.get('/api/v1/users/',
                                   HTTP_AUTHORIZATION=f'Bearer {make_token(exp=int(time.time()) - 600)}')
        self.assertEqual(response.status_code, 401)
        self.assertIn('expired', response.json()['detail'])

    def test_session_login_still_works(self):
        auth_user = get_user_model().objects.create_user('browser', password='pw')
        self.client.force_login(auth_user)
        self.assertEqual(self.client.get('/api/v1/users/').status_code, 200)


class TestHelpers(TestCase):
    def test_bearer_token_parsing(self):
        from django.test import RequestFactory
        rf = RequestFactory()
        self.assertIsNone(oauth.bearer_token(rf.get('/')))
        self.assertIsNone(oauth.bearer_token(rf.get('/', HTTP_AUTHORIZATION='Basic abc')))
        self.assertIsNone(oauth.bearer_token(rf.get('/', HTTP_AUTHORIZATION='Bearer ')))
        self.assertEqual(oauth.bearer_token(rf.get('/', HTTP_AUTHORIZATION='bearer  tok ')), 'tok')

    @override_settings(OAUTH_ISSUER='https://idp.example/o/', OAUTH_JWKS_URL='')
    def test_default_jwks_url_follows_django_oauth_toolkit_layout(self):
        self.assertEqual(oauth.jwks_url(), 'https://idp.example/o/.well-known/jwks.json')
