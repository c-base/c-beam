"""
JSON-RPC endpoint handler.

Split out of the original views.py; function bodies are unchanged.
"""

import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ..json_rpc_client import get_jsonrpc_method, method_requires_authentication


from .helpers import logger


@csrf_exempt
@require_http_methods(['POST'])
def jsonrpc_handler(request):
    """
    JSON-RPC 2.0 endpoint handler.
    Replaces deprecated jsonrpc.jsonrpc_site.dispatch.

    Dispatches JSON-RPC method calls to decorated handlers registered via @jsonrpc_method.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'jsonrpc': '2.0',
            'error': {'code': -32700, 'message': 'Parse error'},
            'id': None,
        }, status=400)

    method = data.get('method')
    params = data.get('params', [])
    request_id = data.get('id')
    jsonrpc_version = data.get('jsonrpc', '2.0')

    # Look up method in the registry
    handler = get_jsonrpc_method(method)

    # Check if method exists
    if handler is None:
        return JsonResponse({
            'jsonrpc': jsonrpc_version,
            'error': {'code': -32601, 'message': 'Method not found'},
            'id': request_id,
        })

    # methods declared with @jsonrpc_method(..., authenticated=True) require a
    # logged-in django session. -32000 is in the implementation-defined server
    # error range reserved by the JSON-RPC 2.0 spec.
    rpc_user = getattr(request, 'user', None)
    if method_requires_authentication(handler) and not (rpc_user and rpc_user.is_authenticated):
        logger.warning("unauthenticated json-rpc call to protected method %s", method)
        return JsonResponse({
            'jsonrpc': jsonrpc_version,
            'error': {'code': -32000, 'message': 'Authentication required'},
            'id': request_id,
        }, status=401)

    try:
        # Call the method with params
        if isinstance(params, list):
            result = handler(request, *params)
        else:
            result = handler(request, **params)

        # Handle different return types
        if isinstance(result, str):
            response_result = result
        elif isinstance(result, HttpResponse):
            # If view returns HttpResponse directly, extract content
            response_result = result.content.decode('utf-8') if isinstance(result.content, bytes) else result.content
        elif isinstance(result, JsonResponse):
            # If it's a JsonResponse, extract the data
            response_result = json.loads(result.content.decode('utf-8'))
        else:
            response_result = result

        return JsonResponse({
            'jsonrpc': jsonrpc_version,
            'result': response_result,
            'id': request_id,
        })
    except Exception as e:
        logger.exception(f"Error calling JSON-RPC method {method}")
        return JsonResponse({
            'jsonrpc': jsonrpc_version,
            'error': {
                'code': -32603,
                'message': 'Internal error',
                'data': str(e),
            },
            'id': request_id,
        })
