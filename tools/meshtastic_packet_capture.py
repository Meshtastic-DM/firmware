#!/usr/bin/env python3
"""
Meshtastic Packet Capture Tool for Wireshark Analysis
Captures packets from Heltec LoRa V3 device via serial and exports to Wireshark

Usage:
    python meshtastic_packet_capture.py --port COM3 --output capture.pcap
    python meshtastic_packet_capture.py --port COM3 --live
"""

import serial
import struct
import time
import argparse
import sys
from datetime import datetime
from collections import deque

try:
    import meshtastic
    import meshtastic.serial_interface
    from meshtastic import mesh_pb2, portnums_pb2
except ImportError:
    print("Error: meshtastic library not installed")
    print("Install with: pip install meshtastic")
    sys.exit(1)

class MeshtasticPacketCapture:
    """Captures Meshtastic packets and exports to PCAP format"""
    
    # PCAP Global Header
    PCAP_GLOBAL_HEADER = struct.pack(
        'IHHiIII',
        0xa1b2c3d4,  # Magic number
        2,           # Major version
        4,           # Minor version
        0,           # Timezone offset
        0,           # Timestamp accuracy
        65535,       # Max packet length
        147          # Data link type (USER0 - user defined)
    )
    
    def __init__(self, port, baudrate=115200, output_file=None, verbose=True):
        """
        Initialize packet capture
        
        Args:
            port: Serial port name (e.g., 'COM3' or '/dev/ttyUSB0')
            baudrate: Serial port baud rate
            output_file: Output PCAP file path (None for live capture only)
            verbose: Enable verbose logging
        """
        self.port = port
        self.baudrate = baudrate
        self.output_file = output_file
        self.verbose = verbose
        self.interface = None
        self.pcap_file = None
        self.packet_count = 0
        self.packets_buffer = deque(maxlen=1000)
        
    def log(self, message, level="INFO"):
        """Log message if verbose mode enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] [{level}] {message}")
    
    def write_pcap_header(self):
        """Write PCAP file header"""
        if self.pcap_file:
            self.pcap_file.write(self.PCAP_GLOBAL_HEADER)
            self.pcap_file.flush()
            self.log("PCAP header written")
    
    def write_pcap_packet(self, packet_data, timestamp=None):
        """
        Write packet to PCAP file
        
        Args:
            packet_data: Raw packet bytes
            timestamp: Packet timestamp (uses current time if None)
        """
        if not self.pcap_file:
            return
        
        if timestamp is None:
            timestamp = time.time()
        
        ts_sec = int(timestamp)
        ts_usec = int((timestamp - ts_sec) * 1000000)
        
        packet_len = len(packet_data)
        
        # PCAP packet header
        pcap_packet_header = struct.pack(
            'IIII',
            ts_sec,      # Timestamp seconds
            ts_usec,     # Timestamp microseconds
            packet_len,  # Captured length
            packet_len   # Original length
        )
        
        self.pcap_file.write(pcap_packet_header)
        self.pcap_file.write(packet_data)
        self.pcap_file.flush()
    
    def format_packet_info(self, packet):
        """Format packet information for display"""
        try:
            info = {
                'id': packet.get('id', 'N/A'),
                'from': hex(packet.get('from', 0)),
                'to': hex(packet.get('to', 0)),
                'hop_limit': packet.get('hopLimit', 0),
                'hop_start': packet.get('hopStart', 0),
                'want_ack': packet.get('wantAck', False),
                'rx_time': packet.get('rxTime', 0),
                'rx_snr': packet.get('rxSnr', 0),
                'rx_rssi': packet.get('rxRssi', 0),
                'channel': packet.get('channel', 0),
            }
            
            # Decode payload if available
            if 'decoded' in packet:
                decoded = packet['decoded']
                info['portnum'] = decoded.get('portnum', 'UNKNOWN')
                
                # Check for text message
                if 'text' in decoded.get('payload', {}):
                    info['message'] = decoded['payload']['text'][:50]  # First 50 chars
            
            return info
        except Exception as e:
            self.log(f"Error formatting packet: {e}", "ERROR")
            return {}
    
    def display_packet(self, packet, packet_num):
        """Display packet information in console"""
        info = self.format_packet_info(packet)
        
        print(f"\n{'='*80}")
        print(f"Packet #{packet_num} - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"{'='*80}")
        print(f"ID:         {info.get('id', 'N/A')}")
        print(f"From:       {info.get('from', 'N/A')}")
        print(f"To:         {info.get('to', 'N/A')}")
        print(f"Hops:       {info.get('hop_limit', 0)}/{info.get('hop_start', 0)}")
        print(f"Channel:    {info.get('channel', 0)}")
        print(f"Want ACK:   {info.get('want_ack', False)}")
        print(f"RX Time:    {info.get('rx_time', 0)}")
        print(f"SNR:        {info.get('rx_snr', 0)} dB")
        print(f"RSSI:       {info.get('rx_rssi', 0)} dBm")
        
        if 'portnum' in info:
            print(f"Port:       {info['portnum']}")
        
        if 'message' in info:
            print(f"Message:    {info['message']}")
        
        print(f"{'='*80}\n")
    
    def packet_callback(self, packet, interface):
        """Callback function for received packets"""
        try:
            self.packet_count += 1
            
            # Convert packet to bytes for PCAP
            if hasattr(packet, 'SerializeToString'):
                packet_bytes = packet.SerializeToString()
            else:
                # If it's a dict, try to serialize
                packet_bytes = str(packet).encode('utf-8')
            
            # Write to PCAP file
            self.write_pcap_packet(packet_bytes)
            
            # Store in buffer for analysis
            self.packets_buffer.append({
                'timestamp': time.time(),
                'packet': packet,
                'bytes': packet_bytes
            })
            
            # Display packet info
            if isinstance(packet, dict):
                self.display_packet(packet, self.packet_count)
            else:
                self.log(f"Packet #{self.packet_count}: {type(packet)}")
            
        except Exception as e:
            self.log(f"Error in packet callback: {e}", "ERROR")
    
    def start_capture(self):
        """Start capturing packets"""
        try:
            self.log(f"Connecting to Meshtastic device on {self.port}...")
            
            # Open PCAP file if specified
            if self.output_file:
                self.pcap_file = open(self.output_file, 'wb')
                self.write_pcap_header()
                self.log(f"Writing packets to {self.output_file}")
            
            # Connect to Meshtastic device
            self.interface = meshtastic.serial_interface.SerialInterface(
                devPath=self.port,
                debugOut=sys.stderr if self.verbose else None
            )
            
            self.log("Connected to Meshtastic device")
            self.log(f"Node: {self.interface.myInfo.my_node_num}")
            
            # Subscribe to packet events
            def on_receive(packet, interface):
                self.packet_callback(packet, interface)
            
            self.interface.onReceive = on_receive
            
            self.log("Packet capture started. Press Ctrl+C to stop.")
            self.log(f"{'='*80}\n")
            
            # Keep the script running
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.log("\nCapture stopped by user", "INFO")
            self.stop_capture()
        except Exception as e:
            self.log(f"Error during capture: {e}", "ERROR")
            self.stop_capture()
            raise
    
    def stop_capture(self):
        """Stop capturing and cleanup"""
        self.log(f"\nTotal packets captured: {self.packet_count}")
        
        if self.interface:
            try:
                self.interface.close()
                self.log("Meshtastic interface closed")
            except:
                pass
        
        if self.pcap_file:
            self.pcap_file.close()
            self.log(f"PCAP file closed: {self.output_file}")
    
    def print_statistics(self):
        """Print capture statistics"""
        if not self.packets_buffer:
            print("\nNo packets captured yet.")
            return
        
        print(f"\n{'='*80}")
        print(f"Capture Statistics")
        print(f"{'='*80}")
        print(f"Total Packets:     {self.packet_count}")
        print(f"Buffer Size:       {len(self.packets_buffer)}")
        
        if len(self.packets_buffer) > 1:
            time_range = self.packets_buffer[-1]['timestamp'] - self.packets_buffer[0]['timestamp']
            if time_range > 0:
                pps = len(self.packets_buffer) / time_range
                print(f"Packets/Second:    {pps:.2f}")
        
        print(f"{'='*80}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Meshtastic Packet Capture Tool for Wireshark',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture to PCAP file
  python meshtastic_packet_capture.py --port COM3 --output capture.pcap
  
  # Live capture (console only)
  python meshtastic_packet_capture.py --port COM3 --live
  
  # Capture with custom baud rate
  python meshtastic_packet_capture.py --port /dev/ttyUSB0 --baudrate 921600 --output mesh.pcap
        """
    )
    
    parser.add_argument(
        '--port',
        required=True,
        help='Serial port (e.g., COM3, /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '--baudrate',
        type=int,
        default=115200,
        help='Serial baud rate (default: 115200)'
    )
    
    parser.add_argument(
        '--output',
        help='Output PCAP file path'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Live capture mode (console only, no file output)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose logging'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.live and not args.output:
        parser.error("Either --output or --live must be specified")
    
    # Create capture instance
    capture = MeshtasticPacketCapture(
        port=args.port,
        baudrate=args.baudrate,
        output_file=args.output if not args.live else None,
        verbose=not args.quiet
    )
    
    try:
        capture.start_capture()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
