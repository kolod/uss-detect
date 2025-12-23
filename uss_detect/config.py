"""Configuration management for USS detector.

Stores last used serial port and device identifiers.
"""

import json
from pathlib import Path
from typing import Optional


class Config:
    """Manages configuration persistence."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to config file (default: ~/.uss-detect.json)
        """
        if config_path is None:
            config_path = Path.home() / ".uss-detect.json"
        
        self.config_path = config_path
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            pass  # Silently fail if can't save config
    
    def get_last_port(self) -> Optional[str]:
        """Get last used serial port."""
        return self.data.get('last_port')
    
    def set_last_port(self, port: str):
        """Set last used serial port."""
        self.data['last_port'] = port
        self.save()
    
    def get_port_hwid(self, port: str) -> Optional[str]:
        """Get hardware ID for a port."""
        ports = self.data.get('ports', {})
        return ports.get(port, {}).get('hwid')
    
    def set_port_hwid(self, port: str, hwid: str):
        """Store hardware ID for a port."""
        if 'ports' not in self.data:
            self.data['ports'] = {}
        
        if port not in self.data['ports']:
            self.data['ports'][port] = {}
        
        self.data['ports'][port]['hwid'] = hwid
        self.save()
    
    def find_port_by_hwid(self, hwid: str) -> Optional[str]:
        """Find port name by hardware ID.
        
        Args:
            hwid: Hardware ID to search for
            
        Returns:
            Port name if found, None otherwise
        """
        ports = self.data.get('ports', {})
        for port, info in ports.items():
            if info.get('hwid') == hwid:
                return port
        return None
