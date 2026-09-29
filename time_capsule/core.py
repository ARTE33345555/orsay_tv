#!/usr/bin/env python3
"""
ORSAY TV Time Capsule - Video Recording System
Manages recording from available sources to local storage with scheduling support.
"""

import os
import sys
import json
import time
import threading
import queue
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).parent.parent
CAPSULE_DIR = BASE_DIR / "time_capsule"
RECORDINGS_DIR = CAPSULE_DIR / "recordings"
METADATA_DIR = CAPSULE_DIR / "metadata"
SCHEDULED_DIR = CAPSULE_DIR / "scheduled"
CONFIG_FILE = CAPSULE_DIR / "config.json"
LOGS_DIR = BASE_DIR / "firmware" / "var" / "logs"


# ============================================
# LOGGER
# ============================================
class TimeCapsuleLogger:
    """Logger for Time Capsule system"""
    
    def __init__(self):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = LOGS_DIR / f"time_capsule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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


logger = TimeCapsuleLogger()


# ============================================
# ENUMS & DATA STRUCTURES
# ============================================
class RecordingSource(Enum):
    """Available recording sources"""
    TV_TUNER = "tv"           # TV broadcast signal
    USB_MEDIA = "usb"         # USB device input
    HDMI_INPUT = "hdmi"       # HDMI input
    NETWORK_STREAM = "network" # Network stream


class StorageType(Enum):
    """Storage media types"""
    INTERNAL_HDD = "internal"
    USB_STORAGE = "usb"
    NETWORK_STORAGE = "network"


class RecordingStatus(Enum):
    """Recording status"""
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"
    INTERRUPTED = "interrupted"
    SCHEDULED = "scheduled"


@dataclass
class Recording:
    """Recording metadata"""
    recording_id: str
    title: str
    source: str
    started: str  # ISO format datetime
    duration: int  # seconds
    storage: str
    storage_type: str
    filepath: str
    filesize: int  # bytes
    status: str
    interrupted: bool = False
    metadata_file: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class StorageDevice:
    """Storage device information"""
    device_id: str
    device_type: str  # "internal", "usb", "network"
    mount_point: str
    total_size: int  # bytes
    used_size: int
    free_size: int
    filesystem: str
    status: str  # "available", "error", "disconnected"
    
    @property
    def usage_percent(self) -> float:
        if self.total_size == 0:
            return 0.0
        return (self.used_size / self.total_size) * 100


@dataclass
class ScheduledRecording:
    """Scheduled recording configuration"""
    schedule_id: str
    title: str
    source: str
    channel: Optional[int]  # for TV tuner
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    storage: str
    enabled: bool = True
    status: str = "pending"  # pending, completed, failed, cancelled


# ============================================
# SOURCE DETECTOR
# ============================================
class SourceDetector:
    """Detect available recording sources on the TV"""
    
    def __init__(self):
        self.sources: Dict[RecordingSource, bool] = {}
        self.detect_sources()
    
    def detect_sources(self):
        """Detect which sources are available"""
        logger.info("=== Detecting Recording Sources ===")
        
        # TV Tuner detection
        self.sources[RecordingSource.TV_TUNER] = self._detect_tv_tuner()
        
        # USB Media detection
        self.sources[RecordingSource.USB_MEDIA] = self._detect_usb_media()
        
        # HDMI Input detection
        self.sources[RecordingSource.HDMI_INPUT] = self._detect_hdmi()
        
        # Network Stream detection
        self.sources[RecordingSource.NETWORK_STREAM] = True  # Usually available
        
        # Log results
        for source, available in self.sources.items():
            status = "✓ Available" if available else "✗ Not available"
            logger.info(f"{source.value.upper()}: {status}")
    
    def _detect_tv_tuner(self) -> bool:
        """Check if TV tuner is available"""
        try:
            # Orsay: check for /dev/dvb or similar
            if os.path.exists("/dev/dvb0") or os.path.exists("/dev/video0"):
                logger.info("TV Tuner detected")
                return True
        except:
            pass
        
        logger.warning("TV Tuner not found or not accessible")
        return False
    
    def _detect_usb_media(self) -> bool:
        """Check if USB media input is available"""
        try:
            # Check for USB devices
            if os.path.exists("/media") or os.path.exists("/mnt/usb0"):
                logger.info("USB Media detected")
                return True
        except:
            pass
        
        return False
    
    def _detect_hdmi(self) -> bool:
        """Check if HDMI input is available"""
        try:
            # Check for HDMI capture devices
            if os.path.exists("/dev/video1") or os.path.exists("/dev/video2"):
                logger.info("HDMI Input detected")
                return True
        except:
            pass
        
        logger.warning("HDMI Input not available on this model")
        return False
    
    def get_available_sources(self) -> List[str]:
        """Get list of available source names"""
        return [s.value for s, available in self.sources.items() if available]
    
    def is_source_available(self, source: RecordingSource) -> bool:
        """Check if specific source is available"""
        return self.sources.get(source, False)


# ============================================
# STORAGE MANAGER
# ============================================
class StorageManager:
    """Manage storage devices and space"""
    
    def __init__(self):
        self.devices: Dict[str, StorageDevice] = {}
        self.primary_storage: Optional[str] = None
        self._scan_storage()
    
    def _scan_storage(self):
        """Scan for available storage devices"""
        logger.info("=== Scanning Storage Devices ===")
        
        # Internal storage
        self._scan_internal_storage()
        
        # USB storage
        self._scan_usb_storage()
        
        # Network storage (if available)
        self._scan_network_storage()
        
        if self.devices:
            self.primary_storage = list(self.devices.keys())[0]
            logger.success(f"Found {len(self.devices)} storage device(s)")
        else:
            logger.warning("No storage devices found!")
    
    def _scan_internal_storage(self):
        """Scan internal storage/HDD"""
        try:
            stat = os.statvfs("/")
            device = StorageDevice(
                device_id="internal",
                device_type="internal",
                mount_point="/",
                total_size=stat.f_blocks * stat.f_frsize,
                used_size=(stat.f_blocks - stat.f_avail) * stat.f_frsize,
                free_size=stat.f_avail * stat.f_frsize,
                filesystem="ext4",
                status="available"
            )
            self.devices["internal"] = device
            logger.info(f"Internal storage: {device.free_size / (1024**3):.1f} GB free")
        except Exception as e:
            logger.error(f"Failed to scan internal storage: {e}")
    
    def _scan_usb_storage(self):
        """Scan USB storage devices"""
        usb_paths = ["/mnt/usb0", "/media/usb", "/mnt/usb", "/media"]
        usb_count = 0
        
        for usb_path in usb_paths:
            if os.path.exists(usb_path):
                try:
                    stat = os.statvfs(usb_path)
                    device_id = f"usb{usb_count}"
                    device = StorageDevice(
                        device_id=device_id,
                        device_type="usb",
                        mount_point=usb_path,
                        total_size=stat.f_blocks * stat.f_frsize,
                        used_size=(stat.f_blocks - stat.f_avail) * stat.f_frsize,
                        free_size=stat.f_avail * stat.f_frsize,
                        filesystem="fat32",
                        status="available"
                    )
                    self.devices[device_id] = device
                    logger.info(f"USB {device_id}: {device.free_size / (1024**3):.1f} GB free")
                    usb_count += 1
                except Exception as e:
                    logger.error(f"Failed to scan USB at {usb_path}: {e}")
    
    def _scan_network_storage(self):
        """Scan network storage (if available)"""
        # Network storage detection would go here
        # For now, skip if not configured
        pass
    
    def get_devices(self) -> List[StorageDevice]:
        """Get all storage devices"""
        return list(self.devices.values())
    
    def get_device(self, device_id: str) -> Optional[StorageDevice]:
        """Get specific storage device"""
        return self.devices.get(device_id)
    
    def has_free_space(self, device_id: str, required_bytes: int) -> bool:
        """Check if device has enough free space"""
        device = self.devices.get(device_id)
        if not device:
            return False
        return device.free_size >= required_bytes
    
    def get_free_space(self, device_id: str) -> int:
        """Get free space in bytes"""
        device = self.devices.get(device_id)
        return device.free_size if device else 0


# ============================================
# RECORDING ENGINE
# ============================================
class RecordingEngine:
    """Handles actual recording operations"""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.current_recording: Optional[Recording] = None
        self.is_recording = False
        self.record_thread: Optional[threading.Thread] = None
        self.record_queue: queue.Queue = queue.Queue()
    
    def start_recording(self, source: str, storage_id: str, title: str = "Recording") -> Tuple[bool, str]:
        """Start recording from source"""
        logger.info(f"Starting recording from {source} to {storage_id}")
        
        # Validate source and storage
        if not self.storage_manager.has_free_space(storage_id, 100 * 1024 * 1024):  # 100MB minimum
            msg = "Insufficient storage space"
            logger.error(msg)
            return False, msg
        
        # Create recording metadata
        recording_id = f"rec_{int(time.time())}"
        filepath = RECORDINGS_DIR / f"{recording_id}.ts"  # MPEG-TS format (common for DVB)
        
        metadata_file = METADATA_DIR / f"{recording_id}.json"
        
        self.current_recording = Recording(
            recording_id=recording_id,
            title=title,
            source=source,
            started=datetime.now().isoformat(),
            duration=0,
            storage=storage_id,
            storage_type="usb" if "usb" in storage_id else "internal",
            filepath=str(filepath),
            filesize=0,
            status="recording",
            metadata_file=str(metadata_file)
        )
        
        self.is_recording = True
        
        # Start recording thread
        self.record_thread = threading.Thread(
            target=self._record_loop,
            args=(source, filepath),
            daemon=True
        )
        self.record_thread.start()
        
        logger.success(f"Recording started: {recording_id}")
        return True, recording_id
    
    def _record_loop(self, source: str, filepath: Path):
        """Recording loop (simulated or real)"""
        logger.info(f"Recording loop started for {source}")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # In real implementation:
            # - Would hook into actual video stream via ffmpeg/gstreamer
            # - For Orsay: might use DVR API if available
            # - For simulator: generate test video
            
            # Simulated recording
            bytes_written = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(filepath, 'wb') as f:
                while self.is_recording and self.current_recording:
                    # Simulate writing video data
                    f.write(b'\x00' * chunk_size)
                    bytes_written += chunk_size
                    
                    self.current_recording.filesize = bytes_written
                    self.current_recording.duration = int(bytes_written / (1024 * 1024))  # Simplified
                    
                    time.sleep(0.1)  # Simulate recording delay
            
            logger.info(f"Recording saved: {filepath} ({bytes_written / (1024**2):.1f} MB)")
        
        except Exception as e:
            logger.error(f"Recording error: {e}")
            if self.current_recording:
                self.current_recording.status = "interrupted"
                self.current_recording.interrupted = True
    
    def stop_recording(self) -> Optional[Recording]:
        """Stop current recording"""
        if not self.is_recording or not self.current_recording:
            logger.warning("No recording in progress")
            return None
        
        logger.info(f"Stopping recording: {self.current_recording.recording_id}")
        
        self.is_recording = False
        
        if self.record_thread:
            self.record_thread.join(timeout=5)
        
        # Save metadata
        if self.current_recording:
            self.current_recording.status = "stopped"
            self._save_metadata(self.current_recording)
        
        recording = self.current_recording
        self.current_recording = None
        
        logger.success(f"Recording stopped: {recording.recording_id}")
        return recording
    
    def _save_metadata(self, recording: Recording):
        """Save recording metadata to file"""
        try:
            METADATA_DIR.mkdir(parents=True, exist_ok=True)
            metadata_file = Path(recording.metadata_file)
            
            with open(metadata_file, 'w') as f:
                json.dump(recording.to_dict(), f, indent=2)
            
            logger.debug(f"Metadata saved: {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def get_current_recording_status(self) -> Optional[Dict]:
        """Get current recording status"""
        if not self.current_recording:
            return None
        
        return {
            "recording_id": self.current_recording.recording_id,
            "title": self.current_recording.title,
            "source": self.current_recording.source,
            "duration": self.current_recording.duration,
            "filesize": self.current_recording.filesize,
            "storage": self.current_recording.storage
        }


# ============================================
# RECORDINGS LIBRARY
# ============================================
class RecordingsLibrary:
    """Manage recorded files"""
    
    def __init__(self):
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def list_recordings(self, sort_by: str = "date") -> List[Recording]:
        """List all recordings"""
        recordings = []
        
        for metadata_file in METADATA_DIR.glob("*.json"):
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                    recording = Recording(**data)
                    recordings.append(recording)
            except Exception as e:
                logger.error(f"Failed to load metadata {metadata_file}: {e}")
        
        # Sort
        if sort_by == "date":
            recordings.sort(key=lambda r: r.started, reverse=True)
        elif sort_by == "size":
            recordings.sort(key=lambda r: r.filesize, reverse=True)
        elif sort_by == "duration":
            recordings.sort(key=lambda r: r.duration, reverse=True)
        
        return recordings
    
    def get_recording(self, recording_id: str) -> Optional[Recording]:
        """Get specific recording"""
        metadata_file = METADATA_DIR / f"{recording_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file) as f:
                data = json.load(f)
                return Recording(**data)
        except Exception as e:
            logger.error(f"Failed to load recording {recording_id}: {e}")
            return None
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording"""
        recording = self.get_recording(recording_id)
        if not recording:
            return False
        
        try:
            # Delete file
            if os.path.exists(recording.filepath):
                os.remove(recording.filepath)
            
            # Delete metadata
            metadata_file = METADATA_DIR / f"{recording_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.success(f"Deleted recording: {recording_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete recording: {e}")
            return False
    
    def rename_recording(self, recording_id: str, new_title: str) -> bool:
        """Rename a recording"""
        recording = self.get_recording(recording_id)
        if not recording:
            return False
        
        recording.title = new_title
        metadata_file = METADATA_DIR / f"{recording_id}.json"
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(recording.to_dict(), f, indent=2)
            logger.info(f"Renamed recording: {recording_id} -> {new_title}")
            return True
        except Exception as e:
            logger.error(f"Failed to rename recording: {e}")
            return False
    
    def search_recordings(self, query: str) -> List[Recording]:
        """Search recordings by title"""
        all_recordings = self.list_recordings()
        query_lower = query.lower()
        return [r for r in all_recordings if query_lower in r.title.lower()]


# ============================================
# SCHEDULED RECORDING MANAGER
# ============================================
class ScheduledRecordingManager:
    """Manage scheduled recordings"""
    
    def __init__(self, recording_engine: RecordingEngine, source_detector: SourceDetector):
        self.recording_engine = recording_engine
        self.source_detector = source_detector
        self.scheduled: Dict[str, ScheduledRecording] = {}
        SCHEDULED_DIR.mkdir(parents=True, exist_ok=True)
        self._load_scheduled()
    
    def add_schedule(self, title: str, source: str, date: str, start_time: str, 
                     end_time: str, storage: str) -> Tuple[bool, str]:
        """Add a scheduled recording"""
        # Validate
        if not self._validate_schedule(source, storage, date, start_time):
            return False, "Validation failed"
        
        schedule_id = f"sch_{int(time.time())}"
        
        scheduled = ScheduledRecording(
            schedule_id=schedule_id,
            title=title,
            source=source,
            channel=None,
            date=date,
            start_time=start_time,
            end_time=end_time,
            storage=storage
        )
        
        self.scheduled[schedule_id] = scheduled
        self._save_schedule(scheduled)
        
        logger.success(f"Scheduled recording: {schedule_id}")
        return True, schedule_id
    
    def _validate_schedule(self, source: str, storage: str, date: str, start_time: str) -> bool:
        """Validate scheduled recording parameters"""
        # Check source availability
        try:
            recording_source = RecordingSource(source)
            if not self.source_detector.is_source_available(recording_source):
                logger.warning(f"Source {source} not available on this TV")
                return False
        except:
            logger.error(f"Invalid source: {source}")
            return False
        
        # Check if date is in future or today
        schedule_date = datetime.strptime(date, "%Y-%m-%d")
        if schedule_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            logger.warning("Cannot schedule recording in the past")
            return False
        
        return True
    
    def _save_schedule(self, scheduled: ScheduledRecording):
        """Save schedule to file"""
        schedule_file = SCHEDULED_DIR / f"{scheduled.schedule_id}.json"
        
        try:
            with open(schedule_file, 'w') as f:
                json.dump(asdict(scheduled), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save schedule: {e}")
    
    def _load_scheduled(self):
        """Load all scheduled recordings"""
        for schedule_file in SCHEDULED_DIR.glob("*.json"):
            try:
                with open(schedule_file) as f:
                    data = json.load(f)
                    scheduled = ScheduledRecording(**data)
                    self.scheduled[scheduled.schedule_id] = scheduled
            except Exception as e:
                logger.error(f"Failed to load schedule {schedule_file}: {e}")
    
    def list_scheduled(self) -> List[ScheduledRecording]:
        """List all scheduled recordings"""
        return list(self.scheduled.values())
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a scheduled recording"""
        if schedule_id not in self.scheduled:
            return False
        
        schedule_file = SCHEDULED_DIR / f"{schedule_id}.json"
        if schedule_file.exists():
            schedule_file.unlink()
        
        del self.scheduled[schedule_id]
        logger.info(f"Deleted schedule: {schedule_id}")
        return True


# ============================================
# TIME CAPSULE MAIN SYSTEM
# ============================================
class TimeCapsuleSystem:
    """Main Time Capsule system coordinator"""
    
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        
        logger.info("=== Initializing ORSAY Time Capsule ===")
        
        self.source_detector = SourceDetector()
        self.storage_manager = StorageManager()
        self.recording_engine = RecordingEngine(self.storage_manager)
        self.library = RecordingsLibrary()
        self.scheduler = ScheduledRecordingManager(self.recording_engine, self.source_detector)
        
        logger.success("Time Capsule System Ready")
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            "available_sources": self.source_detector.get_available_sources(),
            "storage_devices": [asdict(d) for d in self.storage_manager.get_devices()],
            "recording_active": self.recording_engine.is_recording,
            "current_recording": self.recording_engine.get_current_recording_status(),
            "recordings_count": len(self.library.list_recordings())
        }
    
    def start_recording(self, source: str, storage_id: str, title: str = "Recording") -> Tuple[bool, str]:
        """Start recording"""
        return self.recording_engine.start_recording(source, storage_id, title)
    
    def stop_recording(self) -> Optional[Recording]:
        """Stop recording"""
        return self.recording_engine.stop_recording()
    
    def list_recordings(self) -> List[Recording]:
        """List all recordings"""
        return self.library.list_recordings()
    
    def schedule_recording(self, title: str, source: str, date: str, start_time: str,
                          end_time: str, storage: str) -> Tuple[bool, str]:
        """Schedule a recording"""
        return self.scheduler.add_schedule(title, source, date, start_time, end_time, storage)


# ============================================
# DEMONSTRATION
# ============================================
def demo():
    """Demo of Time Capsule system"""
    
    print("\n" + "="*60)
    print("ORSAY TV Time Capsule - System Demo")
    print("="*60 + "\n")
    
    # Initialize
    time_capsule = TimeCapsuleSystem()
    
    # Show status
    status = time_capsule.get_system_status()
    
    print("\n[Available Sources]")
    for source in status["available_sources"]:
        print(f"  ✓ {source.upper()}")
    
    print("\n[Storage Devices]")
    for device in status["storage_devices"]:
        free_gb = device["free_size"] / (1024**3)
        print(f"  {device['device_id']}: {free_gb:.1f} GB free ({device['status']})")
    
    # Test recording
    if status["storage_devices"]:
        print("\n[Starting Test Recording]")
        success, rec_id = time_capsule.start_recording("tv", "internal", "Test Recording")
        
        if success:
            print(f"Recording started: {rec_id}")
            time.sleep(2)  # Record for 2 seconds
            
            recording = time_capsule.stop_recording()
            if recording:
                print(f"Stopped: {recording.title}")
                print(f"  Duration: {recording.duration}s")
                print(f"  Filesize: {recording.filesize / (1024**2):.1f} MB")
        
        # List recordings
        print("\n[Recordings Library]")
        recordings = time_capsule.list_recordings()
        for rec in recordings:
            print(f"  {rec.started}: {rec.title} ({rec.duration}s)")
    
    print("\n✓ Time Capsule demo complete")


if __name__ == "__main__":
    demo()
