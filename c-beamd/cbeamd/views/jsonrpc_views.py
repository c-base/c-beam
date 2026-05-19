# -*- coding: utf-8 -*-
"""
JSON-RPC endpoint handler.
"""

import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..json_rpc_client import get_jsonrpc_method


@csrf_exempt
@require_http_methods(['POST'])
def jsonrpc_handler(request):
    """
    JSON-RPC 2.0 endpoint handler.
    Replaces deprecated jsonrpc.jsonrpc_site.dispatch.

    Dispatches JSON-RPC method calls to decorated handlers registered via @jsonrpc_method.
    """
    from .view_helpers import logger

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
            response_result = result.content.decode('utf-8') if isinstance(result.content, bytes) else result.content
        elif isinstance(result, JsonResponse):
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
