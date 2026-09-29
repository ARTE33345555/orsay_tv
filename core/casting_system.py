#!/usr/bin/env python3
"""
ORSAY TV Casting System
Support for Chromecast, AirPlay, DLNA and Wi-Fi Direct casting.
"""

import json
import socket
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).parent.parent
CAST_CONFIG = BASE_DIR / "firmware" / "etc" / "casting.conf"
CAST_LOGS = BASE_DIR / "firmware" / "var" / "logs"


# ============================================
# LOGGER
# ============================================
class CastingLogger:
    """Logger for casting system"""
    
    def __init__(self):
        CAST_LOGS.mkdir(parents=True, exist_ok=True)
        self.log_file = CAST_LOGS / f"casting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass
    
    def info(self, msg: str):
        self.log(msg, "INFO")
    
    def success(self, msg: str):
        self.log(msg, "SUCCESS")
    
    def warning(self, msg: str):
        self.log(msg, "WARNING")
    
    def error(self, msg: str):
        self.log(msg, "ERROR")
    
    def debug(self, msg: str):
        self.log(msg, "DEBUG")


logger = CastingLogger()


# ============================================
# CASTING PROTOCOLS
# ============================================
class CastProtocol(Enum):
    """Supported casting protocols"""
    CHROMECAST = "chromecast"      # Google Cast
    AIRPLAY = "airplay"             # Apple AirPlay 2
    DLNA = "dlna"                   # DLNA/UPnP
    WIFI_DIRECT = "wifi_direct"     # Wi-Fi Direct
    MIRACAST = "miracast"           # Miracast (WiFi Alliance)


class CastMode(Enum):
    """Casting modes"""
    SCREEN_MIRROR = "screen_mirror"     # Mirror entire screen
    VIDEO = "video"                     # Cast video file
    AUDIO = "audio"                     # Cast audio
    TAB = "tab"                         # Cast specific app (not on TV)


@dataclass
class CastDevice:
    """Discovered casting-capable device"""
    device_id: str
    name: str
    protocol: str
    ip_address: str
    port: int
    model: str
    capability: str  # "audio", "video", "screen"
    status: str  # "available", "busy", "offline"
    signal_strength: int  # -100 to 0 (dBm)


@dataclass
class CastSession:
    """Active casting session"""
    session_id: str
    device: CastDevice
    protocol: str
    mode: str
    status: str  # "connecting", "connected", "casting", "stopped"
    started: str
    source: Optional[str]  # URL or file path
    duration: int  # seconds
    position: int  # current position in seconds


# ============================================
# DEVICE DISCOVERY
# ============================================
class CastDeviceDiscovery:
    """Discover castable devices on network"""
    
    def __init__(self):
        self.devices: Dict[str, CastDevice] = {}
        self.discovery_thread: Optional[threading.Thread] = None
        self.is_scanning = False
    
    def start_discovery(self):
        """Start discovering devices"""
        logger.info("=== Starting Device Discovery ===")
        
        self.is_scanning = True
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            daemon=True
        )
        self.discovery_thread.start()
    
    def stop_discovery(self):
        """Stop device discovery"""
        self.is_scanning = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        logger.info("Device discovery stopped")
    
    def _discovery_loop(self):
        """Discovery loop - scan network for cast devices"""
        while self.is_scanning:
            try:
                self._scan_chromecast()
                self._scan_airplay()
                self._scan_dlna()
                self._scan_wifi_direct()
                self._scan_miracast()
                
                time.sleep(5)  # Rescan every 5 seconds
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                time.sleep(5)
    
    def _scan_chromecast(self):
        """Scan for Chromecast devices"""
        try:
            # In real implementation: mDNS query for _googlecast._tcp.local
            # For now: check common Chromecast IP ranges
            for i in range(2, 255):
                ip = f"192.168.1.{i}"
                try:
                    # Try to connect to port 8008 (Chromecast)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, 8008))
                    sock.close()
                    
                    if result == 0:
                        # Found a Chromecast
                        device = CastDevice(
                            device_id=f"chromecast_{ip}",
                            name=f"Chromecast ({ip})",
                            protocol=CastProtocol.CHROMECAST.value,
                            ip_address=ip,
                            port=8008,
                            model="Generic Chromecast",
                            capability="video",
                            status="available",
                            signal_strength=-30
                        )
                        self.devices[device.device_id] = device
                        logger.debug(f"Found Chromecast: {ip}")
                except:
                    pass
        except Exception as e:
            logger.debug(f"Chromecast scan error: {e}")
    
    def _scan_airplay(self):
        """Scan for AirPlay devices"""
        try:
            # AirPlay uses mDNS: _airplay._tcp.local
            # For now: check common Apple device patterns
            logger.debug("Scanning for AirPlay devices...")
            
            # Simulated discovery
            common_ips = ["192.168.1.100", "192.168.1.101"]
            for ip in common_ips:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, 7000))
                    sock.close()
                    
                    if result == 0:
                        device = CastDevice(
                            device_id=f"airplay_{ip}",
                            name=f"AirPlay Device ({ip})",
                            protocol=CastProtocol.AIRPLAY.value,
                            ip_address=ip,
                            port=7000,
                            model="Apple AirPlay 2",
                            capability="audio,video",
                            status="available",
                            signal_strength=-40
                        )
                        self.devices[device.device_id] = device
                        logger.debug(f"Found AirPlay: {ip}")
                except:
                    pass
        except Exception as e:
            logger.debug(f"AirPlay scan error: {e}")
    
    def _scan_dlna(self):
        """Scan for DLNA/UPnP devices"""
        try:
            # DLNA uses UPnP discovery on port 1900
            logger.debug("Scanning for DLNA devices...")
            
            # Send SSDP discovery request
            ssdp_request = (
                'M-SEARCH * HTTP/1.1\r\n'
                'HOST: 239.255.255.250:1900\r\n'
                'MAN: "ssdp:discover"\r\n'
                'MX: 2\r\n'
                'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n'
                'USER-AGENT: ORSAY-TV/1.0 UPnP/1.0\r\n'
                '\r\n'
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            try:
                sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
                
                while True:
                    try:
                        data, addr = sock.recvfrom(1024)
                        # Parse SSDP response
                        if b'MediaRenderer' in data:
                            device = CastDevice(
                                device_id=f"dlna_{addr[0]}",
                                name=f"DLNA Renderer ({addr[0]})",
                                protocol=CastProtocol.DLNA.value,
                                ip_address=addr[0],
                                port=8000,
                                model="DLNA Device",
                                capability="video",
                                status="available",
                                signal_strength=-50
                            )
                            self.devices[device.device_id] = device
                            logger.debug(f"Found DLNA: {addr[0]}")
                    except socket.timeout:
                        break
            finally:
                sock.close()
        except Exception as e:
            logger.debug(f"DLNA scan error: {e}")
    
    def _scan_wifi_direct(self):
        """Scan for Wi-Fi Direct devices"""
        try:
            if not self._has_wifi_direct_support():
                return
            
            logger.debug("Scanning for Wi-Fi Direct devices...")
            # Would use iw wlan0 p2p find
            # For now: simulated
        except Exception as e:
            logger.debug(f"Wi-Fi Direct scan error: {e}")
    
    def _scan_miracast(self):
        """Scan for Miracast devices"""
        try:
            logger.debug("Scanning for Miracast devices...")
            # Miracast uses Wi-Fi Direct
            # Would require p2p service discovery
        except Exception as e:
            logger.debug(f"Miracast scan error: {e}")
    
    def _has_wifi_direct_support(self) -> bool:
        """Check if system supports Wi-Fi Direct"""
        return Path("/sys/class/net/p2p0").exists()
    
    def get_devices(self) -> List[CastDevice]:
        """Get list of discovered devices"""
        return list(self.devices.values())
    
    def get_device_by_protocol(self, protocol: CastProtocol) -> List[CastDevice]:
        """Get devices supporting specific protocol"""
        return [d for d in self.devices.values() if d.protocol == protocol.value]


# ============================================
# CHROMECAST CONTROLLER
# ============================================
class ChromecastController:
    """Control Chromecast devices"""
    
    def __init__(self, device: CastDevice):
        self.device = device
        self.session: Optional[CastSession] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to Chromecast"""
        logger.info(f"Connecting to Chromecast: {self.device.name}")
        
        try:
            # Chromecast protocol: connect to port 8008
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device.ip_address, self.device.port))
            
            # Send initial handshake (would use protobuf in real impl)
            self.is_connected = True
            logger.success(f"Connected to {self.device.name}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def cast_video(self, video_url: str, title: str = "Video") -> bool:
        """Cast video to Chromecast"""
        if not self.is_connected:
            if not self.connect():
                return False
        
        logger.info(f"Casting video to {self.device.name}: {title}")
        
        try:
            # Create casting session
            self.session = CastSession(
                session_id=f"cast_{int(time.time())}",
                device=self.device,
                protocol=CastProtocol.CHROMECAST.value,
                mode=CastMode.VIDEO.value,
                status="casting",
                started=datetime.now().isoformat(),
                source=video_url,
                duration=0,
                position=0
            )
            
            # Send LOAD command (Chromecast protocol)
            # In real implementation: use pychromecast or similar
            
            logger.success(f"Casting started: {title}")
            return True
        except Exception as e:
            logger.error(f"Cast failed: {e}")
            return False
    
    def cast_screen(self) -> bool:
        """Mirror screen to Chromecast"""
        if not self.is_connected:
            if not self.connect():
                return False
        
        logger.info(f"Mirroring screen to {self.device.name}")
        
        try:
            self.session = CastSession(
                session_id=f"cast_{int(time.time())}",
                device=self.device,
                protocol=CastProtocol.CHROMECAST.value,
                mode=CastMode.SCREEN_MIRROR.value,
                status="casting",
                started=datetime.now().isoformat(),
                source=None,
                duration=0,
                position=0
            )
            
            logger.success("Screen mirroring started")
            return True
        except Exception as e:
            logger.error(f"Screen mirroring failed: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause casting"""
        if not self.session:
            return False
        
        self.session.status = "paused"
        logger.info("Casting paused")
        return True
    
    def resume(self) -> bool:
        """Resume casting"""
        if not self.session:
            return False
        
        self.session.status = "casting"
        logger.info("Casting resumed")
        return True
    
    def stop(self) -> bool:
        """Stop casting"""
        logger.info("Stopping casting")
        self.session = None
        return True


# ============================================
# AIRPLAY CONTROLLER
# ============================================
class AirPlayController:
    """Control AirPlay devices"""
    
    def __init__(self, device: CastDevice):
        self.device = device
        self.session: Optional[CastSession] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to AirPlay device"""
        logger.info(f"Connecting to AirPlay: {self.device.name}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device.ip_address, self.device.port))
            
            self.is_connected = True
            logger.success(f"Connected to {self.device.name}")
            return True
        except Exception as e:
            logger.error(f"AirPlay connection failed: {e}")
            return False
    
    def cast_video(self, video_url: str, title: str = "Video") -> bool:
        """Cast video via AirPlay"""
        if not self.is_connected:
            if not self.connect():
                return False
        
        logger.info(f"AirPlay casting: {title}")
        
        try:
            self.session = CastSession(
                session_id=f"airplay_{int(time.time())}",
                device=self.device,
                protocol=CastProtocol.AIRPLAY.value,
                mode=CastMode.VIDEO.value,
                status="casting",
                started=datetime.now().isoformat(),
                source=video_url,
                duration=0,
                position=0
            )
            
            # AirPlay protocol: RTSP for video
            logger.success(f"AirPlay casting: {title}")
            return True
        except Exception as e:
            logger.error(f"AirPlay cast failed: {e}")
            return False
    
    def cast_audio(self, audio_url: str, title: str = "Audio") -> bool:
        """Cast audio via AirPlay"""
        if not self.is_connected:
            if not self.connect():
                return False
        
        logger.info(f"AirPlay audio: {title}")
        
        try:
            self.session = CastSession(
                session_id=f"airplay_audio_{int(time.time())}",
                device=self.device,
                protocol=CastProtocol.AIRPLAY.value,
                mode=CastMode.AUDIO.value,
                status="casting",
                started=datetime.now().isoformat(),
                source=audio_url,
                duration=0,
                position=0
            )
            
            logger.success(f"AirPlay audio: {title}")
            return True
        except Exception as e:
            logger.error(f"AirPlay audio failed: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop AirPlay casting"""
        logger.info("Stopping AirPlay")
        self.session = None
        return True


# ============================================
# DLNA/UPnP CONTROLLER
# ============================================
class DLNAController:
    """Control DLNA/UPnP MediaRenderer devices"""
    
    def __init__(self, device: CastDevice):
        self.device = device
        self.session: Optional[CastSession] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to DLNA device"""
        logger.info(f"Connecting to DLNA: {self.device.name}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device.ip_address, self.device.port))
            
            self.is_connected = True
            logger.success(f"Connected to {self.device.name}")
            return True
        except Exception as e:
            logger.error(f"DLNA connection failed: {e}")
            return False
    
    def cast_video(self, video_url: str, title: str = "Video") -> bool:
        """Cast video via DLNA"""
        if not self.is_connected:
            if not self.connect():
                return False
        
        logger.info(f"DLNA casting: {title}")
        
        try:
            self.session = CastSession(
                session_id=f"dlna_{int(time.time())}",
                device=self.device,
                protocol=CastProtocol.DLNA.value,
                mode=CastMode.VIDEO.value,
                status="casting",
                started=datetime.now().isoformat(),
                source=video_url,
                duration=0,
                position=0
            )
            
            # DLNA uses UPnP AVTransport service
            logger.success(f"DLNA casting: {title}")
            return True
        except Exception as e:
            logger.error(f"DLNA cast failed: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop DLNA casting"""
        logger.info("Stopping DLNA")
        self.session = None
        return True


# ============================================
# CASTING MANAGER
# ============================================
class CastingManager:
    """Central casting system manager"""
    
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.discovery = CastDeviceDiscovery()
        self.active_sessions: Dict[str, CastSession] = {}
        
        logger.info("=== Initializing ORSAY TV Casting System ===")
        self.discovery.start_discovery()
        logger.success("Casting system ready")
    
    def get_available_devices(self) -> List[CastDevice]:
        """Get all available cast devices"""
        return self.discovery.get_devices()
    
    def get_devices_by_protocol(self, protocol: str) -> List[CastDevice]:
        """Get devices by protocol"""
        try:
            protocol_enum = CastProtocol[protocol.upper()]
            return self.discovery.get_device_by_protocol(protocol_enum)
        except:
            return []
    
    def cast_video_to_device(self, device_id: str, video_url: str, title: str = "Video") -> bool:
        """Cast video to specific device"""
        device = None
        for d in self.discovery.get_devices():
            if d.device_id == device_id:
                device = d
                break
        
        if not device:
            logger.error(f"Device not found: {device_id}")
            return False
        
        try:
            if device.protocol == CastProtocol.CHROMECAST.value:
                controller = ChromecastController(device)
                success = controller.cast_video(video_url, title)
                if success and controller.session:
                    self.active_sessions[controller.session.session_id] = controller.session
                return success
            
            elif device.protocol == CastProtocol.AIRPLAY.value:
                controller = AirPlayController(device)
                success = controller.cast_video(video_url, title)
                if success and controller.session:
                    self.active_sessions[controller.session.session_id] = controller.session
                return success
            
            elif device.protocol == CastProtocol.DLNA.value:
                controller = DLNAController(device)
                success = controller.cast_video(video_url, title)
                if success and controller.session:
                    self.active_sessions[controller.session.session_id] = controller.session
                return success
        
        except Exception as e:
            logger.error(f"Casting error: {e}")
            return False
        
        return False
    
    def cast_screen_to_device(self, device_id: str) -> bool:
        """Mirror screen to device (Chromecast only)"""
        device = None
        for d in self.discovery.get_devices():
            if d.device_id == device_id:
                device = d
                break
        
        if not device:
            return False
        
        if device.protocol != CastProtocol.CHROMECAST.value:
            logger.warning("Screen mirroring only supported on Chromecast")
            return False
        
        controller = ChromecastController(device)
        return controller.cast_screen()
    
    def cast_audio_to_device(self, device_id: str, audio_url: str, title: str = "Audio") -> bool:
        """Cast audio to device (AirPlay/DLNA)"""
        device = None
        for d in self.discovery.get_devices():
            if d.device_id == device_id:
                device = d
                break
        
        if not device:
            return False
        
        if device.protocol == CastProtocol.AIRPLAY.value:
            controller = AirPlayController(device)
            return controller.cast_audio(audio_url, title)
        elif device.protocol == CastProtocol.DLNA.value:
            controller = DLNAController(device)
            return controller.cast_video(audio_url, title)
        
        return False
    
    def get_active_sessions(self) -> List[CastSession]:
        """Get all active casting sessions"""
        return list(self.active_sessions.values())
    
    def stop_session(self, session_id: str) -> bool:
        """Stop a casting session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Session stopped: {session_id}")
            return True
        return False
    
    def stop_all(self):
        """Stop all casting sessions"""
        self.active_sessions.clear()
        self.discovery.stop_discovery()
        logger.info("Casting system stopped")


# ============================================
# TV CASTING SERVICE
# ============================================
class TVCastingService:
    """
    ORSAY TV Casting Service
    System service for casting (similar to IPTVService)
    """
    
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.casting_manager = CastingManager(event_bus)
        self.running = False
    
    def init(self):
        """Initialize service"""
        logger.info("[Service] CastingService initialized")
        self.running = True
    
    def loop(self):
        """Service main loop"""
        if self.running:
            # Check for device updates, session status, etc
            pass
    
    def shutdown(self):
        """Shutdown service"""
        self.casting_manager.stop_all()
        self.running = False
        logger.info("[Service] CastingService stopped")
    
    # Public API methods
    def get_cast_devices(self) -> List[Dict]:
        """Get available cast devices"""
        devices = self.casting_manager.get_available_devices()
        return [
            {
                "id": d.device_id,
                "name": d.name,
                "protocol": d.protocol,
                "ip": d.ip_address,
                "capability": d.capability,
                "status": d.status
            }
            for d in devices
        ]
    
    def cast_video(self, device_id: str, video_url: str, title: str = "Video") -> bool:
        """Cast video"""
        return self.casting_manager.cast_video_to_device(device_id, video_url, title)
    
    def cast_screen(self, device_id: str) -> bool:
        """Mirror screen"""
        return self.casting_manager.cast_screen_to_device(device_id)
    
    def cast_audio(self, device_id: str, audio_url: str, title: str = "Audio") -> bool:
        """Cast audio"""
        return self.casting_manager.cast_audio_to_device(device_id, audio_url, title)
    
    def stop_casting(self, session_id: str) -> bool:
        """Stop casting"""
        return self.casting_manager.stop_session(session_id)


# ============================================
# DEMONSTRATION
# ============================================
def demo():
    """Demo of casting system"""
    
    print("\n" + "="*60)
    print("ORSAY TV Casting System - Demo")
    print("="*60 + "\n")
    
    # Create a simple event bus
    class SimpleEventBus:
        def emit(self, event, data=None):
            print(f"[Event] {event}: {data}")
    
    event_bus = SimpleEventBus()
    
    # Initialize casting service
    casting_service = TVCastingService(event_bus)
    casting_service.init()
    
    # Wait for discovery
    print("Discovering cast devices...\n")
    time.sleep(3)
    
    # Get available devices
    devices = casting_service.get_cast_devices()
    
    if devices:
        print(f"Found {len(devices)} cast device(s):\n")
        for device in devices:
            print(f"  • {device['name']} ({device['protocol'].upper()})")
            print(f"    IP: {device['ip']} | Capability: {device['capability']}")
            print(f"    Status: {device['status']}\n")
        
        # Try casting to first device
        device_id = devices[0]['id']
        print(f"\nAttempting to cast video to {devices[0]['name']}...")
        
        success = casting_service.cast_video(
            device_id,
            "http://example.com/video.mp4",
            "Test Video"
        )
        
        if success:
            print("✓ Casting started")
        else:
            print("✗ Casting failed")
    else:
        print("No cast devices found on network")
        print("\nTips:")
        print("  - Connect Chromecast, AirPlay device, or DLNA renderer to your network")
        print("  - Ensure devices are powered on")
        print("  - Check network connectivity")
    
    casting_service.shutdown()
    print("\n✓ Demo complete")


if __name__ == "__main__":
    demo()
