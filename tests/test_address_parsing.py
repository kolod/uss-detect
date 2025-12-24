"""Tests for address range parsing functionality."""

import pytest
from uss_detect.__main__ import parse_address_range


class TestParseAddressRange:
    """Test cases for parse_address_range function."""
    
    # Single address tests
    def test_single_address_zero(self):
        """Test parsing single address 0."""
        result = parse_address_range("0")
        assert result == [0]
    
    def test_single_address_middle(self):
        """Test parsing single address in middle of range."""
        result = parse_address_range("15")
        assert result == [15]
    
    def test_single_address_max(self):
        """Test parsing maximum address."""
        result = parse_address_range("31")
        assert result == [31]
    
    # Range tests
    def test_range_start_to_end(self):
        """Test parsing range from 0 to 10."""
        result = parse_address_range("0-10")
        assert result == list(range(0, 11))
    
    def test_range_middle_values(self):
        """Test parsing range in middle of address space."""
        result = parse_address_range("10-15")
        assert result == [10, 11, 12, 13, 14, 15]
    
    def test_range_full_span(self):
        """Test parsing full address range."""
        result = parse_address_range("0-31")
        assert result == list(range(0, 32))
    
    def test_range_single_value(self):
        """Test range with same start and end."""
        result = parse_address_range("5-5")
        assert result == [5]
    
    def test_range_with_spaces(self):
        """Test range with whitespace."""
        result = parse_address_range("5 - 10")
        assert result == [5, 6, 7, 8, 9, 10]
    
    # Comma-separated tests
    def test_comma_separated_simple(self):
        """Test simple comma-separated addresses."""
        result = parse_address_range("0,2,3")
        assert result == [0, 2, 3]
    
    def test_comma_separated_unordered(self):
        """Test unordered comma-separated addresses are sorted."""
        result = parse_address_range("5,1,3")
        assert result == [1, 3, 5]
    
    def test_comma_separated_with_spaces(self):
        """Test comma-separated with whitespace."""
        result = parse_address_range("1, 5, 10")
        assert result == [1, 5, 10]
    
    def test_comma_separated_duplicates(self):
        """Test that duplicates are removed."""
        result = parse_address_range("1,2,1,3,2")
        assert result == [1, 2, 3]
    
    # Mixed format tests
    def test_mixed_ranges_and_singles(self):
        """Test combination of ranges and single addresses."""
        result = parse_address_range("0-2,5,10-12")
        assert result == [0, 1, 2, 5, 10, 11, 12]
    
    def test_mixed_with_overlaps(self):
        """Test mixed format with overlapping values."""
        result = parse_address_range("0-5,3-7,10")
        assert result == [0, 1, 2, 3, 4, 5, 6, 7, 10]
    
    # Error cases - invalid format
    def test_invalid_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("")
    
    def test_invalid_non_numeric(self):
        """Test that non-numeric input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("abc")
    
    def test_invalid_range_format(self):
        """Test that invalid range format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_address_range("1-2-3")
    
    def test_invalid_range_reversed(self):
        """Test that reversed range (start > end) raises ValueError."""
        with pytest.raises(ValueError, match="start > end"):
            parse_address_range("10-5")
    
    # Error cases - out of range
    def test_address_below_minimum(self):
        """Test that address below minimum raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_address_range("-1")
    
    def test_address_above_maximum(self):
        """Test that address above maximum raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("32")
    
    def test_range_with_invalid_start(self):
        """Test range with start address out of range."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_address_range("-1-5")
    
    def test_range_with_invalid_end(self):
        """Test range with end address out of range."""
        with pytest.raises(ValueError, match="out of valid range"):
            parse_address_range("28-35")
    
    def test_comma_list_with_invalid_address(self):
        """Test comma-separated list with one invalid address."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("1,5,100")
    
    # Edge cases
    def test_single_trailing_comma(self):
        """Test single address with trailing comma."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("5,")
    
    def test_multiple_commas(self):
        """Test multiple consecutive commas."""
        with pytest.raises(ValueError, match="Invalid address"):
            parse_address_range("1,,5")
