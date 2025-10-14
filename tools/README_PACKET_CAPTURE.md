# Meshtastic Packet Capture & Network Analysis Tools

Tools for capturing and analyzing Meshtastic mesh network traffic from Heltec LoRa V3 devices for Wireshark analysis.

## Features

- ✅ Real-time packet capture from serial interface
- ✅ PCAP export for Wireshark analysis
- ✅ Network flooding analysis
- ✅ Message propagation tracking
- ✅ Signal strength monitoring (RSSI/SNR)
- ✅ Node topology mapping
- ✅ Live statistics display

## Prerequisites

### 1. Install Python Dependencies

```bash
pip install meshtastic pyserial
```

### 2. Install Meshtastic CLI (Optional but recommended)

```bash
pip install --upgrade meshtastic
```

### 3. Connect Heltec LoRa V3 Device

Connect your Heltec LoRa V3 device to your PC via USB cable.

### 4. Find Serial Port

**Windows:**
```powershell
# Open Device Manager and look for COM ports
# Or use PowerShell:
Get-WmiObject Win32_SerialPort | Select-Object Name,DeviceID
```

**Linux:**
```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Or:
dmesg | grep tty
```

**macOS:**
```bash
ls /dev/cu.*
```

## Tool 1: Basic Packet Capture

### Usage

```bash
# Capture to PCAP file for Wireshark
python tools/meshtastic_packet_capture.py --port COM3 --output capture.pcap

# Live capture (console only)
python tools/meshtastic_packet_capture.py --port COM3 --live

# Linux example
python tools/meshtastic_packet_capture.py --port /dev/ttyUSB0 --output mesh_traffic.pcap

# Quiet mode (less verbose)
python tools/meshtastic_packet_capture.py --port COM3 --output capture.pcap --quiet
```

### Features
- Captures all Meshtastic packets
- Exports to PCAP format
- Real-time packet display
- Message content preview

## Tool 2: Advanced Network Analyzer

### Usage

```bash
# Full network analysis with PCAP export
python tools/meshtastic_network_analyzer.py --port COM3 --output network.pcap

# Custom statistics interval (every 60 seconds)
python tools/meshtastic_network_analyzer.py --port COM3 --output mesh.pcap --stats-interval 60

# Live monitoring without file output
python tools/meshtastic_network_analyzer.py --port COM3
```

### Features
- **Flooding Analysis**: Detects duplicate messages and flooding patterns
- **Network Statistics**: Node counts, packet rates, active nodes
- **Message Tracking**: Follows message propagation through the mesh
- **Signal Metrics**: RSSI and SNR monitoring
- **Topology Mapping**: Identifies network structure

### Example Output

```
====================================================================================================
Network Statistics - 2025-10-14 14:30:45
====================================================================================================
Uptime:              120.5 seconds
Total Nodes:         5
Active Nodes:        4
Total Packets:       234
Packets/Second:      1.94

Flooding Analysis:
Total Messages:      45
Flooded Messages:    12
Avg Duplicates:      2.3
Max Duplicates:      5

Active Nodes:
  0x1a2b3c4d     Packets: 89     Last seen: 2.3s ago [ACTIVE]
  0x5e6f7a8b     Packets: 67     Last seen: 5.1s ago [ACTIVE]
  0x9c8d7e6f     Packets: 42     Last seen: 1.8s ago [ACTIVE]
  0x4f3e2d1c     Packets: 36     Last seen: 12.4s ago [ACTIVE]

Top Flooded Messages:
  1. 0x1a2b3c4d_123456: 5 duplicates
  2. 0x5e6f7a8b_789012: 4 duplicates
  3. 0x9c8d7e6f_345678: 3 duplicates
====================================================================================================
```

## Wireshark Analysis

### 1. Open Captured PCAP File

```bash
wireshark capture.pcap
```

Or drag and drop the `.pcap` file into Wireshark.

### 2. Wireshark Display Filters

Since Meshtastic uses custom protocol, packets will appear as "User Defined" data. You can filter by:

```
# Filter by packet size
frame.len > 100

# Filter by time range
frame.time >= "2025-10-14 14:00:00" && frame.time <= "2025-10-14 15:00:00"

# Show only data packets (not empty)
data.len > 0
```

### 3. Live Capture with Wireshark

For real-time Wireshark monitoring:

**Option 1: Named Pipe (Linux/macOS)**
```bash
# Create named pipe
mkfifo /tmp/meshtastic_pipe

# Start Wireshark on the pipe
wireshark -k -i /tmp/meshtastic_pipe &

# Run capture to pipe
python tools/meshtastic_network_analyzer.py --port /dev/ttyUSB0 --output /tmp/meshtastic_pipe
```

**Option 2: Live File Monitoring**
```bash
# Start capture with auto-flush
python tools/meshtastic_network_analyzer.py --port COM3 --output live.pcap

# In Wireshark: File → Open → live.pcap
# Enable: View → Reload (Ctrl+R) or set auto-reload
```

## Analysis Use Cases

### 1. Flooding Behavior Analysis

Monitor how messages propagate through the mesh:
- Count duplicate packets per message
- Identify flooding hotspots
- Measure network efficiency

### 2. Signal Quality Monitoring

Track RSSI and SNR values:
- Identify weak links
- Optimize node placement
- Detect interference

### 3. Network Topology Mapping

Discover mesh structure:
- Active node identification
- Hop count analysis
- Message routing paths

### 4. Performance Metrics

Measure network performance:
- Packets per second
- Message delivery time
- Network utilization

## Troubleshooting

### Port Permission Issues (Linux)

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or run with sudo (not recommended)
sudo python tools/meshtastic_network_analyzer.py --port /dev/ttyUSB0 --output capture.pcap
```

### Device Not Found

```bash
# Check if device is detected
ls -l /dev/ttyUSB* /dev/ttyACM*

# Check dmesg for USB events
dmesg | tail -20
```

### Meshtastic Library Issues

```bash
# Reinstall meshtastic
pip uninstall meshtastic
pip install --upgrade meshtastic

# Check version
python -c "import meshtastic; print(meshtastic.__version__)"
```

### No Packets Captured

1. Verify device is connected and powered on
2. Check that Meshtastic firmware is running (LED should blink)
3. Ensure other nodes are active in the mesh
4. Try sending a test message from the Meshtastic app

## Advanced Usage

### Export Statistics to JSON

```bash
# Modify the script to export stats
python tools/meshtastic_network_analyzer.py --port COM3 --output capture.pcap > stats.log
```

### Filter Specific Message Types

Edit the `packet_handler` function to filter:
```python
def packet_handler(self, packet, interface):
    # Only capture TEXT_MESSAGE_APP packets
    if packet.get('decoded', {}).get('portnum') == 'TEXT_MESSAGE_APP':
        # Process packet
        pass
```

### Integrate with External Analysis Tools

The PCAP format is compatible with:
- Wireshark
- tcpdump
- tshark (CLI Wireshark)
- Custom Python analysis with scapy

## Example Analysis Workflow

1. **Start Capture**
   ```bash
   python tools/meshtastic_network_analyzer.py --port COM3 --output test1.pcap
   ```

2. **Send Test Messages**
   - Use Meshtastic mobile app to send messages
   - Observe packet capture in real-time

3. **Analyze Flooding**
   - Watch console for duplicate message statistics
   - Note "Flooded Messages" count

4. **Review in Wireshark**
   ```bash
   wireshark test1.pcap
   ```
   - Analyze packet timing
   - Identify patterns
   - Export statistics

5. **Generate Report**
   - Save console output
   - Export Wireshark statistics
   - Create flooding analysis report

## Files Created

- `meshtastic_packet_capture.py` - Basic packet capture tool
- `meshtastic_network_analyzer.py` - Advanced analysis with flooding detection
- `README_PACKET_CAPTURE.md` - This documentation

## License

Same as Meshtastic firmware (GPL v3)

## Support

For issues or questions:
1. Check Meshtastic documentation: https://meshtastic.org
2. Review tool logs for error messages
3. Verify serial connection and permissions
