#!/usr/bin/env python3
"""
Standalone test script for JSON-RPC decorator and registry system.
This can be run without Django or pytest to verify basic functionality.
"""

import sys
import os

# Add the c-beamd directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cbeamd.json_rpc_client import (
    jsonrpc_method,
    get_jsonrpc_method,
    get_jsonrpc_methods,
    _jsonrpc_method_registry,
)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def record_result(test_name, passed, message=""):
    """Print test result."""
    symbol = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
    msg = f" - {message}" if message else ""
    print(f"  {symbol} {test_name}{msg}")
    return passed


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print("JSON-RPC Decorator and Registry Tests")
    print(f"{'=' * 60}{Colors.END}\n")

    total_tests = 0
    passed_tests = 0

    # Test 1: Basic decorator registration
    print(f"{Colors.BOLD}Test Group: Decorator Registration{Colors.END}")
    _jsonrpc_method_registry.clear()

    total_tests += 1
    @jsonrpc_method('test1')
    def func1(request):
        return "result1"

    if record_result("Basic registration", get_jsonrpc_method('test1') is not None):
        passed_tests += 1

    # Test 2: Multiple methods
    total_tests += 1
    @jsonrpc_method('test2')
    def func2(request):
        return "result2"

    @jsonrpc_method('test3')
    def func3(request):
        return "result3"

    methods = get_jsonrpc_methods()
    if record_result("Multiple methods", len(methods) == 3, f"Found {len(methods)} methods"):
        passed_tests += 1

    # Test 3: Method lookup
    total_tests += 1
    method = get_jsonrpc_method('test1')
    if record_result("Method lookup", method is not None):
        passed_tests += 1

    # Test 4: Call registered method
    total_tests += 1
    result = method(None)
    if record_result("Call registered method", result == "result1", f"Got: {result}"):
        passed_tests += 1

    # Test 5: Metadata preservation
    print(f"\n{Colors.BOLD}Test Group: Metadata Preservation{Colors.END}")
    _jsonrpc_method_registry.clear()

    total_tests += 1
    @jsonrpc_method('documented')
    def documented_func(request):
        """This is a documented function."""
        return "result"

    registered = get_jsonrpc_method('documented')
    if record_result(
        "Metadata preserved",
        registered.__name__ == 'documented_func',
        f"Name: {registered.__name__}"
    ):
        passed_tests += 1

    total_tests += 1
    has_doc = "documented" in registered.__doc__.lower()
    if record_result("Docstring preserved", has_doc):
        passed_tests += 1

    # Test 6: Parameters handling
    print(f"\n{Colors.BOLD}Test Group: Parameters Handling{Colors.END}")
    _jsonrpc_method_registry.clear()

    total_tests += 1
    @jsonrpc_method('add')
    def add(request, a, b):
        return a + b

    registered = get_jsonrpc_method('add')
    result = registered(None, 5, 3)
    if record_result("Parameter passing", result == 8, f"5 + 3 = {result}"):
        passed_tests += 1

    # Test 7: Method not found
    total_tests += 1
    result = get_jsonrpc_method('nonexistent')
    if record_result("Method not found returns None", result is None):
        passed_tests += 1

    # Test 8: Registry isolation
    print(f"\n{Colors.BOLD}Test Group: Registry Management{Colors.END}")

    total_tests += 1
    methods1 = get_jsonrpc_methods()
    methods2 = get_jsonrpc_methods()
    is_copy = methods1 is not methods2
    if record_result("Registry returns copy", is_copy):
        passed_tests += 1

    # Test 10: Many methods
    total_tests += 1
    _jsonrpc_method_registry.clear()
    for i in range(100):
        @jsonrpc_method(f'method_{i}')
        def func(request, method_num=i):
            return method_num

    methods = get_jsonrpc_methods()
    if record_result("Register 100 methods", len(methods) == 100):
        passed_tests += 1

    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print(f"Test Results: {passed_tests}/{total_tests} passed")
    print(f"{'=' * 60}{Colors.END}\n")

    if passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}\n")
        return 0
    else:
        failed = total_tests - passed_tests
        print(f"{Colors.RED}{Colors.BOLD}✗ {failed} test(s) failed{Colors.END}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
