# ORSAY TV Time Capsule
## Video Recording System Documentation

---

## Overview

**ORSAY Time Capsule** is a video recording and management system for ORSAY TV that leverages available local storage (internal HDD, USB) and supported input sources to capture and organize video content.

The system is designed with realistic constraints in mind:
- **No cloud dependency**: Recording stored only locally
- **Platform-aware**: Only uses APIs actually available on target platform
- **Graceful degradation**: Clearly reports unsupported features instead of simulating them
- **Safe operation**: Crash protection, metadata preservation, recovery on restart

---

## Supported Features

### ✓ Recording Sources

| Source | Samsung Orsay (2010-2014) | Status | Notes |
|--------|---------------------------|--------|-------|
| **TV Tuner** | /dev/dvb0 or /dev/video0 | ✓ Supported | MPEG-TS format, requires DVB drivers |
| **USB Media** | /media or /mnt/usb | ✓ Supported | USB stick/drive with media input |
| **HDMI Input** | /dev/video1, /dev/video2 | ⚠ Limited | Only on models with HDMI capture |
| **Network Stream** | Local network (RTSP/HTTP) | ✓ Supported | Via software decode (slower) |

**Detection Logic**:
```python
# System automatically scans:
- /dev/dvb*      → TV Tuner
- /dev/video*    → Video input devices
- /media, /mnt   → USB storage
- Network stack  → Stream capability
```

### ✓ Storage

| Type | Location | Capacity | Status |
|------|----------|----------|--------|
| **Internal** | / (root filesystem) | 256MB - 2GB | ✓ Available |
| **USB Storage** | /mnt/usb0, /media/usb | 4GB - 1TB | ✓ Available |
| **Network Storage** | SMB/NFS mount | Variable | ⚠ Not implemented yet |

**Storage Manager**:
- Auto-detects mount points
- Checks free space before recording
- Warns if < 100MB free
- Supports multiple USB devices

### ✓ Recording Format

**Primary Format**: MPEG-TS (`.ts`)
- Standard for DVB/TV capture
- No re-encoding needed
- Preserves video quality
- Compatible with most TV players

**Metadata**: JSON
```json
{
  "recording_id": "rec_1695998400",
  "title": "Channel 5 News",
  "source": "tv",
  "started": "2026-09-29T19:20:00",
  "duration": 3600,
  "storage": "internal",
  "storage_type": "internal",
  "filepath": "/time_capsule/recordings/rec_1695998400.ts",
  "filesize": 1073741824,
  "status": "complete",
  "interrupted": false
}
```

### ✓ Recording Library

- List recordings by date/size/duration
- Play recording (via IPTV Service)
- Delete recording (file + metadata)
- Rename recording
- Search by title
- View info (source, duration, filesize)
- Sort options: date, size, duration

### ✓ Scheduled Recording

- Schedule by date/time
- Select source and storage
- Validate before scheduling
- Check for conflicts
- Persist schedules to disk
- Load on restart

**Scheduling Limitations**:
- Cannot start TV from standby (TV must be on)
- Only schedules recording when system is running
- No ACPI/WoL support on Orsay devices

### ✓ Crash Protection

- Metadata saved immediately after stop
- Interrupted recordings marked as such
- File integrity checks on load
- Recovery detection on next boot
- Existing recordings never corrupted

---

## Unsupported Features

### ✗ Features NOT Available

| Feature | Reason | Workaround |
|---------|--------|-----------|
| **Wake-on-LAN Recording** | Orsay doesn't support WoL recording | Schedule must start when TV is on |
| **Network Streaming Input** | Complex codec support needed | Use local USB input instead |
| **H.265/HEVC Recording** | Old kernel/drivers don't support | MPEG-TS output is H.264 compatible |
| **3G/Mobile Upload** | No cloud backend | Manual transfer via USB |
| **Real-time Transcoding** | CPU too weak for real-time | Pre-process recordings on PC |
| **Multi-source Recording** | Single tuner limitation | Sequential recording only |
| **Recording from Web Apps** | Browser sandbox limitations | Use TV tuner or USB input |

### ⚠ Features With Limitations

| Feature | Limitation | Details |
|---------|-----------|---------|
| **Scheduled Recording** | TV must stay on | Power management issues if TV sleeps |
| **USB Recording** | Speed dependent | Slow USB 2.0 on older models |
| **Storage Ejection** | Files locked during record | Must stop recording before ejecting USB |
| **Remote Control** | Basic commands only | See Wi-Con API limitations |

---

## Platform-Specific Notes

### Samsung Orsay (2010-2014)

**Hardware Specs**:
- CPU: ARM Cortex-A9 @ 1.4-1.8 GHz
- RAM: 512MB typical
- Storage: 256MB - 2GB eMMC
- Tuner: Built-in DVB-T/S (varies by region)
- I/O: USB 2.0, Ethernet, HDMI

**Recording Capability**:
- **TV Tuner**: Yes, via DVB devices
- **HDMI Input**: No capture chip on most models
- **Recording Duration**: Limited by storage (256MB = ~45min at 1.5Mbps)
- **Simultaneous Recording + Playback**: Not recommended (memory pressure)

**Supported Codecs** (passthrough):
- H.264 (AVC)
- MPEG-2
- MPEG-1

**Known Issues**:
1. **DVB driver availability**: Not all Orsay builds include DVB drivers
2. **Tuner locking**: Some models lock tuner during recording
3. **USB speed**: USB 2.0 limited to ~35-40 MB/s, video bitrate must fit
4. **Storage wear**: eMMC has limited write cycles (check firmware)

### Tizen Modern (2015+)

**Recommended**: Use native Tizen recording APIs instead of Time Capsule.

Time Capsule still works but:
- More storage available (1-8GB)
- Better CPU (better codec support)
- Tizen SDK provides better API access

### LG WebOS

**Not supported**: Use native webOS recording features.

---

## System Architecture

```
Time Capsule
    │
    ├─ SourceDetector
    │   ├─ Scan /dev/dvb*       → TV Tuner
    │   ├─ Scan /dev/video*     → Video devices
    │   ├─ Scan /media, /mnt    → USB storage
    │   └─ Check network stack  → Network capability
    │
    ├─ StorageManager
    │   ├─ Scan /                → Internal
    │   ├─ Scan /mnt/usb*        → USB devices
    │   └─ Calculate free space
    │
    ├─ RecordingEngine
    │   ├─ Start recording
    │   ├─ Write video stream
    │   ├─ Save metadata
    │   └─ Stop recording
    │
    ├─ RecordingsLibrary
    │   ├─ List recordings
    │   ├─ Delete recording
    │   ├─ Rename recording
    │   └─ Search recordings
    │
    └─ ScheduledRecordingManager
        ├─ Add schedule
        ├─ Validate schedule
        ├─ Load/save to disk
        └─ Check conflicts
```

---

## Configuration

**Config File**: `/firmware/orsay.conf`

```ini
[time_capsule]
enabled=true
default_storage=internal
max_recording_duration=7200
auto_cleanup_old=false
cleanup_older_than_days=30

[recording]
source=tv
video_codec=h264
bitrate=2500k
resolution=720x480
framerate=25

[storage]
internal_enabled=true
usb_enabled=true
network_enabled=false

[scheduling]
enabled=true
check_interval=60
```

---

## Storage Calculation

**Recording Bitrate**: ~2.5 Mbps (typical)

| Duration | Storage Required |
|----------|------------------|
| 30 min | 562 MB |
| 1 hour | 1.1 GB |
| 2 hours | 2.2 GB |
| 4 hours | 4.5 GB |

**Free Space Warning**:
- < 500 MB: Warning (about 3 min remaining)
- < 100 MB: Recording blocked
- Buffer: 50 MB reserved

---

## Recording Process

### Start Recording
```
1. Validate source available
2. Validate storage has free space
3. Create recording metadata
4. Open video device/stream
5. Start writing to file
6. Update recording status
7. Return recording_id
```

### Stop Recording
```
1. Close video stream
2. Finalize file (flush buffers)
3. Update duration, filesize
4. Save metadata to JSON
5. Mark status as "complete"
6. Return recording object
```

### Interrupted Recovery
```
1. On boot, scan /time_capsule/metadata/
2. Find recordings with status != "complete"
3. Mark as "interrupted"
4. Preserve file and metadata
5. Offer user to delete or retry
```

---

## Wi-Con Remote TV Integration

**Available Commands**:

```
time_capsule.list_sources
  → Returns: ["tv", "usb", "network"]

time_capsule.start_recording
  Params: {source, storage, title}
  → Returns: {recording_id, status}

time_capsule.stop_recording
  → Returns: {recording_id, duration, filesize}

time_capsule.list_recordings
  Params: {sort_by, limit}
  → Returns: [{id, title, duration, date, ...}]

time_capsule.delete_recording
  Params: {recording_id}
  → Returns: {status}

time_capsule.schedule_recording
  Params: {source, date, start_time, end_time, storage}
  → Returns: {schedule_id, status}

time_capsule.storage_info
  → Returns: [{device_id, free, used, status}]
```

**Remote TV Display**:
```
TIME CAPSULE - REMOTE

● Recording
  Source: TV
  Duration: 00:13:42
  Storage: USB
  [■ Stop]

● Available Sources
  ✓ TV
  ✓ USB
  ✗ HDMI (not supported)

● Storage
  Internal: 120 MB free
  USB: 2.3 GB free
```

---

## Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| Start recording | 1-2 sec | Opens device, allocates buffers |
| Stop recording | 0.5-1 sec | Flushes buffers, saves metadata |
| List recordings | <100ms | Scans JSON files |
| Delete recording | 1-5 sec | Depends on file size |
| Search recordings | <200ms | In-memory search |
| Get storage info | <500ms | Calls statvfs() |

**Memory Usage**:
- Core system: ~15-20 MB
- Per active recording: ~5-10 MB
- Metadata in RAM: <1 MB

---

## Testing & Debugging

### Simulator Mode

**PC Simulator** (for development):
```python
from time_capsule.simulator import TimeCapsuleSimulator

sim = TimeCapsuleSimulator()
sim.start_recording("tv", "internal")
time.sleep(2)
rec = sim.stop_recording()

print(f"Recording: {rec.title}")
print(f"Duration: {rec.duration}s")
print(f"Filesize: {rec.filesize / (1024**2):.1f} MB")
```

**Test Sources**:
- Virtual TV tuner (generates test video)
- Virtual USB device
- Mock network stream

### Debug Logs

```bash
# View Time Capsule logs
tail -f /firmware/var/logs/time_capsule_*.log

# Check metadata
cat /time_capsule/metadata/rec_*.json | jq .

# List recordings
ls -lah /time_capsule/recordings/
```

---

## Security Considerations

1. **File Permissions**: Recordings readable only by ORSAY TV system user
2. **Metadata Privacy**: Contains timestamps but no personal data
3. **Storage Encryption**: Not supported (would require kernel changes)
4. **USB Ejection**: System checks if file locked before allowing eject
5. **Interrupted Files**: Can't corrupt existing recordings

---

## Limitations & Workarounds

### Limitation #1: Limited Storage
**Problem**: Orsay has only 256MB-2GB internal storage

**Workaround**:
- Use external USB drive (4GB+)
- Schedule shorter recordings
- Delete old recordings regularly
- Consider external HDD via USB hub

### Limitation #2: No Wake-on-LAN
**Problem**: Can't start recording automatically if TV is off

**Workaround**:
- Keep TV on for scheduled recordings
- Use smartphone app to check/start recording manually
- Consider Smart Plug to power on TV before scheduled time

### Limitation #3: Single Tuner
**Problem**: Can't record one channel while watching another

**Workaround**:
- Plan recording and watching times
- Use dual-tuner external device (not standard)
- Record to file, watch later

### Limitation #4: No HDMI Capture
**Problem**: Most Orsay models don't have HDMI input capture

**Workaround**:
- Use composite/SCART input if available
- Route HDMI through external capture device
- Capture on PC and transfer via USB

---

## Future Enhancements

- [ ] Network storage support (SMB/NFS)
- [ ] Integration with Home Assistant
- [ ] Automatic file management (delete old after X days)
- [ ] Thumbnail generation for faster browsing
- [ ] Export to formats (MP4, WebM)
- [ ] Subtitle/EPG integration
- [ ] Cloud backup (optional, user-configured)
- [ ] Multi-tuner support (external devices)

---

## Troubleshooting

### Recording won't start
1. Check if source is available: `time_capsule.list_sources`
2. Verify storage has free space: `time_capsule.storage_info`
3. Check logs: `tail /firmware/var/logs/time_capsule_*.log`

### Recordings disappeared
1. Check USB device is still mounted: `df -h`
2. Look for interrupted recordings: `ls -l /time_capsule/metadata/`
3. Verify file system integrity: `fsck` (requires reboot)

### Recording playback stutters
1. Reduce recording bitrate in config
2. Use faster USB device (USB 3.0)
3. Close other applications to free RAM
4. Check TV CPU usage with system monitor

### Storage full, can't record
1. Delete old recordings: `time_capsule.delete_recording(id)`
2. Move recordings to USB via media player
3. Format and clear Time Capsule system
4. Consider external storage solution

---

## Support & Reporting Issues

When reporting issues, include:
1. TV model: `cat /proc/version`
2. Orsay version: Check system settings
3. Storage device: `df -h`
4. Recent logs: `/firmware/var/logs/time_capsule_*.log`
5. Last few recordings: `ls -la /time_capsule/metadata/` (last 3-5)

---

## See Also

- `ARCHITECTURE.md` - System architecture overview
- `CREATE_APP.md` - How to build custom apps
- `README.md` - Main documentation
- `core/voice_assistant.py` - Voice control integration
- `platform/orsay/native_api.py` - Orsay-specific APIs

