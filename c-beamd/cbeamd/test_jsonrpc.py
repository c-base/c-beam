# -*- coding: utf-8 -*-
"""
Tests for JSON-RPC method registration and endpoint handling.
"""

import json
import pytest
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta

from cbeamd.models import User
from cbeamd.json_rpc_client import (
    jsonrpc_method,
    get_jsonrpc_method,
    get_jsonrpc_methods,
    JSONRPCError,
    JSONRPCClient,
    _jsonrpc_method_registry,
)


class TestJSONRPCDecorator(TestCase):
    """Tests for the @jsonrpc_method decorator and registry system."""

    def setUp(self):
        """Clear registry before each test."""
        _jsonrpc_method_registry.clear()

    def test_decorator_registers_method(self):
        """Test that @jsonrpc_method decorator registers a function."""
        @jsonrpc_method('test_method')
        def test_func(request):
            return "test result"

        # Method should be in registry
        registered = get_jsonrpc_method('test_method')
        self.assertIsNotNone(registered)
        self.assertEqual(registered.__name__, 'test_func')

    def test_decorator_preserves_function_metadata(self):
        """Test that @wraps preserves original function metadata."""
        @jsonrpc_method('documented')
        def documented_func(request):
            """This is a documented function."""
            return "result"

        registered = get_jsonrpc_method('documented')
        self.assertEqual(registered.__name__, 'documented_func')
        self.assertIn('documented function', registered.__doc__)

    def test_multiple_methods_registered(self):
        """Test that multiple methods can be registered."""
        @jsonrpc_method('method1')
        def func1(request):
            return "result1"

        @jsonrpc_method('method2')
        def func2(request):
            return "result2"

        @jsonrpc_method('method3')
        def func3(request):
            return "result3"

        all_methods = get_jsonrpc_methods()
        self.assertEqual(len(all_methods), 3)
        self.assertIn('method1', all_methods)
        self.assertIn('method2', all_methods)
        self.assertIn('method3', all_methods)

    def test_decorator_with_extra_parameters(self):
        """Test decorator accepts extra parameters (authenticated, validate)."""
        @jsonrpc_method('protected', authenticated=True)
        def protected_func(request):
            return "protected"

        # Should still be registered despite extra parameters
        registered = get_jsonrpc_method('protected')
        self.assertIsNotNone(registered)

    def test_registered_method_is_callable(self):
        """Test that registered method can be called."""
        @jsonrpc_method('callable_method')
        def test_func(request, arg1, arg2):
            return f"{arg1}-{arg2}"

        registered = get_jsonrpc_method('callable_method')
        result = registered(None, 'hello', 'world')
        self.assertEqual(result, 'hello-world')

    def test_get_jsonrpc_methods_returns_copy(self):
        """Test that get_jsonrpc_methods returns a copy, not reference."""
        @jsonrpc_method('original')
        def func(request):
            return "original"

        methods1 = get_jsonrpc_methods()
        methods2 = get_jsonrpc_methods()

        # Should be different objects
        self.assertIsNot(methods1, methods2)
        # But contain same data
        self.assertEqual(methods1.keys(), methods2.keys())

    def test_method_not_found_returns_none(self):
        """Test that get_jsonrpc_method returns None for unregistered method."""
        result = get_jsonrpc_method('nonexistent')
        self.assertIsNone(result)


class TestJSONRPCClient(TestCase):
    """Tests for the JSONRPCClient class."""

    def test_client_initialization(self):
        """Test that JSONRPCClient initializes with correct URL."""
        client = JSONRPCClient('http://example.com/rpc')
        self.assertEqual(client.url, 'http://example.com/rpc/')

    def test_client_url_normalization(self):
        """Test that client normalizes URLs with trailing slashes."""
        client1 = JSONRPCClient('http://example.com/rpc')
        client2 = JSONRPCClient('http://example.com/rpc/')

        self.assertEqual(client1.url, client2.url)

    def test_client_timeout_config(self):
        """Test that client stores timeout value."""
        client = JSONRPCClient('http://example.com/rpc', timeout=60)
        self.assertEqual(client.timeout, 60)


class TestJSONRPCError(TestCase):
    """Tests for JSONRPCError exception."""

    def test_error_creation(self):
        """Test that JSONRPCError can be created with code and message."""
        error = JSONRPCError(code=-32601, message='Method not found')
        self.assertEqual(error.code, -32601)
        self.assertEqual(error.message, 'Method not found')

    def test_error_with_data(self):
        """Test that JSONRPCError can include additional data."""
        error = JSONRPCError(
            code=-32603,
            message='Internal error',
            data='Division by zero'
        )
        self.assertEqual(error.data, 'Division by zero')

    def test_error_string_representation(self):
        """Test error message format."""
        error = JSONRPCError(code=-32601, message='Method not found')
        error_str = str(error)
        self.assertIn('-32601', error_str)
        self.assertIn('Method not found', error_str)


class TestJSONRPCHandler(TestCase):
    """Tests for the JSON-RPC HTTP endpoint handler."""

    def setUp(self):
        """Set up test client and clear registry."""
        self.client = Client()
        _jsonrpc_method_registry.clear()

        # Register test methods
        @jsonrpc_method('echo')
        def echo(request, message):
            return message

        @jsonrpc_method('add')
        def add(request, a, b):
            return a + b

        @jsonrpc_method('get_user')
        def get_user(request, username):
            user = User.objects.filter(username=username).first()
            if user:
                return user.username
            return None

        @jsonrpc_method('error_method')
        def error_method(request):
            raise ValueError("Test error")

    def test_valid_json_rpc_request(self):
        """Test handling of valid JSON-RPC request."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'echo',
            'params': ['hello'],
            'id': '1',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['result'], 'hello')
        self.assertEqual(data['id'], '1')

    def test_json_rpc_with_multiple_params(self):
        """Test JSON-RPC request with multiple parameters."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'add',
            'params': [5, 3],
            'id': '2',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertEqual(data['result'], 8)

    def test_method_not_found(self):
        """Test error response for non-existent method."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'nonexistent',
            'params': [],
            'id': '3',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], -32601)
        self.assertEqual(data['error']['message'], 'Method not found')

    def test_parse_error(self):
        """Test error response for invalid JSON."""
        response = self.client.post(
            '/rpc/',
            data='invalid json {',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error']['code'], -32700)
        self.assertEqual(data['error']['message'], 'Parse error')

    def test_internal_error(self):
        """Test error response when method raises exception."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'error_method',
            'params': [],
            'id': '4',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], -32603)
        self.assertEqual(data['error']['message'], 'Internal error')
        self.assertIn('Test error', data['error']['data'])

    def test_jsonrpc_version_preserved(self):
        """Test that JSON-RPC version is preserved in response."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'echo',
            'params': ['test'],
            'id': '5',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertEqual(data['jsonrpc'], '2.0')

    def test_request_id_preserved(self):
        """Test that request ID is preserved in response."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'echo',
            'params': ['test'],
            'id': 'unique-id-123',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertEqual(data['id'], 'unique-id-123')

    def test_params_list_format(self):
        """Test handling of params as a list."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'echo',
            'params': ['list_param'],
            'id': '6',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        self.assertEqual(data['result'], 'list_param')

    def test_default_params_to_empty_list(self):
        """Test that params defaults to empty list."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'get_user',
            'id': '7',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Should get an error about missing required argument
        data = response.json()
        self.assertIn('error', data)


class TestLoginJSONRPCMethod(TestCase):
    """Tests for the login JSON-RPC method specifically."""

    def setUp(self):
        """Set up test client and test user."""
        self.client = Client()
        self.user = User.objects.create(
            username='testuser',
            status='offline',
            logintime=timezone.now(),
            logouttime=timezone.now() - timedelta(hours=1),
            extendtime=timezone.now(),
            autologout=600,
        )

    def test_login_method_registered(self):
        """Test that login method is registered."""
        login_method = get_jsonrpc_method('login')
        self.assertIsNotNone(login_method)

    def test_login_via_json_rpc(self):
        """Test login via JSON-RPC endpoint."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'login',
            'params': ['testuser'],
            'id': '1',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('result', data)
        # Result should be a string indicating success
        self.assertTrue(data['result'])

    def test_login_method_exists(self):
        """Test that the actual login method exists in views."""
        # Check that login is among registered methods
        all_methods = get_jsonrpc_methods()
        self.assertIn('login', all_methods)


class TestJSONRPCMethodsCount(TestCase):
    """Tests to verify all expected JSON-RPC methods are registered."""

    def test_expected_methods_registered(self):
        """Test that all expected methods are registered."""
        all_methods = get_jsonrpc_methods()

        # List of key methods that should be registered
        expected_methods = [
            'login',
            'logout',
            'who',
            'eta',
            'available',
            'get_user_by_name',
            'get_user_by_id',
        ]

        for method_name in expected_methods:
            self.assertIn(
                method_name,
                all_methods,
                f"Method '{method_name}' not found in registry"
            )

    def test_significant_number_of_methods(self):
        """Test that a significant number of methods are registered."""
        all_methods = get_jsonrpc_methods()
        # We expect many methods (>50)
        self.assertGreater(
            len(all_methods),
            50,
            "Expected many JSON-RPC methods to be registered"
        )


class TestJSONRPCEndpointSecurity(TestCase):
    """Tests for security aspects of the JSON-RPC endpoint."""

    def setUp(self):
        """Set up test client and clear registry."""
        self.client = Client()
        _jsonrpc_method_registry.clear()

        @jsonrpc_method('safe_method')
        def safe_method(request):
            return "safe result"

    def test_post_only(self):
        """Test that GET requests are not allowed."""
        response = self.client.get('/rpc/')
        self.assertIn(response.status_code, [405, 404])  # Method Not Allowed or Not Found

    def test_csrf_exempt(self):
        """Test that endpoint is CSRF exempt for JSON-RPC calls."""
        # JSON-RPC endpoint should work without CSRF token
        payload = {
            'jsonrpc': '2.0',
            'method': 'safe_method',
            'params': [],
            'id': '1',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Should not get CSRF error
        self.assertEqual(response.status_code, 200)

    def test_malicious_payload_handling(self):
        """Test handling of potentially malicious payloads."""
        # Very large payload
        large_payload = {
            'jsonrpc': '2.0',
            'method': 'safe_method',
            'params': ['x' * 10000],
            'id': '1',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(large_payload),
            content_type='application/json',
        )

        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400, 500])


class TestJSONRPCIntegration(TestCase):
    """Integration tests for the complete JSON-RPC system."""

    def setUp(self):
        """Set up test client and test data."""
        self.client = Client()
        _jsonrpc_method_registry.clear()

        self.test_user = User.objects.create(
            username='integrationtest',
            status='online',
            logintime=timezone.now(),
            logouttime=timezone.now() + timedelta(hours=1),
            extendtime=timezone.now(),
            autologout=600,
        )

        @jsonrpc_method('get_status')
        def get_status(request, username):
            user = User.objects.filter(username=username).first()
            return user.status if user else 'unknown'

        @jsonrpc_method('set_status')
        def set_status(request, username, new_status):
            user = User.objects.filter(username=username).first()
            if user:
                user.status = new_status
                user.save()
                return f"Status updated to {new_status}"
            return "User not found"

    def test_sequential_rpc_calls(self):
        """Test that sequential RPC calls work correctly."""
        # First call: get status
        payload1 = {
            'jsonrpc': '2.0',
            'method': 'get_status',
            'params': ['integrationtest'],
            'id': '1',
        }

        response1 = self.client.post(
            '/rpc/',
            data=json.dumps(payload1),
            content_type='application/json',
        )
        data1 = response1.json()
        self.assertEqual(data1['result'], 'online')

        # Second call: set status
        payload2 = {
            'jsonrpc': '2.0',
            'method': 'set_status',
            'params': ['integrationtest', 'offline'],
            'id': '2',
        }

        response2 = self.client.post(
            '/rpc/',
            data=json.dumps(payload2),
            content_type='application/json',
        )
        data2 = response2.json()
        self.assertIn('Status updated', data2['result'])

        # Third call: verify status changed
        response3 = self.client.post(
            '/rpc/',
            data=json.dumps(payload1),
            content_type='application/json',
        )
        data3 = response3.json()
        self.assertEqual(data3['result'], 'offline')

    def test_complex_response_types(self):
        """Test that different response types are handled correctly."""
        @jsonrpc_method('complex_response')
        def complex_response(request):
            return {
                'user': 'testuser',
                'status': 'online',
                'timestamp': '2024-01-01T00:00:00Z',
                'tags': ['alpha', 'beta'],
            }

        payload = {
            'jsonrpc': '2.0',
            'method': 'complex_response',
            'params': [],
            'id': '1',
        }

        response = self.client.post(
            '/rpc/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        data = response.json()
        result = data['result']
        self.assertEqual(result['user'], 'testuser')
        self.assertEqual(result['status'], 'online')
        self.assertEqual(result['tags'], ['alpha', 'beta'])
