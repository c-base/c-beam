"""
JSON-RPC endpoint handler.

Replaces jsonrpc.jsonrpc_site.dispatch from the removed django-json-rpc package.
Dispatches JSON-RPC method calls to handlers registered via @jsonrpc_method.
"""

import inspect
import json

from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..json_rpc_client import get_jsonrpc_method, method_requires_authentication
from ..oauth import InvalidToken, authenticate_bearer
from .helpers import logger

# the two leading positional params an authenticated method accepts instead of
# a session — the contract django-json-rpc established for authenticated=True.
AUTH_ARGUMENTS = ('username', 'password')


def _error(code, message, request_id=None, data=None, version='2.0'):
    body = {'code': code, 'message': message}
    if data is not None:
        body['data'] = data
    return {'jsonrpc': version, 'error': body, 'id': request_id}


def _authenticate(request, params):
    """
    resolve the user for a method declared with authenticated=True.

    an `Authorization: Bearer` token from the c-base idp is checked first
    (cbeamd.oauth) and, when present, decides on its own — a bad token is
    refused even if a session exists. next a logged-in django session wins.
    otherwise the credentials are taken from the params — the first two
    positional ones, or the `username`/`password` keys — and stripped before
    the call, as django-json-rpc did. returns the params to call with, or
    None if the caller could not be authenticated; raises InvalidToken for a
    bearer token that does not hold up.
    """
    bearer_user = authenticate_bearer(request)
    if bearer_user is not None:
        request.user = bearer_user
        return params

    rpc_user = getattr(request, 'user', None)
    if rpc_user is not None and rpc_user.is_authenticated:
        return params

    if isinstance(params, dict):
        if not all(k in params for k in AUTH_ARGUMENTS):
            return None
        creds = {k: params[k] for k in AUTH_ARGUMENTS}
        remaining = {k: v for k, v in params.items() if k not in AUTH_ARGUMENTS}
    else:
        if len(params) < len(AUTH_ARGUMENTS):
            return None
        creds = dict(zip(AUTH_ARGUMENTS, params))
        remaining = params[len(AUTH_ARGUMENTS):]

    user = authenticate(request, **creds)
    if user is None:
        return None
    request.user = user
    return remaining


def _dispatch_one(request, data):
    """
    handle a single request object. returns the response dict, or None for
    a notification (a request without an id), which gets no reply.
    """
    if not isinstance(data, dict):
        return _error(-32600, 'Invalid Request')

    method = data.get('method')
    params = data.get('params')
    request_id = data.get('id')
    is_notification = 'id' not in data or request_id is None
    version = data.get('jsonrpc', '2.0')

    def reply(response):
        return None if is_notification else response

    if not isinstance(method, str):
        return reply(_error(-32600, 'Invalid Request', request_id, version=version))

    # "params" may be omitted, and a client sending null means the same
    if params is None:
        params = []
    if not isinstance(params, (list, dict)):
        return reply(_error(-32602, 'Invalid params', request_id,
                            'params must be an array or an object', version))

    handler = get_jsonrpc_method(method)
    if handler is None:
        return reply(_error(-32601, 'Method not found', request_id, version=version))

    if method_requires_authentication(handler):
        try:
            params = _authenticate(request, params)
        except InvalidToken as e:
            logger.warning("json-rpc call to %s with invalid bearer token: %s", method, e)
            return reply(_error(-32000, 'Authentication required', request_id, str(e), version))
        if params is None:
            logger.warning("unauthenticated json-rpc call to protected method %s", method)
            # -32000 is in the implementation-defined server error range
            # reserved by the JSON-RPC 2.0 spec.
            return reply(_error(-32000, 'Authentication required', request_id, version=version))

    args, kwargs = (params, {}) if isinstance(params, list) else ([], params)

    # bind before calling, so that a TypeError from a wrong arity or an
    # unknown keyword is reported as invalid params, while a TypeError raised
    # inside the handler still counts as an internal error.
    try:
        inspect.signature(handler).bind(request, *args, **kwargs)
    except TypeError as e:
        return reply(_error(-32602, 'Invalid params', request_id, str(e), version))

    try:
        result = handler(request, *args, **kwargs)
    except Exception as e:
        logger.exception("error calling json-rpc method %s", method)
        return reply(_error(-32603, 'Internal error', request_id, str(e), version))

    # views double as html endpoints and may hand back a response object
    if isinstance(result, JsonResponse):
        result = json.loads(result.content.decode('utf-8'))
    elif isinstance(result, HttpResponse):
        result = result.content.decode('utf-8') if isinstance(result.content, bytes) else result.content
    elif isinstance(result, tuple):
        result = list(result)

    return reply({'jsonrpc': version, 'result': result, 'id': request_id})


@csrf_exempt
@require_http_methods(['POST'])
def jsonrpc_handler(request):
    """
    JSON-RPC 2.0 endpoint. accepts single requests, batches (a json array of
    requests, answered with an array in the same order, notifications left
    out) and notifications (answered with an empty 204).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(_error(-32700, 'Parse error'), status=400)

    if isinstance(data, list):
        if not data:
            return JsonResponse(_error(-32600, 'Invalid Request'), status=400)
        responses = [r for r in (_dispatch_one(request, d) for d in data) if r is not None]
        if not responses:
            return HttpResponse(status=204)
        return JsonResponse(responses, safe=False)

    response = _dispatch_one(request, data)
    if response is None:
        return HttpResponse(status=204)

    error = response.get('error')
    if error is None:
        status = 200
    elif error['code'] == -32000:
        status = 401
    elif error['code'] == -32600:
        status = 400
    else:
        status = 200
    return JsonResponse(response, status=status)
