#!/usr/bin/env python3
"""
Advanced Meshtastic Network Analyzer
Real-time packet analysis with Wireshark integration and network statistics

Features:
- Live packet capture to Wireshark
- Network topology mapping
- Flooding analysis
- Message flow tracking
- Signal strength monitoring
"""

import serial
import struct
import time
import json
import threading
from datetime import datetime
from collections import defaultdict, deque
import argparse
import sys

try:
    import meshtastic
    import meshtastic.serial_interface
    from meshtastic import mesh_pb2, portnums_pb2
except ImportError:
    print("Error: meshtastic library not installed")
    print("Install with: pip install meshtastic")
    sys.exit(1)


class NetworkAnalyzer:
    """Analyzes Meshtastic network behavior and flooding patterns"""
    
    def __init__(self):
        self.nodes = {}  # Node database
        self.packet_history = deque(maxlen=10000)
        self.message_paths = defaultdict(list)  # Track message propagation
        self.flooding_stats = defaultdict(int)
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def add_packet(self, packet_info):
        """Add packet to analysis database"""
        with self.lock:
            timestamp = time.time()
            
            # Extract packet details
            from_node = packet_info.get('from', 0)
            to_node = packet_info.get('to', 0)
            packet_id = packet_info.get('id', 0)
            hop_limit = packet_info.get('hopLimit', 0)
            hop_start = packet_info.get('hopStart', 0)
            
            # Track node information
            if from_node and from_node not in self.nodes:
                self.nodes[from_node] = {
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'packet_count': 0,
                    'messages_sent': 0,
                    'hops': []
                }
            
            if from_node:
                self.nodes[from_node]['last_seen'] = timestamp
                self.nodes[from_node]['packet_count'] += 1
            
            # Track message propagation (flooding analysis)
            if packet_id:
                path_key = f"{from_node}_{packet_id}"
                self.message_paths[path_key].append({
                    'timestamp': timestamp,
                    'hops_remaining': hop_limit,
                    'hops_total': hop_start,
                    'rssi': packet_info.get('rxRssi', 0),
                    'snr': packet_info.get('rxSnr', 0)
                })
                
                # Count flooding occurrences
                if len(self.message_paths[path_key]) > 1:
                    self.flooding_stats[path_key] += 1
            
            # Add to history
            self.packet_history.append({
                'timestamp': timestamp,
                'packet': packet_info
            })
    
    def get_flooding_analysis(self):
        """Analyze flooding behavior"""
        with self.lock:
            analysis = {
                'total_messages': len(self.message_paths),
                'flooded_messages': sum(1 for path in self.message_paths.values() if len(path) > 1),
                'avg_duplicates': 0,
                'max_duplicates': 0,
                'paths': []
            }
            
            duplicate_counts = [len(path) for path in self.message_paths.values()]
            if duplicate_counts:
                analysis['avg_duplicates'] = sum(duplicate_counts) / len(duplicate_counts)
                analysis['max_duplicates'] = max(duplicate_counts)
            
            # Get top flooded messages
            for path_key, path_data in sorted(
                self.message_paths.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:10]:
                analysis['paths'].append({
                    'message': path_key,
                    'duplicate_count': len(path_data),
                    'path_data': path_data
                })
            
            return analysis
    
    def get_network_stats(self):
        """Get network statistics"""
        with self.lock:
            uptime = time.time() - self.start_time
            
            stats = {
                'uptime': uptime,
                'total_nodes': len(self.nodes),
                'total_packets': len(self.packet_history),
                'packets_per_second': len(self.packet_history) / uptime if uptime > 0 else 0,
                'active_nodes': sum(1 for node in self.nodes.values() 
                                   if time.time() - node['last_seen'] < 300),
                'nodes': []
            }
            
            for node_id, node_data in self.nodes.items():
                stats['nodes'].append({
                    'id': hex(node_id),
                    'packet_count': node_data['packet_count'],
                    'last_seen': time.time() - node_data['last_seen'],
                    'active': time.time() - node_data['last_seen'] < 300
                })
            
            return stats
    
    def print_stats(self):
        """Print network statistics to console"""
        stats = self.get_network_stats()
        flooding = self.get_flooding_analysis()
        
        print(f"\n{'='*100}")
        print(f"Network Statistics - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*100}")
        print(f"Uptime:              {stats['uptime']:.1f} seconds")
        print(f"Total Nodes:         {stats['total_nodes']}")
        print(f"Active Nodes:        {stats['active_nodes']}")
        print(f"Total Packets:       {stats['total_packets']}")
        print(f"Packets/Second:      {stats['packets_per_second']:.2f}")
        print(f"\nFlooding Analysis:")
        print(f"Total Messages:      {flooding['total_messages']}")
        print(f"Flooded Messages:    {flooding['flooded_messages']}")
        print(f"Avg Duplicates:      {flooding['avg_duplicates']:.2f}")
        print(f"Max Duplicates:      {flooding['max_duplicates']}")
        
        if stats['nodes']:
            print(f"\nActive Nodes:")
            for node in sorted(stats['nodes'], key=lambda x: x['packet_count'], reverse=True)[:10]:
                status = "ACTIVE" if node['active'] else "INACTIVE"
                print(f"  {node['id']:<15} Packets: {node['packet_count']:<6} Last seen: {node['last_seen']:.1f}s ago [{status}]")
        
        if flooding['paths']:
            print(f"\nTop Flooded Messages:")
            for i, path in enumerate(flooding['paths'][:5], 1):
                print(f"  {i}. {path['message']}: {path['duplicate_count']} duplicates")
        
        print(f"{'='*100}\n")


class WiresharkCapture:
    """Enhanced packet capture with Wireshark support"""
    
    PCAP_GLOBAL_HEADER = struct.pack(
        'IHHiIII',
        0xa1b2c3d4,  # Magic number
        2, 4,        # Version
        0, 0,        # Timezone
        65535,       # Snaplen
        147          # Data link type (USER0)
    )
    
    def __init__(self, port, output_file=None, stats_interval=30):
        self.port = port
        self.output_file = output_file
        self.stats_interval = stats_interval
        self.interface = None
        self.pcap_file = None
        self.analyzer = NetworkAnalyzer()
        self.packet_count = 0
        self.running = False
        self.stats_thread = None
        
    def write_pcap_packet(self, packet_data, timestamp=None):
        """Write packet to PCAP file"""
        if not self.pcap_file:
            return
        
        if timestamp is None:
            timestamp = time.time()
        
        ts_sec = int(timestamp)
        ts_usec = int((timestamp - ts_sec) * 1000000)
        packet_len = len(packet_data)
        
        header = struct.pack('IIII', ts_sec, ts_usec, packet_len, packet_len)
        self.pcap_file.write(header + packet_data)
        self.pcap_file.flush()
    
    def packet_handler(self, packet, interface):
        """Handle received packets"""
        try:
            self.packet_count += 1
            timestamp = time.time()
            
            # Parse packet information
            packet_info = {}
            if isinstance(packet, dict):
                packet_info = packet
            
            # Add to analyzer
            self.analyzer.add_packet(packet_info)
            
            # Serialize for PCAP
            if hasattr(packet, 'SerializeToString'):
                packet_bytes = packet.SerializeToString()
            else:
                packet_bytes = json.dumps(packet_info).encode('utf-8')
            
            # Write to PCAP
            self.write_pcap_packet(packet_bytes, timestamp)
            
            # Display packet
            self.display_packet(packet_info, self.packet_count)
            
        except Exception as e:
            print(f"Error handling packet: {e}", file=sys.stderr)
    
    def display_packet(self, packet_info, packet_num):
        """Display packet information"""
        from_node = hex(packet_info.get('from', 0))
        to_node = hex(packet_info.get('to', 0))
        hop_limit = packet_info.get('hopLimit', 0)
        hop_start = packet_info.get('hopStart', 0)
        channel = packet_info.get('channel', 0)
        rssi = packet_info.get('rxRssi', 0)
        snr = packet_info.get('rxSnr', 0)
        
        hops_used = hop_start - hop_limit if hop_start > 0 else 0
        
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
              f"Pkt#{packet_num:<5} {from_node} → {to_node} | "
              f"Hops:{hops_used}/{hop_start} | Ch:{channel} | "
              f"RSSI:{rssi:>4}dBm SNR:{snr:>4}dB", end='')
        
        if 'decoded' in packet_info:
            decoded = packet_info['decoded']
            portnum = decoded.get('portnum', 'UNKNOWN')
            print(f" | Port:{portnum}", end='')
            
            if portnum == 'TEXT_MESSAGE_APP' and 'text' in decoded.get('payload', {}):
                msg = decoded['payload']['text'][:30]
                print(f" | Msg:\"{msg}\"", end='')
        
        print()  # New line
    
    def stats_worker(self):
        """Background thread for periodic statistics"""
        while self.running:
            time.sleep(self.stats_interval)
            if self.running:
                self.analyzer.print_stats()
    
    def start(self):
        """Start packet capture"""
        try:
            print(f"Connecting to Meshtastic device on {self.port}...")
            
            # Open PCAP file
            if self.output_file:
                self.pcap_file = open(self.output_file, 'wb')
                self.pcap_file.write(self.PCAP_GLOBAL_HEADER)
                print(f"Writing packets to: {self.output_file}")
            
            # Connect to device
            self.interface = meshtastic.serial_interface.SerialInterface(
                devPath=self.port
            )
            
            print(f"Connected! Node: {hex(self.interface.myInfo.my_node_num)}")
            print(f"Firmware: {self.interface.myInfo.firmware_version}")
            print(f"{'='*100}")
            
            # Set packet handler
            self.interface.onReceive = self.packet_handler
            
            # Start stats thread
            self.running = True
            self.stats_thread = threading.Thread(target=self.stats_worker, daemon=True)
            self.stats_thread.start()
            
            print("Capture started. Press Ctrl+C to stop.\n")
            
            # Keep running
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nStopping capture...")
            self.stop()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            self.stop()
            raise
    
    def stop(self):
        """Stop capture and cleanup"""
        self.running = False
        
        if self.stats_thread:
            self.stats_thread.join(timeout=2)
        
        print(f"\nFinal Statistics:")
        self.analyzer.print_stats()
        
        print(f"\nTotal packets captured: {self.packet_count}")
        
        if self.interface:
            try:
                self.interface.close()
            except:
                pass
        
        if self.pcap_file:
            self.pcap_file.close()
            print(f"PCAP file saved: {self.output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Meshtastic Network Analyzer with Wireshark Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--port', required=True, help='Serial port (COM3, /dev/ttyUSB0)')
    parser.add_argument('--output', help='Output PCAP file for Wireshark')
    parser.add_argument('--stats-interval', type=int, default=30, 
                       help='Statistics display interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    capture = WiresharkCapture(
        port=args.port,
        output_file=args.output,
        stats_interval=args.stats_interval
    )
    
    capture.start()


if __name__ == "__main__":
    main()
