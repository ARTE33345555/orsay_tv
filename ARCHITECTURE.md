# ORSAY TV Architecture

## System Overview

ORSAY TV is a custom firmware platform that transforms legacy Samsung Smart TV devices into programmable multimedia and IoT centers. The system leverages existing browser vulnerabilities for initial code execution, then bootstraps a complete runtime environment.

```
┌─────────────────────────────────────────┐
│       Samsung Orsay TV Hardware          │
│  (2010-2014 models, ARM Cortex-A9)     │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼────────┐
       │ Samsung Browser │ (Existing Vulnerability)
       └───────┬────────┘
               │
    ┌──────────▼──────────────┐
    │  install.html Entry     │ (Injected via browser)
    │  (HTML/JavaScript)      │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────────┐
    │  ORSAY TV Bootstrap         │
    │  (bootstrap.py)             │
    │  - Platform detection       │
    │  - Version check            │
    │  - Hardware validation      │
    │  - Recovery mode            │
    └──────────┬──────────────────┘
               │
    ┌──────────▼────────────────────────┐
    │  ORSAY TV Core Runtime             │
    │  - ServiceManager                  │
    │  - EventBus                        │
    │  - AppManager                      │
    └──────────┬────────────────────────┘
               │
    ┌──────────▼────────────────────────┐
    │  Python 3 Runtime                  │
    │  - Native (if available)           │
    │  - External via Local Network      │
    └──────────┬────────────────────────┘
               │
  ┌────────────┼────────────┬───────────┬──────────┐
  │            │            │           │          │
  ▼            ▼            ▼           ▼          ▼
┌────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌────┐
│IPTV│  │OliStore│  │IoT Daemon│  │Display │  │Apps│
│    │  │        │  │          │  │UI      │  │    │
└────┘  └────────┘  └──────────┘  └────────┘  └────┘
  │            │            │           │          │
  └────────────┼────────────┴───────────┴──────────┘
               │
       ┌───────▼────────┐
       │  Local Network │
       │  (LAN/Wi-Fi)   │
       └────────┬───────┘
                │
    ┌───────────┴──────────┬────────────┐
    │                      │            │
    ▼                      ▼            ▼
┌─────────┐         ┌──────────┐   ┌─────────┐
│Raspberry│         │ESP32/Ardu│   │  MQTT   │
│   Pi    │         │ino Devices│   │ Broker  │
└─────────┘         └──────────┘   └─────────┘
    (IoT Runtime)  (Sensors/Actuators)
```

## Directory Structure

```
orsay_tv/
├── bootstrap/                    # Bootstrap and initialization
│   ├── bootstrap.py             # Main bootstrap entry point
│   ├── platform_detector.py      # Hardware/platform detection
│   ├── recovery.py              # Recovery mode and safe mode
│   └── installer.py             # Component installation logic
│
├── core/                        # Core system components
│   ├── service_manager.py        # Service lifecycle management
│   ├── app_manager.py           # Application stack and lifecycle
│   ├── event_bus.py             # Event-driven architecture
│   └── hardware_profile.py       # Hardware abstraction layer
│
├── runtime/                     # Python runtime and execution
│   ├── python_runtime/          # Python 3 execution layer
│   │   ├── native/              # Native Python (if available)
│   │   └── external/            # External runtime via network
│   └── orsay_tv/                # ORSAY TV Python API modules
│       ├── __init__.py
│       ├── display.py           # Display/UI operations
│       ├── network.py           # Network utilities
│       ├── remote.py            # Remote control handling
│       ├── storage.py           # File storage operations
│       ├── media.py             # Media playback control
│       ├── apps.py              # App management API
│       ├── iot.py               # IoT device management
│       └── cast.py              # Cast operations
│
├── iot/                         # IoT framework
│   ├── device_manager.py         # Device discovery and management
│   ├── protocols/               # Communication protocols
│   │   ├── mqtt.py              # MQTT protocol support
│   │   ├── local_json.py         # Local JSON protocol
│   │   └── bridge.py            # Protocol bridging
│   └── telemetry.py             # Telemetry collection
│
├── store/                       # Application store (OliStore)
│   ├── store_manager.py         # App store logic
│   ├── manifest.py              # App manifest handling
│   ├── repository.py            # Local app repository
│   └── installer.py             # App installation/uninstall
│
├── apps/                        # Built-in applications
│   ├── hello/                   # Hello World demo app
│   │   ├── manifest.json
│   │   └── main.py
│   ├── settings/                # Settings application
│   ├── iptv/                    # IPTV application
│   ├── games/                   # Game center
│   ├── iot/                     # IoT control app
│   └── recovery/                # Recovery console app
│
├── ui/                          # User interface
│   ├── tv_renderer.py           # TV-optimized rendering
│   ├── d_pad_handler.py         # D-pad navigation
│   ├── remote_handler.py        # Remote control handling
│   └── themes/                  # UI themes
│
├── platform/                    # Hardware abstraction
│   ├── orsay/                   # Samsung Orsay specific
│   │   ├── native_api.py        # Orsay native API bindings
│   │   └── quirks.py            # Platform-specific quirks
│   ├── external_runtime/        # External runtime (Raspberry Pi, etc)
│   │   ├── client.py            # Client to external runtime
│   │   └── server.py            # External runtime server
│   └── simulator/               # PC simulator
│       ├── simulator.py         # Main simulator
│       └── mock_hardware.py      # Hardware mocking
│
├── tests/                       # Testing suite
│   ├── test_bootstrap.py
│   ├── test_installer.py
│   ├── test_app_manager.py
│   ├── test_iot_protocol.py
│   └── test_python_api.py
│
├── main.py                      # Main kernel entry point
├── backend.py                   # Installation backend server
├── install.html                 # Browser injection interface
├── bootstrap_entry.js           # JavaScript bootstrap stub
│
├── ARCHITECTURE.md              # This file
├── COMPATIBILITY.md             # Compatibility matrix
├── CREATE_APP.md                # App development guide
└── README.md                    # Main documentation
```

## Core Components

### 1. Bootstrap (bootstrap/)

**Purpose**: Initialize the ORSAY TV environment after browser injection.

**Key Responsibilities**:
- Detect TV model, Orsay version, CPU architecture
- Validate available memory and storage
- Check required APIs and system capabilities
- Create ORSAY TV directories and file structure
- Verify installation integrity
- Provide recovery and safe mode options
- Maintain installation logs

**Entry Point**: `bootstrap/bootstrap.py`

### 2. Core Kernel (core/)

**Components**:

#### ServiceManager
- Manages system services (SSH, IPTV, Casting, Samba)
- Provides lifecycle methods: `init()`, `loop()`, `shutdown()`
- Thread-safe service registration and execution

#### AppManager
- Manages application stack (foreground/background)
- Implements card-like UI with pause/resume/launch
- Event-driven app communication

#### EventBus
- Central event dispatcher
- Loosely coupled component communication
- Thread-safe event emission and subscription

#### HardwareProfile
- Detects and caches hardware information
- Provides platform abstraction
- Manages theme assets and resources

### 3. Python Runtime (runtime/)

**Strategy**:
1. **Preferred**: Run Python 3 native on the TV (if architecture compatible)
2. **Fallback**: External runtime via local network (Raspberry Pi, Linux PC)

**Architecture**:
```
ORSAY TV (Python API Consumer)
    │
    └─┬─ Native Runtime? ──YES──> Direct execution
      │
      └─ NO ──> Network Client ──> External Runtime
                                   (Raspberry Pi/PC)
```

### 4. ORSAY TV Python API (runtime/orsay_tv/)

Unified Python API across all runtime configurations:

```python
# Display operations
from orsay_tv import display
display.show("Hello World", x=100, y=100)
display.clear()

# Network operations
from orsay_tv import network
devices = network.scan_iot_devices()

# Remote control
from orsay_tv import remote
remote.on_keypress(lambda key: print(f"Key: {key}"))

# Storage operations
from orsay_tv import storage
storage.save("config", {"theme": "dark"})

# Media control
from orsay_tv import media
media.play_video("http://stream.mp4")

# App management
from orsay_tv import apps
apps.install("myapp", manifest)

# IoT device management
from orsay_tv import iot
iot.connect("living-room-lights")
iot.send("color", "red")

# Casting
from orsay_tv import cast
cast.enable_miracast()
```

### 5. IoT Framework (iot/)

**Architecture**:
```
ORSAY TV IoT Service
    │
    ├─ Device Discovery (mDNS/Manual)
    ├─ Device Manager (IDs, State, Properties)
    ├─ Protocol Handler (MQTT, Local JSON)
    ├─ Telemetry Collector
    └─ Command Router
         │
         └─ Local Network (LAN/Wi-Fi)
             │
             ├─ Raspberry Pi (Python runtime)
             ├─ ESP32 (Firmware)
             ├─ Arduino (Serial)
             └─ Other Smart Devices
```

**Supported Protocols**:
- **MQTT**: Industry standard for IoT
- **Local JSON**: Simple TCP-based protocol for custom devices
- **Protocol Bridging**: Convert between protocols

**Features**:
- Device discovery and auto-pairing
- Device state management
- Telemetry collection and logging
- Offline mode with local caching
- Reconnect with exponential backoff

### 6. OliStore (store/)

**Responsibilities**:
- Manage local app repository
- Parse and validate app manifests
- Handle app installation/uninstall
- Dependency resolution
- Version management
- Compatibility checking

**Manifest Format** (JSON):
```json
{
  "name": "Hello World",
  "version": "1.0.0",
  "description": "Simple hello world app",
  "runtime": "python",
  "entry": "main.py",
  "permissions": ["display", "network", "iot"],
  "dependencies": [],
  "min_version": "2.6"
}
```

### 7. Application System (apps/)

**App Structure**:
```
hello/
├── manifest.json    # App metadata
├── main.py         # Entry point
├── requirements.txt # Dependencies
└── resources/      # Assets
```

**App Lifecycle**:
```
Registry → Launch → Resume → Loop → Pause → (Stopped)
```

## Platform Abstraction

### Native (Orsay Platform)

Directly interact with Samsung Orsay APIs:
- Frame buffer rendering
- Remote control input
- Native libraries (libc, libm)
- TV-specific system calls

### External Runtime

Client-server architecture for external platforms:

**Client** (on TV):
- Connects to external runtime via network
- Marshals Python API calls
- Receives results and displays

**Server** (Raspberry Pi/PC):
- Full Python 3 environment
- Executes requested operations
- Returns results in JSON format

### Simulator

PC-based simulator for development:
- Mock hardware interfaces
- Headless or SDL display
- Network simulation
- Perfect for testing without real hardware

## Event Flow

```
Remote Control Input
    │
    ▼
RemoteHandler (tv/remote_handler.py)
    │
    ▼
EventBus.emit("remote_key", key_code)
    │
    ├─→ AppManager (foreground app gets event)
    ├─→ UILayer (navigation, menus)
    └─→ Services (IPTV, IoT, etc)
```

## Service Architecture

```
SystemManager
    ├─ HomeRadioAssistant (Voice commands, UI)
    ├─ SSHServerService (Remote access)
    ├─ CastToScreen (DLNA, AirPlay, Miracast)
    ├─ SambaShareService (File sharing)
    ├─ IPTVService (Stream playback)
    └─ IoTDaemon (Device management)
```

## Data Flow: App Installation

```
OliStore (UI)
    │
    ├─ parse manifest.json
    ├─ check dependencies
    ├─ verify compatibility
    │
    ▼
AppInstaller
    ├─ download/copy files
    ├─ verify checksums
    ├─ create isolated environment
    │
    ▼
AppRegistry
    │
    ├─ add to installed apps list
    ├─ create shortcuts
    │
    ▼
AppManager (can now launch)
```

## Data Flow: IoT Device Command

```
IoT Control App (UI)
    │
    ▼
IoTAPI.send("living-room-light", "power", "on")
    │
    ▼
IoTDeviceManager
    ├─ lookup device by ID
    ├─ check device capabilities
    │
    ▼
ProtocolHandler (MQTT/LocalJSON)
    │
    ▼
Network (LAN/Wi-Fi)
    │
    ▼
IoT Device (ESP32/Arduino/Pi)
    │
    ▼
Acknowledgment → IoTAPI (event: "device_updated")
```

## Configuration

**Main Config**: `/firmware/orsay.conf`
```ini
[platform]
version=2.6
model=Samsung_UN55ES6500
cpu_arch=armv7l

[network]
wifi_ssid=MyNetwork
mqtt_broker=192.168.1.100

[apps]
auto_launch=hello
theme=dark

[iot]
discovery=enabled
protocol=mqtt
```

## Recovery System

**Boot Modes**:
1. **Normal**: Full boot with all services
2. **Safe Mode**: Only core services, no user apps
3. **Recovery Console**: Interactive recovery shell
4. **Maintenance Mode**: Services available for debugging

**Recovery Menu**:
```
[1] Start normally
[2] Safe mode
[3] Repair installation
[4] Remove installed apps
[5] View logs
[6] Factory reset
```

## Error Handling & Fallbacks

- **Installation Failure**: Automatic rollback from backup
- **Service Crash**: Auto-restart with backoff
- **Network Unavailable**: IoT goes into offline mode
- **App Crash**: App is terminated, others continue
- **Runtime Error**: Logged, handled gracefully

## Threading Model

- **Main Thread**: UI loop (60 FPS target)
- **Service Threads**: Background services
- **Worker Threads**: I/O operations
- **Event Thread**: Event dispatcher (thread-safe)

## Security Considerations

1. **No Root Access Needed**: Runs in user context
2. **Sandboxed Apps**: Limited permissions model
3. **Local Network Only**: No cloud dependency
4. **SSL/TLS**: For any external communication
5. **Auth**: SSH key-based, no default passwords

## Performance Targets

- **Boot Time**: ~5-10 seconds
- **App Launch**: <1 second
- **UI Responsiveness**: 60 FPS
- **Memory Usage**: <150 MB (core)
- **Network Response**: <100ms (local)

## Limitations & Known Constraints

1. **RAM**: Limited to ~512MB (Orsay spec)
   - Mitigated: External runtime fallback
   
2. **Storage**: ~256MB eMMC
   - Mitigated: Compressed apps, external storage via network
   
3. **Network**: Early Wi-Fi adapters may be slow
   - Mitigated: Fallback to Ethernet via USB adapter
   
4. **No GPU**: Older models lack discrete GPU
   - Mitigated: Software rendering, efficient 2D only
   
5. **Closed Ecosystem**: Limited OS APIs
   - Mitigated: Hardware abstraction, system calls where available

## Future Extensions

- **3D Graphics**: Panda3D integration
- **Machine Learning**: TensorFlow Lite on external runtime
- **Voice Control**: Vosk integration for speech recognition
- **HomeAssistant**: Integration with HA ecosystem
- **Multi-Zone**: Synchronized content across multiple TVs

## See Also

- `COMPATIBILITY.md` - Supported devices and versions
- `CREATE_APP.md` - App development guide
- `README.md` - User guide and installation
