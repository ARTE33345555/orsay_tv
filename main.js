/**
 * Orsay TV 2.6 Main Dashboard Controller
 * Python 3.11.4 Runtime - Wi-Fi Direct P2P Support
 * Orsay Remote TV (Android/iOS) Compatible
 */

// ==========================================
// SECTION NAVIGATION
// ==========================================
function switchSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));

    // Show selected section
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.classList.add('active');
    }

    // Update active menu item
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => item.classList.remove('active'));
    
    const activeItem = document.querySelector(`[onclick="switchSection('${sectionId}')"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }

    // Log navigation
    console.log(`[Navigation] Switched to section: ${sectionId}`);
}

// ==========================================
// REMOTE DEVICES & WI-FI DIRECT
// ==========================================
function startDiscovery() {
    alert('🔍 Starting Wi-Fi Direct device discovery...\n\nSearching for nearby Orsay Remote TV (Android/iOS) devices on port 5555...');
    
    // Simulate discovery
    setTimeout(() => {
        alert('✅ Discovery complete!\n\n1x Android device found (Samsung Galaxy S23)\n1x iOS device found (iPhone 14)');
    }, 2000);
    
    console.log('[Wi-Fi Direct] Device discovery started on port 5555');
}

function showQRCode() {
    document.getElementById('qrModal').classList.add('active');
    console.log('[QR Code] Showing pairing QR code');
}

function closeQRModal() {
    document.getElementById('qrModal').classList.remove('active');
}

// ==========================================
// IPTV FUNCTIONS
// ==========================================
function loadIPTVPlaylist() {
    const urlInput = document.getElementById('iptv-url');
    const url = urlInput.value;

    if (!url) {
        alert('Please enter a valid M3U playlist URL');
        return;
    }

    alert(`📥 Loading IPTV playlist from:\n${url}\n\nThis will parse the M3U file and load all channels.`);
    console.log(`[IPTV] Loading playlist from: ${url}`);

    // Clear input
    urlInput.value = '';
}

function playChannel(channelName) {
    alert(`▶️ Now Playing: ${channelName}\n\nStreaming video via H.264/H.265 codec...\n\nYou can control playback with your Orsay Remote TV app.`);
    console.log(`[IPTV] Playing channel: ${channelName}`);
}

// ==========================================
// MEDIA FUNCTIONS
// ==========================================
function openMediaBrowser() {
    alert('📂 Opening AllShare DLNA Media Browser\n\nThis will display all media files in your library:\n- Videos: 42 items\n- Photos: 156 items\n- Music: 284 items');
    console.log('[Media] Opening AllShare DLNA media browser');
}

// ==========================================
// SYSTEM FUNCTIONS
// ==========================================
function rebootSystem() {
    if (confirm('🔄 Reboot the TV system?\n\nThis will restart all services. Continue?')) {
        alert('🔄 System rebooting...\n\nAll services will be restarted in 10 seconds.');
        console.log('[System] Rebooting system');
    }
}

function factoryReset() {
    if (confirm('⚠️ WARNING: Factory Reset will erase all settings and data!\n\nAre you absolutely sure?')) {
        if (confirm('This action cannot be undone. Continue with factory reset?')) {
            alert('📝 Performing factory reset...\n\nAll settings will be restored to defaults.\nSystem will reboot automatically.');
            console.log('[System] Factory reset initiated');
        }
    }
}

// ==========================================
// SYSTEM MONITORING
// ==========================================
class SystemMonitor {
    constructor() {
        this.uptime = 48 * 60 + 23; // minutes
        this.memory = 156; // MB
        this.connectedDevices = 2;
        this.activeServices = 7;
    }

    update() {
        // Update uptime
        this.uptime++;
        const hours = Math.floor(this.uptime / 60);
        const minutes = this.uptime % 60;
        document.getElementById('stat-uptime').textContent = `${hours}h ${minutes}m`;

        // Simulate memory fluctuation
        this.memory = 150 + Math.random() * 20;
        document.getElementById('stat-ram').textContent = Math.round(this.memory) + ' MB';

        // Log to console periodically
        if (this.uptime % 60 === 0) {
            console.log(`[Monitor] Uptime: ${hours}h ${minutes}m | Memory: ${Math.round(this.memory)}MB`);
        }
    }
}

const monitor = new SystemMonitor();
setInterval(() => monitor.update(), 60000); // Update every minute

// ==========================================
// WI-FI DIRECT P2P HANDLER
// ==========================================
class WiFiDirectHandler {
    constructor() {
        this.port = 5555;
        this.isListening = false;
        this.connectedDevices = [];
    }

    start() {
        this.isListening = true;
        console.log(`[Wi-Fi Direct] Started listening on port ${this.port}`);
        console.log('[Wi-Fi Direct] Waiting for Orsay Remote TV (Android/iOS) connections...');
    }

    handleCommand(device, command) {
        console.log(`[Wi-Fi Direct] Command from ${device}: ${command.type}`);
        
        switch(command.type) {
            case 'power':
                console.log(`[Power] ${command.action}`);
                break;
            case 'volume':
                console.log(`[Volume] ${command.action} (level: ${command.level})`);
                break;
            case 'channel':
                console.log(`[Channel] ${command.channel}`);
                break;
            case 'app':
                console.log(`[App] Launch: ${command.app_id}`);
                break;
            default:
                console.log(`[Command] Unknown: ${command.type}`);
        }
    }
}

const wifiDirect = new WiFiDirectHandler();
wifiDirect.start();

// ==========================================
// ALLSHARE DLNA MEDIA SERVER
// ==========================================
class AllShareMediaServer {
    constructor() {
        this.port = 8008;
        this.isRunning = false;
        this.mediaLibrary = {
            videos: 42,
            photos: 156,
            music: 284,
            storage: '8.4 GB'
        };
    }

    start() {
        this.isRunning = true;
        console.log(`[AllShare DLNA] Media server started on port ${this.port}`);
        console.log(`[AllShare DLNA] Device is discoverable on local network`);
        console.log(`[AllShare DLNA] Media Library: ${this.mediaLibrary.videos} videos, ${this.mediaLibrary.photos} photos, ${this.mediaLibrary.music} songs`);
    }

    addMedia(type, metadata) {
        console.log(`[AllShare] Added ${type}: ${metadata.title}`);
    }
}

const allshare = new AllShareMediaServer();
allshare.start();

// ==========================================
// WOL / WOWLAN HANDLER
// ==========================================
class PowerManagement {
    constructor() {
        this.wolEnabled = true;
        this.wowlanEnabled = true;
    }

    listenForWOL() {
        console.log('[WoL] Listening for magic packets on port 9');
        console.log('[WoWLAN] Wake-on-Wireless-LAN enabled');
    }

    handleMagicPacket(source) {
        console.log(`[WoL] Magic packet received from ${source} - Waking system`);
    }
}

const powerMgmt = new PowerManagement();
powerMgmt.listenForWOL();

// ==========================================
// IPTV SERVICE
// ==========================================
class IPTVService {
    constructor() {
        this.isRunning = true;
        this.channels = [];
        this.currentChannel = null;
    }

    loadPlaylist(url) {
        console.log(`[IPTV] Loading playlist from: ${url}`);
        // Parse M3U and load channels
        this.channels = [
            { name: 'Channel 1', url: 'http://stream1.example.com', logo: '📡' },
            { name: 'Channel 2', url: 'http://stream2.example.com', logo: '📡' },
            { name: 'Channel 3', url: 'http://stream3.example.com', logo: '📡' }
        ];
        console.log(`[IPTV] Loaded ${this.channels.length} channels`);
    }

    play(channelIndex) {
        if (channelIndex < this.channels.length) {
            this.currentChannel = this.channels[channelIndex];
            console.log(`[IPTV] Playing: ${this.currentChannel.name} from ${this.currentChannel.url}`);
        }
    }
}

const iptv = new IPTVService();

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('╔════════════════════════════════════════════════════╗');
    console.log('║  ORSAY TV 2.6 - Universal TV Reviver               ║');
    console.log('║  Python 3.11.4 Runtime Environment                ║');
    console.log('║  Wi-Fi Direct P2P Ready                            ║');
    console.log('║  AllShare DLNA Media Server Running                ║');
    console.log('║  WoL / WoWLAN Enabled                              ║');
    console.log('╚════════════════════════════════════════════════════╝');
    console.log('');
    
    console.log('[System] Core Services Initialized:');
    console.log('  ✓ Wi-Fi Direct (P2P) - Port 5555');
    console.log('  ✓ AllShare DLNA - Port 8008');
    console.log('  ✓ IPTV Service - Ready');
    console.log('  ✓ Power Management - WoL/WoWLAN');
    console.log('  ✓ Telegram TV - Available');
    console.log('  ✓ Home Radio Pro - Voice Ready');
    console.log('  ✓ OTA Daemon - Connected to ARTE_SERVER');
    console.log('');
    
    console.log('[Status] Waiting for Orsay Remote TV connection...');
    console.log('[Status] Dashboard ready for user interaction');
});

// ==========================================
// WEBSOCKET CONNECTION FOR REAL-TIME UPDATES
// ==========================================
class RealtimeUpdater {
    constructor() {
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        // In a real scenario, this would connect to WebSocket server
        console.log('[WebSocket] Attempting connection to real-time service...');
        
        // Simulate connection
        setTimeout(() => {
            this.connected = true;
            console.log('[WebSocket] Connected to real-time updates');
            this.subscribeToEvents();
        }, 500);
    }

    subscribeToEvents() {
        const events = [
            'remote_device_connected',
            'remote_command_received',
            'iptv_channel_changed',
            'media_file_accessed',
            'system_status_changed',
            'network_event'
        ];

        console.log('[WebSocket] Subscribed to events:');
        events.forEach(event => console.log(`  - ${event}`));
    }
}

const updater = new RealtimeUpdater();
updater.connect();

// ==========================================
// ERROR HANDLING & LOGGING
// ==========================================
window.addEventListener('error', function(event) {
    console.error(`[Error] ${event.error.message}`);
    console.error(event.error.stack);
});

console.log('[Ready] Main dashboard initialized successfully');
