# Meshtastic Firmware Block Diagram - Heltec LoRa V3

## Complete System Architecture: Power-On to Message Send/Receive

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POWER-ON SEQUENCE                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │   ESP32-S3 Bootloader     │
                    │   - Hardware Init         │
                    │   - Clock Configuration   │
                    └───────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    src/main.cpp :: setup() - Line 292                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ Hardware GPIO Init    │       │  Power Management     │
        │ - PIN_POWER_EN        │       │  - Power class        │
        │ - LED_POWER           │       │  - Battery Monitor    │
        │ - USER_LED            │       │  - PMU (AXP2101)      │
        └───────────────────────┘       └───────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │   SPI Initialization  │
                        │   - LORA_SCK          │
                        │   - LORA_MISO         │
                        │   - LORA_MOSI         │
                        │   - LORA_CS           │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   I2C Initialization  │
                        │   - Wire.begin()      │
                        │   - I2C Scanner       │
                        │   - Display Detect    │
                        └───────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NodeDB Creation (Line 720)                                │
│                    nodeDB = new NodeDB                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │  src/mesh/NodeDB.cpp :: NodeDB Constructor        │
        │  - Calls loadFromDisk()                           │
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │  LittleFS File System Access                      │
        │  ┌─────────────────────────────────────────┐      │
        │  │ /prefs/config.proto                     │      │
        │  │  - myRegion (EU_868, US, etc.)          │      │
        │  │  - lora.region                          │      │
        │  │  - lora.modem_preset                    │      │
        │  │  - device.role                          │      │
        │  └─────────────────────────────────────────┘      │
        │  ┌─────────────────────────────────────────┐      │
        │  │ /prefs/channels.proto                   │      │
        │  │  - Channel settings                     │      │
        │  │  - PSK encryption keys                  │      │
        │  └─────────────────────────────────────────┘      │
        │  ┌─────────────────────────────────────────┐      │
        │  │ /prefs/module.proto                     │      │
        │  │  - GPS, Telemetry, Range Test modules   │      │
        │  └─────────────────────────────────────────┘      │
        │  ┌─────────────────────────────────────────┐      │
        │  │ /prefs/nodes.proto                      │      │
        │  │  - Known nodes database                 │      │
        │  └─────────────────────────────────────────┘      │
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │  src/mesh/RadioInterface.cpp :: initRegion()      │
        │  - Sets myRegion pointer based on config          │
        │  - Loads duty cycle limits (EU: 10%, US: 100%)    │
        │  - Configures frequency band                      │
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Router Selection (Line 730-738)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ Role = REPEATER?      │       │ Role = ROUTER/CLIENT? │
        │ router =              │       │ router =              │
        │   new NextHopRouter() │       │   new ReliableRouter()│
        └───────────────────────┘       └───────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │ Display Initialization│
                        │ - SSD1306 OLED        │
                        │ - 128x64 resolution   │
                        │ - I2C Address 0x3C    │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ LoRa Radio Init       │
                        │ - SX1262 Chip         │
                        │ - Frequency Setup     │
                        │ - DIO1 Interrupt      │
                        │ - Bandwidth/SF Config │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Module Initialization │
                        │ - GPS Module          │
                        │ - Telemetry Module    │
                        │ - Position Module     │
                        │ - Text Message Module │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Service Initialization│
                        │ - MeshService         │
                        │ - AdminService        │
                        │ - NodeInfoService     │
                        └───────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              MAIN EVENT LOOP: src/main.cpp :: loop() - Line 1511            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │   service->loop()     │       │ mainController.       │
        │   - Process messages  │       │   runOrDelay()        │
        │   - Handle radio RX   │       │ - Display updates     │
        │   - Transmit queue    │       │ - Button handling     │
        └───────────────────────┘       │ - Sleep management    │
                    │                   └───────────────────────┘
                    │
                    └──────────────┬────────────────────────────────────┐
                                   │                                    │
                                   ▼                                    ▼


┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE SEND FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    User Input                                    Application Layer
        │                                               │
        ▼                                               ▼
┌─────────────────┐                         ┌─────────────────────┐
│ Button Press /  │                         │ Module Message      │
│ Serial Command /│                         │ (GPS, Telemetry)    │
│ BLE Command     │                         │ Auto-generated      │
└─────────────────┘                         └─────────────────────┘
        │                                               │
        └───────────────────┬───────────────────────────┘
                            ▼
                ┌───────────────────────────┐
                │ src/mesh/MeshService.cpp  │
                │ - sendText() / sendData() │
                │ - Create MeshPacket       │
                │ - Set destination         │
                │ - Encrypt if needed       │
                └───────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │ src/mesh/Router.cpp       │
                │ send(MeshPacket *p)       │
                └───────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────────────────┐
                │ Duty Cycle Check (Line 224)           │
                │ - src/airtime.cpp                     │
                │ - Check if airTime < dutyCycleLimit   │
                │ - EU_868: 10%, US: 100%               │
                └───────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │ Duty Cycle   │        │ Duty Cycle   │
        │ EXCEEDED     │        │ OK           │
        │ Drop Packet  │        │ Continue     │
        └──────────────┘        └──────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Router Routing Decision   │
                            │ - FloodingRouter: Rebroadcast│
                            │ - NextHopRouter: Find route  │
                            │ - ReliableRouter: ACK       │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Add to TX Queue           │
                            │ - Priority sorting        │
                            │ - Hop limit check         │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ src/mesh/RadioInterface.cpp│
                            │ startTransmit()           │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Channel Activity Check    │
                            │ - CAD (Channel Activity   │
                            │   Detection)              │
                            │ - Wait if busy            │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ SX1262 LoRa Chip          │
                            │ - Modulate packet         │
                            │ - Transmit on frequency   │
                            │ - Record airtime          │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ TX Complete Interrupt     │
                            │ - Update airtime usage    │
                            │ - Return to RX mode       │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Wait for ACK (if needed)  │
                            │ - ReliableRouter only     │
                            │ - Timeout & Retry         │
                            └───────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         MESSAGE RECEIVE FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┐
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ SX1262 LoRa Chip          │
                            │ - Continuous RX Mode      │
                            │ - Demodulate signal       │
                            │ - DIO1 Interrupt fires    │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ arch/esp32/               │
                            │ ESP32 ISR Handler         │
                            │ - DIO1 Pin Interrupt      │
                            │ - Set flag for processing │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ src/mesh/RadioInterface.cpp│
                            │ handleReceiveInterrupt()  │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Read packet from SX1262   │
                            │ - Get RSSI, SNR           │
                            │ - Extract payload         │
                            │ - CRC validation          │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ Decode MeshPacket         │
                            │ - Protocol Buffer decode  │
                            │ - Extract header fields   │
                            └───────────────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────┐
                            │ src/mesh/Router.cpp       │
                            │ handleReceived()          │
                            └───────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐             ┌───────────────────────┐
        │ Check Duplicate       │             │ Check Hop Count       │
        │ - Recently seen IDs   │             │ - hop_limit > 0?      │
        │ - Drop if duplicate   │             │ - Drop if exceeded    │
        └───────────────────────┘             └───────────────────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                            ┌───────────────────────────┐
                            │ Decrypt (if encrypted)    │
                            │ - Channel PSK key         │
                            │ - AES-256 CTR mode        │
                            └───────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐             ┌───────────────────────┐
        │ For Me?               │             │ For Others?           │
        │ - Destination = myID  │             │ - Route/Rebroadcast   │
        │ - Process locally     │             │ - Flooding: resend    │
        └───────────────────────┘             │ - NextHop: forward    │
                    │                         └───────────────────────┘
                    ▼                                       │
        ┌───────────────────────┐                          │
        │ Update Node Database  │                          │
        │ - SNR, RSSI, position │                          │
        │ - Last heard time     │                          │
        └───────────────────────┘                          │
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐             ┌───────────────────────┐
        │ Route to Module       │             │ Rebroadcast Decision  │
        │ - Text Message        │             │ - Check hop limit     │
        │ - Position Update     │             │ - Check duty cycle    │
        │ - Telemetry Data      │             │ - Add to TX queue     │
        │ - Admin Command       │             └───────────────────────┘
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Display on Screen     │
        │ - Show message        │
        │ - Update node list    │
        │ - Show SNR/RSSI       │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Send to Serial/BLE    │
        │ - Forward to app      │
        │ - JSON format         │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Send ACK (if needed)  │
        │ - ReliableRouter      │
        │ - ACK packet back     │
        └───────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         HARDWARE LAYER DETAILS                               │
└─────────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────┐
        │         ESP32-S3 Microcontroller                │
        │  ┌──────────────────────────────────────┐       │
        │  │ CPU: Dual-core Xtensa LX7 @ 240MHz   │       │
        │  │ RAM: 512KB SRAM                      │       │
        │  │ Flash: 8MB (partition-table.csv)     │       │
        │  │   - Firmware partition               │       │
        │  │   - LittleFS partition (/prefs)      │       │
        │  │   - OTA partition                    │       │
        │  └──────────────────────────────────────┘       │
        │                                                  │
        │  ┌──────────────────────────────────────┐       │
        │  │ SPI Bus (VSPI)                       │       │
        │  │  - SCK:  GPIO9                       │       │
        │  │  - MISO: GPIO11                      │       │
        │  │  - MOSI: GPIO10                      │       │
        │  │  - CS:   GPIO8                       │       │
        │  └──────────────────────────────────────┘       │
        │                      │                           │
        └──────────────────────┼───────────────────────────┘
                               ▼
                ┌──────────────────────────────┐
                │    SX1262 LoRa Transceiver   │
                │  ┌────────────────────────┐  │
                │  │ Frequency: 868/915MHz  │  │
                │  │ Bandwidth: 125-500kHz  │  │
                │  │ SF: 7-12               │  │
                │  │ TX Power: up to 22dBm  │  │
                │  │ Sensitivity: -148dBm   │  │
                │  └────────────────────────┘  │
                │                               │
                │  Pins:                        │
                │  - DIO1: GPIO14 (interrupt)   │
                │  - BUSY: GPIO13               │
                │  - RESET: GPIO12              │
                └───────────────────────────────┘

        ┌─────────────────────────────────────────┐
        │ I2C Bus (Wire)                          │
        │  - SDA: GPIO17                          │
        │  - SCL: GPIO18                          │
        └─────────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
    ┌───────────────────┐         ┌───────────────────┐
    │ SSD1306 OLED      │         │ AXP2101 PMU       │
    │ Display           │         │ (Power Mgmt)      │
    │ - 128x64 pixels   │         │ - Battery charge  │
    │ - I2C Addr: 0x3C  │         │ - Voltage monitor │
    └───────────────────┘         └───────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         KEY FILE STRUCTURE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

src/main.cpp                    → Main entry point, setup() & loop()
src/mesh/Router.cpp             → Routing logic, duty cycle enforcement
src/mesh/RadioInterface.cpp     → LoRa radio interface, region config
src/mesh/FloodingRouter.cpp     → Current flooding algorithm
src/mesh/ReliableRouter.cpp     → Reliable delivery with ACKs
src/mesh/NextHopRouter.cpp      → Next-hop routing (repeater mode)
src/mesh/NodeDB.cpp             → Configuration persistence
src/mesh/MeshService.cpp        → Message creation and handling
src/airtime.cpp                 → Duty cycle tracking
arch/esp32/esp32.cpp            → ESP32-specific code
variants/heltec_v3/variant.h    → Hardware pin definitions
protobufs/meshtastic/*.proto    → Message and config schemas


┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENT STORAGE STRUCTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

        ESP32 Flash Memory (8MB)
        ┌──────────────────────────────────┐
        │ Bootloader (64KB)                │
        ├──────────────────────────────────┤
        │ Partition Table                  │
        ├──────────────────────────────────┤
        │ Firmware Partition (1.5MB)       │
        │  - Meshtastic firmware binary    │
        ├──────────────────────────────────┤
        │ OTA Partition (1.5MB)            │
        │  - Firmware updates              │
        ├──────────────────────────────────┤
        │ LittleFS Partition (300KB)       │
        │  /prefs/                         │
        │   ├── config.proto               │
        │   │   └── myRegion, lora config  │
        │   ├── channels.proto             │
        │   │   └── Encryption keys        │
        │   ├── module.proto               │
        │   │   └── Module settings        │
        │   └── nodes.proto                │
        │       └── Known nodes DB         │
        ├──────────────────────────────────┤
        │ NVS (Non-Volatile Storage)       │
        │  - WiFi credentials              │
        │  - BLE pairing info              │
        └──────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIMING DIAGRAM                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Time (ms)    Event
─────────────────────────────────────────────────────────────────────────────
0            Power ON
5            ESP32-S3 bootloader starts
50           setup() begins
100          GPIO initialization complete
150          SPI bus initialized
200          I2C devices scanned
250          NodeDB created, loading from flash
300          Region configured (myRegion set)
350          Router created
400          Display initialized
450          LoRa radio initialized
500          Modules loaded
550          Services started
600          setup() complete
600+         loop() starts (runs forever)
             - Every loop: ~10ms
             - Radio RX check: continuous
             - Display update: 1Hz
             - Battery check: 60s

Message TX timing:
─────────────────
T+0ms:     User sends message
T+5ms:     MeshPacket created
T+10ms:    Duty cycle check
T+15ms:    Add to TX queue
T+20ms:    CAD (channel clear check)
T+50ms:    TX begins (depends on message size)
T+200ms:   TX complete (typical for small message)
T+205ms:   Return to RX mode

Message RX timing:
─────────────────
T+0ms:     Preamble detected
T+10ms:    Header received
T+50ms:    Payload received (depends on size)
T+55ms:    DIO1 interrupt fires
T+56ms:    ISR sets flag
T+57ms:    handleReceiveInterrupt() called
T+60ms:    Packet decoded
T+65ms:    Routing decision made
T+70ms:    Delivered to application / queued for rebroadcast
T+75ms:    Display updated (if for this node)
```

## Summary

This block diagram shows the complete architecture of Meshtastic firmware on Heltec LoRa V3:

1. **Power-On**: ESP32-S3 boots → setup() initializes hardware → loads config from flash
2. **Configuration**: NodeDB loads region settings (duty cycle limits), channel encryption keys
3. **Message Send**: User input → duty cycle check → routing decision → LoRa TX
4. **Message Receive**: LoRa RX interrupt → decode → routing → deliver to app/rebroadcast
5. **Continuous Loop**: service->loop() processes messages, updates display, manages power

**Key Components for Your FYP:**
- **Router.cpp**: Where duty cycle enforcement happens (line 224)
- **RadioInterface.cpp**: Region definitions and LoRa configuration
- **NodeDB.cpp**: Persistent storage of settings
- **FloodingRouter.cpp**: Current implementation to compare with your AODV

For AODV implementation, you'll add routing table logic between "Routing Decision" and "Add to TX Queue" blocks.
