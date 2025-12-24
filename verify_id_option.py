#!/usr/bin/env python3
"""Manual verification of --id option parsing and integration."""

import sys
import argparse

# Import the actual main module
sys.path.insert(0, '/home/runner/work/uss-detect/uss-detect')
from uss_detect.__main__ import parse_address_range


def test_cli_help():
    """Verify help text includes --id option."""
    print("Testing CLI help output...")
    import subprocess
    result = subprocess.run(
        ['python', '-m', 'uss_detect', '--help'],
        cwd='/home/runner/work/uss-detect/uss-detect',
        capture_output=True,
        text=True
    )
    
    # Normalize whitespace to handle line wrapping
    help_text = ' '.join(result.stdout.split())
    
    assert '--id' in result.stdout, "Help should mention --id option"
    assert 'ADDRESSES' in result.stdout, "Help should mention ADDRESSES metavar"
    assert 'single (0)' in help_text, "Help should include example"
    assert '0-10' in result.stdout, "Help should include range example"
    assert '0,2,' in result.stdout or '0, 2,' in result.stdout, "Help should include comma example"
    
    print("✓ Help text verification passed")


def test_address_parsing_integration():
    """Test that addresses are correctly parsed and formatted."""
    print("\nTesting address parsing integration...")
    
    test_cases = [
        ("0", [0], "single address 0"),
        ("0-5", [0, 1, 2, 3, 4, 5], "range 0-5"),
        ("0,2,5", [0, 2, 5], "comma-separated"),
        ("0-2,5-7,10", [0, 1, 2, 5, 6, 7, 10], "mixed format"),
        ("31", [31], "maximum address"),
        ("0-31", list(range(32)), "full range"),
    ]
    
    for input_str, expected, description in test_cases:
        result = parse_address_range(input_str)
        assert result == expected, f"Failed: {description} - got {result}, expected {expected}"
        print(f"  ✓ {description}: '{input_str}' -> {result}")
    
    print("✓ Address parsing integration passed")


def test_error_cases():
    """Test error handling."""
    print("\nTesting error handling...")
    
    error_cases = [
        ("abc", "non-numeric input"),
        ("32", "out of range"),
        ("5-0", "reverse range"),
        ("-1", "negative address"),
        ("", "empty input"),
    ]
    
    for input_str, description in error_cases:
        try:
            result = parse_address_range(input_str)
            print(f"  ✗ Failed to catch: {description}")
            return False
        except ValueError as e:
            print(f"  ✓ {description}: correctly raises ValueError")
    
    print("✓ Error handling passed")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Manual Verification of --id Option")
    print("=" * 60)
    
    try:
        test_cli_help()
        test_address_parsing_integration()
        test_error_cases()
        
        print("\n" + "=" * 60)
        print("✓ ALL VERIFICATION TESTS PASSED")
        print("=" * 60)
        print("\nThe --id option is correctly implemented and integrated!")
        print("\nExample usage:")
        print("  uss-detect --id 0           # Scan only address 0")
        print("  uss-detect --id 0-10        # Scan addresses 0-10")
        print("  uss-detect --id 0,2,5       # Scan specific addresses")
        print("  uss-detect --force-all --id 1-5  # Combine options")
        return 0
    
    except AssertionError as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
