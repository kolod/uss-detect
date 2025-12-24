"""Siemens USS Protocol Implementation

USS (Universal Serial Interface Protocol) is used for communication with Siemens drives.
"""


class USSProtocol:
    """Handles USS protocol telegram generation and parsing."""
    
    # USS telegram structure: STX LGE ADR [net data] BCC
    # According to USS specification section A.4:
    # - STX = Start of Text (0x02)
    # - LGE = Telegram length (ADR + net characters + BCC)
    # - ADR = Address byte
    # - Net data = PKW and PZD words
    # - BCC = Block check character (XOR checksum)
    STX = 0x02
    
    # Standard USS baudrates (ordered from fastest to slowest)
    BAUDRATES = [115200, 57600, 38400, 19200, 9600, 4800, 2400, 1200]
    
    # Standard USS device addresses (0-31)
    MIN_ADDRESS = 0
    MAX_ADDRESS = 31
    
    @staticmethod
    def calculate_bcc(data: bytes) -> int:
        """Calculate Block Check Character (XOR checksum) for USS telegram.
        
        Args:
            data: Telegram data without BCC
            
        Returns:
            BCC checksum byte
        """
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc
    
    @staticmethod
    def create_telegram(address: int, pkw: list[int] = None, pzd: list[int] = None) -> bytes:
        """Create USS telegram for communication.
        
        Args:
            address: Device address (0-31)
            pkw: Parameter channel words (PKW)
            pzd: Process data words (PZD)
            
        Returns:
            Complete USS telegram as bytes
        """
        if not 0 <= address <= 31:
            raise ValueError(f"Address must be 0-31, got {address}")
        
        pkw = pkw or []
        pzd = pzd or []
        
        # Build telegram according to USS specification: STX LGE ADR [net data] BCC
        telegram = bytearray()
        telegram.append(USSProtocol.STX)
        
        # Calculate net data length in bytes
        net_data_bytes = (len(pkw) + len(pzd)) * 2
        
        # LGE = ADR (1 byte) + net data bytes + BCC (1 byte)
        # According to spec: LGE = n + 2, where n is number of net characters
        length = net_data_bytes + 2
        telegram.append(length)
        
        # Add address byte
        telegram.append(address)
        
        # Add PKW words (high byte first)
        for word in pkw:
            telegram.append((word >> 8) & 0xFF)
            telegram.append(word & 0xFF)
        
        # Add PZD words (high byte first)
        for word in pzd:
            telegram.append((word >> 8) & 0xFF)
            telegram.append(word & 0xFF)
        
        # Calculate BCC on all bytes except STX (from LGE onwards)
        # According to USS spec section A.4.4: BCC is XOR of LGE, ADR, and all net data
        bcc = USSProtocol.calculate_bcc(telegram[1:])  # Skip STX at index 0
        telegram.append(bcc)
        
        return bytes(telegram)
    
    @staticmethod
    def parse_telegram(data: bytes) -> dict:
        """Parse received USS telegram.
        
        Args:
            data: Received telegram bytes
            
        Returns:
            Dictionary with parsed telegram fields or None if invalid
        """
        if len(data) < 4:
            return None
        
        if data[0] != USSProtocol.STX:
            return None
        
        # According to USS spec: STX LGE ADR [net data] BCC
        length = data[1]  # LGE byte
        address = data[2]  # ADR byte
        
        # Calculate expected size
        # LGE includes: ADR (1) + net characters (n) + BCC (1)
        # Total telegram = STX (1) + LGE (1) + [LGE bytes]
        expected_size = 2 + length  # STX + LGE + (ADR + net_data + BCC)
        if len(data) < expected_size:
            return None
        
        # Verify BCC (last byte)
        bcc_received = data[expected_size - 1]
        bcc_calculated = USSProtocol.calculate_bcc(data[1:expected_size - 1])
        
        if bcc_received != bcc_calculated:
            return None
        
        # Extract net data words (between ADR and BCC)
        # Net data starts at index 3, ends before BCC
        net_data_bytes = length - 2  # Subtract ADR and BCC from LGE
        words = []
        for i in range(3, 3 + net_data_bytes, 2):
            if i + 1 < len(data):
                word = (data[i] << 8) | data[i + 1]
                words.append(word)
        
        return {
            'address': address,
            'length': length,
            'words': words,
            'valid': True
        }
    
    @staticmethod
    def create_read_parameter_telegram(address: int, parameter: int) -> bytes:
        """Create telegram to read a parameter from USS device.
        
        Args:
            address: Device address
            parameter: Parameter number to read
            
        Returns:
            USS telegram bytes
        """
        # PKW for parameter read: task=1 (request), parameter number
        # Format: AK IND PWE1 PWE2
        # AK = 0x01 (request), IND = parameter index
        pkw = [0x0100 | ((parameter >> 8) & 0xFF), (parameter & 0xFF) << 8]
        return USSProtocol.create_telegram(address, pkw=pkw)
    
    @staticmethod
    def create_ping_telegram(address: int) -> bytes:
        """Create simple ping telegram to check device presence.
        
        Args:
            address: Device address to ping
            
        Returns:
            USS telegram bytes
        """
        # Simple telegram with no PKW/PZD - just for presence check
        return USSProtocol.create_telegram(address, pkw=[], pzd=[])
