# USS Device Detector

![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Automatically detects Siemens USS protocol devices on a serial bus and determines their configuration (device IDs and baudrate).

## Features

- 🔍 **Automatic Device Detection** - Scans for all USS devices on the bus
- ⚡ **Smart Baudrate Detection** - Tests faster baudrates first for quick detection
- 💾 **Port Memory** - Remembers your last used serial port and reconnects automatically
- 🔌 **Auto-Connect** - Waits for serial port connection and auto-connects when available
- 🎨 **Rich UI** - Beautiful terminal interface with progress indicators and color output
- ⌨️ **Ctrl+C Support** - Gracefully stop detection at any time
- 🔧 **Force Mode** - Test all combinations for devices with non-standard baudrates

## What is USS Protocol?

USS (Universal Serial Interface Protocol) is a serial communication protocol developed by Siemens for communication with frequency converters and drives. It uses RS-485 physical layer and allows control and monitoring of industrial automation equipment.

## Installation

### Using uv (recommended)

```bash
git clone https://github.com/kolod/uss-detect.git
cd uss-detect
uv sync
```

### Using pip

```bash
git clone https://github.com/kolod/uss-detect.git
cd uss-detect
pip install -e .
```

## Usage

### Basic Detection

```bash
uss-detect
```

This will:
1. Connect to a serial port (using last port as default or waiting for connection)
2. Scan for USS devices starting with fastest baudrate
3. Display all found devices with their addresses and bus settings
4. Exit after detection completes

### Force All Combinations

For buses where some devices have incorrect baudrate configuration:

```bash
uss-detect --force-all
```

This mode tests all baudrate and address combinations to find misconfigured devices.

### Example Output

```
USS Device Detector
Siemens USS Protocol Device Scanner

Connected to: COM3
USB Serial Device

Starting USS device detection...
Press Ctrl+C to stop at any time

Testing 115200 baud ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 
Testing 57600 baud - Found device at address 1

==================================================
Detection Complete!

Bus Settings:
  Baudrate: 57600 baud
  Parity: Even
  Data bits: 8
  Stop bits: 1

Found Devices:
  • Address: 1
  • Address: 3
==================================================
```

## How It Works

### Port Selection

1. **Port Memory**: The tool remembers the last used port and its hardware ID
2. **Auto-Detection**: If the same physical device is connected (even on a different port), it's automatically detected
3. **Wait Mode**: If no ports are available, enters waiting mode with a spinner
4. **Multi-Port**: If multiple ports connect simultaneously, prompts for selection

### Device Detection

1. **Baudrate Scanning**: Tests standard USS baudrates in order: 115200, 57600, 38400, 19200, 9600, 4800, 2400, 1200
2. **Address Scanning**: For each baudrate, tests addresses 0-31
3. **Smart Exit**: Stops after finding first device (unless `--force-all` is used)
4. **USS Protocol**: Uses proper USS telegram structure with BCC checksum verification

### USS Protocol Details

USS telegrams follow this structure:
- STX (0x02) - Start byte
- ADR - Device address (0-31)
- LEN - Number of data words
- DATA - PKW and PZD words (16-bit, big-endian)
- BCC - XOR checksum

## Configuration

Configuration is stored in `~/.uss-detect.json` and includes:
- Last used serial port
- Hardware IDs for port identification
- Port mapping for automatic reconnection

## Requirements

- Python 3.13+
- pyserial >= 3.5
- rich >= 14.2.0

## Supported Platforms

- Windows
- Linux
- macOS

## Tested Devices

This tool works with Siemens devices supporting USS protocol:
- MICROMASTER frequency converters
- SINAMICS drives
- Other USS-compatible Siemens devices

## Troubleshooting

### No devices detected

- Verify devices are powered on
- Check RS-485 wiring (A/B connections)
- Ensure correct serial port is selected
- Try `--force-all` mode for non-standard configurations
- Check that devices are configured for USS protocol (not MODBUS)

### Port not found

- Device may be using different port number - the tool will detect by hardware ID
- Try waiting mode - disconnect and reconnect the USB-RS485 adapter

### Detection is slow

- Normal mode prioritizes faster baudrates first
- Time depends on actual device baudrate and number of addresses to scan

## Development

### Project Structure

```
uss-detect/
├── uss_detect/
│   ├── __init__.py       # Package initialization
│   ├── __main__.py       # Main application logic
│   ├── config.py         # Configuration management
│   └── uss_protocol.py   # USS protocol implementation
├── pyproject.toml        # Project metadata and dependencies
└── README.md            # This file
```

### Running from source

```bash
uv run python -m uss_detect
```

## License

MIT License - see LICENSE file for details

## Author

**Oleksandr Kolodkin**
- Email: oleksandr.kolodkin@ukr.net
- GitHub: [@kolod](https://github.com/kolod)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Siemens for the USS protocol specification
- Rich library for beautiful terminal output
- PySerial for serial communication support
