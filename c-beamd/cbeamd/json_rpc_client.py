"""
Lightweight JSON-RPC 2.0 implementation to replace deprecated jsonrpc package.
Includes both client and decorator-based server registration.
"""

import json
import logging
import uuid
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, Optional

import requests
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse

logger = logging.getLogger(__name__)

# Global registry for JSON-RPC methods
_jsonrpc_method_registry: Dict[str, Callable] = {}


class JSONRPCError(Exception):
    """Exception for JSON-RPC errors."""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")


class JSONRPCClient:
    """
    Lightweight JSON-RPC 2.0 client.

    Replaces deprecated jsonrpclib.Server() with a modern implementation
    using requests library.

    Usage:
        client = JSONRPCClient('http://example.com:1234/')
        result = client.some_method(arg1, arg2, kwarg1=value1)
    """

    def __init__(self, url: str, timeout: int = 30):
        """
        Initialize JSON-RPC client.

        Args:
            url: The JSON-RPC server URL
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip('/') + '/' if url else ''
        self.timeout = timeout

    def _call(self, method: str, *args, **kwargs) -> Any:
        """
        Make a JSON-RPC 2.0 call.

        Args:
            method: The JSON-RPC method name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result from the JSON-RPC response

        Raises:
            JSONRPCError: If the server returns an error
            requests.RequestException: If the HTTP request fails
        """
        request_id = str(uuid.uuid4())

        # Build params: prioritize kwargs if present, otherwise use args
        if kwargs:
            params = kwargs
        else:
            params = list(args) if args else []

        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': request_id,
        }

        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(
                self.url,
                data=json.dumps(payload),
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error(f"JSON-RPC request failed: {e}")
            raise

        # a json-rpc error body is the more useful failure even when it comes
        # with an http error status — django-json-rpc servers answer a
        # method-not-found with a 404, for example. only fall back to the http
        # status when there is no json-rpc envelope to report.
        try:
            result_data = response.json()
        except ValueError as e:
            if not response.ok:
                response.raise_for_status()
            logger.error(f"Failed to parse JSON-RPC response: {e}\nResponse: {response.text}")
            raise
        if not isinstance(result_data, dict):
            response.raise_for_status()
            raise JSONRPCError(-32603, f"unexpected JSON-RPC response: {result_data!r}")

        # Check for JSON-RPC error
        if 'error' in result_data and result_data['error'] is not None:
            error = result_data['error']
            raise JSONRPCError(
                code=error.get('code', -1),
                message=error.get('message', 'Unknown error'),
                data=error.get('data'),
            )

        return result_data.get('result')

    def __getattr__(self, name: str):
        """
        Allow calling JSON-RPC methods as attributes.

        Example:
            client = JSONRPCClient('http://example.com/rpc/')
            result = client.some_method(arg1, arg2)
        """
        def method_call(*args, **kwargs):
            return self._call(name, *args, **kwargs)
        return method_call


def jsonrpc_method(method_name: str, authenticated: bool = False, **kwargs):
    """
    Decorator to register a function as a JSON-RPC method.

    Replaces the deprecated @jsonrpc_method decorator from the jsonrpc package.

    Usage:
        @jsonrpc_method('login')
        def login(request, username):
            return "logged in"

        @jsonrpc_method('protected', authenticated=True)
        def protected_func(request):
            return "protected"

    Args:
        method_name: The JSON-RPC method name to register
        authenticated: If True, the dispatcher refuses the call unless the
            request carries an authenticated django session.
        **kwargs: Further parameters (e.g. validate) - accepted but not acted on.

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        """Register the function and return it unchanged."""
        # the dispatcher reads this off the registered callable. the registry
        # deliberately keeps storing plain callables so that callers can invoke
        # what get_jsonrpc_method() hands back.
        func.jsonrpc_authenticated = bool(authenticated)
        _jsonrpc_method_registry[method_name] = func
        return func

    return decorator


def get_jsonrpc_method(method_name: str) -> Optional[Callable]:
    """
    Retrieve a registered JSON-RPC method by name.

    Args:
        method_name: The JSON-RPC method name

    Returns:
        The callable method, or None if not registered
    """
    return _jsonrpc_method_registry.get(method_name)


def method_requires_authentication(method: Callable) -> bool:
    """Whether a registered method was declared with authenticated=True."""
    return bool(getattr(method, 'jsonrpc_authenticated', False))


def get_jsonrpc_methods() -> Dict[str, Callable]:
    """
    Get all registered JSON-RPC methods.

    Returns:
        Dictionary of method name -> callable
    """
    return _jsonrpc_method_registry.copy()


def ajax(func):
    """
    Decorator that wraps a view's return value in the response envelope the
    removed django_ajax package produced:

        {"status": 200, "statusText": "OK", "content": <return value>}

    the javascript consuming these views (assets/js/mpdwidget.jsx) reads the
    payload from `content`, so the envelope is part of the contract. an
    HttpResponse is passed through with its body as the content, and an
    exception becomes a 500 envelope instead of an html error page — both as
    django_ajax did. what it does not reproduce is the X-Requested-With gate.
    """
    @wraps(func)
    def _wrapper(request, *args, **kwargs):
        try:
            result = func(request, *args, **kwargs)
        except Exception as e:
            logger.exception("error in ajax view %s", func.__name__)
            status, content = 500, str(e)
        else:
            if isinstance(result, HttpResponse):
                status = result.status_code
                content = result.content.decode('utf-8') if isinstance(result.content, bytes) else result.content
            else:
                status, content = 200, result
        try:
            status_text = HTTPStatus(status).phrase.upper()
        except ValueError:
            status_text = 'UNKNOWN STATUS CODE'
        envelope = {'status': status, 'statusText': status_text, 'content': content}
        return HttpResponse(json.dumps(envelope, cls=DjangoJSONEncoder), content_type="application/json", status=status)
    return _wrapper
