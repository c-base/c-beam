# -*- coding: utf-8 -*-
"""
Lightweight JSON-RPC 2.0 implementation to replace deprecated jsonrpc package.
Includes both client and decorator-based server registration.
"""

import json
import logging
import uuid
from functools import wraps
from typing import Any, Callable, Dict, Optional

import requests

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
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"JSON-RPC request failed: {e}")
            raise
        
        try:
            result_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON-RPC response: {e}\nResponse: {response.text}")
            raise
        
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


def jsonrpc_method(method_name: str):
    """
    Decorator to register a function as a JSON-RPC method.
    
    Replaces the deprecated @jsonrpc_method decorator from the jsonrpc package.
    
    Usage:
        @jsonrpc_method('login')
        def login(request, username):
            return "logged in"
    
    Args:
        method_name: The JSON-RPC method name to register
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        """Register the function and return it unchanged."""
        _jsonrpc_method_registry[method_name] = func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
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


def get_jsonrpc_methods() -> Dict[str, Callable]:
    """
    Get all registered JSON-RPC methods.
    
    Returns:
        Dictionary of method name -> callable
    """
    return _jsonrpc_method_registry.copy()
