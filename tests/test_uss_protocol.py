"""Tests for USS protocol implementation."""

import pytest
from uss_detect.uss_protocol import USSProtocol


class TestBCCCalculation:
    """Test cases for BCC (Block Check Character) calculation."""
    
    def test_bcc_empty_data(self):
        """Test BCC calculation with empty data."""
        result = USSProtocol.calculate_bcc(b'')
        assert result == 0
    
    def test_bcc_single_byte(self):
        """Test BCC calculation with single byte."""
        result = USSProtocol.calculate_bcc(b'\x05')
        assert result == 0x05
    
    def test_bcc_two_bytes_same(self):
        """Test BCC calculation with two identical bytes (should XOR to 0)."""
        result = USSProtocol.calculate_bcc(b'\x05\x05')
        assert result == 0x00
    
    def test_bcc_two_bytes_different(self):
        """Test BCC calculation with two different bytes."""
        # 0x02 XOR 0x05 = 0x07
        result = USSProtocol.calculate_bcc(b'\x02\x05')
        assert result == 0x07
    
    def test_bcc_three_bytes(self):
        """Test BCC calculation with three bytes."""
        # 0x02 XOR 0x00 XOR 0x01 = 0x03
        result = USSProtocol.calculate_bcc(b'\x02\x00\x01')
        assert result == 0x03
    
    def test_bcc_ping_address_zero(self):
        """Test BCC for ping telegram to address 0.
        
        Ping telegram format: STX LGE ADR BCC
        For address 0 with no data: 02 02 00 ??
        BCC = LGE XOR ADR = 0x02 XOR 0x00 = 0x02
        """
        # Data without STX (LGE and ADR only)
        data = b'\x02\x00'  # LGE=0x02, ADR=0x00
        result = USSProtocol.calculate_bcc(data)
        assert result == 0x02
    
    def test_bcc_ping_address_five(self):
        """Test BCC for ping telegram to address 5.
        
        For address 5 with no data: 02 02 05 ??
        BCC = LGE XOR ADR = 0x02 XOR 0x05 = 0x07
        """
        data = b'\x02\x05'  # LGE=0x02, ADR=0x05
        result = USSProtocol.calculate_bcc(data)
        assert result == 0x07
    
    def test_bcc_with_net_data(self):
        """Test BCC calculation with net data.
        
        Example: LGE=0x04, ADR=0x01, Data=0x12, 0x34
        BCC = 0x04 XOR 0x01 XOR 0x12 XOR 0x34 = 0x23
        """
        data = b'\x04\x01\x12\x34'
        result = USSProtocol.calculate_bcc(data)
        expected = 0x04 ^ 0x01 ^ 0x12 ^ 0x34
        assert result == expected
        assert result == 0x23
    
    def test_bcc_all_bits_set(self):
        """Test BCC with all bits set."""
        result = USSProtocol.calculate_bcc(b'\xFF\xFF')
        assert result == 0x00  # 0xFF XOR 0xFF = 0x00
    
    def test_bcc_alternating_pattern(self):
        """Test BCC with alternating bit pattern."""
        # 0xAA = 10101010, 0x55 = 01010101
        result = USSProtocol.calculate_bcc(b'\xAA\x55')
        assert result == 0xFF  # All bits flip


class TestTelegramCreation:
    """Test cases for USS telegram creation."""
    
    def test_create_ping_address_zero(self):
        """Test creating ping telegram for address 0."""
        telegram = USSProtocol.create_ping_telegram(0)
        # Expected: STX=0x02, LGE=0x02, ADR=0x00, BCC=0x02
        expected = bytes([0x02, 0x02, 0x00, 0x02])
        assert telegram == expected
    
    def test_create_ping_address_five(self):
        """Test creating ping telegram for address 5."""
        telegram = USSProtocol.create_ping_telegram(5)
        # Expected: STX=0x02, LGE=0x02, ADR=0x05, BCC=0x07
        expected = bytes([0x02, 0x02, 0x05, 0x07])
        assert telegram == expected
    
    def test_create_ping_max_address(self):
        """Test creating ping telegram for max address 31."""
        telegram = USSProtocol.create_ping_telegram(31)
        # BCC = 0x02 XOR 0x1F = 0x1D
        expected = bytes([0x02, 0x02, 0x1F, 0x1D])
        assert telegram == expected
    
    def test_create_telegram_invalid_address_negative(self):
        """Test that negative addresses raise ValueError."""
        with pytest.raises(ValueError, match="Address must be 0-31"):
            USSProtocol.create_telegram(-1)
    
    def test_create_telegram_invalid_address_too_high(self):
        """Test that addresses > 31 raise ValueError."""
        with pytest.raises(ValueError, match="Address must be 0-31"):
            USSProtocol.create_telegram(32)
    
    def test_create_telegram_with_pkw(self):
        """Test creating telegram with PKW data."""
        # Single PKW word
        telegram = USSProtocol.create_telegram(0, pkw=[0x1234])
        # STX, LGE=4 (ADR+2bytes+BCC), ADR=0, PKW_HI=0x12, PKW_LO=0x34, BCC
        # BCC = 0x04 XOR 0x00 XOR 0x12 XOR 0x34 = 0x22
        assert telegram[0] == 0x02  # STX
        assert telegram[1] == 0x04  # LGE
        assert telegram[2] == 0x00  # ADR
        assert telegram[3] == 0x12  # PKW high byte
        assert telegram[4] == 0x34  # PKW low byte
        assert telegram[5] == 0x22  # BCC
    
    def test_create_telegram_with_pzd(self):
        """Test creating telegram with PZD data."""
        # Single PZD word
        telegram = USSProtocol.create_telegram(1, pzd=[0xABCD])
        # STX, LGE=4, ADR=1, PZD_HI=0xAB, PZD_LO=0xCD, BCC
        # BCC = 0x04 XOR 0x01 XOR 0xAB XOR 0xCD = 0x63
        assert telegram[0] == 0x02  # STX
        assert telegram[1] == 0x04  # LGE
        assert telegram[2] == 0x01  # ADR
        assert telegram[3] == 0xAB  # PZD high byte
        assert telegram[4] == 0xCD  # PZD low byte
        assert telegram[5] == 0x63  # BCC
    
    def test_create_telegram_with_pkw_and_pzd(self):
        """Test creating telegram with both PKW and PZD data."""
        telegram = USSProtocol.create_telegram(5, pkw=[0x0001], pzd=[0x1000])
        # STX, LGE=6 (ADR + 4 bytes data + BCC), ADR=5, PKW=0x0001, PZD=0x1000, BCC
        # BCC = 0x06 XOR 0x05 XOR 0x00 XOR 0x01 XOR 0x10 XOR 0x00 = 0x12
        assert len(telegram) == 8  # STX + LGE + ADR + 2*PKW + 2*PZD + BCC
        assert telegram[0] == 0x02
        assert telegram[1] == 0x06
        assert telegram[2] == 0x05
        assert telegram[-1] == 0x12  # BCC


class TestTelegramParsing:
    """Test cases for USS telegram parsing."""
    
    def test_parse_ping_address_zero(self):
        """Test parsing ping telegram for address 0."""
        telegram = bytes([0x02, 0x02, 0x00, 0x02])
        result = USSProtocol.parse_telegram(telegram)
        
        assert result is not None
        assert result['valid'] is True
        assert result['address'] == 0
        assert result['length'] == 2
        assert result['words'] == []
    
    def test_parse_ping_address_five(self):
        """Test parsing ping telegram for address 5."""
        telegram = bytes([0x02, 0x02, 0x05, 0x07])
        result = USSProtocol.parse_telegram(telegram)
        
        assert result is not None
        assert result['valid'] is True
        assert result['address'] == 5
        assert result['length'] == 2
        assert result['words'] == []
    
    def test_parse_telegram_with_data(self):
        """Test parsing telegram with data words."""
        # Create a valid telegram with one word
        telegram = bytes([0x02, 0x04, 0x00, 0x12, 0x34, 0x22])
        result = USSProtocol.parse_telegram(telegram)
        
        assert result is not None
        assert result['valid'] is True
        assert result['address'] == 0
        assert result['length'] == 4
        assert result['words'] == [0x1234]
    
    def test_parse_telegram_invalid_stx(self):
        """Test that telegram with wrong STX is rejected."""
        telegram = bytes([0x01, 0x02, 0x00, 0x02])  # Wrong STX
        result = USSProtocol.parse_telegram(telegram)
        assert result is None
    
    def test_parse_telegram_invalid_bcc(self):
        """Test that telegram with wrong BCC is rejected."""
        telegram = bytes([0x02, 0x02, 0x00, 0xFF])  # Wrong BCC
        result = USSProtocol.parse_telegram(telegram)
        assert result is None
    
    def test_parse_telegram_too_short(self):
        """Test that too short telegram is rejected."""
        telegram = bytes([0x02, 0x02])  # Only 2 bytes
        result = USSProtocol.parse_telegram(telegram)
        assert result is None
    
    def test_parse_telegram_truncated(self):
        """Test that truncated telegram is rejected."""
        # LGE says 4 bytes should follow, but only 2 are present
        telegram = bytes([0x02, 0x04, 0x00])
        result = USSProtocol.parse_telegram(telegram)
        assert result is None
    
    def test_parse_telegram_multiple_words(self):
        """Test parsing telegram with multiple data words."""
        # Two words: 0x1234 and 0x5678
        # STX=0x02, LGE=6, ADR=1, Data1=0x12,0x34, Data2=0x56,0x78, BCC
        # BCC = 0x06 XOR 0x01 XOR 0x12 XOR 0x34 XOR 0x56 XOR 0x78 = 0x0F
        telegram = bytes([0x02, 0x06, 0x01, 0x12, 0x34, 0x56, 0x78, 0x0F])
        result = USSProtocol.parse_telegram(telegram)
        
        assert result is not None
        assert result['valid'] is True
        assert result['address'] == 1
        assert result['length'] == 6
        assert result['words'] == [0x1234, 0x5678]
    
    def test_roundtrip_ping(self):
        """Test that created telegram can be parsed back correctly."""
        # Create ping telegram
        created = USSProtocol.create_ping_telegram(10)
        
        # Parse it back
        parsed = USSProtocol.parse_telegram(created)
        
        assert parsed is not None
        assert parsed['valid'] is True
        assert parsed['address'] == 10
        assert parsed['words'] == []
    
    def test_roundtrip_with_data(self):
        """Test roundtrip with PKW and PZD data."""
        # Create telegram with data
        pkw_data = [0x1234, 0x5678]
        pzd_data = [0xABCD, 0xEF01]
        created = USSProtocol.create_telegram(15, pkw=pkw_data, pzd=pzd_data)
        
        # Parse it back
        parsed = USSProtocol.parse_telegram(created)
        
        assert parsed is not None
        assert parsed['valid'] is True
        assert parsed['address'] == 15
        assert parsed['words'] == pkw_data + pzd_data


class TestConstants:
    """Test USS protocol constants."""
    
    def test_stx_value(self):
        """Test STX constant is correct."""
        assert USSProtocol.STX == 0x02
    
    def test_baudrates_list(self):
        """Test baudrates list is complete and sorted."""
        expected = [115200, 57600, 38400, 19200, 9600, 4800, 2400, 1200]
        assert USSProtocol.BAUDRATES == expected
    
    def test_address_range(self):
        """Test address range constants."""
        assert USSProtocol.MIN_ADDRESS == 0
        assert USSProtocol.MAX_ADDRESS == 31
