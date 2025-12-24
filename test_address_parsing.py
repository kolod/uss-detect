#!/usr/bin/env python3
"""Tests for address range parsing functionality."""

import sys
import os

# Add parent directory to path to import uss_detect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uss_detect.__main__ import parse_address_range
from uss_detect.uss_protocol import USSProtocol


def test_single_address():
    """Test parsing single address."""
    print("Testing single address...")
    
    # Test valid single addresses
    assert parse_address_range("0") == [0], "Failed: single address 0"
    assert parse_address_range("5") == [5], "Failed: single address 5"
    assert parse_address_range("31") == [31], "Failed: single address 31"
    
    print("✓ Single address tests passed")


def test_address_range():
    """Test parsing address ranges."""
    print("\nTesting address ranges...")
    
    # Test valid ranges
    assert parse_address_range("0-5") == [0, 1, 2, 3, 4, 5], "Failed: range 0-5"
    assert parse_address_range("10-15") == [10, 11, 12, 13, 14, 15], "Failed: range 10-15"
    assert parse_address_range("0-31") == list(range(32)), "Failed: range 0-31"
    assert parse_address_range("5-5") == [5], "Failed: single value range 5-5"
    
    # Test with spaces
    assert parse_address_range("0 - 5") == [0, 1, 2, 3, 4, 5], "Failed: range with spaces"
    assert parse_address_range(" 0-5 ") == [0, 1, 2, 3, 4, 5], "Failed: range with leading/trailing spaces"
    
    print("✓ Address range tests passed")


def test_comma_separated():
    """Test parsing comma-separated addresses."""
    print("\nTesting comma-separated addresses...")
    
    # Test valid comma-separated lists
    assert parse_address_range("0,2,5") == [0, 2, 5], "Failed: comma-separated 0,2,5"
    assert parse_address_range("1,2,3,4") == [1, 2, 3, 4], "Failed: comma-separated 1,2,3,4"
    assert parse_address_range("0,5,10,15") == [0, 5, 10, 15], "Failed: comma-separated with gaps"
    
    # Test with spaces
    assert parse_address_range("0, 2, 5") == [0, 2, 5], "Failed: comma-separated with spaces"
    assert parse_address_range(" 0 , 2 , 5 ") == [0, 2, 5], "Failed: comma-separated with extra spaces"
    
    # Test duplicates (should be removed by set)
    assert parse_address_range("0,0,1,1,2") == [0, 1, 2], "Failed: duplicates not removed"
    
    print("✓ Comma-separated tests passed")


def test_mixed_formats():
    """Test parsing mixed comma-separated and ranges."""
    print("\nTesting mixed formats...")
    
    # Test combinations
    assert parse_address_range("0,2-4,6") == [0, 2, 3, 4, 6], "Failed: mixed 0,2-4,6"
    assert parse_address_range("0-2,5-7") == [0, 1, 2, 5, 6, 7], "Failed: multiple ranges 0-2,5-7"
    assert parse_address_range("1,3-5,7,9-10") == [1, 3, 4, 5, 7, 9, 10], "Failed: complex mixed"
    
    print("✓ Mixed format tests passed")


def test_invalid_formats():
    """Test that invalid formats raise ValueError."""
    print("\nTesting invalid formats...")
    
    invalid_inputs = [
        ("abc", "non-numeric"),
        ("0-", "incomplete range"),
        ("-5", "missing start"),
        ("5-0", "reverse range (start > end)"),
        ("0--5", "double dash"),
        ("", "empty string"),
        ("0,", "trailing comma"),
        (",0", "leading comma"),
    ]
    
    for input_str, description in invalid_inputs:
        try:
            result = parse_address_range(input_str)
            print(f"✗ Failed to catch invalid input: {description} ('{input_str}') -> {result}")
            assert False, f"Should have raised ValueError for {description}"
        except ValueError:
            pass  # Expected
    
    print("✓ Invalid format tests passed")


def test_out_of_range():
    """Test that out-of-range addresses raise ValueError."""
    print("\nTesting out-of-range addresses...")
    
    # Note: "-1" is treated as a range format (empty start, 1 end) and causes "Invalid range format" error
    # This is acceptable behavior since negative addresses are not valid in ranges either
    out_of_range_inputs = [
        ("32", "address too high", "out of valid range"),
        ("0-32", "range exceeds maximum", "out of valid range"),
        ("100", "far out of range", "out of valid range"),
        ("-1", "negative (treated as range)", "Invalid range format"),
    ]
    
    for input_str, description, expected_msg in out_of_range_inputs:
        try:
            result = parse_address_range(input_str)
            print(f"✗ Failed to catch out-of-range: {description} ('{input_str}') -> {result}")
            assert False, f"Should have raised ValueError for {description}"
        except ValueError as e:
            if expected_msg not in str(e):
                print(f"✗ Wrong error message for {description}: expected '{expected_msg}' in error, got '{e}'")
                assert False, f"Expected '{expected_msg}' in error message"
    
    print("✓ Out-of-range tests passed")


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")
    
    # Test minimum and maximum addresses
    assert parse_address_range("0") == [USSProtocol.MIN_ADDRESS], "Failed: minimum address"
    assert parse_address_range("31") == [USSProtocol.MAX_ADDRESS], "Failed: maximum address"
    assert parse_address_range(f"{USSProtocol.MIN_ADDRESS}-{USSProtocol.MAX_ADDRESS}") == list(range(USSProtocol.MIN_ADDRESS, USSProtocol.MAX_ADDRESS + 1)), "Failed: full range"
    
    print("✓ Edge case tests passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Address Range Parsing Tests")
    print("=" * 60)
    
    try:
        test_single_address()
        test_address_range()
        test_comma_separated()
        test_mixed_formats()
        test_invalid_formats()
        test_out_of_range()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ UNEXPECTED ERROR: {e}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
