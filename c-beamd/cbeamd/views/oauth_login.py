"""
browser login through the c-base identity provider.

authorization code + pkce, with c-beam as a confidential client. the callback
redeems the code for an access token and then walks the same path a bearer
token takes on /rpc/ and /api/ — cbeamd.oauth.claims_for() and
user_from_claims() — before opening a django session. the password form at
/login/ remains the login page; it carries a button for this flow, so local
accounts and crew accounts both start there.
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

from django.contrib.auth import login as django_login
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .. import oauth
from .helpers import logger

SESSION_KEY = 'oauth_login'


def _redirect_uri(request):
    return oauth._setting('OAUTH_REDIRECT_URI') or request.build_absolute_uri(reverse('oauth_callback'))


def _safe_next(request, candidate):
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()},
                                                     require_https=request.is_secure()):
        return candidate
    return reverse('index')


def oauth_login(request):
    """send the browser to the idp; state and pkce verifier stay in the session."""
    if not oauth.enabled():
        return redirect(f"{reverse('login')}?{urlencode({'next': request.GET.get('next', '')})}")

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    request.session[SESSION_KEY] = {
        'state': state,
        'verifier': verifier,
        'next': _safe_next(request, request.GET.get('next')),
    }

    redirect_uri = _redirect_uri(request)
    logger.info("oauth login: sending browser to %s with redirect_uri=%s", oauth.authorization_url(), redirect_uri)
    params = {
        'response_type': 'code',
        'client_id': oauth._setting('OAUTH_CLIENT_ID'),
        'redirect_uri': redirect_uri,
        'state': state,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
    }
    scope = oauth._setting('OAUTH_LOGIN_SCOPE')
    if scope:
        params['scope'] = scope
    return HttpResponseRedirect(f"{oauth.authorization_url()}?{urlencode(params)}")


def oauth_callback(request):
    """redeem the code, resolve the crew member, open the session."""
    pending = request.session.pop(SESSION_KEY, None)
    if not pending or not secrets.compare_digest(pending['state'], request.GET.get('state', '')):
        logger.warning("oauth callback with missing or mismatched state")
        return HttpResponseBadRequest("oauth login: state mismatch — bitte nochmal anmelden")

    if 'error' in request.GET:
        logger.warning("idp refused the login: %s", request.GET.get('error_description') or request.GET['error'])
        return HttpResponseBadRequest(f"oauth login abgelehnt: {request.GET['error']}")

    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest("oauth login: kein code")

    try:
        tokens = oauth.exchange_code(code, _redirect_uri(request), pending['verifier'])
        claims = oauth.claims_for(tokens['access_token'])
        user = oauth.user_from_claims(claims)
    except oauth.InvalidToken as e:
        logger.warning("oauth login failed: %s", e)
        return HttpResponseBadRequest(f"oauth login fehlgeschlagen: {e}")

    django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    logger.info("oauth login: %s", user.username)
    return HttpResponseRedirect(pending['next'])
