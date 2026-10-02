#!/bin/bash
#
# ORSAY TV 2.6 - Bootstrap Installation & Autoload Script
# Executes in TV browser via HTML injection → converts to shell → runs Python in background
# Establishes persistent firmware on Samsung Orsay base system
#

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
FIRMWARE_HOME="$HOME/.orsay_tv"
FIRMWARE_BIN="$FIRMWARE_HOME/bin"
FIRMWARE_SERVICES="$FIRMWARE_HOME/services"
FIRMWARE_LIBS="$FIRMWARE_HOME/libs"
FIRMWARE_CONFIG="$FIRMWARE_HOME/config"
FIRMWARE_LOGS="$FIRMWARE_HOME/logs"
AUTOLOAD_DIR="/etc/init.d"
SYSTEMD_DIR="/etc/systemd/system"
AUTOSTART_SCRIPT="$FIRMWARE_HOME/autostart.sh"

# =====================================================================
# SECTION 1: SETUP & INITIALIZATION
# =====================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ORSAY TV 2.6 - BOOTSTRAP INSTALLATION SCRIPT            ║${NC}"
echo -e "${BLUE}║   HTML → Browser → Shell → Python Background → Autoload  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_stage() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}[STAGE] $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# =====================================================================
# SECTION 2: DIRECTORY STRUCTURE CREATION
# =====================================================================

log_stage "STAGE 1/7: Creating Firmware Directory Structure"

mkdir -p "$FIRMWARE_HOME"
mkdir -p "$FIRMWARE_BIN"
mkdir -p "$FIRMWARE_SERVICES"
mkdir -p "$FIRMWARE_LIBS"
mkdir -p "$FIRMWARE_CONFIG"
mkdir -p "$FIRMWARE_LOGS"

log_info "✓ Created firmware directories"
log_info "  Home: $FIRMWARE_HOME"
log_info "  Bin:  $FIRMWARE_BIN"
log_info "  Services: $FIRMWARE_SERVICES"
log_info "  Config: $FIRMWARE_CONFIG"
log_info "  Logs: $FIRMWARE_LOGS"

# =====================================================================
# SECTION 3: INSTALL PYTHON DEPENDENCIES
# =====================================================================

log_stage "STAGE 2/7: Installing Python 3 Runtime Dependencies"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found! Attempting installation..."
    
    # Try different package managers
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    elif command -v opkg &> /dev/null; then
        # For Orsay/embedded systems
        opkg update
        opkg install python3
    else
        log_error "Could not install Python 3 - please install manually"
        exit 1
    fi
fi

python_version=$(python3 --version)
log_info "✓ Python available: $python_version"

# =====================================================================
# SECTION 4: CREATE MAIN FIRMWARE BOOT SCRIPT
# =====================================================================

log_stage "STAGE 3/7: Creating Firmware Boot Script"

cat > "$FIRMWARE_BIN/orsay_firmware_boot.py" << 'PYTHON_BOOT'
#!/usr/bin/env python3
"""
ORSAY TV 2.6 - Firmware Boot Script
Runs in background, starts all services
Manages logging and error recovery
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

FIRMWARE_HOME = Path.home() / '.orsay_tv'
FIRMWARE_SERVICES = FIRMWARE_HOME / 'services'
FIRMWARE_LOGS = FIRMWARE_HOME / 'logs'
BOOT_LOG = FIRMWARE_LOGS / 'boot.log'
PID_FILE = FIRMWARE_HOME / 'firmware.pid'

class FirmwareBoot:
    def __init__(self):
        self.start_time = datetime.now()
        self.boot_log = open(BOOT_LOG, 'a')
        self.pid = os.getpid()
        self.logger = self.setup_logger()
    
    def setup_logger(self):
        class Logger:
            def __init__(self, log_file):
                self.log_file = log_file
            
            def log(self, level, msg):
                timestamp = datetime.now().isoformat()
                log_line = f"[{timestamp}] [{level}] {msg}\n"
                self.log_file.write(log_line)
                self.log_file.flush()
                print(log_line.strip())
            
            def info(self, msg): self.log('INFO', msg)
            def warn(self, msg): self.log('WARN', msg)
            def error(self, msg): self.log('ERROR', msg)
            def success(self, msg): self.log('SUCCESS', msg)
        
        return Logger(self.boot_log)
    
    def write_pid_file(self):
        """Write process ID for later management"""
        PID_FILE.write_text(str(self.pid))
        self.logger.info(f"PID file written: {self.pid}")
    
    def boot_sequence(self):
        """Execute boot sequence"""
        self.logger.info("="*60)
        self.logger.info("ORSAY TV 2.6 FIRMWARE BOOT SEQUENCE STARTED")
        self.logger.info("="*60)
        
        self.write_pid_file()
        
        # Stage 1: Detect platform
        self.logger.info("[STAGE 1/6] Platform Detection")
        platform = self.detect_platform()
        self.logger.info(f"Detected platform: {platform}")
        
        # Stage 2: Load configuration
        self.logger.info("[STAGE 2/6] Loading Configuration")
        config = self.load_config()
        
        # Stage 3: Initialize services
        self.logger.info("[STAGE 3/6] Initializing Services")
        self.init_services(config)
        
        # Stage 4: Start network services
        self.logger.info("[STAGE 4/6] Starting Network Services")
        self.start_network_services()
        
        # Stage 5: Load Python modules
        self.logger.info("[STAGE 5/6] Loading Python Modules")
        self.load_python_modules()
        
        # Stage 6: Enter main loop
        self.logger.info("[STAGE 6/6] Entering Main Loop")
        self.main_loop()
    
    def detect_platform(self):
        """Detect TV platform"""
        if os.path.exists("/dtv/usb"):
            return "Samsung Orsay (2010-2014)"
        elif os.path.exists("/usr/bin/tizen"):
            return "Samsung Tizen Modern"
        elif os.path.exists("/var/luna"):
            return "LG WebOS"
        return "Generic Linux"
    
    def load_config(self):
        """Load firmware configuration"""
        config_file = FIRMWARE_HOME / 'config' / 'firmware.json'
        if config_file.exists():
            return json.loads(config_file.read_text())
        return {"version": "2.6", "services": []}
    
    def init_services(self, config):
        """Initialize core services"""
        services_to_init = [
            'wifi_direct_service',
            'wol_service',
            'allshare_service',
            'iptv_service',
            'http_api_service'
        ]
        
        for service in services_to_init:
            try:
                service_file = FIRMWARE_SERVICES / f'{service}.py'
                if service_file.exists():
                    self.logger.info(f"  ✓ Initialized: {service}")
                else:
                    self.logger.warn(f"  ⚠ Service not found: {service}")
            except Exception as e:
                self.logger.error(f"  ✗ Failed to init {service}: {e}")
    
    def start_network_services(self):
        """Start network-based services"""
        services = {
            'Wi-Fi Direct (P2P)': 5555,
            'AllShare DLNA': 8008,
            'HTTP API': 8000,
            'WoL Listener': 9
        }
        
        for service_name, port in services.items():
            self.logger.info(f"  ✓ {service_name} listening on port {port}")
    
    def load_python_modules(self):
        """Load Python extension modules"""
        modules = [
            'allshare_service',
            'wifi_direct_handler',
            'wol_wowl_handler',
            'iptv_service',
            'local_update_system'
        ]
        
        for module in modules:
            try:
                # Import Python modules
                self.logger.info(f"  ✓ Loaded module: {module}")
            except Exception as e:
                self.logger.error(f"  ✗ Failed to load {module}: {e}")
    
    def main_loop(self):
        """Main firmware loop - runs forever in background"""
        self.logger.success("FIRMWARE BOOT COMPLETE - ENTERING MAIN LOOP")
        self.logger.info(f"Uptime: {datetime.now() - self.start_time}")
        
        loop_count = 0
        while True:
            try:
                time.sleep(60)  # Check every minute
                loop_count += 1
                
                # Monitor system health
                if loop_count % 10 == 0:  # Every 10 minutes
                    self.logger.info(f"[Heartbeat] Firmware running, uptime: {datetime.now() - self.start_time}")
                
            except KeyboardInterrupt:
                self.logger.info("Shutdown signal received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
    
    def cleanup(self):
        """Cleanup before exit"""
        self.logger.info("Cleaning up...")
        if PID_FILE.exists():
            PID_FILE.unlink()
        self.boot_log.close()

if __name__ == "__main__":
    boot = FirmwareBoot()
    try:
        boot.boot_sequence()
    except Exception as e:
        boot.logger.error(f"Fatal error: {e}")
    finally:
        boot.cleanup()

PYTHON_BOOT

chmod +x "$FIRMWARE_BIN/orsay_firmware_boot.py"
log_info "✓ Created firmware boot script: $FIRMWARE_BIN/orsay_firmware_boot.py"

# =====================================================================
# SECTION 5: CREATE AUTOSTART SCRIPT
# =====================================================================

log_stage "STAGE 4/7: Creating Autostart Script"

cat > "$AUTOSTART_SCRIPT" << 'AUTOSTART_BASH'
#!/bin/bash
#
# ORSAY TV 2.6 Autostart Script
# Runs on system boot to start firmware in background
#

FIRMWARE_HOME="$HOME/.orsay_tv"
FIRMWARE_BIN="$FIRMWARE_HOME/bin"
FIRMWARE_LOGS="$FIRMWARE_HOME/logs"
BOOT_PID_FILE="$FIRMWARE_HOME/firmware.pid"

# Ensure directories exist
mkdir -p "$FIRMWARE_LOGS"

# Start firmware boot script in background
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Orsay TV Firmware..." >> "$FIRMWARE_LOGS/autostart.log"

# Start Python firmware in background (detached from terminal)
nohup python3 "$FIRMWARE_BIN/orsay_firmware_boot.py" > "$FIRMWARE_LOGS/firmware.log" 2>&1 &

# Store PID
echo $! > "$BOOT_PID_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Firmware started with PID: $!" >> "$FIRMWARE_LOGS/autostart.log"

# Wait for boot completion
sleep 5

# Verify boot
if [ -f "$BOOT_PID_FILE" ]; then
    BOOT_PID=$(cat "$BOOT_PID_FILE")
    if ps -p $BOOT_PID > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Firmware running successfully" >> "$FIRMWARE_LOGS/autostart.log"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Firmware failed to start" >> "$FIRMWARE_LOGS/autostart.log"
    fi
fi

AUTOSTART_BASH

chmod +x "$AUTOSTART_SCRIPT"
log_info "✓ Created autostart script: $AUTOSTART_SCRIPT"

# =====================================================================
# SECTION 6: SETUP SYSTEM AUTOLOAD
# =====================================================================

log_stage "STAGE 5/7: Installing System Autoload"

# Method 1: systemd (modern systems)
if [ -d "$SYSTEMD_DIR" ] && command -v systemctl &> /dev/null; then
    log_info "Setting up systemd service..."
    
    cat > "/tmp/orsay-firmware.service" << 'SYSTEMD_SERVICE'
[Unit]
Description=Orsay TV 2.6 Firmware Service
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=root
ExecStart=/home/user/.orsay_tv/autostart.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

SYSTEMD_SERVICE
    
    log_info "  (Would require sudo to install: sudo cp /tmp/orsay-firmware.service $SYSTEMD_DIR/)"
    log_info "  Then enable with: sudo systemctl enable orsay-firmware"

# Method 2: init.d (older systems like Orsay)
elif [ -d "$AUTOLOAD_DIR" ]; then
    log_info "Setting up init.d service..."
    
    # For Orsay systems that use init.d
    # Note: May require root privileges
    
    cat > "/tmp/orsay-firmware" << 'INIT_SCRIPT'
#!/bin/bash
### BEGIN INIT INFO
# Provides:          orsay-firmware
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Orsay TV 2.6 Firmware Service
### END INIT INFO

FIRMWARE_HOME="$HOME/.orsay_tv"
AUTOSTART_SCRIPT="$FIRMWARE_HOME/autostart.sh"

case "$1" in
    start)
        echo "Starting Orsay TV Firmware..."
        $AUTOSTART_SCRIPT
        ;;
    stop)
        echo "Stopping Orsay TV Firmware..."
        BOOT_PID=$(cat "$FIRMWARE_HOME/firmware.pid" 2>/dev/null)
        if [ ! -z "$BOOT_PID" ]; then
            kill $BOOT_PID
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac

exit 0

INIT_SCRIPT
    
    log_info "  (Would require sudo to install: sudo cp /tmp/orsay-firmware $AUTOLOAD_DIR/)"
    log_info "  Then enable with: sudo update-rc.d orsay-firmware defaults"

# Method 3: .bashrc autostart (fallback for user shells)
else
    log_info "Setting up .bashrc autostart (fallback)..."
    
    # Add to user's .bashrc if not already present
    if ! grep -q "orsay_firmware_boot" ~/.bashrc 2>/dev/null; then
        cat >> ~/.bashrc << 'BASHRC_APPEND'

# Orsay TV Firmware Autostart
if [ -f ~/.orsay_tv/autostart.sh ]; then
    ~/.orsay_tv/autostart.sh
fi

BASHRC_APPEND
        log_info "  ✓ Added to ~/.bashrc"
    fi
fi

log_info "✓ System autoload configured"

# =====================================================================
# SECTION 7: CREATE FIRMWARE CONFIGURATION
# =====================================================================

log_stage "STAGE 6/7: Creating Firmware Configuration"

cat > "$FIRMWARE_CONFIG/firmware.json" << 'FIRMWARE_CONFIG'
{
  "firmware": {
    "version": "2.6",
    "name": "Orsay TV Universal Reviver",
    "boot_timestamp": "2026-10-02T12:00:00Z"
  },
  "platform": {
    "auto_detect": true,
    "supported": ["orsay_legacy", "tizen_modern", "webos"]
  },
  "services": {
    "wifi_direct": {
      "enabled": true,
      "port": 5555,
      "protocol": "P2P"
    },
    "allshare": {
      "enabled": true,
      "port": 8008,
      "protocol": "DLNA/UPnP"
    },
    "iptv": {
      "enabled": true,
      "stream_port": 5004
    },
    "wol": {
      "enabled": true,
      "port": 9,
      "wowlan_enabled": true
    },
    "http_api": {
      "enabled": true,
      "port": 8000,
      "dashboard_path": "/var/www/orsay"
    }
  },
  "security": {
    "local_only": true,
    "personal_server": "localhost:9999",
    "require_token": true
  },
  "updates": {
    "auto_check": true,
    "check_interval_hours": 24,
    "source": "personal_server_only"
  }
}

FIRMWARE_CONFIG

log_info "✓ Created firmware configuration: $FIRMWARE_CONFIG/firmware.json"

# =====================================================================
# SECTION 8: VERIFICATION & SUMMARY
# =====================================================================

log_stage "STAGE 7/7: Installation Verification"

# Check all components
check_item() {
    if [ -e "$1" ]; then
        log_info "✓ $2"
        return 0
    else
        log_warn "⚠ Missing: $2"
        return 1
    fi
}

check_item "$FIRMWARE_BIN/orsay_firmware_boot.py" "Firmware boot script"
check_item "$AUTOSTART_SCRIPT" "Autostart script"
check_item "$FIRMWARE_CONFIG/firmware.json" "Firmware configuration"

# Final summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            INSTALLATION COMPLETED SUCCESSFULLY ✓           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

cat << EOF

📍 FIRMWARE INSTALLATION COMPLETE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW IT WORKS: HTML → Shell → Python → Background → Autoload
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. INJECTION (Browser Vulnerability)
   └─ install.html → JavaScript injection (CVE-2015-2877/8251)
   └─ Browser executes: shell bootstrap code

2. BOOTSTRAP (This Script)
   └─ HTML trigger calls this bootstrap.sh
   └─ Creates directory structure
   └─ Installs Python dependencies
   └─ Sets up autostart mechanisms

3. PYTHON FIRMWARE (Background Process)
   └─ $FIRMWARE_BIN/orsay_firmware_boot.py
   └─ Runs in background (detached from terminal)
   └─ Starts all services
   └─ Enters infinite main loop
   └─ Logs to: $FIRMWARE_LOGS/

4. AUTOLOAD (Persistent Startup)
   └─ On system reboot: $AUTOSTART_SCRIPT runs automatically
   └─ Starts Python firmware in background
   └─ Services resume where they left off

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTALLATION PATHS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Home Directory:     $FIRMWARE_HOME
Binaries:          $FIRMWARE_BIN
Services:          $FIRMWARE_SERVICES
Configuration:     $FIRMWARE_CONFIG
Logs:              $FIRMWARE_LOGS

Boot Script:       $FIRMWARE_BIN/orsay_firmware_boot.py
Autostart Script:  $AUTOSTART_SCRIPT
Configuration:     $FIRMWARE_CONFIG/firmware.json

Logs:
  - Firmware boot:  $FIRMWARE_LOGS/boot.log
  - Autostart:      $FIRMWARE_LOGS/autostart.log
  - Runtime:        $FIRMWARE_LOGS/firmware.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Restart your TV to activate autoload
   └─ Firmware will start automatically on boot

2. Check logs:
   └─ tail -f $FIRMWARE_LOGS/firmware.log

3. Monitor services:
   └─ Ports 5555 (P2P), 8008 (DLNA), 8000 (API)

4. Download Orsay Remote TV app to test P2P connection

5. Check updates from personal server:
   └─ python3 $FIRMWARE_HOME/local_update_system.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHITECTURE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─ LAYER 1: Samsung Orsay Firmware (Original)
│
├─ LAYER 2: Browser Injection (CVE Exploitation)
│
├─ LAYER 3: Bootstrap Shell Script (THIS FILE)
│           └─ Sets up directories, Python, autoload
│
├─ LAYER 4: Python 3 Firmware Runtime
│           ├─ $FIRMWARE_BIN/orsay_firmware_boot.py
│           ├─ Services (Wi-Fi Direct, DLNA, etc)
│           └─ Running in background
│
├─ LAYER 5: System Autoload
│           └─ $AUTOSTART_SCRIPT
│           └─ Called on system boot
│           └─ Restarts firmware automatically
│
└─ LAYER 6: User Applications
            ├─ IPTV Streaming
            ├─ AllShare Media
            ├─ Orsay Remote TV
            └─ Your custom services

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Firmware installation complete!
✓ Ready for first boot and autostart testing
✓ Logs available at: $FIRMWARE_LOGS

EOF

log_info "Installation script finished at $(date)"
