"""
oauth2 bearer-token authentication for the json-rpc and rest surfaces.

c-beam is a resource server. the c-base identity provider (django-oauth-toolkit)
issues the tokens; c-beam only validates them and maps the subject to a crew
member. it never sees a password. two validation paths, both configured from
the environment (see OAUTH_* in settings.py):

- jwt (primary): the signature is checked against the idp's jwks, issuer,
  expiry and — when configured — audience and scope are enforced. the mqtt
  broker validates the same tokens against the same keys, so a token that
  works here works there.
- introspection (optional fallback): for opaque tokens, or a jwt whose key is
  unknown, POST the token to the idp's introspection endpoint with c-beam's
  own client credentials. off unless OAUTH_INTROSPECTION_URL is set.

a blank OAUTH_ISSUER disables bearer authentication entirely; the header is
then ignored and the session / credential paths behave as before.
"""

import logging

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

# algorithms the idp may sign with. "none" and the hmac family are excluded on
# purpose — a shared-secret token could be minted by anyone holding the jwks.
ALLOWED_ALGORITHMS = ('RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512')

# tolerated clock skew between the idp and this host, in seconds
LEEWAY = 30

_jwks_client = None


class InvalidToken(Exception):
    """the bearer token was present but could not be accepted."""


def _setting(name, default=''):
    return getattr(settings, name, default) or default


def enabled():
    return bool(_setting('OAUTH_ISSUER'))


def jwks_url():
    return _setting('OAUTH_JWKS_URL') or _setting('OAUTH_ISSUER').rstrip('/') + '/.well-known/jwks.json'


def accepted_issuers():
    """
    the configured issuer with and without a trailing slash. the `iss` claim
    is compared verbatim, and django-oauth-toolkit publishes it without the
    slash while the url people copy from the browser usually has one.
    """
    issuer = _setting('OAUTH_ISSUER').rstrip('/')
    return [issuer, issuer + '/']


def authorization_url():
    return _setting('OAUTH_AUTHORIZATION_URL') or _setting('OAUTH_ISSUER').rstrip('/') + '/authorize/'


def token_url():
    return _setting('OAUTH_TOKEN_URL') or _setting('OAUTH_ISSUER').rstrip('/') + '/token/'


def exchange_code(code, redirect_uri, code_verifier):
    """
    redeem an authorization code at the idp's token endpoint (browser login,
    see views/oauth_login.py). c-beam authenticates as a confidential client
    with its own credentials; pkce is sent on top. returns the token response.
    """
    try:
        response = requests.post(
            token_url(),
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier,
            },
            auth=(_setting('OAUTH_CLIENT_ID'), _setting('OAUTH_CLIENT_SECRET')),
            timeout=10,
        )
        body = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("code exchange at %s failed: %s", token_url(), e)
        raise InvalidToken(f"code exchange failed: {e}")
    if response.status_code != 200 or 'access_token' not in body:
        raise InvalidToken(f"code exchange refused: {body.get('error', response.status_code)}")
    return body


def jwks_client():
    """the shared PyJWKClient; keys are cached, a miss refetches once."""
    global _jwks_client
    if _jwks_client is None or _jwks_client.uri != jwks_url():
        _jwks_client = jwt.PyJWKClient(jwks_url(), cache_keys=True, timeout=5)
    return _jwks_client


def bearer_token(request):
    """the token from an `Authorization: Bearer …` header, or None."""
    header = request.META.get('HTTP_AUTHORIZATION', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None
    return token.strip()


def validate_jwt(token):
    """decode and verify a jwt; returns its claims or raises InvalidToken."""
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
    except jwt.PyJWKClientError as e:
        raise InvalidToken(f"no signing key for token: {e}")
    except jwt.DecodeError as e:
        raise InvalidToken(f"malformed token: {e}")

    audience = _setting('OAUTH_AUDIENCE')
    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(ALLOWED_ALGORITHMS),
            issuer=accepted_issuers(),
            audience=audience or None,
            leeway=LEEWAY,
            options={'verify_aud': bool(audience), 'require': ['exp', 'iss']},
        )
    except jwt.PyJWTError as e:
        raise InvalidToken(str(e))
    return claims


def introspect(token):
    """
    ask the idp about a token (rfc 7662). returns the introspection response
    as claims when the token is active, raises InvalidToken otherwise.
    """
    url = _setting('OAUTH_INTROSPECTION_URL')
    if not url:
        raise InvalidToken("token is not a valid jwt and introspection is not configured")
    try:
        response = requests.post(
            url,
            data={'token': token},
            auth=(_setting('OAUTH_CLIENT_ID'), _setting('OAUTH_CLIENT_SECRET')),
            timeout=5,
        )
        response.raise_for_status()
        claims = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("token introspection at %s failed: %s", url, e)
        raise InvalidToken(f"introspection failed: {e}")
    if not claims.get('active'):
        raise InvalidToken("token is not active")
    return claims


def claims_for(token):
    """claims for a bearer token, via jwt validation with introspection as fallback."""
    looks_like_jwt = token.count('.') == 2
    if looks_like_jwt:
        try:
            claims = validate_jwt(token)
        except InvalidToken:
            if not _setting('OAUTH_INTROSPECTION_URL'):
                raise
            claims = introspect(token)
    else:
        claims = introspect(token)

    required_scope = _setting('OAUTH_REQUIRED_SCOPE')
    if required_scope:
        granted = claims.get('scope', '')
        granted = granted.split() if isinstance(granted, str) else list(granted)
        if required_scope not in granted:
            raise InvalidToken(f"token lacks the '{required_scope}' scope")
    return claims


def username_from_claims(claims):
    for claim in (_setting('OAUTH_USERNAME_CLAIM', 'preferred_username'), 'username', 'sub'):
        value = claims.get(claim)
        if value:
            return str(value)
    raise InvalidToken("token carries no usable subject")


def user_from_claims(claims):
    """
    the django auth user for a token's subject, created on first sight. the
    crew member row (cbeamd.models.User) is ensured alongside, because that is
    what the view layer means by "user"; both are keyed by the idp username.
    """
    username = username_from_claims(claims)
    auth_user, created = get_user_model().objects.get_or_create(
        username=username,
        defaults={'email': claims.get('email', '') or ''},
    )
    if created:
        auth_user.set_unusable_password()
        auth_user.save(update_fields=['password'])
        logger.info("created django user %s from oauth token", username)

    # imported here: views.helpers pulls in the whole view layer
    from .views.helpers import getuser
    getuser(username)
    return auth_user


def authenticate_bearer(request):
    """
    resolve the user behind a request's bearer token. returns None when there
    is no bearer header or bearer auth is disabled; raises InvalidToken when
    there is one and it does not hold up. sets request.oauth_claims on success.
    """
    if not enabled():
        return None
    token = bearer_token(request)
    if token is None:
        return None
    claims = claims_for(token)
    user = user_from_claims(claims)
    request.oauth_claims = claims
    return user


class OAuth2BearerAuthentication(authentication.BaseAuthentication):
    """drf authentication class; the rest api accepts the same tokens as /rpc/."""

    def authenticate(self, request):
        try:
            user = authenticate_bearer(request._request)
        except InvalidToken as e:
            raise exceptions.AuthenticationFailed(str(e))
        if user is None:
            return None
        return (user, getattr(request._request, 'oauth_claims', None))

    def authenticate_header(self, request):
        # makes drf answer 401 with a challenge rather than 403
        return 'Bearer realm="c-beam"'
