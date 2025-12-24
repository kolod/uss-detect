#!/usr/bin/env python3
"""USS Device Detector

Detects Siemens USS protocol devices on serial bus and determines their settings.

Author: Oleksandr Kolodkin <oleksandr.kolodkin@ukr.net>
GitHub: https://github.com/kolod
"""

import argparse
import signal
import sys
import time
from typing import Optional, List, Tuple

import serial
import serial.tools.list_ports
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

from .config import Config
from .uss_protocol import USSProtocol


console = Console()
exit_requested = False


def parse_address_range(address_arg: str) -> List[int]:
    """Parse address range argument.
    
    Supported formats:
    - Single address: "0"
    - Range: "0-10"
    - Comma-separated: "0,2,3"
    
    Args:
        address_arg: Address specification string
        
    Returns:
        List of addresses to scan
        
    Raises:
        ValueError: If format is invalid or addresses out of range
    """
    addresses = set()
    
    # Split by commas for comma-separated values
    parts = address_arg.split(',')
    
    for part in parts:
        part = part.strip()
        
        # Check if it's a range
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                
                if start > end:
                    raise ValueError(f"Invalid range: {part} (start > end)")
                
                for addr in range(start, end + 1):
                    if not (USSProtocol.MIN_ADDRESS <= addr <= USSProtocol.MAX_ADDRESS):
                        raise ValueError(f"Address {addr} out of valid range [{USSProtocol.MIN_ADDRESS}-{USSProtocol.MAX_ADDRESS}]")
                    addresses.add(addr)
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid range format: {part}")
                raise
        else:
            # Single address
            try:
                addr = int(part)
            except ValueError:
                raise ValueError(f"Invalid address: {part}")
            
            if not (USSProtocol.MIN_ADDRESS <= addr <= USSProtocol.MAX_ADDRESS):
                raise ValueError(f"Address {addr} out of valid range [{USSProtocol.MIN_ADDRESS}-{USSProtocol.MAX_ADDRESS}]")
            addresses.add(addr)
    
    return sorted(list(addresses))


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global exit_requested
    exit_requested = True
    console.print("\n[yellow]Stopping detection...[/yellow]")


def get_available_ports() -> List[serial.tools.list_ports_common.ListPortInfo]:
    """Get list of available serial ports."""
    return list(serial.tools.list_ports.comports())


def get_port_hwid(port_info: serial.tools.list_ports_common.ListPortInfo) -> str:
    """Get hardware identifier for a port."""
    return port_info.hwid or port_info.device


def wait_for_port_connection(config: Config) -> serial.tools.list_ports_common.ListPortInfo:
    """Wait for serial port to be connected.
    
    Args:
        config: Configuration manager
        
    Returns:
        Selected port info
    """
    last_port = config.get_last_port()
    last_hwid = config.get_port_hwid(last_port) if last_port else None
    
    console.print("[cyan]Waiting for serial port connection...[/cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning for serial ports...", total=None)
        
        previous_ports = set()
        
        while not exit_requested:
            ports = get_available_ports()
            current_ports = {p.device for p in ports}
            
            if not ports:
                time.sleep(0.5)
                continue
            
            # Check if last used port (by hwid) is available
            if last_hwid:
                for port in ports:
                    if get_port_hwid(port) == last_hwid:
                        console.print(f"[green]✓ Found previous device: {port.device}[/green]")
                        config.set_last_port(port.device)
                        return port
            
            # Check for newly connected ports
            new_ports = current_ports - previous_ports
            
            if new_ports:
                # Get full port info for new ports
                new_port_infos = [p for p in ports if p.device in new_ports]
                
                if len(new_port_infos) == 1:
                    # Auto-connect to single new port
                    port = new_port_infos[0]
                    console.print(f"[green]✓ Auto-connecting to: {port.device}[/green]")
                    return port
                elif len(new_port_infos) > 1:
                    # Multiple ports connected simultaneously
                    console.print("\n[yellow]Multiple ports connected:[/yellow]")
                    for i, port in enumerate(new_port_infos, 1):
                        desc = port.description or "Unknown"
                        console.print(f"  {i}. {port.device} - {desc}")
                    
                    choice = Prompt.ask(
                        "Select port",
                        choices=[str(i) for i in range(1, len(new_port_infos) + 1)],
                        default="1"
                    )
                    return new_port_infos[int(choice) - 1]
            
            previous_ports = current_ports
            time.sleep(0.5)
    
    sys.exit(0)


def select_serial_port(config: Config) -> serial.tools.list_ports_common.ListPortInfo:
    """Select serial port, using last port as default or waiting for connection.
    
    Args:
        config: Configuration manager
        
    Returns:
        Selected port info
    """
    ports = get_available_ports()
    
    if not ports:
        return wait_for_port_connection(config)
    
    # Try to find last used port by hardware ID
    last_port = config.get_last_port()
    last_hwid = config.get_port_hwid(last_port) if last_port else None
    
    default_port = None
    if last_hwid:
        for port in ports:
            if get_port_hwid(port) == last_hwid:
                default_port = port
                break
    
    # If no match by hwid, try by name
    if not default_port and last_port:
        for port in ports:
            if port.device == last_port:
                default_port = port
                break
    
    # Single port available
    if len(ports) == 1:
        port = ports[0]
        if default_port and default_port.device == port.device:
            console.print(f"[green]Using port: {port.device}[/green]")
            return port
        else:
            use_it = Confirm.ask(f"Use port {port.device}?", default=True)
            if use_it:
                return port
            else:
                return wait_for_port_connection(config)
    
    # Multiple ports available
    console.print("\n[cyan]Available serial ports:[/cyan]")
    for i, port in enumerate(ports, 1):
        desc = port.description or "Unknown"
        default_marker = " [green](last used)[/green]" if default_port and port.device == default_port.device else ""
        console.print(f"  {i}. {port.device} - {desc}{default_marker}")
    
    default_choice = "1"
    if default_port:
        default_choice = str(next(i for i, p in enumerate(ports, 1) if p.device == default_port.device))
    
    choice = Prompt.ask(
        "Select port",
        choices=[str(i) for i in range(1, len(ports) + 1)],
        default=default_choice
    )
    
    return ports[int(choice) - 1]


def test_device_at_address(ser: serial.Serial, address: int, timeout: float = 0.1) -> bool:
    """Test if USS device responds at given address.
    
    Args:
        ser: Serial port connection
        address: Device address to test
        timeout: Response timeout in seconds
        
    Returns:
        True if device responds, False otherwise
    """
    try:
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send ping telegram
        telegram = USSProtocol.create_ping_telegram(address)
        ser.write(telegram)
        
        # Wait for response
        start_time = time.time()
        response = bytearray()
        
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                response.extend(ser.read(ser.in_waiting))
                
                # Try to parse response
                parsed = USSProtocol.parse_telegram(bytes(response))
                if parsed and parsed.get('valid') and parsed.get('address') == address:
                    return True
            
            time.sleep(0.001)
        
        return False
    
    except (serial.SerialException, OSError):
        return False


def detect_devices_at_baudrate(
    port_name: str,
    baudrate: int,
    force_all: bool = False,
    addresses: Optional[List[int]] = None
) -> List[int]:
    """Detect USS devices at specific baudrate.
    
    Args:
        port_name: Serial port name
        baudrate: Baudrate to test
        force_all: If True, test all addresses even if device found
        addresses: List of specific addresses to test (None = test all)
        
    Returns:
        List of detected device addresses
    """
    found_addresses = []
    
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1
        )
        
        # Use specified addresses or all addresses
        if addresses is None:
            addresses_to_test = list(range(USSProtocol.MIN_ADDRESS, USSProtocol.MAX_ADDRESS + 1))
        else:
            addresses_to_test = addresses
        
        total_addresses = len(addresses_to_test)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Testing {baudrate:>6} baud",
                total=total_addresses
            )
            
            for address in addresses_to_test:
                if exit_requested:
                    break
                
                if test_device_at_address(ser, address):
                    found_addresses.append(address)
                    progress.update(task, description=f"[green]Testing {baudrate:>6} baud - Found device at address {address}")
                    
                    if not force_all:
                        # If found a device and not forcing all, we found the baudrate
                        progress.update(task, completed=total_addresses)
                        break
                
                progress.advance(task)
        
        ser.close()
    
    except (serial.SerialException, OSError) as e:
        console.print(f"[red]Error testing baudrate {baudrate}: {e}[/red]")
    
    return found_addresses


def detect_all_devices(port_name: str, force_all: bool = False, addresses: Optional[List[int]] = None) -> Tuple[int, List[int]]:
    """Detect all USS devices and determine bus baudrate.
    
    Args:
        port_name: Serial port name
        force_all: If True, test all baudrate/address combinations
        addresses: List of specific addresses to test (None = test all)
        
    Returns:
        Tuple of (baudrate, list of device addresses)
    """
    console.print("\n[cyan]Starting USS device detection...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop at any time[/dim]\n")
    
    if force_all:
        console.print("[yellow]Force mode: Testing all baudrate/address combinations[/yellow]\n")
    
    if addresses:
        console.print(f"[cyan]Testing specific addresses: {', '.join(map(str, addresses))}[/cyan]\n")
    
    all_results = {}
    
    for baudrate in USSProtocol.BAUDRATES:
        if exit_requested:
            break
        
        found = detect_devices_at_baudrate(port_name, baudrate, force_all, addresses)
        
        if found:
            all_results[baudrate] = found
            
            if not force_all:
                # Found devices at this baudrate, no need to test others
                return baudrate, found
    
    # In force mode, return the baudrate with most devices found
    if all_results:
        best_baudrate = max(all_results.keys(), key=lambda k: len(all_results[k]))
        return best_baudrate, all_results[best_baudrate]
    
    return None, []


def main():
    """Main application entry point."""
    global exit_requested
    
    parser = argparse.ArgumentParser(
        description="Detect Siemens USS devices on serial bus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uss-detect                    # Normal detection (stop after finding devices)
  uss-detect --force-all        # Test all baudrate/address combinations
  uss-detect --id 0             # Scan only address 0
  uss-detect --id 0-10          # Scan addresses 0 through 10
  uss-detect --id 0,2,5         # Scan addresses 0, 2, and 5

Author: Oleksandr Kolodkin <oleksandr.kolodkin@ukr.net>
GitHub: https://github.com/kolod
        """
    )
    
    parser.add_argument(
        '--force-all',
        action='store_true',
        help='Force testing all baudrate/address combinations (for devices with incorrect baudrate)'
    )
    
    parser.add_argument(
        '--id',
        type=str,
        metavar='ADDRESSES',
        help='Specify address(es) to scan. Format: single (0), range (0-10), or comma-separated (0,2,3)'
    )
    
    args = parser.parse_args()
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Display header
    console.print("\n[bold cyan]USS Device Detector[/bold cyan]")
    console.print("[dim]Siemens USS Protocol Device Scanner[/dim]\n")
    
    # Load configuration
    config = Config()
    
    # Select serial port
    port_info = select_serial_port(config)
    port_name = port_info.device
    port_hwid = get_port_hwid(port_info)
    
    # Save port configuration
    config.set_last_port(port_name)
    config.set_port_hwid(port_name, port_hwid)
    
    console.print(f"\n[green]Connected to: {port_name}[/green]")
    if port_info.description:
        console.print(f"[dim]{port_info.description}[/dim]\n")
    
    # Parse address range if specified
    addresses = None
    if args.id:
        try:
            addresses = parse_address_range(args.id)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    # Detect devices
    baudrate, devices = detect_all_devices(port_name, args.force_all, addresses)
    
    # Display results
    console.print("\n" + "=" * 50)
    if devices:
        console.print(f"[bold green]Detection Complete![/bold green]\n")
        console.print(f"[cyan]Bus Settings:[/cyan]")
        console.print(f"  Baudrate: [bold]{baudrate}[/bold] baud")
        console.print(f"  Parity: [bold]Even[/bold]")
        console.print(f"  Data bits: [bold]8[/bold]")
        console.print(f"  Stop bits: [bold]1[/bold]\n")
        
        console.print(f"[cyan]Found Devices:[/cyan]")
        for addr in sorted(devices):
            console.print(f"  • Address: [bold]{addr}[/bold]")
    else:
        console.print("[yellow]No USS devices detected[/yellow]")
        console.print("\n[dim]Possible reasons:[/dim]")
        console.print("[dim]  • No devices connected[/dim]")
        console.print("[dim]  • Wrong serial port[/dim]")
        console.print("[dim]  • Devices not powered[/dim]")
        console.print("[dim]  • Non-standard baudrate (try --force-all)[/dim]")
    
    console.print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
